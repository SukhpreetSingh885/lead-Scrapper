import asyncio
import json
import logging
from datetime import datetime, timezone
from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.core.config import settings
from app.models import DiscoveryJob, DiscoveryJobItem, Branch
from app.services.discovery import (
    DemoDiscoveryProvider,
    OverpassDiscoveryProvider,
    GooglePlacesDiscoveryProvider,
    GoogleSearchDiscoveryProvider,
)
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.enrichment.website_enricher import WebsiteEnrichmentEngine

logger = logging.getLogger(__name__)


def run_async(coro):
    """Utility to run an async coroutine inside a synchronous Celery task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        # In case loop is already running (e.g. in some async runners)
        import nest_asyncio
        nest_asyncio.apply()
    return loop.run_until_complete(coro)


@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def execute_discovery_job(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if not job:
            logger.error(f"Discovery job {job_id} not found.")
            return {"error": "Job not found"}

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Parse filters
        filters = {}
        if job.filters_json:
            try:
                filters = json.loads(job.filters_json)
            except Exception:
                pass

        # Select provider based on source_code and configuration
        provider = None
        source_code = job.source_code

        if source_code == "overpass":
            provider = OverpassDiscoveryProvider()

        elif source_code == "auto":
            if getattr(settings, "DISCOVERY_PROVIDER", "overpass") == "overpass":
                provider = OverpassDiscoveryProvider()
            else:
                places_p = GooglePlacesDiscoveryProvider()
                if places_p.is_configured:
                    provider = places_p
                elif settings.DEMO_MODE:
                    provider = DemoDiscoveryProvider()
                else:
                    provider = OverpassDiscoveryProvider()

        elif source_code == "google_places":
            places_p = GooglePlacesDiscoveryProvider()
            if places_p.is_configured:
                provider = places_p
            else:
                job.status = "failed"
                job.error_message = (
                    "No live discovery provider configured. "
                    "Configure an authorized Google Places API key or use Overpass discovery mode."
                )
                db.commit()
                return {"error": job.error_message}

        elif source_code == "google_search":
            search_p = GoogleSearchDiscoveryProvider()
            if search_p.is_configured:
                provider = search_p
            else:
                job.status = "failed"
                job.error_message = "Google Custom Search is not configured."
                db.commit()
                return {"error": job.error_message}

        elif source_code == "demo_fixture":
            if not settings.DEMO_MODE:
                job.status = "failed"
                job.error_message = "Demo mode is disabled in this environment. Please use Overpass discovery for real leads."
                db.commit()
                return {"error": job.error_message}
            provider = DemoDiscoveryProvider()

        else:
            # Default to real Overpass discovery provider
            provider = OverpassDiscoveryProvider()

        # Determine target locations (supporting multi-location discovery batches)
        locations_to_query = filters.get("locations")
        if not locations_to_query and "," in job.resolved_city:
            locations_to_query = [c.strip() for c in job.resolved_city.split(",") if c.strip()]
        if not locations_to_query:
            locations_to_query = [job.resolved_city]

        from datetime import timedelta
        from sqlalchemy import or_
        import time
        import math
        from collections import defaultdict
        from app.models import Company, BusinessContact
        from app.services.deduplication.normalizer import DataNormalizer
        from app.services.enrichment.phone_extractor import IndianPhoneExtractor

        def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            r = 6371.0
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Pre-resolve coordinates for all queried cities
        city_metadata = {}
        for loc_name in locations_to_query:
            if hasattr(provider, "_resolve_coordinates"):
                c_lat, c_lon, res_city, res_state = provider._resolve_coordinates(loc_name)
                city_metadata[loc_name] = {
                    "city": res_city,
                    "state": res_state,
                    "lat": c_lat,
                    "lon": c_lon
                }
            else:
                city_metadata[loc_name] = {
                    "city": loc_name,
                    "state": job.resolved_state,
                    "lat": 0.0,
                    "lon": 0.0
                }

        radius_meters = int(filters.get("radius_meters", 15000)) if filters else 15000
        normalizer = DataNormalizer()
        seen_ext_ids = set()
        seen_business_keys = set()
        city_buckets = defaultdict(list)
        per_city_stats = []

        # Execute discovery search across locations sequentially with fair-use delay
        for loc_idx, loc_name in enumerate(locations_to_query):
            current_job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
            if not current_job or current_job.status == "cancelled":
                logger.info(f"Discovery job {job_id} was cancelled or deleted. Aborting execution.")
                return {"status": "cancelled"}

            if loc_idx > 0:
                time.sleep(1.5)  # Fair use rate limit delay between successive Overpass queries

            c_meta = city_metadata.get(loc_name, {})
            logger.info(
                f"[Multi-City Discovery] Querying city {loc_idx + 1}/{len(locations_to_query)}: "
                f"'{c_meta.get('city', loc_name)}' ({c_meta.get('lat')}, {c_meta.get('lon')}) "
                f"with radius {radius_meters / 1000:.1f}km for '{job.category}'."
            )

            try:
                # Request ample results per city so no subsequent city is starved
                batch_items = run_async(
                    provider.search(
                        location=loc_name,
                        category=job.category,
                        max_results=max(job.max_leads, 100),
                        filters=filters
                    )
                )
            except ValueError as val_err:
                job.status = "failed"
                job.error_message = str(val_err)
                db.commit()
                return {"error": job.error_message}

            raw_count = len(batch_items)
            city_dups = 0
            unique_for_this_city = []

            for item in batch_items:
                # Deduplicate overlapping businesses across locations by external_id
                if item.external_id and item.external_id in seen_ext_ids:
                    city_dups += 1
                    continue

                # Deduplicate by normalized name and coordinates / address
                norm_name = normalizer.normalize_company_name(item.business_name)
                coord_str = (
                    f"{round(item.latitude, 3)}_{round(item.longitude, 3)}"
                    if item.latitude and item.longitude
                    else (item.address_line or item.city or "")
                )
                b_key = f"{norm_name}_{coord_str}"
                if b_key in seen_business_keys:
                    city_dups += 1
                    continue

                if item.external_id:
                    seen_ext_ids.add(item.external_id)
                seen_business_keys.add(b_key)

                # Geographic city attribution based on proximity to queried city centers
                assigned_city = c_meta.get("city", loc_name)
                assigned_state = c_meta.get("state", job.resolved_state)
                if item.latitude and item.longitude and len(locations_to_query) > 1:
                    best_dist = float("inf")
                    for q_loc, meta in city_metadata.items():
                        if meta.get("lat") and meta.get("lon"):
                            d = haversine_km(item.latitude, item.longitude, meta["lat"], meta["lon"])
                            if d < best_dist:
                                best_dist = d
                                assigned_city = meta["city"]
                                assigned_state = meta["state"]

                raw_tags = item.raw_payload.get("tags", {}) if isinstance(item.raw_payload, dict) else {}
                addr_city = raw_tags.get("addr:city")
                if addr_city and any(m["city"].lower() in addr_city.lower() for m in city_metadata.values()):
                    item.city = addr_city
                else:
                    item.city = assigned_city
                    item.state = assigned_state

                unique_for_this_city.append(item)
                city_buckets[item.city].append(item)

            stat_entry = {
                "city": c_meta.get("city", loc_name),
                "state": c_meta.get("state", job.resolved_state),
                "latitude": round(c_meta.get("lat", 0.0), 4),
                "longitude": round(c_meta.get("lon", 0.0), 4),
                "radius_meters": radius_meters,
                "raw_discovered": raw_count,
                "category_matched": raw_count,
                "duplicates_removed": city_dups,
                "unique_contributed": len(unique_for_this_city),
                "contact_qualified": sum(1 for it in unique_for_this_city if bool(it.phone or (it.raw_payload.get("tags", {}) if isinstance(it.raw_payload, dict) else {}).get("contact:phone")))
            }
            per_city_stats.append(stat_entry)

        current_job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if not current_job or current_job.status == "cancelled":
            logger.info(f"Discovery job {job_id} was cancelled or deleted before saving items.")
            return {"status": "cancelled"}

        # Balanced round-robin allocation to prevent one city from starving others when max_leads is reached
        total_unique_items = sum(len(b) for b in city_buckets.values())
        if total_unique_items <= job.max_leads:
            discovered_items = [it for b in city_buckets.values() for it in b]
        else:
            discovered_items = []
            bucket_keys = list(city_buckets.keys())
            indices = {k: 0 for k in bucket_keys}
            while len(discovered_items) < job.max_leads:
                added_any = False
                for k in bucket_keys:
                    if indices[k] < len(city_buckets[k]):
                        discovered_items.append(city_buckets[k][indices[k]])
                        indices[k] += 1
                        added_any = True
                        if len(discovered_items) >= job.max_leads:
                            break
                if not added_any:
                    break

        job.total_discovered = len(discovered_items)
        job.total_duplicates_flagged = sum(s["duplicates_removed"] for s in per_city_stats)

        # Stage: Polite Website Contact Enrichment during preview
        enricher = WebsiteEnrichmentEngine(db)
        items_with_website = [it for it in discovered_items if it.website_url]
        total_with_website = len(items_with_website)
        enriched_success_count = 0

        if items_with_website:
            logger.info(
                f"[Discovery Pipeline] Starting preview website enrichment for {total_with_website} businesses "
                f"with official websites (SSRF protected, polite crawling, max 2 pages, 5s timeout)..."
            )

            async def enrich_all_preview_items():
                sem = asyncio.Semaphore(3)

                async def enrich_single(it_lead):
                    async with sem:
                        try:
                            return await enricher.enrich_preview_item(
                                website_url=it_lead.website_url,
                                business_name=it_lead.business_name,
                                max_pages=2,
                                timeout=5.0
                            )
                        except Exception as e:
                            logger.debug(f"Preview enrichment failed for {it_lead.business_name}: {e}")
                            return {"success": False, "reason": str(e)}

                coros = [enrich_single(it) for it in items_with_website]
                return await asyncio.gather(*coros, return_exceptions=True)

            try:
                enrichment_results = run_async(enrich_all_preview_items())

                for it, res in zip(items_with_website, enrichment_results):
                    if isinstance(res, dict) and res.get("success"):
                        phones = res.get("phones", [])
                        emails = res.get("emails", [])
                        socials = res.get("socials", [])

                        if phones or emails or socials:
                            enriched_success_count += 1

                            if not hasattr(it, "all_contacts") or it.all_contacts is None:
                                it.all_contacts = []

                            existing_norm_keys = {(c.get("contact_type"), c.get("normalized_value")) for c in it.all_contacts if c.get("normalized_value")}

                            for p in phones:
                                key = (p.get("contact_type"), p.get("normalized_value"))
                                if key not in existing_norm_keys:
                                    it.all_contacts.append(p)
                                    existing_norm_keys.add(key)
                                    if p.get("contact_type") == "mobile" and not it.mobile:
                                        it.mobile = p.get("normalized_value")
                                    elif p.get("contact_type") == "whatsapp" and not it.whatsapp:
                                        it.whatsapp = p.get("normalized_value")
                                    elif not it.phone:
                                        it.phone = p.get("normalized_value")

                            for e in emails:
                                norm_e = e.get("normalized_value")
                                if not it.email and norm_e:
                                    it.email = norm_e
                                if norm_e:
                                    e_key = ("email", norm_e)
                                    if e_key not in existing_norm_keys:
                                        it.all_contacts.append({
                                            "original_value": e.get("original_value") or norm_e,
                                            "normalized_value": norm_e,
                                            "contact_type": "email",
                                            "is_valid": True,
                                            "source": "website_enrichment",
                                            "source_url": e.get("source_url"),
                                            "evidence": e.get("evidence")
                                        })
                                        existing_norm_keys.add(e_key)

                            if socials:
                                if not it.social_profiles:
                                    it.social_profiles = {}
                                for s in socials:
                                    it.social_profiles[s["platform"]] = s["profile_url"]
            except Exception as enrich_err:
                logger.warning(f"[Discovery Pipeline] Non-fatal preview enrichment exception: {enrich_err}")

        eligible_count = 0
        already_saved_count = 0
        contact_qualified_count = 0
        missing_contact_count = 0

        total_mobile_count = 0
        total_landline_count = 0
        total_whatsapp_count = 0
        total_missing_phone_count = 0

        for item in discovered_items:
            # Consolidate contacts from all_contacts or item fields
            if not hasattr(item, "all_contacts") or item.all_contacts is None:
                item.all_contacts = []

            # If all_contacts is empty but item has raw phone, parse it
            if not item.all_contacts and item.phone:
                extracted = IndianPhoneExtractor.extract_multiple_phones(
                    raw_string=item.phone,
                    source="osm",
                    source_url=f"https://www.openstreetmap.org/{item.raw_payload.get('type', 'node')}/{item.raw_payload.get('id')}" if isinstance(item.raw_payload, dict) and item.raw_payload.get('id') else None,
                    evidence=f"OSM tag: phone={item.phone}"
                )
                item.all_contacts.extend(extracted)

            # Ensure mobile, phone, whatsapp are assigned from all_contacts
            for c in item.all_contacts:
                ctype = c.get("contact_type")
                if ctype == "mobile" and not item.mobile:
                    item.mobile = c.get("normalized_value")
                elif ctype in ("landline", "phone") and not item.phone:
                    item.phone = c.get("normalized_value")
                elif ctype == "whatsapp" and not item.whatsapp:
                    item.whatsapp = c.get("normalized_value")

            mobile = item.mobile
            phone = item.phone
            whatsapp = item.whatsapp
            email = item.email
            website = item.website_url

            has_mobile = bool(mobile)
            has_landline = bool(phone and phone != mobile)
            has_whatsapp = bool(whatsapp)
            has_any_contact = bool(mobile or phone or whatsapp)

            if has_mobile:
                total_mobile_count += 1
            if has_landline:
                total_landline_count += 1
            if has_whatsapp:
                total_whatsapp_count += 1

            if has_any_contact:
                contact_qualified_count += 1
            else:
                total_missing_phone_count += 1
                missing_contact_count += 1

            # Check if this business is already saved in the permanent CRM
            norm_branch = normalizer.normalize_branch_name(item.business_name)
            norm_comp = normalizer.normalize_company_name(item.business_name)

            existing_branch = db.query(Branch).join(Company).filter(
                Company.organization_id == job.organization_id,
                Branch.is_active == True,
                or_(
                    Branch.normalized_branch_name == norm_branch,
                    Company.normalized_name == norm_comp
                )
            ).first()

            if not existing_branch and item.all_contacts:
                for c in item.all_contacts:
                    if c.get("normalized_value"):
                        existing_branch = db.query(Branch).join(Company).join(BusinessContact).filter(
                            Company.organization_id == job.organization_id,
                            Branch.is_active == True,
                            BusinessContact.normalized_value == c["normalized_value"]
                        ).first()
                        if existing_branch:
                            break

            is_already_saved = existing_branch is not None
            existing_branch_id = existing_branch.id if existing_branch else None

            if is_already_saved:
                already_saved_count += 1

            # Apply user filter preferences
            if filters.get("must_have_phone") and not has_any_contact:
                continue
            if filters.get("must_have_mobile") and not has_mobile:
                continue
            if filters.get("must_have_email") and not email:
                continue
            if filters.get("must_have_website") and not website:
                continue
            if filters.get("must_have_whatsapp") and not has_whatsapp:
                continue
            if filters.get("exclude_already_saved") and is_already_saved:
                continue

            primary_city = locations_to_query[0] if locations_to_query else job.resolved_city
            primary_state = job.resolved_state.split(",")[0].strip() if job.resolved_state else "India"

            # Full serialized payload for future manual saving
            payload_dict = {
                "external_id": item.external_id,
                "business_name": item.business_name,
                "category": item.category or job.category,
                "address_line": item.address_line,
                "locality": item.locality,
                "city": item.city or primary_city,
                "state": item.state or primary_state,
                "pincode": item.pincode,
                "country": item.country or "India",
                "phone": phone,
                "mobile": mobile,
                "whatsapp": whatsapp,
                "email": email,
                "website_url": website,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "social_profiles": item.social_profiles,
                "raw_payload": item.raw_payload,
                "source_code": item.source_code,
                "license_status": item.license_status,
                "is_demo": item.is_demo,
                "is_eligible_for_crm": item.is_eligible_for_crm,
                "all_contacts": item.all_contacts
            }

            # Save in preview storage (discovery_job_items) with 24h expiration
            job_item = DiscoveryJobItem(
                job_id=job.id,
                external_id=item.external_id,
                raw_payload=json.dumps(payload_dict, default=str),
                business_name=item.business_name,
                category=item.category or job.category,
                address=item.address_line,
                city=item.city or primary_city,
                state=item.state or primary_state,
                phone=phone,
                mobile=mobile,
                whatsapp=whatsapp,
                email=email,
                website=website,
                source_code=item.source_code or "overpass",
                is_eligible_for_crm=item.is_eligible_for_crm,
                is_already_saved=is_already_saved,
                is_saved=False,  # Unsaved preview item: not committed to permanent CRM
                branch_id=existing_branch_id,
                rejection_reason=item.rejection_reason,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            db.add(job_item)
            eligible_count += 1

        # Store contact metrics and per-city stats in filters_json
        filters["contact_metrics"] = {
            "total_mobile": total_mobile_count,
            "total_landline": total_landline_count,
            "total_whatsapp": total_whatsapp_count,
            "total_missing_phone": total_missing_phone_count,
            "total_enriched": enriched_success_count,
            "total_enrichment_unavailable": total_with_website - enriched_success_count,
            "total_with_website": total_with_website
        }
        filters["per_city_stats"] = per_city_stats
        job.filters_json = json.dumps(filters)

        # Finalize job in completed state with preview items available
        job.total_eligible = eligible_count
        job.total_contact_qualified = contact_qualified_count
        job.total_inserted = 0  # Previews are NOT automatically saved to CRM
        job.total_updated = already_saved_count  # Accurately reflect count already existing in CRM
        job.total_duplicates_flagged = sum(s["duplicates_removed"] for s in per_city_stats) if per_city_stats else 0
        job.total_failed = 0
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        db.commit()

        logger.info(
            f"[Discovery Pipeline] Search Job {job.id} finalized for '{job.category}' in '{job.resolved_city}': "
            f"Stage 1: Discovered={job.total_discovered} (from OpenStreetMap before deduplication), "
            f"Stage 2: Eligible Previews={eligible_count} (after user filters), "
            f"Stage 3: Already in CRM={already_saved_count} (deduplication matches), "
            f"Stage 4: Contact-qualified={contact_qualified_count} (has phone/mobile/whatsapp), "
            f"Stage 5: Missing contact numbers={missing_contact_count}"
        )

        return {
            "job_id": job.id,
            "status": job.status,
            "discovered": job.total_discovered,
            "eligible": eligible_count,
            "already_saved": already_saved_count,
            "contact_qualified": contact_qualified_count,
            "missing_contacts": missing_contact_count,
            "is_preview_ready": True
        }

    except Exception as exc:
        db.rollback()
        logger.exception(f"Failed discovery job {job_id}: {exc}")
        job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
        if hasattr(self, "request") and getattr(self.request, "id", None):
            try:
                raise self.retry(exc=exc)
            except Exception:
                pass
        return {"error": str(exc), "status": "failed"}
    finally:
        db.close()

