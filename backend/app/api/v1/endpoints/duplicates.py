from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models import User
from app.schemas.duplicate import DuplicateCandidateOut, DuplicateResolveRequest
from app.schemas.common import PaginatedResponse, MessageResponse
from app.repositories.duplicate_repo import DuplicateRepository
from app.services.deduplication.resolver import DeduplicationResolver

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DuplicateCandidateOut])
def list_duplicate_candidates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = DuplicateRepository(db)
    items, total = repo.get_pending_duplicates_paginated(page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/{candidate_id}/resolve", response_model=MessageResponse)
def resolve_duplicate_candidate(
    candidate_id: str,
    resolve_in: DuplicateResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if resolve_in.resolution not in ("merge", "keep_distinct", "reject_candidate"):
        raise HTTPException(
            status_code=400,
            detail="Invalid resolution. Must be 'merge', 'keep_distinct', or 'reject_candidate'."
        )

    resolver = DeduplicationResolver(db)
    success = resolver.resolve_candidate(
        candidate_id=candidate_id,
        resolution=resolve_in.resolution,
        user_id=current_user.id,
        notes=resolve_in.notes
    )

    if not success:
        raise HTTPException(status_code=404, detail="Duplicate candidate not found")

    return MessageResponse(
        message=f"Duplicate candidate successfully resolved as '{resolve_in.resolution}'."
    )

