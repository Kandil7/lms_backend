from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.courses.models.lesson import Lesson
from app.modules.quizzes.models.question import QuizQuestion
from app.modules.quizzes.models.quiz import Quiz


class QuizRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, quiz_id: UUID, with_questions: bool = False) -> Quiz | None:
        stmt = select(Quiz).where(Quiz.id == quiz_id)
        if with_questions:
            stmt = stmt.options(selectinload(Quiz.questions))
        return self.db.scalar(stmt)

    def get_by_lesson(self, lesson_id: UUID) -> Quiz | None:
        stmt = select(Quiz).where(Quiz.lesson_id == lesson_id)
        return self.db.scalar(stmt)

    def list_by_course(self, course_id: UUID) -> list[Quiz]:
        stmt = (
            select(Quiz)
            .join(Lesson, Lesson.id == Quiz.lesson_id)
            .where(Lesson.course_id == course_id)
            .order_by(Quiz.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create(self, **fields) -> Quiz:
        quiz = Quiz(**fields)
        self.db.add(quiz)
        self.db.flush()
        self.db.refresh(quiz)
        return quiz

    def update(self, quiz: Quiz, **fields) -> Quiz:
        for key, value in fields.items():
            if value is not None:
                setattr(quiz, key, value)

        self.db.add(quiz)
        self.db.flush()
        self.db.refresh(quiz)
        return quiz

    def count_questions(self, quiz_id: UUID) -> int:
        stmt = select(func.count()).select_from(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
        return int(self.db.scalar(stmt) or 0)

    def total_points(self, quiz_id: UUID) -> Decimal:
        stmt = select(func.coalesce(func.sum(QuizQuestion.points), 0)).where(QuizQuestion.quiz_id == quiz_id)
        total = self.db.scalar(stmt) or 0
        return Decimal(str(total)).quantize(Decimal("0.01"))
