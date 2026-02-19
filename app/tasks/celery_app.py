from celery import Celery

from app.core.config import settings
from app.core.model_registry import load_all_models
from app.core.observability import init_sentry_for_celery

load_all_models()
init_sentry_for_celery()

celery_app = Celery(
    "lms_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.progress_tasks",
        "app.tasks.certificate_tasks",
    ],
)

celery_app.conf.update(
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.progress_tasks.*": {"queue": "progress"},
        "app.tasks.certificate_tasks.*": {"queue": "certificates"},
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_default_retry_delay=5,
    task_time_limit=300,
    task_soft_time_limit=240,
)
