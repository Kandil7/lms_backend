# Architecture Decisions

## Design Patterns and Architectural Choices Explained

This document explains the key architectural decisions made in this LMS backend, the reasoning behind them, and alternatives considered.

---

## 1. Modular Monolith Architecture

### Decision: Organize code by domain modules within a single application

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     LMS BACKEND ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     FastAPI Application                   │  │
│  │                                                              │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │  │
│  │  │    API      │ │   Router    │ │ Middleware  │          │  │
│  │  │   Layer     │ │   Layer     │ │   Layer    │          │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘          │  │
│  │          │              │               │                  │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │                  Core Layer                         │ │  │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │ │  │
│  │  │  │Config  │ │Database│ │Security│ │Cache   │      │ │  │
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘      │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │          │              │               │                  │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │                  Modules Layer                     │ │  │
│  │  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌──────┐ │ │  │
│  │  │  │ Auth  │ │ Users │ │Courses│ │Quizzes│ │ Pay  │ │ │  │
│  │  │  └───────┘ └───────┘ └───────┘ └───────┘ └──────┘ │ │  │
│  │  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌──────┐ │ │  │
│  │  │  │ Enroll│ │ Certs │ │Analytics│ │ Files │ │Emails│ │ │  │
│  │  │  └───────┘ └───────┘ └───────┘ └───────┘ └──────┘ │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │          │              │               │                  │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │                  Tasks Layer (Celery)              │ │  │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │ │  │
│  │  │  │ Emails  │ │ Certs  │ │Progress │ │ Webhooks│   │ │  │
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  PostgreSQL │ │    Redis    │ │    S3/Local │               │
│  │  (Database) │ │ (Cache/MQ)  │ │   (Files)   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Modular Monolith?

| Aspect | Monolith | Microservices |
|--------|----------|---------------|
| **Complexity** | Low | High |
| **Deployment** | Simple | Complex |
| **Data Consistency** | Easy | Hard |
| **Scaling** | Vertical first | Horizontal |
| **Team Size** | Small-Medium | Large |
| **LMS Domain** | Suitable | Overkill |

### Module Structure

```
app/modules/
├── auth/              # Authentication, tokens, MFA
│   ├── __init__.py
│   ├── models.py       # SQLAlchemy models
│   ├── schemas.py      # Pydantic schemas
│   ├── router.py       # API routes
│   └── service.py      # Business logic
├── users/             # User management
├── courses/           # Courses and lessons
├── enrollments/       # Student enrollments
├── quizzes/           # Quiz system
├── certificates/      # Certificate generation
├── payments/         # Payment processing
├── files/            # File uploads
├── analytics/       # Reporting
└── emails/          # Email templates
```

### Benefits for This Project

1. **Single Repository**: Easy to develop and test
2. **Shared Database**: No distributed transactions
3. **Module Isolation**: Clear boundaries within monolith
4. **Future Extraction**: Can split modules later if needed

---

## 2. Repository Pattern with SQLAlchemy

### Decision: Use SQLAlchemy with async support and repository pattern

### Implementation

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class DatabaseSession:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def commit(self):
        await self.session.commit()
    
    # Repository-like methods
    async def get(self, model, id: UUID):
        return await self.session.get(model, id)
    
    async def list(self, model, **filters):
        query = select(model)
        # Apply filters...
        return await self.session.execute(query)
```

### Why This Approach?

| Feature | Benefit |
|---------|---------|
| **Async/Await** | Non-blocking database operations |
| **Connection Pooling** | Efficient resource usage |
| **Type Hints** | IDE autocomplete, mypy support |
| **Migration Ready** | Schema changes tracked by Alembic |

---

## 3. Dependency Injection with FastAPI

### Decision: Use FastAPI's built-in dependency injection system

### Implementation Pattern

```python
# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Validate token and return user
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    # ... token validation logic
    return user
```

### Why FastAPI Dependencies?

1. **Declarative**: Clear input/output contracts
2. **Automatic Cleanup**: Session management with yield
3. **Mockable**: Easy to override in tests
4. **Ordered**: Dependencies can depend on other dependencies

---

## 4. Pydantic for Data Validation

### Decision: Use Pydantic v2 for all data validation and serialization

### Schema Layer

```python
# app/modules/auth/schemas.py
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=100)
    role: Role = Role.STUDENT

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

### Why Pydantic?

| Feature | Benefit |
|---------|---------|
| **Type Coercion** | Automatic type conversion |
| **Validation** | Built-in validators |
| **Serialization** | JSON/from_attributes support |
| **Performance** | Rust-based core in v2 |

---

## 5. Layered API Structure

### Decision: Separate API routes, schemas, and business logic

### Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│                  API LAYER                          │
│              (FastAPI Routers)                      │
│   - Route definitions                               │
│   - HTTP status codes                               │
│   - Request parsing                                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│               SCHEMA LAYER                          │
│              (Pydantic Models)                      │
│   - Request/Response schemas                        │
│   - Validation                                      │
│   - Serialization                                   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│               SERVICE LAYER                        │
│              (Business Logic)                       │
│   - Business rules                                  │
│   - Data transformation                             │
│   - Complex operations                              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│               REPOSITORY LAYER                      │
│              (Database Access)                       │
│   - CRUD operations                                 │
│   - Queries                                         │
│   - Transactions                                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│               DATABASE                              │
│              (PostgreSQL)                           │
│   - Data storage                                    │
│   - Indexes                                         │
│   - Constraints                                     │
└─────────────────────────────────────────────────────┘
```

### Example: Create Course Flow

```python
# Layer 1: API Route
@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.INSTRUCTOR))
):
    # Call service layer
    course = await course_service.create_course(
        db=db,
        instructor_id=current_user.id,
        course_data=course_data
    )
    return course

# Layer 2: Service
class CourseService:
    async def create_course(self, db, instructor_id, course_data):
        # Business logic
        slug = course_data.slug or generate_slug(course_data.title)
        
        # Validate unique slug
        existing = await self.repo.get_by_slug(db, slug)
        if existing:
            raise DuplicateSlugError()
        
        # Create course
        course = Course(
            title=course_data.title,
            slug=slug,
            instructor_id=instructor_id,
            # ...
        )
        return await self.repo.create(db, course)
```

---

## 6. Async-First Design

### Decision: Use async/await for all I/O operations

### Why Async?

| Operation | Sync Time | Async Time |
|-----------|-----------|------------|
| Database Query | 100ms | 10ms |
| External API | 200ms | 50ms |
| File Read | 50ms | 5ms |
| Redis Cache | 5ms | 1ms |

### Implementation

```python
# All database operations are async
async def get_courses(db: AsyncSession, page: int, page_size: int):
    query = select(Course).offset((page-1)*page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()

# Background tasks are handled by Celery
@celery_app.task
def send_email_task(email: str, subject: str, template: str):
    # Synchronous email sending
    send_email(email, subject, template)
```

---

## 7. Configuration Management

### Decision: Use environment variables with Pydantic Settings

### Configuration Hierarchy

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars
    )
    
    # Required
    SECRET_KEY: str
    POSTGRES_PASSWORD: str
    
    # Optional with defaults
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Feature flags
    MFA_ENABLED: bool = True
    PAYMENT_ENABLED: bool = True
```

### Environment Files

```
.env                 # Local development
.env.example         # Template for developers
.env.staging.example # Staging configuration
.env.production.example # Production configuration
.env.observability.example # Monitoring stack
```

### Why This Approach?

1. **12-Factor App**: Configuration from environment
2. **Type Safety**: Automatic type coercion
3. **Validation**: Validate on startup
4. **Documentation**: Self-documenting settings

---

## 8. Event-Driven for Background Tasks

### Decision: Use Celery for asynchronous task processing

### Task Categories

```python
# app/tasks/celery_app.py
task_routes = {
    # High priority - immediate delivery
    "app.tasks.email_tasks.send_immediate": {"queue": "emails"},
    
    # CPU intensive - separate queue
    "app.tasks.certificate_tasks.generate_pdf": {"queue": "certificates"},
    
    # Periodic - handled by beat
    "app.tasks.email_tasks.send_weekly_report": {"queue": "scheduled"},
}
```

### Hybrid Execution Model

```python
# app/tasks/dispatcher.py
if settings.TASKS_FORCE_INLINE:
    # Development: Run synchronously
    result = task_func(*args, **kwargs)
else:
    # Production: Queue to Celery
    task_func.delay(*args, **kwargs)
```

### Why Hybrid?

- **Development**: No need to run Celery workers
- **Production**: Full async processing
- **Reliability**: Fallback if queue fails

---

## 9. JWT Authentication with Refresh Tokens

### Decision: Short-lived access tokens with database-backed refresh tokens

### Token Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. LOGIN                                                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  Client   │───►│   API    │───►│ Database │              │
│   │ (email/pw)│    │          │    │          │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│        │               │                                    │
│        │          ┌────┴────┐                                │
│        │          │  Verify │                                │
│        │          │Password │                                │
│        │          └────┬────┘                                │
│        │               │                                      │
│        │          ┌────┴────┐                                │
│        │          │ Generate│                                │
│        │          │ Tokens  │                                │
│        │          └────┬────┘                                │
│        │               │                                      │
│        │          ┌────┴────┐                                │
│        │          │ Store   │                                │
│        │          │ Refresh │                                │
│        │          │ Token   │                                │
│        │          └────┬────┘                                │
│        │               │                                      │
│        │◄──────────────┘                                      │
│        │         Return: access_token + refresh_token         │
│                                                                 │
│   2. ACCESS API                                                │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  Client  │───►│   API  │  Validate│              │
│   │(access)   │    │         │───► │    │   JWT    │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│                                             │                  │
│                           ┌─────────────────┘                  │
│                           │ Check token blacklist             │
│                           │ (Redis)                            │
│                           ▼                                    │
│                          VALID                                 │
│                                                                 │
│   3. REFRESH                                                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  Client  │───►│   API   │───►│  Revoke   │              │
│   │(refresh)  │    │         │    │ old token │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│        │               │                                    │
│        │          ┌────┴────┐                                │
│        │          │ Generate│                                │
│        │          │ New     │                                │
│        │          │ Tokens  │                                │
│        │          └────┬────┘                                │
│        │               │                                      │
│        │          ┌────┴────┐                                │
│        │          │ Store   │                                │
│        │          │ New     │                                │
│        │          │ Refresh │                                │
│        │          └────┬────┘                                │
│        │               │                                      │
│        │◄──────────────┘                                      │
│        │        Return: new access + refresh tokens           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Design?

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Access | 15 minutes | Balance Token** security vs. UX |
| **Refresh Token** | 30 days | Long-lived sessions |
| **Storage** | Database | Revocability |
| **Blacklist** | Redis | Fast lookup |
| **MFA** | Email-based | User-friendly |

---

## 10. Middleware Stack

### Decision: Layer middleware for cross-cutting concerns

### Middleware Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    REQUEST PIPELINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Incoming Request                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │   Host      │  - Validate Host header                   │
│  │ Validation  │  - Prevent host header attacks             │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │    CORS    │  - Handle Cross-Origin                     │
│  │ Middleware │  - Preflight requests                       │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │   Rate      │  - Token bucket algorithm                 │
│  │  Limiting   │  - Per-IP/User limits                      │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │  Security   │  - Add security headers                   │
│  │  Headers    │  - CSP, HSTS, X-Frame-Options             │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │   Request   │  - Log incoming requests                   │
│  │  Logging    │  - Track performance                       │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │   Response  │  - Wrap responses in envelope              │
│  │  Envelope   │  - (optional, configurable)                │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │    Route    │  - Match URL to handler                   │
│  │   Handler   │  - Execute business logic                  │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │   Response  │  - Serialize to JSON                       │
│  │  Serializ.  │  - Set content-type                        │
│  └─────────────┘                                           │
│        │                                                    │
│        ▼                                                    │
│   Response to Client                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Middleware Implementation

```python
# app/core/middleware/rate_limit.py
class RateLimitMiddleware:
    async def __call__(self, request: Request, call_next):
        # Check rate limit
        if not await self.is_allowed(request):
            raise HTTPException(429, "Rate limit exceeded")
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(self.remaining)
        
        return response
```

---

## 11. Health Check Strategy

### Decision: Separate readiness and liveness checks

### Implementation

```python
# Health endpoint
@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

# Readiness endpoint
@app.get("/api/v1/ready")
async def readiness_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis()
    }
    
    all_up = all(v == "up" for v in checks.values())
    
    return {
        "status": "ok" if all_up else "degraded",
        **checks
    }
```

### Why Separate?

| Check | Purpose | When Fails |
|-------|---------|------------|
| **Liveness** | Is process running? | Restart pod |
| **Readiness** | Can handle requests? | Remove from load balancer |

---

## 12. Error Handling Strategy

### Decision: Centralized exception handling with custom errors

### Error Hierarchy

```
HTTPException (FastAPI built-in)
    │
    ├── UnauthorizedException (401)
    │       └── InvalidCredentials
    │       └── TokenExpired
    │       └── TokenBlacklisted
    │
    ├── ForbiddenException (403)
    │       └── InsufficientPermissions
    │       └── InactiveUser
    │
    ├── NotFoundException (404)
    │       └── UserNotFound
    │       └── CourseNotFound
    │       └── ResourceNotFound
    │
    ├── ValidationException (422)
    │       └── SchemaValidationError
    │       └── BusinessRuleViolation
    │
    └── ConflictException (409)
            └── DuplicateResource
            └── InvalidState
```

### Global Exception Handler

```python
# app/core/exceptions.py
@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": exc.message}
    )
```

---

## Summary: Architecture Principles

| Principle | Implementation |
|-----------|-----------------|
| **Separation of Concerns** | Layered architecture (API, Schema, Service, Repo) |
| **Dependency Inversion** | FastAPI Depends, repository pattern |
| **Async-First** | All I/O operations are async |
| **Configuration as Code** | Pydantic Settings with env vars |
| **Security by Default** | Fail-closed in production, secure middleware |
| **Observability** | Prometheus metrics, Sentry errors, structured logging |
| **Modularity** | Domain-driven module structure |
| **Testability** | Dependency injection, mockable interfaces |

---

## Trade-offs and Decisions

| Decision | Trade-off | Mitigation |
|----------|-----------|------------|
| Modular monolith | Harder to scale than microservices | Design for eventual extraction |
| Async throughout | Learning curve for sync code | Clear patterns, documentation |
| JWT refresh tokens | Database overhead for refresh | Caching, short-lived access |
| Celery for all async | Added complexity | Hybrid inline for dev |
| Multiple payment gateways | Integration maintenance | Abstract adapter pattern |

---

*This architecture balances complexity, scalability, and developer experience while remaining suitable for production deployment.*
