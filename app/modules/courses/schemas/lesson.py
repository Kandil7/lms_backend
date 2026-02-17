from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LessonBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    content: str | None = None
    lesson_type: str = Field(pattern="^(video|text|quiz|assignment)$")
    order_index: int | None = Field(default=None, ge=1)
    parent_lesson_id: UUID | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    video_url: str | None = None
    is_preview: bool = False
    metadata: dict | None = None


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    content: str | None = None
    lesson_type: str | None = Field(default=None, pattern="^(video|text|quiz|assignment)$")
    order_index: int | None = Field(default=None, ge=1)
    parent_lesson_id: UUID | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    video_url: str | None = None
    is_preview: bool | None = None
    metadata: dict | None = None


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    title: str
    slug: str
    description: str | None
    content: str | None
    lesson_type: str
    order_index: int
    parent_lesson_id: UUID | None
    duration_minutes: int | None
    video_url: str | None
    is_preview: bool
    created_at: datetime
    updated_at: datetime


class LessonListResponse(BaseModel):
    items: list[LessonResponse]
    total: int
