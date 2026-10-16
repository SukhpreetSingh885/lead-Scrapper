from celery import Celery
from app.core.config import settings

celery = Celery(
    "india_leads_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.discovery_tasks",
        "app.workers.tasks.enrichment_tasks",
        "app.workers.tasks.export_tasks",
    ]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,       # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    # Support immediate execution for local testing / zero-credential setups
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
)

