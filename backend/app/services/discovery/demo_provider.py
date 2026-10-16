import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz
from app.services.discovery.base import BaseDiscoveryProvider, DiscoveredLeadItem


class DemoDiscoveryProvider(BaseDiscoveryProvider):
    def __init__(self):
        self._demo_data = []
        self._load_demo_data()

    def _load_demo_data(self):
        seed_path = Path(__file__).resolve().parents[4] / "database" / "seed" / "demo_leads.json"
        if seed_path.exists():
            try:
                with open(seed_path, "r", encoding="utf-8") as f:
                    self._demo_data = json.load(f)
            except Exception:
                self._demo_data = []

    @property
    def code(self) -> str:
        return "demo_fixture"

    @property
    def is_configured(self) -> bool:
        return True

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "provider": "Demo Discovery Provider (Deterministic Offline Fixtures)",
            "configured": True,
            "demo_records_available": len(self._demo_data),
            "free_testing_mode": True
        }

    async def search(
        self,
        location: str,
        category: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DiscoveredLeadItem]:
        results: List[DiscoveredLeadItem] = []
        clean_loc = location.strip().lower()
        clean_cat = category.strip().lower()

        # 1. First, search loaded seed data for matching city/category
        matched_from_seed = []
        for item in self._demo_data:
            item_city = item.get("city", "").lower()
            item_cat = item.get("category", "").lower()

            loc_match = clean_loc in item_city or item_city in clean_loc or fuzz.partial_ratio(clean_loc, item_city) > 75
            cat_match = clean_cat in item_cat or item_cat in clean_cat or fuzz.partial_ratio(clean_cat, item_cat) > 75

            if loc_match and cat_match:
                matched_from_seed.append(item)
            elif loc_match:
                matched_from_seed.append(item)

        # 2. If matched items found in seed, convert them
        for item in matched_from_seed:
            phone_val = None
            for c in item.get("contacts", []):
                if c.get("type") in ("mobile", "landline", "whatsapp"):
                    phone_val = c.get("value")
                    break

            results.append(
                DiscoveredLeadItem(
                    external_id=f"DEMO-{item.get('branch_name', '').replace(' ', '-').lower()}",
                    business_name=f"[DEMO DATA] {item.get('branch_name', item.get('company_name'))}",
                    category=item.get("category", category.title()),
                    address_line=item.get("address_line"),
                    locality=item.get("locality"),
                    city=item.get("city", location.title()),
                    state=item.get("state", "India"),
                    pincode=item.get("pincode"),
                    country="India",
                    phone=phone_val,
                    website_url=item.get("website_url"),
                    raw_payload=item,
                    is_eligible_for_crm=True,
                    source_code=self.code,
                    license_status="permitted_storage",
                    is_demo=True
                )
            )

        # 3. If user requested a custom location/category not in the seed,
        # generate deterministic, cleanly labeled DEMO fixtures for this specific input
        # so any Indian city (e.g. Pune, Jaipur, Ludhiana) + category can be tested!
        if len(results) < max_results:
            sample_localities = [
                "Main Market", "Commercial Complex", "Industrial Area Phase 1",
                "City Centre", "Sector 1", "Civil Lines", "Mall Road", "Ring Road"
            ]
            sample_names = [
                f"Elite {category.title()} Studio",
                f"Apex {category.title()} Hub",
                f"Royal {category.title()} Works",
                f"Premier {category.title()} Enterprises",
                f"Urban {category.title()} Co.",
                f"Golden {category.title()} Solutions",
                f"Supreme {category.title()} & Services",
                f"Star {category.title()} Centre"
            ]

            needed = min(max_results - len(results), len(sample_names))
            for i in range(needed):
                loc_name = sample_localities[i % len(sample_localities)]
                b_name = f"[DEMO DATA] {sample_names[i]} - {loc_name}"
                mock_phone = f"+91 98{i:02d}0 12345"
                mock_domain = f"{category.lower().replace(' ', '')}{i+1}{location.lower().replace(' ', '')}.in"

                results.append(
                    DiscoveredLeadItem(
                        external_id=f"DEMO-AUTO-{location.lower()}-{category.lower()}-{i}",
                        business_name=b_name,
                        category=category.title(),
                        address_line=f"SCO {10 + i}, Ground Floor, {loc_name}",
                        locality=loc_name,
                        city=location.title(),
                        state="India",
                        pincode=f"{100000 + (i * 111):06d}",
                        country="India",
                        phone=mock_phone,
                        website_url=f"https://www.{mock_domain}",
                        raw_payload={"demo": True, "index": i, "generated_for_testing": True},
                        is_eligible_for_crm=True,
                        source_code=self.code,
                        license_status="permitted_storage",
                        is_demo=True
                    )
                )

        return results[:max_results]

