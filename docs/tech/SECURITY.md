# Security Implementation Documentation

This document covers all security aspects of the LMS Backend.

## Table of Contents

1. [Authentication](#authentication)
2. [Authorization](#authorization)
3. [Data Protection](#data-protection)
4. [Infrastructure Security](#infrastructure-security)
5. [Security Headers](#security-headers)
6. [Rate Limiting](#rate-limiting)
7. [Input Validation](#input-validation)
8. [Audit Logging](#audit-logging)

---

## Authentication

### JWT Token-Based Authentication

**Implementation**: `app/core/security.py`

#### Token Structure

```python
# Access Token Payload
{
    "sub": "user-uuid",
    "role": "student",
    "jti": "unique-token-id",
    "typ": "access",
    "iat": 1704067200,
    "exp": 1704068100
}

# Refresh Token Payload
{
    "sub": "user-uuid",
    "jti": "unique-token-id",
    "typ": "refresh",
    "iat": 1704067200,
    "exp": 1706659200
}
```

#### Token Configuration

| Setting | Development | Production |
|---------|-------------|------------|
| Access Token Expiry | 15 minutes | 15 minutes |
| Refresh Token Expiry | 30 days | 30 days |
| Algorithm | HS256 | HS256 |
| Token Blacklist | Optional | Required |

### Cookie-Based Authentication (Production)

**Implementation**: `app/modules/auth/service_cookie.py`, `app/core/cookie_utils.py`

In production, tokens are stored in HTTP-only cookies:

```python
def create_access_token_cookie(token: str, expires_minutes: int) -> Response:
    response = Response(content="authenticated")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="lax",
        max_age=expires_minutes * 60,
        domain=settings.APP_DOMAIN,
    )
    return response
```

### Multi-Factor Authentication (MFA)

**Implementation**: `app/modules/auth/service.py`

Optional MFA using numeric codes:

```python
class MFAService:
    def create_mfa_challenge(self, user_id: UUID) -> tuple[str, str, int]:
        """Create MFA challenge"""
        # 1. Generate 6-digit code
        code = generate_numeric_code(6)
        
        # 2. Create challenge token
        challenge_token = create_mfa_challenge_token(str(user_id))
        
        # 3. Store code in cache
        cache_key = f"auth:mfa:login:{jti}"
        cache.set_json(cache_key, {"user_id": str(user_id), "code": code}, ttl=600)
        
        return challenge_token, code, 600
    
    def verify_mfa_code(self, challenge_token: str, code: str) -> bool:
        """Verify MFA code"""
        # Validate code from cache
        pass
```

### Account Lockout

**Implementation**: `app/core/account_lockout.py`

Prevents brute force attacks:

```python
class AccountLockoutManager:
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes
    
    def increment_failed_attempts(self, email: str, ip_address: str):
        """Increment failed attempts counter"""
        key = f"auth:failed:{email}:{ip_address}"
        redis.incr(key)
        redis.expire(key, self.LOCKOUT_DURATION)
    
    def check_lockout(self, email: str, ip_address: str) -> bool:
        """Check if account is locked"""
        key = f"auth:failed:{email}:{ip_address}"
        attempts = int(redis.get(key) or 0)
        return attempts >= self.MAX_FAILED_ATTEMPTS
```

---

## Authorization

### Role-Based Access Control (RBAC)

**Implementation**: `app/core/permissions.py`

#### Roles

```python
class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"
```

#### Permissions

```python
class Permission(str, Enum):
    # Users
    USERS_READ = "users:read"
    USERS_EDIT = "users:edit"
    USERS_DELETE = "users:delete"
    
    # Courses
    COURSES_CREATE = "courses:create"
    COURSES_EDIT_OWN = "courses:edit_own"
    COURSES_EDIT_ALL = "courses:edit_all"
    
    # Enrollments
    ENROLLMENTS_CREATE = "enrollments:create"
    ENROLLMENTS_VIEW = "enrollments:view"
    
    # Assignments
    ASSIGNMENTS_CREATE = "assignments:create"
    ASSIGNMENTS_GRADE = "assignments:grade"
```

#### Permission Mapping

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
    ],
    Role.INSTRUCTOR: [
        Permission.COURSES_CREATE,
        Permission.COURSES_EDIT_OWN,
        Permission.ASSIGNMENTS_CREATE,
        Permission.ASSIGNMENTS_GRADE,
    ],
    Role.STUDENT: [
        Permission.COURSES_READ,
        Permission.ENROLLMENTS_CREATE,
    ],
}
```

### Authorization Implementation

```python
from app.core.dependencies import require_roles, require_permissions

# Role-based
@app.post("/courses/")
def create_course(
    course: CourseCreate,
    user: User = Depends(require_roles(Role.INSTRUCTOR, Role.ADMIN))
):
    return course_service.create_course(course, user.id)

# Permission-based
@app.put("/users/{user_id}")
def update_user(
    user_id: UUID,
    data: UserUpdate,
    user: User = Depends(require_permissions(Permission.USERS_EDIT))
):
    return user_service.update_user(user_id, data)
```

---

## Data Protection

### Password Hashing

**Implementation**: `app/core/security.py`

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Sensitive Data Redaction

**Implementation**: `app/core/log_redaction.py`

```python
SENSITIVE_FIELDS = [
    "password",
    "password_hash",
    "secret_key",
    "access_token",
    "refresh_token",
    "credit_card",
    "ssn",
]

def redact_sensitive_data(data: dict) -> dict:
    """Redact sensitive fields from data"""
    redacted = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in redacted:
            redacted[field] = "[REDACTED]"
    return redacted
```

### Token Blacklisting

```python
# On password change - invalidate all sessions
def on_password_change(user_id: UUID):
    # 1. Hash new password
    user.password_hash = hash_password(new_password)
    
    # 2. Revoke all refresh tokens
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(UTC)})
    
    # 3. Blacklist current access tokens (via Redis)
    blacklist_access_token(current_token)
```

---

## Infrastructure Security

### Secrets Management

**Implementation**: `app/core/secrets.py`

Supports multiple secret providers:

```python
# Azure Key Vault
initialize_secrets_manager("azure_key_vault", vault_url="https://myvault.vault.azure.net/")

# HashiCorp Vault
initialize_secrets_manager("vault", vault_url="http://vault:8200", vault_token="...")

# Environment Variables
initialize_secrets_manager("env_var")

# Get secret
secret = get_secret("DATABASE_PASSWORD")
```

### Database Security

```python
# Connection string (production)
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/db?sslmode=require

# SQLAlchemy pool settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Check connection before use
    pool_recycle=1800,    # Recycle after 30 minutes
)
```

---

## Security Headers

**Implementation**: `app/core/middleware/security_headers.py`

```python
class SecurityHeadersMiddleware:
    async def __call__(self, request, call_next):
        response = await call_next(request)
        
        # Strict Transport Security
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self';"
        )
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )
        
        return response
```

---

## Rate Limiting

**Implementation**: `app/core/middleware/rate_limit.py`

### Global Rate Limiting

```python
RateLimitMiddleware(
    limit=100,           # requests
    period_seconds=60,    # per minute
    use_redis=True,     # Redis-backed
)
```

### Custom Rate Limits

```python
# Auth endpoints - stricter
RateLimitRule(
    name="auth",
    path_prefixes=["/api/v1/auth/login"],
    limit=60,
    period_seconds=60,
    key_mode="ip",  # By IP address
),

# File uploads - per user/IP
RateLimitRule(
    name="upload",
    path_prefixes=["/api/v1/files/upload"],
    limit=100,
    period_seconds=3600,  # per hour
    key_mode="user_or_ip",
),
```

### Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067260
```

---

## Input Validation

### Pydantic Validation

All request bodies validated via Pydantic:

```python
from pydantic import BaseModel, EmailStr, Field, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="student")
    
    @validator("password")
    def password_strength(cls, v):
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain letters")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain numbers")
        return v
```

### SQL Injection Prevention

Using SQLAlchemy ORM prevents SQL injection:

```python
# Safe - using parameterized queries
user = db.query(User).filter(User.email == email).first()

# Also safe - using SQLAlchemy expressions
users = db.query(User).filter(User.role.in_(["admin", "instructor"])).all()
```

### XSS Prevention

**Implementation**: `app/core/xss_protection.py`

```python
def sanitize_html(content: str) -> str:
    """Remove potentially dangerous HTML"""
    # Remove script tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers
    content = re.sub(r' on\w+="[^"]*"', '', content, flags=re.IGNORECASE)
    
    return content
```

---

## CSRF Protection

**Implementation**: `app/core/csrf_protection.py`

Enabled in production only:

```python
if settings.CSRF_ENABLED:
    app.add_middleware(
        CSRFMiddleware,
        csrf_protection=get_csrf_protection(),
        exempt_paths=[
            "/docs",
            "/api/v1/health",
            "/api/v1/auth/token",
        ],
    )
```

### CSRF Token Flow

1. **Login**: Server generates CSRF token
2. **Cookie**: Token set in `csrf_token` cookie
3. **Request**: Client sends token in `X-CSRF-Token` header
4. **Validation**: Server validates token matches cookie

---

## Audit Logging

### Implementation

```python
import logging

audit_logger = logging.getLogger("audit")

def log_user_action(user_id: UUID, action: str, resource: str, details: dict = None):
    audit_logger.info(
        f"User {user_id} performed {action} on {resource}",
        extra={
            "user_id": str(user_id),
            "action": action,
            "resource": resource,
            "details": details or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
```

### Logged Events

| Event | Details |
|-------|---------|
| Login | IP, timestamp, success/failure |
| Logout | User ID, timestamp |
| Password Change | User ID, IP |
| User Create/Delete | Admin ID, target user |
| Course Create/Modify | Instructor ID, course |
| Enrollment | Student ID, course |
| Payment | Amount, status, user |

---

## Security Checklist

### Development

- [ ] Use strong SECRET_KEY (32+ characters)
- [ ] DEBUG = False in staging/production
- [ ] No hardcoded credentials
- [ ] Use environment variables

### Authentication

- [ ] HTTPS enforced
- [ ] Strong password requirements (8+ chars, letters + numbers)
- [ ] Account lockout after 5 failed attempts
- [ ] Token expiry: 15 min access, 30 day refresh
- [ ] Optional MFA available

### Authorization

- [ ] Role-based permissions implemented
- [ ] Permission checks on all endpoints
- [ ] No privilege escalation possible

### Data Protection

- [ ] Passwords hashed with bcrypt
- [ ] Sensitive data redacted in logs
- [ ] HTTPS only in production
- [ ] CSRF protection enabled (production)
- [ ] Security headers implemented

### Infrastructure

- [ ] Secrets in Azure Key Vault (production)
- [ ] Rate limiting enabled
- [ ] Firewall rules configured
- [ ] Database credentials rotated regularly
- [ ] Regular security updates

### Monitoring

- [ ] Sentry error tracking
- [ ] Audit logging enabled
- [ ] Failed login monitoring
- [ ] Anomaly detection

---

## Security Headers Summary

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | max-age=31536000 | Enforce HTTPS |
| `Content-Security-Policy` | default-src 'self' | XSS prevention |
| `X-Frame-Options` | DENY | Clickjacking prevention |
| `X-Content-Type-Options` | nosniff | MIME sniffing prevention |
| `Referrer-Policy` | strict-origin-when-cross-origin | Privacy |
| `Permissions-Policy` | geolocation=() etc. | Feature control |
