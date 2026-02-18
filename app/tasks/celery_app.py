from celery import Celery

from app.core.config import settings
from app.core.model_registry import load_all_models

load_all_models()

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

celery_app.conf.task_routes = {
    "app.tasks.email_tasks.*": {"queue": "emails"},
    "app.tasks.progress_tasks.*": {"queue": "progress"},
    "app.tasks.certificate_tasks.*": {"queue": "certificates"},
}
