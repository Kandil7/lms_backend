# Security Implementation

This document explains the security architecture, authentication system, authorization patterns, and protective measures implemented in this LMS Backend.

---

## Table of Contents

1. [Authentication System](#1-authentication-system)
2. [Password Security](#2-password-security)
3. [JWT Implementation](#3-jwt-implementation)
4. [Authorization and Permissions](#4-authorization-and-permissions)
5. [API Security](#5-api-security)
6. [Data Protection](#6-data-protection)
7. [Rate Limiting](#7-rate-limiting)
8. [CORS Configuration](#8-cors-configuration)
9. [Security Headers](#9-security-headers)
10. [Input Validation](#10-input-validation)

---

## 1. Authentication System

### Overview

The authentication system uses **JWT (JSON Web Tokens)** with a dual-token strategy:

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. REGISTER                                                │
│     User → POST /auth/register → Create User + Send Email │
│                                                             │
│  2. LOGIN                                                   │
│     User → POST /auth/login → Verify Password              │
│     ← Return Access + Refresh Tokens                        │
│                                                             │
│  3. API REQUESTS                                           │
│     User → GET /courses → Include Access Token             │
│     ← Validate Token → Return Data                          │
│                                                             │
│  4. TOKEN REFRESH                                          │
│     User → POST /auth/refresh → Include Refresh Token      │
│     ← Return New Access Token                              │
│                                                             │
│  5. LOGOUT                                                  │
│     User → POST /auth/logout → Blacklist Access Token      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Token Strategy

| Token | Lifetime | Purpose |
|-------|----------|---------|
| Access Token | 15 minutes | API requests |
| Refresh Token | 30 days | Obtain new access tokens |
| Password Reset | 30 minutes | One-time password reset |

---

## 2. Password Security

### Password Hashing

```python
from passlib.context import CryptContext

# Configure bcrypt with cost factor
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Higher = more secure but slower
)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### Why Bcrypt?

| Factor | Reason |
|--------|--------|
| **Adaptive** | Configurable work factor |
| **Salt** | Automatic salt generation |
| **Mature** | 20+ years of security review |
| **Standard** | Widely recommended |

### Password Requirements

```python
class PasswordValidator:
    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit"
        
        return True, ""
```

---

## 3. JWT Implementation

### Token Creation

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uuid

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4())  # Unique token ID
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt
```

### Token Validation

```python
async def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise UnauthorizedError("Invalid token type")
        
        # Check if token is blacklisted
        if await is_token_blacklisted(payload.get("jti")):
            raise UnauthorizedError("Token has been revoked")
        
        return payload
        
    except JWTError:
        raise UnauthorizedError("Could not validate credentials")
```

### Token Blacklisting

```python
async def blacklist_token(jti: str, expires_in: int):
    """Add token to blacklist."""
    await redis.setex(
        f"blacklist:{jti}",
        expires_in,
        "revoked"
    )

async def is_token_blacklisted(jti: str) -> bool:
    """Check if token is blacklisted."""
    return await redis.exists(f"blacklist:{jti}")
```

### Current User Dependency

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = UnauthorizedError("Could not validate credentials")
    
    try:
        payload = await verify_token(token, "access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except UnauthorizedError:
        raise credentials_exception
    
    user = await user_repository.get_by_id(db, UUID(user_id))
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise UnauthorizedError("Inactive user")
    
    return user
```

---

## 4. Authorization and Permissions

### Role-Based Access Control (RBAC)

```python
from enum import Enum
from functools import wraps

class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

class Permission(str, Enum):
    # Course permissions
    CREATE_COURSE = "create_course"
    UPDATE_COURSE = "update_course"
    DELETE_COURSE = "delete_course"
    PUBLISH_COURSE = "publish_course"
    
    # User permissions
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    
    # Quiz permissions
    MANAGE_QUIZZES = "manage_quizzes"
    
    # Enrollment permissions
    MANAGE_ENROLLMENTS = "manage_enrollments"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.CREATE_COURSE,
        Permission.UPDATE_COURSE,
        Permission.DELETE_COURSE,
        Permission.PUBLISH_COURSE,
        Permission.MANAGE_USERS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_QUIZZES,
        Permission.MANAGE_ENROLLMENTS,
    },
    Role.INSTRUCTOR: {
        Permission.CREATE_COURSE,
        Permission.UPDATE_COURSE,
        Permission.PUBLISH_COURSE,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_QUIZZES,
    },
    Role.STUDENT: set(),  # No special permissions
}
```

### Permission Checker

```python
def require_permission(permission: Permission):
    """Dependency to check if user has a specific permission."""
    async def checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, set())
        
        if permission not in user_permissions:
            raise ForbiddenError(
                f"Permission denied: {permission.value}"
            )
        
        return current_user
    
    return checker

# Usage
@router.post("/courses")
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_COURSE))
):
    # Only admins and instructors can create courses
    ...
```

### Ownership Check

```python
async def check_course_ownership(
    course_id: UUID,
    current_user: User,
    course_service: CourseService
) -> Course:
    """Verify user owns or is admin."""
    course = await course_service.get_by_id(course_id)
    
    if not course:
        raise NotFoundError("Course", course_id)
    
    if course.instructor_id != current_user.id and current_user.role != Role.ADMIN:
        raise ForbiddenError("You don't have permission to modify this course")
    
    return course
```

---

## 5. API Security

### OAuth2 Bearer Token

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)

# Usage in routes
@router.get("/courses")
async def list_courses(
    current_user: User = Depends(get_current_user)
):
    ...
```

### Optional Authentication

```python
async def get_current_user_optional(
    token: str = Depends(oauth2_scheme)
) -> User | None:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None
    
    try:
        return await get_current_user(token)
    except UnauthorizedError:
        return None
```

---

## 6. Data Protection

### Sensitive Data Handling

```python
# Never return password hash
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
    
    # Exclude password_hash from response
    model_config = ConfigDict(exclude={"password_hash"})

# Mask sensitive data in logs
def sanitize_request(data: dict) -> dict:
    """Remove sensitive data from logs."""
    sensitive_fields = ["password", "token", "secret", "api_key"]
    
    sanitized = data.copy()
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "***REDACTED***"
    
    return sanitized
```

### Database Security

```python
# Use parameterized queries (SQLAlchemy handles this)
query = select(User).where(User.email == email)

# Never construct raw SQL with user input
# ❌ Dangerous: query = f"SELECT * FROM users WHERE email = '{email}'"
# ✅ Safe: query = select(User).where(User.email == email)
```

---

## 7. Rate Limiting

### Implementation

```python
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    """Rate limit login attempts."""
    ...

# Global rate limiting via middleware
app.state.limiter = limiter

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    response = await call_next(request)
    return response
```

### Redis-Based Rate Limiting

```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> tuple[bool, int]:
        """Check if request is within rate limit."""
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, window)
        
        remaining = limit - current
        return current <= limit, max(0, remaining)

# Usage
rate_limiter = RateLimiter(redis)

async def rate_limit(user_id: str, endpoint: str):
    key = f"rate_limit:{user_id}:{endpoint}"
    allowed, remaining = await rate_limiter.check_rate_limit(
        key, 
        limit=100, 
        window=60
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
```

---

## 8. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
    max_age=600,  # 10 minutes
)
```

### Why CORS Matters

| Setting | Purpose |
|---------|---------|
| `allow_origins` | Restrict which domains can access API |
| `allow_credentials` | Allow cookies/auth headers |
| `allow_methods` | Restrict HTTP methods |
| `max_age` | Browser cache duration |

---

## 9. Security Headers

```python
# app/core/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent XSS
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (only enable in production)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
```

### Header Definitions

| Header | Value | Purpose |
|--------|-------|---------|
| X-Frame-Options | DENY | Prevent clickjacking |
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-XSS-Protection | 1; mode=block | XSS filter (legacy) |
| Referrer-Policy | strict-origin... | Control referrer info |
| Strict-Transport-Security | max-age=31536000 | Enforce HTTPS |

---

## 10. Input Validation

### Pydantic Validation

```python
from pydantic import BaseModel, EmailStr, validator, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.STUDENT
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain digit")
        return v

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=5000)
    category: str | None = Field(None, max_length=100)
    difficulty_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Introduction to Python",
                "description": "Learn Python basics",
                "category": "programming",
                "difficulty_level": "beginner"
            }
        }
    )
```

### Why Input Validation Matters

| Threat | Protection |
|--------|------------|
| SQL Injection | Parameterized queries + ORM |
| XSS | Input sanitization + output encoding |
| Buffer Overflow | Length limits |
| Mass Assignment | Explicit field definitions |

---

## Security Summary

| Security Measure | Implementation |
|-----------------|----------------|
| Authentication | JWT with access + refresh tokens |
| Password Security | Bcrypt hashing with salt |
| Authorization | Role-based permissions |
| API Security | OAuth2 Bearer tokens |
| Rate Limiting | Redis-backed, configurable |
| CORS | Configurable origin whitelist |
| Security Headers | Custom middleware |
| Input Validation | Pydantic models |
| Token Blacklist | Redis storage |
| HTTPS | Enforced via HSTS in production |

This security architecture provides defense in depth, protecting against common vulnerabilities while maintaining usability for legitimate users.
