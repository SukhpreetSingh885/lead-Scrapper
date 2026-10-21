from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DiscoveredLeadItem(BaseModel):
    external_id: Optional[str] = None
    business_name: str
    category: str
    address_line: Optional[str] = None
    locality: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    country: str = "India"
    phone: Optional[str] = None
    mobile: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    social_profiles: Optional[Dict[str, str]] = None
    raw_payload: Optional[Dict[str, Any]] = None
    is_eligible_for_crm: bool = True
    rejection_reason: Optional[str] = None
    source_code: str
    license_status: str = "permitted_storage"
    is_demo: bool = False
    all_contacts: Optional[List[Dict[str, Any]]] = None


class BaseDiscoveryProvider(ABC):
    @property
    @abstractmethod
    def code(self) -> str:
        """Unique identifier code for the source provider."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """True if the provider has all required credentials or can run."""
        pass

    @abstractmethod
    async def search(
        self,
        location: str,
        category: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DiscoveredLeadItem]:
        """Execute discovery search and return discovered items."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check provider connectivity and configuration status."""
        pass

