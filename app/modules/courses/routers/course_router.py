from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.permissions import Role
from app.modules.courses.schemas.course import CourseCreate, CourseListResponse, CourseResponse, CourseUpdate
from app.modules.courses.services.course_service import CourseService
from app.utils.pagination import PageParams, paginate

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=CourseListResponse)
def list_courses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
    difficulty_level: str | None = Query(default=None),
    mine: bool = Query(default=False),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CourseListResponse:
    service = CourseService(db)

    payload = service.list_courses(
        page=page,
        page_size=page_size,
        category=category,
        difficulty_level=difficulty_level,
        current_user=current_user,
        mine=mine,
    )

    result = paginate(
        [CourseResponse.model_validate(course) for course in payload["items"]],
        payload["total"],
        PageParams(page=page, page_size=page_size),
    )
    return CourseListResponse.model_validate(result)


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    service = CourseService(db)
    try:
        course = service.create_course(payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course already exists") from exc

    return CourseResponse.model_validate(course)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = CourseService(db).get_course(course_id, current_user)
    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = CourseService(db).update_course(course_id, payload, current_user)
    return CourseResponse.model_validate(course)


@router.post("/{course_id}/publish", response_model=CourseResponse)
def publish_course(
    course_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = CourseService(db).publish_course(course_id, current_user)
    return CourseResponse.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    CourseService(db).delete_course(course_id, current_user)
