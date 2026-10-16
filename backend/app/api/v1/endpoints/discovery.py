import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, DiscoveryJob
from app.schemas.job import DiscoveryJobCreate, DiscoveryJobOut
from app.schemas.common import PaginatedResponse
from app.repositories.location_repo import LocationRepository
from app.repositories.job_repo import JobRepository
from app.services.discovery.google_places import GooglePlacesDiscoveryProvider
from app.workers.tasks.discovery_tasks import execute_discovery_job

router = APIRouter()


@router.post("/jobs", response_model=DiscoveryJobOut, status_code=status.HTTP_201_CREATED)
def create_discovery_job(
    job_in: DiscoveryJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    1. Validates that the location is strictly within India.
    2. Validates configured data source.
    3. Creates background search job.
    4. Triggers background discovery pipeline.
    """
    loc_repo = LocationRepository(db)
    val_res = loc_repo.validate_indian_location(job_in.location)

    if not val_res.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=val_res.message or f"Location '{job_in.location}' is not a recognized Indian location."
        )

    resolved_city = val_res.resolved_city or job_in.location.title()
    resolved_state = val_res.resolved_state or "India"

    # Sourcing validation
    source_code = job_in.source
    if source_code == "auto":
        places_p = GooglePlacesDiscoveryProvider()
        if places_p.is_configured:
            source_code = "google_places"
        else:
            source_code = "demo_fixture"
    elif source_code == "google_places":
        places_p = GooglePlacesDiscoveryProvider()
        if not places_p.is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No live discovery provider configured. Configure an authorized Google Places API key or use demo mode."
            )

    job_repo = JobRepository(db)
    job = job_repo.create_discovery_job(
        job_in=job_in,
        resolved_city=resolved_city,
        resolved_state=resolved_state,
        org_id=current_user.organization_id,
        source_code=source_code
    )

    # Dispatch Celery task
    try:
        execute_discovery_job.delay(job.id)
    except Exception as e:
        # Fallback to direct synchronous execution if Celery broker is offline
        execute_discovery_job(job.id)

    # Reload job with items
    db.refresh(job)
    return DiscoveryJobOut.model_validate(job)


@router.get("/jobs", response_model=PaginatedResponse[DiscoveryJobOut])
def list_discovery_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job_repo = JobRepository(db)
    jobs, total = job_repo.list_jobs_paginated(
        org_id=current_user.organization_id,
        page=page,
        page_size=page_size
    )
    items_out = [DiscoveryJobOut.model_validate(j) for j in jobs]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items_out,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/jobs/{job_id}", response_model=DiscoveryJobOut)
def get_discovery_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job_repo = JobRepository(db)
    job = job_repo.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return DiscoveryJobOut.model_validate(job)

