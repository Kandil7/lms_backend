from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.modules.quizzes.schemas.quiz import QuizCreate, QuizListItem, QuizListResponse, QuizResponse, QuizUpdate
from app.modules.quizzes.services.quiz_service import QuizService

router = APIRouter(prefix="/courses/{course_id}/quizzes", tags=["Quizzes"])


@router.get("", response_model=QuizListResponse)
def list_course_quizzes(
    course_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> QuizListResponse:
    service = QuizService(db)
    quizzes = service.list_course_quizzes(course_id, current_user)

    items = [
        QuizListItem(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            quiz_type=quiz.quiz_type,
            time_limit_minutes=quiz.time_limit_minutes,
            passing_score=quiz.passing_score,
            max_attempts=quiz.max_attempts,
            total_questions=service.quiz_repo.count_questions(quiz.id),
            total_points=service.quiz_repo.total_points(quiz.id),
            is_published=quiz.is_published,
        )
        for quiz in quizzes
    ]

    return QuizListResponse(quizzes=items, total=len(items))


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    course_id: UUID,
    quiz_id: UUID,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> QuizResponse:
    quiz = QuizService(db).get_quiz(course_id, quiz_id, current_user)
    return QuizResponse.model_validate(quiz)


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
    return QuizResponse.model_validate(quiz)


@router.post("/{quiz_id}/publish", response_model=QuizResponse)
def publish_quiz(
    course_id: UUID,
    quiz_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizResponse:
    quiz = QuizService(db).publish_quiz(course_id, quiz_id, current_user)
    return QuizResponse.model_validate(quiz)
