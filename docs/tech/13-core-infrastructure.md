# Core Infrastructure Documentation

This document provides a comprehensive reference for the core infrastructure components of the LMS Backend system.

---

## Table of Contents

1. Configuration System
2. Database Layer
3. Security & Authentication
4. Permissions System
5. Caching System
6. Exception Handling
7. Middleware Components
8. Dependencies & Injection
9. Health Checks
10. Model Registry

---

## 1. Configuration System

Location: app/core/config.py

The configuration system uses Pydantic BaseSettings for environment-based configuration with validation.

### Key Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| PROJECT_NAME | str | LMS Backend | Project name |
| VERSION | str | 1.0.0 | API version |
| ENVIRONMENT | Literal | development | Environment: development, staging, production |
| DEBUG | bool | True | Debug mode |
| API_V1_PREFIX | str | /api/v1 | API prefix |
| DATABASE_URL | str | postgresql | Database connection |
| SECRET_KEY | str | change-me | JWT signing key |
| ALGORITHM | str | HS256 | JWT algorithm |
| ACCESS_TOKEN_EXPIRE_MINUTES | int | 15 | Access token expiry |
| REFRESH_TOKEN_EXPIRE_DAYS | int | 30 | Refresh token expiry |
| CACHE_ENABLED | bool | True | Cache enabled |
| REDIS_URL | str | redis://localhost:6379/0 | Redis URL |
| RATE_LIMIT_REQUESTS_PER_MINUTE | int | 100 | Requests per minute |

### Usage

```python
from app.core.config import settings

project_name = settings.PROJECT_NAME
```

---

## 2. Database Layer

Location: app/core/database.py

### Components

- Base: SQLAlchemy declarative base
- engine: Database engine with connection pooling
- SessionLocal: Session factory
- get_db(): FastAPI dependency for database sessions
- session_scope(): Context manager for programmatic sessions

### Usage

```python
from app.core.database import get_db, session_scope

# FastAPI dependency
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    pass

# Context manager
with session_scope() as db:
    pass
```

---

## 3. Security & Authentication

Location: app/core/security.py

### Password Handling

```python
from app.core.security import hash_password, verify_password

hashed = hash_password("password")
is_valid = verify_password("password", hashed)
```

### JWT Token Functions

| Function | Purpose |
|----------|---------|
| create_access_token | Create access token (15 min expiry) |
| create_refresh_token | Create refresh token (30 day expiry) |
| create_password_reset_token | Password reset token |
| create_email_verification_token | Email verification token |
| create_mfa_challenge_token | MFA challenge token |
| decode_token | Validate and decode token |
| blacklist_access_token | Revoke token |

---

## 4. Permissions System

Location: app/core/permissions.py

### Roles

- ADMIN: Full system access
- INSTRUCTOR: Course and quiz management
- STUDENT: Learning access

### Permissions

- CREATE_COURSE
- UPDATE_COURSE
- DELETE_COURSE
- VIEW_ANALYTICS
- MANAGE_ENROLLMENTS
- MANAGE_USERS
- MANAGE_QUIZZES

### Usage

```python
from app.core.permissions import has_permission, Role, Permission

if has_permission("instructor", Permission.CREATE_COURSE):
    pass
```

---

## 5. Caching System

Location: app/core/cache.py

### Features

- Redis-backed with in-memory fallback
- JSON serialization
- TTL support
- Prefix-based invalidation

### Usage

```python
from app.core.cache import get_app_cache

cache = get_app_cache()
cache.set_json("key", {"data": "value"}, ttl_seconds=300)
data = cache.get_json("key")
cache.delete_by_prefix("key_prefix:")
```

---

## 6. Exception Handling

Location: app/core/exceptions.py

### Custom Exceptions

| Exception | Status Code |
|-----------|-------------|
| NotFoundException | 404 |
| ForbiddenException | 403 |
| UnauthorizedException | 401 |

---

## 7. Middleware Components

Location: app/core/middleware/

### Security Headers Middleware
Adds X-Content-Type-Options, X-Frame-Options, CSP headers.

### Rate Limit Middleware
Per-client, per-path rate limiting with Redis support.

### Request Logging Middleware
Logs all requests with method, path, status, duration.

---

## 8. Dependencies & Injection

Location: app/core/dependencies.py

### Authentication

- get_current_user: Requires valid JWT
- get_current_user_optional: Returns None if no token

### Authorization

- require_roles(*roles): Role-based access
- require_permissions(*permissions): Permission-based access

### Pagination

- get_pagination(page, page_size): Standard pagination

---

## 9. Health Checks

Location: app/core/health.py

```python
from app.core.database import check_database_health
from app.core.health import check_redis_health

check_database_health()  # Returns bool
check_redis_health()      # Returns bool
```

---

## 10. Model Registry

Location: app/core/model_registry.py

Ensures all SQLAlchemy models are imported before migrations.

---

## Summary

The core infrastructure provides:

1. Configuration with environment-based settings
2. Database with SQLAlchemy ORM
3. Security with JWT tokens
4. Permissions with role-based access control
5. Caching with Redis
6. Exceptions with custom error handling
7. Middleware for security and rate limiting
8. Dependencies for auth and pagination
9. Health checks for monitoring
10. Model registry for migrations
