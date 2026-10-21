import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, DiscoveryJob
from app.schemas.job import DiscoveryJobCreate, DiscoveryJobOut, DiscoveryPreviewItemOut
from app.schemas.common import PaginatedResponse
from app.repositories.location_repo import LocationRepository
from app.repositories.job_repo import JobRepository
from app.services.discovery.google_places import GooglePlacesDiscoveryProvider
from app.workers.tasks.discovery_tasks import execute_discovery_job

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/jobs", response_model=DiscoveryJobOut, status_code=status.HTTP_201_CREATED)
def create_discovery_job(
    job_in: DiscoveryJobCreate,
    background_tasks: BackgroundTasks,
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
    is_valid, resolved_list, err_msg = loc_repo.parse_and_validate_locations(job_in.location, job_in.locations)

    if not is_valid or not resolved_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg or f"Location '{job_in.location}' is not a recognized Indian location."
        )

    resolved_cities = [c for c, _ in resolved_list]
    resolved_states = [s for _, s in resolved_list]
    resolved_city = ", ".join(resolved_cities)
    resolved_state = resolved_states[0] if len(set(resolved_states)) == 1 else ", ".join(resolved_states)

    # Sourcing validation
    source_code = job_in.source
    if source_code in ("auto", "overpass"):
        if getattr(settings, "DISCOVERY_PROVIDER", "overpass") == "overpass":
            source_code = "overpass"
        else:
            places_p = GooglePlacesDiscoveryProvider()
            if places_p.is_configured:
                source_code = "google_places"
            elif settings.DEMO_MODE:
                source_code = "demo_fixture"
            else:
                source_code = "overpass"
    elif source_code == "google_places":
        places_p = GooglePlacesDiscoveryProvider()
        if not places_p.is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No live Google Places API key configured. Use Overpass real discovery mode."
            )
    elif source_code == "demo_fixture":
        if not settings.DEMO_MODE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Demo mode is disabled in this environment. Use Overpass discovery for real business leads."
            )

    # Prevent duplicate jobs from repeated rapid clicks for exact same query if already running
    recent_duplicate = (
        db.query(DiscoveryJob)
        .filter(
            DiscoveryJob.organization_id == current_user.organization_id,
            DiscoveryJob.category == job_in.category,
            DiscoveryJob.resolved_city == resolved_city,
            DiscoveryJob.status.in_(["pending", "running"]),
        )
        .order_by(DiscoveryJob.created_at.desc())
        .first()
    )
    if recent_duplicate:
        logger.info(f"Returning existing active job {recent_duplicate.id} to prevent duplicate execution.")
        return DiscoveryJobOut.model_validate(recent_duplicate)

    job_repo = JobRepository(db)
    job = job_repo.create_discovery_job(
        job_in=job_in,
        resolved_city=resolved_city,
        resolved_state=resolved_state,
        org_id=current_user.organization_id,
        source_code=source_code
    )

    # Dispatch to background execution:
    # 1. If Celery is configured and NOT eager (real background broker active), dispatch via Celery.
    # 2. Otherwise (eager mode or local dev without Celery broker), dispatch via FastAPI BackgroundTasks.
    # This guarantees the HTTP response returns in ~15ms and prevents Next.js proxy socket timeout.
    dispatched_celery = False
    is_eager = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", True)
    if not is_eager:
        try:
            execute_discovery_job.delay(job.id)
            dispatched_celery = True
            logger.info(f"Dispatched discovery job {job.id} to Celery worker.")
        except Exception as e:
            logger.warning(f"Celery dispatch failed: {e}. Falling back to FastAPI BackgroundTasks.")
            dispatched_celery = False

    if not dispatched_celery:
        logger.info(f"Queueing discovery job {job.id} via FastAPI BackgroundTasks for prompt response.")
        background_tasks.add_task(execute_discovery_job, job.id)

    # Reload job state
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
    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Job not found")

    return DiscoveryJobOut.model_validate(job)


@router.get("/categories")
def list_categories():
    """
    Returns full extensible taxonomy of supported Indian business categories
    with OSM tag mappings and reliability metadata.
    """
    from app.services.discovery.taxonomy import CategoryTaxonomyResolver
    return CategoryTaxonomyResolver.list_all_categories()


@router.get("/categories/suggestions")
def get_category_suggestions(q: Optional[str] = Query(default="")):
    """
    Returns auto-complete category suggestions and disambiguation advice.
    """
    from app.services.discovery.taxonomy import CategoryTaxonomyResolver
    return CategoryTaxonomyResolver.get_suggestions_for_input(q)


@router.get("/jobs/{job_id}/preview", response_model=PaginatedResponse[DiscoveryPreviewItemOut])
def get_discovery_job_preview(
    job_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    must_have_phone: Optional[bool] = None,
    must_have_mobile: Optional[bool] = None,
    must_have_landline: Optional[bool] = None,
    must_have_email: Optional[bool] = None,
    must_have_website: Optional[bool] = None,
    must_have_whatsapp: Optional[bool] = None,
    exclude_already_saved: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns discovered business leads for preview WITHOUT committing them to CRM.
    Displays available contacts, source tags, and already-saved status indicators.
    """
    from app.models import DiscoveryJobItem

    job = db.query(DiscoveryJob).filter(
        DiscoveryJob.id == job_id,
        DiscoveryJob.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Discovery job not found")

    query = db.query(DiscoveryJobItem).filter(DiscoveryJobItem.job_id == job_id)

    if must_have_phone:
        query = query.filter(
            (DiscoveryJobItem.phone.isnot(None) & (DiscoveryJobItem.phone != "")) |
            (DiscoveryJobItem.mobile.isnot(None) & (DiscoveryJobItem.mobile != "")) |
            (DiscoveryJobItem.whatsapp.isnot(None) & (DiscoveryJobItem.whatsapp != ""))
        )
    if must_have_mobile:
        query = query.filter(DiscoveryJobItem.mobile.isnot(None) & (DiscoveryJobItem.mobile != ""))
    if must_have_landline:
        query = query.filter(
            DiscoveryJobItem.phone.isnot(None) &
            (DiscoveryJobItem.phone != "") &
            ((DiscoveryJobItem.mobile.is_(None)) | (DiscoveryJobItem.phone != DiscoveryJobItem.mobile))
        )
    if must_have_email:
        query = query.filter(DiscoveryJobItem.email.isnot(None) & (DiscoveryJobItem.email != ""))
    if must_have_website:
        query = query.filter(DiscoveryJobItem.website.isnot(None) & (DiscoveryJobItem.website != ""))
    if must_have_whatsapp:
        query = query.filter(DiscoveryJobItem.whatsapp.isnot(None) & (DiscoveryJobItem.whatsapp != ""))
    if exclude_already_saved:
        query = query.filter(DiscoveryJobItem.is_already_saved == False)

    total = query.count()
    items = query.order_by(DiscoveryJobItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items_out = []
    for item in items:
        has_contact = bool(item.mobile or item.phone or item.whatsapp)
        items_out.append(
            DiscoveryPreviewItemOut(
                id=item.id,
                job_id=item.job_id,
                business_name=item.business_name,
                category=item.category or job.category,
                mobile=item.mobile,
                phone=item.phone,
                whatsapp=item.whatsapp,
                email=item.email,
                website=item.website,
                address=item.address,
                city=item.city or job.resolved_city,
                state=item.state or job.resolved_state,
                source=item.source_code or "overpass",
                has_contact_number=has_contact,
                is_already_saved=item.is_already_saved,
                is_saved=item.is_saved,
                branch_id=item.branch_id,
                is_eligible_for_crm=item.is_eligible_for_crm,
                created_at=item.created_at
            )
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        items=items_out,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.delete("/jobs/{job_id}")
def delete_discovery_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Safely deletes an unwanted search discovery job and its temporary preview records.
    Ownership check: Job must belong to current user's organization.
    Guarantees:
    - Deletes all associated temporary preview records (DiscoveryJobItem).
    - Safely cancels the job if it is currently pending, queued, or running.
    - NEVER deletes permanent CRM leads (Branch, Company, BusinessContact).
    - Handles SQLite foreign keys cleanly without cascade failure.
    """
    job_repo = JobRepository(db)
    deleted_info = job_repo.delete_job(job_id=job_id, org_id=current_user.organization_id)
    if not deleted_info:
        raise HTTPException(status_code=404, detail="Discovery job not found")

    return {
        "success": True,
        "message": f"Search job '{deleted_info['category']} in {deleted_info['city']}' and its preview records have been deleted.",
        "deleted_job_id": job_id
    }


@router.delete("/jobs/{job_id}/preview")
def clear_discovery_job_preview(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clears temporary unsaved preview records for a search job without deleting the job.
    Ownership check: Job must belong to current user's organization.
    Guarantees:
    - Removes only unsaved DiscoveryJobItem records.
    - Recalculates job preview counters.
    - NEVER deletes permanent CRM leads.
    """
    job_repo = JobRepository(db)
    result = job_repo.clear_job_preview(job_id=job_id, org_id=current_user.organization_id)
    if not result:
        raise HTTPException(status_code=404, detail="Discovery job not found")

    return {
        "success": True,
        "message": f"Removed {result['cleared_count']} unsaved preview leads for '{result['category']} in {result['city']}'.",
        "job_id": job_id,
        "cleared_count": result["cleared_count"],
        "remaining_items": result["remaining_items"]
    }


