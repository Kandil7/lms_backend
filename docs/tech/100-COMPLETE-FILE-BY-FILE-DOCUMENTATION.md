# Complete Project File-by-File Documentation

## LMS Backend - Every File Explained

This document provides comprehensive documentation for **every single file** in the LMS backend project, explaining what each file does, why it was created, and how it fits into the overall architecture.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Application Files](#2-core-application-files)
3. [Core Module (app/core/)](#3-core-module)
4. [API Module (app/api/)](#4-api-module)
5. [Modules (app/modules/)](#5-modules)
6. [Tasks Module (app/tasks/)](#6-tasks-module)
7. [Utils Module (app/utils/)](#7-utils-module)
8. [Tests](#8-tests)
9. [Configuration Files](#9-configuration-files)
10. [Database Migrations](#10-database-migrations)
11. [Scripts](#11-scripts)
12. [Why These Technologies Were Chosen](#12-why-these-technologies-were-chosen)

---

## 1. Project Overview

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | FastAPI | 0.115+ |
| **Language** | Python | 3.11+ |
| **Database** | PostgreSQL | 16 |
| **ORM** | SQLAlchemy | 2.0+ |
| **Cache/Queue** | Redis | 7 |
| **Background Jobs** | Celery | 5.4+ |
| **Container** | Docker | Latest |

### Why This Stack?

1. **FastAPI**: Fastest Python web framework, native async support, automatic OpenAPI documentation
2. **Python 3.11+**: Best performance for async code, modern syntax
3. **PostgreSQL 16**: ACID compliance, JSON support, excellent indexing
4. **SQLAlchemy 2.0**: Type-safe ORM with async support
5. **Redis 7**: Multi-purpose (cache, queue, rate limiting)
6. **Celery**: Mature Python task queue with scheduling

---

## 2. Core Application Files

### 2.1 app/__init__.py

```python
# Empty file - marks this directory as a Python package
```

**Purpose**: Makes `app/` a Python package so imports work.

---

### 2.2 app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.model_registry import Base
from app.core import exceptions, health, middleware, metrics, observability

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    docs_url="/docs" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
    redoc_url="/redoc" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add custom middleware
app.add_middleware(middleware.security_headers.SecurityHeadersMiddleware)
app.add_middleware(middleware.rate_limit.RateLimitMiddleware)
app.add_middleware(middleware.request_logging.RequestLoggingMiddleware)

# Register exception handlers
app.add_exception_handler(exceptions.UnauthorizedException, exceptions.unauthorized_exception_handler)
app.add_exception_handler(exceptions.ForbiddenException, exceptions.forbidden_exception_handler)
app.add_exception_handler(exceptions.NotFoundException, exceptions.not_found_exception_handler)
app.add_exception_handler(exceptions.ValidationException, exceptions.validation_exception_handler)
app.add_exception_handler(exceptions.ConflictException, exceptions.conflict_exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Health check endpoints
app.add_api_route("/health", health.health_check, methods=["GET"])
app.add_api_route("/ready", health.readiness_check, methods=["GET"])

# Metrics endpoint
if settings.METRICS_ENABLED:
    app.add_api_route(settings.METRICS_ENDPOINT, metrics.metrics, methods=["GET"])
```

**Why This File Exists**:
- Entry point for the FastAPI application
- Configures all middleware in correct order
- Registers exception handlers
- Sets up API routes and versioning
- Includes health checks for container orchestration

---

## 3. Core Module (app/core/)

The core module contains foundational infrastructure used throughout the application.

### 3.1 app/core/__init__.py

Empty file that marks the core directory as a package.

---

### 3.2 app/core/config.py

```python
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "default-secret-key-change-in-production"
    API_DOCS_EFFECTIVE_ENABLED: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lms_user:lms_password@localhost:5432/lms"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED: bool = True
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Features
    MFA_ENABLED: bool = True
    PAYMENT_ENABLED: bool = True
    CERTIFICATE_AUTO_GENERATE: bool = True
    
    # ... many more settings

settings = Settings()
```

**Why This File Exists**:
- Centralizes all configuration in one place
- Uses Pydantic Settings for automatic environment variable loading
- Provides type safety and validation
- Enforces production settings validation

**Why Pydantic Settings**:
- Type coercion (string "true" → boolean True)
- Validation on startup
- Documentation through type hints
- 12-factor app compliance

---

### 3.3 app/core/database.py

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# Session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency for getting database session
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

**Why This File Exists**:
- Manages database connections
- Provides connection pooling for performance
- Creates session dependency for FastAPI
- Handles transactions (commit/rollback)

**Why Async SQLAlchemy**:
- Non-blocking database operations
- Better performance under load
- Works with async/await syntax

---

### 3.4 app/core/security.py

```python
from datetime import datetime, timedelta
from jose import jwt
from passlib.hash import bcrypt
from uuid import uuid4

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hash(password, rounds=12)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "jti": str(uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode and validate JWT token"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

class AccessTokenBlacklist:
    """Redis-based token blacklist for revocation"""
    
    async def is_blacklisted(self, jti: str) -> bool:
        # Check if token JTI is in blacklist
        pass
    
    async def add(self, jti: str, expiry: int):
        # Add token to blacklist with TTL
        pass
```

**Why This File Exists**:
- Handles password hashing (security critical)
- Creates and validates JWT tokens
- Manages token blacklist for logout/revocation

**Why bcrypt with 12 rounds**:
- Industry standard for password hashing
- Adaptive cost factor prevents brute force
- Salted automatically

**Why JWT**:
- Stateless authentication
- Scalable across multiple servers
- Short-lived tokens minimize damage from theft

---

### 3.5 app/core/dependencies.py

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.permissions import Role, check_role
from app.modules.users.models import User
from app.modules.users.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # Decode token, check blacklist, fetch user
    pass

async def require_roles(*roles: Role):
    """Dependency to require specific roles"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False))
) -> User | None:
    """Get current user if authenticated, otherwise None"""
    # Same as get_current_user but returns None if not authenticated
    pass

async def get_pagination(page: int = 1, page_size: int = 20):
    """Pagination dependency"""
    return {"skip": (page - 1) * page_size, "limit": page_size}
```

**Why This File Exists**:
- Provides reusable dependencies for routes
- Handles authentication logic in one place
- Enables role-based access control
- Standardizes pagination across endpoints

---

### 3.6 app/core/exceptions.py

```python
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any

class UnauthorizedException(Exception):
    """401 Unauthorized"""
    def __init__(self, message: str = "Not authenticated"):
        self.message = message

class ForbiddenException(Exception):
    """403 Forbidden"""
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message

class NotFoundException(Exception):
    """404 Not Found"""
    def __init__(self, message: str = "Resource not found"):
        self.message = message

class ValidationException(Exception):
    """422 Validation Error"""
    def __init__(self, message: str = "Validation error", details: dict = None):
        self.message = message
        self.details = details or {}

class ConflictException(Exception):
    """409 Conflict"""
    def __init__(self, message: str = "Resource conflict"):
        self.message = message

# Exception handlers
async def unauthorized_exception_handler(request, exc: UnauthorizedException):
    return JSONResponse(status_code=401, content={"error": "unauthorized", "message": exc.message})

async def forbidden_exception_handler(request, exc: ForbiddenException):
    return JSONResponse(status_code=403, content={"error": "forbidden", "message": exc.message})

# ... more handlers
```

**Why This File Exists**:
- Defines custom exception classes
- Provides consistent error responses
- Centralizes error handling logic

---

### 3.7 app/core/health.py

```python
from fastapi import APIRouter
from app.core.database import engine
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic liveness check"""
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check():
    """Readiness check - can the app handle requests?"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis()
    }
    
    all_up = all(v == "up" for v in checks.values())
    
    return {
        "status": "ok" if all_up else "degraded",
        **checks
    }

async def check_database() -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "up"
    except Exception:
        return "down"

async check_redis() -> str:
    try:
        r = await redis.from_url(settings.REDIS_URL)
        await r.ping()
        return "up"
    except Exception:
        return "down"
```

**Why This File Exists**:
- Kubernetes/Container orchestration uses these endpoints
- `/health` - Is the container running?
- `/ready` - Is the container ready to receive traffic?

---

### 3.8 app/core/cache.py

```python
import redis.asyncio as redis
import json
from typing import Any, Optional

class Cache:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        await self.redis.set(key, json.dumps(value), ex=ttl)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

cache = Cache()
```

**Why This File Exists**:
- Provides caching layer for frequently accessed data
- Reduces database load
- Improves response times

---

### 3.9 app/core/metrics.py

```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Database metrics
DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

**Why This File Exists**:
- Exposes metrics for Prometheus
- Enables monitoring and alerting
- Tracks performance and usage

---

### 3.10 app/core/observability.py

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

def setup_observability():
    """Initialize Sentry for error tracking"""
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
    )
```

**Why This File Exists**:
- Error tracking and debugging
- Performance monitoring
- Release health tracking

---

### 3.11 app/core/permissions.py

```python
from enum import Enum
from functools import wraps

class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

class Permission(str, Enum):
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    COURSES_READ = "courses:read"
    COURSES_WRITE = "courses:write"
    # ... more permissions

ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],
    Role.INSTRUCTOR: [
        Permission.COURSES_READ, Permission.COURSES_WRITE,
        # ...
    ],
    Role.STUDENT: [
        Permission.COURSES_READ,
        # ...
    ],
}

def check_role(user_role: Role, required_roles: list[Role]) -> bool:
    """Check if user has required role"""
    return user_role in required_roles

def check_permission(user_role: Role, required_permission: Permission) -> bool:
    """Check if role has required permission"""
    return required_permission in ROLE_PERMISSIONS.get(user_role, [])
```

**Why This File Exists**:
- Defines roles and permissions
- Enables role-based access control (RBAC)
- Separates authorization from authentication

---

### 3.12 app/core/model_registry.py

```python
from sqlalchemy.orm import declarative_base

# Import all models to register them with SQLAlchemy
from app.modules.users.models import User
from app.modules.courses.models.course import Course
from app.modules.courses.models.lesson import Lesson
from app.modules.enrollments.models import Enrollment
# ... import all models

Base = declarative_base()

# This ensures all models are imported before create_all is called
__all__ = [
    "Base",
    "User",
    "Course",
    "Lesson",
    # ... all models
]
```

**Why This File Exists**:
- Central registry of all SQLAlchemy models
- Used by Alembic for migrations
- Ensures all models are loaded

---

## 4. Middleware (app/core/middleware/)

### 4.1 app/core/middleware/rate_limit.py

```python
import redis.asyncio as redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiting"""
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or user ID)
        client_id = self.get_client_id(request)
        
        # Check rate limit
        allowed = await self.check_rate_limit(client_id)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(self.remaining)
        
        return response
    
    async def check_rate_limit(self, client_id: str) -> bool:
        # Redis-based token bucket implementation
        key = f"ratelimit:{client_id}"
        # ... implementation
        pass
```

**Why This File Exists**:
- Prevents abuse and DDoS attacks
- Protects expensive operations
- Uses Redis for distributed rate limiting

---

### 4.2 app/core/middleware/security_headers.py

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        
        return response
```

**Why This File Exists**:
- Adds HTTP security headers
- Protects against common web vulnerabilities
- XSS, clickjacking, MIME sniffing prevention

---

### 4.3 app/core/middleware/request_logging.py

```python
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )
        
        return response
```

**Why This File Exists**:
- Logs all HTTP requests/responses
- Helps debugging
- Enables performance monitoring

---

### 4.4 app/core/middleware/response_envelope.py

```python
class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Wrap response in envelope for consistent format
        # Only for JSON responses
        if response.headers.get("content-type") == "application/json":
            # ... implementation
            pass
        
        return response
```

**Why This File Exists**:
- Provides consistent API response format
- Enables metadata (pagination, etc.) in responses

---

## 5. API Module (app/api/)

### 5.1 app/api/__init__.py

Empty file - marks directory as package.

---

### 5.2 app/api/v1/__init__.py

Empty file - marks directory as package.

---

### 5.3 app/api/v1/api.py

```python
from fastapi import APIRouter
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.courses.routers.course_router import router as courses_router
from app.modules.courses.routers.lesson_router import router as lessons_router
from app.modules.enrollments.router import router as enrollments_router
from app.modules.quizzes.routers.quiz_router import router as quizzes_router
from app.modules.quizzes.routers.question_router import router as questions_router
from app.modules.quizzes.routers.attempt_router import router as attempts_router
from app.modules.certificates.router import router as certificates_router
from app.modules.files.router import router as files_router
from app.modules.analytics.router import router as analytics_router

api_router = APIRouter()

# Include all module routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(courses_router, prefix="/courses", tags=["Courses"])
# ... more routers
```

**Why This File Exists**:
- Aggregates all API routes in one place
- Provides API versioning (/api/v1/)
- Organizes routes by tags for documentation

---

## 6. Modules (app/modules/)

### 6.1 Authentication Module (app/modules/auth/)

This is the most critical module - handles all authentication.

#### app/modules/auth/__init__.py
Empty file - marks directory as package.

#### app/modules/auth/models.py

```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime

from app.core.model_registry import Base

class RefreshToken(Base):
    """Refresh token for session management"""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_jti = Column(String(64), unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Why This Model Exists**:
- Stores refresh tokens in database (not JWT)
- Enables token revocation
- Tracks token expiration

#### app/modules/auth/schemas.py

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=100)
    role: str = "student"

class UserLogin(BaseModel):
    """Schema for login"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AuthResponse(BaseModel):
    """Full auth response with user data"""
    user: "UserResponse\"
    access_token: str
    refresh_token: str
```

**Why These Schemas Exist**:
- Validate incoming request data
- Serialize outgoing response data
- Provide API documentation automatically

#### app/modules/auth/service.py

```python
from app.core.security import hash_password, verify_password, create_access_token
from app.modules.users.repositories.user_repository import UserRepository
from app.modules.auth.models import RefreshToken

class AuthService:
    """Authentication business logic"""
    
    async def register(self, db, email: str, password: str, full_name: str, role: str):
        # Check if user exists
        # Hash password
        # Create user
        # Generate tokens
        # Return response
    
    async def login(self, db, email: str, password: str):
        # Find user
        # Verify password
        # Generate tokens
        # Return response
    
    async def refresh_tokens(self, db, refresh_token: str):
        # Validate refresh token
        # Check if not revoked
        # Check if not expired
        # Generate new access token
        # Return new tokens
    
    async def logout(self, db, refresh_token: str):
        # Revoke refresh token
        pass
```

**Why This Service Exists**:
- Contains authentication business logic
- Separates logic from API routes
- Reusable across different entry points

#### app/modules/auth/router.py

```python
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.modules.auth.schemas import *
from app.modules.auth.service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db = Depends(get_db)):
    return await auth_service.register(db, **user_data.dict())

@router.post("/login")
async def login(credentials: UserLogin, db = Depends(get_db)):
    return await auth_service.login(db, credentials.email, credentials.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_data: RefreshTokenRequest, db = Depends(get_db)):
    return await auth_service.refresh_tokens(db, refresh_data.refresh_token)

@router.post("/logout")
async def logout(refresh_data: LogoutRequest, db = Depends(get_db), current_user = Depends(get_current_user)):
    return await auth_service.logout(db, refresh_data.refresh_token, current_user.id)
```

**Why This Router Exists**:
- Defines HTTP endpoints
- Maps URLs to service functions
- Handles request/response conversion

---

### 6.2 Users Module (app/modules/users/)

Manages user accounts and profiles.

#### app/modules/users/models.py

```python
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4
from datetime import datetime

from app.core.model_registry import Base

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="student", nullable=False)  # admin, instructor, student
    is_active = Column(Boolean, default=True, nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    profile_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
```

**Why This Model Exists**:
- Central user account storage
- Supports different roles (admin, instructor, student)
- Tracks account status and metadata

#### app/modules/users/schemas.py

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    email_verified_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_metadata: Optional[dict] = None
    is_active: Optional[bool] = None
```

#### app/modules/users/router.py

```python
@router.get("/", response_model=UserListResponse)
async def list_users(
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.ADMIN)),
    pagination = Depends(get_pagination)
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
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    # Get current user profile
```

#### app/modules/users/services/user_service.py

```python
class UserService:
    async def create_user(self, db, email: str, password: str, full_name: str, role: str):
        # Create new user
        
    async def update_user(self, db, user_id: UUID, updates: dict):
        # Update user
        
    async def get_user_by_email(self, db, email: str):
        # Find user by email
        
    async def change_password(self, db, user_id: UUID, old_password: str, new_password: str):
        # Change password
```

#### app/modules/users/repositories/user_repository.py

```python
class UserRepository:
    async def get_by_id(self, db, user_id: UUID) -> Optional[User]:
        return await db.get(User, user_id)
    
    async def get_by_email(self, db, email: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, db, user: User) -> User:
        db.add(user)
        await db.flush()
        return user
```

**Why Split into Service and Repository**:
- **Repository**: Data access layer (database queries)
- **Service**: Business logic layer
- Clean separation of concerns
- Easier testing (can mock either layer)

---

### 6.3 Courses Module (app/modules/courses/)

Manages courses and lessons.

#### app/modules/courses/models/course.py

```python
class Course(Base):
    """Course model"""
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    difficulty_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    is_published = Column(Boolean, default=False, index=True)
    thumbnail_url = Column(String(500), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    course_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### app/modules/courses/models/lesson.py

```python
class Lesson(Base):
    """Lesson model"""
    __tablename__ = "lessons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # For text lessons
    lesson_type = Column(String(50), nullable=False)  # video, text, quiz, assignment
    order_index = Column(Integer, nullable=False)
    parent_lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    video_url = Column(String(500), nullable=True)
    is_preview = Column(Boolean, default=False)  # Free preview
    lesson_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Why This Structure**:
- Courses contain multiple lessons
- Lessons have different types (video, text, quiz)
- Supports nested lessons (parent_lesson_id)
- SEO-friendly slugs

#### app/modules/courses/schemas/course.py

```python
class CourseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    slug: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    thumbnail_url: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    metadata: Optional[dict] = None

class CourseResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: Optional[str]
    instructor_id: UUID
    category: Optional[str]
    difficulty_level: Optional[str]
    is_published: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

#### app/modules/courses/routers/course_router.py

```python
@router.get("/", response_model=CourseListResponse)
async def list_courses(
    category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    is_published: bool = True,
    pagination = Depends(get_pagination)
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
    # Get course details

@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    course_data: CourseUpdate,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Update course

@router.post("/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: UUID,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Publish course
```

#### app/modules/courses/routers/lesson_router.py

```python
@router.get("/{course_id}/lessons", response_model=LessonListResponse)
async def list_lessons(course_id: UUID):
    # List lessons for a course

@router.post("/{course_id}/lessons", response_model=LessonResponse)
async def create_lesson(
    course_id: UUID,
    lesson_data: LessonCreate,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Create lesson

@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: UUID):
    # Get lesson details
```

#### app/modules/courses/services/course_service.py

```python
class CourseService:
    async def create_course(self, db, instructor_id: UUID, course_data: dict) -> Course:
        # Generate slug if not provided
        slug = course_data.get("slug") or self.generate_slug(course_data["title"])
        
        # Check for duplicate slug
        existing = await self.course_repo.get_by_slug(db, slug)
        if existing:
            raise ConflictException("Course with this title already exists")
        
        # Create course
        course = Course(
            title=course_data["title"],
            slug=slug,
            instructor_id=instructor_id,
            **course_data
        )
        
        return await self.course_repo.create(db, course)
    
    async def publish_course(self, db, course_id: UUID, instructor_id: UUID) -> Course:
        # Validate course has lessons
        # Update is_published to True
        pass
```

#### app/modules/courses/repositories/course_repository.py

```python
class CourseRepository:
    async def get_by_id(self, db, course_id: UUID) -> Optional[Course]:
        return await db.get(Course, course_id)
    
    async def get_by_slug(self, db, slug: str) -> Optional[Course]:
        result = await db.execute(
            select(Course).where(Course.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def list_with_filters(
        self, db, 
        category: str = None,
        difficulty_level: str = None,
        is_published: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> List[Course]:
        query = select(Course).where(Course.is_published == is_published)
        
        if category:
            query = query.where(Course.category == category)
        if difficulty_level:
            query = query.where(Course.difficulty_level == difficulty_level)
        
        query = query.offset(skip).limit(limit).order_by(Course.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
```

---

### 6.4 Enrollments Module (app/modules/enrollments/)

Tracks student enrollments and progress.

#### app/modules/enrollments/models.py

```python
class Enrollment(Base):
    """Student course enrollment"""
    __tablename__ = "enrollments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")  # active, completed, dropped, expired
    progress_percentage = Column(Numeric(5,2), default=0)
    completed_lessons_count = Column(Integer, default=0)
    total_lessons_count = Column(Integer, default=0)
    total_time_spent_seconds = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    certificate_issued_at = Column(DateTime, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    review = Column(Text, nullable=True)

class LessonProgress(Base):
    """Individual lesson progress"""
    __tablename__ = "lesson_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"))
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"))
    status = Column(String(50), default="not_started")  # not_started, in_progress, completed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    last_position_seconds = Column(Integer, default=0)
    completion_percentage = Column(Numeric(5,2), default=0)
    attempts_count = Column(Integer, default=0)
```

**Why This Structure**:
- Enrollment: Overall course progress
- LessonProgress: Per-lesson tracking
- Enables detailed analytics

#### app/modules/enrollments/router.py

```python
@router.post("/", response_model=EnrollmentResponse)
async def enroll_in_course(
    enrollment_data: EnrollmentCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Create enrollment

@router.get("/my-courses", response_model=EnrollmentListResponse)
async def my_enrollments(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get current user's enrollments

@router.put("/{enrollment_id}/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    enrollment_id: UUID,
    lesson_id: UUID,
    progress_data: LessonProgressUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Update lesson progress

@router.post("/{enrollment_id}/lessons/{lesson_id}/complete")
async def mark_lesson_complete(
    enrollment_id: UUID,
    lesson_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Mark lesson as complete
```

#### app/modules/enrollments/service.py

```python
class EnrollmentService:
    async def enroll_student(self, db, student_id: UUID, course_id: UUID) -> Enrollment:
        # Check course exists and is published
        # Check not already enrolled
        # Get total lessons count
        # Create enrollment
        
    async def update_progress(
        self, db, 
        enrollment_id: UUID, 
        lesson_id: UUID,
        time_spent: int,
        position: int
    ) -> LessonProgress:
        # Update or create lesson progress
        # Recalculate enrollment progress
        # Update completion percentage
        
    async def complete_enrollment(self, db, enrollment_id: UUID):
        # Mark enrollment as completed
        # Issue certificate if eligible
```

---

### 6.5 Quizzes Module (app/modules/quizzes/)

Assessment and quiz functionality.

#### app/modules/quizzes/models/quiz.py

```python
class Quiz(Base):
    """Quiz attached to a lesson"""
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quiz_type = Column(String(50), default="graded")  # practice, graded
    passing_score = Column(Numeric(5,2), default=70.0)
    time_limit_minutes = Column(Integer, nullable=True)
    max_attempts = Column(Integer, nullable=True)
    shuffle_questions = Column(Boolean, default=True)
    shuffle_options = Column(Boolean, default=True)
    show_correct_answers = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
```

#### app/modules/quizzes/models/question.py

```python
class QuizQuestion(Base):
    """Quiz question"""
    __tablename__ = "quiz_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"))
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice, true_false, short_answer, essay
    points = Column(Numeric(5,2), default=1.0)
    order_index = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    options = Column(JSONB, nullable=True)  # [{"id": "a", "text": "..."}]
    correct_answer = Column(String(500), nullable=True)
```

#### app/modules/quizzes/models/attempt.py

```python
class QuizAttempt(Base):
    """Student quiz attempt"""
    __tablename__ = "quiz_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"))
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"))
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(50), default="in_progress")  # in_progress, submitted, graded
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    score = Column(Numeric(6,2), nullable=True)
    max_score = Column(Numeric(6,2), nullable=True)
    percentage = Column(Numeric(6,2), nullable=True)
    is_passed = Column(Boolean, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    answers = Column(JSONB, nullable=True)  # [{"question_id": "...", "answer": "..."}]
```

#### app/modules/quizzes/routers/quiz_router.py

```python
@router.get("/", response_model=QuizListResponse)
async def list_quizzes(course_id: UUID):
    # List quizzes for course

@router.post("/", response_model=QuizResponse)
async def create_quiz(
    course_id: UUID,
    quiz_data: QuizCreate,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Create quiz

@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: UUID):
    # Get quiz details

@router.post("/{quiz_id}/publish", response_model=QuizResponse)
async def publish_quiz(
    quiz_id: UUID,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Publish quiz
```

#### app/modules/quizzes/routers/attempt_router.py

```python
@router.post("/attempts", response_model=AttemptStartResponse)
async def start_attempt(
    quiz_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Start new quiz attempt

@router.get("/attempts/start", response_model=QuizTakeResponse)
async def get_quiz_for_taking(
    quiz_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get quiz questions for taking

@router.post("/attempts/{attempt_id}/submit", response_model=AttemptResultResponse)
async def submit_attempt(
    attempt_id: UUID,
    submit_data: AttemptSubmitRequest,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Submit quiz answers and get grade

@router.get("/attempts/{attempt_id}", response_model=AttemptResultResponse)
async def get_attempt_result(
    attempt_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get attempt result

@router.get("/attempts/my-attempts", response_model=List[AttemptResponse])
async def my_attempts(
    quiz_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # List user's attempts for quiz
```

#### app/modules/quizzes/services/attempt_service.py

```python
class AttemptService:
    async def start_attempt(self, db, quiz_id: UUID, enrollment_id: UUID) -> QuizAttempt:
        # Check max attempts not exceeded
        # Create new attempt with next attempt number
        # Return attempt
        
    async def grade_attempt(self, db, attempt_id: UUID, answers: List[dict]) -> QuizAttempt:
        # Get quiz questions
        # Compare answers to correct answers
        # Calculate score and percentage
        # Determine pass/fail
        # Update attempt status
        # Update enrollment progress
        
    async def can_take_quiz(self, db, quiz_id: UUID, enrollment_id: UUID) -> bool:
        # Check if quiz is published
        # Check max attempts not exceeded
        # Check enrollment exists
```

---

### 6.6 Certificates Module (app/modules/certificates/)

Generates completion certificates.

#### app/modules/certificates/models.py

```python
class Certificate(Base):
    """Course completion certificate"""
    __tablename__ = "certificates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), unique=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    certificate_number = Column(String(50), unique=True, index=True)
    pdf_path = Column(String(1024), nullable=False)
    completion_date = Column(DateTime, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
```

#### app/modules/certificates/service.py

```python
class CertificateService:
    async def generate_certificate(self, db, enrollment_id: UUID) -> Certificate:
        # Get enrollment
        # Check if already has certificate
        # Check if course is completed
        # Generate certificate number
        # Generate PDF
        # Save certificate
        
    async def verify_certificate(self, db, certificate_number: str) -> Certificate:
        # Look up by certificate number
        # Return certificate details
        
    async def revoke_certificate(self, db, certificate_id: UUID, reason: str):
        # Mark certificate as revoked
        # Record revocation reason
```

**Why This Service Exists**:
- Generates PDF certificates using fpdf2
- Unique certificate numbers for verification
- Supports revocation

---

### 6.7 Files Module (app/modules/files/)

File upload and storage.

#### app/modules/files/models.py

```python
class UploadedFile(Base):
    """Uploaded file metadata"""
    __tablename__ = "uploaded_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String(255), unique=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_url = Column(String(1024), nullable=False)
    storage_path = Column(String(1024), nullable=False)
    file_type = Column(String(50), default="other")  # image, video, document
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    folder = Column(String(100), default="uploads")
    storage_provider = Column(String(50), default="local")  # local, s3
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### app/modules/files/storage/base.py

```python
class StorageBase:
    """Abstract base class for storage backends"""
    
    async def upload(self, file: UploadFile, folder: str) -> UploadResult:
        raise NotImplementedError
    
    async def download(self, file_path: str) -> bytes:
        raise NotImplementedError
    
    async def delete(self, file_path: str):
        raise NotImplementedError
    
    async def get_signed_url(self, file_path: str, expiry: int = 900) -> str:
        raise NotImplementedError
```

#### app/modules/files/storage/local.py

```python
class LocalStorage(StorageBase):
    """Local filesystem storage"""
    
    async def upload(self, file: UploadFile, folder: str) -> UploadResult:
        # Generate unique filename
        # Save to local directory
        # Return file info
        
    async def get_signed_url(self, file_path: str, expiry: int = 900) -> str:
        # Return direct file URL (no signing for local)
```

#### app/modules/files/storage/s3.py

```python
class S3Storage(StorageBase):
    """AWS S3 storage"""
    
    async def upload(self, file: UploadFile, folder: str) -> UploadResult:
        # Upload to S3 bucket
        # Return S3 URL
        
    async def get_signed_url(self, file_path: str, expiry: int = 900) -> str:
        # Generate pre-signed URL
        # Return signed URL
```

**Why Multiple Storage Backends**:
- Local: Simple for development
- S3: Scalable for production
- Easy to swap implementations

#### app/modules/files/router.py

```python
@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile,
    folder: str = "uploads",
    is_public: bool = False,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Handle file upload

@router.get("/my-files", response_model=FileListResponse)
async def my_files(
    file_type: str = None,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # List user's uploaded files

@router.get("/download/{file_id}")
async def download_file(
    file_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Download or redirect to file
```

---

### 6.8 Analytics Module (app/modules/analytics/)

Reporting and analytics.

#### app/modules/analytics/router.py

```python
@router.get("/my-progress", response_model=MyProgressSummary)
async def my_progress(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get student's learning progress

@router.get("/my-dashboard", response_model=MyDashboardResponse)
async def my_dashboard(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get student's personalized dashboard

@router.get("/courses/{course_id}", response_model=CourseAnalyticsResponse)
async def course_analytics(
    course_id: UUID,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Get course analytics (instructor view)

@router.get("/instructors/{instructor_id}/overview", response_model=InstructorOverviewResponse)
async def instructor_overview(
    instructor_id: UUID,
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Get instructor's courses overview

@router.get("/system/overview", response_model=SystemOverviewResponse)
async def system_overview(
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.ADMIN))
):
    # Get system-wide analytics (admin only)
```

#### app/modules/analytics/services/course_analytics_service.py

```python
class CourseAnalyticsService:
    async def get_course_stats(self, db, course_id: UUID) -> dict:
        # Total enrollments
        # Active students
        # Completion rate
        # Average rating
        # Average progress
        
    async def get_lesson_completion_rates(self, db, course_id: UUID) -> dict:
        # Per-lesson completion rates
        # Identify difficult lessons
        
    async def get_quiz_performance(self, db, course_id: UUID) -> dict:
        # Quiz pass rates
        # Average scores
        # Common wrong answers
```

---

### 6.9 Payments Module (app/modules/payments/)

Payment processing integration.

#### app/modules/payments/models.py

```python
class Payment(Base):
    """Payment record"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    stripe_payment_intent_id = Column(String(255), unique=True)
    stripe_subscription_id = Column(String(255))
    stripe_invoice_id = Column(String(255), unique=True)
    stripe_customer_id = Column(String(255))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=True)
    payment_type = Column(String(20))  # one_time, recurring, trial
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(3), default="EGP")
    status = Column(String(20), default="pending")  # pending, succeeded, failed, refunded
    plan_name = Column(String(100), nullable=True)
    tax_amount = Column(Numeric(10,2), default=0)
    total_amount = Column(Numeric(10,2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class Subscription(Base):
    """Subscription record"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    stripe_subscription_id = Column(String(255), unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    plan_name = Column(String(100))
    status = Column(String(20), default="incomplete")  # trial, active, past_due, canceled
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
```

#### app/modules/payments/router.py

```python
@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: CreatePaymentIntent,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Create Stripe payment intent

@router.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(
    sub_data: CreateSubscription,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Create Stripe subscription

@router.get("/my-payments", response_model=PaymentListResponse)
async def my_payments(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # List user's payments

@router.get("/my-subscriptions", response_model=List[SubscriptionResponse])
async def my_subscriptions(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # List user's subscriptions

@router.get("/revenue/summary", response_model=RevenueSummaryResponse)
async def revenue_summary(
    currency: str = "EGP",
    db = Depends(get_db),
    current_user = Depends(require_roles(Role.ADMIN))
):
    # Get revenue summary (admin only)

@router.post("/webhooks/myfatoorah")
async def myfatoorah_webhook(
    request: Request,
    db = Depends(get_db)
):
    # Handle MyFatoorah payment webhook

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db = Depends(get_db)
):
    # Handle Stripe payment webhook
```

**Why Multiple Payment Providers**:
- MyFatoorah: Popular in MENA region for EGP
- Stripe: Global, subscriptions support
- Paymob: Alternative Egyptian provider

---

### 6.10 Emails Module

Email templates and sending (handled by tasks).

---

## 7. Tasks Module (app/tasks/)

Background job processing with Celery.

### 7.1 app/tasks/celery_app.py

```python
from celery import Celery

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

# Configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300,
    task_soft_time_limit=240,
    
    # Task routing
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.certificate_tasks.*": {"queue": "certificates"},
        "app.tasks.progress_tasks.*": {"queue": "progress"},
        "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
    
    # Beat schedule
    beat_schedule={
        "weekly-progress-report": {
            "task": "app.tasks.email_tasks.send_weekly_progress_report",
            "schedule": crontab(minute=0, hour=9, day_of_week="monday"),
        },
        "daily-course-reminders": {
            "task": "app.tasks.email_tasks.send_course_reminders",
            "schedule": crontab(minute=0, hour=10),
        },
    },
)
```

**Why This File Exists**:
- Central Celery configuration
- Defines task queues
- Configures scheduling

---

### 7.2 app/tasks/email_tasks.py

```python
from .celery_app import celery_app

@celery_app.task(
    name="app.tasks.email_tasks.send_welcome_email",
    max_retries=3,
    default_retry_delay=60
)
def send_welcome_email(user_id: str, email: str, full_name: str):
    """Send welcome email to new user"""
    # Render template
    # Send via SMTP
    pass

@celery_app.task(name="app.tasks.email_tasks.send_password_reset_email")
def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email"""
    pass

@celery_app.task(name="app.tasks.email_tasks.send_course_enrolled_email")
def send_course_enrolled_email(user_id: str, course_id: str):
    """Send enrollment confirmation"""
    pass

@celery_app.task(name="app.tasks.email_tasks.send_certificate_email")
def send_certificate_email(user_id: str, certificate_id: str):
    """Send certificate issued email"""
    pass

@celery_app.task(name="app.tasks.email_tasks.send_weekly_progress_report")
def send_weekly_progress_report():
    """Send weekly progress to all students"""
    pass

@celery_app.task(name="app.tasks.email_tasks.send_course_reminders")
def send_course_reminders():
    """Send reminders to inactive students"""
    pass
```

**Why These Tasks Exist**:
- Email sending is slow
- Don't want user to wait for email
- Can retry if failed

---

### 7.3 app/tasks/certificate_tasks.py

```python
@celery_app.task(
    name="app.tasks.certificate_tasks.generate_certificate",
    max_retries=2,
    time_limit=120
)
def generate_certificate(enrollment_id: str):
    """Generate PDF certificate"""
    # Load enrollment data
    # Load course and student data
    # Generate PDF using fpdf2
    # Save PDF to storage
    # Create certificate record
    pass

@celery_app.task(name="app.tasks.certificate_tasks.revoke_certificate")
def revoke_certificate(certificate_id: str, reason: str):
    """Revoke certificate"""
    pass
```

**Why Background**:
- PDF generation is CPU intensive
- Takes several seconds
- Don't block API response

---

### 7.4 app/tasks/progress_tasks.py

```python
@celery_app.task(name="app.tasks.progress_tasks.update_enrollment_progress")
def update_enrollment_progress(enrollment_id: str):
    """Recalculate enrollment progress"""
    # Get all lesson progress
    # Calculate completion percentage
    # Update enrollment
    pass

@celery_app.task(name="app.tasks.progress_tasks.calculate_course_statistics")
def calculate_course_statistics(course_id: str):
    """Calculate and cache course stats"""
    pass
```

---

### 7.5 app/tasks/webhook_tasks.py

```python
@celery_app.task(
    name="app.tasks.webhook_tasks.dispatch_webhook",
    max_retries=3,
    default_retry_delay=30
)
def dispatch_webhook(webhook_url: str, event_type: str, payload: dict):
    """Dispatch webhook to external URL"""
    # HTTP POST to webhook_url
    # Handle response
    pass
```

---

### 7.6 app/tasks/dispatcher.py

```python
from app.core.config import settings

def send_task(task_name: str, *args, fallback=None, **kwargs):
    """
    Hybrid task dispatcher.
    
    Development: Run inline (synchronous)
    Production: Queue to Celery
    """
    if settings.TASKS_FORCE_INLINE:
        # Run synchronously
        return _run_fallback(task_name, *args, fallback=fallback, **kwargs)
    else:
        # Queue to Celery
        celery_app.send_task(task_name, args=args, kwargs=kwargs)
        return "queued"
```

**Why This Design**:
- Dev: No need to run Celery workers
- Prod: Full async processing
- Easy to switch between modes

---

## 8. Utils Module (app/utils/)

### 8.1 app/utils/constants.py

```python
# User roles
ROLE_ADMIN = "admin"
ROLE_INSTRUCTOR = "instructor"
ROLE_STUDENT = "student"

# Lesson types
LESSON_TYPE_VIDEO = "video"
LESSON_TYPE_TEXT = "text"
LESSON_TYPE_QUIZ = "quiz"
LESSON_TYPE_ASSIGNMENT = "assignment"

# Quiz types
QUIZ_TYPE_PRACTICE = "practice"
QUIZ_TYPE_GRADED = "graded"

# Enrollment status
ENROLLMENT_ACTIVE = "active"
ENROLLMENT_COMPLETED = "completed"
ENROLLMENT_DROPPED = "dropped"
ENROLLMENT_EXPIRED = "expired"

# Payment status
PAYMENT_PENDING = "pending"
PAYMENT_SUCCEEDED = "succeeded"
PAYMENT_FAILED = "failed"
PAYMENT_REFUNDED = "refunded"

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
```

### 8.2 app/utils/pagination.py

```python
def paginate(query, page: int = 1, page_size: int = 20):
    """Add pagination to SQLAlchemy query"""
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)

def get_pagination_params(page: int = 1, page_size: int = 20):
    """Get pagination parameters"""
    return {
        "page": page,
        "page_size": page_size,
        "skip": (page - 1) * page_size,
        "limit": page_size
    }

def create_pagination_meta(page: int, page_size: int, total: int):
    """Create pagination metadata"""
    total_pages = (total + page_size - 1) // page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
```

### 8.3 app/utils/validators.py

```python
from pydantic import validator

def validate_email(value: str):
    """Validate email format"""
    if "@" not in value:
        raise ValueError("Invalid email format")
    return value

def validate_password_strength(password: str):
    """Validate password meets requirements"""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain uppercase")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain lowercase")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain digit")
    return password

def validate_slug(slug: str):
    """Validate URL slug format"""
    import re
    if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug):
        raise ValueError("Invalid slug format")
    return slug
```

---

## 9. Tests (tests/)

### 9.1 tests/conftest.py

Pytest configuration and shared fixtures.

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    # Create test database
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def client(test_db):
    # Override database dependency
    async def override_get_db():
        async with test_db() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

**Why This File Exists**:
- Shared test fixtures
- Database setup/teardown
- Test client configuration

---

### 9.2 tests/test_auth.py

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
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

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 200

# ... more auth tests
```

---

### 9.3 Other Test Files

| File | Purpose |
|------|---------|
| `test_courses.py` | Course API tests |
| `test_enrollments.py` | Enrollment tests |
| `test_quizzes.py` | Quiz tests |
| `test_certificates.py` | Certificate tests |
| `test_files.py` | File upload tests |
| `test_health.py` | Health check tests |
| `test_permissions.py` | Permission tests |
| `test_analytics.py` | Analytics tests |
| `test_webhooks.py` | Webhook tests |
| `test_rate_limit_rules.py` | Rate limiting tests |

---

## 10. Configuration Files

### 10.1 requirements.txt

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.36
alembic>=1.14.0
psycopg2-binary>=2.9.10
asyncpg>=0.30.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.2.0
redis>=5.0.0
celery>=5.4.0
flower>=2.0.0
python-multipart>=0.0.10
python-fsdp>=1.1.0
pydantic>=2.10.0
pydantic-settings>=2.7.1
httpx>=0.28.0
prometheus-client>=0.21.0
sentry-sdk>=2.0.0
fpdf2>=2.7.0
boto3>=1.35.0
```

### 10.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd --create-home --shell /bin/bash nobody
RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
```

### 10.3 docker-compose.yml

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
    volumes:
      - ./app:/app

  celery_worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q emails,certificates,progress
    environment:
      - DATABASE_URL=postgresql+asyncpg://lms_user:lms_password@postgres:5432/lms
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery_beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info

  flower:
    build: .
    command: celery -A app.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=lms
      - POSTGRES_USER=lms_user
      - POSTGRES_PASSWORD=lms_password
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

### 10.4 alembic.ini

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+asyncpg://lms_user:lms_password@localhost:5432/lms

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

---

## 11. Scripts

### 11.1 scripts/create_admin.py

```python
"""Create admin user"""
import asyncio
from app.core.database import async_session_maker
from app.core.security import hash_password
from app.modules.users.models import User
from uuid import uuid4

async def create_admin():
    async with async_session_maker() as session:
        admin = User(
            id=uuid4(),
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True,
            email_verified_at=datetime.utcnow()
        )
        session.add(admin)
        await session.commit()
        print("Admin user created!")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

### 11.2 scripts/seed_demo_data.py

```python
"""Seed database with demo data"""
# Creates:
# - 3 demo users (admin, instructor, student)
# - 1 demo course with 3 lessons
# - 1 quiz with 2 questions
# - 1 enrollment with progress
# - 1 certificate
```

### 11.3 scripts/generate_postman_collection.py

```python
"""Generate Postman collection from API routes"""
# Parses OpenAPI spec
# Creates Postman collection JSON
```

---

## 12. Why These Technologies Were Chosen

### FastAPI

| Factor | Reason |
|--------|--------|
| Performance | Async, comparable to Node.js |
| Type Safety | Pydantic v2, automatic validation |
| Documentation | Auto-generates Swagger/ReDoc |
| Developer Experience | Minimal boilerplate, clear errors |

### PostgreSQL

| Factor | Reason |
|--------|--------|
| ACID | Critical for payments/enrollments |
| JSON Support | Flexible metadata storage |
| Indexing | Excellent performance |
| Reliability | 30+ years production use |

### SQLAlchemy 2.0

| Factor | Reason |
|--------|--------|
| Async Support | Works with async/await |
| Type Safety | Mapped annotations |
| Migration Integration | Works with Alembic |

### Redis

| Factor | Reason |
|--------|--------|
| Multi-purpose | Cache + Queue + Rate Limiting |
| Performance | Sub-millisecond operations |
| Persistence | AOF for durability |

### Celery

| Factor | Reason |
|--------|--------|
| Python Native | No external dependencies |
| Distributed | Scale horizontally |
| Scheduling | Celery Beat for cron tasks |
| Monitoring | Flower dashboard |

### bcrypt

| Factor | Reason |
|--------|--------|
| Industry Standard | Well-audited |
| Adaptive | Cost factor prevents brute force |
| Salted | Rainbow table attacks ineffective |

### Docker

| Factor | Reason |
|--------|--------|
| Consistency | Same environment everywhere |
| Isolation | Services don't conflict |
| Scaling | Easy to add more workers |

---

## Summary

This project has been documented file-by-file. Each file serves a specific purpose:

| Category | Files | Purpose |
|----------|-------|---------|
| Core | 12 | Infrastructure, security, config |
| Middleware | 4 | Cross-cutting concerns |
| Modules | 50+ | Business logic |
| Tasks | 6 | Background processing |
| Utils | 3 | Helpers |
| Tests | 16 | Quality assurance |
| Config | 10+ | Deployment |

The architecture follows these principles:
1. **Separation of Concerns** - Routes → Services → Repositories
2. **Async-First** - All I/O is non-blocking
3. **Type Safety** - Pydantic + SQLAlchemy 2.0
4. **Production-Ready** - Docker, monitoring, error tracking
5. **Security by Default** - JWT, bcrypt, rate limiting

---

*This documentation covers every single file in the LMS backend project, explaining what it does and why it exists.*
