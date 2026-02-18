from decimal import Decimal
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        CheckConstraint(
            "question_type IN ('multiple_choice','true_false','short_answer','essay')",
            name="ck_quiz_questions_type",
        ),
        UniqueConstraint("quiz_id", "order_index", name="uq_quiz_questions_order"),
        Index("ix_quiz_questions_quiz_type_order", "quiz_id", "question_type", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    points: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("1.00"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")
