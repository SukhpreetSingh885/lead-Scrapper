import asyncio
import json
import logging
from datetime import datetime, timezone
from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.core.config import settings
from app.models import DiscoveryJob, DiscoveryJobItem, Branch
from app.services.discovery import (
    DemoDiscoveryProvider,
    GooglePlacesDiscoveryProvider,
    GoogleSearchDiscoveryProvider,
)
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.enrichment.website_enricher import WebsiteEnrichmentEngine

logger = logging.getLogger(__name__)


def run_async(coro):
    """Utility to run an async coroutine inside a synchronous Celery task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        # In case loop is already running (e.g. in some async runners)
        import nest_asyncio
        nest_asyncio.apply()
    return loop.run_until_complete(coro)


@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def execute_discovery_job(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if not job:
            logger.error(f"Discovery job {job_id} not found.")
            return {"error": "Job not found"}

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Parse filters
        filters = {}
        if job.filters_json:
            try:
                filters = json.loads(job.filters_json)
            except Exception:
                pass

        # Select provider based on source_code and configuration
        provider = None
        source_code = job.source_code

        if source_code == "google_places":
            places_p = GooglePlacesDiscoveryProvider()
            if places_p.is_configured:
                provider = places_p
            else:
                job.status = "failed"
                job.error_message = (
                    "No live discovery provider configured. "
                    "Configure an authorized Google Places API key or use demo / licensed import mode."
                )
                db.commit()
                return {"error": job.error_message}

        elif source_code == "google_search":
            search_p = GoogleSearchDiscoveryProvider()
            if search_p.is_configured:
                provider = search_p
            else:
                job.status = "failed"
                job.error_message = "Google Custom Search is not configured."
                db.commit()
                return {"error": job.error_message}

        else:
            # Default or demo_fixture
            provider = DemoDiscoveryProvider()

        # Execute discovery search
        discovered_items = run_async(
            provider.search(
                location=job.resolved_city,
                category=job.category,
                max_results=job.max_leads,
                filters=filters
            )
        )

        job.total_discovered = len(discovered_items)
        db.commit()

        resolver = DeduplicationResolver(db)
        enricher = WebsiteEnrichmentEngine(db)

        inserted_count = 0
        updated_count = 0
        dup_flagged_count = 0
        eligible_count = 0
        failed_count = 0
        saved_branches = []

        for item in discovered_items:
            # Record item in discovery_job_items table
            job_item = DiscoveryJobItem(
                job_id=job.id,
                external_id=item.external_id,
                raw_payload=json.dumps(item.raw_payload) if item.raw_payload else None,
                business_name=item.business_name,
                address=item.address_line,
                phone=item.phone,
                website=item.website_url,
                is_eligible_for_crm=item.is_eligible_for_crm,
                rejection_reason=item.rejection_reason
            )
            db.add(job_item)
            db.flush()

            if not item.is_eligible_for_crm:
                # E.g. Google Places preview item: Compliant temporary preview only, not saved to permanent CRM
                continue

            # Check user filters
            if filters.get("must_have_phone") and not item.phone:
                continue
            if filters.get("must_have_website") and not item.website_url:
                continue

            eligible_count += 1

            # Process through global duplicate resolution across database
            try:
                branch, action = resolver.process_discovered_lead(item, job.organization_id)
                if action == "inserted":
                    inserted_count += 1
                    if branch:
                        saved_branches.append(branch)
                elif action == "updated":
                    updated_count += 1
                    if branch:
                        saved_branches.append(branch)
                elif action == "flagged_duplicate":
                    dup_flagged_count += 1
                elif action == "rejected_license":
                    failed_count += 1
            except Exception as e:
                logger.exception(f"Error processing lead item {item.business_name}: {e}")
                failed_count += 1

        # Enrich newly saved branches that have a website
        for branch in saved_branches:
            if branch.website_url and branch.enrichment_status == "pending":
                try:
                    run_async(enricher.enrich_branch(branch.id))
                except Exception as e:
                    logger.debug(f"Auto-enrichment skipped/failed for branch {branch.id}: {e}")

        # Update final job state
        job.total_eligible = eligible_count
        job.total_inserted = inserted_count
        job.total_updated = updated_count
        job.total_duplicates_flagged = dup_flagged_count
        job.total_failed = failed_count
        job.status = "completed" if failed_count == 0 else "partially_completed"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "job_id": job.id,
            "status": job.status,
            "discovered": job.total_discovered,
            "inserted": inserted_count,
            "updated": updated_count,
            "duplicates": dup_flagged_count
        }

    except Exception as exc:
        db.rollback()
        logger.exception(f"Failed discovery job {job_id}: {exc}")
        job = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()

