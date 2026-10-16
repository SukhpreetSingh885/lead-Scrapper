import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, Branch, Company
from app.schemas.lead import (
    LeadListItem,
    LeadBranchDetail,
    LeadUpdate,
    LeadFilterParams
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.repositories.lead_repo import LeadRepository
from app.services.discovery.licensed_import import LicensedImportService
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.enrichment.website_enricher import WebsiteEnrichmentEngine

router = APIRouter()


@router.get("", response_model=PaginatedResponse[LeadListItem])
def list_leads(
    city: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    has_phone: Optional[bool] = None,
    has_mobile: Optional[bool] = None,
    has_email: Optional[bool] = None,
    has_website: Optional[bool] = None,
    has_whatsapp: Optional[bool] = None,
    enrichment_status: Optional[str] = None,
    is_demo: Optional[bool] = None,
    query: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    params = LeadFilterParams(
        city=city,
        state=state,
        category=category,
        has_phone=has_phone,
        has_mobile=has_mobile,
        has_email=has_email,
        has_website=has_website,
        has_whatsapp=has_whatsapp,
        enrichment_status=enrichment_status,
        is_demo=is_demo,
        query=query,
        page=page,
        page_size=page_size
    )

    repo = LeadRepository(db)
    items, total = repo.get_leads_paginated(
        org_id=current_user.organization_id,
        filters=params
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/metrics/dashboard")
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = LeadRepository(db)
    return repo.get_dashboard_metrics(org_id=current_user.organization_id)


@router.get("/{lead_id}", response_model=LeadBranchDetail)
def get_lead_detail(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = LeadRepository(db)
    lead = repo.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadBranchDetail)
def update_lead(
    lead_id: str,
    update_data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    branch = db.query(Branch).filter(Branch.id == lead_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Lead not found")

    if update_data.branch_name is not None:
        branch.branch_name = update_data.branch_name
    if update_data.address_line is not None:
        branch.address_line = update_data.address_line
    if update_data.locality is not None:
        branch.locality = update_data.locality
    if update_data.city is not None:
        branch.city = update_data.city
    if update_data.district is not None:
        branch.district = update_data.district
    if update_data.state is not None:
        branch.state = update_data.state
    if update_data.pincode is not None:
        branch.pincode = update_data.pincode
    if update_data.website_url is not None:
        branch.website_url = update_data.website_url
    if update_data.category is not None and branch.company:
        branch.company.primary_category = update_data.category

    db.commit()
    repo = LeadRepository(db)
    return repo.get_lead_by_id(lead_id)


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_licensed_leads(
    file: UploadFile = File(...),
    license_name: str = Form(default="Verified Commercial Lead License"),
    permitted_usage: str = Form(default="Permitted Storage, Enrichment & Export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Imports licensed CSV or XLSX business records into the CRM.
    Enforces required field validation, records provenance, and runs duplicate detection.
    """
    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".csv"):
        items = LicensedImportService.parse_csv(content, license_name, permitted_usage)
    elif filename.endswith((".xlsx", ".xls")):
        items = LicensedImportService.parse_xlsx(content, license_name, permitted_usage)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a .csv or .xlsx file."
        )

    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid business records found in the uploaded file."
        )

    resolver = DeduplicationResolver(db)
    inserted = 0
    updated = 0
    duplicates = 0

    for item in items:
        try:
            branch, action = resolver.process_discovered_lead(item, current_user.organization_id)
            if action == "inserted":
                inserted += 1
            elif action == "updated":
                updated += 1
            elif action == "flagged_duplicate":
                duplicates += 1
        except Exception:
            continue

    return {
        "success": True,
        "filename": file.filename,
        "total_parsed": len(items),
        "inserted": inserted,
        "updated": updated,
        "duplicates_flagged": duplicates,
        "license": license_name
    }


@router.post("/{lead_id}/enrich")
async def enrich_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers website contact enrichment for a branch against its public business website.
    """
    engine = WebsiteEnrichmentEngine(db)
    result = await engine.enrich_branch(lead_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Enrichment failed"))
    return result

