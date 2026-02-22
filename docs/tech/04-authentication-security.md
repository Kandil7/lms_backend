# Authentication & Security

## Complete Security Implementation Guide

This document explains all authentication mechanisms, security implementations, and protective measures in this LMS backend.

---

## 1. Authentication Architecture

### Multi-Layer Authentication

```
┌─────────────────────────────────────────────────────────────────┐
│                 AUTHENTICATION LAYERS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Password Authentication                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - Bcrypt hashing with salt                             │   │
│  │  - Password validation rules                            │   │
│  │  - Account lockout after failed attempts                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Layer 2: JWT Access Tokens                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - Short-lived (15 minutes)                             │   │
│  │  - Stateless validation                                 │   │
│  │  - Token blacklist support                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Layer 3: Refresh Tokens                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - Long-lived (30 days)                                │   │
│  │  - Database storage with revocation                     │   │
│  │  - Rotating tokens                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Layer 4: Multi-Factor Authentication (Optional)               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - Email-based OTP                                     │   │
│  │  - 6-digit codes                                       │   │
│  │  - 10-minute expiration                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Password Security

### Hashing Algorithm

```python
# app/core/security.py
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt"""
    return bcrypt.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.verify(plain_password, hashed_password)
```

### Why Bcrypt?

| Feature | Benefit |
|---------|---------|
| **Adaptive** | Cost factor can be increased over time |
| **Salted** | Rainbow table attacks ineffective |
| **Secure** | Industry-standard, well-audited |
| **Slow** | Prevents brute force |

### Password Requirements

```python
# app/core/config.py
PASSWORD_MIN_LENGTH: int = 8
PASSWORD_REQUIRE_UPPERCASE: bool = True
PASSWORD_REQUIRE_LOWERCASE: bool = True
PASSWORD_REQUIRE_DIGIT: bool = True
PASSWORD_REQUIRE_SPECIAL: bool = False
```

---

## 3. JWT Token Implementation

### Token Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    JWT TOKEN STRUCTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ACCESS TOKEN (15 minutes)                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Header:                                                   │   │
│  │ {                                                         │   │
│  │   "alg": "HS256",                                        │   │
│  │   "typ": "JWT"                                           │   │
│  │ }                                                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Payload:                                                  │   │
│  │ {                                                         │   │
│  │   "sub": "user-uuid",           // User ID              │   │
│  │   "role": "student",           // User role            │   │
│  │   "jti": "unique-token-id",   // Token ID             │   │
│  │   "iat": 1705312800,           // Issued at            │   │
│  │   "exp": 1705313700            // Expires at           │   │
│  │ }                                                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Signature:                                                │   │
│  │ HMAC-SHA256 of header.payload + SECRET_KEY              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  REFRESH TOKEN (30 days)                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ - Stored in database                                     │   │
│  │ - Can be revoked                                         │   │
│  │ - Used to obtain new access tokens                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Token Generation

```python
# app/core/security.py
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(user_id: UUID, role: str) -> str:
    """Create short-lived JWT access token"""
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": str(uuid4()),  # Unique token ID
        "iat": now,
        "exp": expire
    }
    
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

def create_refresh_token(user_id: UUID) -> RefreshToken:
    """Create database-backed refresh token"""
    token = RefreshToken(
        user_id=user_id,
        token_jti=str(uuid4()),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return token
```

### Token Configuration

```python
# app/core/config.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 30
JWT_ALGORITHM: str = "HS256"
```

---

## 4. Multi-Factor Authentication (MFA)

### MFA Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MFA AUTHENTICATION FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Initial Login                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Client       │───►│ API          │───►│ Validate    │     │
│  │ (email/pw)  │    │              │    │ Credentials │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│        │                                    │                  │
│        │                               ┌─────┴─────┐           │
│        │                               │ MFA Enabled│           │
│        │                               └─────┬─────┘           │
│        │                                     │ Yes              │
│        │                                     ▼                  │
│        │◄────────── MFA Challenge ──────────                   │
│        │         (challenge_token sent)                        │
│                                                                 │
│  2. MFA Verification                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Client       │───►│ API          │───►│ Validate    │     │
│  │ (code)       │    │              │    │ MFA Code    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│        │                                    │                  │
│        │                               ┌─────┴─────┐           │
│        │                               │ Valid Code │           │
│        │                               └─────┬─────┘           │
│        │                                     │                  │
│        │◄────────── Access Token ──────────                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### MFA Implementation

```python
# app/modules/auth/mfa.py
import random
import string

def generate_mfa_code() -> str:
    """Generate 6-digit MFA code"""
    return ''.join(random.choices(string.digits, k=6))

def verify_mfa_code(stored_code: str, provided_code: str) -> bool:
    """Verify MFA code"""
    return stored_code == provided_code
```

### Why Email-Based MFA?

| Factor | Email MFA | TOTP | SMS MFA |
|--------|-----------|------|---------|
| Setup Complexity | Low | Medium | Medium |
| Device Dependency | None | Phone | Phone |
| Cost | Low | Free | High |
| Security | Medium | High | Low |
| User Experience | Good | Good | Excellent |

---

## 5. Token Blacklisting

### Blacklist Implementation

```python
# app/core/security.py
import redis
from typing import Optional

class AccessTokenBlacklist:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
    
    async def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        return self.redis_client.exists(f"blacklist:{jti}")
    
    async def add_to_blacklist(self, jti: str, expiry: int):
        """Add token to blacklist"""
        self.redis_client.setex(
            f"blacklist:{jti}",
            expiry,
            "1"
        )
```

### Blacklist Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 TOKEN BLACKLIST CHECK                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Request arrives with access token                           │
│  2. Decode JWT to extract jti (token ID)                        │
│  3. Check Redis: blacklist:{jti}                               │
│  4. If exists: Reject (401 Unauthorized)                         │
│  5. If not exists: Allow request                                │
│                                                                 │
│  Blacklist stored in Redis with TTL matching token expiry       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Fail-Closed Strategy

```python
# In production, fail-closed for security
if settings.ENVIRONMENT == "production":
    if not ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:
        raise ValueError("Must fail-closed in production")
```

---

## 6. Role-Based Access Control (RBAC)

### Roles

```python
# app/core/permissions.py
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"
```

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                      ROLE HIERARCHY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                                │
│  │   ADMIN    │  Full system access                            │
│  │            │  - Manage users                                │
│  │            │  - View all analytics                         │
│  │            │  - Manage payments                            │
│  └──────┬──────┘                                                │
│         │                                                        │
│         │ Can do everything instructor can                     │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ INSTRUCTOR │  Course management                             │
│  │            │  - Create courses                             │
│  │            │  - View course analytics                      │
│  │            │  - Manage quizzes                             │
│  └──────┬──────┘                                                │
│         │                                                        │
│         │ Can do everything student can                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │  STUDENT    │  Learning access                               │
│  │            │  - Enroll in courses                          │
│  │            │  - Take quizzes                               │
│  │            │  - View own progress                          │
│  └─────────────┘                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Authorization Implementation

```python
# app/core/dependencies.py
from functools import wraps

def require_roles(*roles: Role):
    """Decorator to require specific roles"""
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {roles}"
            )
        return current_user
    return dependency

# Usage in routes
@router.post("/courses")
async def create_course(
    course: CourseCreate,
    current_user: User = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    # Only instructors and admins can create courses
    pass
```

---

## 7. Permission System

### Permissions

```python
# app/core/permissions.py
class Permission(str, Enum):
    # User permissions
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    
    # Course permissions
    COURSES_READ = "courses:read"
    COURSES_WRITE = "courses:write"
    COURSES_DELETE = "courses:delete"
    
    # Quiz permissions
    QUIZZES_READ = "quizzes:read"
    QUIZZES_WRITE = "quizzes:write"
    
    # Payment permissions
    PAYMENTS_READ = "payments:read"
    PAYMENTS_WRITE = "payments:write"
```

### Role-Permission Mapping

```python
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.USERS_READ, Permission.USERS_WRITE, Permission.USERS_DELETE,
        Permission.COURSES_READ, Permission.COURSES_WRITE, Permission.COURSES_DELETE,
        Permission.QUIZZES_READ, Permission.QUIZZES_WRITE,
        Permission.PAYMENTS_READ, Permission.PAYMENTS_WRITE,
    ],
    Role.INSTRUCTOR: [
        Permission.COURSES_READ, Permission.COURSES_WRITE,
        Permission.QUIZZES_READ, Permission.QUIZZES_WRITE,
    ],
    Role.STUDENT: [
        Permission.COURSES_READ,
        Permission.QUIZZES_READ,
    ],
}
```

---

## 8. Rate Limiting

### Rate Limiting Strategy

```python
# app/core/middleware/rate_limit.py
class RateLimitMiddleware:
    def __init__(self, request: Request, call_next):
        self.request = request
        self.call_next = call_next
    
    async def __call__(self):
        # Get client identifier (IP or user ID if authenticated)
        client_id = self.get_client_id()
        
        # Check rate limit
        if not await self.check_rate_limit(client_id):
            raise HTTPException(429, "Rate limit exceeded")
        
        response = await self.call_next(self.request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(self.remaining)
        response.headers["X-RateLimit-Reset"] = str(self.reset_time)
        
        return response
```

### Rate Limit Rules

```python
# app/core/config.py
RATE_LIMIT_PER_MINUTE: int = 100           # Global: 100/min
RATE_LIMIT_AUTH_PER_MINUTE: int = 60      # Auth: 60/min (prevent brute force)
RATE_LIMIT_UPLOAD_PER_HOUR: int = 100     # Uploads: 100/hour
```

### Redis-Based Rate Limiting

```python
# Token bucket algorithm
async def check_rate_limit(self, client_id: str) -> bool:
    key = f"ratelimit:{client_id}"
    
    # Get current count
    current = self.redis.get(key)
    
    if current is None:
        # First request - set up bucket
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)  # 1 minute window
        pipe.execute()
        return True
    
    if int(current) >= self.limit:
        return False
    
    # Increment counter
    self.redis.incr(key)
    return True
```

---

## 9. Security Headers

### HTTP Security Headers

```python
# app/core/middleware/security_headers.py
class SecurityHeadersMiddleware:
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent content type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # Cross-domain policies
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Feature policies
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'; object-src 'none'"
        
        # Force HTTPS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
```

### Header Explanations

| Header | Purpose | Protection |
|--------|---------|------------|
| X-Content-Type-Options | Prevent MIME sniffing | Script injection |
| X-Frame-Options | Prevent iframe embedding | Clickjacking |
| Referrer-Policy | Control referrer info | Privacy leak |
| CSP | Restrict resource loading | XSS, injection |
| HSTS | Force HTTPS | Man-in-the-middle |

---

## 10. CORS Configuration

### CORS Settings

```python
# app/core/config.py
CORS_ORIGINS: List[str] = ["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_METHODS: List[str] = ["*"]
CORS_ALLOW_HEADERS: List[str] = ["*"]
```

### Implementation

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)
```

---

## 11. Input Validation

### Pydantic Validation

```python
# app/modules/auth/schemas.py
from pydantic import BaseModel, EmailStr, Field, validator

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=100)
    role: Role = Role.STUDENT
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

### SQL Injection Prevention

```python
# Always use parameterized queries via SQLAlchemy
# WRONG: db.execute(f"SELECT * FROM users WHERE email = '{email}'")
# RIGHT: db.execute(select(User).where(User.email == email))
```

---

## 12. Production Security Validations

### Startup Validation

```python
# app/core/config.py
@model_validator(mode="after")
def validate_production_settings(self):
    if self.ENVIRONMENT != "production":
        return self
    
    # Debug must be off
    if self.DEBUG:
        raise ValueError("DEBUG must be false in production")
    
    # Secret key must be strong
    if len(self.SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    
    # Fail-closed for token blacklist
    if not self.ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:
        raise ValueError("ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED must be true in production")
    
    # Don't run tasks inline
    if self.TASKS_FORCE_INLINE:
        raise ValueError("TASKS_FORCE_INLINE must be false in production")
    
    return self
```

---

## 13. Password Reset Flow

### Reset Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   PASSWORD RESET FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Request Reset                                               │
│  ┌──────────────────┐                                           │
│  │ POST /auth/forgot-password │                                │
│  │ Body: { email }           │                                │
│  └──────────────────┘                                           │
│        │                                                         │
│        │  Generate reset token                                  │
│        │  Send email with link                                  │
│        │                                                         │
│  2. Click Reset Link                                            │
│  ┌──────────────────────────────────┐                          │
│  │ https://app.com/reset-password?token=xxx                  │
│  └──────────────────────────────────┘                          │
│        │                                                         │
│  3. Submit New Password                                         │
│  ┌──────────────────┐                                           │
│  │ POST /auth/reset-password  │                               │
│  │ Body: { token, new_password }│                              │
│  └──────────────────┘                                           │
│        │                                                         │
│        │  Validate token                                        │
│        │  Hash new password                                     │
│        │  Invalidate all refresh tokens                        │
│        │                                                         │
│        ▼                                                         │
│     Success                                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 14. Email Verification Flow

### Verification Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  EMAIL VERIFICATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Request Verification                                        │
│  ┌─────────────────────────────┐                               │
│  │ POST /auth/verify-email/request │                            │
│  │ Body: { email }               │                               │
│  └─────────────────────────────┘                               │
│        │                                                         │
│        │  Generate verification token                           │
│        │  Send verification email                               │
│        │                                                         │
│  2. Click Verification Link                                     │
│  ┌─────────────────────────────────────┐                       │
│  │ POST /auth/verify-email/confirm    │                       │
│  │ Body: { token }                      │                       │
│  └─────────────────────────────────────┘                       │
│        │                                                         │
│        │  Validate token                                        │
│        │  Set email_verified_at timestamp                       │
│        │                                                         │
│        ▼                                                         │
│     Success                                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

This security implementation provides:

| Layer | Protection |
|-------|------------|
| Password | Bcrypt hashing with salt |
| Access Tokens | JWT, 15-minute expiry |
| Refresh Tokens | Database-backed, 30-day expiry |
| MFA | Email-based OTP |
| Rate Limiting | Redis-based token bucket |
| RBAC | Role and permission system |
| Headers | Security headers middleware |
| Validation | Pydantic + SQLAlchemy |
| Production | Fail-closed validation |

The authentication system is designed to be secure by default while remaining user-friendly.
