import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, Branch, Company, DiscoveryJob, DiscoveryJobItem, BusinessContact
from app.schemas.lead import (
    LeadListItem,
    LeadBranchDetail,
    LeadUpdate,
    LeadFilterParams,
    SaveSelectedLeadsRequest,
    SaveSelectedLeadsResponse,
    BulkDeleteLeadsRequest,
    DeleteLeadsResponse
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.repositories.lead_repo import LeadRepository
from app.services.discovery.base import DiscoveredLeadItem
from app.services.discovery.licensed_import import LicensedImportService
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.enrichment.website_enricher import WebsiteEnrichmentEngine

router = APIRouter()


@router.get("", response_model=PaginatedResponse[LeadListItem])
def list_leads(
    city: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    job_id: Optional[str] = None,
    has_contact_number: Optional[bool] = None,
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
        job_id=job_id,
        has_contact_number=has_contact_number,
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
    lead = repo.get_lead_by_id(lead_id, org_id=current_user.organization_id)
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
    branch = db.query(Branch).join(Company).filter(
        Branch.id == lead_id,
        Company.organization_id == current_user.organization_id
    ).first()
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
    return repo.get_lead_by_id(lead_id, org_id=current_user.organization_id)


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
    branch = db.query(Branch).join(Company).filter(
        Branch.id == lead_id,
        Company.organization_id == current_user.organization_id
    ).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Lead not found")

    engine = WebsiteEnrichmentEngine(db)
    result = await engine.enrich_branch(lead_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Enrichment failed"))
    return result


@router.post("/save-selected", response_model=SaveSelectedLeadsResponse)
async def save_selected_leads(
    req: SaveSelectedLeadsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves selected preview records or all eligible preview records from a discovery job into the permanent CRM.
    Performs data normalization, source licensing checks, global deduplication across the database,
    and updates existing records without duplication.
    """
    job = db.query(DiscoveryJob).filter(
        DiscoveryJob.id == req.job_id,
        DiscoveryJob.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Discovery job not found")

    items_query = db.query(DiscoveryJobItem).filter(DiscoveryJobItem.job_id == req.job_id)
    if req.save_all_eligible:
        items_query = items_query.filter(DiscoveryJobItem.is_eligible_for_crm == True)
    elif req.item_ids:
        items_query = items_query.filter(DiscoveryJobItem.id.in_(req.item_ids))
    else:
        raise HTTPException(status_code=400, detail="Must provide item_ids or set save_all_eligible=True")

    items = items_query.all()
    if not items:
        return SaveSelectedLeadsResponse(
            success=True,
            total_requested=0,
            saved_count=0,
            already_existing_count=0,
            skipped_count=0,
            failed_count=0,
            saved_lead_ids=[],
            message="No matching preview items found to save."
        )

    resolver = DeduplicationResolver(db)
    enricher = WebsiteEnrichmentEngine(db)

    saved_count = 0
    already_existing_count = 0
    skipped_count = 0
    failed_count = 0
    saved_branches = []

    for item in items:
        if item.is_saved and item.branch_id:
            already_existing_count += 1
            continue

        try:
            lead_data = json.loads(item.raw_payload) if item.raw_payload else {}
            lead_item = DiscoveredLeadItem(
                external_id=item.external_id or lead_data.get("external_id"),
                business_name=item.business_name,
                category=item.category or lead_data.get("category", job.category),
                address_line=item.address or lead_data.get("address_line"),
                locality=lead_data.get("locality"),
                city=item.city or lead_data.get("city", job.resolved_city),
                state=item.state or lead_data.get("state", job.resolved_state),
                pincode=lead_data.get("pincode"),
                country="India",
                phone=item.phone or item.mobile or lead_data.get("phone"),
                email=item.email or lead_data.get("email"),
                website_url=item.website or lead_data.get("website_url"),
                latitude=lead_data.get("latitude"),
                longitude=lead_data.get("longitude"),
                social_profiles=lead_data.get("social_profiles"),
                raw_payload=lead_data.get("raw_payload"),
                is_eligible_for_crm=True,
                source_code=item.source_code or lead_data.get("source_code", "overpass"),
                license_status="permitted_storage",
                is_demo=False
            )

            branch, action = resolver.process_discovered_lead(lead_item, current_user.organization_id)
            if branch:
                item.is_saved = True
                item.branch_id = branch.id

                # Link with discovery_job_leads association table
                exists_assoc = db.execute(
                    text("SELECT 1 FROM discovery_job_leads WHERE job_id = :jid AND branch_id = :bid"),
                    {"jid": job.id, "bid": branch.id}
                ).first()
                if not exists_assoc:
                    db.execute(
                        text("INSERT INTO discovery_job_leads (job_id, branch_id) VALUES (:jid, :bid)"),
                        {"jid": job.id, "bid": branch.id}
                    )

                # Persist all preview contacts with provenance to BusinessContact
                all_extracted_contacts = lead_data.get("all_contacts") or []
                if not all_extracted_contacts:
                    if item.mobile:
                        all_extracted_contacts.append({
                            "original_value": item.mobile,
                            "normalized_value": item.mobile,
                            "contact_type": "mobile",
                            "source": item.source_code or "overpass"
                        })
                    if item.phone and item.phone != item.mobile:
                        all_extracted_contacts.append({
                            "original_value": item.phone,
                            "normalized_value": item.phone,
                            "contact_type": "landline",
                            "source": item.source_code or "overpass"
                        })
                    if item.whatsapp:
                        all_extracted_contacts.append({
                            "original_value": item.whatsapp,
                            "normalized_value": item.whatsapp,
                            "contact_type": "whatsapp",
                            "source": item.source_code or "overpass"
                        })
                    if item.email:
                        all_extracted_contacts.append({
                            "original_value": item.email,
                            "normalized_value": item.email,
                            "contact_type": "email",
                            "source": item.source_code or "overpass"
                        })

                existing_contacts = db.query(BusinessContact).filter(
                    BusinessContact.branch_id == branch.id
                ).all()
                existing_keys = {(c.contact_type, c.normalized_value) for c in existing_contacts}
                has_primary = any(c.is_primary for c in existing_contacts)

                for c_info in all_extracted_contacts:
                    norm_val = c_info.get("normalized_value")
                    ctype = c_info.get("contact_type", "phone")
                    if not norm_val or (ctype, norm_val) in existing_keys:
                        continue

                    is_primary = False
                    if not has_primary and ctype in ("mobile", "landline", "phone"):
                        is_primary = True
                        has_primary = True

                    bc = BusinessContact(
                        branch_id=branch.id,
                        contact_type=ctype,
                        original_value=c_info.get("original_value") or norm_val,
                        normalized_value=norm_val,
                        is_primary=is_primary,
                        is_verified=True,
                        source=c_info.get("source", "website_enrichment" if "enrich" in str(c_info.get("evidence", "")) else "osm"),
                        source_url=c_info.get("source_url"),
                        evidence=c_info.get("evidence")
                    )
                    db.add(bc)
                    existing_keys.add((ctype, norm_val))

                if action == "inserted":
                    item.is_already_saved = False
                    saved_count += 1
                    saved_branches.append(branch)
                elif action in ("updated", "flagged_duplicate"):
                    item.is_already_saved = True
                    already_existing_count += 1
                    saved_branches.append(branch)
                elif action == "rejected_license":
                    skipped_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.exception(f"Failed to save preview item {item.id}: {e}")
            failed_count += 1

    # Accurately update job counters from actual items to avoid double-counting
    db.flush()
    job.total_inserted = db.query(DiscoveryJobItem).filter(
        DiscoveryJobItem.job_id == job.id,
        DiscoveryJobItem.is_saved == True,
        DiscoveryJobItem.is_already_saved == False
    ).count()
    job.total_updated = db.query(DiscoveryJobItem).filter(
        DiscoveryJobItem.job_id == job.id,
        DiscoveryJobItem.is_already_saved == True
    ).count()
    db.commit()

    # Asynchronously kick off enrichment for newly saved branches with website
    for branch in saved_branches:
        if branch.website_url and branch.enrichment_status == "pending":
            try:
                await enricher.enrich_branch(branch.id)
            except Exception:
                pass

    return SaveSelectedLeadsResponse(
        success=True,
        total_requested=len(items),
        saved_count=saved_count,
        already_existing_count=already_existing_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        saved_lead_ids=[b.id for b in saved_branches],
        message=f"Successfully processed {len(items)} leads: {saved_count} newly saved, {already_existing_count} linked to existing CRM records."
    )


@router.delete("/{lead_id}", response_model=MessageResponse)
def delete_single_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a single saved business lead from the CRM.
    Safely cascades through foreign keys and cleans up orphaned companies.
    """
    branch = db.query(Branch).join(Company).filter(
        Branch.id == lead_id,
        Company.organization_id == current_user.organization_id
    ).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Lead not found or unauthorized")

    company_id = branch.company_id
    db.delete(branch)
    db.flush()

    # Clean up orphaned company if no other branches remain
    remaining = db.query(Branch).filter(Branch.company_id == company_id).count()
    if remaining == 0:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            db.delete(company)

    db.commit()
    return MessageResponse(message="Lead deleted successfully.")


@router.post("/bulk-delete", response_model=DeleteLeadsResponse)
def bulk_delete_leads(
    delete_in: BulkDeleteLeadsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk deletes selected leads or all filtered leads from the CRM.
    """
    repo = LeadRepository(db)
    target_ids = []

    if delete_in.delete_all_filtered and delete_in.filters:
        target_ids = repo.get_lead_ids_by_filters(
            org_id=current_user.organization_id,
            filters=delete_in.filters
        )
    elif delete_in.lead_ids:
        target_ids = delete_in.lead_ids
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide lead_ids or specify delete_all_filtered=True with valid filters."
        )

    if not target_ids:
        return DeleteLeadsResponse(
            success=True,
            deleted_count=0,
            message="No matching saved leads found to delete."
        )

    branches = db.query(Branch).join(Company).filter(
        Branch.id.in_(target_ids),
        Company.organization_id == current_user.organization_id
    ).all()

    deleted_count = 0
    affected_company_ids = set()

    for b in branches:
        affected_company_ids.add(b.company_id)
        db.delete(b)
        deleted_count += 1

    db.flush()

    for cid in affected_company_ids:
        if db.query(Branch).filter(Branch.company_id == cid).count() == 0:
            comp = db.query(Company).filter(Company.id == cid).first()
            if comp:
                db.delete(comp)

    db.commit()
    return DeleteLeadsResponse(
        success=True,
        deleted_count=deleted_count,
        message=f"Successfully deleted {deleted_count} saved leads."
    )


