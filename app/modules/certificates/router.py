from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import Role
from app.modules.certificates.models import Certificate
from app.modules.certificates.schemas import (
    CertificateListResponse,
    CertificateResponse,
    CertificateVerifyResponse,
)
from app.modules.certificates.service import CertificateService
from app.modules.courses.models.course import Course
from app.modules.enrollments.models import Enrollment

router = APIRouter(prefix="/certificates", tags=["Certificates"])


def _to_response(certificate: Certificate) -> CertificateResponse:
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


@router.get("/my-certificates", response_model=CertificateListResponse)
def my_certificates(current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> CertificateListResponse:
    certificates = CertificateService(db).get_my_certificates(current_user.id)
    payload = [_to_response(cert) for cert in certificates]
    return CertificateListResponse(certificates=payload, total=len(payload))


@router.get("/{certificate_id}/download")
def download_certificate(
    certificate_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FastAPIFileResponse:
    service = CertificateService(db)
    certificate = service.get_certificate_for_user(certificate_id, current_user)
    path = Path(certificate.pdf_path)
    return FastAPIFileResponse(path=str(path), filename=f"{certificate.certificate_number}.pdf", media_type="application/pdf")


@router.get("/verify/{certificate_number}", response_model=CertificateVerifyResponse)
def verify_certificate(certificate_number: str, db: Session = Depends(get_db)) -> CertificateVerifyResponse:
    certificate = CertificateService(db).verify_certificate(certificate_number)
    if not certificate:
        return CertificateVerifyResponse(valid=False, certificate=None, message="Certificate not found")
    return CertificateVerifyResponse(valid=True, certificate=_to_response(certificate), message="Certificate is valid")


@router.post("/{certificate_id}/revoke", response_model=CertificateResponse)
def revoke_certificate(
    certificate_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CertificateResponse:
    certificate = CertificateService(db).revoke_certificate(certificate_id, current_user)
    return _to_response(certificate)


@router.post("/enrollments/{enrollment_id}/generate", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def generate_certificate(
    enrollment_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CertificateResponse:
    enrollment = db.scalar(select(Enrollment).where(Enrollment.id == enrollment_id))
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    is_authorized = False
    if current_user.role == Role.ADMIN.value:
        is_authorized = True
    elif current_user.role == Role.STUDENT.value and enrollment.student_id == current_user.id:
        is_authorized = True
    elif current_user.role == Role.INSTRUCTOR.value:
        owned_course = db.scalar(
            select(Course.id).where(
                Course.id == enrollment.course_id,
                Course.instructor_id == current_user.id,
            )
        )
        is_authorized = owned_course is not None

    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate certificate for this enrollment",
        )

    certificate = CertificateService(db).issue_for_enrollment(enrollment)
    if certificate is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enrollment is not complete yet")

    return _to_response(certificate)
