from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Instructor(Base):
    __tablename__ = "instructors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    expertise: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    teaching_experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    education_level: Mapped[str] = mapped_column(String(100), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    verification_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="instructor")

    def __repr__(self):
        return f"<Instructor(id={self.id}, user_id={self.user_id}, is_verified={self.is_verified})>"
