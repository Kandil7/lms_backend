from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.modules.quizzes.schemas.question import (
    QuestionCreate,
    QuestionOptionResponse,
    QuestionPublicResponse,
    QuestionResponse,
    QuestionUpdate,
)
from app.modules.quizzes.services.question_service import QuestionService

router = APIRouter(prefix="/courses/{course_id}/quizzes/{quiz_id}/questions", tags=["Quiz Questions"])


def _viewer_scope(current_user) -> str:
    if not current_user:
        return "anon"
    return f"{current_user.role}:{current_user.id}"


def _invalidate_question_quiz_cache() -> None:
    cache = get_app_cache()
    cache.delete_by_prefix("quiz_questions:")
    cache.delete_by_prefix("quizzes:")
    cache.delete_by_prefix("quiz_take:")


def _to_public_question(question) -> QuestionPublicResponse:
    options = None
    if question.options:
        options = [
            QuestionOptionResponse(
                option_id=option.get("option_id") or option.get("id"),
                option_text=option.get("option_text") or option.get("text"),
            )
            for option in question.options
        ]
    return QuestionPublicResponse(
        id=question.id,
        question_text=question.question_text,
        question_type=question.question_type,
        points=question.points,
        options=options,
    )


@router.get("", response_model=list[QuestionPublicResponse])
def list_questions(
    course_id: UUID,
    quiz_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[QuestionPublicResponse]:
    cache = get_app_cache()
    cache_key = f"quiz_questions:list:{_viewer_scope(current_user)}:course={course_id}:quiz={quiz_id}"
    cached_payload = cache.get_json(cache_key)
    if cached_payload is not None:
        return [QuestionPublicResponse.model_validate(item) for item in cached_payload]

    questions = QuestionService(db).list_quiz_questions(course_id, quiz_id, current_user)
    payload = [_to_public_question(question) for question in questions]
    cache.set_json(
        cache_key,
        [item.model_dump(mode="json") for item in payload],
        ttl_seconds=settings.QUIZ_QUESTION_CACHE_TTL_SECONDS,
    )
    return payload


@router.get("/manage", response_model=list[QuestionResponse])
def list_questions_for_management(
    course_id: UUID,
    quiz_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QuestionResponse]:
    questions = QuestionService(db).list_quiz_questions_for_management(course_id, quiz_id, current_user)
    return [QuestionResponse.model_validate(question) for question in questions]


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    course_id: UUID,
    quiz_id: UUID,
    payload: QuestionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestionResponse:
    question = QuestionService(db).add_question(course_id, quiz_id, payload, current_user)
    _invalidate_question_quiz_cache()
    return QuestionResponse.model_validate(question)


@router.patch("/{question_id}", response_model=QuestionResponse)
def update_question(
    course_id: UUID,
    quiz_id: UUID,
    question_id: UUID,
    payload: QuestionUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestionResponse:
    question = QuestionService(db).update_question(course_id, quiz_id, question_id, payload, current_user)
    _invalidate_question_quiz_cache()
    return QuestionResponse.model_validate(question)
