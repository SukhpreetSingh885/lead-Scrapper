from typing import List, Optional
from pydantic import BaseModel


class LocationSuggestion(BaseModel):
    id: Optional[int] = None
    city: str
    state: str
    district: Optional[str] = None
    locality: Optional[str] = None
    pincode: Optional[str] = None
    display_name: str

    class Config:
        from_attributes = True


class LocationValidationResult(BaseModel):
    is_valid: bool
    resolved_city: Optional[str] = None
    resolved_state: Optional[str] = None
    resolved_district: Optional[str] = None
    resolved_pincode: Optional[str] = None
    ambiguous: bool = False
    candidates: List[LocationSuggestion] = []
    message: Optional[str] = None

