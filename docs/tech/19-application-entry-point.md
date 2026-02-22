# Complete Application Entry Point - main.py

This document provides an extremely detailed explanation of the main.py file, the FastAPI application setup, middleware configuration, and how the entire application is initialized.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Imports and Initialization](#2-imports-and-initialization)
3. [Model Loading](#3-model-loading)
4. [Lifespan Events](#4-lifespan-events)
5. [FastAPI Application Creation](#5-fastapi-application-creation)
6. [CORS Middleware](#6-cors-middleware)
7. [Compression Middleware](#7-compression-middleware)
8. [Trusted Host Middleware](#8-trusted-host-middleware)
9. [Security Headers Middleware](#9-security-headers-middleware)
10. [Request Logging Middleware](#10-request-logging-middleware)
11. [Metrics Middleware](#11-metrics-middleware)
12. [Response Envelope Middleware](#12-response-envelope-middleware)
13. [Rate Limiting Middleware](#13-rate-limiting-middleware)
14. [Exception Handlers](#14-exception-handlers)
15. [Router Inclusion](#15-router-inclusion)
16. [Metrics Router](#16-metrics-router)
17. [Root Endpoint](#17-root-endpoint)
18. [Complete Flow](#18-complete-flow)

---

## 1. Overview

**Location:** `app/main.py`

This file is the entry point for the entire LMS Backend application. It:
- Initializes all models
- Configures middleware
- Sets up exception handlers
- Registers all API routers
- Configures observability (Sentry)

---

## 2. Imports and Initialization

```python
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.metrics import MetricsMiddleware, build_metrics_router, metrics_available
from app.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    ResponseEnvelopeMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.middleware.rate_limit import RateLimitRule
from app.core.model_registry import load_all_models
from app.core.observability import init_sentry_for_api

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
```

### Why This Setup?

| Import | Purpose |
|--------|---------|
| `logging` | Application logging |
| `asynccontextmanager` | Lifespan context manager |
| `Path` | File path operations |
| `FastAPI` | Web framework |
| `CORSMiddleware` | Cross-origin requests |
| `GZipMiddleware` | Response compression |
| `TrustedHostMiddleware` | Host validation |

---

## 3. Model Loading

```python
# Load all SQLAlchemy models
load_all_models()

# Initialize Sentry for error tracking
init_sentry_for_api()
```

### Model Loading

```python
def load_all_models():
    """Import all models to register them with SQLAlchemy Base."""
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
```

**Why:** Ensures all models are imported before any database operations.

### Sentry Initialization

```python
def init_sentry_for_api():
    """Initialize Sentry for error tracking."""
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT_EFFECTIVE,
            release=settings.SENTRY_RELEASE,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            send_default_pii=settings.SENTRY_SEND_PII,
        )
```

---

## 4. Lifespan Events

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup: Create required directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CERTIFICATES_DIR).mkdir(parents=True, exist_ok=True)
    
    yield
    # Shutdown: Cleanup if needed
```

### Startup Tasks

| Task | Purpose |
|------|---------|
| Create upload directory | Store user uploads |
| Create certificates directory | Store generated PDFs |

### Directory Structure

```
uploads/                  # User uploaded files
  ├── images/
  ├── documents/
  └── videos/

certificates/             # Generated certificates
  └── pdfs/
```

---

## 5. FastAPI Application Creation

```python
app = FastAPI(
    title=settings.PROJECT_NAME,           # "LMS Backend"
    version=settings.VERSION,               # "1.0.0"
    debug=settings.DEBUG,                  # True/False
    lifespan=lifespan,                    # Startup/shutdown events
    docs_url="/docs" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
    redoc_url="/redoc" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
    openapi_url="/openapi.json" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
)
```

### Documentation URLs

| Setting | Development | Production |
|---------|-------------|------------|
| /docs | Enabled | Disabled |
| /redoc | Enabled | Disabled |
| /openapi.json | Enabled | Disabled |

---

## 6. CORS Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### CORS Configuration

```python
# Example CORS_ORIGINS
CORS_ORIGINS = [
    "http://localhost:3000",    # React dev server
    "http://localhost:8080",     # Vue dev server
    "https://app.example.com", # Production
]
```

### What CORS Does

```
┌─────────────────────────────────────────────────────────────────┐
│                    CORS REQUEST FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Browser                    Server                              │
│     │                          │                                 │
│     │──── GET /api ──────────▶│                                 │
│     │◀─── 200 OK + CORS ─────│                                 │
│     │     (Access-Control-    │                                 │
│     │      Allow-Origin: *)  │                                 │
│                                                                 │
│  PREFLIGHT (OPTIONS):                                          │
│     │                          │                                 │
│     │── OPTIONS /api ────────▶│                                 │
│     │◀─ 200 OK + CORS ───────│                                 │
│     │     (Allow-Methods:     │                                 │
│     │      GET, POST, etc.)   │                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Compression Middleware

```python
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Compression Settings

| Setting | Value | Description |
|---------|-------|-------------|
| minimum_size | 1000 bytes | Only compress responses > 1KB |

### Compression Benefits

- **Bandwidth**: Up to 70% reduction for JSON
- **Speed**: Faster page loads
- **Cost**: Lower data transfer costs

---

## 8. Trusted Host Middleware

```python
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
```

### Trusted Hosts

```python
TRUSTED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
    "api.example.com",    # Production API
    "app.example.com",    # Production frontend
]
```

### Purpose

Prevents HTTP Host header attacks by validating the Host header matches allowed hosts.

---

## 9. Security Headers Middleware

```python
if settings.SECURITY_HEADERS_ENABLED:
    app.add_middleware(SecurityHeadersMiddleware)
```

### Security Headers Added

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| Referrer-Policy | no-referrer | Control referrer |
| X-Permitted-Cross-Domain-Policies | none | Restrict Adobe |
| Permissions-Policy | camera=(), mic=(), geo=() | Disable features |
| Content-Security-Policy | frame-ancestors 'none' | XSS protection |
| Strict-Transport-Security | max-age=31536000 | Force HTTPS |

---

## 10. Request Logging Middleware

```python
app.add_middleware(RequestLoggingMiddleware)
```

### What It Logs

```
2024-01-15 10:30:00 INFO  [app.middleware.request_logging] POST /api/v1/courses status=201 duration=0.123s
2024-01-15 10:30:01 INFO  [app.middleware.request_logging] GET /api/v1/courses/123 status=200 duration=0.045s
2024-01-15 10:30:02 INFO  [app.middleware.request_logging] DELETE /api/v1/courses/123 status=204 duration=0.089s
```

### Logged Information

- HTTP Method
- Request Path
- Response Status Code
- Request Duration

---

## 11. Metrics Middleware

```python
if settings.METRICS_ENABLED and metrics_available():
    app.add_middleware(MetricsMiddleware, excluded_paths={settings.METRICS_PATH})
```

### Metrics Available

- Request count by endpoint
- Request duration histogram
- Response size
- Active connections

### Prometheus Format

```prometheus
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/courses",status="200"} 1234

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/api/v1/courses",le="0.1"} 987
```

---

## 12. Response Envelope Middleware

```python
if settings.API_RESPONSE_ENVELOPE_ENABLED:
    app.add_middleware(
        ResponseEnvelopeMiddleware,
        success_message=settings.API_RESPONSE_SUCCESS_MESSAGE,
        excluded_paths=settings.API_RESPONSE_ENVELOPE_EXCLUDED_PATHS,
    )
```

### Envelope Format

**Without Envelope:**
```json
{"id": "123", "name": "Course"}
```

**With Envelope:**
```json
{
  "message": "Success",
  "data": {"id": "123", "name": "Course"}
}
```

### Excluded Paths

```python
API_RESPONSE_ENVELOPE_EXCLUDED_PATHS = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
    "/api/v1/health",
    "/api/v1/ready",
    "/api/v1/auth/token",
]
```

---

## 13. Rate Limiting Middleware

```python
# Exclude certain paths from rate limiting
rate_limit_excluded_paths = list(settings.RATE_LIMIT_EXCLUDED_PATHS)
if settings.METRICS_ENABLED and settings.METRICS_PATH not in rate_limit_excluded_paths:
    rate_limit_excluded_paths.append(settings.METRICS_PATH)

# Define rate limit rules
rate_limit_rules: list[RateLimitRule] = [
    RateLimitRule(
        name="auth",
        path_prefixes=settings.AUTH_RATE_LIMIT_PATHS,
        limit=settings.AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE,
        period_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        key_mode="ip",
    ),
    RateLimitRule(
        name="upload",
        path_prefixes=settings.FILE_UPLOAD_RATE_LIMIT_PATHS,
        limit=settings.FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR,
        period_seconds=settings.FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS,
        key_mode="user_or_ip",
    ),
]

# Add middleware
app.add_middleware(
    RateLimitMiddleware,
    limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    period_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    use_redis=settings.RATE_LIMIT_USE_REDIS,
    redis_url=settings.REDIS_URL,
    key_prefix=settings.RATE_LIMIT_REDIS_PREFIX,
    excluded_paths=rate_limit_excluded_paths,
    custom_rules=rate_limit_rules,
)
```

### Rate Limit Configuration

| Rule | Path | Limit | Period |
|------|------|-------|--------|
| Default | All | 100 | 60 seconds |
| Auth | /auth/login | 60 | 60 seconds |
| Upload | /files/upload | 100 | 3600 seconds |

### Rate Limit Response

```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds"
}
```

---

## 14. Exception Handlers

```python
register_exception_handlers(app)
```

### Registered Handlers

| Exception | Status Code | Response |
|-----------|-------------|----------|
| AppException | Custom | {"detail": "message"} |
| HTTPException | Custom | {"detail": "detail"} |
| RequestValidationError | 422 | {"detail": [...]} |
| ValueError | 400 | {"detail": "message"} |
| Exception | 500 | {"detail": "Internal server error"} |

---

## 15. Router Inclusion

```python
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
```

### API Router Structure

```python
# app/api/v1/api.py
api_router = APIRouter()

# Include all module routers
_safe_include(api_router, "app.modules.auth.router:router")
_safe_include(api_router, "app.modules.users.router:router")
_safe_include(api_router, "app.modules.courses.routers.course_router:router")
_safe_include(api_router, "app.modules.courses.routers.lesson_router:router")
_safe_include(api_router, "app.modules.enrollments.router:router")
_safe_include(api_router, "app.modules.quizzes.routers.quiz_router:router")
_safe_include(api_router, "app.modules.quizzes.routers.question_router:router")
_safe_include(api_router, "app.modules.quizzes.routers.attempt_router:router")
_safe_include(api_router, "app.modules.analytics.router:router")
_safe_include(api_router, "app.modules.files.router:router")
_safe_include(api_router, "app.modules.certificates.router:router")
_safe_include(api_router, "app.modules.payments.router:router")
```

### All Routes

| Prefix | Module | Endpoints |
|--------|--------|-----------|
| /api/v1/auth | Authentication | 12 |
| /api/v1/users | Users | 5 |
| /api/v1/courses | Courses | 6 |
| /api/v1/lessons | Lessons | 5 |
| /api/v1/enrollments | Enrollments | 8 |
| /api/v1/quizzes | Quizzes | 5 |
| /api/v1/analytics | Analytics | 5 |
| /api/v1/files | Files | 3 |
| /api/v1/certificates | Certificates | 5 |

---

## 16. Metrics Router

```python
if settings.METRICS_ENABLED:
    app.include_router(build_metrics_router(settings.METRICS_PATH))
```

### Metrics Endpoint

```
GET /metrics
```

Returns Prometheus-format metrics.

---

## 17. Root Endpoint

```python
@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {"message": "LMS Backend API"}
```

### Response

```json
{
  "message": "LMS Backend API"
}
```

---

## 18. Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    APPLICATION STARTUP FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Load Models                                                    │
│     └─> Import all SQLAlchemy models                               │
│                                                                     │
│  2. Initialize Sentry                                               │
│     └─> Set up error tracking (if DSN configured)                  │
│                                                                     │
│  3. Create FastAPI App                                             │
│     └─> Configure title, version, docs URLs                         │
│                                                                     │
│  4. Add Middleware (in order)                                      │
│     ├─> CORS (cross-origin requests)                              │
│     ├─> GZip (compression)                                         │
│     ├─> Trusted Host (host validation)                             │
│     ├─> Security Headers (security)                                │
│     ├─> Request Logging (logging)                                   │
│     ├─> Metrics (monitoring)                                       │
│     ├─> Response Envelope (formatting)                             │
│     └─> Rate Limiting (throttling)                                 │
│                                                                     │
│  5. Register Exception Handlers                                    │
│     └─> Handle all exception types                                 │
│                                                                     │
│  6. Include API Routers                                            │
│     ├─> Auth                                                       │
│     ├─> Users                                                      │
│     ├─> Courses                                                   │
│     ├─> Lessons                                                    │
│     ├─> Enrollments                                                │
│     ├─> Quizzes                                                    │
│     ├─> Analytics                                                  │
│     ├─> Files                                                      │
│     ├─> Certificates                                               │
│     └─> Payments                                                  │
│                                                                     │
│  7. Include Metrics Router                                         │
│     └─> /metrics endpoint                                          │
│                                                                     │
│  8. Lifespan Events                                                │
│     ├─> Startup: Create directories                                │
│     └─> Shutdown: Cleanup                                         │
│                                                                     │
│  9. Ready to Serve!                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Summary

The main.py file is the heart of the application, responsible for:

1. **Initialization** - Loading models and configuring Sentry
2. **Application Creation** - Setting up FastAPI with docs
3. **Middleware Stack** - 8+ middleware for security, performance, and monitoring
4. **Error Handling** - Global exception handlers
5. **Router Registration** - Including all module routers
6. **Lifespan Management** - Startup and shutdown events

This setup ensures a secure, performant, and maintainable application.
