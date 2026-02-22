from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.core.webhooks import emit_webhook_event
from app.modules.certificates.models import Certificate
from app.modules.courses.models.course import Course
from app.modules.users.models import User


class CertificateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def issue_for_enrollment(self, enrollment, commit: bool = True) -> Certificate | None:
        if enrollment.status != "completed":
            return None

        existing = self.db.scalar(select(Certificate).where(Certificate.enrollment_id == enrollment.id))
        if existing:
            return existing

        student = self.db.scalar(select(User).where(User.id == enrollment.student_id))
        course = self.db.scalar(select(Course).where(Course.id == enrollment.course_id))
        if not student or not course:
            raise NotFoundException("Certificate dependencies are missing")

        completion_date = enrollment.completed_at or datetime.now(UTC)
        certificate_number = self._generate_certificate_number()

        certificates_dir = Path(settings.CERTIFICATES_DIR)
        certificates_dir.mkdir(parents=True, exist_ok=True)

        pdf_filename = f"{certificate_number}.pdf"
        pdf_path = certificates_dir / pdf_filename
        self._generate_pdf(
            output_path=pdf_path,
            certificate_number=certificate_number,
            student_name=student.full_name,
            course_title=course.title,
            completion_date=completion_date,
        )

        certificate = Certificate(
            enrollment_id=enrollment.id,
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
            certificate_number=certificate_number,
            pdf_path=pdf_path.as_posix(),
            completion_date=completion_date,
            issued_at=datetime.now(UTC),
            is_revoked=False,
        )

        enrollment.certificate_issued_at = datetime.now(UTC)

        self.db.add(certificate)
        self.db.add(enrollment)
        self.db.flush()
        self.db.refresh(certificate)

        if commit:
            self.db.commit()
            emit_webhook_event(
                "certificate.issued",
                {
                    "certificate_id": str(certificate.id),
                    "certificate_number": certificate.certificate_number,
                    "enrollment_id": str(certificate.enrollment_id),
                    "student_id": str(certificate.student_id),
                    "course_id": str(certificate.course_id),
                    "issued_at": certificate.issued_at.isoformat() if certificate.issued_at else None,
                },
            )

        return certificate

    def get_my_certificates(self, student_id):
        stmt = (
            select(Certificate)
            .where(Certificate.student_id == student_id, Certificate.is_revoked.is_(False))
            .order_by(Certificate.issued_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_certificate_for_user(self, certificate_id, current_user) -> Certificate:
        certificate = self.db.scalar(select(Certificate).where(Certificate.id == certificate_id))
        if not certificate:
            raise NotFoundException("Certificate not found")

        if current_user.role == Role.ADMIN.value:
            return certificate

        if current_user.role == Role.STUDENT.value and certificate.student_id == current_user.id:
            return certificate

        raise ForbiddenException("Not authorized to access this certificate")

    def verify_certificate(self, certificate_number: str) -> Certificate | None:
        return self.db.scalar(
            select(Certificate).where(
                Certificate.certificate_number == certificate_number,
                Certificate.is_revoked.is_(False),
            )
        )

    def revoke_certificate(self, certificate_id, current_user) -> Certificate:
        if current_user.role != Role.ADMIN.value:
            raise ForbiddenException("Only admins can revoke certificates")

        certificate = self.db.scalar(select(Certificate).where(Certificate.id == certificate_id))
        if not certificate:
            raise NotFoundException("Certificate not found")

        certificate.is_revoked = True
        certificate.revoked_at = datetime.now(UTC)
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        return certificate

    @staticmethod
    def _generate_certificate_number() -> str:
        date_part = datetime.now(UTC).strftime("%Y%m%d")
        random_part = uuid4().hex[:6].upper()
        return f"CERT-{date_part}-{random_part}"

    @staticmethod
    def _generate_pdf(
        *,
        output_path: Path,
        certificate_number: str,
        student_name: str,
        course_title: str,
        completion_date: datetime,
    ) -> None:
        try:
            from fpdf import FPDF
        except Exception:
            output_path.write_text(
                "\n".join(
                    [
                        "Certificate of Completion",
                        f"Certificate Number: {certificate_number}",
                        f"Student: {student_name}",
                        f"Course: {course_title}",
                        f"Completion Date: {completion_date.date().isoformat()}",
                    ]
                ),
                encoding="utf-8",
            )
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 12, "Certificate of Completion", ln=True, align="C")

        pdf.ln(10)
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 8, f"Certificate Number: {certificate_number}", ln=True)
        pdf.cell(0, 8, f"Student: {student_name}", ln=True)
        pdf.cell(0, 8, f"Course: {course_title}", ln=True)
        pdf.cell(0, 8, f"Completion Date: {completion_date.date().isoformat()}", ln=True)

        pdf.output(str(output_path))
