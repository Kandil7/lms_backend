from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionOptionCreate(BaseModel):
    option_id: str | None = None
    option_text: str = Field(min_length=1)
    is_correct: bool = False

    @field_validator("option_id", mode="before")
    @classmethod
    def default_option_id(cls, value: str | None) -> str:
        return value or str(uuid4())


class QuestionOptionResponse(BaseModel):
    option_id: str
    option_text: str


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=3)
    question_type: str = Field(pattern="^(multiple_choice|true_false|short_answer|essay)$")
    points: Decimal = Field(default=Decimal("1.00"), ge=0)
    explanation: str | None = None
    options: list[QuestionOptionCreate] | None = None
    correct_answer: str | None = None
    metadata: dict | None = None


class QuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=3)
    question_type: str | None = Field(default=None, pattern="^(multiple_choice|true_false|short_answer|essay)$")
    points: Decimal | None = Field(default=None, ge=0)
    explanation: str | None = None
    options: list[QuestionOptionCreate] | None = None
    correct_answer: str | None = None
    metadata: dict | None = None


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quiz_id: UUID
    question_text: str
    question_type: str
    points: Decimal
    order_index: int
    explanation: str | None
    options: list[dict] | None
    correct_answer: str | None


class QuestionPublicResponse(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    points: Decimal
    options: list[QuestionOptionResponse] | None
