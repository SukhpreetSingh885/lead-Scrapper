from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ExportCreate(BaseModel):
    file_format: str = Field(default="csv", pattern="^(csv|xlsx)$")
    selected_ids: Optional[List[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    has_mobile: Optional[bool] = None
    has_email: Optional[bool] = None


class ExportOut(BaseModel):
    id: str
    file_format: str
    row_count: int
    file_size_bytes: int
    status: str
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

