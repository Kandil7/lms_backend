from datetime import datetime
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.modules.assignments.models import Assignment, Submission
from app.modules.assignments.schemas import AssignmentCreate, AssignmentUpdate, SubmissionCreate, SubmissionUpdate
from app.modules.users.models import User
from app.modules.courses.models import Course
from app.modules.enrollments.models import Enrollment


class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_assignment(self, assignment_data: AssignmentCreate, instructor_id: str) -> Assignment:
        """Create a new assignment"""
        assignment = Assignment(
            title=assignment_data.title,
            description=assignment_data.description,
            instructions=assignment_data.instructions,
            course_id=assignment_data.course_id,
            instructor_id=instructor_id,
            status=assignment_data.status,
            is_published=assignment_data.is_published,
            due_date=assignment_data.due_date,
            max_points=assignment_data.max_points,
            grading_type=assignment_data.grading_type,
            assignment_metadata=assignment_data.assignment_metadata,
        )
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def get_assignment(self, assignment_id: str) -> Optional[Assignment]:
        """Get assignment by ID"""
        result = await self.db.execute(
            select(Assignment)
            .options(joinedload(Assignment.course), joinedload(Assignment.instructor))
            .where(Assignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_assignments_by_course(self, course_id: str, skip: int = 0, limit: int = 100) -> Tuple[List[Assignment], int]:
        """Get assignments for a course"""
        query = select(Assignment).where(Assignment.course_id == course_id)
        total_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar_one()

        result = await self.db.execute(
            query
            .options(joinedload(Assignment.course), joinedload(Assignment.instructor))
            .offset(skip)
            .limit(limit)
        )
        assignments = result.scalars().all()
        return assignments, total

    async def update_assignment(self, assignment_id: str, update_data: AssignmentUpdate) -> Optional[Assignment]:
        """Update assignment"""
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(assignment, field, value)

        assignment.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def delete_assignment(self, assignment_id: str) -> bool:
        """Delete assignment"""
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return False

        await self.db.delete(assignment)
        await self.db.commit()
        return True

    async def grade_submission(
        self,
        submission_id: str,
        grade: float,
        max_grade: float,
        feedback: str,
        feedback_attachments: List[str],
        current_user: User,
    ) -> Submission:
        """Grade a submission with feedback and attachments"""
        # Get submission
        result = await self.db.execute(
            select(Submission)
            .options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise ValueError("Submission not found")

        # Verify instructor owns the assignment
        if (
            current_user.role != "instructor" 
            or str(submission.assignment.instructor_id) != str(current_user.id)
        ):
            raise ValueError("You don't have permission to grade this submission")

        # Update submission with grading information
        submission.grade = grade
        submission.max_grade = max_grade
        submission.feedback = feedback
        submission.feedback_attachments = feedback_attachments
        submission.status = "graded"
        submission.graded_at = datetime.utcnow()

        # Update enrollment progress if assignment is graded
        await self._update_enrollment_progress_on_grade(submission.enrollment_id, submission.assignment_id)

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def _update_enrollment_progress_on_grade(
        self, enrollment_id: str, assignment_id: str
    ) -> None:
        """Update enrollment progress when an assignment is graded"""
        # Get assignment to check if it's part of the course structure
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return

        # Get enrollment
        result = await self.db.execute(
            select(Enrollment).where(Enrollment.id == enrollment_id)
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            return

        # Get lesson associated with this assignment (if any)
        # In our current model, assignments are directly linked to courses, not lessons
        # So we'll treat assignments as separate progress items
        
        # For now, we'll just ensure the enrollment is updated
        # In a more sophisticated system, we might want to track assignment completion separately
        enrollment.last_accessed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(enrollment)


class SubmissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.assignment_service = AssignmentService(db)

    async def create_submission(self, submission_data: SubmissionCreate, student_id: str) -> Submission:
        """Create a new submission"""
        # Verify enrollment exists
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.id == submission_data.enrollment_id
            )
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise ValueError("Enrollment not found")

        # Verify assignment exists and belongs to the same course as enrollment
        result = await self.db.execute(
            select(Assignment).where(
                Assignment.id == submission_data.assignment_id,
                Assignment.course_id == enrollment.course_id
            )
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ValueError("Assignment not found or does not belong to the course")

        submission = Submission(
            enrollment_id=submission_data.enrollment_id,
            assignment_id=submission_data.assignment_id,
            submitted_at=submission_data.submitted_at or datetime.utcnow(),
            status=submission_data.status,
            content=submission_data.content,
            file_urls=submission_data.file_urls,
            submission_type=submission_data.submission_type,
            submission_metadata=submission_data.submission_metadata,
        )
        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def get_submission(self, submission_id: str) -> Optional[Submission]:
        """Get submission by ID"""
        result = await self.db.execute(
            select(Submission)
            .options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .where(Submission.id == submission_id)
        )
        return result.scalar_one_or_none()

    async def get_submissions_by_assignment(self, assignment_id: str, skip: int = 0, limit: int = 100) -> Tuple[List[Submission], int]:
        """Get submissions for an assignment"""
        query = select(Submission).where(Submission.assignment_id == assignment_id)
        total_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar_one()

        result = await self.db.execute(
            query
            .options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .offset(skip)
            .limit(limit)
        )
        submissions = result.scalars().all()
        return submissions, total

    async def get_submissions_by_enrollment(self, enrollment_id: str, skip: int = 0, limit: int = 100) -> Tuple[List[Submission], int]:
        """Get submissions for an enrollment"""
        query = select(Submission).where(Submission.enrollment_id == enrollment_id)
        total_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar_one()

        result = await self.db.execute(
            query
            .options(joinedload(Submission.assignment), joinedload(Submission.enrollment))
            .offset(skip)
            .limit(limit)
        )
        submissions = result.scalars().all()
        return submissions, total

    async def update_submission(self, submission_id: str, update_data: SubmissionUpdate) -> Optional[Submission]:
        """Update submission"""
        result = await self.db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(submission, field, value)

        if update_data.status == "graded" and not submission.graded_at:
            submission.graded_at = datetime.utcnow()
        elif update_data.status == "returned" and not submission.returned_at:
            submission.returned_at = datetime.utcnow()

        submission.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def delete_submission(self, submission_id: str) -> bool:
        """Delete submission"""
        result = await self.db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            return False

        await self.db.delete(submission)
        await self.db.commit()
        return True

    async def grade_submission(
        self,
        submission_id: str,
        grade: float,
        max_grade: float,
        feedback: str,
        feedback_attachments: List[str],
        current_user: User,
    ) -> Submission:
        """Grade a submission with feedback and attachments"""
        # Use assignment service for grading logic
        return await self.assignment_service.grade_submission(
            submission_id, grade, max_grade, feedback, feedback_attachments, current_user
        )