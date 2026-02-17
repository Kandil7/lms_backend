from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuizCreate(BaseModel):
    lesson_id: UUID
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    quiz_type: str = Field(default="graded", pattern="^(practice|graded)$")
    time_limit_minutes: int | None = Field(default=None, ge=1)
    passing_score: Decimal = Field(default=Decimal("70.00"), ge=0, le=100)
    max_attempts: int | None = Field(default=None, ge=1)
    shuffle_questions: bool = True
    shuffle_options: bool = True
    show_correct_answers: bool = True


class QuizUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    quiz_type: str | None = Field(default=None, pattern="^(practice|graded)$")
    time_limit_minutes: int | None = Field(default=None, ge=1)
    passing_score: Decimal | None = Field(default=None, ge=0, le=100)
    max_attempts: int | None = Field(default=None, ge=1)
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    show_correct_answers: bool | None = None
    is_published: bool | None = None


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lesson_id: UUID
    title: str
    description: str | None
    quiz_type: str
    time_limit_minutes: int | None
    passing_score: Decimal
    max_attempts: int | None
    shuffle_questions: bool
    shuffle_options: bool
    show_correct_answers: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime


class QuizListItem(BaseModel):
    id: UUID
    title: str
    description: str | None
    quiz_type: str
    time_limit_minutes: int | None
    passing_score: Decimal
    max_attempts: int | None
    total_questions: int
    total_points: Decimal
    is_published: bool


class QuizListResponse(BaseModel):
    quizzes: list[QuizListItem]
    total: int
