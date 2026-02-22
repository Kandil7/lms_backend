# Advanced Features Deep Dive

## Webhooks, Caching, Secrets, and Advanced Middleware

This document provides comprehensive documentation for the advanced features in the LMS backend that are not fully covered in other documentation files.

---

## Table of Contents

1. [Webhook System](#1-webhook-system)
2. [Caching System](#2-caching-system)
3. [Secrets Management](#3-secrets-management)
4. [Advanced Rate Limiting](#4-advanced-rate-limiting)
5. [Security Headers Middleware](#5-security-headers-middleware)
6. [Request Logging Middleware](#6-request-logging-middleware)
7. [Response Envelope Middleware](#7-response-envelope-middleware)
8. [Metrics System](#8-metrics-system)
9. [Observability Setup](#9-observability-setup)

---

## 1. Webhook System

### Overview

The webhook system allows the LMS to notify external systems when events occur within the platform. This is essential for:
- Payment confirmations
- Enrollment events
- Certificate issuances
- Integration with CRM systems

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEBHOOK ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Event Occurs                                                   │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐                                                │
│  │   Webhook    │                                                │
│  │   Emitter    │                                                │
│  └──────┬───────┘                                                │
│         │                                                        │
│         │ Enqueue Task                                           │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │    Celery    │                                                │
│  │   Task Queue │                                                │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐     ┌──────────────┐                        │
│  │   Dispatch   │────►│  External    │                        │
│  │   Task       │     │  System      │                        │
│  └──────────────┘     └──────────────┘                        │
│                                                                 │
│  Features:                                                      │
│  • HMAC Signature                                               │
│  • Retry with exponential backoff                               │
│  • Event versioning                                             │
│  • Multiple targets                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Webhook Configuration

```python
# app/core/config.py
class Settings(BaseSettings):
    # Webhook settings
    WEBHOOKS_ENABLED: bool = False
    WEBHOOK_SIGNING_SECRET: str = ""
    WEBHOOK_RETRY_MAX: int = 3
    WEBHOOK_RETRY_DELAY: int = 60  # seconds
```

### Webhook Events

```python
# app/core/webhooks.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

class WebhookEvent(str, Enum):
    """All supported webhook events"""
    
    # Auth events
    USER_REGISTERED = "user.registered"
    USER_EMAIL_VERIFIED = "user.email_verified"
    USER_PASSWORD_RESET = "user.password_reset"
    
    # Enrollment events
    ENROLLMENT_CREATED = "enrollment.created"
    ENROLLMENT_COMPLETED = "enrollment.completed"
    ENROLLMENT_DROPPED = "enrollment.dropped"
    
    # Payment events
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Certificate events
    CERTIFICATE_ISSUED = "certificate.issued"
    CERTIFICATE_REVOKED = "certificate.revoked"
    
    # Course events
    COURSE_PUBLISHED = "course.published"
    COURSE_UPDATED = "course.updated"

@dataclass
class WebhookPayload:
    """Webhook payload structure"""
    event: WebhookEvent
    timestamp: datetime
    data: dict
    version: str = "1.0"
    signature: str = ""
```

### Webhook Emitter

```python
# app/core/webhooks.py
import hmac
import hashlib
import json
from typing import List, Optional
from app.core.config import settings

class WebhookEmitter:
    """Emit webhook events to registered endpoints"""
    
    def __init__(self):
        self.signing_secret = settings.WEBHOOK_SIGNING_SECRET
    
    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature"""
        if not self.signing_secret:
            return ""
        return hmac.new(
            self.signing_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def emit(
        self,
        event: WebhookEvent,
        data: dict,
        targets: List[str]
    ) -> dict:
        """Emit webhook to all targets"""
        
        # Create payload
        payload = {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "data": data
        }
        
        payload_json = json.dumps(payload, default=str)
        signature = self._generate_signature(payload_json)
        
        # Dispatch to Celery task
        from app.tasks.dispatcher import send_task
        
        results = {}
        for target_url in targets:
            task = send_task(
                "app.tasks.webhook_tasks.dispatch_webhook",
                webhook_url=target_url,
                event_type=event.value,
                payload=payload,
                signature=signature
            )
            results[target_url] = "queued"
        
        return results
    
    async def emit_enrollment_completed(
        self,
        enrollment_id: str,
        student_email: str,
        course_title: str,
        certificate_url: Optional[str] = None
    ):
        """Emit enrollment completed event"""
        
        data = {
            "enrollment_id": enrollment_id,
            "student_email": student_email,
            "course_title": course_title,
            "certificate_url": certificate_url,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Get webhook targets from database or config
        targets = settings.WEBHOOK_TARGETS.get(WebhookEvent.ENROLLMENT_COMPLETED, [])
        
        if targets:
            await self.emit(WebhookEvent.ENROLLMENT_COMPLETED, data, targets)

# Global instance
webhook_emitter = WebhookEmitter()
```

###ery Task

```python
# app Webhook Cel/tasks/webhook_tasks.py
from celery import Task
from celery.exceptions import MaxRetriesExceededError
import httpx
import logging

logger = logging.getLogger(__name__)

class WebhookTask(Task):
    """Base webhook task with retry logic"""
    
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

@celery_app.task(
    name="app.tasks.webhook_tasks.dispatch_webhook",
    base=WebhookTask,
    max_retries=3,
    default_retry_delay=60
)
def dispatch_webhook(
    webhook_url: str,
    event_type: str,
    payload: dict,
    signature: str = ""
) -> dict:
    """Dispatch webhook to external URL"""
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "LMS-Webhook/1.0",
        "X-Webhook-Event": event_type
    }
    
    if signature:
        headers["X-Webhook-Signature"] = f"sha256={signature}"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            logger.info(f"Webhook delivered: {event_type} to {webhook_url}")
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "event": event_type,
                "target": webhook_url
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Webhook failed: {e.response.status_code} - {webhook_url}")
        raise
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)} - {webhook_url}")
        raise

@celery_app.task(name="app.tasks.webhook_tasks.retry_failed_webhooks")
def retry_failed_webhooks():
    """Retry all failed webhooks from the database"""
    # Query failed webhook events and retry
    pass
```

### Webhook Verification (For Receiving Webhooks)

```python
# app/modules/payments/router.py
from fastapi import APIRouter, Request, Header
import hmac
import hashlib
import json

router = APIRouter()

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify incoming webhook signature"""
    if not signature or not secret:
        return False
    
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None)
):
    """Handle Stripe webhook events"""
    
    payload = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(
        payload,
        stripe_signature,
        settings.STRIPE_WEBHOOK_SECRET
    ):
        raise HTTPException(401, "Invalid signature")
    
    event = json.loads(payload)
    
    # Handle event
    event_type = event.get("type")
    
    if event_type == "payment_intent.succeeded":
        # Process successful payment
        pass
    elif event_type == "payment_intent.payment_failed":
        # Process failed payment
        pass
    
    return {"status": "received"}
```

---

## 2. Caching System

### Overview

The caching system uses Redis to cache frequently accessed data, reducing database load and improving response times.

### Cache Configuration

```python
# app/core/config.py
class Settings(BaseSettings):
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_KEY_PREFIX: str = "lms"
    CACHE_DEFAULT_TTL_SECONDS: int = 120
    
    # Entity-specific cache TTL
    COURSE_CACHE_TTL_SECONDS: int = 300
    LESSON_CACHE_TTL_SECONDS: int = 300
    QUIZ_CACHE_TTL_SECONDS: int = 180
    QUIZ_QUESTION_CACHE_TTL_SECONDS: int = 180
    USER_CACHE_TTL_SECONDS: int = 300
    ENROLLMENT_CACHE_TTL_SECONDS: int = 60
```

### Cache Implementation

```python
# app/core/cache.py
import redis.asyncio as redis
import json
import hashlib
from typing import Any, Optional, TypeVar, Callable
from functools import wraps
from app.core.config import settings

T = TypeVar('T')

class Cache:
    """Redis-based caching system"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.enabled = settings.CACHE_ENABLED
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self.redis is None:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        parts = [settings.CACHE_KEY_PREFIX, prefix]
        
        for arg in args:
            parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        
        return ":".join(parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            client = await self.get_client()
            value = await client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            # Log error but don't fail
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
        
        try:
            client = await self.get_client()
            ttl = ttl or settings.CACHE_DEFAULT_TTL_SECONDS
            
            await client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
            
        except Exception as e:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            client = await self.get_client()
            await client.delete(key)
            return True
        except Exception:
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            client = await self.get_client()
            full_pattern = f"{settings.CACHE_KEY_PREFIX}:{pattern}"
            keys = await client.keys(full_pattern)
            
            if keys:
                return await client.delete(*keys)
            return 0
            
        except Exception:
            return 0
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or set using factory function"""
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Get from factory
        value = await factory() if callable(factory) else factory
        
        # Store in cache
        await self.set(key, value, ttl)
        
        return value

# Global cache instance
cache = Cache()

# Cache decorators
def cached(prefix: str, ttl: Optional[int] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._make_key(prefix, *args, **kwargs)
            
            # Try cache
            result = await cache.get(key)
            if result is not None:
                return result
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

### Cache Usage Examples

```python
# In course service
class CourseService:
    
    @cached("course", ttl=settings.COURSE_CACHE_TTL_SECONDS)
    async def get_course(self, db, course_id: UUID) -> Optional[Course]:
        """Get course with caching"""
        return await db.get(Course, course_id)
    
    @cached("courses:list", ttl=settings.COURSE_CACHE_TTL_SECONDS)
    async def list_courses(
        self,
        db,
        category: Optional[str] = None,
        published: bool = True
    ) -> List[Course]:
        """List courses with caching"""
        # ... query logic
    
    async def update_course(self, db, course_id: UUID, data: dict):
        """Update course and invalidate cache"""
        # Update in database
        course = await self._update_in_db(db, course_id, data)
        
        # Invalidate cache
        await cache.delete(f"lms:course:{course_id}")
        await cache.invalidate_pattern("courses:list:*")
        
        return course
```

### Cache Invalidation Strategies

```python
# Automatic cache invalidation on model changes
async def invalidate_course_cache(course_id: UUID):
    """Invalidate all cache entries for a course"""
    patterns = [
        f"course:{course_id}",
        "courses:list:*",
        f"lessons:course:{course_id}",
        f"enrollments:course:{course_id}",
        f"analytics:course:{course_id}"
    ]
    
    for pattern in patterns:
        await cache.invalidate_pattern(pattern)
```

---

## 3. Secrets Management

### Overview

The secrets management system provides secure handling of sensitive configuration in production environments.

### Secrets Configuration

```python
# app/core/config.py
class Settings(BaseSettings):
    # Secrets management
    SECRET_KEY: str = ""
    
    # Database
    DATABASE_URL: str = ""
    
    # Redis
    REDIS_URL: str = ""
    
    # External services
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    MYFATOORAH_API_KEY: str = ""
    
    # Email
    SMTP_PASSWORD: str = ""
    
    # AWS
    AWS_SECRET_ACCESS_KEY: str = ""
    
    # Sentry
    SENTRY_DSN: str = ""
```

### Environment Variable Loading

```bash
# .env.production
ENVIRONMENT=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/db
REDIS_URL=redis://:password@host:6379/0
STRIPE_SECRET_KEY=sk_live_xxxxx
MYFATOORAH_API_KEY=xxxxx
SMTP_PASSWORD=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

### Secrets Best Practices

```python
# app/core/config.py
class Settings(BaseSettings):
    
    @model_validator(mode="after")
    def validate_production_secrets(self):
        """Validate required secrets in production"""
        
        if self.ENVIRONMENT != "production":
            return self
        
        # Check critical secrets
        required_secrets = [
            ("SECRET_KEY", self.SECRET_KEY),
            ("DATABASE_URL", self.DATABASE_URL),
        ]
        
        for name, value in required_secrets:
            if not value:
                raise ValueError(f"{name} must be set in production")
        
        # Validate secret strength
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        
        # Warn about default values
        if self.SECRET_KEY == "default-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed in production")
        
        return self
```

### Integration with HashiCorp Vault (Optional)

```python
# app/core/secrets.py (Optional extension)
import hvac
from typing import Optional

class VaultSecrets:
    """HashiCorp Vault integration for secrets"""
    
    def __init__(self, vault_url: str, token: str, mount_point: str = "secret"):
        self.client = hvac.Client(url=vault_url, token=token)
        self.mount_point = mount_point
    
    def get_secret(self, path: str) -> dict:
        """Read secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=self.mount_point
        )
        return response["data"]["data"]
    
    def get_database_url(self) -> str:
        """Get database URL from Vault"""
        secrets = self.get_secret("database")
        return secrets["url"]

# Usage with Vault (optional)
def load_secrets_from_vault():
    """Load secrets from Vault if configured"""
    if settings.USE_VAULT:
        vault = VaultSecrets(
            vault_url=settings.VAULT_URL,
            token=settings.VAULT_TOKEN
        )
        
        # Override settings from Vault
        settings.DATABASE_URL = vault.get_database_url()
        settings.REDIS_URL = vault.get_secret("redis")["url"]
```

---

## 4. Advanced Rate Limiting

### Overview

The rate limiting system provides granular control over API request rates using a token bucket algorithm backed by Redis.

### Rate Limit Configuration

```python
# app/core/config.py
class Settings(BaseSettings):
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_AUTH_PER_MINUTE: int = 60
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 100
    
    # Rate limit key mode
    RATE_LIMIT_KEY_MODE: str = "ip"  # ip, user, user_or_ip
    
    # Custom rules
    RATE_LIMIT_CUSTOM_RULES: dict = {}
```

### Rate Limit Implementation

```python
# app/core/middleware/rate_limit.py
import redis.asyncio as redis
import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from typing import Optional

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with token bucket algorithm"""
    
    def __init__(self, app):
        super().__init__(app)
        self.redis: Optional[redis.Redis] = None
        self.default_limit = settings.RATE_LIMIT_PER_MINUTE
        self.default_window = 60  # seconds
        
        # Custom rules per endpoint
        self.custom_rules = {
            "/api/v1/auth/login": {
                "limit": settings.RATE_LIMIT_AUTH_PER_MINUTE,
                "window": 60
            },
            "/api/v1/auth/register": {
                "limit": settings.RATE_LIMIT_AUTH_PER_MINUTE,
                "window": 60
            },
            "/api/v1/files/upload": {
                "limit": settings.RATE_LIMIT_UPLOAD_PER_HOUR,
                "window": 3600
            }
        }
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis is None:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        return self.redis
    
    def _get_client_key(self, request: Request) -> str:
        """Get rate limit key based on configuration"""
        
        if settings.RATE_LIMIT_KEY_MODE == "ip":
            # Use IP address
            return request.client.host if request.client else "unknown"
        
        elif settings.RATE_LIMIT_KEY_MODE == "user":
            # Use user ID (if authenticated)
            user_id = getattr(request.state, "user_id", None)
            return f"user:{user_id}" if user_id else None
        
        else:  # user_or_ip
            # Use user ID if available, otherwise IP
            user_id = getattr(request.state, "user_id", None)
            return f"user:{user_id}" if user_id else (request.client.host if request.client else "unknown")
    
    def _get_limit_for_path(self, path: str) -> tuple[int, int]:
        """Get rate limit for specific path"""
        
        # Check exact match
        if path in self.custom_rules:
            rule = self.custom_rules[path]
            return rule["limit"], rule["window"]
        
        # Check prefix match
        for pattern, rule in self.custom_rules.items():
            if path.startswith(pattern):
                return rule["limit"], rule["window"]
        
        # Default
        return self.default_limit, self.default_window
    
    async def _check_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Check rate limit using token bucket"""
        
        if not settings.RATE_LIMIT_ENABLED:
            return True, limit, limit
        
        redis_client = await self.get_redis()
        
        # Token bucket key
        bucket_key = f"ratelimit:{key}"
        
        try:
            # Get current count
            current = await redis_client.get(bucket_key)
            
            if current is None:
                # First request in window
                await redis_client.setex(bucket_key, window, 1)
                return True, limit, limit - 1
            
            current = int(current)
            
            if current >= limit:
                # Rate limit exceeded
                ttl = await redis_client.ttl(bucket_key)
                return False, limit, 0
            
            # Increment counter
            await redis_client.incr(bucket_key)
            return True, limit, limit - current - 1
            
        except Exception:
            # If Redis fails, allow request (fail-open for availability)
            # In production, you might want fail-closed
            return True, limit, limit
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        # Get client key
        client_key = self._get_client_key(request)
        
        if not client_key:
            # Can't determine key, allow request
            return await call_next(request)
        
        # Get limit for this path
        limit, window = self._get_limit_for_path(request.url.path)
        
        # Check rate limit
        allowed, limit_value, remaining = await self._check_rate_limit(
            client_key, limit, window
        )
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit_value),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + window)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_value)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
```

### Fallback to In-Memory Rate Limiting

```python
# In-memory fallback when Redis is unavailable
class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development or Redis failure"""
    
    def __init__(self):
        self.buckets: dict = {}
    
    async def check(self, key: str, limit: int, window: int) -> bool:
        now = time.time()
        
        if key not in self.buckets:
            self.buckets[key] = {"count": 1, "reset": now + window}
            return True
        
        bucket = self.buckets[key]
        
        if now > bucket["reset"]:
            # Reset window
            bucket["count"] = 1
            bucket["reset"] = now + window
            return True
        
        if bucket["count"] >= limit:
            return False
        
        bucket["count"] += 1
        return True
```

---

## 5. Security Headers Middleware

### Overview

The security headers middleware adds HTTP security headers to protect against common web vulnerabilities.

### Implementation

```python
# app/core/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # Prevent cross-domain requests for Adobe Flash/PDF
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Disable browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Content Security Policy
        csp_policy = self._get_csp_policy()
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Strict Transport Security (production only)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; "
                "includeSubDomains; "
                "preload"
            )
        
        # Remove server identification
        response.headers["Server"] = "LMS"
        
        return response
    
    def _get_csp_policy(self) -> str:
        """Generate Content Security Policy"""
        
        # Base policy
        policy = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        return "; ".join(policy)
```

### Header Explanations

| Header | Purpose | Protection |
|--------|---------|------------|
| X-Content-Type-Options | Prevent MIME sniffing | Files interpreted as wrong type |
| X-Frame-Options | Prevent iframe embedding | Clickjacking attacks |
| Referrer-Policy | Control referrer info | Privacy leakage |
| X-Permitted-Cross-Domain-Policies | Adobe policy | Cross-domain attacks |
| Permissions-Policy | Disable browser features | Feature abuse |
| Content-Security-Policy | Restrict resource loading | XSS, injection |
| Strict-Transport-Security | Force HTTPS | Man-in-the-middle |

---

## 6. Request Logging Middleware

### Overview

Logs all HTTP requests and responses for debugging, auditing, and analytics.

### Implementation

```python
# app/core/middleware/request_logging.py
import time
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from typing import Optional

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses"""
    
    def __init__(self, app, log_bodies: bool = False):
        super().__init__(app)
        self.log_bodies = log_bodies
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request details
        request_id = request.headers.get("X-Request-ID", "")
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_ip,
                "user_agent": user_agent,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )
            
            # Add request ID to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True
            )
            raise
```

---

## 7. Response Envelope Middleware

### Overview

Wraps all API responses in a consistent envelope format.

### Implementation

```python
# app/core/middleware/response_envelope.py
import json
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import Response
from typing import Any, Optional

class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """Wrap API responses in consistent envelope"""
    
    # Paths to exclude from envelope
    EXCLUDED_PATHS = {
        "/health",
        "/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip certain paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Skip non-JSON responses
        if request.url.path.startswith("/files/"):
            return await call_next(request)
        
        response = await call_next(request)
        
        # Only envelope 2xx responses
        if response.status_code < 200 or response.status_code >= 300:
            return response
        
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Parse JSON if possible
        try:
            data = json.loads(body)
            
            # Create envelope
            envelope = {
                "success": True,
                "data": data,
                "meta": {
                    "status_code": response.status_code
                }
            }
            
            # Create new response
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=envelope,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except json.JSONDecodeError:
            # Not JSON, return as-is
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
```

### Envelope Format

```json
// Without envelope (original)
{
    "id": "123",
    "name": "Course Name"
}

// With envelope
{
    "success": true,
    "data": {
        "id": "123",
        "name": "Course Name"
    },
    "meta": {
        "status_code": 200
    }
}
```

---

## 8. Metrics System

### Overview

Exposes Prometheus metrics for monitoring and alerting.

### Implementation

```python
# app/core/metrics.py
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time

# Request metrics
REQUEST_COUNT = Counter(
    'lms_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'lms_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Database metrics
DB_QUERY_DURATION = Histogram(
    'lms_db_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table']
)

DB_QUERY_COUNT = Counter(
    'lms_db_query_total',
    'Total database queries',
    ['query_type', 'table']
)

# Business metrics
ACTIVE_USERS = Gauge(
    'lms_active_users_total',
    'Number of active users',
    ['role']
)

ENROLLMENTS_COUNT = Gauge(
    'lms_enrollments_total',
    'Number of active enrollments'
)

CERTIFICATES_ISSUED = Counter(
    'lms_certificates_issued_total',
    'Total certificates issued'
)

# Celery metrics
CELERY_TASK_DURATION = Histogram(
    'lms_celery_task_duration_seconds',
    'Celery task duration',
    ['task_name', 'status']
)

def track_request(method: str, endpoint: str):
    """Decorator to track request metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Track request
            start_time = time.time()
            status = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                
                # Update metrics
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
                REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        return wrapper
    return decorator

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### Metrics Available

| Metric | Type | Description |
|--------|------|-------------|
| lms_http_requests_total | Counter | Total HTTP requests |
| lms_http_request_duration_seconds | Histogram | Request duration |
| lms_db_query_duration_seconds | Histogram | DB query duration |
| lms_active_users_total | Gauge | Active users by role |
| lms_enrollments_total | Gauge | Total enrollments |
| lms_certificates_issued_total | Counter | Certificates issued |

---

## 9. Observability Setup

### Prometheus Configuration

```yaml
# ops/observability/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: 'lms-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
  
  - job_name: 'celery'
    static_configs:
      - targets: ['celery-exporter:9808']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Alert Rules

```yaml
# ops/observability/prometheus/alerts.yml
groups:
  - name: lms-alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(lms_http_requests_total{status=~"5.."}[5m])) 
          / sum(rate(lms_http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
      
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, 
            sum(rate(lms_http_request_duration_seconds_bucket[5m])) by (le)
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
      
      - alert: CeleryTaskFailures
        expr: |
          sum(rate(lms_celery_task_duration_seconds{status="failure"}[5m])) 
          > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Celery task failure rate"
```

### Grafana Dashboard

```json
// ops/observability/grafana/dashboards/lms-api-overview.json
{
  "dashboard": {
    "title": "LMS API Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(lms_http_requests_total[1m])) by (method)",
            "legendFormat": "{{method}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(lms_http_requests_total{status=~'5..'}[1m])) / sum(rate(lms_http_requests_total[1m]))",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Latency P95",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(lms_http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95 Latency"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(lms_active_users_total) by (role)",
            "legendFormat": "{{role}}"
          }
        ]
      }
    ]
  }
}
```

---

## Summary

This documentation covers the advanced features of the LMS backend:

| Feature | Purpose | Files |
|---------|---------|-------|
| Webhooks | External system notifications | webhooks.py, webhook_tasks.py |
| Caching | Redis-based caching | cache.py |
| Secrets | Secure configuration | config.py |
| Rate Limiting | Request throttling | rate_limit.py |
| Security Headers | HTTP protection | security_headers.py |
| Request Logging | Debugging/audit | request_logging.py |
| Response Envelope | Consistent API format | response_envelope.py |
| Metrics | Prometheus monitoring | metrics.py |
| Observability | Full stack monitoring | ops/ |

---

*This document provides deep technical details on advanced features used in the LMS backend.*
