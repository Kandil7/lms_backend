from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.assignments.models import Assignment, Submission
from app.modules.assignments.schemas import (
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdate,
    SubmissionCreate,
    SubmissionGradeRequest,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionUpdate,
)
from app.modules.assignments.services import AssignmentService, SubmissionService
from app.modules.courses.models import Course
from app.modules.enrollments.models import Enrollment
from app.modules.users.models import User

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _as_assignment_response(item: Assignment) -> AssignmentResponse:
    return AssignmentResponse.model_validate(item)


def _as_submission_response(item: Submission) -> SubmissionResponse:
    return SubmissionResponse.model_validate(item)


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    if current_user.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can create assignments",
        )

    course = db.scalar(select(Course).where(Course.id == assignment_data.course_id))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create assignments for this course",
        )

    assignment = AssignmentService(db).create_assignment(assignment_data, current_user.id)
    return _as_assignment_response(assignment)


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    assignment = AssignmentService(db).get_assignment(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if current_user.role == "student":
        enrollment = db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == assignment.course_id,
            )
        )
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this assignment",
            )
        if not assignment.is_published or assignment.status != "published":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assignment is not available to students",
            )
    elif current_user.role == "instructor" and assignment.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this assignment",
        )

    return _as_assignment_response(assignment)


@router.get("/course/{course_id}", response_model=AssignmentListResponse)
def get_assignments_by_course(
    course_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentListResponse:
    if current_user.role == "student":
        enrollment = db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == course_id,
            )
        )
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this course",
            )
    elif current_user.role == "instructor":
        course = db.scalar(select(Course).where(Course.id == course_id))
        if course is None or course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this course",
            )

    assignments, total = AssignmentService(db).get_assignments_by_course(
        course_id,
        skip,
        limit,
        published_only=(current_user.role == "student"),
    )
    return AssignmentListResponse(
        assignments=[_as_assignment_response(item) for item in assignments],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: UUID,
    update_data: AssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    service = AssignmentService(db)
    assignment = service.get_assignment(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if current_user.role != "instructor" or assignment.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this assignment",
        )

    updated_assignment = service.update_assignment(assignment_id, update_data)
    if updated_assignment is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update assignment")

    return _as_assignment_response(updated_assignment)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    service = AssignmentService(db)
    assignment = service.get_assignment(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if current_user.role != "instructor" or assignment.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this assignment",
        )

    success = service.delete_assignment(assignment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete assignment")


@router.post("/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_assignment(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments",
        )

    service = SubmissionService(db)
    try:
        submission = service.create_submission(submission_data, current_user.id)
    except ValueError as exc:
        detail = str(exc)
        if detail == "Enrollment not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from exc
        if detail == "Assignment is not published":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc
    return _as_submission_response(submission)


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    submission = SubmissionService(db).get_submission(submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if current_user.role == "student":
        if submission.enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this submission",
            )
    elif current_user.role == "instructor":
        if submission.assignment.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this submission",
            )

    return _as_submission_response(submission)


@router.get("/submissions/assignment/{assignment_id}", response_model=SubmissionListResponse)
def get_submissions_by_assignment(
    assignment_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionListResponse:
    if current_user.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can view submissions for an assignment",
        )

    assignment = AssignmentService(db).get_assignment(assignment_id)
    if assignment is None or assignment.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or you don't have access",
        )

    submissions, total = SubmissionService(db).get_submissions_by_assignment(assignment_id, skip, limit)
    return SubmissionListResponse(
        submissions=[_as_submission_response(item) for item in submissions],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/submissions/enrollment/{enrollment_id}", response_model=SubmissionListResponse)
def get_submissions_by_enrollment(
    enrollment_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionListResponse:
    enrollment = db.scalar(select(Enrollment).where(Enrollment.id == enrollment_id))
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if current_user.role == "student":
        if enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own submissions",
            )
    elif current_user.role == "instructor":
        course = db.scalar(
            select(Course.id).where(
                Course.id == enrollment.course_id,
                Course.instructor_id == current_user.id,
            )
        )
        if course is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this enrollment",
            )

    submissions, total = SubmissionService(db).get_submissions_by_enrollment(enrollment_id, skip, limit)
    return SubmissionListResponse(
        submissions=[_as_submission_response(item) for item in submissions],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.put("/submissions/{submission_id}", response_model=SubmissionResponse)
def update_submission(
    submission_id: UUID,
    update_data: SubmissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    service = SubmissionService(db)
    submission = service.get_submission(submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if current_user.role != "instructor" or submission.assignment.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this submission",
        )

    updated_submission = service.update_submission(submission_id, update_data)
    if updated_submission is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update submission")

    return _as_submission_response(updated_submission)


@router.post("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
def grade_submission(
    submission_id: UUID,
    payload: SubmissionGradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    if current_user.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can grade submissions",
        )

    service = SubmissionService(db)
    try:
        submission = service.grade_submission(
            submission_id,
            grade=payload.grade,
            max_grade=payload.max_grade,
            feedback=payload.feedback,
            feedback_attachments=payload.feedback_attachments,
            instructor_id=current_user.id,
        )
    except ValueError as exc:
        detail = str(exc)
        if detail == "Submission not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from exc
        if "permission" in detail.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc

    return _as_submission_response(submission)
