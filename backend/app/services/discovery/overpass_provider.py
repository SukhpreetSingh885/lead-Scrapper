import re
import json
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import httpx
from rapidfuzz import fuzz

from app.core.config import settings
from app.services.discovery.base import BaseDiscoveryProvider, DiscoveredLeadItem
from app.services.discovery.taxonomy import TAXONOMY, CategoryTaxonomyResolver
from app.services.enrichment.phone_extractor import IndianPhoneExtractor

logger = logging.getLogger(__name__)


# Dynamically populated category mappings from extensible taxonomy
CATEGORY_TAG_MAP: Dict[str, List[Tuple[str, str]]] = {}
CATEGORY_CANONICAL_NAME: Dict[str, str] = {}

for cat_def in TAXONOMY.values():
    canon_lower = cat_def.canonical_name.lower()
    CATEGORY_TAG_MAP[canon_lower] = cat_def.osm_tags
    CATEGORY_CANONICAL_NAME[canon_lower] = cat_def.canonical_name
    for alias in cat_def.aliases:
        alias_lower = alias.lower()
        CATEGORY_TAG_MAP[alias_lower] = cat_def.osm_tags
        CATEGORY_CANONICAL_NAME[alias_lower] = cat_def.canonical_name

# Standard coordinates for major Indian locations as fast lookup
INDIAN_CITY_COORDINATES: Dict[str, Tuple[float, float, str]] = {
    "mohali": (30.7046, 76.7179, "Punjab"),
    "sas nagar": (30.7046, 76.7179, "Punjab"),
    "chandigarh": (30.7333, 76.7794, "Chandigarh"),
    "ludhiana": (30.9010, 75.8573, "Punjab"),
    "amritsar": (31.6340, 74.8723, "Punjab"),
    "jalandhar": (31.3260, 75.5762, "Punjab"),
    "delhi": (28.6139, 77.2090, "Delhi"),
    "new delhi": (28.6139, 77.2090, "Delhi"),
    "noida": (28.5355, 77.3910, "Uttar Pradesh"),
    "gurugram": (28.4595, 77.0266, "Haryana"),
    "gurgaon": (28.4595, 77.0266, "Haryana"),
    "mumbai": (19.0760, 72.8777, "Maharashtra"),
    "pune": (18.5204, 73.8567, "Maharashtra"),
    "bengaluru": (12.9716, 77.5946, "Karnataka"),
    "bangalore": (12.9716, 77.5946, "Karnataka"),
    "jaipur": (26.9124, 75.7873, "Rajasthan"),
    "chennai": (13.0827, 80.2707, "Tamil Nadu"),
    "hyderabad": (17.3850, 78.4867, "Telangana"),
    "ahmedabad": (23.0225, 72.5714, "Gujarat"),
    "panchkula": (30.6942, 76.8606, "Haryana"),
    "zirakpur": (30.6425, 76.8173, "Punjab"),
    "kharar": (30.7499, 76.6411, "Punjab"),
    "navi mumbai": (19.0330, 73.0297, "Maharashtra"),
    "thane": (19.2183, 72.9781, "Maharashtra"),
    "kolkata": (22.5726, 88.3639, "West Bengal"),
}

SOCIAL_DOMAINS = [
    "instagram.com", "facebook.com", "fb.com", "linkedin.com",
    "twitter.com", "x.com", "youtube.com", "youtu.be", "pinterest.com"
]


class OverpassDiscoveryProvider(BaseDiscoveryProvider):
    def __init__(self):
        # Pool of Overpass servers with automatic fallback
        # OSM France and Kumi Systems have proven high availability
        self.endpoints = [
            getattr(settings, "OVERPASS_API_URL", "https://overpass.openstreetmap.fr/api/interpreter"),
            "https://overpass.openstreetmap.fr/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass-api.de/api/interpreter",
        ]
        # Remove duplicates while preserving order
        seen = set()
        self.endpoints = [x for x in self.endpoints if not (x in seen or seen.add(x))]

    @property
    def code(self) -> str:
        return "overpass"

    @property
    def is_configured(self) -> bool:
        return True

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "provider": "OpenStreetMap Overpass API (Real Data)",
            "configured": True,
            "primary_endpoint": self.endpoints[0],
            "fallback_endpoints": self.endpoints[1:],
            "attribution": "Data © OpenStreetMap contributors, ODbL 1.0",
            "license": "ODbL 1.0"
        }

    def _resolve_category(self, category_input: str) -> Tuple[str, List[Tuple[str, str]]]:
        cat_def, _ = CategoryTaxonomyResolver.resolve(category_input)
        return cat_def.canonical_name, cat_def.osm_tags

    def _resolve_category_tags(self, category_input: str) -> List[Tuple[str, str]]:
        _, tags = self._resolve_category(category_input)
        return tags

    def _validate_element_category(self, tags: Dict[str, Any], canonical_cat: str) -> Tuple[bool, Optional[str]]:
        """
        Validates whether an OSM element actually corresponds to the requested category.
        Rejects elements that lack relevant source tags or belong to unrelated categories
        (e.g., rejecting coffee shops or hairdressers when searching for Gyms).
        """
        try:
            cat_def, _ = CategoryTaxonomyResolver.resolve(canonical_cat)
        except ValueError:
            return False, None

        name = (tags.get("name") or tags.get("name:en") or "").lower()

        # 1. Check negative tags - exclude unrelated amenities, shops, and leisure types
        for tag_key, excluded_vals in cat_def.negative_tags.items():
            current_val = tags.get(tag_key, "").lower()
            if current_val:
                current_split = [x.strip() for x in current_val.split(";")]
                if any(x in excluded_vals for x in current_split):
                    return False, None

        # 2. Check matching OSM tags
        for k, v in cat_def.osm_tags:
            tag_val = tags.get(k, "").lower()
            if tag_val:
                tag_split = [x.strip() for x in tag_val.split(";")]
                if v.lower() in tag_split or tag_val == v.lower():
                    # Disambiguate generic tags like sports_centre
                    if k == "leisure" and v == "sports_centre":
                        sport = tags.get("sport", "").lower()
                        if "fitness" in sport or any(kw in name for kw in cat_def.keywords):
                            return True, cat_def.canonical_name
                        return False, None
                    return True, cat_def.canonical_name

        # Support sports_hall when business name contains fitness/gym keywords
        if tags.get("leisure") == "sports_hall" and any(kw in name for kw in cat_def.keywords):
            return True, cat_def.canonical_name

        # 3. Commercial entity with keyword in name
        has_commercial_tag = bool(
            tags.get("amenity") or tags.get("shop") or tags.get("office") or
            tags.get("healthcare") or tags.get("leisure") or tags.get("tourism")
        )
        if has_commercial_tag and name:
            for kw in cat_def.keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', name):
                    return True, cat_def.canonical_name

        return False, None

    def _resolve_coordinates(self, location_input: str) -> Tuple[float, float, str, str]:
        """Resolves Indian location string into (latitude, longitude, resolved_city, resolved_state)."""
        clean_loc = location_input.strip().lower().replace(", india", "").strip()

        # Check in predefined Indian city coordinates
        for city_key, (lat, lon, state) in INDIAN_CITY_COORDINATES.items():
            if city_key in clean_loc or clean_loc in city_key or fuzz.ratio(clean_loc, city_key) >= 75:
                return lat, lon, city_key.title(), state

        # If not in dictionary, check database IndiaLocation table
        try:
            from app.core.database import SessionLocal
            from app.models import IndiaLocation
            db = SessionLocal()
            try:
                loc = db.query(IndiaLocation).filter(
                    IndiaLocation.latitude.isnot(None),
                    (IndiaLocation.city.ilike(f"%{clean_loc}%") | IndiaLocation.pincode.like(f"{clean_loc}%"))
                ).first()
                if loc and loc.latitude and loc.longitude:
                    return loc.latitude, loc.longitude, loc.city, loc.state
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to lookup coordinates from database: {e}")

        # Default fallback to Mohali / SAS Nagar center if Mohali was intended
        return 30.7046, 76.7179, location_input.title(), "Punjab"

    def _build_overpass_query(
        self,
        tag_filters: List[Tuple[str, str]],
        lat: float,
        lon: float,
        radius_meters: int = 15000,
        timeout_seconds: int = 30
    ) -> str:
        """
        Builds valid Overpass QL with radius around center coordinates.
        Uses [out:json] and out center tags.
        """
        clauses = []
        for key, value in tag_filters:
            clauses.append(f'  nwr["{key}"="{value}"](around:{radius_meters},{lat},{lon});')

        query_body = "\n".join(clauses)
        return f"""[out:json][timeout:{timeout_seconds}];
(
{query_body}
);
out center tags;"""

    async def search(
        self,
        location: str,
        category: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DiscoveredLeadItem]:
        """
        Executes real business discovery via OpenStreetMap Overpass API.
        Extracts real names, addresses, contacts, websites, social links.
        """
        canonical_cat, tag_filters = self._resolve_category(category)
        lat, lon, resolved_city, resolved_state = self._resolve_coordinates(location)

        # 15 km default radius covers municipal boundaries and contiguous urban agglomerations (e.g. Chandigarh Tricity)
        radius_meters = 15000
        if filters and filters.get("radius_meters"):
            try:
                radius_meters = int(filters["radius_meters"])
            except Exception:
                pass

        logger.info(
            f"[Discovery Pipeline] Initiating Overpass search for '{canonical_cat}' in '{resolved_city}' "
            f"around coordinates ({lat}, {lon}) with radius {radius_meters/1000:.1f} km, max_results={max_results}."
        )

        query = self._build_overpass_query(
            tag_filters=tag_filters,
            lat=lat,
            lon=lon,
            radius_meters=radius_meters,
            timeout_seconds=30
        )

        headers = {
            "User-Agent": "IndiaLeadsPlatform/1.0 (+https://indialeads.internal; lead-enrichment-verification)",
            "Referer": "https://overpass-turbo.eu/",
            "Accept": "*/*"
        }

        data_payload = {"data": query}
        raw_elements: List[Dict[str, Any]] = []
        query_succeeded = False
        error_details = []

        # Execute request across endpoints with exponential backoff on transient errors
        for endpoint in self.endpoints:
            max_attempts = 2
            backoff_delay = 1.0

            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"Querying Overpass endpoint {endpoint} (attempt {attempt})...")
                    async with httpx.AsyncClient(timeout=30.0, http2=False) as client:
                        resp = await client.post(endpoint, data=data_payload, headers=headers)

                    if resp.status_code == 200:
                        try:
                            json_resp = resp.json()
                            raw_elements = json_resp.get("elements", [])
                            query_succeeded = True
                            logger.info(f"Overpass query succeeded with {len(raw_elements)} elements from {endpoint}")
                            break
                        except Exception as json_err:
                            err_msg = f"Invalid JSON response from {endpoint}: {json_err}"
                            logger.warning(err_msg)
                            error_details.append(err_msg)
                    elif resp.status_code == 429:
                        err_msg = f"Rate limited (HTTP 429) on {endpoint}"
                        logger.warning(f"{err_msg}. Attempt {attempt}/{max_attempts}.")
                        error_details.append(err_msg)
                        if attempt < max_attempts:
                            await asyncio.sleep(backoff_delay)
                            backoff_delay *= 2
                    elif resp.status_code in (500, 502, 503, 504, 406):
                        err_msg = f"Server error (HTTP {resp.status_code}) on {endpoint}"
                        logger.warning(f"{err_msg}. Attempt {attempt}/{max_attempts}.")
                        error_details.append(err_msg)
                        if attempt < max_attempts:
                            await asyncio.sleep(backoff_delay)
                            backoff_delay *= 2
                    else:
                        err_msg = f"HTTP {resp.status_code} on {endpoint}: {resp.text[:100]}"
                        logger.warning(err_msg)
                        error_details.append(err_msg)
                        break
                except httpx.TimeoutException as exc:
                    err_msg = f"Timeout connecting to {endpoint}: {exc}"
                    logger.warning(f"{err_msg}. Attempt {attempt}/{max_attempts}.")
                    error_details.append(err_msg)
                    if attempt < max_attempts:
                        await asyncio.sleep(backoff_delay)
                except Exception as exc:
                    err_msg = f"Network error on {endpoint}: {exc}"
                    logger.warning(f"{err_msg}. Attempt {attempt}/{max_attempts}.")
                    error_details.append(err_msg)
                    if attempt < max_attempts:
                        await asyncio.sleep(backoff_delay)

            if query_succeeded:
                break

        if not query_succeeded:
            err_summary = "; ".join(error_details[-3:]) if error_details else "All endpoints unreachable"
            logger.error(f"All Overpass mirrors failed. Details: {err_summary}")
            if any("429" in e for e in error_details):
                raise RuntimeError(
                    f"OpenStreetMap Overpass API rate limit reached (HTTP 429). Please wait a moment and retry. ({err_summary})"
                )
            elif any("Timeout" in e for e in error_details):
                raise TimeoutError(
                    f"OpenStreetMap Overpass API requests timed out across all mirrors. Please retry. ({err_summary})"
                )
            else:
                raise RuntimeError(
                    f"OpenStreetMap Overpass servers are currently unavailable ({err_summary}). Please retry in a few moments."
                )

        # Parse OSM elements into DiscoveredLeadItem objects
        raw_count = len(raw_elements)
        unnamed_count = 0
        cat_mismatch_count = 0
        discovered_leads: List[DiscoveredLeadItem] = []

        for elem in raw_elements:
            tags = elem.get("tags", {})
            name = tags.get("name") or tags.get("name:en") or tags.get("brand")
            if not name or not name.strip():
                # Skip anonymous or unnamed nodes/ways
                unnamed_count += 1
                continue

            # Strictly validate that the OSM element belongs to the requested business category
            is_valid_cat, detected_cat = self._validate_element_category(tags, canonical_cat)
            if not is_valid_cat:
                cat_mismatch_count += 1
                logger.debug(
                    f"Discarding OSM element {elem.get('id')} ({name}): tags do not match category '{canonical_cat}'"
                )
                continue

            elem_type = elem.get("type", "node")
            elem_id = elem.get("id")
            external_id = f"osm-{elem_type}-{elem_id}"

            # Coordinates
            elem_lat = elem.get("lat") or elem.get("center", {}).get("lat") or lat
            elem_lon = elem.get("lon") or elem.get("center", {}).get("lon") or lon

            # Address fields
            street = tags.get("addr:street")
            housenumber = tags.get("addr:housenumber")
            suburb = tags.get("addr:suburb") or tags.get("addr:locality")
            postcode = tags.get("addr:postcode") or tags.get("postal_code")
            city = tags.get("addr:city") or resolved_city
            district = tags.get("addr:district") or resolved_city
            state = tags.get("addr:state") or resolved_state

            # Build readable address line
            addr_parts = []
            if housenumber:
                addr_parts.append(housenumber)
            if street:
                addr_parts.append(street)
            if suburb and suburb not in addr_parts:
                addr_parts.append(suburb)
            address_line = ", ".join(addr_parts) if addr_parts else None

            # Contact Tag Extraction via IndianPhoneExtractor
            osm_contacts = IndianPhoneExtractor.extract_all_contacts_from_osm_tags(
                tags=tags,
                elem_type=elem.get("type", "node"),
                elem_id=elem.get("id")
            )

            primary_mobile = None
            primary_landline = None
            primary_whatsapp = None

            for c in osm_contacts:
                ctype = c.get("contact_type")
                if ctype == "mobile" and not primary_mobile:
                    primary_mobile = c.get("normalized_value")
                elif ctype in ("landline", "phone") and not primary_landline:
                    primary_landline = c.get("normalized_value")
                elif ctype == "whatsapp" and not primary_whatsapp:
                    primary_whatsapp = c.get("normalized_value")

            phone = primary_mobile or primary_landline
            mobile = primary_mobile
            whatsapp = primary_whatsapp

            # Email
            email = tags.get("contact:email") or tags.get("email")

            # Website & Social Profiles classification
            raw_website = tags.get("contact:website") or tags.get("website") or tags.get("url")
            website_url = None
            social_profiles: Dict[str, str] = {}

            # Direct social tags
            for plat in ["instagram", "facebook", "linkedin", "twitter", "youtube", "whatsapp"]:
                tag_val = tags.get(f"contact:{plat}") or tags.get(plat)
                if tag_val:
                    social_profiles[plat] = tag_val

            if not whatsapp and social_profiles.get("whatsapp"):
                whatsapp_norm = IndianPhoneExtractor.normalize_phone(social_profiles["whatsapp"], default_type="whatsapp")
                if whatsapp_norm:
                    whatsapp = whatsapp_norm["normalized_value"]
                    osm_contacts.append({
                        "original_value": social_profiles["whatsapp"],
                        "normalized_value": whatsapp,
                        "contact_type": "whatsapp",
                        "is_valid": True,
                        "source": "osm",
                        "source_url": f"https://www.openstreetmap.org/{elem.get('type', 'node')}/{elem.get('id')}",
                        "evidence": f"OSM social tag: whatsapp={social_profiles['whatsapp']}"
                    })

            # Social classification on website tag
            if raw_website:
                raw_lower = raw_website.lower()
                is_social = False
                for domain in SOCIAL_DOMAINS:
                    if domain in raw_lower:
                        is_social = True
                        if "instagram" in domain:
                            social_profiles["instagram"] = raw_website
                        elif "facebook" in domain or "fb.com" in domain:
                            social_profiles["facebook"] = raw_website
                        elif "linkedin" in domain:
                            social_profiles["linkedin"] = raw_website
                        elif "twitter" in domain or "x.com" in domain:
                            social_profiles["twitter"] = raw_website
                        elif "youtube" in domain or "youtu.be" in domain:
                            social_profiles["youtube"] = raw_website
                        break

                if not is_social:
                    website_url = raw_website

            # Category
            item_cat = detected_cat or canonical_cat

            item = DiscoveredLeadItem(
                external_id=external_id,
                business_name=name.strip(),
                category=item_cat,
                address_line=address_line,
                locality=suburb,
                city=city,
                state=state,
                pincode=postcode,
                country="India",
                phone=phone,
                mobile=mobile,
                whatsapp=whatsapp,
                email=email,
                website_url=website_url,
                latitude=float(elem_lat) if elem_lat else None,
                longitude=float(elem_lon) if elem_lon else None,
                social_profiles=social_profiles if social_profiles else None,
                raw_payload=elem,
                is_eligible_for_crm=True,
                source_code=self.code,
                license_status="permitted_storage",
                is_demo=False,
                all_contacts=osm_contacts
            )
            discovered_leads.append(item)

            if len(discovered_leads) >= max_results:
                break

        logger.info(
            f"[Discovery Pipeline] Overpass query completed for '{canonical_cat}' in '{resolved_city}' "
            f"(Radius {radius_meters/1000:.1f}km): Raw={raw_count}, Unnamed skipped={unnamed_count}, "
            f"Category mismatches skipped={cat_mismatch_count}, Valid real businesses returned={len(discovered_leads)} (max requested={max_results})"
        )

        return discovered_leads
