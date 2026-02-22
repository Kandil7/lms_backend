import importlib
import logging
from collections.abc import Callable

from app.core.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.tasks.dispatcher")

INLINE_TASK_MAP = {
    "app.tasks.email_tasks.send_welcome_email": "app.tasks.email_tasks:send_welcome_email",
    "app.tasks.email_tasks.send_password_reset_email": "app.tasks.email_tasks:send_password_reset_email",
    "app.tasks.email_tasks.send_email_verification_email": "app.tasks.email_tasks:send_email_verification_email",
    "app.tasks.email_tasks.send_mfa_login_code_email": "app.tasks.email_tasks:send_mfa_login_code_email",
    "app.tasks.email_tasks.send_mfa_setup_code_email": "app.tasks.email_tasks:send_mfa_setup_code_email",
    "app.tasks.progress_tasks.recalculate_course_progress": "app.tasks.progress_tasks:recalculate_course_progress",
    "app.tasks.certificate_tasks.generate_certificate": "app.tasks.certificate_tasks:generate_certificate",
    "app.tasks.webhook_tasks.dispatch_webhook_event": "app.tasks.webhook_tasks:dispatch_webhook_event",
}


def enqueue_task(task_name: str, *args, **kwargs) -> bool:
    try:
        celery_app.send_task(task_name, args=list(args), kwargs=kwargs)
        return True
    except Exception as exc:
        logger.warning("Failed to enqueue task '%s': %s", task_name, exc)
        return False


def run_task_inline(task_name: str, *args, **kwargs):
    target = INLINE_TASK_MAP.get(task_name)
    if not target:
        raise ValueError(f"No inline fallback mapped for task '{task_name}'")

    module_name, attr_name = target.rsplit(":", 1)
    module = importlib.import_module(module_name)
    task_callable = getattr(module, attr_name)
    return task_callable(*args, **kwargs)


def _run_fallback(
    task_name: str,
    *args,
    fallback: Callable[[], object] | None = None,
    **kwargs,
) -> str:
    try:
        if fallback is not None:
            fallback()
        else:
            run_task_inline(task_name, *args, **kwargs)
        return "inline"
    except Exception as exc:
        logger.exception("Task '%s' failed in inline fallback mode: %s", task_name, exc)
        return "failed"


def enqueue_task_with_fallback(
    task_name: str,
    *args,
    fallback: Callable[[], object] | None = None,
    **kwargs,
) -> str:
    if settings.TASKS_FORCE_INLINE:
        return _run_fallback(task_name, *args, fallback=fallback, **kwargs)

    if enqueue_task(task_name, *args, **kwargs):
        return "queued"

    return _run_fallback(task_name, *args, fallback=fallback, **kwargs)
