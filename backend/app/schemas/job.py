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


class DiscoveryJobItemOut(BaseModel):
    id: str
    business_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    is_eligible_for_crm: bool
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


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

