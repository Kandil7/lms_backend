# Project Structure - Complete Guide

This document explains the complete project structure, the purpose of each directory and file, and the reasoning behind the organization.

---

## Table of Contents

1. [Root Directory Overview](#1-root-directory-overview)
2. [Application Core (`app/core/`)](#2-application-core-appcore)
3. [Feature Modules (`app/modules/`)](#3-feature-modules-appmodules)
4. [Background Tasks (`app/tasks/`)](#4-background-tasks-apptasks)
5. [Utilities (`app/utils/`)](#5-utilities-apputils)
6. [Main Application (`app/main.py`)](#6-main-application-appmainpy)
7. [Database Migrations (`alembic/`)](#7-database-migrations-alembic)
8. [Tests (`tests/`)](#8-tests-tests)
9. [Configuration Files](#9-configuration-files)
10. [How to Navigate](#10-how-to-navigate)

---

## 1. Root Directory Overview

```
lms_backend/
├── app/                          # Main application package
│   ├── api/                      # API route aggregation
│   ├── core/                     # Shared infrastructure
│   ├── modules/                  # Feature modules (vertical slices)
│   ├── tasks/                    # Background tasks (Celery)
│   ├── utils/                    # Shared utilities
│   └── main.py                   # FastAPI application entry point
├── alembic/                      # Database migrations
├── tests/                        # Test suite
├── scripts/                      # Utility scripts
├── docs/                         # Documentation
├── docker-compose.yml            # Local development stack
├── docker-compose.prod.yml       # Production stack
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── pytest.ini                    # Pytest configuration
```

### Purpose of Root Files

| File/Directory | Purpose |
|----------------|---------|
| `requirements.txt` | All Python dependencies |
| `docker-compose.yml` | Local development environment |
| `.env.example` | Template for environment variables |
| `pytest.ini` | Pytest configuration |
| `alembic.ini` | Alembic configuration |

---

## 2. Application Core (`app/core/`)

The `core` directory contains **shared infrastructure** used across all modules.

```
app/core/
├── __init__.py
├── config.py              # Settings and configuration
├── database.py            # Database engine and session
├── security.py            # JWT, password hashing
├── dependencies.py        # FastAPI dependencies
├── permissions.py         # Role-based access control
├── exceptions.py         # Custom exceptions
├── cache.py               # Redis caching
├── health.py              # Health check endpoints
└── middleware/            # Custom middleware
    ├── __init__.py
    ├── rate_limit.py      # Rate limiting
    ├── security_headers.py # Security headers
    └── request_logging.py  # Request logging
```

### File Explanations

#### `app/core/config.py`
**Purpose:** Centralized configuration management using environment variables.

```python
# Key configuration classes
class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "LMS Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    # Redis
    REDIS_URL: str
    
    # Email
    SMTP_HOST: str

settings = Settings()
```

**Why:** Single source of truth for all configuration. Uses Pydantic for validation.

---

#### `app/core/database.py`
**Purpose:** Database engine setup, session management, and base model.

```python
# Key components
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Async engine for PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()
```

**Why:** 
- Async support for better performance
- Centralized database connection management
- Reusable base class for all models

---

#### `app/core/security.py`
**Purpose:** Authentication and authorization utilities.

```python
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# JWT token handling
def create_access_token(data: dict) -> str:
    ...

def decode_token(token: str) -> dict:
    ...
```

**Why:** 
- Centralized security logic
- bcrypt for secure password storage
- JWT for stateless authentication

---

#### `app/core/dependencies.py`
**Purpose:** FastAPI dependency injection providers.

```python
# Database session dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Current user dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    ...

# Optional current user (for public endpoints)
async def get_current_user_optional(
    ...
) -> User | None:
    ...
```

**Why:** Reusable dependencies across all routes.

---

#### `app/core/permissions.py`
**Purpose:** Role-based access control (RBAC).

```python
# Permission definitions
class Permission(str, Enum):
    CREATE_COURSE = "create_course"
    UPDATE_COURSE = "update_course"
    DELETE_COURSE = "delete_course"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_USERS = "manage_users"

# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: {*all_permissions},
    Role.INSTRUCTOR: {CREATE_COURSE, UPDATE_COURSE, VIEW_ANALYTICS},
    Role.STUDENT: set()  # No special permissions
}

# Permission checker
def require_permission(permission: Permission):
    def checker(user: User = Depends(get_current_user)):
        if permission not in ROLE_PERMISSIONS.get(user.role, set()):
            raise ForbiddenError()
        return user
    return checker
```

**Why:** Centralized, declarative authorization.

---

#### `app/core/exceptions.py`
**Purpose:** Custom exception classes.

```python
class LMSException(Exception):
    status_code: int = 400
    
class NotFoundError(LMSException):
    status_code = 404
    
class UnauthorizedError(LMSException):
    status_code = 401
    
class ForbiddenError(LMSException):
    status_code = 403
```

**Why:** Consistent error handling across the application.

---

#### `app/core/cache.py`
**Purpose:** Redis caching utilities.

```python
class CacheService:
    async def get(self, key: str) -> Any:
        ...
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        ...
    
    async def delete(self, key: str):
        ...
```

**Why:** Centralized caching logic with TTL support.

---

#### `app/core/middleware/`
**Purpose:** Custom middleware for cross-cutting concerns.

| Middleware | Purpose |
|------------|---------|
| `rate_limit.py` | Prevent API abuse |
| `security_headers.py` | Add security headers (CORS, etc.) |
| `request_logging.py` | Log all requests |

---

## 3. Feature Modules (`app/modules/`)

Each module is a **vertical slice** containing all layers for a feature.

```
app/modules/
├── auth/                   # Authentication
│   ├── __init__.py
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── repositories/       # Data access
│   ├── services/           # Business logic
│   └── routers/            # API endpoints
├── users/                  # User management
├── courses/                # Courses & lessons
├── enrollments/            # Student enrollments
├── quizzes/                # Quiz system
├── analytics/              # Reporting & analytics
├── files/                  # File uploads
└── certificates/           # Certificate generation
```

### Module Structure Pattern

Each module follows this pattern:

```
module_name/
├── __init__.py             # Module exports
├── models/
│   ├── __init__.py
│   └── *.py                # SQLAlchemy models
├── schemas/
│   ├── __init__.py
│   ├── *.py                # Pydantic schemas (request/response)
├── repositories/
│   ├── __init__.py
│   └── *.py                # Data access classes
├── services/
│   ├── __init__.py
│   └── *.py                # Business logic classes
└── routers/
    ├── __init__.py
    └── *.py                # API route handlers
```

### Why This Structure?

| Layer | Purpose | Example |
|-------|---------|---------|
| Models | Database entities | `Course`, `Lesson` |
| Schemas | API request/response | `CourseCreate`, `CourseResponse` |
| Repositories | Data access | `CourseRepository.get_by_id()` |
| Services | Business logic | `CourseService.create_course()` |
| Routers | HTTP handling | `POST /courses` |

---

### Module Details

#### `app/modules/auth/`
**Purpose:** User authentication (register, login, tokens)

| Component | File | Purpose |
|-----------|------|---------|
| Models | `models.py` | `User`, `RefreshToken` |
| Schemas | `schemas.py` | `LoginRequest`, `TokenResponse` |
| Services | `services.py` | `AuthService.login()`, `register()` |
| Routers | `routers.py` | `/auth/*` endpoints |

---

#### `app/modules/users/`
**Purpose:** User management (CRUD, profiles)

| Component | File | Purpose |
|-----------|------|---------|
| Models | `models.py` | `User` entity |
| Schemas | `schemas.py` | `UserResponse`, `UserUpdate` |
| Services | `services.py` | `UserService` |
| Routers | `routers.py` | `/users/*` endpoints |

---

#### `app/modules/courses/`
**Purpose:** Course and lesson management

```
courses/
├── models/
│   ├── __init__.py
│   ├── course.py          # Course model
│   └── lesson.py           # Lesson model
├── schemas/
│   ├── __init__.py
│   ├── course.py          # Course schemas
│   └── lesson.py           # Lesson schemas
├── repositories/
│   ├── __init__.py
│   ├── course_repo.py
│   └── lesson_repo.py
├── services/
│   ├── __init__.py
│   ├── course_service.py
│   └── lesson_service.py
└── routers/
    ├── __init__.py
    ├── course_router.py
    └── lesson_router.py
```

---

#### `app/modules/enrollments/`
**Purpose:** Student enrollments and progress tracking

| Component | Purpose |
|-----------|---------|
| `Enrollment` | Links student to course |
| `LessonProgress` | Tracks completion per lesson |
| Enrollment service | Handle enrollment logic |
| Progress service | Track and calculate progress |

---

#### `app/modules/quizzes/`
**Purpose:** Quiz system

```
quizzes/
├── models/
│   ├── quiz.py             # Quiz configuration
│   ├── question.py         # Quiz questions
│   └── attempt.py          # Student attempts
├── schemas/
│   ├── quiz.py
│   ├── question.py
│   └── attempt.py
├── repositories/
│   ├── quiz_repo.py
│   ├── question_repo.py
│   └── attempt_repo.py
├── services/
│   ├── quiz_service.py
│   ├── grading_service.py
│   └── attempt_service.py
└── routers/
    ├── quiz_router.py
    ├── question_router.py
    └── attempt_router.py
```

---

#### `app/modules/analytics/`
**Purpose:** Reporting and analytics

| Endpoint | Purpose |
|----------|---------|
| `/analytics/my-progress` | Student's personal progress |
| `/analytics/my-dashboard` | Student's dashboard data |
| `/analytics/courses/{id}` | Course-level analytics |
| `/analytics/instructors/{id}` | Instructor dashboard |
| `/analytics/system` | Admin system overview |

---

#### `app/modules/files/`
**Purpose:** File upload and management

```python
# Storage abstraction
class FileStorage(ABC):
    @abstractmethod
    async def upload(self, file: UploadFile, path: str) -> str:
        pass

# Local storage implementation
class LocalStorage(FileStorage):
    async def upload(self, file: UploadFile, path: str) -> str:
        # Save to uploads/ directory
        ...

# S3 storage implementation  
class S3Storage(FileStorage):
    async def upload(self, file: UploadFile, path: str) -> str:
        # Upload to AWS S3
        ...
```

---

#### `app/modules/certificates/`
**Purpose:** Certificate generation and verification

```python
# Certificate generation flow
1. Student completes course (100% progress)
2. Background task triggered
3. PDF generated using fpdf2
4. Certificate stored (local or S3)
5. Student can download/verify
```

---

## 4. Background Tasks (`app/tasks/`)

Celery tasks for asynchronous processing.

```
app/tasks/
├── __init__.py
├── celery_app.py          # Celery app configuration
├── dispatcher.py           # Task dispatcher (async/sync)
├── email_tasks.py          # Email sending tasks
├── certificate_tasks.py   # Certificate generation
└── progress_tasks.py       # Progress calculation
```

### Task Files Explained

#### `app/tasks/celery_app.py`
```python
from celery import Celery

celery_app = Celery("lms")

celery_app.conf.update(
    broker_url="redis://redis:6379/0",
    result_backend="redis://redis:6379/1",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
```

---

#### `app/tasks/dispatcher.py`
**Purpose:** Unified task dispatching (async or inline)

```python
class TaskDispatcher:
    @staticmethod
    def send_welcome_email(user_id: UUID):
        if settings.TASKS_FORCE_INLINE:
            # Run immediately (development)
            email_service.send_welcome(user_id)
        else:
            # Queue for background processing (production)
            send_welcome_email.delay(user_id)
```

---

## 5. Utilities (`app/utils/`)

Shared utility functions.

```
app/utils/
├── __init__.py
├── helpers.py              # General helpers
├── slug.py                 # Slug generation
├── validators.py           # Custom validators
└── constants.py            # Application constants
```

---

## 6. Main Application (`app/main.py`)

FastAPI application entry point.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LMS Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "LMS Backend API"}
```

---

## 7. Database Migrations (`alembic/`)

```
alembic/
├── versions/               # Migration scripts
│   ├── 001_initial.py
│   ├── 002_add_courses.py
│   └── ...
├── env.py                  # Alembic environment
└── script.py.mako         # Migration template
```

---

## 8. Tests (`tests/`)

```
tests/
├── __init__.py
├── conftest.py             # Pytest fixtures
├── unit/                   # Unit tests
│   ├── test_auth/
│   ├── test_courses/
│   └── ...
├── integration/           # Integration tests
│   ├── test_api/
│   └── ...
└── fixtures/               # Test data
    ├── users.json
    └── courses.json
```

---

## 9. Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | Local development stack |
| `.env.example` | Environment template |
| `pytest.ini` | Pytest configuration |
| `alembic.ini` | Alembic configuration |

---

## 10. How to Navigate

### Finding Code for a Feature

**Question:** Where is the course creation logic?

1. **API Route** → `app/modules/courses/routers/course_router.py`
2. **Service** → `app/modules/courses/services/course_service.py`
3. **Repository** → `app/modules/courses/repositories/course_repo.py`
4. **Model** → `app/modules/courses/models/course.py`
5. **Schema** → `app/modules/courses/schemas/course.py`

### Adding a New Feature

1. Create new module in `app/modules/`
2. Add subdirectories: `models/`, `schemas/`, `repositories/`, `services/`, `routers/`
3. Create `__init__.py` files
4. Import router in `app/api/v1/api.py`
5. Add migration in `alembic/versions/`

---

## Summary

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `app/core/` | Shared infrastructure | `config.py`, `security.py`, `database.py` |
| `app/modules/` | Feature implementations | All vertical slices |
| `app/tasks/` | Background jobs | Celery tasks |
| `app/api/` | Route aggregation | `api.py` |
| `alembic/` | Database migrations | `env.py`, versions |
| `tests/` | Test suite | `conftest.py`, test modules |
| Root | Configuration | `docker-compose.yml`, `.env.example` |

This structure provides:
- **Clear organization** - Easy to find related code
- **Scalability** - Add features without affecting existing code
- **Testability** - Each layer can be tested independently
- **Maintainability** - Clear separation of concerns
