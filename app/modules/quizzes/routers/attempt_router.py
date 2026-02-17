from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.quizzes.schemas.attempt import (
    AttemptResponse,
    AttemptResultResponse,
    AttemptStartResponse,
    AttemptSubmitRequest,
    QuizTakeResponse,
)
from app.modules.quizzes.schemas.question import QuestionOptionResponse, QuestionPublicResponse
from app.modules.quizzes.services.attempt_service import AttemptService

router = APIRouter(prefix="/quizzes/{quiz_id}/attempts", tags=["Quiz Attempts"])


@router.post("", response_model=AttemptStartResponse, status_code=status.HTTP_201_CREATED)
def start_attempt(
    quiz_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttemptStartResponse:
    attempt = AttemptService(db).start_attempt(quiz_id, current_user)
    return AttemptStartResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=attempt.started_at,
        max_score=attempt.max_score,
    )


@router.get("/start", response_model=QuizTakeResponse)
def get_quiz_for_attempt(
    quiz_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizTakeResponse:
    payload = AttemptService(db).get_quiz_for_taking(quiz_id, current_user)

    questions = [
        QuestionPublicResponse(
            id=question["id"],
            question_text=question["question_text"],
            question_type=question["question_type"],
            points=question["points"],
            options=[QuestionOptionResponse(**option) for option in question["options"]] if question["options"] else None,
        )
        for question in payload["questions"]
    ]

    return QuizTakeResponse(quiz=payload["quiz"], questions=questions)


@router.post("/{attempt_id}/submit", response_model=AttemptResultResponse)
def submit_attempt(
    quiz_id: UUID,
    attempt_id: UUID,
    payload: AttemptSubmitRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttemptResultResponse:
    attempt = AttemptService(db).submit_attempt(quiz_id, attempt_id, payload, current_user)
    result = AttemptResultResponse.model_validate(attempt)
    result.answers = attempt.answers
    return result


@router.get("/my-attempts", response_model=list[AttemptResponse])
def list_my_attempts(
    quiz_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AttemptResponse]:
    attempts = AttemptService(db).list_my_attempts(quiz_id, current_user)
    return [AttemptResponse.model_validate(attempt) for attempt in attempts]


@router.get("/{attempt_id}", response_model=AttemptResultResponse)
def get_attempt_result(
    quiz_id: UUID,
    attempt_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttemptResultResponse:
    attempt = AttemptService(db).get_attempt(quiz_id, attempt_id, current_user)
    result = AttemptResultResponse.model_validate(attempt)
    result.answers = attempt.answers
    return result
