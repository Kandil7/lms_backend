# How to Add a New Module

This guide provides a step-by-step walkthrough for adding a new functional module to the EduConnect Pro LMS Backend. We'll use a hypothetical "Feedback" module as an example.

---

## 🏗️ 1. Create the Module Structure
Navigate to `app/modules/` and create your new module directory with the following structure:

```text
app/modules/feedback/
├── __init__.py
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic models (Input/Output)
├── repository.py    # Database CRUD logic
├── service.py       # Business logic
├── router.py        # API endpoints
├── exceptions.py    # Module-specific exceptions
└── dependencies.py  # Module-specific FastAPI dependencies
```

---

## 🗄️ 2. Define the Model
In `models.py`, define your database table using SQLAlchemy.

```python
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class CourseFeedback(Base):
    __tablename__ = "course_feedback"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
```

---

## 📋 3. Define the Schemas
In `schemas.py`, create Pydantic models for data validation.

```python
from pydantic import BaseModel, Field
from uuid import UUID

class FeedbackCreate(BaseModel):
    course_id: UUID
    comment: str = Field(..., min_length=10)
    rating: int = Field(..., ge=1, le=5)

class FeedbackResponse(FeedbackCreate):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True
```

---

## 🛠️ 4. Implement Repository & Service
Keep your logic clean by separating DB operations from business rules.

**repository.py**:
```python
class FeedbackRepository:
    def create(self, db: Session, feedback: CourseFeedback) -> CourseFeedback:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
```

**service.py**:
```python
class FeedbackService:
    def __init__(self, repo: FeedbackRepository):
        self.repo = repo

    def submit_feedback(self, db: Session, user_id: UUID, data: FeedbackCreate):
        # Business Rule: Ensure user is enrolled before allowing feedback
        # (This is where you'd call the enrollment module)
        feedback = CourseFeedback(**data.dict(), user_id=user_id)
        return self.repo.create(db, feedback)
```

---

## 🌐 5. Create the Router
In `router.py`, define your API endpoints.

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_db, get_current_user

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("/", response_model=FeedbackResponse)
def create_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = FeedbackService(FeedbackRepository())
    return service.submit_feedback(db, user.id, data)
```

---

## 🔗 6. Register the Router
Finally, wire your new module into the main API aggregator at `app/api/v1/api.py`.

```python
# app/api/v1/api.py
_safe_include(api_router, "app.modules.feedback.router:router")
```

---

## 🧪 7. Add Tests
Create a new test file in `tests/` (e.g., `tests/test_feedback.py`) to verify your work.

```python
def test_create_feedback(client, student_token, test_course):
    response = client.post(
        "/api/v1/feedback/",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"course_id": str(test_course.id), "comment": "Excellent course!", "rating": 5}
    )
    assert response.status_code == 200
```

---

## ✅ Checklist
- [ ] Model defined and inherits from `Base`.
- [ ] Alembic migration generated (`alembic revision --autogenerate`).
- [ ] Schemas cover input validation and output formatting.
- [ ] Service layer handles business rules (e.g., permissions).
- [ ] Router registered in `api.py`.
- [ ] Unit/Integration tests passing.
