from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DiscoveryJobCreate(BaseModel):
    location: str = Field(..., description="Indian city, district, state, or PIN code", min_length=2)
    category: str = Field(..., description="Business category or industry", min_length=2)
    max_leads: int = Field(default=50, ge=1, le=1000)
    source: str = Field(default="auto", description="Data source to query: auto, google_places, demo_fixture, licensed_csv")
    must_have_phone: bool = False
    must_have_mobile: bool = False
    must_have_email: bool = False
    must_have_website: bool = False
    must_have_whatsapp: bool = False
    exclude_already_saved: bool = False
    radius_km: Optional[int] = Field(default=None, description="Search radius in kilometers", ge=1, le=50)
    locations: Optional[List[str]] = Field(default=None, description="Optional list of Indian cities/areas for multi-location batch")


class DiscoveryJobItemOut(BaseModel):
    id: str
    business_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    is_eligible_for_crm: bool
    is_saved: bool = False
    is_already_saved: bool = False
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CityDiscoveryStats(BaseModel):
    city: str
    state: str
    latitude: float
    longitude: float
    radius_meters: int
    raw_discovered: int
    category_matched: int
    duplicates_removed: int
    unique_contributed: int
    contact_qualified: int = 0


class DiscoveryJobOut(BaseModel):
    id: str
    location_input: str
    resolved_city: str
    resolved_state: str
    category: str
    max_leads: int
    source_code: str
    status: str  # pending, queued, running, completed, partially_completed, failed, cancelled
    total_discovered: int
    total_eligible: int
    total_contact_qualified: int = 0
    total_mobile: int = 0
    total_landline: int = 0
    total_whatsapp: int = 0
    total_missing_phone: int = 0
    total_enriched: int = 0
    total_enrichment_unavailable: int = 0
    total_inserted: int
    total_updated: int
    total_duplicates_flagged: int
    total_failed: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[DiscoveryJobItemOut] = []
    per_city_stats: Optional[List[CityDiscoveryStats]] = None

    class Config:
        from_attributes = True


class EnrichmentJobOut(BaseModel):
    id: str
    branch_id: str
    status: str
    pages_crawled: int
    emails_found: int
    phones_found: int
    socials_found: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DiscoveryPreviewItemOut(BaseModel):
    id: str
    job_id: str
    business_name: str
    category: Optional[str] = None
    mobile: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    source: Optional[str] = None
    has_contact_number: bool = False
    is_already_saved: bool = False
    is_saved: bool = False
    branch_id: Optional[str] = None
    is_eligible_for_crm: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


