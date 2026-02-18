from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.modules.quizzes.schemas.quiz import QuizCreate, QuizListItem, QuizListResponse, QuizResponse, QuizUpdate
from app.modules.quizzes.services.quiz_service import QuizService

router = APIRouter(prefix="/courses/{course_id}/quizzes", tags=["Quizzes"])


def _viewer_scope(current_user) -> str:
    if not current_user:
        return "anon"
    return f"{current_user.role}:{current_user.id}"


def _invalidate_quiz_cache() -> None:
    cache = get_app_cache()
    cache.delete_by_prefix("quizzes:")
    cache.delete_by_prefix("quiz_questions:")
    cache.delete_by_prefix("quiz_take:")


@router.get("", response_model=QuizListResponse)
def list_course_quizzes(
    course_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> QuizListResponse:
    cache = get_app_cache()
    cache_key = f"quizzes:list:{_viewer_scope(current_user)}:course={course_id}"
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return QuizListResponse.model_validate(cached_payload)

    service = QuizService(db)
    items = [QuizListItem(**item) for item in service.list_course_quiz_items(course_id, current_user)]
    response = QuizListResponse(quizzes=items, total=len(items))
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=settings.QUIZ_CACHE_TTL_SECONDS)
    return response


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    course_id: UUID,
    quiz_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> QuizResponse:
    cache = get_app_cache()
    cache_key = f"quizzes:get:{_viewer_scope(current_user)}:course={course_id}:quiz={quiz_id}"
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return QuizResponse.model_validate(cached_payload)

    quiz = QuizService(db).get_quiz(course_id, quiz_id, current_user)
    response = QuizResponse.model_validate(quiz)
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=settings.QUIZ_CACHE_TTL_SECONDS)
    return response


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    course_id: UUID,
    payload: QuizCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizResponse:
    service = QuizService(db)
    try:
        quiz = service.create_quiz(course_id, payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    _invalidate_quiz_cache()
    return QuizResponse.model_validate(quiz)


@router.patch("/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    course_id: UUID,
    quiz_id: UUID,
    payload: QuizUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizResponse:
    quiz = QuizService(db).update_quiz(course_id, quiz_id, payload, current_user)
    _invalidate_quiz_cache()
    return QuizResponse.model_validate(quiz)


@router.post("/{quiz_id}/publish", response_model=QuizResponse)
def publish_quiz(
    course_id: UUID,
    quiz_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizResponse:
    quiz = QuizService(db).publish_quiz(course_id, quiz_id, current_user)
    _invalidate_quiz_cache()
    return QuizResponse.model_validate(quiz)
