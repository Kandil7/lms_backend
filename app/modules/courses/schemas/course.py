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


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
