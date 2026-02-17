from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.modules.courses.schemas.lesson import LessonCreate, LessonListResponse, LessonResponse, LessonUpdate
from app.modules.courses.services.lesson_service import LessonService

router = APIRouter(tags=["Lessons"])


@router.get("/courses/{course_id}/lessons", response_model=LessonListResponse)
def list_lessons(
    course_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> LessonListResponse:
    lessons = LessonService(db).list_lessons(course_id, current_user)
    return LessonListResponse(items=[LessonResponse.model_validate(lesson) for lesson in lessons], total=len(lessons))


@router.post("/courses/{course_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: UUID,
    payload: LessonCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonResponse:
    lesson = LessonService(db).create_lesson(course_id, payload, current_user)
    return LessonResponse.model_validate(lesson)


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> LessonResponse:
    lesson = LessonService(db).get_lesson(lesson_id, current_user)
    return LessonResponse.model_validate(lesson)


@router.patch("/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: UUID,
    payload: LessonUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonResponse:
    lesson = LessonService(db).update_lesson(lesson_id, payload, current_user)
    return LessonResponse.model_validate(lesson)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    LessonService(db).delete_lesson(lesson_id, current_user)
