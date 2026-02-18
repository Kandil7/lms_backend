import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.tasks.email")


@celery_app.task(name="app.tasks.email_tasks.send_welcome_email")
def send_welcome_email(email: str, full_name: str) -> str:
    message = f"welcome email processed for {full_name} <{email}>"
    logger.info(message)
    return message
