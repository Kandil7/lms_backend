from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    certificate_number: str
    student_id: UUID
    course_id: UUID
    completion_date: datetime
    issued_at: datetime
    pdf_url: str
    is_revoked: bool


class CertificateListResponse(BaseModel):
    certificates: list[CertificateResponse]
    total: int


class CertificateVerifyResponse(BaseModel):
    valid: bool
    certificate: CertificateResponse | None
    message: str
