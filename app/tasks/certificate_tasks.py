from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.certificate_tasks.generate_certificate")
def generate_certificate(enrollment_id: str) -> str:
    return f"certificate generation queued for enrollment {enrollment_id}"
