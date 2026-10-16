import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.discovery.base import BaseDiscoveryProvider, DiscoveredLeadItem


class GoogleSearchDiscoveryProvider(BaseDiscoveryProvider):
    SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: Optional[str] = None, cx: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_SEARCH_API_KEY
        self.cx = cx or settings.GOOGLE_SEARCH_CX

    @property
    def code(self) -> str:
        return "google_search"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.cx and len(self.api_key.strip()) > 10)

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "ready" if self.is_configured else "disabled",
            "provider": "Google Custom Search JSON API",
            "configured": self.is_configured,
            "requires_key": True,
            "compliance_note": "Authorized Google Search API only. No consumer HTML scraping."
        }

    async def search(
        self,
        location: str,
        category: str,
        max_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DiscoveredLeadItem]:
        if not self.is_configured:
            raise ValueError(
                "Google Search API is disabled or not configured. "
                "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX in your environment."
            )

        query = f'"{category}" "{location}" India contact phone email'
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(max_results, 10),
            "gl": "in"
        }

        discovered: List[DiscoveredLeadItem] = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(self.SEARCH_API_URL, params=params)
            if response.status_code != 200:
                raise RuntimeError(f"Google Search API error ({response.status_code}): {response.text}")

            data = response.json()
            items = data.get("items", [])

            for item in items:
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")

                discovered.append(
                    DiscoveredLeadItem(
                        external_id=link,
                        business_name=title.split("-")[0].split("|")[0].strip(),
                        category=category,
                        address_line=location,
                        city=location,
                        state="India",
                        country="India",
                        website_url=link,
                        raw_payload={"snippet": snippet, "link": link},
                        is_eligible_for_crm=True,
                        source_code=self.code,
                        license_status="permitted_storage",
                        is_demo=False
                    )
                )

        return discovered

