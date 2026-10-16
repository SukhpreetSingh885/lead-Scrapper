import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload

from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.models import Export, Branch, Company, BusinessContact
from app.services.exports.csv_export import CsvExportService
from app.services.exports.excel_export import ExcelExportService

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def execute_export_generation(self, export_id: str):
    db = SessionLocal()
    try:
        export_record = db.query(Export).filter(Export.id == export_id).first()
        if not export_record:
            return {"error": "Export record not found"}

        export_record.status = "processing"
        db.commit()

        # Parse filter criteria
        filters = {}
        if export_record.filter_criteria:
            try:
                filters = json.loads(export_record.filter_criteria)
            except Exception:
                pass

        # Query eligible unique leads (ensuring provider compliance: only permitted CRM records)
        query = db.query(Branch).join(Company).options(
            joinedload(Branch.company),
            joinedload(Branch.contacts),
            joinedload(Branch.social_profiles),
            joinedload(Branch.source)
        ).filter(
            Branch.is_active == True,
            Branch.source_permission_status == "permitted_storage"
        )

        selected_ids = filters.get("selected_ids")
        if selected_ids:
            query = query.filter(Branch.id.in_(selected_ids))
        else:
            if filters.get("city"):
                query = query.filter(Branch.city.ilike(f"%{filters['city'].strip()}%"))
            if filters.get("state"):
                query = query.filter(Branch.state.ilike(f"%{filters['state'].strip()}%"))
            if filters.get("category"):
                query = query.filter(Company.primary_category.ilike(f"%{filters['category'].strip()}%"))
            if filters.get("has_mobile"):
                query = query.filter(Branch.contacts.any(BusinessContact.contact_type == "mobile"))
            if filters.get("has_email"):
                query = query.filter(Branch.contacts.any(BusinessContact.contact_type == "email"))

        branches = query.order_by(Branch.created_at.desc()).all()

        # Prepare export output directory
        export_dir = Path("./exports_data")
        export_dir.mkdir(parents=True, exist_ok=True)

        filename = f"leads_export_{export_record.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_record.file_format}"
        file_path = export_dir / filename

        if export_record.file_format == "xlsx":
            content_bytes = ExcelExportService.generate_xlsx_bytes(branches)
            with open(file_path, "wb") as f:
                f.write(content_bytes)
        else:
            content_bytes = CsvExportService.generate_csv_bytes(branches)
            with open(file_path, "wb") as f:
                f.write(content_bytes)

        export_record.status = "ready"
        export_record.file_path = str(file_path)
        export_record.row_count = len(branches)
        export_record.file_size_bytes = len(content_bytes)
        db.commit()

        return {
            "export_id": export_record.id,
            "status": "ready",
            "row_count": len(branches),
            "file_size": len(content_bytes)
        }

    except Exception as exc:
        db.rollback()
        logger.exception(f"Export generation failed for {export_id}: {exc}")
        record = db.query(Export).filter(Export.id == export_id).first()
        if record:
            record.status = "failed"
            record.error_message = str(exc)
            db.commit()
        return {"error": str(exc)}
    finally:
        db.close()

