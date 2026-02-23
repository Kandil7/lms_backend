from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.assignments.models.models import Assignment, Submission
from app.modules.assignments.schemas.schemas import AssignmentCreate, AssignmentUpdate, SubmissionCreate, SubmissionUpdate
from app.modules.users.models import User
from app.modules.courses.models import Course
from app.modules.enrollments.models import Enrollment
from app.core.database import get_db


class AssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, assignment_data: AssignmentCreate, instructor_id: str) -> Assignment:
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

    async def get_by_id(self, assignment_id: str) -> Optional[Assignment]:
        """Get assignment by ID"""
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        return result.scalar_one_or_none()

    async def get_by_course(self, course_id: str, skip: int = 0, limit: int = 100) -> List[Assignment]:
        """Get assignments for a course"""
        result = await self.db.execute(
            select(Assignment)
            .where(Assignment.course_id == course_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, assignment_id: str, update_data: AssignmentUpdate) -> Optional[Assignment]:
        """Update assignment"""
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(assignment, field, value)
        
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def delete(self, assignment_id: str) -> bool:
        """Delete assignment"""
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            return False

        await self.db.delete(assignment)
        await self.db.commit()
        return True


class SubmissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, submission_data: SubmissionCreate, enrollment_id: str) -> Submission:
        """Create a new submission"""
        submission = Submission(
            enrollment_id=enrollment_id,
            assignment_id=submission_data.assignment_id,
            submitted_at=submission_data.submitted_at,
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

    async def get_by_id(self, submission_id: str) -> Optional[Submission]:
        """Get submission by ID"""
        result = await self.db.execute(select(Submission).where(Submission.id == submission_id))
        return result.scalar_one_or_none()

    async def get_by_assignment(self, assignment_id: str, skip: int = 0, limit: int = 100) -> List[Submission]:
        """Get submissions for an assignment"""
        result = await self.db.execute(
            select(Submission)
            .where(Submission.assignment_id == assignment_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_enrollment(self, enrollment_id: str, skip: int = 0, limit: int = 100) -> List[Submission]:
        """Get submissions for an enrollment"""
        result = await self.db.execute(
            select(Submission)
            .where(Submission.enrollment_id == enrollment_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, submission_id: str, update_data: SubmissionUpdate) -> Optional[Submission]:
        """Update submission"""
        result = await self.db.execute(select(Submission).where(Submission.id == submission_id))
        submission = result.scalar_one_or_none()
        if not submission:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(submission, field, value)
        
        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def delete(self, submission_id: str) -> bool:
        """Delete submission"""
        result = await self.db.execute(select(Submission).where(Submission.id == submission_id))
        submission = result.scalar_one_or_none()
        if not submission:
            return False

        await self.db.delete(submission)
        await self.db.commit()
        return True