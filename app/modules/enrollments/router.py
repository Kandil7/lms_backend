from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import Role
from app.modules.enrollments.schemas import (
    CourseEnrollmentStats,
    EnrollmentCreate,
    EnrollmentListResponse,
    EnrollmentResponse,
    LessonProgressResponse,
    LessonProgressUpdate,
    ReviewCreate,
)
from app.modules.enrollments.service import EnrollmentService
from app.utils.pagination import PageParams, paginate

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_course(
    payload: EnrollmentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    if current_user.role not in {Role.STUDENT.value, Role.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can enroll")

    enrollment = EnrollmentService(db).enroll(current_user.id, payload.course_id)
    return EnrollmentResponse.model_validate(enrollment)


@router.get("/my-courses", response_model=EnrollmentListResponse)
def list_my_courses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnrollmentListResponse:
    payload = EnrollmentService(db).list_my_enrollments(current_user.id, page, page_size)
    paginated = paginate(
        [EnrollmentResponse.model_validate(item) for item in payload["items"]],
        payload["total"],
        PageParams(page=page, page_size=page_size),
    )
    return EnrollmentListResponse.model_validate(paginated)


@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
def get_enrollment(
    enrollment_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    enrollment = EnrollmentService(db).get_enrollment(enrollment_id, current_user)
    return EnrollmentResponse.model_validate(enrollment)


@router.put("/{enrollment_id}/lessons/{lesson_id}/progress", response_model=LessonProgressResponse)
def update_lesson_progress(
    enrollment_id: UUID,
    lesson_id: UUID,
    payload: LessonProgressUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonProgressResponse:
    progress = EnrollmentService(db).update_lesson_progress(enrollment_id, lesson_id, payload, current_user)
    return LessonProgressResponse.model_validate(progress)


@router.post("/{enrollment_id}/lessons/{lesson_id}/complete", response_model=LessonProgressResponse)
def mark_lesson_completed(
    enrollment_id: UUID,
    lesson_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonProgressResponse:
    progress = EnrollmentService(db).mark_lesson_completed(enrollment_id, lesson_id, current_user)
    return LessonProgressResponse.model_validate(progress)


@router.post("/{enrollment_id}/review", response_model=EnrollmentResponse)
def add_review(
    enrollment_id: UUID,
    payload: ReviewCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    enrollment = EnrollmentService(db).add_review(enrollment_id, payload, current_user)
    return EnrollmentResponse.model_validate(enrollment)


@router.get("/courses/{course_id}", response_model=EnrollmentListResponse)
def list_course_enrollments(
    course_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnrollmentListResponse:
    payload = EnrollmentService(db).list_course_enrollments(course_id, current_user, page, page_size)
    paginated = paginate(
        [EnrollmentResponse.model_validate(item) for item in payload["items"]],
        payload["total"],
        PageParams(page=page, page_size=page_size),
    )
    return EnrollmentListResponse.model_validate(paginated)


@router.get("/courses/{course_id}/stats", response_model=CourseEnrollmentStats)
def get_course_enrollment_stats(
    course_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseEnrollmentStats:
    total, active, completed, avg_progress = EnrollmentService(db).get_course_stats(course_id, current_user)
    return CourseEnrollmentStats(
        course_id=course_id,
        total_enrollments=total,
        active_enrollments=active,
        completed_enrollments=completed,
        average_progress=avg_progress,
    )
