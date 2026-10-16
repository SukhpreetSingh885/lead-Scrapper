import asyncio
import logging
from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.services.enrichment.website_enricher import WebsiteEnrichmentEngine

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=1, default_retry_delay=5)
def execute_website_enrichment(self, branch_id: str):
    db = SessionLocal()
    try:
        engine = WebsiteEnrichmentEngine(db)
        loop = asyncio.get_event_loop() if not asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
        res = loop.run_until_complete(engine.enrich_branch(branch_id))
        return res
    except Exception as exc:
        logger.exception(f"Enrichment task error for branch {branch_id}: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()

