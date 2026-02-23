from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.modules.certificates.models import Certificate
from app.modules.certificates.schemas import CertificateResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("/verify/{certificate_id}", response_model=CertificateResponse)
def verify_certificate(
    certificate_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CertificateResponse:
    """Public endpoint to verify certificate validity without authentication"""
    _ = current_user  # optional dependency retained for audit/telemetry hooks
    certificate = db.scalar(
        select(Certificate).where(
            Certificate.id == certificate_id,
            Certificate.is_revoked.is_(False),
        )
    )
    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found or invalid")
    return CertificateResponse(
        id=certificate.id,
        certificate_number=certificate.certificate_number,
        student_id=certificate.student_id,
        course_id=certificate.course_id,
        completion_date=certificate.completion_date,
        issued_at=certificate.issued_at,
        pdf_url=f"/certificates/{certificate.id}/download",
        is_revoked=certificate.is_revoked,
    )
