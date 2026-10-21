from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class IndustryExportOption(BaseModel):
    category: str
    slug: str
    total_leads: int
    qualified_leads: int


class ExportCreate(BaseModel):
    file_format: str = Field(default="xlsx", pattern="^(csv|xlsx)$")
    export_mode: str = Field(default="single", pattern="^(single|all_combined|all_separate_zip)$")
    selected_ids: Optional[List[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    job_id: Optional[str] = None
    has_contact_number: Optional[bool] = None
    contact_qualified: Optional[bool] = None
    has_mobile: Optional[bool] = None
    has_email: Optional[bool] = None


class ExportOut(BaseModel):
    id: str
    file_format: str
    filename: Optional[str] = None
    row_count: int
    file_size_bytes: int
    status: str
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
