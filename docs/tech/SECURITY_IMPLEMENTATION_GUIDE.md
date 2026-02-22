# Security Implementation Guide

This document provides comprehensive documentation of the security measures implemented in the LMS Backend, including authentication, authorization, data protection, and security best practices.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Authorization](#authorization)
3. [Password Security](#password-security)
4. [Token Management](#token-management)
5. [Multi-Factor Authentication](#multi-factor-authentication)
6. [Rate Limiting](#rate-limiting)
7. [Input Validation](#input-validation)
8. [Data Protection](#data-protection)
9. [Security Headers](#security-headers)
10. [Audit Logging](#audit-logging)

---

## Authentication

### JWT-Based Authentication

The LMS Backend uses JSON Web Tokens (JWT) for stateless authentication. This approach was chosen over session-based authentication for several reasons:

1. **Scalability**: JWTs are self-contained and don't require server-side session storage
2. **Flexibility**: Works across multiple domains and services
3. **Performance**: No database lookup required to validate tokens
4. **Simplicity**: Easy to implement and debug

### Token Structure

JWTs contain three parts: header, payload, and signature. The payload includes:

```python
{
    "sub": "user-uuid",           # Subject (user ID)
    "role": "student",            # User role
    "jti": "unique-token-id",     # JWT ID for blacklisting
    "typ": "access",              # Token type
    "iat": 1705760400,            # Issued at
    "exp": 1705761300             # Expiration
}
```

### Token Types

| Token Type | Purpose | Expiration | Usage |
|------------|---------|------------|-------|
| access | API authentication | 15 minutes | All authenticated requests |
| refresh | Get new access token | 30 days | Token refresh endpoint |
| password_reset | Password recovery | 30 minutes | Password reset link |
| email_verification | Email verification | 24 hours | Email verification link |
| mfa_challenge | MFA verification | 10 minutes | MFA login flow |

### Authentication Flow

The authentication flow works as follows:

1. **Registration**: User creates account with email and password
2. **Login**: User provides credentials, receives tokens
3. **API Access**: User includes access token in requests
4. **Token Refresh**: When access token expires, use refresh token
5. **Logout**: Access token is blacklisted

### Implementation Details

The authentication logic is implemented in `app/core/security.py`:

```python
def create_access_token(subject: str, role: str) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token({"sub": subject, "role": role}, expires_delta, TokenType.ACCESS)

def decode_token(token: str, expected_type: str | None = None, *, check_blacklist: bool = True) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedException("Could not validate credentials") from exc
    
    # Validate token type
    token_type = payload.get("typ")
    if expected_type and token_type != expected_type:
        raise UnauthorizedException("Invalid token type")
    
    # Check blacklist for access tokens
    if token_type == TokenType.ACCESS:
        if check_blacklist and get_access_token_blacklist().is_revoked(str(payload.get("jti"))):
            raise UnauthorizedException("Token has been revoked")
    
    return payload
```

---

## Authorization

### Role-Based Access Control (RBAC)

The system implements RBAC with three roles:

| Role | Permissions |
|------|-------------|
| admin | Full system access, user management, all analytics |
| instructor | Create/manage own courses, view own analytics |
| student | Enroll in courses, take quizzes, view own progress |

### Permission Enforcement

Permissions are enforced at multiple levels:

1. **Router Level**: Check user role in endpoint
2. **Service Level**: Verify ownership or permissions
3. **Database Level**: Use foreign key constraints

### Permission Examples

**Instructor-only endpoint**:

```python
@router.post("/courses")
def create_course(
    payload: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CourseResponse:
    if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can create courses"
        )
    # Proceed with course creation
```

**Ownership check**:

```python
@router.patch("/courses/{course_id}")
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CourseResponse:
    course = CourseService(db).get_course(course_id)
    
    # Check ownership or admin
    if course.instructor_id != current_user.id:
        if current_user.role != Role.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this course"
            )
```

### Permission Definitions

The permission system is defined in `app/core/permissions.py`:

```python
class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

class Permission(str, Enum):
    # Course permissions
    CREATE_COURSE = "course:create"
    UPDATE_OWN_COURSE = "course:update:own"
    UPDATE_ANY_COURSE = "course:update:any"
    DELETE_OWN_COURSE = "course:delete:own"
    DELETE_ANY_COURSE = "course:delete:any"
    
    # Enrollment permissions
    ENROLL = "enrollment:create"
    VIEW_OWN_ENROLLMENTS = "enrollment:view:own"
    VIEW_ANY_ENROLLMENT = "enrollment:view:any"
    
    # Analytics permissions
    VIEW_OWN_ANALYTICS = "analytics:view:own"
    VIEW_INSTRUCTOR_ANALYTICS = "analytics:view:instructor"
    VIEW_ADMIN_ANALYTICS = "analytics:view:admin"
```

---

## Password Security

### Hashing Algorithm

Passwords are hashed using bcrypt through the passlib library:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Why Bcrypt?

Bcrypt was chosen for several reasons:

1. **Adaptive Cost**: Work factor can be increased as hardware improves
2. **Built-in Salt**: Automatically generates and stores salt
3. **Proven Security**: Battle-tested algorithm with decades of use
4. **Wide Adoption**: Well-understood and reviewed

### Password Requirements

The system enforces password requirements through Pydantic validation:

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

```python
class UserRegistration(BaseModel):
    email: str = Field(..., email=True)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v
```

---

## Token Management

### Access Tokens

Access tokens are short-lived (15 minutes) for security:

- If compromised, window of vulnerability is limited
- Reduces impact of token theft
- Forces regular re-authentication

### Refresh Tokens

Refresh tokens are long-lived (30 days) for usability:

- Allows persistent sessions
- Can be rotated for security
- Can be revoked instantly

### Token Refresh Flow

```python
@router.post("/auth/refresh")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    # Validate refresh token
    payload = security.decode_token(
        request.refresh_token, 
        expected_type=security.TokenType.REFRESH
    )
    
    # Get user
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise UnauthorizedException("Invalid refresh token")
    
    # Create new tokens
    access_token = security.create_access_token(user.email, user.role)
    refresh_token = security.create_refresh_token(user.email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=900  # 15 minutes
    )
```

### Token Blacklisting

Logout immediately invalidates access tokens through blacklisting:

```python
@router.post("/auth/logout")
def logout(
    current_user: User = Depends(get_current_user),
    authorization: str = Header(...)
):
    # Extract token
    token = authorization.replace("Bearer ", "")
    
    # Blacklist the token
    security.blacklist_access_token(token)
    
    return {"message": "Successfully logged out"}
```

The blacklist uses Redis in production for distributed access:

```python
class AccessTokenBlacklist:
    def __init__(self, *, enabled: bool, redis_url: str | None, key_prefix: str):
        self.enabled = enabled
        self.key_prefix = key_prefix
        self._redis = Redis.from_url(redis_url) if redis_url else None
    
    def revoke(self, *, jti: str, exp_epoch: int) -> None:
        if not self.enabled:
            return
        
        ttl = max(0, exp_epoch - int(time.time()))
        if ttl <= 0:
            return
        
        if self._redis:
            self._redis.set(self._build_key(jti), "1", ex=ttl)
```

---

## Multi-Factor Authentication

### TOTP-Based MFA

The system implements TOTP (Time-based One-Time Password) MFA:

1. User enables MFA in profile settings
2. System generates a secret key
3. User configures authenticator app (Google Authenticator, Authy, etc.)
4. Login requires both password and TOTP code

### MFA Flow

**Enable MFA**:

```python
@router.post("/auth/mfa/enable")
def enable_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MFAEnableResponse:
    # Generate secret
    secret = pyotp.random_base32()
    
    # Store temporarily (not enabled until verified)
    current_user.mfa_secret = secret
    db.commit()
    
    # Generate QR code URL
    totp = pyotp.TOTP(secret)
    provisioning_url = totp.provisioning_uri(
        current_user.email,
        issuer_name="LMS Platform"
    )
    
    return MFAEnableResponse(
        secret=secret,
        provisioning_url=provisioning_url
    )
```

**Verify and Enable**:

```python
@router.post("/auth/mfa/verify")
def verify_mfa(
    code: str,
    current_user: User = Depends(get_current_user)
) -> MFAEnableResponse:
    # Verify code
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(code):
        raise HTTPException(status_code=400, detail="Invalid code")
    
    # Enable MFA
    current_user.mfa_enabled = True
    current_user.mfa_secret = None  # Clear temporary secret
    db.commit()
    
    return {"message": "MFA enabled successfully"}
```

**MFA Login**:

```python
@router.post("/auth/mfa/login")
def mfa_login(
    request: MFALoginRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    # First verify password
    user = verify_email_password(request.email, request.password)
    
    # Then verify MFA code
    if user.mfa_enabled:
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(request.mfa_code):
            raise UnauthorizedException("Invalid MFA code")
    
    # Create tokens
    return create_tokens(user)
```

---

## Rate Limiting

### Rate Limiting Strategy

The system implements tiered rate limiting:

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| General API | 100 requests | Per minute |
| Authentication | 60 requests | Per minute |
| File Uploads | 100 requests | Per hour |

### Implementation

Rate limiting is implemented as middleware:

```python
class RateLimitMiddleware:
    def __init__(
        self,
        app,
        limit: int = 100,
        period_seconds: int = 60,
        use_redis: bool = True,
        redis_url: str = None,
        key_prefix: str = "ratelimit",
        excluded_paths: list = None,
        custom_rules: list = None
    ):
        self.app = app
        self.limit = limit
        self.period = period_seconds
        self.use_redis = use_redis
        self.excluded_paths = excluded_paths or []
        self.custom_rules = custom_rules or []
        
        if use_redis and redis_url:
            self.redis = Redis.from_url(redis_url)
    
    async def __call__(self, scope, receive, send):
        # Check if path is excluded
        if scope["path"] in self.excluded_paths:
            return await self.app(scope, receive, send)
        
        # Get client identifier
        client_id = self._get_client_id(scope)
        
        # Check rate limit
        if not self._check_rate_limit(client_id):
            await self._send_rate_limit_response(send)
            return
        
        await self.app(scope, receive, send)
```

### Custom Rate Limit Rules

Different rules can be defined for specific endpoints:

```python
rate_limit_rules = [
    RateLimitRule(
        name="auth",
        path_prefixes=["/api/v1/auth/login", "/api/v1/auth/token"],
        limit=60,
        period_seconds=60,
        key_mode="ip",
    ),
    RateLimitRule(
        name="upload",
        path_prefixes=["/api/v1/files/upload"],
        limit=100,
        period_seconds=3600,
        key_mode="user_or_ip",
    ),
]
```

---

## Input Validation

### Pydantic Validation

All input is validated using Pydantic models:

```python
class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    difficulty_level: Optional[str] = Field(
        None,
        pattern="^(beginner|intermediate|advanced)$"
    )
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    metadata: Optional[dict] = None
    
    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
```

### SQL Injection Prevention

SQLAlchemy ORM prevents SQL injection through parameterized queries:

```python
# Safe: Using parameterized query
course = db.query(Course).filter(Course.id == course_id).first()

# Unsafe: String concatenation (NEVER DO THIS)
# course = db.query(Course).filter(f"id = '{course_id}'").first()
```

### XSS Prevention

Response serialization escapes HTML by default in Pydantic. Content is treated as strings, not executable code.

---

## Data Protection

### Sensitive Data Handling

| Data Type | Protection |
|-----------|-------------|
| Password hashes | Bcrypt (one-way) |
| JWT secrets | Environment variables |
| Database credentials | Secrets manager |
| API keys | Environment variables |
| File contents | Encryption at rest (cloud storage) |

### PII Handling

Personally Identifiable Information (PII) is handled according to best practices:

1. **Minimization**: Only collect necessary data
2. **Encryption**: Sensitive fields encrypted at rest
3. **Access Control**: Role-based access to PII
4. **Logging**: PII not logged in plain text
5. **Retention**: Data retention policies enforced

### Database Security

- Use parameterized queries (handled by SQLAlchemy)
- Enable SSL connections for production
- Regular security updates
- Principle of least privilege for database users

---

## Security Headers

### Implemented Headers

The application adds security headers to all responses:

```python
class SecurityHeadersMiddleware:
    async def __call__(self, scope, receive, send):
        # Add security headers
        headers = [
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("X-XSS-Protection", "1; mode=block"),
            ("Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
            ("Content-Security-Policy", "default-src 'self'"),
        ]
        
        await self.app(scope, receive, send)
```

### Header Purpose

| Header | Purpose |
|--------|---------|
| X-Content-Type-Options | Prevent MIME type sniffing |
| X-Frame-Options | Prevent clickjacking |
| X-XSS-Protection | XSS filter in browsers |
| Strict-Transport-Security | Enforce HTTPS |
| Content-Security-Policy | Prevent XSS and injections |

---

## Audit Logging

### Request Logging

All requests are logged with relevant information:

```python
class RequestLoggingMiddleware:
    async def __call__(self, scope, receive, send):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request",
            method=scope["method"],
            path=scope["path"],
            client=scope.get("client"),
            user=scope.get("user"),
        )
        
        # Process request
        await self.app(scope, receive, send)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            "Response",
            method=scope["method"],
            path=scope["path"],
            status=status_code,
            duration=duration,
        )
```

### Security Events

Security-relevant events are logged:

- Login attempts (success and failure)
- Password changes
- MFA enable/disable
- Permission denied errors
- Rate limit exceeded

---

## Production Security Checklist

Before deploying to production, ensure:

- [ ] DEBUG=False
- [ ] Strong SECRET_KEY (32+ random characters)
- [ ] CORS restricted to production domains
- [ ] Rate limiting enabled with Redis
- [ ] Security headers enabled
- [ ] SSL/TLS configured
- [ ] Database SSL enabled
- [ ] Secrets from environment or vault
- [ ] Sentry error tracking configured
- [ ] Access token blacklist enabled
- [ ] File storage uses cloud provider
- [ ] Log aggregation configured
- [ ] Monitoring and alerting set up

---

## Summary

The LMS Backend implements comprehensive security measures:

1. **Authentication**: JWT-based with short-lived access tokens
2. **Authorization**: Role-based access control
3. **Password Security**: Bcrypt hashing with validation
4. **Token Management**: Blacklisting for immediate revocation
5. **MFA**: TOTP-based optional two-factor authentication
6. **Rate Limiting**: Per-endpoint configurable limits
7. **Input Validation**: Pydantic for all input
8. **Data Protection**: Encryption and access control
9. **Security Headers**: Defense-in-depth approach
10. **Audit Logging**: Comprehensive request logging

These measures work together to protect user data and prevent common security vulnerabilities.
