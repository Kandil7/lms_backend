from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CourseBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    difficulty_level: str | None = Field(default=None, pattern="^(beginner|intermediate|advanced)$")
    thumbnail_url: str | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    metadata: dict | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=3)
    is_free: bool | None = None
    long_description: str | None = None
    preview_video_url: str | None = None
    requirements: list[str] | None = None
    learning_objectives: list[str] | None = None
    total_reviews: int | None = Field(default=None, ge=0)
    total_quizzes: int | None = Field(default=None, ge=0)
    enrollment_count: int | None = Field(default=None, ge=0)
    average_rating: float | None = Field(default=None, ge=0, le=5)
    status: str | None = Field(default=None, max_length=20)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    difficulty_level: str | None = Field(default=None, pattern="^(beginner|intermediate|advanced)$")
    thumbnail_url: str | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    is_published: bool | None = None
    metadata: dict | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=3)
    is_free: bool | None = None
    long_description: str | None = None
    preview_video_url: str | None = None
    requirements: list[str] | None = None
    learning_objectives: list[str] | None = None
    total_reviews: int | None = Field(default=None, ge=0)
    total_quizzes: int | None = Field(default=None, ge=0)
    enrollment_count: int | None = Field(default=None, ge=0)
    average_rating: float | None = Field(default=None, ge=0, le=5)
    status: str | None = Field(default=None, max_length=20)


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    description: str | None
    instructor_id: UUID
    category: str | None
    difficulty_level: str | None
    is_published: bool
    thumbnail_url: str | None
    estimated_duration_minutes: int | None
    created_at: datetime
    updated_at: datetime
    # Additional fields for frontend compatibility
    price: float | None = None
    currency: str | None = None
    is_free: bool | None = None
    long_description: str | None = None
    preview_video_url: str | None = None
    requirements: list[str] | None = None
    learning_objectives: list[str] | None = None
    total_reviews: int | None = None
    total_quizzes: int | None = None
    enrollment_count: int | None = None
    average_rating: float | None = None
    instructor_name: str | None = None
    rating: float | None = None
    review_count: int | None = None
    total_lessons: int | None = None
    duration_hours: int | None = None
    status: str | None = None


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
