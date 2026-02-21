# How to Build This Project - Complete Step by Step Guide

## Build the LMS Backend from Scratch

This document provides a complete, step-by-step guide to building the entire LMS backend project from scratch, explaining every decision along the way.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Step 1: Project Setup](#2-step-1-project-setup)
3. [Step 2: Core Infrastructure](#3-step-2-core-infrastructure)
4. [Step 3: Authentication Module](#4-step-3-authentication-module)
5. [Step 4: Users Module](#5-step-4-users-module)
6. [Step 5: Courses Module](#6-step-5-courses-module)
7. [Step 6: Enrollments Module](#7-step-6-enrollments-module)
8. [Step 7: Quizzes Module](#8-step-7-quizzes-module)
9. [Step 8: Certificates Module](#9-step-8-certificates-module)
10. [Step 9: Files Module](#10-step-9-files-module)
11. [Step 10: Analytics Module](#11-step-10-analytics-module)
12. [Step 11: Payments Module](#12-step-11-payments-module)
13. [Step 12: Background Tasks](#13-step-12-background-tasks)
14. [Step 13: Testing](#14-step-13-testing)
15. [Step 14: Docker Setup](#15-step-14-docker-setup)
16. [Step 15: Deployment](#16-step-15-deployment)

---

## 1. Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 16 | Database |
| Redis | 7 | Cache & Queue |
| Docker | Latest | Containerization |
| Git | Latest | Version Control |

### Why These Versions?

- **Python 3.11+**: Best async performance, modern syntax support
- **PostgreSQL 16**: Latest features, JSON support, excellent indexing
- **Redis 7**: Latest features, better memory management
- **Docker**: Standard containerization

---

## 2. Step 1: Project Setup

### 2.1 Create Project Directory

```bash
mkdir lms_backend
cd lms_backend
git init
```

**Why Git First?**
- Track changes from the beginning
- Rollback capability during development

### 2.2 Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

**Why Virtual Environment?**
- Isolated dependencies
- No conflicts with system packages

### 2.3 Create requirements.txt

```txt
# Core Framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
pydantic-settings>=2.7.1

# Database
sqlalchemy>=2.0.36
alembic>=1.14.0
psycopg2-binary>=2.9.10
asyncpg>=0.30.0

# Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.2.0

# Cache & Queue
redis>=5.0.0
celery>=5.4.0
flower>=2.0.0

# Utilities
python-multipart>=0.0.10
httpx>=0.28.0
jinja2>=3.1.0
fpdf2>=2.7.0

# Monitoring
prometheus-client>=0.21.0
sentry-sdk>=2.0.0

# Storage
boto3>=1.35.0

# Testing
pytest>=8.3.0
pytest-asyncio>=0.25.0
pytest-cov>=6.0.0
faker>=30.0.0
```

**Why Each Package?**

| Package | Purpose |
|---------|---------|
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| Pydantic | Data validation |
| SQLAlchemy | ORM |
| Alembic | Migrations |
| psycopg2 | PostgreSQL driver |
| python-jose | JWT tokens |
| passlib | Password hashing |
| Redis | Cache/broker |
| Celery | Background tasks |
| pytest | Testing |

### 2.4 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Step 2: Core Infrastructure

### 3.1 Create Directory Structure

```
app/
├── __init__.py
├── main.py
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── api.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── health.py
│   ├── permissions.py
│   ├── cache.py
│   ├── metrics.py
│   ├── observability.py
│   ├── model_registry.py
│   └── middleware/
│       ├── __init__.py
│       ├── rate_limit.py
│       ├── security_headers.py
│       ├── request_logging.py
│       └── response_envelope.py
├── modules/
│   ├── __init__.py
│   ├── auth/
│   ├── users/
│   ├── courses/
│   └── ...
├── tasks/
│   ├── __init__.py
│   ├── celery_app.py
│   ├── dispatcher.py
│   └── ...
└── utils/
    ├── __init__.py
    ├── constants.py
    ├── pagination.py
    └── validators.py
```

### 3.2 Create config.py

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"
    API_DOCS_ENABLED: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/lms"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # ... more settings

settings = Settings()
```

**Why Pydantic Settings?**
- Type coercion
- Environment variable support
- Validation on startup

### 3.3 Create database.py

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Why Async SQLAlchemy?**
- Non-blocking I/O
- Better concurrency
- Works with FastAPI

### 3.4 Create main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core import middleware, exceptions, health

app = FastAPI(
    title="LMS Backend",
    version="1.0.0",
    docs_url="/docs" if settings.API_DOCS_ENABLED else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(middleware.security_headers.SecurityHeadersMiddleware)
app.add_middleware(middleware.rate_limit.RateLimitMiddleware)
app.add_middleware(middleware.request_logging.RequestLoggingMiddleware)

# Exception handlers
app.add_exception_handler(exceptions.UnauthorizedException, exceptions.unauthorized_handler)
# ... more handlers

# Routes
app.include_router(api_router, prefix="/api/v1")

# Health
app.add_api_route("/health", health.health_check)
app.add_api_route("/ready", health.readiness_check)
```

### 3.5 Create security.py

```python
from datetime import datetime, timedelta
from jose import jwt
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hash(password, rounds=12)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "jti": str(uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
```

**Why bcrypt with 12 rounds?**
- Industry standard
- Adaptive cost prevents brute force

### 3.6 Create dependencies.py

```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.core.permissions import Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # Decode token, check blacklist, fetch user
    pass

async def require_roles(*roles: Role):
    async def role_checker(user = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return role_checker
```

---

## 4. Step 3: Authentication Module

### 4.1 Create Models

```python
# app/modules/auth/models.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_jti = Column(String(64), unique=True)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 4.2 Create Schemas

```python
# app/modules/auth/schemas.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

### 4.3 Create Service

```python
# app/modules/auth/service.py
class AuthService:
    async def register(self, db, email: str, password: str, full_name: str, role: str):
        # Check if user exists
        # Hash password
        # Create user
        # Generate tokens
        pass
    
    async def login(self, db, email: str, password: str):
        # Find user
        # Verify password
        # Generate tokens
        pass
    
    async def refresh(self, db, refresh_token: str):
        # Validate token
        # Generate new access token
        pass
    
    async def logout(self, db, refresh_token: str):
        # Revoke token
        pass
```

### 4.4 Create Router

```python
# app/modules/auth/router.py
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.modules.auth.schemas import *
from app.modules.auth.service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db = Depends(get_db)):
    return await auth_service.register(db, **user_data.dict())

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db = Depends(get_db)):
    return await auth_service.login(db, credentials.email, credentials.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_data: RefreshTokenRequest, db = Depends(get_db)):
    return await auth_service.refresh(db, refresh_data.refresh_token)

@router.post("/logout")
async def logout(refresh_data: LogoutRequest, db = Depends(get_db), user = Depends(get_current_user)):
    return await auth_service.logout(db, refresh_data.refresh_token, user.id)
```

### 4.5 Add to API Router

```python
# app/api/v1/api.py
from app.modules.auth.router import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
```

---

## 5. Step 4: Users Module

### 5.1 Create User Model

```python
# app/modules/users/models.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    full_name = Column(String(255))
    role = Column(String(50), default="student")  # admin, instructor, student
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    profile_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
```

### 5.2 Create Repository

```python
# app/modules/users/repositories/user_repository.py
class UserRepository:
    async def get_by_id(self, db, user_id):
        return await db.get(User, user_id)
    
    async def get_by_email(self, db, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def create(self, db, user: User):
        db.add(user)
        await db.flush()
        return user
```

### 5.3 Create Service

```python
# app/modules/users/services/user_service.py
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def create_user(self, db, email: str, password: str, full_name: str, role: str):
        # Check if exists
        existing = await self.repository.get_by_email(db, email)
        if existing:
            raise ConflictException("Email already exists")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role
        )
        
        return await self.repository.create(db, user)
```

### 5.4 Create Router

```python
# app/modules/users/router.py
@router.get("/", response_model=List[UserResponse])
async def list_users(
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.ADMIN))
):
    # List all users (admin only)

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.ADMIN))
):
    # Create user (admin only)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return current_user
```

---

## 6. Step 5: Courses Module

### 6.1 Create Course Model

```python
# app/modules/courses/models/course.py
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255))
    slug = Column(String(255), unique=True, index=True)
    description = Column(Text)
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    category = Column(String(100), index=True)
    difficulty_level = Column(String(50))  # beginner, intermediate, advanced
    is_published = Column(Boolean, default=False, index=True)
    thumbnail_url = Column(String(500))
    estimated_duration_minutes = Column(Integer)
    course_metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### 6.2 Create Lesson Model

```python
# app/modules/courses/models/lesson.py
class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    title = Column(String(255))
    slug = Column(String(255))
    description = Column(Text)
    content = Column(Text)  # For text lessons
    lesson_type = Column(String(50))  # video, text, quiz, assignment
    order_index = Column(Integer)
    parent_lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True)
    duration_minutes = Column(Integer)
    video_url = Column(String(500))
    is_preview = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### 6.3 Create Schemas

```python
# app/modules/courses/schemas/course.py
class CourseCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str | None = None
    category: str | None = None
    difficulty_level: str | None = None
    thumbnail_url: str | None = None

class CourseResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    instructor_id: UUID
    is_published: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

### 6.4 Create Router

```python
# app/modules/courses/routers/course_router.py
@router.get("/", response_model=CourseListResponse)
async def list_courses(
    category: str | None = None,
    difficulty: str | None = None,
    published: bool = True
):
    # List courses with filters

@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Create course

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: UUID):
    # Get course

@router.post("/{course_id}/publish")
async def publish_course(
    course_id: UUID,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Publish course
```

### 6.5 Create Lesson Router

```python
# app/modules/courses/routers/lesson_router.py
@router.get("/{course_id}/lessons", response_model=LessonListResponse)
async def list_lessons(course_id: UUID):
    # List lessons

@router.post("/{course_id}/lessons", response_model=LessonResponse)
async def create_lesson(
    course_id: UUID,
    lesson_data: LessonCreate,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Create lesson
```

---

## 7. Step 6: Enrollments Module

### 7.1 Create Models

```python
# app/modules/enrollments/models.py
class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")  # active, completed, dropped
    progress_percentage = Column(Numeric(5,2), default=0)
    completed_lessons_count = Column(Integer, default=0)
    total_lessons_count = Column(Integer, default=0)
    total_time_spent_seconds = Column(Integer, default=0)
    rating = Column(Integer, nullable=True)  # 1-5
    review = Column(Text, nullable=True)

class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"))
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"))
    status = Column(String(50), default="not_started")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    completion_percentage = Column(Numeric(5,2), default=0)
```

### 7.2 Create Router

```python
# app/modules/enrollments/router.py
@router.post("/", response_model=EnrollmentResponse)
async def enroll_in_course(
    enrollment_data: EnrollmentCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Enroll student

@router.get("/my-courses", response_model=EnrollmentListResponse)
async def my_enrollments(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get student's courses

@router.put("/{enrollment_id}/lessons/{lesson_id}/progress")
async def update_progress(
    enrollment_id: UUID,
    lesson_id: UUID,
    progress_data: ProgressUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Update lesson progress

@router.post("/{enrollment_id}/lessons/{lesson_id}/complete")
async def mark_complete(
    enrollment_id: UUID,
    lesson_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Mark lesson complete
```

---

## 8. Step 7: Quizzes Module

### 8.1 Create Models

```python
# app/modules/quizzes/models/quiz.py
class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), unique=True)
    title = Column(String(255))
    description = Column(Text)
    quiz_type = Column(String(50), default="graded")  # practice, graded
    passing_score = Column(Numeric(5,2), default=70.0)
    time_limit_minutes = Column(Integer, nullable=True)
    max_attempts = Column(Integer, nullable=True)
    shuffle_questions = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)

# app/modules/quizzes/models/question.py
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"))
    question_text = Column(Text)
    question_type = Column(String(50))  # multiple_choice, true_false, short_answer
    points = Column(Numeric(5,2), default=1.0)
    order_index = Column(Integer)
    options = Column(JSONB, nullable=True)  # [{"id": "a", "text": "..."}]
    correct_answer = Column(String(500))

# app/modules/quizzes/models/attempt.py
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"))
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"))
    attempt_number = Column(Integer)
    status = Column(String(50), default="in_progress")  # in_progress, submitted, graded
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    score = Column(Numeric(6,2), nullable=True)
    percentage = Column(Numeric(6,2), nullable=True)
    is_passed = Column(Boolean, nullable=True)
    answers = Column(JSONB, nullable=True)
```

### 8.2 Create Quiz Routers

```python
# Quiz management
# app/modules/quizzes/routers/quiz_router.py
@router.post("/", response_model=QuizResponse)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Create quiz

@router.post("/{quiz_id}/publish")
async def publish_quiz(quiz_id: UUID, current_user = Depends(require_roles(Role.INSTRUCTOR))):
    # Publish quiz

# Question management
# app/modules/quizzes/routers/question_router.py
@router.post("/{quiz_id}/questions")
async def add_question(
    quiz_id: UUID,
    question_data: QuestionCreate,
    current_user = Depends(require_roles(Role.INSTRUCTOR))
):
    # Add question

# Taking quizzes
# app/modules/quizzes/routers/attempt_router.py
@router.post("/attempts")
async def start_attempt(
    quiz_id: UUID,
    current_user = Depends(get_current_user)
):
    # Start quiz attempt

@router.post("/attempts/{attempt_id}/submit")
async def submit_attempt(
    attempt_id: UUID,
    answers: List[AnswerSubmit],
    current_user = Depends(get_current_user)
):
    # Submit and grade

@router.get("/attempts/{attempt_id}")
async def get_attempt_result(attempt_id: UUID, current_user = Depends(get_current_user)):
    # Get results
```

---

## 9. Step 8: Certificates Module

### 9.1 Create Model

```python
# app/modules/certificates/models.py
class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), unique=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    certificate_number = Column(String(50), unique=True)
    pdf_path = Column(String(1024))
    completion_date = Column(DateTime)
    issued_at = Column(DateTime, default=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
```

### 9.2 Create Service

```python
# app/modules/certificates/service.py
from fpdf import FPDF

class CertificateService:
    async def generate_certificate(self, db, enrollment_id: UUID) -> Certificate:
        # Get enrollment data
        enrollment = await db.get(Enrollment, enrollment_id)
        
        # Generate certificate number
        cert_number = f"CERT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8]}"
        
        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 10, "Certificate of Completion", 0, 1, "C")
        # ... more PDF generation
        
        # Save PDF
        pdf_path = f"certificates/{cert_number}.pdf"
        pdf.output(pdf_path)
        
        # Create record
        certificate = Certificate(
            enrollment_id=enrollment_id,
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
            certificate_number=cert_number,
            pdf_path=pdf_path,
            completion_date=datetime.utcnow()
        )
        
        return certificate
```

### 9.3 Create Router

```python
# app/modules/certificates/router.py
@router.get("/my-certificates")
async def my_certificates(current_user = Depends(get_current_user)):
    # List user's certificates

@router.get("/{certificate_id}/download")
async def download_certificate(certificate_id: UUID, current_user = Depends(get_current_user)):
    # Download PDF

@router.get("/verify/{certificate_number}")
async def verify_certificate(certificate_number: str):
    # Public verification endpoint

@router.post("/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: UUID,
    current_user = Depends(require_roles(Role.ADMIN))
):
    # Revoke certificate
```

**Why fpdf2?**
- Pure Python
- Lightweight
- Easy to customize

---

## 10. Step 9: Files Module

### 10.1 Create Storage Backends

```python
# app/modules/files/storage/base.py
class StorageBase:
    async def upload(self, file, folder: str):
        raise NotImplementedError
    
    async def get_url(self, path: str):
        raise NotImplementedError

# app/modules/files/storage/local.py
class LocalStorage(StorageBase):
    async def upload(self, file, folder: str):
        # Save to local filesystem
        path = f"{folder}/{filename}"
        with open(path, "wb") as f:
            await file.write(f.read())
        return path
    
    async def get_url(self, path: str):
        return f"/uploads/{path}"

# app/modules/files/storage/s3.py
class S3Storage(StorageBase):
    async def upload(self, file, folder: str):
        # Upload to S3
        s3.upload_fileobj(file, bucket, key)
        return key
    
    async def get_url(self, path: str):
        # Generate presigned URL
        return s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": path})
```

### 10.2 Create Router

```python
# app/modules/files/router.py
@router.post("/upload")
async def upload_file(
    file: UploadFile,
    folder: str = "uploads",
    current_user = Depends(get_current_user)
):
    # Upload file

@router.get("/my-files")
async def my_files(current_user = Depends(get_current_user)):
    # List user's files

@router.get("/download/{file_id}")
async def download_file(file_id: UUID, current_user = Depends(get_current_user)):
    # Download file
```

**Why Multiple Storage Backends?**
- Local: Development
- S3: Production
- Easy to swap

---

## 11. Step 10: Analytics Module

### 11.1 Create Router

```python
# app/modules/analytics/router.py
@router.get("/my-progress")
async def my_progress(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Student progress summary

@router.get("/my-dashboard")
async def my_dashboard(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Personalized dashboard

@router.get("/courses/{course_id}")
async def course_analytics(
    course_id: UUID,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Course analytics

@router.get("/system/overview")
async def system_overview(
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.ADMIN))
):
    # System-wide analytics
```

---

## 12. Step 11: Payments Module

### 12.1 Create Models

```python
# app/modules/payments/models.py
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    stripe_payment_intent_id = Column(String(255), unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=True)
    payment_type = Column(String(20))  # one_time, recurring
    amount = Column(Numeric(10,2))
    currency = Column(String(3), default="EGP")
    status = Column(String(20), default="pending")  # pending, succeeded, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    stripe_subscription_id = Column(String(255), unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    plan_name = Column(String(100))
    status = Column(String(20), default="incomplete")
    current_period_end = Column(DateTime, nullable=True)
```

### 12.2 Create Router

```python
# app/modules/payments/router.py
@router.post("/create-payment-intent")
async def create_payment_intent(
    payment_data: CreatePaymentIntent,
    current_user = Depends(get_current_user)
):
    # Create Stripe payment intent

@router.post("/create-subscription")
async def create_subscription(
    sub_data: CreateSubscription,
    current_user = Depends(get_current_user)
):
    # Create Stripe subscription

@router.get("/my-payments")
async def my_payments(current_user = Depends(get_current_user)):
    # List payments

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db = Depends(get_db)):
    # Handle Stripe webhooks

@router.post("/webhooks/myfatoorah")
async def myfatoorah_webhook(request: Request, db = Depends(get_db)):
    # Handle MyFatoorah webhooks
```

**Why Multiple Payment Providers?**
- MyFatoorah: EGP payments (MENA)
- Stripe: Global cards, subscriptions
- Paymob: Alternative Egyptian

---

## 13. Step 12: Background Tasks

### 13.1 Create Celery App

```python
# app/tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "lms_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.certificate_tasks",
        "app.tasks.progress_tasks",
        "app.tasks.webhook_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    task_acks_late=True,
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.certificate_tasks.*": {"queue": "certificates"},
    },
    beat_schedule={
        "weekly-report": {
            "task": "app.tasks.email_tasks.send_weekly_report",
            "schedule": crontab(hour=9, minute=0, day_of_week="monday"),
        },
    },
)
```

### 13.2 Create Email Tasks

```python
# app/tasks/email_tasks.py
from app.tasks.celery_app import celery_app

@celery_app.task(name="app.tasks.email_tasks.send_welcome_email")
def send_welcome_email(email: str, full_name: str):
    # Send welcome email
    pass

@celery_app.task(name="app.tasks.email_tasks.send_certificate_email")
def send_certificate_email(user_id: str, certificate_id: str):
    # Send certificate email
    pass
```

### 13.3 Create Certificate Tasks

```python
# app/tasks/certificate_tasks.py
@celery_app.task(name="app.tasks.certificate_tasks.generate_certificate")
def generate_certificate(enrollment_id: str):
    # Generate PDF certificate
    pass
```

### 13.4 Create Dispatcher

```python
# app/tasks/dispatcher.py
from app.core.config import settings

def send_task(task_name: str, *args, **kwargs):
    if settings.TASKS_FORCE_INLINE:
        # Run synchronously (development)
        return run_inline(task_name, *args, **kwargs)
    else:
        # Queue to Celery (production)
        celery_app.send_task(task_name, args=args, kwargs=kwargs)
```

---

## 14. Step 13: Testing

### 14.1 Create conftest.py

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(test_db):
    async def override_get_db():
        async with test_db() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

### 14.2 Create Tests

```python
# tests/test_auth.py
@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "Password123",
            "role": "student"
        }
    )
    assert response.status_code == 201

# tests/test_courses.py
@pytest.mark.asyncio
async def test_list_courses(client):
    response = await client.get("/api/v1/courses")
    assert response.status_code == 200
```

---

## 15. Step 14: Docker Setup

### 15.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN useradd --create-home --shell /bin/bash nobody
RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
```

### 15.2 Create docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://lms_user:lms_password@postgres:5432/lms
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery_worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q emails,certificates
    depends_on:
      - postgres
      - redis

  celery_beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    depends_on:
      - redis

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: lms
      POSTGRES_USER: lms_user
      POSTGRES_PASSWORD: lms_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 16. Step 15: Deployment

### 16.1 Database Setup

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create admin user
docker-compose exec api python scripts/create_admin.py
```

### 16.2 Environment Variables

```bash
# Production .env
ENVIRONMENT=production
SECRET_KEY=your-32-char-secret-key
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
STRIPE_SECRET_KEY=sk_...
MYFATOORAH_API_KEY=...
```

### 16.3 Run

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

---

## Summary

This step-by-step guide has built a complete LMS backend with:

| Step | Component | Key Files |
|------|-----------|-----------|
| 1 | Prerequisites | Python 3.11+, PostgreSQL, Redis |
| 2 | Core Infrastructure | config.py, database.py, main.py, security.py |
| 3 | Authentication | models.py, schemas.py, service.py, router.py |
| 4 | Users | User model, repository, service, router |
| 5 | Courses | Course, lesson models, CRUD operations |
| 6 | Enrollments | Enrollment, progress tracking |
| 7 | Quizzes | Quiz, questions, attempts |
| 8 | Certificates | PDF generation |
| 9 | Files | Local/S3 storage |
| 10 | Analytics | Dashboard, reporting |
| 11 | Payments | Stripe, MyFatoorah integration |
| 12 | Background Tasks | Celery email, certificates |
| 13 | Testing | pytest fixtures, test cases |
| 14 | Docker | Multi-container setup |
| 15 | Deployment | Production configuration |

The project follows clean architecture with separation of concerns:
- **Routes**: HTTP endpoints
- **Schemas**: Request/response validation
- **Services**: Business logic
- **Repositories**: Data access
- **Models**: Database schema

---

*This guide explains how to build every component of the LMS backend, why each decision was made, and how all the pieces fit together.*
