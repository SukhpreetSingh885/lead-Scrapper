from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BusinessContactOut(BaseModel):
    id: str
    contact_type: str  # mobile, landline, whatsapp, email
    original_value: str
    normalized_value: str
    is_primary: bool
    is_verified: bool
    source: str
    source_url: Optional[str] = None
    evidence: Optional[str] = None

    class Config:
        from_attributes = True


class SocialProfileOut(BaseModel):
    id: str
    platform: str
    profile_url: str
    handle: Optional[str] = None

    class Config:
        from_attributes = True


class LeadBranchDetail(BaseModel):
    id: str
    company_id: str
    business_name: str
    legal_name: str
    category: str
    description: Optional[str] = None
    website_domain: Optional[str] = None
    website_url: Optional[str] = None

    address_line: Optional[str] = None
    locality: Optional[str] = None
    city: str
    district: Optional[str] = None
    state: str
    pincode: Optional[str] = None
    country: str = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Extracted contact values for convenience in tables and UI
    primary_mobile: Optional[str] = None
    primary_landline: Optional[str] = None
    primary_whatsapp: Optional[str] = None
    primary_email: Optional[str] = None

    contacts: List[BusinessContactOut] = []
    social_profiles: List[SocialProfileOut] = []

    # Provenance and status
    source_name: Optional[str] = None
    source_code: Optional[str] = None
    source_permission_status: str
    confidence_score: float
    enrichment_status: str
    last_checked_at: Optional[datetime] = None
    is_demo: bool
    is_archived: bool = False
    archive_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadListItem(BaseModel):
    id: str
    company_id: str
    business_name: str
    category: str
    primary_mobile: Optional[str] = None
    primary_landline: Optional[str] = None
    primary_whatsapp: Optional[str] = None
    primary_email: Optional[str] = None
    website_url: Optional[str] = None
    city: str
    state: str
    locality: Optional[str] = None
    pincode: Optional[str] = None
    address_line: Optional[str] = None
    enrichment_status: str
    source_name: Optional[str] = None
    is_demo: bool
    is_archived: bool = False
    archive_reason: Optional[str] = None
    social_profiles_count: int = 0
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    branch_name: Optional[str] = None
    category: Optional[str] = None
    address_line: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    website_url: Optional[str] = None


class LeadFilterParams(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    job_id: Optional[str] = None
    has_contact_number: Optional[bool] = None
    has_phone: Optional[bool] = None
    has_mobile: Optional[bool] = None
    has_email: Optional[bool] = None
    has_website: Optional[bool] = None
    has_whatsapp: Optional[bool] = None
    enrichment_status: Optional[str] = None
    is_demo: Optional[bool] = None
    is_archived: Optional[bool] = False
    query: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)


class SaveSelectedLeadsRequest(BaseModel):
    job_id: str
    item_ids: Optional[List[str]] = None
    save_all_eligible: bool = False


class SaveSelectedLeadsResponse(BaseModel):
    success: bool
    total_requested: int
    saved_count: int
    already_existing_count: int
    skipped_count: int
    failed_count: int
    saved_lead_ids: List[str] = []
    message: str


class BulkDeleteLeadsRequest(BaseModel):
    lead_ids: Optional[List[str]] = None
    delete_all_filtered: bool = False
    filters: Optional[LeadFilterParams] = None


class DeleteLeadsResponse(BaseModel):
    success: bool
    deleted_count: int
    message: str


