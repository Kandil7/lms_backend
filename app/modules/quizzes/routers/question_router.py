from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.modules.quizzes.schemas.question import QuestionCreate, QuestionResponse, QuestionUpdate
from app.modules.quizzes.services.question_service import QuestionService

router = APIRouter(prefix="/courses/{course_id}/quizzes/{quiz_id}/questions", tags=["Quiz Questions"])


@router.get("", response_model=list[QuestionResponse])
def list_questions(
    course_id: UUID,
    quiz_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[QuestionResponse]:
    questions = QuestionService(db).list_quiz_questions(course_id, quiz_id, current_user)
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
    return QuestionResponse.model_validate(question)
