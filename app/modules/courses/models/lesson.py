from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        CheckConstraint(
            "lesson_type IN ('video','text','quiz','assignment')", name="ck_lessons_lesson_type"
        ),
        UniqueConstraint("course_id", "order_index", name="uq_lessons_course_order"),
        Index("ix_lessons_course_lesson_type_order", "course_id", "lesson_type", "order_index"),
        # PERFORMANCE: Additional indexes for common query patterns
        Index("ix_lessons_is_published", "is_published"),
        Index("ix_lessons_course_published", "course_id", "is_published"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    lesson_type: Mapped[str] = mapped_column(String(50), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    parent_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_preview: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lesson_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # Add is_published field to Lesson (was missing but needed for filtering)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    course = relationship("Course", back_populates="lessons")
    parent = relationship("Lesson", remote_side=[id], back_populates="children")
    children = relationship("Lesson", back_populates="parent")
    lesson_progress_entries = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan"
    )
    quiz = relationship(
        "Quiz", back_populates="lesson", uselist=False, cascade="all, delete-orphan"
    )
