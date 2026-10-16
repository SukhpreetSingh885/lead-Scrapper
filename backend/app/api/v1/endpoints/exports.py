import os
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, Export
from app.schemas.export import ExportCreate, ExportOut
from app.workers.tasks.export_tasks import execute_export_generation

router = APIRouter()


@router.post("", response_model=ExportOut, status_code=status.HTTP_201_CREATED)
def create_export(
    export_in: ExportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    token = str(uuid.uuid4())
    filters_dict = {
        "selected_ids": export_in.selected_ids,
        "city": export_in.city,
        "state": export_in.state,
        "category": export_in.category,
        "has_mobile": export_in.has_mobile,
        "has_email": export_in.has_email,
    }

    export_record = Export(
        organization_id=current_user.organization_id,
        file_format=export_in.file_format,
        filter_criteria=json.dumps(filters_dict),
        status="pending",
        download_token=token
    )
    db.add(export_record)
    db.commit()
    db.refresh(export_record)

    # Dispatch Celery task
    try:
        execute_export_generation.delay(export_record.id)
    except Exception:
        # Fallback to direct synchronous execution if Celery broker offline
        execute_export_generation(export_record.id)

    db.refresh(export_record)
    download_url = f"/api/v1/exports/{export_record.id}/download?token={export_record.download_token}"

    out = ExportOut(
        id=export_record.id,
        file_format=export_record.file_format,
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
    record = db.query(Export).filter(Export.id == export_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Export not found")

    download_url = f"/api/v1/exports/{record.id}/download?token={record.download_token}"
    return ExportOut(
        id=record.id,
        file_format=record.file_format,
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

    media_type = "text/csv" if record.file_format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = Path(record.file_path).name

    return FileResponse(
        path=record.file_path,
        media_type=media_type,
        filename=filename
    )

