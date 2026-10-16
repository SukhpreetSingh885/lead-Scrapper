from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.lead import LeadListItem


class DuplicateCandidateOut(BaseModel):
    id: str
    existing_branch_id: str
    candidate_branch_id: str
    match_score: float
    match_reasons: List[str]
    status: str  # pending_review, confirmed_duplicate, confirmed_distinct, resolved_merged
    existing_branch: Optional[LeadListItem] = None
    candidate_branch: Optional[LeadListItem] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DuplicateResolveRequest(BaseModel):
    resolution: str  # "merge", "keep_distinct", "reject_candidate"
    notes: Optional[str] = None

