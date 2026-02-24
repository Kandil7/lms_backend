# Core Infrastructure Documentation

This document covers all core infrastructure components in `app/core/` including configuration, database, security, caching, permissions, and middleware.

## Table of Contents

1. [Configuration Management](#configuration-management)
2. [Database Setup](#database-setup)
3. [Security Utilities](#security-utilities)
4. [Dependencies](#dependencies)
5. [Caching Layer](#caching-layer)
6. [Permissions System](#permissions-system)
7. [Exception Handling](#exception-handling)
8. [Middleware Components](#middleware-components)
9. [Other Core Utilities](#other-core-utilities)

---

## Configuration Management

**File**: `app/core/config.py`

### Overview

The configuration system uses Pydantic Settings with environment variable support. It provides:
- Environment-specific configuration
- Secrets management integration (Azure Key Vault, HashiCorp Vault)
- Validation of production settings
- Type-safe configuration access

### Settings Class

```python
class Settings(BaseSettings):
    # Project Information
    PROJECT_NAME: str = "LMS Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"]
    DEBUG: bool = True
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    ENABLE_API_DOCS: bool = True
    METRICS_ENABLED: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://..."
    DB_POOL_SIZE: int = 20
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ... many more settings
```

### Environment-Specific Behavior

| Setting | Development | Production |
|---------|-------------|------------|
| `DEBUG` | `True` | `False` (forced) |
| API Docs | Enabled | Disabled |
| Auth | JWT Bearer | Cookies + CSRF |
| Secrets | `.env` file | Azure Key Vault |
| Token Blacklist | Optional | Required |

### Secrets Management

In production, sensitive values are loaded from secrets managers:

```python
# Production validation
if self.ENVIRONMENT == "production":
    # Initialize Azure Key Vault or HashiCorp Vault
    initialize_secrets_manager("azure_key_vault", vault_url=...)
    
    # Load secrets
    self.SECRET_KEY = get_secret("SECRET_KEY")
    self.DATABASE_PASSWORD = get_secret("DATABASE_PASSWORD")
```

### Usage

```python
from app.core.config import settings

# Access configuration
print(settings.DATABASE_URL)
print(settings.ENVIRONMENT)

# All settings are cached
from app.core.config import get_settings  # Returns cached instance
```

---

## Database Setup

**File**: `app/core/database.py`

### Overview

SQLAlchemy-based database setup with:
- Connection pooling
- Session management
- Context manager support
- Health check utilities

### Engine Configuration

```python
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)
```

### Connection Pool Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `DB_POOL_SIZE` | 20 | Number of connections in pool |
| `DB_MAX_OVERFLOW` | 40 | Additional connections when pool exhausted |
| `DB_POOL_TIMEOUT` | 30 | Seconds to wait for connection |
| `DB_POOL_RECYCLE` | 1800 | Recycle connections after 30 min |

### Session Management

#### Dependency Injection

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in FastAPI
@app.get("/users/")
def list_users(db: Session = Depends(get_db)):
    ...
```

#### Context Manager

```python
from app.core.database import session_scope

def some_operation():
    with session_scope() as db:
        # Auto-commits on success
        # Auto-rollbacks on exception
        db.add(some_object)
    # Session automatically closed
```

### Base Class

```python
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass
```

All models inherit from this:

```python
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    ...
```

### Health Check

```python
from app.core.database import check_database_health

def health_check() -> bool:
    """Check if database is accessible"""
    return check_database_health()
```

---

## Security Utilities

**File**: `app/core/security.py`

### Overview

Comprehensive security utilities including:
- Password hashing (bcrypt)
- JWT token creation and validation
- Access token blacklist (revocation)
- Multiple token types

### Password Management

```python
from app.core.security import hash_password, verify_password

# Hash password
hashed = hash_password("secure_password123")

# Verify password
is_valid = verify_password("secure_password123", hashed)
```

**Algorithm**: bcrypt (via passlib)

### JWT Token Management

#### Token Types

| Type | Purpose | Expiration |
|------|---------|------------|
| `access` | API authentication | 15 minutes |
| `refresh` | Token refresh | 30 days |
| `password_reset` | Password recovery | 30 minutes |
| `email_verification` | Email verification | 24 hours |
| `mfa_challenge` | MFA verification | 10 minutes |

#### Token Creation

```python
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    create_email_verification_token,
    create_mfa_challenge_token,
)

# Access token (includes role)
access_token = create_access_token(
    subject=str(user_id),
    role=user.role
)

# Refresh token
refresh_token = create_refresh_token(subject=str(user_id))
```

#### Token Validation

```python
from app.core.security import decode_token, TokenType

payload = decode_token(
    token,
    expected_type=TokenType.ACCESS  # Optional type check
)
# Returns: {"sub": "user_id", "role": "student", "jti": "...", "exp": ...}
```

### Token Blacklist

Enables logout and password-change token revocation:

```python
from app.core.security import blacklist_access_token

# Blacklist an access token
blacklist_access_token(token)

# Check if token is blacklisted (automatic in decode_token)
# If blacklisted, UnauthorizedException is raised
```

**Storage**: Redis (primary) with in-memory fallback

### AccessTokenBlacklist Class

```python
class AccessTokenBlacklist:
    def __init__(self, enabled: bool, redis_url: str, key_prefix: str):
        self.enabled = enabled
        self._redis = Redis.from_url(redis_url) if redis_url else None
        self._memory = {}  # Fallback
    
    def revoke(self, jti: str, exp_epoch: int) -> None:
        """Add token to blacklist"""
    
    def is_revoked(self, jti: str) -> bool:
        """Check if token is blacklisted"""
```

---

## Dependencies

**File**: `app/core/dependencies.py`

### Overview

FastAPI dependency providers for:
- Database sessions
- Authentication
- Authorization (roles and permissions)
- Pagination

### Authentication Dependencies

```python
from app.core.dependencies import (
    get_current_user,
    get_current_user_optional,
)

@app.get("/users/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/courses/")
def list_courses(user: User | None = Depends(get_current_user_optional)):
    # Optional authentication
```

### Authorization Dependencies

```python
from app.core.dependencies import (
    require_roles,
    require_permissions,
)

# Role-based access
@app.post("/courses/")
def create_course(
    course: CourseCreate,
    user: User = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    ...

# Permission-based access
@app.put("/users/{user_id}")
def update_user(
    user_id: UUID,
    data: UserUpdate,
    user: User = Depends(require_permissions(Permission.USERS_EDIT))
):
    ...
```

### Pagination Dependency

```python
from app.core.dependencies import get_pagination

@app.get("/users/")
def list_users(
    pagination: tuple[int, int] = Depends(get_pagination),
    db: Session = Depends(get_db)
):
    page, page_size = pagination
    offset = (page - 1) * page_size
    # Use offset in query
```

---

## Caching Layer

**File**: `app/core/cache.py`

### Overview

Redis-based caching with:
- JSON serialization
- TTL support
- Prefix-based organization
- Cache invalidation

### Cache Client

```python
from app.core.cache import get_app_cache

cache = get_app_cache()

# Set value
cache.set("user:123", {"name": "John"}, ttl=300)

# Get value
data = cache.get("user:123")

# Delete by key
cache.delete("user:123")

# Delete by prefix
cache.delete_by_prefix("user:")
```

### Cache Keys

Standard key prefixes:
- `app:cache` - General cache
- `auth:mfa:*` - MFA codes
- `course:*` - Course data
- `lesson:*` - Lesson data

### Configuration

```python
# Settings
CACHE_ENABLED: bool = True
CACHE_KEY_PREFIX: str = "app:cache"
CACHE_DEFAULT_TTL_SECONDS: int = 120

# Module-specific TTL
COURSE_CACHE_TTL_SECONDS: int = 120
LESSON_CACHE_TTL_SECONDS: int = 120
QUIZ_CACHE_TTL_SECONDS: int = 120
```

---

## Permissions System

**File**: `app/core/permissions.py`

### Overview

Role-Based Access Control (RBAC) with:
- Role hierarchy
- Permission definitions
- Decorator-based enforcement

### Roles

```python
class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"
```

### Permissions

```python
class Permission(str, Enum):
    # User permissions
    USERS_READ = "users:read"
    USERS_EDIT = "users:edit"
    USERS_DELETE = "users:delete"
    
    # Course permissions
    COURSES_CREATE = "courses:create"
    COURSES_EDIT_OWN = "courses:edit_own"
    COURSES_EDIT_ALL = "courses:edit_all"
    COURSES_DELETE = "courses:delete"
    
    # Enrollment permissions
    ENROLLMENTS_CREATE = "enrollments:create"
    ENROLLMENTS_VIEW = "enrollments:view"
    
    # Assignment permissions
    ASSIGNMENTS_CREATE = "assignments:create"
    ASSIGNMENTS_GRADE = "assignments:grade"
    
    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    AUDIT_LOGS_VIEW = "audit_logs:view"
```

### Permission Mapping

```python
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.USERS_READ,
        Permission.USERS_EDIT,
        Permission.USERS_DELETE,
        Permission.COURSES_CREATE,
        Permission.COURSES_EDIT_ALL,
        Permission.COURSES_DELETE,
        Permission.ADMIN_ACCESS,
        Permission.AUDIT_LOGS_VIEW,
        # ... all permissions
    ],
    Role.INSTRUCTOR: [
        Permission.COURSES_CREATE,
        Permission.COURSES_EDIT_OWN,
        Permission.ASSIGNMENTS_CREATE,
        Permission.ASSIGNMENTS_GRADE,
        Permission.ENROLLMENTS_VIEW,
    ],
    Role.STUDENT: [
        Permission.COURSES_READ,
        Permission.ENROLLMENTS_CREATE,
        Permission.ASSIGNMENTS_SUBMIT,
    ],
}
```

### Permission Checking

```python
from app.core.permissions import has_permission, Role, Permission

# Check if role has permission
if has_permission(Role.INSTRUCTOR, Permission.COURSES_CREATE):
    # Allow action

# Using dependency
from app.core.dependencies import require_permissions

@app.post("/courses/")
def create_course(
    user: User = Depends(require_permissions(Permission.COURSES_CREATE))
):
    ...
```

---

## Exception Handling

**File**: `app/core/exceptions.py`

### Custom Exceptions

```python
class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=401, detail=detail)

class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=403, detail=detail)

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)

class ValidationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)

class ConflictException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)
```

### Exception Handler Registration

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request, exc):
        return JSONResponse(
            status_code=401,
            content={"detail": exc.detail}
        )
    
    # ... other handlers
    
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )
```

---

## Middleware Components

**File**: `app/core/middleware/`

### Overview

The project includes multiple middleware components for request/response processing.

### Security Headers Middleware

**File**: `app/core/middleware/security_headers.py`

Adds security headers to all responses:

```python
class SecurityHeadersMiddleware:
    async def __call__(self, request, call_next):
        response = await call_next(request)
        
        # HTTP Strict Transport Security
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
```

### Rate Limit Middleware

**File**: `app/core/middleware/rate_limit.py`

Implements request rate limiting with Redis backend.

#### Configuration

```python
# Global rate limit
RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
RATE_LIMIT_WINDOW_SECONDS: int = 60

# Auth endpoints (stricter)
AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

# File uploads (very strict)
FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR: int = 100

# Assignment submissions
ASSIGNMENT_RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
```

#### RateLimitRule

```python
class RateLimitRule(BaseModel):
    name: str
    path_prefixes: list[str]
    limit: int
    period_seconds: int
    key_mode: Literal["ip", "user_or_ip"]
```

#### Usage

```python
app.add_middleware(
    RateLimitMiddleware,
    limit=100,
    period_seconds=60,
    use_redis=True,
    redis_url=settings.REDIS_URL,
    excluded_paths=["/api/v1/health", "/docs"],
    custom_rules=[
        RateLimitRule(
            name="auth",
            path_prefixes=["/api/v1/auth/login"],
            limit=60,
            period_seconds=60,
            key_mode="ip",
        ),
    ],
)
```

### Request Logging Middleware

**File**: `app/core/middleware/request_logging.py`

Logs all incoming requests and outgoing responses:

```python
class RequestLoggingMiddleware:
    async def __call__(self, request, call_next):
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(f"Response: {response.status_code}")
        
        return response
```

### Response Envelope Middleware

**File**: `app/core/middleware/response_envelope.py`

Wraps responses in a standard envelope format:

```json
{
  "success": true,
  "message": "Success",
  "data": { ... }
}
```

### Security Enhancement Middleware

**File**: `app/core/middleware/security_enhancement.py`

Additional security measures:
- Request body size limits
- URL normalization
- Suspicious pattern detection

---

## Other Core Utilities

### CSRF Protection

**File**: `app/core/csrf_protection.py`

CSRF middleware for cookie-based authentication:

```python
app.add_middleware(
    CSRFMiddleware,
    csrf_protection=get_csrf_protection(),
    exempt_paths=["/docs", "/api/v1/health"],
)
```

### Account Lockout

**File**: `app/core/account_lockout.py`

Prevents brute force attacks:

```python
from app.core.account_lockout import (
    check_account_lockout,
    account_lockout_manager,
)

# Check if account is locked
check_account_lockout(email, ip_address)

# Track failed attempts
account_lockout_manager.increment_failed_attempts(email, ip_address)

# Reset on successful login
account_lockout_manager.reset_failed_attempts(email, ip_address)
```

**Configuration**:
```python
MAX_FAILED_LOGIN_ATTEMPTS: int = 5
ACCOUNT_LOCKOUT_DURATION_SECONDS: int = 900  # 15 minutes
```

### Secrets Management

**File**: `app/core/secrets.py`

Unified secrets access:

```python
from app.core.secrets import (
    initialize_secrets_manager,
    get_secret,
)

# Initialize (Azure Key Vault, Vault, or env vars)
initialize_secrets_manager("azure_key_vault", vault_url="...")

# Get secret
db_password = get_secret("DATABASE_PASSWORD")
```

### Health Checks

**File**: `app/core/health.py`

Application health monitoring:

```python
from app.core.health import check_redis_health

def readiness_check():
    db_ok = check_database_health()
    redis_ok = check_redis_health()
    return db_ok and redis_ok
```

### Observability (Sentry)

**File**: `app/core/observability.py`

Sentry integration for error tracking:

```python
from app.core.observability import init_sentry_for_api

# Initialize
init_sentry_for_api()

# Configure
SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions
```

### Metrics (Prometheus)

**File**: `app/core/metrics.py`

Prometheus metrics collection:

```python
from app.core.metrics import MetricsMiddleware, build_metrics_router

# Add middleware
app.add_middleware(MetricsMiddleware)

# Add metrics endpoint
app.include_router(build_metrics_router("/metrics"))
```

### Webhooks

**File**: `app/core/webhooks.py`

Generic webhook dispatching:

```python
from app.core.webhooks import dispatch_webhook

# Dispatch to multiple targets
await dispatch_webhook(
    event="course.published",
    payload={"course_id": "..."},
)
```

### Log Redaction

**File**: `app/core/log_redaction.py`

Redacts sensitive data from logs:

```python
from app.core.log_redaction import redact_sensitive_data

# Redact before logging
safe_data = redact_sensitive_data({"password": "secret", "email": "test@test.com"})
# Result: {"password": "[REDACTED]", "email": "test@test.com"}
```

### XSS Protection

**File**: `app/core/xss_protection.py`

Input sanitization for XSS prevention:

```python
from app.core.xss_protection import sanitize_html

# Sanitize HTML content
safe_html = sanitize_html(user_input)
```

### Cookie Utilities

**File**: `app/core/cookie_utils.py`

Cookie creation and parsing:

```python
from app.core.cookie_utils import create_access_token_cookie

# Create HTTP-only cookie
cookie = create_access_token_cookie(
    token="...",
    expires_minutes=15,
    domain=settings.APP_DOMAIN,
)
```

### Firebase Integration

**File**: `app/core/firebase.py`

Firebase authentication and cloud functions:

```python
from app.core.firebase import (
    verify_firebase_token,
    send_via_firebase_function,
)

# Verify Firebase token
user_info = await verify_firebase_token(id_token)

# Call Firebase Cloud Function
result = await send_via_firebase_function("sendEmail", {...})
```

### Model Registry

**File**: `app/core/model_registry.py`

Ensures all models are loaded before use:

```python
from app.core.model_registry import load_all_models

# Load all SQLAlchemy models
load_all_models()
```

### Pagination Utilities

**File**: `app/utils/pagination.py`

```python
from app.utils.pagination import paginate

def list_items(db: Session, page: int, page_size: int):
    offset = (page - 1) * page_size
    return db.query(Item).offset(offset).limit(page_size).all()
```

### Constants

**File**: `app/utils/constants.py`

Application-wide constants:

```python
# Roles
ADMIN = "admin"
INSTRUCTOR = "instructor"
STUDENT = "student"

# Course status
DRAFT = "draft"
PUBLISHED = "published"
ARCHIVED = "archived"

# Payment status
PENDING = "pending"
COMPLETED = "completed"
FAILED = "failed"
REFUNDED = "refunded"
```

---

## Configuration Summary

### Required Environment Variables

| Variable | Description | Required In |
|----------|-------------|-------------|
| `DATABASE_URL` | PostgreSQL connection string | All |
| `REDIS_URL` | Redis connection string | All |
| `SECRET_KEY` | JWT signing key | Production |
| `POSTGRES_PASSWORD` | Database password | Production |
| `SMTP_PASSWORD` | Email sending password | Production |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob connection | Production (if using Azure) |

### All Configuration Categories

1. **Project** - Name, version, environment
2. **API** - Prefixes, docs, metrics
3. **Database** - Connection, pooling
4. **Security** - JWT, MFA, CSRF
5. **Authentication** - Methods, tokens
6. **Email** - SMTP configuration
7. **Firebase** - Auth, cloud functions
8. **Storage** - Azure Blob settings
9. **Cache** - Redis, TTL settings
10. **CORS** - Allowed origins
11. **Rate Limiting** - Limits and paths
12. **File Uploads** - Size, extensions
13. **Webhooks** - URLs, secrets
14. **Monitoring** - Sentry configuration
