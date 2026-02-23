from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assignments.models import Assignment, Submission


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, assignment_id: UUID) -> Assignment | None:
        return self.db.scalar(select(Assignment).where(Assignment.id == assignment_id))


class SubmissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, submission_id: UUID) -> Submission | None:
        return self.db.scalar(select(Submission).where(Submission.id == submission_id))
