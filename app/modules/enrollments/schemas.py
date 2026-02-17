from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentCreate(BaseModel):
    course_id: UUID


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    course_id: UUID
    enrolled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    status: str
    progress_percentage: Decimal
    completed_lessons_count: int
    total_lessons_count: int
    total_time_spent_seconds: int
    last_accessed_at: datetime | None
    certificate_issued_at: datetime | None
    rating: int | None
    review: str | None


class EnrollmentListResponse(BaseModel):
    items: list[EnrollmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LessonProgressUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(not_started|in_progress|completed)$")
    time_spent_seconds: int | None = Field(default=None, ge=0)
    last_position_seconds: int | None = Field(default=None, ge=0)
    completion_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class LessonProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    enrollment_id: UUID
    lesson_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    time_spent_seconds: int
    last_position_seconds: int
    completion_percentage: Decimal


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    review: str = Field(min_length=10, max_length=2000)


class CourseEnrollmentStats(BaseModel):
    course_id: UUID
    total_enrollments: int
    active_enrollments: int
    completed_enrollments: int
    average_progress: Decimal
