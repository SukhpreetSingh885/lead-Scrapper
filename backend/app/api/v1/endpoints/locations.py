from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.location_repo import LocationRepository
from app.schemas.location import LocationSuggestion, LocationValidationResult

router = APIRouter()


@router.get("", response_model=List[LocationSuggestion])
def get_location_suggestions(
    q: Optional[str] = Query(default="", min_length=0, max_length=100),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Autocomplete endpoint for India-only cities, localities, districts, and PIN codes.
    """
    repo = LocationRepository(db)
    return repo.suggest_locations(q, limit=limit)


@router.get("/validate", response_model=LocationValidationResult)
def validate_location(
    location: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Validates that a location string is within India and resolves city/state.
    """
    repo = LocationRepository(db)
    return repo.validate_indian_location(location)

