from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy import JSON, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint("status IN ('draft','published','archived')", name="ck_assignments_status"),
        Index("ix_assignments_course_created_at", "course_id", "created_at"),
        Index("ix_assignments_instructor_created_at", "instructor_id", "created_at"),
        Index("ix_assignments_is_published_created_at", "is_published", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    max_points: Mapped[int | None] = mapped_column(nullable=True)
    grading_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    assignment_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    course = relationship("Course", back_populates="assignments")
    instructor = relationship("User", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        CheckConstraint("status IN ('submitted','graded','returned','revised')", name="ck_submissions_status"),
        UniqueConstraint("enrollment_id", "assignment_id", name="uq_submissions_enrollment_assignment"),
        Index("ix_submissions_enrollment_status", "enrollment_id", "status"),
        Index("ix_submissions_assignment_status", "assignment_id", "status"),
        Index("ix_submissions_enrollment_submitted_at", "enrollment_id", "submitted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="submitted", index=True)
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_attachments: Mapped[list | None] = mapped_column(JSON, nullable=True)
    submission_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    submission_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    enrollment = relationship("Enrollment", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
