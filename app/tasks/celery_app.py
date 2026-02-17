from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "lms_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.task_routes = {
    "app.tasks.email_tasks.*": {"queue": "emails"},
    "app.tasks.progress_tasks.*": {"queue": "progress"},
    "app.tasks.certificate_tasks.*": {"queue": "certificates"},
}
