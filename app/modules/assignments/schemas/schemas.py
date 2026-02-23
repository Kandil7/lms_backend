from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AssignmentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_points: Optional[int] = None
    grading_type: Optional[str] = None
    assignment_metadata: Optional[dict] = None


class AssignmentCreate(AssignmentBase):
    course_id: str  # UUID as string
    status: str = "draft"
    is_published: bool = False


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_points: Optional[int] = None
    grading_type: Optional[str] = None
    status: Optional[str] = None
    is_published: Optional[bool] = None
    assignment_metadata: Optional[dict] = None


class AssignmentResponse(AssignmentBase):
    id: str  # UUID as string
    course_id: str  # UUID as string
    instructor_id: str  # UUID as string
    status: str
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentListResponse(BaseModel):
    assignments: List[AssignmentResponse]
    total: int
    page: int
    page_size: int


class SubmissionBase(BaseModel):
    content: Optional[str] = None
    file_urls: Optional[List[str]] = None
    submission_type: Optional[str] = None
    submission_metadata: Optional[dict] = None


class SubmissionCreate(SubmissionBase):
    assignment_id: str  # UUID as string
    enrollment_id: str  # UUID as string
    submitted_at: Optional[datetime] = None
    status: str = "submitted"


class SubmissionUpdate(BaseModel):
    grade: Optional[float] = None
    max_grade: Optional[float] = None
    feedback: Optional[str] = None
    feedback_attachments: Optional[List[str]] = None
    status: Optional[str] = None
    graded_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None


class SubmissionResponse(SubmissionBase):
    id: str  # UUID as string
    assignment_id: str  # UUID as string
    enrollment_id: str  # UUID as string
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    status: str
    grade: Optional[float] = None
    max_grade: Optional[float] = None
    feedback: Optional[str] = None
    feedback_attachments: Optional[List[str]] = None
    submission_metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    submissions: List[SubmissionResponse]
    total: int
    page: int
    page_size: int