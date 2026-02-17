from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.quizzes.models.question import QuizQuestion


class QuestionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, question_id: UUID) -> QuizQuestion | None:
        stmt = select(QuizQuestion).where(QuizQuestion.id == question_id)
        return self.db.scalar(stmt)

    def list_by_quiz(self, quiz_id: UUID) -> list[QuizQuestion]:
        stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order_index.asc())
        return list(self.db.scalars(stmt).all())

    def get_next_order_index(self, quiz_id: UUID) -> int:
        stmt = select(func.max(QuizQuestion.order_index)).where(QuizQuestion.quiz_id == quiz_id)
        max_order = self.db.scalar(stmt)
        return int(max_order or 0) + 1

    def create(self, **fields) -> QuizQuestion:
        question = QuizQuestion(**fields)
        self.db.add(question)
        self.db.flush()
        self.db.refresh(question)
        return question

    def update(self, question: QuizQuestion, **fields) -> QuizQuestion:
        for key, value in fields.items():
            if value is not None:
                setattr(question, key, value)

        self.db.add(question)
        self.db.flush()
        self.db.refresh(question)
        return question

    def delete(self, question: QuizQuestion) -> None:
        self.db.delete(question)
        self.db.flush()
