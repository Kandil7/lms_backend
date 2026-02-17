from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.quizzes.schemas.question import QuestionPublicResponse


class AttemptStartResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    attempt_number: int
    status: str
    started_at: datetime
    max_score: Decimal


class QuizTakeResponse(BaseModel):
    quiz: dict
    questions: list[QuestionPublicResponse]


class AnswerSubmission(BaseModel):
    question_id: UUID
    selected_option_id: str | None = None
    answer_text: str | None = None


class AttemptSubmitRequest(BaseModel):
    answers: list[AnswerSubmission] = Field(default_factory=list)


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    enrollment_id: UUID
    quiz_id: UUID
    attempt_number: int
    status: str
    started_at: datetime
    submitted_at: datetime | None
    graded_at: datetime | None
    score: Decimal | None
    max_score: Decimal | None
    percentage: Decimal | None
    is_passed: bool | None
    time_taken_seconds: int | None


class AttemptResultResponse(AttemptResponse):
    answers: list[dict] | None
