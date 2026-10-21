import os
import json
import uuid
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, Export, Branch, Company, BusinessContact
from app.schemas.export import ExportCreate, ExportOut, IndustryExportOption
from app.workers.tasks.export_tasks import execute_export_generation, category_to_slug

router = APIRouter()


@router.get("/industries", response_model=List[IndustryExportOption])
def get_export_industries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dynamically returns all distinct business categories present in saved CRM leads,
    along with their total lead counts and contact-qualified lead counts.
    Strictly excludes unsaved discovery previews.
    Contact-qualified condition: Mobile OR Phone/Landline OR advertised WhatsApp.
    """
    results = (
        db.query(
            Company.primary_category,
            func.count(Branch.id).label("total"),
            func.count(func.distinct(BusinessContact.branch_id)).label("qualified")
        )
        .join(Company, Branch.company_id == Company.id)
        .outerjoin(
            BusinessContact,
            (BusinessContact.branch_id == Branch.id) &
            (BusinessContact.contact_type.in_(["mobile", "landline", "phone", "whatsapp"])) &
            (
                (BusinessContact.normalized_value.isnot(None) & (BusinessContact.normalized_value != "")) |
                (BusinessContact.original_value.isnot(None) & (BusinessContact.original_value != ""))
            )
        )
        .filter(
            Branch.is_active == True,
            Branch.is_archived == False,
            Branch.is_demo == False,
            Branch.source_permission_status == "permitted_storage"
        )
        .group_by(Company.primary_category)
        .order_by(
            func.count(func.distinct(BusinessContact.branch_id)).desc(),
            func.count(Branch.id).desc()
        )
        .all()
    )

    out: List[IndustryExportOption] = []
    for cat, total, qual in results:
        if cat and cat.strip():
            clean_cat = cat.strip()
            out.append(
                IndustryExportOption(
                    category=clean_cat,
                    slug=category_to_slug(clean_cat),
                    total_leads=total,
                    qualified_leads=qual,
                )
            )
    return out


@router.post("", response_model=ExportOut, status_code=status.HTTP_201_CREATED)
def create_export(
    export_in: ExportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    token = str(uuid.uuid4())
    filters_dict = {
        "file_format": export_in.file_format,
        "export_mode": export_in.export_mode,
        "selected_ids": export_in.selected_ids,
        "city": export_in.city,
        "state": export_in.state,
        "category": export_in.category,
        "job_id": export_in.job_id,
        "has_contact_number": export_in.has_contact_number,
        "contact_qualified": export_in.contact_qualified,
        "has_mobile": export_in.has_mobile,
        "has_email": export_in.has_email,
    }

    initial_format = "zip" if export_in.export_mode == "all_separate_zip" else export_in.file_format

    export_record = Export(
        organization_id=current_user.organization_id,
        file_format=initial_format,
        filter_criteria=json.dumps(filters_dict),
        status="pending",
        download_token=token
    )
    db.add(export_record)
    db.commit()
    db.refresh(export_record)

    # Dispatch task
    try:
        execute_export_generation.delay(export_record.id)
    except Exception:
        execute_export_generation(export_record.id)

    db.refresh(export_record)
    download_url = f"/api/v1/exports/{export_record.id}/download?token={export_record.download_token}"

    out = ExportOut(
        id=export_record.id,
        file_format=export_record.file_format,
        filename=export_record.filename,
        row_count=export_record.row_count,
        file_size_bytes=export_record.file_size_bytes,
        status=export_record.status,
        download_url=download_url,
        error_message=export_record.error_message,
        created_at=export_record.created_at
    )
    return out


@router.get("/{export_id}", response_model=ExportOut)
def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(Export).filter(
        Export.id == export_id,
        Export.organization_id == current_user.organization_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Export not found")

    download_url = f"/api/v1/exports/{record.id}/download?token={record.download_token}"
    return ExportOut(
        id=record.id,
        file_format=record.file_format,
        filename=record.filename,
        row_count=record.row_count,
        file_size_bytes=record.file_size_bytes,
        status=record.status,
        download_url=download_url,
        error_message=record.error_message,
        created_at=record.created_at
    )


@router.get("/{export_id}/download")
def download_export_file(
    export_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    record = db.query(Export).filter(
        Export.id == export_id,
        Export.download_token == token
    ).first()

    if not record or not record.file_path or not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="Export file not found or expired")

    if record.file_format == "zip" or (record.filename and record.filename.endswith(".zip")):
        media_type = "application/zip"
    elif record.file_format == "csv" or (record.filename and record.filename.endswith(".csv")):
        media_type = "text/csv"
    else:
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    filename = record.filename or Path(record.file_path).name

    return FileResponse(
        path=record.file_path,
        media_type=media_type,
        filename=filename
    )
