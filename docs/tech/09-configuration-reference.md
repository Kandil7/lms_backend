# Configuration Reference

## Complete Configuration Guide

This document provides a comprehensive reference for all configuration options in the LMS backend.

---

## 1. Application Settings

### Core Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENVIRONMENT` | str | "development" | Environment name (development/staging/production) |
| `DEBUG` | bool | False | Enable debug mode |
| `SECRET_KEY` | str | - | Secret key for JWT/sessions (32+ chars) |
| `API_DOCS_EFFECTIVE_ENABLED` | bool | True | Enable API documentation |

### API Settings

```python
# app/core/config.py

class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "default-secret-key-change-in-production"
    API_DOCS_EFFECTIVE_ENABLED: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "LMS Backend"
    PROJECT_VERSION: str = "1.0.0"
    ALLOWED_HOSTS: List[str] = ["*"]
```

---

## 2. Database Settings

### PostgreSQL Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | str | "postgresql+asyncpg://..." | Database connection URL |
| `DATABASE_POOL_SIZE` | int | 20 | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | int | 40 | Max overflow connections |
| `DATABASE_POOL_PRE_PING` | bool | True | Test connections before use |
| `DATABASE_POOL_RECYCLE` | int | 3600 | Connection recycle time (seconds) |

```python
# Database URL format
DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database"

# SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

### Database URL Examples

```bash
# Local development
DATABASE_URL=postgresql+asyncpg://lms_user:lms_password@localhost:5432/lms

# Docker
DATABASE_URL=postgresql+asyncpg://lms_user:lms_password@postgres:5432/lms

# Production (SSL)
DATABASE_URL=postgresql+asyncpg://user:password@host.aws-region.rds.amazonaws.com:5432/lms?sslmode=require
```

---

## 3. Redis Settings

### Redis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | str | "redis://..." | Redis connection URL |
| `REDIS_PASSWORD` | str | - | Redis password |

```bash
# Redis URL format
REDIS_URL=redis://[:password]@host:port/database

# Examples
REDIS_URL=redis://localhost:6379/0
REDIS_URL=redis://:password@redis:6379/0
REDIS_URL=redis://:password@redis.cache.amazonaws.com:6379/0
```

### Redis Usage

| Purpose | Database Number |
|---------|-----------------|
| Cache | 0 |
| Celery broker | 0 |
| Token blacklist | 0 |
| Rate limiting | 0 |

---

## 4. JWT & Authentication Settings

### Token Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | 15 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | 30 | Refresh token lifetime |
| `JWT_ALGORITHM` | str | "HS256" | JWT signing algorithm |
| `ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED` | bool | True | Fail-closed in production |

```python
# JWT Settings
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15    # Short-lived for security
REFRESH_TOKEN_EXPIRE_DAYS: int = 30      # Long-lived for UX
JWT_ALGORITHM: str = "HS256"             # HMAC-SHA256
```

### Password Settings

```python
PASSWORD_MIN_LENGTH: int = 8
PASSWORD_REQUIRE_UPPERCASE: bool = True
PASSWORD_REQUIRE_LOWERCASE: bool = True
PASSWORD_REQUIRE_DIGIT: bool = True
PASSWORD_REQUIRE_SPECIAL: bool = False
```

---

## 5. Rate Limiting

### Rate Limit Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RATE_LIMIT_ENABLED` | bool | True | Enable rate limiting |
| `RATE_LIMIT_PER_MINUTE` | int | 100 | General request limit |
| `RATE_LIMIT_AUTH_PER_MINUTE` | int | 60 | Auth endpoint limit |
| `RATE_LIMIT_UPLOAD_PER_HOUR` | int | 100 | Upload limit |

```python
# Rate limiting
RATE_LIMIT_ENABLED: bool = True
RATE_LIMIT_PER_MINUTE: int = 100
RATE_LIMIT_AUTH_PER_MINUTE: int = 60      # Stricter for auth
RATE_LIMIT_UPLOAD_PER_HOUR: int = 100
RATE_LIMIT_STORAGE_PER_HOUR: int = 500
```

---

## 6. CORS Settings

### Cross-Origin Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CORS_ORIGINS` | List[str] | ["http://localhost:3000"] | Allowed origins |
| `CORS_ALLOW_CREDENTIALS` | bool | True | Allow credentials |
| `CORS_ALLOW_METHODS` | List[str] | ["*"] | Allowed methods |
| `CORS_ALLOW_HEADERS` | List[str] | ["*"] | Allowed headers |

```python
# CORS
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "https://yourdomain.com",
]
CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_METHODS: List[str] = ["*"]
CORS_ALLOW_HEADERS: List[str] = ["*"]
```

---

## 7. File Storage

### Storage Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FILE_STORAGE_PROVIDER` | str | "local" | Storage backend (local/s3) |
| `FILE_UPLOAD_DIR` | str | "uploads" | Local upload directory |
| `MAX_UPLOAD_MB` | int | 100 | Max upload size |
| `FILE_DOWNLOAD_URL_EXPIRE_SECONDS` | int | 900 | Signed URL expiry |

### S3 Configuration

```python
FILE_STORAGE_PROVIDER: str = "s3"
AWS_ACCESS_KEY_ID: str = ""
AWS_SECRET_ACCESS_KEY: str = ""
AWS_S3_BUCKET: str = "lms-files"
AWS_REGION: str = "us-east-1"
AWS_S3_ENDPOINT_URL: str = None  # For MinIO/S3-compatible
```

### File Type Allowed

```python
ALLOWED_FILE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "video/mp4",
    "video/webm",
    "application/pdf",
    "application/json",
    "text/csv",
]
```

---

## 8. Email Configuration

### SMTP Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SMTP_HOST` | str | - | SMTP server host |
| `SMTP_PORT` | int | 587 | SMTP server port |
| `SMTP_USER` | str | - | SMTP username |
| `SMTP_PASSWORD` | str | - | SMTP password |
| `SMTP_FROM` | str | "noreply@localhost" | From email address |
| `SMTP_FROM_NAME` | str | "LMS Platform" | From name |

```python
# Email
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
SMTP_FROM: str = "noreply@yourdomain.com"
SMTP_FROM_NAME: str = "LMS Platform"
SMTP_USE_TLS: bool = True
```

---

## 9. Payment Configuration

### Stripe Settings

```python
# Stripe
STRIPE_SECRET_KEY: str = ""
STRIPE_PUBLISHABLE_KEY: str = ""
STRIPE_WEBHOOK_SECRET: str = ""
STRIPE_API_VERSION: str = "2024-12-18.acacia"
```

### MyFatoorah Settings

```python
# MyFatoorah
MYFATOORAH_API_KEY: str = ""
MYFATOORAH_BASE_URL: str = "https://api.myfatoorah.com"
MYFATOORAH_IS_TEST: bool = True
```

### Paymob Settings

```python
# Paymob
PAYMOB_API_KEY: str = ""
PAYMOB_INTEGRATION_ID: int = 0
PAYMOB_IFRAME_ID: int = 0
PAYMOB_HMAC_SECRET: str = ""
```

---

## 10. Celery Configuration

### Task Queue Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TASKS_FORCE_INLINE` | bool | True | Run tasks inline (dev) |
| `CELERY_TASK_TRACK_STARTED` | bool | True | Track task start |
| `CELERY_TASK_TIME_LIMIT` | int | 300 | Hard timeout (seconds) |
| `CELERY_TASK_SOFT_TIME_LIMIT` | int | 240 | Soft timeout |

```python
# Celery
TASKS_FORCE_INLINE: bool = True  # Set to False in production
CELERY_TASK_TRACK_STARTED: bool = True
CELERY_TASK_TIME_LIMIT: int = 300
CELERY_TASK_SOFT_TIME_LIMIT: int = 240
CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
```

---

## 11. Cache Configuration

### Redis Caching

```python
# Caching
CACHE_ENABLED: bool = True
CACHE_DEFAULT_TTL_SECONDS: int = 120
COURSE_CACHE_TTL_SECONDS: int = 300
LESSON_CACHE_TTL_SECONDS: int = 300
ENROLLMENT_CACHE_TTL_SECONDS: int = 60
```

---

## 12. Monitoring

### Sentry Configuration

```python
# Sentry
SENTRY_DSN: str = ""
SENTRY_ENVIRONMENT: str = "development"
SENTRY_TRACES_SAMPLE_RATE: float = 0.1
SENTRY_PROFILES_SAMPLE_RATE: float = 0.1
```

### Prometheus Configuration

```python
# Metrics
METRICS_ENABLED: bool = True
METRICS_ENDPOINT: str = "/metrics"
```

---

## 13. Feature Flags

### Feature Toggles

```python
# Feature flags
EMAIL_VERIFICATION_REQUIRED: bool = True
MFA_ENABLED: bool = True
PAYMENT_ENABLED: bool = True
CERTIFICATE_AUTO_GENERATE: bool = True
ANALYTICS_ENABLED: bool = True
WEBHOOKS_ENABLED: bool = False
```

---

## 14. Environment Examples

### Development (.env)

```bash
# Development
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-not-for-production
API_DOCS_EFFECTIVE_ENABLED=true

# Database
DATABASE_URL=postgresql+asyncpg://lms_user:lms_password@localhost:5432/lms

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=localhost
SMTP_PORT=1025

# Features
TASKS_FORCE_INLINE=true
EMAIL_VERIFICATION_REQUIRED=false
MFA_ENABLED=false
```

### Production (.env.production)

```bash
# Production
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-32-character-secret-key-here
API_DOCS_EFFECTIVE_ENABLED=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@prod-host:5432/lms?sslmode=require

# Redis
REDIS_URL=redis://:password@redis-host:6379/0

# Security
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=true
RATE_LIMIT_PER_MINUTE=100

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# Features
TASKS_FORCE_INLINE=false
EMAIL_VERIFICATION_REQUIRED=true
MFA_ENABLED=true
```

---

## 15. Configuration Validation

### Production Validation

The application validates production settings on startup:

```python
# app/core/config.py
@model_validator(mode="after")
def validate_production_settings(self):
    if self.ENVIRONMENT != "production":
        return self
    
    # Must be off in production
    if self.DEBUG:
        raise ValueError("DEBUG must be false in production")
    
    # Must be strong
    if len(self.SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    
    # Must be fail-closed
    if not self.ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:
        raise ValueError("ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED must be true in production")
    
    # Must not inline tasks
    if self.TASKS_FORCE_INLINE:
        raise ValueError("TASKS_FORCE_INLINE must be false in production")
    
    return self
```

---

## Summary

### Configuration Categories

| Category | Key Variables |
|----------|---------------|
| Core | ENVIRONMENT, DEBUG, SECRET_KEY |
| Database | DATABASE_URL, POOL_SIZE |
| Cache | REDIS_URL, CACHE_ENABLED |
| Auth | JWT settings, PASSWORD settings |
| Security | CORS, RATE_LIMIT |
| Files | FILE_STORAGE_PROVIDER |
| Email | SMTP_HOST, SMTP_PORT |
| Payments | STRIPE, MYFATOORAH |
| Monitoring | SENTRY_DSN |

### Best Practices

1. **Never commit secrets** - Use environment variables
2. **Validate in production** - Fails fast on misconfiguration
3. **Document all settings** - This reference helps
4. **Use feature flags** - Control features without deploys
5. **Separate environments** - Dev/staging/production configs
