import logging
from uuid import UUID

from sqlalchemy import select

from app.core.database import session_scope
from app.modules.enrollments.models import Enrollment
from app.modules.enrollments.service import EnrollmentService
from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.tasks.progress")


@celery_app.task(name="app.tasks.progress_tasks.recalculate_course_progress")
def recalculate_course_progress(enrollment_id: str) -> str:
    try:
        enrollment_uuid = UUID(enrollment_id)
    except ValueError:
        return f"invalid enrollment id: {enrollment_id}"

    with session_scope() as db:
        enrollment = db.scalar(select(Enrollment).where(Enrollment.id == enrollment_uuid))
        if not enrollment:
            return f"enrollment not found: {enrollment_id}"

        EnrollmentService(db).recalculate_enrollment_summary(enrollment_uuid, commit=False)
        message = f"progress recalculated for enrollment {enrollment_id}"
        logger.info(message)
        return message
