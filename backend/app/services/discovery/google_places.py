import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.discovery.base import BaseDiscoveryProvider, DiscoveredLeadItem


class GooglePlacesDiscoveryProvider(BaseDiscoveryProvider):
    PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY

    @property
    def code(self) -> str:
        return "google_places"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "ready" if self.is_configured else "unconfigured",
            "provider": "Google Places API (Official Text Search v1)",
            "configured": self.is_configured,
            "requires_key": True,
            "compliance_note": "Field-limited discovery preview only. Restricted from permanent CRM storage/export."
        }

    async def search(
        self,
        location: str,
        category: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DiscoveredLeadItem]:
        if not self.is_configured:
            raise ValueError(
                "Google Places API key is not configured. "
                "Set GOOGLE_MAPS_API_KEY in your environment, or use demo/licensed import mode."
            )

        query = f"{category} in {location}, India"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            # Field mask to strictly limit billing and data exposure
            "X-Goog-FieldMask": (
                "places.id,"
                "places.displayName,"
                "places.formattedAddress,"
                "places.nationalPhoneNumber,"
                "places.internationalPhoneNumber,"
                "places.websiteUri,"
                "places.location"
            )
        }
        body = {
            "textQuery": query,
            "pageSize": min(max_results, 20),
            "regionCode": "IN"
        }

        discovered: List[DiscoveredLeadItem] = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(self.PLACES_API_URL, headers=headers, json=body)
            if response.status_code != 200:
                raise RuntimeError(f"Google Places API error ({response.status_code}): {response.text}")

            data = response.json()
            places = data.get("places", [])

            for place in places:
                name = place.get("displayName", {}).get("text", "Unknown Business")
                addr = place.get("formattedAddress", "")
                phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
                website = place.get("websiteUri")
                place_id = place.get("id")

                # Parse basic city and state from formatted address if possible
                addr_parts = [p.strip() for p in addr.split(",") if p.strip()]
                city = location
                state = "India"
                if len(addr_parts) >= 2:
                    city = addr_parts[-2]

                discovered.append(
                    DiscoveredLeadItem(
                        external_id=place_id,
                        business_name=name,
                        category=category,
                        address_line=addr,
                        city=city,
                        state=state,
                        country="India",
                        phone=phone,
                        website_url=website,
                        raw_payload=place,
                        # Google Places terms: Compliant temporary discovery preview only
                        is_eligible_for_crm=False,
                        rejection_reason="Google Maps Platform Terms: Restricted from permanent export/storage into CRM without independent licensing.",
                        source_code=self.code,
                        license_status="google_terms_preview_only",
                        is_demo=False
                    )
                )

        return discovered

