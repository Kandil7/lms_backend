from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.email_tasks.send_welcome_email")
def send_welcome_email(email: str, full_name: str) -> str:
    return f"welcome email queued for {full_name} <{email}>"
