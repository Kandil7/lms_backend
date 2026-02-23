from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.assignments.models import Assignment, Submission
from app.modules.assignments.schemas import AssignmentCreate, AssignmentUpdate, SubmissionCreate, SubmissionUpdate, AssignmentResponse, AssignmentListResponse, SubmissionResponse, SubmissionListResponse
from app.modules.assignments.services import AssignmentService, SubmissionService
from app.core.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.courses.models import Course
from app.modules.enrollments.models import Enrollment
from app.core.config import settings


router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new assignment"""
    # Verify user is instructor and owns the course
    if current_user.role != "instructor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only instructors can create assignments")

    # Verify course exists and belongs to current user
    try:
        course_id_uuid = uuid.UUID(assignment_data.course_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID format")

    result = await db.execute(select(Course).where(Course.id == course_id_uuid))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to create assignments for this course")

    service = AssignmentService(db)
    assignment = await service.create_assignment(assignment_data, str(current_user.id))
    return assignment


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assignment by ID"""
    service = AssignmentService(db)
    assignment = await service.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    
    # Check permissions
    if current_user.role == "student":
        # Student can only access assignments in their enrolled courses
        result = await db.execute(
            select(Enrollment).where(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == assignment.course_id
            )
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this assignment")
    elif current_user.role == "instructor":
        # Instructor can only access assignments they created
        if assignment.instructor_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this assignment")
    
    return assignment


@router.get("/course/{course_id}", response_model=AssignmentListResponse)
async def get_assignments_by_course(
    course_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assignments for a course"""
    # Verify user has access to the course
    try:
        course_id_uuid = uuid.UUID(course_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID format")

    if current_user.role == "student":
        result = await db.execute(
            select(Enrollment).where(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == course_id_uuid
            )
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this course")
    elif current_user.role == "instructor":
        result = await db.execute(select(Course).where(Course.id == course_id_uuid))
        course = result.scalar_one_or_none()
        if not course or course.instructor_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this course")

    service = AssignmentService(db)
    assignments, total = await service.get_assignments_by_course(str(course_id_uuid), skip, limit)

    return AssignmentListResponse(
        assignments=[AssignmentResponse.from_orm(a) for a in assignments],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str,
    update_data: AssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update assignment"""
    service = AssignmentService(db)
    assignment = await service.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Only instructor who created the assignment can update it
    if current_user.role != "instructor" or assignment.instructor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to update this assignment")

    updated_assignment = await service.update_assignment(assignment_id, update_data)
    if not updated_assignment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update assignment")

    return updated_assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete assignment"""
    service = AssignmentService(db)
    assignment = await service.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Only instructor who created the assignment can delete it
    if current_user.role != "instructor" or assignment.instructor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete this assignment")

    success = await service.delete_assignment(assignment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete assignment")


# Submissions router
submissions_router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an assignment"""
    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can submit assignments")
    
    # Verify enrollment exists and assignment belongs to the same course
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.id == submission_data.enrollment_id
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == submission_data.assignment_id,
            Assignment.course_id == enrollment.course_id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found or does not belong to your course")
    
    service = SubmissionService(db)
    submission = await service.create_submission(submission_data, str(current_user.id))
    return submission


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get submission by ID"""
    service = SubmissionService(db)
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    
    # Check permissions
    if current_user.role == "student":
        # Student can only access their own submissions
        if str(submission.enrollment_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this submission")
    elif current_user.role == "instructor":
        # Instructor can only access submissions for assignments they created
        result = await db.execute(
            select(Assignment).where(
                Assignment.id == submission.assignment_id,
                Assignment.instructor_id == current_user.id
            )
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this submission")
    
    return submission


@router.get("/assignment/{assignment_id}", response_model=SubmissionListResponse)
async def get_submissions_by_assignment(
    assignment_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get submissions for an assignment"""
    if current_user.role != "instructor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only instructors can view submissions for an assignment")

    # Verify assignment exists and belongs to current user
    try:
        assignment_id_uuid = uuid.UUID(assignment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assignment ID format")

    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id_uuid,
            Assignment.instructor_id == current_user.id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found or you don't have access")

    service = SubmissionService(db)
    submissions, total = await service.get_submissions_by_assignment(str(assignment_id_uuid), skip, limit)

    return SubmissionListResponse(
        submissions=[SubmissionResponse.from_orm(s) for s in submissions],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/enrollment/{enrollment_id}", response_model=SubmissionListResponse)
async def get_submissions_by_enrollment(
    enrollment_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get submissions for an enrollment"""
    # Verify enrollment belongs to current user
    if current_user.role == "student":
        try:
            enrollment_id_uuid = uuid.UUID(enrollment_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid enrollment ID format")
        if enrollment_id_uuid != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only access your own submissions")
    elif current_user.role == "instructor":
        # Instructor can access submissions for enrollments in their courses
        result = await db.execute(
            select(Enrollment).where(
                Enrollment.id == enrollment_id,
                Enrollment.course.has(instructor_id=current_user.id)
            )
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this enrollment")

    service = SubmissionService(db)
    submissions, total = await service.get_submissions_by_enrollment(enrollment_id, skip, limit)

    return SubmissionListResponse(
        submissions=[SubmissionResponse.from_orm(s) for s in submissions],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: str,
    update_data: SubmissionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update submission (grading/feedback)"""
    service = SubmissionService(db)
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Only instructor who created the assignment can update submissions
    try:
        assignment_id_uuid = uuid.UUID(submission.assignment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assignment ID format")

    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id_uuid,
            Assignment.instructor_id == current_user.id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to update this submission")

    updated_submission = await service.update_submission(submission_id, update_data)
    if not updated_submission:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update submission")

    return updated_submission


@router.post("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(
    submission_id: str,
    grade: float,
    max_grade: float,
    feedback: str = "",
    feedback_attachments: List[str] = [],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grade a submission with feedback and attachments"""
    if current_user.role != "instructor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only instructors can grade submissions")

    service = SubmissionService(db)
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Verify instructor owns the assignment
    try:
        assignment_id_uuid = uuid.UUID(submission.assignment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assignment ID format")

    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id_uuid,
            Assignment.instructor_id == current_user.id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to grade this submission")

    # Validate grade range
    if grade < 0 or grade > max_grade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grade must be between 0 and {max_grade}"
        )

    try:
        graded_submission = await service.grade_submission(
            submission_id, grade, max_grade, feedback, feedback_attachments, current_user
        )
        return graded_submission
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))