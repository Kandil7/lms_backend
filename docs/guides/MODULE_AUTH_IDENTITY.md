# Module Guide: Auth & Identity

This guide provides a detailed technical breakdown of the modules responsible for user identity, authentication, and specialized roles.

---

## 🔑 Auth Module (`app/modules/auth`)
**Purpose**: Manages the authentication lifecycle—from login to token issuance and refreshing.

### Key Components:
- **`router.py`**: Standard JWT endpoints (`/login`, `/register`). Returns `access_token` in JSON body.
- **`router_cookie.py`**: Secure endpoints for web clients. Sets `HttpOnly` cookies and requires CSRF tokens.
- **`service.py`**:
  - `authenticate_user()`: Verifies password hashes using `app.core.security`.
  - `create_tokens()`: Generates Access (short-lived) and Refresh (long-lived) tokens.
- **`models.py`**: Defines `RefreshToken` for database-backed token rotation.

### The Login Flow:
1. User submits credentials.
2. Service verifies hash against `users` table.
3. If MFA is enabled, returns `403 MFA_REQUIRED` with a temporary session ID.
4. If valid, generates tokens.
5. If Cookie mode: Sets `access_token` and `refresh_token` cookies + returns CSRF token header.

---

## 👤 Users Module (`app/modules/users`)
**Purpose**: Manages the User entity and profile data.

### Data Model (`User`):
- `id`: UUID (Primary Key).
- `email`: Indexed, Unique.
- `role`: Enum (`student`, `instructor`, `admin`).
- `is_active`: Soft-delete flag.
- `email_verified_at`: Timestamp for account verification.

### Capabilities:
- **Profile Management**: Users can update their bio and avatar.
- **Password Reset**: Handles the "Forgot Password" flow via email tokens.

---

## 👩‍🏫 Instructors Module (`app/modules/instructors`)
**Purpose**: Manages the verification workflow for teachers.

### The Onboarding State Machine:
1. **Registered**: User has `role=instructor` but `status=pending`.
2. **Submitted**: Instructor submits verification docs (CV, LinkedIn).
3. **Verified**: Admin approves docs. `status=active`.
4. **Rejected**: Admin denies with reason.

### Key Endpoints:
- `POST /instructors/register`: Creates a user + instructor profile in one transaction.
- `GET /instructors/me/stats`: Aggregated view of student enrollments across all courses.

---

## 👮 Admin Module (`app/modules/admin`)
**Purpose**: Superuser controls.

### Security:
- All routes are protected by `Depends(get_current_admin_user)`.
- **Audit Logs**: Critical actions (banning a user) are logged to the database.

### Features:
- **User Search**: Paginated search across the entire user base.
- **System Health**: View metrics from `app.core.metrics`.
- **Impersonation**: (Optional) Ability to "log in as" another user for support.
