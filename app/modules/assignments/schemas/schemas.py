from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssignmentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None
    instructions: str | None = None
    due_date: datetime | None = None
    max_points: int | None = None
    grading_type: str | None = None
    assignment_metadata: dict | None = None


class AssignmentCreate(AssignmentBase):
    course_id: UUID
    status: str = "draft"
    is_published: bool = False


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    instructions: str | None = None
    due_date: datetime | None = None
    max_points: int | None = None
    grading_type: str | None = None
    status: str | None = None
    is_published: bool | None = None
    assignment_metadata: dict | None = None


class AssignmentResponse(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    instructor_id: UUID
    status: str
    is_published: bool
    created_at: datetime
    updated_at: datetime


class AssignmentListResponse(BaseModel):
    assignments: list[AssignmentResponse]
    total: int
    page: int
    page_size: int


class SubmissionBase(BaseModel):
    content: str | None = None
    file_urls: list[str] | None = None
    submission_type: str | None = None
    submission_metadata: dict | None = None


class SubmissionCreate(SubmissionBase):
    assignment_id: UUID
    enrollment_id: UUID
    submitted_at: datetime | None = None
    status: str = "submitted"


class SubmissionUpdate(BaseModel):
    grade: float | None = None
    max_grade: float | None = None
    feedback: str | None = None
    feedback_attachments: list[str] | None = None
    status: str | None = None
    graded_at: datetime | None = None
    returned_at: datetime | None = None


class SubmissionGradeRequest(BaseModel):
    grade: float
    max_grade: float
    feedback: str = ""
    feedback_attachments: list[str] = Field(default_factory=list)


class SubmissionResponse(SubmissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assignment_id: UUID
    enrollment_id: UUID
    submitted_at: datetime
    graded_at: datetime | None = None
    returned_at: datetime | None = None
    status: str
    grade: float | None = None
    max_grade: float | None = None
    feedback: str | None = None
    feedback_attachments: list[str] | None = None
    submission_metadata: dict | None = None


class SubmissionListResponse(BaseModel):
    submissions: list[SubmissionResponse]
    total: int
    page: int
    page_size: int
