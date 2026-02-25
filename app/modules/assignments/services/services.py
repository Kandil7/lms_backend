from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.config import settings
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.modules.assignments.models import Assignment, Submission
from app.modules.assignments.schemas import AssignmentCreate, AssignmentUpdate, SubmissionCreate, SubmissionUpdate
from app.modules.enrollments.models import Enrollment
from app.utils.cache import cache_manager


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db

    def create_assignment(self, payload: AssignmentCreate, instructor_id: UUID) -> Assignment:
        assignment = Assignment(
            title=payload.title,
            description=payload.description,
            instructions=payload.instructions,
            course_id=payload.course_id,
            instructor_id=instructor_id,
            status=payload.status,
            is_published=payload.is_published,
            due_date=payload.due_date,
            max_points=payload.max_points,
            grading_type=payload.grading_type,
            assignment_metadata=payload.assignment_metadata,
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        self._invalidate_assignments_list_cache(payload.course_id)

        return assignment

    def get_assignment(self, assignment_id: UUID) -> Assignment | None:
        stmt = (
            select(Assignment)
            .options(joinedload(Assignment.course), joinedload(Assignment.instructor))
            .where(Assignment.id == assignment_id)
        )
        return self.db.scalar(stmt)

    def get_assignments_by_course(
        self,
        course_id: UUID,
        skip: int,
        limit: int,
        *,
        published_only: bool = False,
    ) -> tuple[list[Assignment], int]:
        viewer_scope = "published" if published_only else "manage"
        cache_key = cache_manager.get_assignment_list_cache_key(str(course_id), skip, limit, viewer_scope)

        if settings.CACHE_ENABLED:
            cached_data = cache_manager.get_json(cache_key)
            if isinstance(cached_data, dict):
                assignments_data = cached_data.get("assignments")
                total = cached_data.get("total", 0)
                if isinstance(assignments_data, list):
                    try:
                        assignments = [
                            self._assignment_from_cache_record(record)
                            for record in assignments_data
                            if isinstance(record, dict)
                        ]
                        return assignments, int(total)
                    except (TypeError, ValueError, KeyError):
                        cache_manager.delete(cache_key)

        base_stmt = select(Assignment).where(Assignment.course_id == course_id)
        if published_only:
            base_stmt = base_stmt.where(
                Assignment.is_published.is_(True),
                Assignment.status == "published",
            )
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
        rows = self.db.scalars(
            base_stmt.options(joinedload(Assignment.course), joinedload(Assignment.instructor))
            .offset(skip)
            .limit(limit)
        ).all()

        if settings.CACHE_ENABLED and rows:
            cache_data = {
                "assignments": [
                    self._assignment_to_cache_record(item)
                    for item in rows
                ],
                "total": int(total),
                "timestamp": datetime.now(UTC).isoformat(),
            }

            cache_manager.set_json(cache_key, cache_data, settings.COURSE_CACHE_TTL_SECONDS)

        return list(rows), int(total)

    def update_assignment(self, assignment_id: UUID, payload: AssignmentUpdate) -> Assignment | None:
        assignment = self.db.scalar(select(Assignment).where(Assignment.id == assignment_id))
        if assignment is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(assignment, field, value)
        assignment.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(assignment)

        self._invalidate_assignments_list_cache(assignment.course_id)

        return assignment

    def delete_assignment(self, assignment_id: UUID) -> bool:
        assignment = self.db.scalar(select(Assignment).where(Assignment.id == assignment_id))
        if assignment is None:
            return False
        course_id = assignment.course_id
        self.db.delete(assignment)
        self.db.commit()

        self._invalidate_assignments_list_cache(course_id)

        return True

    @staticmethod
    def _assignment_to_cache_record(assignment: Assignment) -> dict[str, Any]:
        return {
            "id": str(assignment.id),
            "title": assignment.title,
            "description": assignment.description,
            "instructions": assignment.instructions,
            "course_id": str(assignment.course_id),
            "instructor_id": str(assignment.instructor_id),
            "status": assignment.status,
            "is_published": assignment.is_published,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "max_points": assignment.max_points,
            "grading_type": assignment.grading_type,
            "assignment_metadata": assignment.assignment_metadata,
            "created_at": assignment.created_at.isoformat(),
            "updated_at": assignment.updated_at.isoformat(),
        }

    @staticmethod
    def _assignment_from_cache_record(record: dict[str, Any]) -> Assignment:
        created_at_raw = record.get("created_at")
        updated_at_raw = record.get("updated_at")
        if not isinstance(created_at_raw, str) or not isinstance(updated_at_raw, str):
            raise ValueError("Invalid cached assignment timestamps")

        due_date_raw = record.get("due_date")
        due_date = datetime.fromisoformat(due_date_raw) if isinstance(due_date_raw, str) and due_date_raw else None

        return Assignment(
            id=UUID(str(record["id"])),
            title=str(record["title"]),
            description=record.get("description"),
            instructions=record.get("instructions"),
            course_id=UUID(str(record["course_id"])),
            instructor_id=UUID(str(record["instructor_id"])),
            status=str(record["status"]),
            is_published=bool(record["is_published"]),
            due_date=due_date,
            max_points=record.get("max_points"),
            grading_type=record.get("grading_type"),
            assignment_metadata=record.get("assignment_metadata"),
            created_at=datetime.fromisoformat(created_at_raw),
            updated_at=datetime.fromisoformat(updated_at_raw),
        )

    @staticmethod
    def _invalidate_assignments_list_cache(course_id: UUID) -> None:
        if not settings.CACHE_ENABLED:
            return
        prefix = f"{settings.CACHE_KEY_PREFIX}:assignments:list:{course_id}:"
        cache_manager.delete_by_prefix(prefix)


class SubmissionService:
    def __init__(self, db: Session):
        self.db = db

    def create_submission(self, payload: SubmissionCreate, student_id: UUID) -> Submission:
        enrollment = self.db.scalar(
            select(Enrollment).where(
                Enrollment.id == payload.enrollment_id,
                Enrollment.student_id == student_id,
            )
        )
        if enrollment is None:
            raise ValueError("Enrollment not found")

        assignment = self.db.scalar(
            select(Assignment).where(
                Assignment.id == payload.assignment_id,
                Assignment.course_id == enrollment.course_id,
            )
        )
        if assignment is None:
            raise ValueError("Assignment not found or does not belong to the course")
        if not assignment.is_published or assignment.status != "published":
            raise ValueError("Assignment is not published")

        submission = Submission(
            enrollment_id=payload.enrollment_id,
            assignment_id=payload.assignment_id,
            submitted_at=payload.submitted_at or datetime.now(UTC),
            status=payload.status,
            content=payload.content,
            file_urls=payload.file_urls,
            submission_type=payload.submission_type,
            submission_metadata=payload.submission_metadata,
        )
        self.db.add(submission)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("A submission already exists for this assignment and enrollment") from exc
        self.db.refresh(submission)
        return submission

    def get_submission(self, submission_id: UUID) -> Submission | None:
        stmt = (
            select(Submission)
            .options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .where(Submission.id == submission_id)
        )
        return self.db.scalar(stmt)

    def get_submissions_by_assignment(self, assignment_id: UUID, skip: int, limit: int) -> tuple[list[Submission], int]:
        base_stmt = select(Submission).where(Submission.assignment_id == assignment_id)
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
        rows = self.db.scalars(
            base_stmt.options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .offset(skip)
            .limit(limit)
        ).all()
        return list(rows), int(total)

    def get_submissions_by_enrollment(self, enrollment_id: UUID, skip: int, limit: int) -> tuple[list[Submission], int]:
        base_stmt = select(Submission).where(Submission.enrollment_id == enrollment_id)
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
        rows = self.db.scalars(
            base_stmt.options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .offset(skip)
            .limit(limit)
        ).all()
        return list(rows), int(total)

    def update_submission(self, submission_id: UUID, payload: SubmissionUpdate) -> Submission | None:
        submission = self.db.scalar(select(Submission).where(Submission.id == submission_id))
        if submission is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(submission, field, value)
        if payload.status == "graded" and submission.graded_at is None:
            submission.graded_at = datetime.now(UTC)
        if payload.status == "returned" and submission.returned_at is None:
            submission.returned_at = datetime.now(UTC)
        submission.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def delete_submission(self, submission_id: UUID) -> bool:
        submission = self.db.scalar(select(Submission).where(Submission.id == submission_id))
        if submission is None:
            return False
        self.db.delete(submission)
        self.db.commit()
        return True

    def grade_submission(
        self,
        submission_id: UUID,
        *,
        grade: float,
        max_grade: float,
        feedback: str,
        feedback_attachments: list[str],
        instructor_id: UUID,
    ) -> Submission:
        if grade < 0 or grade > max_grade:
            raise ValueError(f"Grade must be between 0 and {int(max_grade) if max_grade.is_integer() else max_grade}")

        submission = self.db.scalar(
            select(Submission)
            .options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .where(Submission.id == submission_id)
        )
        if submission is None:
            raise ValueError("Submission not found")

        if submission.assignment.instructor_id != instructor_id:
            raise ValueError("You don't have permission to grade this submission")

        submission.grade = grade
        submission.max_grade = max_grade
        submission.feedback = feedback
        submission.feedback_attachments = feedback_attachments
        submission.status = "graded"
        submission.graded_at = datetime.now(UTC)
        submission.updated_at = datetime.now(UTC)
        submission.enrollment.last_accessed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(submission)
        return submission
