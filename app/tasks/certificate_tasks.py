import logging
from uuid import UUID

from sqlalchemy import select

from app.core.database import session_scope
from app.modules.certificates.service import CertificateService
from app.modules.enrollments.models import Enrollment
from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.tasks.certificate")


@celery_app.task(name="app.tasks.certificate_tasks.generate_certificate")
def generate_certificate(enrollment_id: str) -> str:
    try:
        enrollment_uuid = UUID(enrollment_id)
    except ValueError:
        return f"invalid enrollment id: {enrollment_id}"

    with session_scope() as db:
        enrollment = db.scalar(select(Enrollment).where(Enrollment.id == enrollment_uuid))
        if not enrollment:
            return f"enrollment not found: {enrollment_id}"

        certificate = CertificateService(db).issue_for_enrollment(enrollment, commit=False)
        if certificate is None:
            return f"certificate skipped for enrollment {enrollment_id}"

        message = f"certificate generated for enrollment {enrollment_id}"
        logger.info(message)
        return message
