# Complete Configuration Reference

This document provides an exhaustive reference for all configuration options in the LMS Backend system. Every setting is documented with its purpose, type, default value, and usage examples.

---

## Table of Contents

1. [Configuration System Overview](#1-configuration-system-overview)
2. [Application Settings](#2-application-settings)
3. [API & Documentation Settings](#3-api--documentation-settings)
4. [Sentry/Observability Settings](#4-sentryobservability-settings)
5. [Webhook Settings](#5-webhook-settings)
6. [Payment Gateway Settings](#6-payment-gateway-settings)
7. [Database Settings](#7-database-settings)
8. [Security & Authentication Settings](#8-security--authentication-settings)
9. [Email Settings](#9-email-settings)
10. [Cache Settings](#10-cache-settings)
11. [CORS & Security Settings](#11-cors--security-settings)
12. [Redis & Rate Limiting Settings](#12-redis--rate-limiting-settings)
13. [File Upload Settings](#13-file-upload-settings)
14. [AWS S3 Settings](#14-aws-s3-settings)
15. [Validation Rules](#15-validation-rules)
16. [Environment-Specific Settings](#16-environment-specific-settings)

---

## 1. Configuration System Overview

The system uses **Pydantic Settings** for configuration management:

```python
from app.core.config import settings

# Access any setting
value = settings.SETTING_NAME
```

### Configuration Sources (Priority Order)

1. **Environment Variables** (Highest)
2. **.env File**
3. **Default Values** (Lowest)

---

## 2. Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROJECT_NAME` | str | "LMS Backend" | Application name |
| `VERSION` | str | "1.0.0" | API version |
| `ENVIRONMENT` | Literal | "development" | Environment: development, staging, production |
| `DEBUG` | bool | True | Enable debug mode |
| `API_V1_PREFIX` | str | "/api/v1" | API URL prefix |

### Usage

```python
print(settings.PROJECT_NAME)  # "LMS Backend"
print(settings.VERSION)       # "1.0.0"
print(settings.ENVIRONMENT)    # "development"
```

---

## 3. API & Documentation Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_API_DOCS` | bool | True | Enable API documentation |
| `STRICT_ROUTER_IMPORTS` | bool | False | Fail on router import errors |
| `METRICS_ENABLED` | bool | True | Enable Prometheus metrics |
| `METRICS_PATH` | str | "/metrics" | Metrics endpoint path |
| `API_RESPONSE_ENVELOPE_ENABLED` | bool | False | Wrap responses in envelope |
| `API_RESPONSE_SUCCESS_MESSAGE` | str | "Success" | Success message in envelope |

### Documentation Endpoints

| Environment | /docs | /redoc | /openapi.json |
|-------------|-------|--------|---------------|
| Development | ✅ Enabled | ✅ Enabled | ✅ Enabled |
| Staging | ✅ Configurable | ✅ Configurable | ✅ Configurable |
| Production | ❌ Disabled | ❌ Disabled | ❌ Disabled |

---

## 4. Sentry/Observability Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SENTRY_DSN` | str \| None | None | Sentry DSN for error tracking |
| `SENTRY_ENVIRONMENT` | str \| None | None | Sentry environment |
| `SENTRY_RELEASE` | str \| None | None | Sentry release version |
| `SENTRY_TRACES_SAMPLE_RATE` | float | 0.0 | Trace sample rate (0-1) |
| `SENTRY_PROFILES_SAMPLE_RATE` | float | 0.0 | Profile sample rate (0-1) |
| `SENTRY_SEND_PII` | bool | False | Send PII to Sentry |
| `SENTRY_ENABLE_FOR_CELERY` | bool | True | Enable Sentry for Celery |

### Sentry Configuration

```python
# In production, set these environment variables:
SENTRY_DSN=https://key@sentry.io/project
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=lms-backend@1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
```

---

## 5. Webhook Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WEBHOOKS_ENABLED` | bool | False | Enable outgoing webhooks |
| `WEBHOOK_TARGET_URLS` | list[str] | [] | List of webhook URLs |
| `WEBHOOK_SIGNING_SECRET` | str \| None | None | Secret for signing webhooks |
| `WEBHOOK_TIMEOUT_SECONDS` | float | 5.0 | Webhook request timeout |

### Webhook Payload

```json
{
  "event": "course.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": "uuid",
    "course_id": "uuid",
    "certificate_id": "uuid"
  },
  "signature": "sha256=..."
}
```

---

## 6. Payment Gateway Settings

### MyFatoorah Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MYFATOORAH_API_KEY` | str \| None | None | MyFatoorah API key |
| `MYFATOORAH_BASE_URL` | str | "https://api.myfatoorah.com" | API base URL |
| `MYFATOORAH_WEBHOOK_SECRET` | str \| None | None | Webhook secret |
| `MYFATOORAH_HTTP_TIMEOUT_SECONDS` | float | 10.0 | HTTP timeout |
| `MYFATOORAH_DEFAULT_PAYMENT_METHOD_ID` | int | 2 | Default payment method |
| `MYFATOORAH_LANGUAGE` | str | "en" | API language |
| `MYFATOORAH_SUBSCRIPTION_DEFAULT_AMOUNT_EGP` | float | 99.0 | Default subscription amount |
| `MYFATOORAH_SUBSCRIPTION_PERIOD_DAYS` | int | 30 | Subscription period |
| `PAYMENTS_MOCK_MODE` | bool | False | Enable mock checkout flow (must be false in production) |

### Paymob Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PAYMOB_API_KEY` | str \| None | None | Paymob API key |
| `PAYMOB_INTEGRATION_ID` | int \| None | None | Integration ID |
| `PAYMOB_IFRAME_ID` | int \| None | None | IFrame ID |
| `PAYMOB_WEBHOOK_SECRET` | str \| None | None | Webhook secret |
| `PAYMOB_BASE_URL` | str | "https://accept.paymob.com/api" | API base URL |
| `PAYMOB_PAYMENT_KEY_EXPIRATION_SECONDS` | int | 3600 | Payment key validity |
| `PAYMOB_HTTP_TIMEOUT_SECONDS` | float | 10.0 | HTTP timeout |
| `PAYMOB_SUBSCRIPTION_DEFAULT_AMOUNT_EGP` | float | 99.0 | Default amount |
| `PAYMOB_SUBSCRIPTION_PERIOD_DAYS` | int | 30 | Subscription period |

---

## 7. Database Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | str | "postgresql+psycopg2://lms:lms@localhost:5432/lms" | Database connection string |
| `SQLALCHEMY_ECHO` | bool | False | Log SQL queries |
| `DB_POOL_SIZE` | int | 20 | Database connection pool size |
| `DB_MAX_OVERFLOW` | int | 40 | Max overflow connections |

### Database URL Format

```
postgresql+psycopg2://username:password@host:port/database
```

### Example

```python
DATABASE_URL=postgresql+psycopg2://admin:password@db.example.com:5432/lms_production
```

### Pool Configuration

```python
# For production, tune these based on expected concurrent connections
DB_POOL_SIZE = 20        # Base connections
DB_MAX_OVERFLOW = 40      # Additional connections when pool is full
# Total max connections = 20 + 40 = 60
```

---

## 8. Security & Authentication Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | str | "change-me" | JWT signing key |
| `ALGORITHM` | str | "HS256" | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | 15 | Access token expiry |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | 30 | Refresh token expiry |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | int | 30 | Password reset token expiry |
| `EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES` | int | 1440 | Email verification token expiry |
| `ALLOW_PUBLIC_ROLE_REGISTRATION` | bool | False | Allow public registration |
| `REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN` | bool | False | Require email verification to login |
| `MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES` | int | 10 | MFA challenge token expiry |
| `MFA_LOGIN_CODE_EXPIRE_MINUTES` | int | 10 | MFA code expiry |
| `MFA_LOGIN_CODE_LENGTH` | int | 6 | MFA code length |
| `ACCESS_TOKEN_BLACKLIST_ENABLED` | bool | True | Enable token blacklist |
| `ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED` | bool | False | Fail closed on blacklist error |
| `ACCESS_TOKEN_BLACKLIST_PREFIX` | str | "auth:blacklist:access" | Redis prefix for blacklist |

### Token Expiry Summary

| Token Type | Expiry | Use Case |
|------------|--------|----------|
| Access Token | 15 minutes | API requests |
| Refresh Token | 30 days | Get new access tokens |
| Password Reset | 30 minutes | Password recovery |
| Email Verification | 1440 minutes (24 hours) | Account verification |
| MFA Challenge | 10 minutes | MFA verification |

### Security Requirements

```python
# Generate a secure SECRET_KEY
import secrets
SECRET_KEY = secrets.token_hex(32)  # 64 character hex string
```

---

## 9. Email Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FRONTEND_BASE_URL` | str | "http://localhost:3000" | Frontend base URL |
| `EMAIL_FROM` | str | "no-reply@lms.local" | From email address |
| `EMAIL_FROM_NAME` | str | "LMS Platform" | From email name |
| `SMTP_HOST` | str \| None | None | SMTP server hostname |
| `SMTP_PORT` | int | 587 | SMTP server port |
| `SMTP_USERNAME` | str \| None | None | SMTP username |
| `SMTP_PASSWORD` | str \| None | None | SMTP password |
| `SMTP_USE_TLS` | bool | True | Use TLS encryption |
| `SMTP_USE_SSL` | bool | False | Use SSL encryption |

### SMTP Configuration Examples

**Gmail:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=True
```

**Amazon SES:**
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USERNAME=AKIAIOSFODNN7EXAMPLE
SMTP_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Mailtrap (Testing):**
```bash
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=username
SMTP_PASSWORD=password
```

---

## 10. Cache Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CACHE_ENABLED` | bool | True | Enable caching |
| `CACHE_KEY_PREFIX` | str | "app:cache" | Redis key prefix |
| `CACHE_DEFAULT_TTL_SECONDS` | int | 120 | Default cache TTL |
| `COURSE_CACHE_TTL_SECONDS` | int | 120 | Course data TTL |
| `LESSON_CACHE_TTL_SECONDS` | int | 120 | Lesson data TTL |
| `QUIZ_CACHE_TTL_SECONDS` | int | 120 | Quiz data TTL |
| `QUIZ_QUESTION_CACHE_TTL_SECONDS` | int | 120 | Quiz question TTL |

### Cache Key Format

```
{prefix}:{key}
Example: app:cache:course:uuid-here
```

### TTL Recommendations

| Data Type | TTL | Reason |
|----------|-----|--------|
| Course list | 5 min | Changes infrequently |
| Course details | 2 min | Updates occasionally |
| Lesson content | 2 min | Updates occasionally |
| Quiz questions | 2 min | May change |
| User data | No cache | Sensitive |

---

## 11. CORS & Security Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CORS_ORIGINS` | list[str] | ["http://localhost:3000"] | Allowed CORS origins |
| `TRUSTED_HOSTS` | list[str] | ["localhost", "127.0.0.1", "testserver"] | Allowed hosts |
| `SECURITY_HEADERS_ENABLED` | bool | True | Enable security headers |

### CORS Origins

```python
# Development
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Production
CORS_ORIGINS=["https://app.example.com", "https://admin.example.com"]
```

---

## 12. Redis & Rate Limiting Settings

### Redis Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | str | "redis://localhost:6379/0" | Redis connection URL |
| `CELERY_BROKER_URL` | str | "redis://localhost:6379/1" | Celery broker URL |
| `CELERY_RESULT_BACKEND` | str | "redis://localhost:6379/2" | Celery result backend |
| `TASKS_FORCE_INLINE` | bool | True | Run tasks inline (not async) |

### Rate Limiting Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RATE_LIMIT_USE_REDIS` | bool | True | Use Redis for rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | int | 100 | Default rate limit |
| `RATE_LIMIT_WINDOW_SECONDS` | int | 60 | Rate limit window |
| `RATE_LIMIT_REDIS_PREFIX` | str | "ratelimit" | Redis key prefix |
| `RATE_LIMIT_EXCLUDED_PATHS` | list[str] | ["/", "/docs", ...] | Excluded paths |

### Auth Rate Limiting

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE` | int | 60 | Auth endpoint limit |
| `AUTH_RATE_LIMIT_WINDOW_SECONDS` | int | 60 | Auth window |
| `AUTH_RATE_LIMIT_PATHS` | list[str] | ["/api/v1/auth/login", ...] | Auth paths |

### File Upload Rate Limiting

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR` | int | 100 | Upload limit per hour |
| `FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS` | int | 3600 | Upload window |
| `FILE_UPLOAD_RATE_LIMIT_PATHS` | list[str] | ["/api/v1/files/upload"] | Upload paths |

---

## 13. File Upload Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `UPLOAD_DIR` | str | "uploads" | Upload directory |
| `CERTIFICATES_DIR` | str | "certificates" | Certificates directory |
| `MAX_UPLOAD_MB` | int | 100 | Max upload size in MB |
| `ALLOWED_UPLOAD_EXTENSIONS` | list[str] | ["mp4","avi","mov","pdf","doc","docx","jpg","jpeg","png"] | Allowed extensions |
| `FILE_STORAGE_PROVIDER` | Literal | "local" | Storage provider: local or s3 |
| `FILE_DOWNLOAD_URL_EXPIRE_SECONDS` | int | 900 | Download URL expiry |

### Upload Directory Structure

```
uploads/
├── images/
│   ├── courses/
│   ├── profiles/
│   └── general/
├── documents/
│   ├── lessons/
│   └── assignments/
├── videos/
│   └── lessons/
└── temp/

certificates/
└── pdfs/
```

---

## 14. AWS S3 Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | str \| None | None | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | str \| None | None | AWS secret key |
| `AWS_REGION` | str \| None | None | AWS region |
| `AWS_S3_BUCKET` | str \| None | None | S3 bucket name |
| `AWS_S3_BUCKET_URL` | str \| None | None | S3 bucket URL |

### S3 Configuration

```bash
# Example AWS S3 configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
AWS_S3_BUCKET=lms-files-prod
AWS_S3_BUCKET_URL=https://lms-files-prod.s3.amazonaws.com
```

---

## 15. Validation Rules

### Production Validation

The system validates production settings at startup:

```python
@model_validator(mode="after")
def validate_production_settings(self):
    if self.ENVIRONMENT != "production":
        return self

    # Validations
    if self.DEBUG:
        raise ValueError("DEBUG must be false in production")
    
    if self.SECRET_KEY in {"change-me", "change-this-in-production..."} or len(self.SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY must be strong (32+ chars)")
    
    if self.ACCESS_TOKEN_BLACKLIST_ENABLED and not self.ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:
        raise ValueError("ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED must be true")
    
    if self.TASKS_FORCE_INLINE:
        raise ValueError("TASKS_FORCE_INLINE must be false in production")

    if self.PAYMENTS_MOCK_MODE:
        raise ValueError("PAYMENTS_MOCK_MODE must be false in production")
    
    return self
```

### Validation Rules Summary

| Setting | Production Rule |
|---------|-----------------|
| DEBUG | Must be False |
| SECRET_KEY | Must be 32+ characters, not default value |
| ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED | Must be True |
| TASKS_FORCE_INLINE | Must be False |
| PAYMENTS_MOCK_MODE | Must be False |

---

## 16. Environment-Specific Settings

### Development

```bash
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-key-change-me
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms_dev
REDIS_URL=redis://localhost:6379/0
TASKS_FORCE_INLINE=True
PAYMENTS_MOCK_MODE=True
CORS_ORIGINS=["http://localhost:3000"]
ENABLE_API_DOCS=True
METRICS_ENABLED=False
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=False
SECRET_KEY=<staging-secret-key>
DATABASE_URL=<staging-db-url>
REDIS_URL=<staging-redis-url>
TASKS_FORCE_INLINE=False
PAYMENTS_MOCK_MODE=False
CORS_ORIGINS=["https://staging.example.com"]
ENABLE_API_DOCS=True
METRICS_ENABLED=True
```

### Production

```bash
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<production-secret-key>
DATABASE_URL=<production-db-url>
REDIS_URL=<production-redis-url>
TASKS_FORCE_INLINE=False
PAYMENTS_MOCK_MODE=False
CORS_ORIGINS=["https://app.example.com"]
ENABLE_API_DOCS=False
METRICS_ENABLED=True
SENTRY_DSN=<sentry-dsn>
```

---

## Summary

This configuration reference provides:

- ✅ Complete list of all 60+ configuration options
- ✅ Type definitions and default values
- ✅ Usage examples for each category
- ✅ Environment-specific configurations
- ✅ Production validation rules
- ✅ Security recommendations

All settings can be set via environment variables or `.env` file.
