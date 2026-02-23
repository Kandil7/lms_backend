from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.permissions import Role
from app.modules.courses.schemas.course import CourseCreate, CourseListResponse, CourseResponse, CourseUpdate
from app.modules.courses.services.course_service import CourseService
from app.utils.pagination import PageParams, paginate

router = APIRouter(prefix="/courses", tags=["Courses"])


def _viewer_scope(current_user) -> str:
    if not current_user:
        return "anon"
    return f"{current_user.role}:{current_user.id}"


def _invalidate_course_lesson_cache() -> None:
    cache = get_app_cache()
    cache.delete_by_prefix("courses:")
    cache.delete_by_prefix("lessons:")


@router.get("", response_model=CourseListResponse)
def list_courses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
    difficulty_level: str | None = Query(default=None),
    search: str | None = Query(default=None),
    mine: bool = Query(default=False),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CourseListResponse:
    cache = get_app_cache()
    scope = _viewer_scope(current_user)
    cache_key = (
        f"courses:list:{scope}:page={page}:page_size={page_size}:"
        f"category={category or ''}:difficulty={difficulty_level or ''}:mine={mine}"
    )
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return CourseListResponse.model_validate(cached_payload)

    service = CourseService(db)

    payload = service.list_courses(
        page=page,
        page_size=page_size,
        category=category,
        difficulty_level=difficulty_level,
        search=search,
        current_user=current_user,
        mine=mine,
    )

    result = paginate(
        [CourseResponse.model_validate(course) for course in payload["items"]],
        payload["total"],
        PageParams(page=page, page_size=page_size),
    )
    response = CourseListResponse.model_validate(result)
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=settings.COURSE_CACHE_TTL_SECONDS)
    return response


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

    _invalidate_course_lesson_cache()
    return CourseResponse.model_validate(course)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CourseResponse:
    cache = get_app_cache()
    cache_key = f"courses:get:{_viewer_scope(current_user)}:{course_id}"
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return CourseResponse.model_validate(cached_payload)

    course = CourseService(db).get_course(course_id, current_user)
    response = CourseResponse.model_validate(course)
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=settings.COURSE_CACHE_TTL_SECONDS)
    return response


@router.get("/slug/{slug}", response_model=CourseResponse)
def get_course_by_slug(
    slug: str,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CourseResponse:
    cache = get_app_cache()
    cache_key = f"courses:get_slug:{_viewer_scope(current_user)}:{slug}"
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return CourseResponse.model_validate(cached_payload)

    course = CourseService(db).get_course_by_slug(slug, current_user)
    response = CourseResponse.model_validate(course)
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=settings.COURSE_CACHE_TTL_SECONDS)
    return response


@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = CourseService(db).update_course(course_id, payload, current_user)
    _invalidate_course_lesson_cache()
    return CourseResponse.model_validate(course)


@router.post("/{course_id}/publish", response_model=CourseResponse)
def publish_course(
    course_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = CourseService(db).publish_course(course_id, current_user)
    _invalidate_course_lesson_cache()
    return CourseResponse.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    CourseService(db).delete_course(course_id, current_user)
    _invalidate_course_lesson_cache()
