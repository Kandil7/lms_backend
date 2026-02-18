from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.modules.courses.schemas.lesson import LessonCreate, LessonListResponse, LessonResponse, LessonUpdate
from app.modules.courses.services.lesson_service import LessonService

router = APIRouter(tags=["Lessons"])


def _viewer_scope(current_user) -> str:
    if not current_user:
        return "anon"
    return f"{current_user.role}:{current_user.id}"


def _invalidate_lesson_course_cache() -> None:
    cache = get_app_cache()
    cache.delete_by_prefix("lessons:")
    cache.delete_by_prefix("courses:")


@router.get("/courses/{course_id}/lessons", response_model=LessonListResponse)
def list_lessons(
    course_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> LessonListResponse:
    cache = get_app_cache()
    cache_key = f"lessons:list:{_viewer_scope(current_user)}:course={course_id}"
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return LessonListResponse.model_validate(cached_payload)

    lessons = LessonService(db).list_lessons(course_id, current_user)
    response = LessonListResponse(items=[LessonResponse.model_validate(lesson) for lesson in lessons], total=len(lessons))
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=settings.LESSON_CACHE_TTL_SECONDS)
    return response


@router.post("/courses/{course_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: UUID,
    payload: LessonCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonResponse:
    service = LessonService(db)
    try:
        lesson = service.create_lesson(course_id, payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lesson already exists or order index conflicts",
        ) from exc
    _invalidate_lesson_course_cache()
    return LessonResponse.model_validate(lesson)


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> LessonResponse:
    cache = get_app_cache()
    cache_key = f"lessons:get:{_viewer_scope(current_user)}:lesson={lesson_id}"
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return LessonResponse.model_validate(cached_payload)

    lesson = LessonService(db).get_lesson(lesson_id, current_user)
    response = LessonResponse.model_validate(lesson)
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=settings.LESSON_CACHE_TTL_SECONDS)
    return response


@router.patch("/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: UUID,
    payload: LessonUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonResponse:
    service = LessonService(db)
    try:
        lesson = service.update_lesson(lesson_id, payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lesson already exists or order index conflicts",
        ) from exc
    _invalidate_lesson_course_cache()
    return LessonResponse.model_validate(lesson)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    LessonService(db).delete_lesson(lesson_id, current_user)
    _invalidate_lesson_course_cache()
