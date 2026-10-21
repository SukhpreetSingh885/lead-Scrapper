import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload

from app.models import DiscoveryJob, DiscoveryJobItem, EnrichmentJob, Organization
from app.models.job import discovery_job_leads
from app.schemas.job import DiscoveryJobCreate, DiscoveryJobOut, DiscoveryJobItemOut


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_discovery_job(
        self,
        job_in: DiscoveryJobCreate,
        resolved_city: str,
        resolved_state: str,
        org_id: str,
        source_code: str
    ) -> DiscoveryJob:
        filters_dict = {
            "must_have_phone": job_in.must_have_phone,
            "must_have_mobile": job_in.must_have_mobile,
            "must_have_email": job_in.must_have_email,
            "must_have_website": job_in.must_have_website,
            "must_have_whatsapp": job_in.must_have_whatsapp,
            "exclude_already_saved": job_in.exclude_already_saved
        }
        if getattr(job_in, "radius_km", None):
            filters_dict["radius_meters"] = int(job_in.radius_km) * 1000
        if getattr(job_in, "locations", None):
            filters_dict["locations"] = job_in.locations
        elif "," in resolved_city:
            filters_dict["locations"] = [c.strip() for c in resolved_city.split(",") if c.strip()]

        job = DiscoveryJob(
            organization_id=org_id,
            location_input=job_in.location,
            resolved_city=resolved_city,
            resolved_state=resolved_state,
            category=job_in.category,
            max_leads=job_in.max_leads,
            source_code=source_code,
            filters_json=json.dumps(filters_dict),
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job_by_id(self, job_id: str) -> Optional[DiscoveryJob]:
        return self.db.query(DiscoveryJob).options(
            joinedload(DiscoveryJob.items)
        ).filter(DiscoveryJob.id == job_id).first()

    def list_jobs_paginated(
        self,
        org_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DiscoveryJob], int]:
        query = self.db.query(DiscoveryJob)
        if org_id:
            query = query.filter(DiscoveryJob.organization_id == org_id)

        total = query.count()
        offset = (page - 1) * page_size
        jobs = query.order_by(DiscoveryJob.created_at.desc()).offset(offset).limit(page_size).all()
        return jobs, total

    def add_job_item(
        self,
        job_id: str,
        business_name: str,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        is_eligible_for_crm: bool = True,
        rejection_reason: Optional[str] = None,
        external_id: Optional[str] = None,
        raw_payload: Optional[str] = None
    ) -> DiscoveryJobItem:
        item = DiscoveryJobItem(
            job_id=job_id,
            external_id=external_id,
            raw_payload=raw_payload,
            business_name=business_name,
            address=address,
            phone=phone,
            website=website,
            is_eligible_for_crm=is_eligible_for_crm,
            rejection_reason=rejection_reason
        )
        self.db.add(item)
        return item

    def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        discovered: int = None,
        eligible: int = None,
        inserted: int = None,
        updated: int = None,
        duplicates: int = None,
        failed: int = None
    ) -> Optional[DiscoveryJob]:
        job = self.db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if not job:
            return None

        job.status = status
        if error_message:
            job.error_message = error_message
        if discovered is not None:
            job.total_discovered = discovered
        if eligible is not None:
            job.total_eligible = eligible
        if inserted is not None:
            job.total_inserted = inserted
        if updated is not None:
            job.total_updated = updated
        if duplicates is not None:
            job.total_duplicates_flagged = duplicates
        if failed is not None:
            job.total_failed = failed

        if status in ("completed", "partially_completed", "failed", "cancelled"):
            job.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Safely deletes a search job and its temporary preview records.
        Guarantees:
        - Cancels processing if job is currently pending, queued, or running.
        - Deletes all associated temporary DiscoveryJobItem preview records.
        - Deletes entries in discovery_job_leads association table.
        - NEVER deletes permanent CRM businesses (Company, Branch, BusinessContact).
        - Respects organization ownership and handles SQLite foreign keys cleanly.
        """
        job = self.db.query(DiscoveryJob).filter(
            DiscoveryJob.id == job_id,
            DiscoveryJob.organization_id == org_id
        ).first()
        if not job:
            return None

        # 1. Safely cancel if active
        if job.status in ("pending", "queued", "running"):
            job.status = "cancelled"
            self.db.flush()

        # 2. Delete discovery_job_leads association table links
        self.db.execute(
            discovery_job_leads.delete().where(discovery_job_leads.c.job_id == job_id)
        )

        # 3. Delete all temporary preview items for this job
        self.db.query(DiscoveryJobItem).filter(
            DiscoveryJobItem.job_id == job_id
        ).delete(synchronize_session=False)

        # 4. Expire relationship to avoid double deletion warning
        self.db.expire(job, ["items"])

        # 5. Delete the discovery job itself
        deleted_info = {
            "id": job.id,
            "category": job.category,
            "city": job.resolved_city
        }
        self.db.delete(job)
        self.db.commit()
        return deleted_info

    def clear_job_preview(self, job_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Removes unsaved temporary preview results for a job without deleting the job itself.
        Guarantees:
        - Removes only DiscoveryJobItem where is_saved is False.
        - Preserves already-saved items if any.
        - Recalculates job counters (total_discovered, total_eligible, total_contact_qualified).
        - NEVER deletes permanent CRM leads.
        """
        job = self.db.query(DiscoveryJob).filter(
            DiscoveryJob.id == job_id,
            DiscoveryJob.organization_id == org_id
        ).first()
        if not job:
            return None

        # Delete only unsaved preview items
        deleted_count = self.db.query(DiscoveryJobItem).filter(
            DiscoveryJobItem.job_id == job_id,
            DiscoveryJobItem.is_saved == False
        ).delete(synchronize_session=False)

        # Recalculate remaining preview counts
        remaining_items = self.db.query(DiscoveryJobItem).filter(
            DiscoveryJobItem.job_id == job_id
        ).all()
        job.total_discovered = len(remaining_items)
        job.total_eligible = sum(1 for item in remaining_items if item.is_eligible_for_crm)
        job.total_contact_qualified = sum(
            1 for item in remaining_items if (item.phone or item.mobile or item.whatsapp)
        )

        self.db.commit()
        self.db.refresh(job)
        return {
            "id": job.id,
            "category": job.category,
            "city": job.resolved_city,
            "cleared_count": deleted_count,
            "remaining_items": len(remaining_items)
        }


