from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.modules.quizzes.repositories.question_repository import QuestionRepository
from app.modules.quizzes.schemas.question import QuestionCreate, QuestionUpdate
from app.modules.quizzes.services.quiz_service import QuizService


class QuestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.quiz_service = QuizService(db)
        self.repo = QuestionRepository(db)

    def add_question(self, course_id: UUID, quiz_id: UUID, payload: QuestionCreate, current_user):
        quiz = self.quiz_service.get_quiz(course_id, quiz_id, current_user, with_questions=False)
        course = self.quiz_service.course_repo.get_by_id(course_id)
        self.quiz_service._ensure_manage_course(course, current_user)

        order_index = self.repo.get_next_order_index(quiz_id)
        options = [option.model_dump() for option in payload.options] if payload.options else None

        question = self.repo.create(
            quiz_id=quiz.id,
            question_text=payload.question_text,
            question_type=payload.question_type,
            points=payload.points,
            order_index=order_index,
            explanation=payload.explanation,
            options=options,
            correct_answer=payload.correct_answer,
            question_metadata=payload.metadata,
        )

        self.db.commit()
        return question

    def update_question(
        self,
        course_id: UUID,
        quiz_id: UUID,
        question_id: UUID,
        payload: QuestionUpdate,
        current_user,
    ):
        quiz = self.quiz_service.get_quiz(course_id, quiz_id, current_user, with_questions=False)
        course = self.quiz_service.course_repo.get_by_id(course_id)
        self.quiz_service._ensure_manage_course(course, current_user)

        question = self.repo.get_by_id(question_id)
        if not question or question.quiz_id != quiz.id:
            raise NotFoundException("Question not found")

        updates = payload.model_dump(exclude_unset=True)
        if "options" in updates and updates["options"] is not None:
            normalized_options = []
            for option in updates["options"]:
                if isinstance(option, dict):
                    normalized_options.append(option)
                else:
                    normalized_options.append(option.model_dump())
            updates["options"] = normalized_options
        if "metadata" in updates:
            updates["question_metadata"] = updates.pop("metadata")

        question = self.repo.update(question, **updates)
        self.db.commit()
        return question

    def list_quiz_questions(self, course_id: UUID, quiz_id: UUID, current_user):
        quiz = self.quiz_service.get_quiz(course_id, quiz_id, current_user, with_questions=False)
        return self.repo.list_by_quiz(quiz.id)
