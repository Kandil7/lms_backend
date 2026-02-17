from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.progress_tasks.recalculate_course_progress")
def recalculate_course_progress(enrollment_id: str) -> str:
    return f"progress recalculation queued for enrollment {enrollment_id}"
