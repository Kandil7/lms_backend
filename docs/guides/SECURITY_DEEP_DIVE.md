# Security Deep Dive: Protecting the LMS

Security is a cornerstone of the EduConnect Pro LMS. This guide explains the multi-layered security architecture we've implemented to protect user data and maintain system integrity.

---

## 📋 Table of Contents
1. [Authentication Strategies](#1-authentication-strategies)
2. [Role-Based Access Control (RBAC)](#2-role-based-access-control-rbac)
3. [CSRF & XSS Protection](#3-csrf--xss-protection)
4. [Rate Limiting](#4-rate-limiting)
5. [Data Privacy & Redaction](#5-data-privacy--redaction)
6. [Account Security](#6-account-security)

---

## 1. Authentication Strategies
We employ two primary authentication methods tailored for different environments:

### JWT (JSON Web Tokens)
- **Used in**: Development and Mobile clients.
- **Header**: `Authorization: Bearer <token>`
- **Rotation**: Short-lived access tokens (15m) + Long-lived refresh tokens (30d).

### HttpOnly Cookies
- **Used in**: Production web client.
- **Why**: Protects tokens from being accessed by malicious JavaScript, effectively mitigating most XSS-based token theft.
- **Flags**: `HttpOnly`, `Secure`, `SameSite=Lax`.

---

## 2. Role-Based Access Control (RBAC)
We use a centralized permission system defined in `app/core/permissions.py`.

### Roles
- **Student**: Can only access their own enrollments and public courses.
- **Instructor**: Can manage their own courses and view their student's progress.
- **Admin**: Full system access.

### Implementation
Permissions are enforced using FastAPI dependencies:
```python
@router.post("/courses")
def create_course(
    data: CourseCreate,
    user: User = Depends(get_current_active_user)
):
    if user.role not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
```

---

## 3. CSRF & XSS Protection

### CSRF (Cross-Site Request Forgery)
For cookie-based sessions, we implement CSRF protection:
1. The backend issues a CSRF token.
2. The client must include this token in a custom header (e.g., `X-CSRF-Token`) for all state-changing requests (POST, PUT, DELETE).
3. The `CsrfProtectionMiddleware` validates the token against the user's session.

### XSS (Cross-Site Scripting)
- **Input Sanitization**: All incoming HTML/Markdown for course content is sanitized.
- **Security Headers**: We inject headers like `Content-Security-Policy` and `X-Content-Type-Options: nosniff`.

---

## 4. Rate Limiting
To prevent brute-force attacks and DoS, we use **Redis-backed rate limiting**:
- **Auth Endpoints**: Strictly limited (e.g., 5 attempts per minute).
- **File Uploads**: Limited by file size and frequency.
- **General API**: Global limits per IP address.

---

## 5. Data Privacy & Redaction
We ensure that sensitive information never leaves the secure boundary:
- **Log Redaction**: A custom logging filter (`app/core/log_redaction.py`) automatically masks fields like `password`, `token`, and `email` in system logs.
- **Response Envelopes**: Consistent response structures ensure we don't accidentally leak internal database IDs or stack traces in production.

---

## 6. Account Security
- **Password Hashing**: Uses `bcrypt` with a high work factor.
- **Account Lockout**: After multiple failed login attempts, accounts are temporarily locked to stop automated brute-force tools.
- **MFA (Multi-Factor Authentication)**: Supported for Admin and Instructor accounts via TOTP (Time-based One-Time Password).

---

## ✅ Security Checklist for Developers
- [ ] Never log plain-text passwords or tokens.
- [ ] Always use `UUID` for public-facing resource IDs.
- [ ] Apply the `get_current_active_user` dependency to all protected routes.
- [ ] Ensure any new state-changing endpoint is covered by CSRF protection if using cookies.
- [ ] Use Pydantic schemas to strictly validate all incoming data.
