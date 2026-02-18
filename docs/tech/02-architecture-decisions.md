# Architecture Decisions

This document explains the architectural patterns, design decisions, and the reasoning behind the system's structure.

---

## Table of Contents

1. [Architectural Style](#1-architectural-style)
2. [Layered Architecture](#2-layered-architecture)
3. [Vertical Slice Architecture](#3-vertical-slice-architecture)
4. [Dependency Injection](#4-dependency-injection)
5. [Repository Pattern](#5-repository-pattern)
6. [Service Layer Pattern](#6-service-layer-pattern)
7. [API Design Patterns](#7-api-design-patterns)
8. [Event-Driven Components](#8-event-driven-components)
9. [Configuration Management](#9-configuration-management)
10. [Error Handling Strategy](#10-error-handling-strategy)

---

## 1. Architectural Style

### Modular Monolith

This project uses a **Modular Monolith** architecture.

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (Routes)                   │
├─────────────────────────────────────────────────────────┤
│                  Service Layer (Business)               │
├─────────────────────────────────────────────────────────┤
│               Repository Layer (Data Access)            │
├─────────────────────────────────────────────────────────┤
│                   Database (PostgreSQL)                 │
└─────────────────────────────────────────────────────────┘
```

### Why Modular Monolith?

| Factor | Decision |
|--------|----------|
| **Simplicity** | Single deployment, easier to develop and debug |
| **Modularity** | Clear boundaries between features |
| **Scalability** | Can be split into microservices later if needed |
| **Team Size** | Perfect for small-to-medium teams |
| **Transaction Integrity** | Easy ACID transactions across modules |

### Microservices Would Be Overkill Because:

1. **Development Complexity** - More services = more complexity
2. **Deployment** - Need orchestration (Kubernetes)
3. **Testing** - End-to-end testing becomes harder
4. **Transactions** - Distributed transactions are complex
5. **Current Scale** - Single instance can handle current load

---

## 2. Layered Architecture

The application follows a **three-tier layered architecture**:

### Layers Overview

```
┌──────────────────────────────────────────────────────────┐
│                    PRESENTATION                          │
│  API Routes (FastAPI Routers)                           │
│  - Input validation (Pydantic)                          │
│  - HTTP response formatting                              │
│  - Route definitions                                    │
├──────────────────────────────────────────────────────────┤
│                    BUSINESS LOGIC                        │
│  Services (Business Logic)                              │
│  - Core business rules                                  │
│  - Cross-module coordination                            │
│  - Complex transformations                             │
├──────────────────────────────────────────────────────────┤
│                    DATA ACCESS                           │
│  Repositories (Data Access)                            │
│  - Database queries                                      │
│  - Data retrieval and storage                           │
│  - SQLAlchemy models                                     │
└──────────────────────────────────────────────────────────┘
```

### Why Layered?

| Layer | Responsibility | Example |
|-------|----------------|---------|
| API Routes | HTTP handling, validation | `@router.post("/courses")` |
| Services | Business logic, orchestration | `CourseService.create()` |
| Repositories | Data access, queries | `CourseRepository.get_by_id()` |

### Alternative: Clean Architecture

**Why not Clean Architecture (Entities/UseCases)?**
- More complex than needed
- Over-abstraction for this project size
- Layered + Vertical Slice is sufficient

---

## 3. Vertical Slice Architecture

Each feature module is organized as a **vertical slice** containing everything it needs:

```
app/modules/courses/
├── models/              # Database models
│   ├── __init__.py
│   ├── course.py
│   └── lesson.py
├── schemas/             # Pydantic schemas
│   ├── __init__.py
│   ├── course.py
│   └── lesson.py
├── repositories/         # Data access
│   ├── __init__.py
│   ├── course_repo.py
│   └── lesson_repo.py
├── services/            # Business logic
│   ├── __init__.py
│   ├── course_service.py
│   └── lesson_service.py
├── routers/             # API endpoints
│   ├── __init__.py
│   ├── course_router.py
│   └── lesson_router.py
└── __init__.py
```

### Benefits of Vertical Slices

1. **Self-Contained** - Each module has everything it needs
2. **Low Coupling** - Modules don't import each other's internals
3. **Easy Navigation** - Find related code together
4. **Independent Testing** - Test each module independently
5. **Team Split** - Different developers can work on different modules

### Why Not Traditional Layered?

In traditional layered (all models together, all services together):
- Finding related code is harder
- Modules become tightly coupled
- Larger files, harder to navigate

---

## 4. Dependency Injection

This project uses **FastAPI's built-in dependency injection** system.

### How It Works

```python
from fastapi import Depends

# Define dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

# Inject into route
@app.get("/courses/{course_id}")
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    return await course_service.get_by_id(db, course_id)
```

### Injected Dependencies

| Dependency | Purpose |
|------------|---------|
| `get_db` | Database session |
| `get_current_user` | Authenticated user |
| `get_cache` | Redis cache client |
| `get_email_service` | Email sending |
| `get_file_storage` | File storage abstraction |

### Why Dependency Injection?

1. **Testability** - Easy to mock dependencies
2. **Loose Coupling** - Components don't create their dependencies
3. **Configuration** - Easy to swap implementations
4. **Lifecycle Management** - FastAPI handles creation/destruction

---

## 5. Repository Pattern

Data access is abstracted through the **Repository Pattern**.

### Repository Structure

```python
class CourseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, course_id: UUID) -> Course | None:
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Course | None:
        result = await self.db.execute(
            select(Course).where(Course.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def create(self, course: Course) -> Course:
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return course
```

### Service Uses Repository

```python
class CourseService:
    def __init__(self, course_repo: CourseRepository):
        self.course_repo = course_repo
    
    async def get_course(self, course_id: UUID) -> Course | None:
        return await self.course_repo.get_by_id(course_id)
```

### Why Repository Pattern?

| Benefit | Explanation |
|---------|-------------|
| **Abstraction** | Service doesn't know about SQLAlchemy |
| **Testability** | Mock repository in tests |
| **Flexibility** | Change data source without changing service |
| **Reusability** | Same repository methods across services |

---

## 6. Service Layer Pattern

The **Service Layer** contains all business logic.

### Service Structure

```python
class CourseService:
    def __init__(
        self,
        course_repo: CourseRepository,
        enrollment_repo: EnrollmentRepository,
        cache: CacheService
    ):
        self.course_repo = course_repo
        self.enrollment_repo = enrollment_repo
        self.cache = cache
    
    async def get_course_with_enrollments(
        self,
        course_id: UUID,
        user_id: UUID
    ) -> CourseDetailResponse:
        # Check cache first
        cached = await self.cache.get(f"course:{course_id}")
        if cached:
            return cached
        
        # Get course
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise CourseNotFoundError(course_id)
        
        # Check permissions
        await self._check_access(course, user_id)
        
        # Get enrollments
        enrollments = await self.enrollment_repo.get_by_course(course_id)
        
        # Transform and return
        return self._to_response(course, enrollments)
```

### Service Responsibilities

1. **Business Rules** - Enforce domain logic
2. **Validation** - Beyond basic input validation
3. **Transactions** - Manage database transactions
4. **Coordination** - Work across multiple repositories
5. **Caching** - Manage cache reads/writes
6. **Authorization** - Check permissions

### Why Separate Service Layer?

| Concern | Layer |
|---------|-------|
| HTTP handling | Router |
| Business logic | Service |
| Data access | Repository |
| Database models | Models |

---

## 7. API Design Patterns

### RESTful Conventions

```
GET    /courses              # List courses
POST   /courses              # Create course
GET    /courses/{id}         # Get course
PATCH  /courses/{id}         # Update course
DELETE /courses/{id}         # Delete course
POST   /courses/{id}/publish # Action on course
```

### Nested Resources

```
GET    /courses/{course_id}/lessons              # Lessons in course
POST   /courses/{course_id}/lessons              # Create lesson
GET    /courses/{course_id}/lessons/{lesson_id}  # Get lesson

GET    /enrollments/{id}/progress                # Enrollment progress
POST   /enrollments/{id}/complete                # Mark complete
```

### Response Patterns

```python
# Standard response wrapper
class APIResponse(BaseModel):
    success: bool
    data: Any
    message: str | None = None

# List response with pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
```

---

## 8. Event-Driven Components

### Background Task Events

While not using a full event bus, the system uses **event-driven patterns** through Celery:

```python
# When enrollment is created
async def create_enrollment(enrollment: Enrollment):
    await enrollment_repo.create(enrollment)
    
    # Trigger background task (event)
    await send_enrollment_notification.delay(enrollment.id)

# Certificate generation event
async def complete_course(enrollment_id: UUID):
    enrollment = await enrollment_repo.get_by_id(enrollment_id)
    
    if enrollment.progress_percentage >= 100:
        # Trigger certificate generation
        await generate_certificate.delay(enrollment_id)
```

### Why Event-Driven for Background Tasks?

1. **Non-blocking** - User doesn't wait for slow operations
2. **Reliability** - Failed tasks can be retried
3. **Scalability** - Background workers scale independently

---

## 9. Configuration Management

### Environment-Based Configuration

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    PROJECT_NAME: str = "LMS Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://..."
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Email
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587

settings = Settings()
```

### Configuration Hierarchy

1. **Environment Variables** - Highest priority
2. **.env file** - Local development
3. **Defaults** - Fallback values

---

## 10. Error Handling Strategy

### Custom Exception Hierarchy

```python
# app/core/exceptions.py
class LMSException(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class NotFoundError(LMSException):
    def __init__(self, resource: str, id: Any):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND"
        )

class UnauthorizedError(LMSException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message=message, code="UNAUTHORIZED")

class ForbiddenError(LMSException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, code="FORBIDDEN")

class ValidationError(LMSException):
    def __init__(self, message: str):
        super().__init__(message=message, code="VALIDATION_ERROR")
```

### Exception Handler

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.exception_handler(LMSException)
async def lms_exception_handler(request: Request, exc: LMSException):
    return JSONResponse(
        status_code=getattr(exc, 'status_code', 400),
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Course with id 550e8400-e29b-41d4-a716-446655440000 not found"
  }
}
```

---

## Architecture Summary

| Pattern | Purpose | Implementation |
|---------|---------|-----------------|
| Modular Monolith | Single deployable, modular | Each module is separate package |
| Layered Architecture | Clear separation | Routes → Services → Repositories |
| Vertical Slices | Self-contained modules | Each feature has all layers |
| Dependency Injection | Loose coupling | FastAPI Depends |
| Repository Pattern | Data abstraction | Repository classes |
| Service Layer | Business logic | Service classes |
| REST API | Standard API design | FastAPI routers |
| Event-Driven | Async processing | Celery tasks |

This architecture provides:
- **Maintainability** - Clear structure, easy to navigate
- **Testability** - All layers can be tested independently
- **Scalability** - Can evolve to microservices if needed
- **Developer Experience** - Easy to understand and contribute
