# Core Infrastructure Documentation

This document provides an EXTREMELY COMPREHENSIVE reference for the core infrastructure components of the LMS Backend system. Every function, class, and configuration is documented with detailed explanations.

---

## Table of Contents

1. [Configuration System (app/core/config.py)](#1-configuration-system)
2. [Database Layer (app/core/database.py)](#2-database-layer)
3. [Security & Authentication (app/core/security.py)](#3-security--authentication)
4. [Permissions System (app/core/permissions.py)](#4-permissions-system)
5. [Caching System (app/core/cache.py)](#5-caching-system)
6. [Exception Handling (app/core/exceptions.py)](#6-exception-handling)
7. [Middleware Components (app/core/middleware/)](#7-middleware-components)
8. [Dependencies & Injection (app/core/dependencies.py)](#8-dependencies--injection)
9. [Health Checks (app/core/health.py)](#9-health-checks)
10. [Model Registry (app/core/model_registry.py)](#10-model-registry)

---

## 1. Configuration System

**Location:** `app/core/config.py`

The configuration system uses Pydantic BaseSettings for environment-based configuration with automatic validation and type coercion.

### Complete Configuration Parameters

```python
from app.core.config import settings

# Application Settings
PROJECT_NAME: str = "LMS Backend"
VERSION: str = "1.0.0"
ENVIRONMENT: Literal["development", "staging", "production"] = "development"
DEBUG: bool = True
API_V1_PREFIX: str = "/api/v1"

# Database Settings
DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:port/db
DATABASE_URL_SYNC: str  # postgresql+psycopg2://user:pass@host:port/db
SQLALCHEMY_ECHO: bool = False
DB_POOL_SIZE: int = 20
DB_MAX_OVERFLOW: int = 40

# Security Settings
SECRET_KEY: str  # Generate: python -c "import secrets; print(secrets.token_hex(32))"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 60
MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES: int = 5
MFA_LOGIN_CODE_LENGTH: int = 6
MFA_LOGIN_CODE_EXPIRE_MINUTES: int = 5
ACCESS_TOKEN_BLACKLIST_ENABLED: bool = True
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED: bool = True
ACCESS_TOKEN_BLACKLIST_PREFIX: str = "token:blacklist"

# Redis Settings
REDIS_URL: str = "redis://localhost:6379/0"

# Cache Settings
CACHE_ENABLED: bool = True
CACHE_KEY_PREFIX: str = "cache"
CACHE_DEFAULT_TTL_SECONDS: int = 120

# Email Settings
EMAIL_FROM: str = "noreply@example.com"
SMTP_HOST: str = "smtp.example.com"
SMTP_PORT: int = 587
SMTP_USERNAME: str = ""
SMTP_PASSWORD: str = ""
SMTP_USE_TLS: bool = True
SMTP_USE_SSL: bool = False

# File Storage Settings
FILE_STORAGE_PROVIDER: Literal["local", "s3"] = "local"
UPLOAD_DIR: str = "uploads"
CERTIFICATES_DIR: str = "certificates"
MAX_UPLOAD_MB: int = 100
ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".pdf", ".mp4", ".webm"]

# AWS S3 Settings
AWS_ACCESS_KEY_ID: str = ""
AWS_SECRET_ACCESS_KEY: str = ""
AWS_REGION: str = "us-east-1"
AWS_S3_BUCKET: str = ""
AWS_S3_BUCKET_URL: str = ""

# Rate Limiting
RATE_LIMIT_USE_REDIS: bool = True
RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
RATE_LIMIT_WINDOW_SECONDS: int = 60

# CORS
CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

# Celery
CELERY_BROKER_URL: str = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
CELERY_TASK_ALWAYS_EAGER: bool = False
TASKS_FORCE_INLINE: bool = False
```

### Configuration Loading Priority

1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

### Usage Examples

```python
# Import settings
from app.core.config import settings

# Access configuration
print(f"Project: {settings.PROJECT_NAME}")
print(f"Database: {settings.DATABASE_URL}")
print(f"Environment: {settings.ENVIRONMENT}")

# Check environment
if settings.ENVIRONMENT == "production":
    # Production-specific logic
    pass

# Database URL is automatically constructed from components
db_url = settings.DATABASE_URL  # Already formatted
```

---

## 2. Database Layer

**Location:** `app/core/database.py`

The database layer provides SQLAlchemy ORM integration with async support, connection pooling, and session management.

### Components

```python
from app.core.database import (
    Base,                    # SQLAlchemy declarative base
    engine,                  # Async database engine
    AsyncSessionLocal,       # Async session factory
    get_db,                  # FastAPI dependency
    session_scope,           # Context manager
    check_database_health    # Health check function
)
```

### Database Engine Configuration

```python
# Engine is created with these settings:
engine = create_async_engine(
    DATABASE_URL,
    echo=SQLALCHEMY_ECHO,           # Print SQL queries
    pool_size=DB_POOL_SIZE,         # Connection pool size
    max_overflow=DB_MAX_OVERFLOW,   # Overflow connections
    pool_pre_ping=True,             # Verify connections
    pool_recycle=3600,             # Recycle after 1 hour
)
```

### Session Management

```python
# Method 1: FastAPI Dependency (Recommended for API routes)
from fastapi import Depends

async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# Method 2: Context Manager (For scripts/tasks)
from app.core.database import session_scope

async def my_function():
    async with session_scope() as db:
        user = User(email="test@example.com")
        db.add(user)
        await db.commit()
    # Session automatically closed

# Method 3: Direct Session (For more control)
async def manual_session():
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(...)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Health Check

```python
from app.core.database import check_database_health

# Returns True if database is accessible
is_healthy = check_database_health()
```

### Model Base Class

```python
from app.core.database import Base

# All models inherit from Base
class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True)
    # ... fields
```

### Why Async?

| Feature | Sync | Async |
|---------|------|-------|
| Performance | Blocking | Non-blocking |
| Concurrency | Limited | High |
| Use Case | Scripts | Web API |
| Database Driver | psycopg2 | asyncpg |

---

## 3. Security & Authentication

**Location:** `app/core/security.py`

The security module handles all authentication and authorization functionality including password hashing, JWT token management, and token blacklisting.

### Token Types

The system uses different JWT token types for different purposes:

```python
from app.core.security import TokenType

# Token Types
TokenType.ACCESS              # Short-lived (15 min) - API authentication
TokenType.REFRESH            # Long-lived (30 days) - Token refresh
TokenType.PASSWORD_RESET     # Short-lived (30 min) - Password recovery
TokenType.EMAIL_VERIFICATION # Medium-lived (60 min)TokenType.MFA - Email verification
_CHALLENGE      # Very short-lived (5 min) - MFA verification
```

### Password Handling

The system uses bcrypt for secure password hashing:

```python
from app.core.security import hash_password, verify_password

# Hash a password
hashed = hash_password("my_secure_password")
# Result: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ePLF3Sp.c6DO

# Verify a password
is_valid = verify_password("my_secure_password", hashed)
# Returns: True or False
```

**Why bcrypt?**
- Adaptive cost factor (work factor)
- Automatic salt generation
- 20+ years of security review
- Resistant to rainbow table attacks

### JWT Token Functions

```python
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    create_email_verification_token,
    create_mfa_challenge_token,
    decode_token,
    blacklist_access_token,
)

# Create access token (15 minute expiry)
access_token = create_access_token(
    subject="user-uuid-here",  # User ID
    role="instructor"           # User role
)

# Create refresh token (30 day expiry)
refresh_token = create_refresh_token(subject="user-uuid-here")

# Create password reset token (30 minute expiry)
reset_token = create_password_reset_token(subject="user-uuid-here")

# Decode and validate token
payload = decode_token(
    token=access_token,
    expected_type="access",  # Verify token type
    check_blacklist=True      # Check if revoked
)

# Payload structure:
# {
#     "sub": "user-uuid-here",      # Subject (user ID)
#     "role": "instructor",         # User role
#     "jti": "unique-token-id",    # JWT ID
#     "typ": "access",              # Token type
#     "iat": 1704067200,           # Issued at
#     "exp": 1704068100            # Expiration
# }

# Blacklist a token (for logout)
blacklist_access_token(access_token)
```

### Token Blacklist System

The system implements token blacklisting for logout and forced password changes:

```python
from app.core.security import get_access_token_blacklist

# Access the blacklist
blacklist = get_access_token_blacklist()

# Manually revoke a token
blacklist.revoke(
    jti="token-unique-id",      # JWT ID from token
    exp_epoch=1704068100        # Expiration timestamp
)

# Check if token is revoked
is_revoked = blacklist.is_revoked(jti="token-unique-id")
```

**How Blacklisting Works:**

1. When a token is created, it gets a unique `jti` (JWT ID)
2. On logout, the `jti` is added to the blacklist
3. On each authenticated request, the blacklist is checked
4. Blacklisted tokens are rejected with 401

**Implementation Details:**

- **Redis Backend** (Production): Fast, persistent storage
- **In-Memory Fallback** (Development): Simple dict with TTL cleanup
- **Fail-Closed** (Production): If Redis fails, reject all requests
- **Fail-Open** (Development): If Redis fails, continue without blacklist

### Complete Token Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TOKEN LIFECYCLE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. LOGIN                                                           │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐        │
│  │  User   │───▶│/auth/login │───▶│ Verify password  │        │
│  │ submits │    │             │    │ + Create tokens  │        │
│  │ creds  │    │             │    └────────┬─────────┘        │
│  └──────────┘    └─────────────┘             │                  │
│                                               ▼                  │
│                                      ┌──────────────────┐       │
│                                      │ Return:          │       │
│                                      │ - access_token   │       │
│                                      │ - refresh_token │       │
│                                      │ - token_type    │       │
│                                      └──────────────────┘       │
│                                                                     │
│  2. API REQUESTS                                                   │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐        │
│  │  User   │───▶│ API Request │───▶│ Validate access  │        │
│  │ makes   │    │ + Header:   │    │ token            │        │
│  │ request │    │ Auth: Bearer│    │ + Check blacklist│        │
│  └──────────┘    └─────────────┘    └────────┬─────────┘        │
│                                               │                  │
│                  ┌───────────────────────────┐                   │
│                  │                           │                   │
│                  ▼                           ▼                   │
│          ┌──────────────┐           ┌──────────────┐          │
│          │ Token Valid  │           │ Token Invalid│          │
│          │ + Process    │           │ + Return 401 │          │
│          │ request     │           │              │          │
│          └──────────────┘           └──────────────┘          │
│                                                                     │
│  3. REFRESH                                                        │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐        │
│  │  User   │───▶│/auth/refresh│───▶│ Verify refresh  │        │
│  │ submits │    │ + Body:     │    │ token            │        │
│  │ refresh │    │ refresh_    │    │ + Revoke old    │        │
│  │ token   │    │ token       │    │ + Create new    │        │
│  └──────────┘    └─────────────┘    │ access_token   │        │
│                                      └────────┬─────────┘        │
│                                               │                  │
│                                               ▼                  │
│                                      ┌──────────────────┐       │
│                                      │ Return new       │       │
│                                      │ access_token    │       │
│                                      └──────────────────┘       │
│                                                                     │
│  4. LOGOUT                                                         │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐        │
│  │  User   │───▶│/auth/logout │───▶│ Blacklist access │       │
│  │ submits │    │ + Headers:   │    │ token            │        │
│  │ logout  │    │ Auth: Bearer│    │ + Revoke refresh │        │
│  └──────────┘    └─────────────┘    │ token           │        │
│                                      └──────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Permissions System

**Location:** `app/core/permissions.py`

The permissions system implements Role-Based Access Control (RBAC) with fine-grained permissions.

### Roles

```python
from app.core.permissions import Role

# Available roles
Role.ADMIN       # Full system access
Role.INSTRUCTOR # Course and quiz management
Role.STUDENT    # Learning access
```

### Permissions

```python
from app.core.permissions import Permission

# Available permissions
Permission.CREATE_COURSE        # Create new courses
Permission.UPDATE_COURSE        # Update existing courses
Permission.DELETE_COURSE        # Delete courses
Permission.VIEW_ANALYTICS        # View analytics
Permission.MANAGE_ENROLLMENTS   # Manage student enrollments
Permission.MANAGE_USERS          # Manage user accounts
Permission.MANAGE_QUIZZES        # Manage quizzes
```

### Role-Permission Mapping

```python
from app.core.permissions import ROLE_PERMISSIONS, Role, Permission

# Admin has all permissions
ROLE_PERMISSIONS[Role.ADMIN] = {
    Permission.CREATE_COURSE,
    Permission.UPDATE_COURSE,
    Permission.DELETE_COURSE,
    Permission.VIEW_ANALYTICS,
    Permission.MANAGE_ENROLLMENTS,
    Permission.MANAGE_USERS,
    Permission.MANAGE_QUIZZES,
}

# Instructor has course and quiz permissions
ROLE_PERMISSIONS[Role.INSTRUCTOR] = {
    Permission.CREATE_COURSE,
    Permission.UPDATE_COURSE,
    Permission.VIEW_ANALYTICS,
    Permission.MANAGE_QUIZZES,
}

# Student has no special permissions
ROLE_PERMISSIONS[Role.STUDENT] = set()  # No special permissions
```

### Check Permissions

```python
from app.core.permissions import has_permission, Role, Permission

# Check if a role has a permission
if has_permission("instructor", Permission.CREATE_COURSE):
    print("Can create courses!")

# Alternative: direct dictionary access
from app.core.permissions import ROLE_PERMISSIONS

role = Role.INSTRUCTOR
permissions = ROLE_PERMISSIONS.get(role, set())
can_create = Permission.CREATE_COURSE in permissions
```

### Permission Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PERMISSION CHECK FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Request → Check Role → Get Permissions → Check Required → Allow  │
│                                                                     │
│  Example: Creating a course                                          │
│                                                                     │
│  1. User submits POST /courses                                      │
│  2. get_current_user dependency extracts user from JWT              │
│  3. require_roles(Role.ADMIN, Role.INSTRUCTOR) decorator runs     │
│  4. Check: user.role in [ADMIN, INSTRUCTOR]                        │
│  5. If true: proceed; else: raise 403 Forbidden                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Caching System

**Location:** `app/core/cache.py`

The caching system provides a unified interface for caching with Redis backend and in-memory fallback.

### Cache Features

- **Redis Backend**: Primary caching layer
- **In-Memory Fallback**: When Redis is unavailable
- **JSON Serialization**: Automatic JSON encoding/decoding
- **TTL Support**: Expire keys after specified time
- **Prefix Support**: Organize cache keys

### Usage

```python
from app.core.cache import get_app_cache

# Get cache instance
cache = get_app_cache()

# Store JSON data (auto-serialized)
cache.set_json(
    "user:123",                           # Key
    {"name": "John", "email": "..."},    # Value
    ttl_seconds=300                       # 5 minutes
)

# Retrieve JSON data
data = cache.get_json("user:123")
# Returns: {"name": "John", "email": "..."} or None

# Delete by prefix (for bulk invalidation)
cache.delete_by_prefix("user:")  # Deletes all user:* keys
```

### Implementation Details

```python
class AppCache:
    def __init__(self, *, enabled, redis_url, key_prefix, default_ttl_seconds):
        self.enabled = enabled
        self.key_prefix = key_prefix
        self.default_ttl_seconds = default_ttl_seconds
        self._memory = {}  # Fallback storage
        self._redis = None  # Redis connection
    
    def get_json(self, key: str) -> Any | None:
        # Try Redis first
        # Fall back to memory if Redis fails
        # Return None if not found
    
    def set_json(self, key: str, value: Any, *, ttl_seconds: int | None = None):
        # Store in Redis with TTL
        # Fall back to memory if Redis fails
    
    def delete_by_prefix(self, prefix: str):
        # Delete all keys matching prefix
        # Both Redis and memory
```

### Cache Keys

The system automatically prefixes all keys:

```python
cache = get_app_cache()

# If key_prefix = "lms"
cache.set_json("course:123", data)
# Actually stored as: lms:course:123
```

### Common Cache Patterns

```python
# Pattern 1: Cache with fallback
def get_course(course_id):
    cache_key = f"course:{course_id}"
    
    # Try cache first
    cached = cache.get_json(cache_key)
    if cached:
        return cached
    
    # Fetch from database
    course = db.query(Course).get(course_id)
    
    # Store in cache
    if course:
        cache.set_json(cache_key, course.to_dict(), ttl_seconds=3600)
    
    return course

# Pattern 2: Invalidate on update
def update_course(course_id, data):
    course = update_in_db(course_id, data)
    
    # Invalidate cache
    cache.delete_by_prefix(f"course:{course_id}")
    
    return course

# Pattern 3: Cache expensive queries
def get_instructor_stats(instructor_id):
    cache_key = f"stats:instructor:{instructor_id}"
    
    cached = cache.get_json(cache_key)
    if cached:
        return cached
    
    # Expensive query
    stats = calculate_stats(instructor_id)
    
    # Cache for 15 minutes
    cache.set_json(cache_key, stats, ttl_seconds=900)
    
    return stats
```

---

## 6. Exception Handling

**Location:** `app/core/exceptions.py`

The exception system provides custom exceptions and global handlers for consistent error responses.

### Custom Exceptions

```python
from app.core.exceptions import (
    AppException,           # Base exception
    NotFoundException,      # 404 - Resource not found
    ForbiddenException,     # 403 - Not authorized
    UnauthorizedException,  # 401 - Invalid credentials
)

# Usage in code
def get_user(user_id):
    user = db.query(User).get(user_id)
    if not user:
        raise NotFoundException(f"User {user_id} not found")
    return user

def delete_course(course, user):
    if course.instructor_id != user.id:
        raise ForbiddenException("You can only delete your own courses")
    # ...

def authenticate(email, password):
    user = verify_credentials(email, password)
    if not user:
        raise UnauthorizedException("Invalid credentials")
    return user
```

### Exception Handlers

The system registers handlers for all exception types:

```python
def register_exception_handlers(app: FastAPI):
    # Custom app exceptions → JSON response
    @app.exception_handler(AppException)
    async def handle_app_exception(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )
    
    # FastAPI HTTP exceptions
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Validation errors (Pydantic)
    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request, exc):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )
    
    # Value errors
    @app.exception_handler(ValueError)
    async def handle_value_error(request, exc):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
    
    # Catch-all for unexpected errors
    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request, exc):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
```

### Error Response Format

All errors follow a consistent format:

```json
// Not Found (404)
{
  "detail": "Resource not found"
}

// Forbidden (403)
{
  "detail": "Not authorized to perform this action"
}

// Unauthorized (401)
{
  "detail": "Could not validate credentials"
}

// Validation Error (422)
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}

// Internal Error (500)
{
  "detail": "Internal server error"
}
```

---

## 7. Middleware Components

**Location:** `app/core/middleware/`

Middleware components process requests and responses globally.

### 7.1 Security Headers Middleware

**File:** `app/core/middleware/security_headers.py`

Adds security headers to all responses:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # Restrict Adobe Flash
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Disable browser features
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
        
        # Force HTTPS in production
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
```

### Security Headers Explained

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| Referrer-Policy | no-referrer | Control referrer info |
| X-Permitted-Cross-Domain-Policies | none | Restrict Adobe Flash |
| Permissions-Policy | camera=(), microphone=(), geolocation=() | Disable browser features |
| Content-Security-Policy | frame-ancestors 'none' | XSS protection |
| Strict-Transport-Security | max-age=31536000 | Force HTTPS |

### 7.2 Rate Limit Middleware

**File:** `app/core/middleware/rate_limit.py`

Per-client rate limiting with Redis support:

```python
class RateLimitMiddleware:
    def __init__(self, app, requests_per_minute=100):
        self.app = app
        self.requests_per_minute = requests_per_minute
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get client identifier
        client_id = self.get_client_id(scope)
        
        # Check rate limit
        if not self.check_rate_limit(client_id):
            # Return 429 Too Many Requests
            await self.send_429_response(send)
            return
        
        # Process request
        await self.app(scope, receive, send)
```

### Rate Limiting Configuration

```python
# In app configuration
RATE_LIMIT_USE_REDIS = True          # Use Redis for distributed rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 100  # Requests per minute
RATE_LIMIT_WINDOW_SECONDS = 60        # Time window
```

### 7.3 Request Logging Middleware

**File:** `app/core/middleware/request_logging.py`

Logs all HTTP requests:

```python
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration:.3f}s"
        )
        
        return response
```

### Logging Format

```
2024-01-15 10:30:00 INFO  POST /api/v1/courses status=201 duration=0.123s
2024-01-15 10:30:01 INFO  GET /api/v1/courses/123 status=200 duration=0.045s
2024-01-15 10:30:02 INFO  DELETE /api/v1/courses/123 status=204 duration=0.089s
```

### Middleware Registration

```python
from fastapi import FastAPI
from app.core.middleware.security_headers import SecurityHeadersMiddleware
from app.core.middleware.rate_limit import RateLimitMiddleware
from app.core.middleware.request_logging import RequestLoggingMiddleware

app = FastAPI()

# Register middleware (order matters - last added runs first)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(SecurityHeadersMiddleware)
```

---

## 8. Dependencies & Injection

**Location:** `app/core/dependencies.py`

FastAPI's dependency injection system provides authentication, authorization, and pagination.

### OAuth2 Scheme

```python
from app.core.dependencies import (
    oauth2_scheme,              # Requires authentication
    optional_oauth2_scheme,     # Optional authentication
)

# In API routes:
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validates JWT and returns user
    pass
```

### Authentication Dependencies

```python
from app.core.dependencies import (
    get_current_user,           # Requires valid JWT
    get_current_user_optional,  # Returns None if no token
)

# Usage: Require authentication
@app.get("/users/me")
async def get_me(user = Depends(get_current_user)):
    return user

# Usage: Optional authentication
@app.get("/courses")
async def list_courses(user = Depends(get_current_user_optional)):
    # User can be None
    if user:
        return get_personalized_courses(user)
    return get_public_courses()
```

### Authorization Dependencies

```python
from app.core.dependencies import (
    require_roles,        # Require specific roles
    require_permissions,  # Require specific permissions
)
from app.core.permissions import Role, Permission

# Require specific roles
@app.post("/courses")
async def create_course(
    course: CourseCreate,
    user = Depends(require_roles(Role.ADMIN, Role.INSTRUCTOR))
):
    # Only admins and instructors can create courses
    return create_course_service(course, user)

# Require specific permissions
@app.delete("/courses/{course_id}")
async def delete_course(
    course_id: UUID,
    user = Depends(require_permissions(Permission.DELETE_COURSE))
):
    # Only users with DELETE_COURSE permission
    return delete_course_service(course_id)

# Multiple roles
@app.get("/users")
async def list_users(
    user = Depends(require_roles(Role.ADMIN))  # Only admins
):
    return get_all_users()
```

### Pagination Dependency

```python
from app.core.dependencies import get_pagination

@app.get("/courses")
async def list_courses(
    pagination: tuple[int, int] = Depends(get_pagination)
):
    page, page_size = pagination
    
    # page: 1, 2, 3, ...
    # page_size: 1-100
    
    offset = (page - 1) * page_size
    courses = db.query(Course).offset(offset).limit(page_size).all()
    
    return {
        "items": courses,
        "page": page,
        "page_size": page_size
    }
```

### Custom Dependencies

You can create custom dependencies:

```python
from fastapi import Depends

# Cache dependency
def get_cache():
    return get_app_cache()

# Use in routes
@app.get("/courses/{course_id}")
async def get_course(
    course_id: UUID,
    cache = Depends(get_cache)
):
    # Try cache first
    cached = cache.get_json(f"course:{course_id}")
    if cached:
        return cached
    
    # Fetch from database
    course = get_course_from_db(course_id)
    
    # Cache result
    cache.set_json(f"course:{course_id}", course, ttl_seconds=3600)
    
    return course
```

---

## 9. Health Checks

**Location:** `app/core/health.py`

Health check endpoints for monitoring and load balancer readiness.

### Health Check Functions

```python
from app.core.health import (
    check_database_health,
    check_redis_health,
)

# Check database connection
is_db_healthy = check_database_health()
# Returns: True if connected, False otherwise

# Check Redis connection
is_redis_healthy = check_redis_health()
# Returns: True if connected, False otherwise

# Combined check
def check_overall_health():
    db_ok = check_database_health()
    redis_ok = check_redis_health()
    
    return {
        "database": "healthy" if db_ok else "unhealthy",
        "redis": "healthy" if redis_ok else "unhealthy",
    }
```

### Health Check Endpoints

The system provides two endpoints:

```python
# GET /api/v1/health
# Lightweight check - just verifies the app is running
{
    "status": "healthy",
    "version": "1.0.0"
}

# GET /api/v1/ready
# Deep check - verifies all dependencies
{
    "database": "connected",
    "redis": "connected"
}
```

### Usage in Load Balancers

```yaml
# Kubernetes readiness probe
readinessProbe:
  httpGet:
    path: /api/v1/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10

# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20
```

---

## 10. Model Registry

**Location:** `app/core/model_registry.py`

Ensures all SQLAlchemy models are imported before migrations run.

### Purpose

Alembic migrations need to know about all models to create tables. The model registry imports all models:

```python
# app/core/model_registry.py
from app.core.database import Base

# Import all models to register them with Base
from app.modules.users.models import User
from app.modules.auth.models import RefreshToken
from app.modules.courses.models.course import Course
from app.modules.courses.models.lesson import Lesson
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.modules.quizzes.models.quiz import Quiz
from app.modules.quizzes.models.question import QuizQuestion
from app.modules.quizzes.models.attempt import QuizAttempt
from app.modules.certificates.models import Certificate
from app.modules.files.models import UploadedFile

# Import this module in alembic/env.py to load all models
```

### Usage in Migrations

```python
# alembic/env.py
from app.core.model_registry import *  # Loads all models
from app.core.database import Base

target_metadata = Base.metadata
```

---

## Summary

The core infrastructure provides a complete foundation for the LMS Backend:

### 1. Configuration System
- Environment-based settings with validation
- All database, security, cache, and app settings

### 2. Database Layer
- SQLAlchemy with async support
- Connection pooling
- Session management
- Health checks

### 3. Security & Authentication
- bcrypt password hashing
- JWT tokens (access, refresh, MFA, password reset)
- Token blacklisting
- Multiple token types

### 4. Permissions System
- Role-based access control (Admin, Instructor, Student)
- Fine-grained permissions
- Decorator-based enforcement

### 5. Caching System
- Redis backend with in-memory fallback
- JSON serialization
- TTL and prefix support

### 6. Exception Handling
- Custom exception classes
- Global handlers
- Consistent error responses

### 7. Middleware Components
- Security headers
- Rate limiting
- Request logging

### 8. Dependencies & Injection
- OAuth2 authentication
- Role-based authorization
- Pagination

### 9. Health Checks
- Lightweight health endpoint
- Deep readiness endpoint

### 10. Model Registry
- Ensures all models loaded for migrations
