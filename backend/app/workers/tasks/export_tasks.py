import os
import re
import json
import logging
import zipfile
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Set
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.models import Export, Branch, Company, BusinessContact
from app.services.exports.csv_export import CsvExportService
from app.services.exports.excel_export import ExcelExportService
from app.services.enrichment.phone_extractor import IndianPhoneExtractor

logger = logging.getLogger(__name__)

ODBL_LICENSING_NOTICE = """================================================================================
INDIA LEADS PLATFORM — DATA LICENSING & ATTRIBUTION NOTICE
================================================================================

Data Source:
  OpenStreetMap Contributors (https://www.openstreetmap.org)

License:
  Open Database License (ODbL) 1.0
  https://opendatacommons.org/licenses/odbl/1.0/

Copyright Notice:
  (C) OpenStreetMap contributors
  https://www.openstreetmap.org/copyright

Platform:
  India Leads Platform — Permitted Business Lead Engine

Permitted Usage:
  Commercial & non-commercial B2B lead discovery, CRM contact management,
  address verification, and local business outreach.

ODbL Attribution Requirement:
  Any public redistribution, derivative database, or public-facing application
  utilizing this data must prominently attribute OpenStreetMap contributors
  under the terms of Open Database License (ODbL) 1.0.
================================================================================
"""


def category_to_slug(category: Optional[str]) -> str:
    """
    Converts category name to a clean, canonical filename slug.
    e.g. 'Hospital' -> 'hospital', 'Dental Clinic' -> 'dental_clinic', 'Pet Shop' -> 'pet_shop'
    """
    if not category:
        return "all"
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", category.strip().lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug or "lead"


def is_lead_contact_qualified(branch: Branch) -> bool:
    """
    MANDATORY EXPORT QUALIFICATION RULE:
    A lead MUST have at least ONE valid contact number:
      - Mobile Number
      - OR Phone/Landline Number
      - OR explicitly advertised WhatsApp Number.

    Rules:
      - Include a lead if any ONE of these three contact types has a valid number.
      - Exclude businesses without all three contact-number types.
      - Email alone does NOT qualify.
      - Website alone does NOT qualify.
      - Validates and normalizes Indian numbers using the phonenumbers library.
      - Never fabricates or guesses numbers.
    """
    if not branch or not branch.contacts:
        return False

    for c in branch.contacts:
        if c.contact_type in ("mobile", "landline", "phone", "whatsapp"):
            val = c.normalized_value or c.original_value
            if val and str(val).strip():
                # Verify validation through phonenumbers
                norm = IndianPhoneExtractor.normalize_phone(
                    str(val),
                    default_type=c.contact_type,
                    city_context=branch.city
                )
                if norm and norm.get("is_valid"):
                    return True
                # Direct check if pre-normalized E.164
                clean = re.sub(r"\D", "", str(val))
                if len(clean) in (10, 11, 12, 13) and (str(val).startswith("+91") or clean[0] in "6789"):
                    return True
    return False


def deduplicate_branches(branches: List[Branch]) -> List[Branch]:
    """Ensures no duplicate business branches are included in export."""
    seen_ids: Set[str] = set()
    unique_branches: List[Branch] = []
    for b in branches:
        if b.id not in seen_ids:
            seen_ids.add(b.id)
            unique_branches.append(b)
    return unique_branches


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

        export_mode = filters.get("export_mode", "single")
        target_format = filters.get("file_format") or export_record.file_format
        if target_format not in ("csv", "xlsx"):
            target_format = "xlsx"

        # Base query: CRM saved leads only (never unsaved discovery previews)
        query = db.query(Branch).join(Company).options(
            joinedload(Branch.company),
            joinedload(Branch.contacts),
            joinedload(Branch.social_profiles),
            joinedload(Branch.source)
        ).filter(
            Branch.is_active == True,
            Branch.is_archived == False,
            Branch.is_demo == False,
            Branch.source_permission_status == "permitted_storage"
        )

        # Mandatory base SQL condition: at least one potential contact number
        query = query.filter(
            Branch.contacts.any(
                (BusinessContact.contact_type.in_(["mobile", "landline", "phone", "whatsapp"])) &
                (
                    (BusinessContact.normalized_value.isnot(None) & (BusinessContact.normalized_value != "")) |
                    (BusinessContact.original_value.isnot(None) & (BusinessContact.original_value != ""))
                )
            )
        )

        if filters.get("has_mobile"):
            query = query.filter(Branch.contacts.any(BusinessContact.contact_type == "mobile"))
        if filters.get("has_email"):
            query = query.filter(Branch.contacts.any(BusinessContact.contact_type == "email"))

        # Job isolation filter
        if filters.get("job_id"):
            from app.models.job import discovery_job_leads
            query = query.join(discovery_job_leads, Branch.id == discovery_job_leads.c.branch_id).filter(
                discovery_job_leads.c.job_id == filters["job_id"]
            )

        if filters.get("city"):
            query = query.filter(Branch.city.ilike(f"%{filters['city'].strip()}%"))
        if filters.get("state"):
            query = query.filter(Branch.state.ilike(f"%{filters['state'].strip()}%"))

        # Output storage directory
        export_dir = Path("./exports_data")
        export_dir.mkdir(parents=True, exist_ok=True)

        if export_mode == "all_separate_zip":
            # Mode: Export all industries grouped into separate files and packaged into a ZIP
            raw_branches = query.order_by(Branch.created_at.desc()).all()
            # Apply deduplication and strict phonenumbers validation
            branches = [b for b in deduplicate_branches(raw_branches) if is_lead_contact_qualified(b)]

            if not branches:
                raise ValueError("No contact-qualified leads available to export across any industry.")

            # Group branches by primary category
            categorized: Dict[str, List[Branch]] = {}
            for b in branches:
                cat_name = b.company.primary_category if b.company and b.company.primary_category else "Uncategorized"
                categorized.setdefault(cat_name, []).append(b)

            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for cat_name, cat_branches in categorized.items():
                    # Rule 13: Do not generate an empty file if a category has no qualifying contact numbers
                    if not cat_branches:
                        continue
                    slug = category_to_slug(cat_name)
                    industry_filename = f"{slug}_leads.{target_format}"
                    if target_format == "xlsx":
                        cat_bytes = ExcelExportService.generate_xlsx_bytes(cat_branches)
                    else:
                        cat_bytes = CsvExportService.generate_csv_bytes(cat_branches)
                    zf.writestr(industry_filename, cat_bytes)

                # Include ODbL 1.0 attribution file
                zf.writestr("README_LICENSING.txt", ODBL_LICENSING_NOTICE.strip())

            content_bytes = zip_buf.getvalue()
            # Requirement: india_leads_by_industry.zip
            nice_filename = "india_leads_by_industry.zip"
            storage_filename = f"{export_record.id}_{nice_filename}"
            file_path = export_dir / storage_filename
            with open(file_path, "wb") as f:
                f.write(content_bytes)

            export_record.status = "ready"
            export_record.file_format = "zip"
            export_record.filename = nice_filename
            export_record.file_path = str(file_path)
            export_record.row_count = len(branches)
            export_record.file_size_bytes = len(content_bytes)
            db.commit()

            return {
                "export_id": export_record.id,
                "filename": nice_filename,
                "status": "ready",
                "row_count": len(branches),
                "file_size": len(content_bytes),
                "industries_count": len(categorized)
            }

        elif export_mode == "all_combined":
            # Mode: Export all contact-qualified leads combined in a single file
            raw_branches = query.order_by(Branch.created_at.desc()).all()
            branches = [b for b in deduplicate_branches(raw_branches) if is_lead_contact_qualified(b)]

            if not branches:
                raise ValueError("No contact-qualified leads available to export.")

            nice_filename = f"all_leads.{target_format}"
            storage_filename = f"{export_record.id}_{nice_filename}"
            file_path = export_dir / storage_filename

            if target_format == "xlsx":
                content_bytes = ExcelExportService.generate_xlsx_bytes(branches)
            else:
                content_bytes = CsvExportService.generate_csv_bytes(branches)

            with open(file_path, "wb") as f:
                f.write(content_bytes)

            export_record.status = "ready"
            export_record.file_format = target_format
            export_record.filename = nice_filename
            export_record.file_path = str(file_path)
            export_record.row_count = len(branches)
            export_record.file_size_bytes = len(content_bytes)
            db.commit()

            return {
                "export_id": export_record.id,
                "filename": nice_filename,
                "status": "ready",
                "row_count": len(branches),
                "file_size": len(content_bytes)
            }

        else:
            # Mode: Single industry or selected leads
            selected_ids = filters.get("selected_ids")
            category_filter = filters.get("category")

            if selected_ids:
                query = query.filter(Branch.id.in_(selected_ids))
                nice_filename = f"selected_leads.{target_format}"
            elif category_filter:
                query = query.filter(func.lower(Company.primary_category) == category_filter.strip().lower())
                slug = category_to_slug(category_filter)
                nice_filename = f"{slug}_leads.{target_format}"
            else:
                nice_filename = f"all_leads.{target_format}"

            raw_branches = query.order_by(Branch.created_at.desc()).all()
            branches = [b for b in deduplicate_branches(raw_branches) if is_lead_contact_qualified(b)]

            # Rule 13: If a category has no qualifying contact numbers, do not generate an empty file.
            if not branches:
                if category_filter:
                    raise ValueError(
                        f"Category '{category_filter}' has 0 contact-qualified leads with valid contact numbers. "
                        f"Exports require at least one valid Mobile, Landline, or WhatsApp number."
                    )
                elif selected_ids:
                    raise ValueError(
                        "None of the selected leads have a valid contact number (Mobile, Landline, or WhatsApp). "
                        "Exports require at least one valid contact number."
                    )

            storage_filename = f"{export_record.id}_{nice_filename}"
            file_path = export_dir / storage_filename

            if target_format == "xlsx":
                content_bytes = ExcelExportService.generate_xlsx_bytes(branches)
            else:
                content_bytes = CsvExportService.generate_csv_bytes(branches)

            with open(file_path, "wb") as f:
                f.write(content_bytes)

            export_record.status = "ready"
            export_record.file_format = target_format
            export_record.filename = nice_filename
            export_record.file_path = str(file_path)
            export_record.row_count = len(branches)
            export_record.file_size_bytes = len(content_bytes)
            db.commit()

            return {
                "export_id": export_record.id,
                "filename": nice_filename,
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
