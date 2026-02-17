from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.quizzes.models.attempt import QuizAttempt


class AttemptRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, attempt_id: UUID) -> QuizAttempt | None:
        stmt = select(QuizAttempt).where(QuizAttempt.id == attempt_id)
        return self.db.scalar(stmt)

    def list_by_enrollment(self, enrollment_id: UUID, quiz_id: UUID) -> list[QuizAttempt]:
        stmt = (
            select(QuizAttempt)
            .where(QuizAttempt.enrollment_id == enrollment_id, QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.attempt_number.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_attempt_number(self, enrollment_id: UUID, quiz_id: UUID) -> int:
        stmt = select(func.max(QuizAttempt.attempt_number)).where(
            QuizAttempt.enrollment_id == enrollment_id,
            QuizAttempt.quiz_id == quiz_id,
        )
        value = self.db.scalar(stmt)
        return int(value or 0)

    def create(self, **fields) -> QuizAttempt:
        attempt = QuizAttempt(**fields)
        self.db.add(attempt)
        self.db.flush()
        self.db.refresh(attempt)
        return attempt

    def update(self, attempt: QuizAttempt, **fields) -> QuizAttempt:
        for key, value in fields.items():
            if value is not None:
                setattr(attempt, key, value)

        self.db.add(attempt)
        self.db.flush()
        self.db.refresh(attempt)
        return attempt

    @staticmethod
    def calculate_percentage(score: Decimal, max_score: Decimal) -> Decimal:
        if max_score <= 0:
            return Decimal("0.00")
        return (score / max_score * Decimal("100")).quantize(Decimal("0.01"))
