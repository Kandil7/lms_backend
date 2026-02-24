# API Routes Reference

Complete API documentation for the LMS Backend.

## Base Information

| Item | Value |
|------|-------|
| Base URL | `http://localhost:8000` |
| API Version | v1 |
| Prefix | `/api/v1` |
| Auth Type | JWT Bearer (dev) / HTTP Cookies (prod) |

## Authentication

### Login (JWT)
```
POST /api/v1/auth/token
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "expires_in": 900
}
```

### Login (Cookies - Production)
```
POST /api/v1/auth/login-cookie
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:** Sets `access_token` and `refresh_token` HTTP-only cookies.

### Refresh Token
```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

### Logout
```
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

## Endpoints by Module

### Health Check

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Basic health check | No |
| GET | `/ready` | Readiness check (DB + Redis) | No |

### Authentication (`/auth`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/auth/token` | Login with JWT | No |
| POST | `/auth/login-cookie` | Login with cookies | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/refresh-cookie` | Refresh cookie token | No |
| POST | `/auth/logout` | Logout | Yes |
| POST | `/auth/logout-cookie` | Logout (cookies) | Yes |
| POST | `/auth/login/mfa` | Verify MFA code | No |
| POST | `/auth/password/reset` | Request password reset | No |
| POST | `/auth/password/reset/confirm` | Confirm password reset | No |
| POST | `/auth/email/verify` | Request email verification | No* |
| POST | `/auth/email/verify/confirm` | Confirm email verification | Yes |
| POST | `/auth/mfa/enable` | Enable MFA | Yes |
| POST | `/auth/mfa/disable` | Disable MFA | Yes |

*May require auth depending on settings.

### Users (`/users`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/users/me` | Get current user | Yes | All |
| PUT | `/users/me` | Update current user | Yes | All |
| GET | `/users/{user_id}` | Get user by ID | Yes | Admin |
| GET | `/users/` | List users (paginated) | Yes | Admin, Instructor |
| POST | `/users/` | Create user | No* | - |
| DELETE | `/users/{user_id}` | Delete user | Yes | Admin |

*Public registration can be enabled.

### Instructors (`/instructors`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/instructors/me` | Get my profile | Yes | Instructor |
| PUT | `/instructors/me` | Update profile | Yes | Instructor |
| GET | `/instructors/me/dashboard` | Instructor dashboard | Yes | Instructor |
| GET | `/instructors/{instructor_id}` | Public instructor profile | No | - |
| GET | `/instructors/` | List instructors | No | - |

### Courses (`/courses`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/courses/` | List courses | No | - |
| GET | `/courses/{course_id}` | Get course details | No* | - |
| GET | `/courses/{course_id}/lessons` | Get course lessons | Yes | - |
| POST | `/courses/` | Create course | Yes | Instructor, Admin |
| PUT | `/courses/{course_id}` | Update course | Yes | Instructor (own), Admin |
| DELETE | `/courses/{course_id}` | Delete course | Yes | Instructor (own), Admin |
| POST | `/courses/{course_id}/publish` | Publish course | Yes | Instructor (own), Admin |
| POST | `/courses/{course_id}/unpublish` | Unpublish course | Yes | Instructor (own), Admin |

*Published courses public, drafts require enrollment.

### Lessons (`/lessons`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/lessons/{lesson_id}` | Get lesson | Yes | - |
| POST | `/lessons/` | Create lesson | Yes | Instructor |
| PUT | `/lessons/{lesson_id}` | Update lesson | Yes | Instructor |
| DELETE | `/lessons/{lesson_id}` | Delete lesson | Yes | Instructor |
| POST | `/lessons/{lesson_id}/complete` | Mark complete | Yes | Student |

### Enrollments (`/enrollments`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/enrollments/` | My enrollments | Yes | Student |
| GET | `/enrollments/{enrollment_id}` | Get enrollment | Yes | Student (own), Admin |
| POST | `/enrollments/` | Enroll in course | Yes | Student |
| PUT | `/enrollments/{enrollment_id}/progress` | Update progress | Yes | Student |
| POST | `/enrollments/{enrollment_id}/complete` | Mark complete | Yes | Student |
| GET | `/enrollments/course/{course_id}` | Course enrollments | Yes | Instructor, Admin |

### Quizzes (`/quizzes`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/quizzes/` | List quizzes | Yes | - |
| GET | `/quizzes/{quiz_id}` | Get quiz | Yes | - |
| POST | `/quizzes/` | Create quiz | Yes | Instructor |
| PUT | `/quizzes/{quiz_id}` | Update quiz | Yes | Instructor |
| DELETE | `/quizzes/{quiz_id}` | Delete quiz | Yes | Instructor |
| POST | `/quizzes/{quiz_id}/publish` | Publish quiz | Yes | Instructor |
| POST | `/quizzes/{quiz_id}/attempts` | Start attempt | Yes | Student |
| GET | `/quizzes/{quiz_id}/attempts/` | My attempts | Yes | Student |
| POST | `/quizzes/{quiz_id}/attempts/{attempt_id}/submit` | Submit attempt | Yes | Student |
| GET | `/quizzes/{quiz_id}/attempts/{attempt_id}` | Get attempt result | Yes | Student |

### Questions (`/questions`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/questions/quiz/{quiz_id}` | Quiz questions | Yes | - `/questions/` | Create question | Yes | Instructor |
| |
| POST | PUT | `/questions/{question_id}` | Update question | Yes | Instructor |
| DELETE | `/questions/{question_id}` | Delete question | Yes | Instructor |

### Assignments (`/assignments`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/assignments/` | List assignments | Yes | - |
| GET | `/assignments/{assignment_id}` | Get assignment | Yes | - |
| POST | `/assignments/` | Create assignment | Yes | Instructor |
| PUT | `/assignments/{assignment_id}` | Update assignment | Yes | Instructor |
| DELETE | `/assignments/{assignment_id}` | Delete assignment | Yes | Instructor |
| POST | `/assignments/{assignment_id}/submit` | Submit assignment | Yes | Student |
| GET | `/assignments/{assignment_id}/submissions` | List submissions | Yes | Instructor |
| GET | `/assignments/submissions/{submission_id}` | Get submission | Yes | Student (own), Instructor |
| POST | `/assignments/submissions/{submission_id}/grade` | Grade submission | Yes | Instructor |

### Files (`/files`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| POST | `/files/upload` | Upload file | Yes | All |
| GET | `/files/{file_id}` | Get file metadata | Yes | - |
| GET | `/files/{file_id}/download` | Download file | Yes | - |
| DELETE | `/files/{file_id}` | Delete file | Yes | - |
| GET | `/files/` | List my files | Yes | - |

### Certificates (`/certificates`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/certificates/` | My certificates | Yes | - |
| GET | `/certificates/{certificate_id}` | Get certificate | Yes | - |
| POST | `/certificates/generate/{enrollment_id}` | Generate certificate | Yes | Student |
| GET | `/certificates/verify/{certificate_number}` | Verify certificate | No | - |

### Payments (`/payments`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| POST | `/payments/create-intent/{order_id}` | Create payment intent | Yes | - |
| POST | `/payments/webhook` | Stripe webhook | No* | - |
| GET | `/payments/{payment_id}` | Get payment details | Yes | - |
| POST | `/payments/{payment_id}/refund` | Refund payment | Yes | Admin |
| GET | `/payments/` | List payments | Yes | Admin |

*Requires signature verification.

### Analytics (`/analytics`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/analytics/overview` | Dashboard overview | Yes | Admin |
| GET | `/analytics/courses/{course_id}` | Course analytics | Yes | Instructor, Admin |
| GET | `/analytics/enrollments` | Enrollment stats | Yes | Admin |
| GET | `/analytics/revenue` | Revenue report | Yes | Admin |
| GET | `/analytics/users/{user_id}` | User activity | Yes | User (own), Admin |

### Admin (`/admin`)

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | `/admin/users` | List all users | Yes | Admin |
| PUT | `/admin/users/{user_id}` | Update user | Yes | Admin |
| DELETE | `/admin/users/{user_id}` | Delete user | Yes | Admin |
| POST | `/admin/users/{user_id}/impersonate` | Impersonate user | Yes | Admin |
| GET | `/admin/audit-logs` | View audit logs | Yes | Admin |
| GET | `/admin/stats` | System statistics | Yes | Admin |

### WebSocket

| Path | Description | Auth |
|------|-------------|------|
| `/ws/notifications` | Real-time notifications | Yes (JWT in query) |

---

## Request/Response Formats

### Pagination

All list endpoints support pagination:

```
GET /users/?page=1&page_size=20
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |

**Response:**
```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 100,
  "pages": 5
}
```

### Filtering

Many endpoints support filtering via query parameters:

```
GET /courses/?category=programming&is_published=true
GET /enrollments/?course_id=uuid
```

### Sorting

Sort via `sort` parameter:

```
GET /courses/?sort=-created_at  # Descending
GET /courses/?sort=price         # Ascending
```

### Search

Full-text search on certain endpoints:

```
GET /courses/?search=python
```

---

## Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Global | 100 | 1 minute |
| Auth | 60 | 1 minute |
| File Upload | 100 | 1 hour |
| Assignments | 60 | 1 minute |

Rate limit headers returned:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "missing"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Response Envelope (Optional)

When enabled, responses wrapped in envelope:

```json
{
  "success": true,
  "message": "Success",
  "data": { ... }
}
```

Enable via: `API_RESPONSE_ENVELOPE_ENABLED`

---

## WebSocket Messages

### Connection
```
wss://api.example.com/ws/notifications?token=<jwt>
```

### Message Types

**From Server:**
```json
{
  "type": "lesson_completed",
  "payload": {
    "lesson_id": "uuid",
    "progress": 50
  }
}
```

```json
{
  "type": "course_updated",
  "payload": {
    "course_id": "uuid",
    "changes": ["title", "description"]
  }
}
```

```json
{
  "type": "new_enrollment",
  "payload": {
    "course_id": "uuid",
    "student_name": "John Doe"
  }
}
```

```json
{
  "type": "assignment_graded",
  "payload": {
    "assignment_id": "uuid",
    "grade": 95
  }
}
```

---

## OpenAPI Documentation

Full API specification available at:
- Development: `/docs`
- Production: Not available (disabled)

---

## SDK Generation

Generate client SDKs:

```bash
# Python client
openapi-generator generate -i /openapi.json -g python -o ./sdk/python

# TypeScript client
openapi-generator generate -i /openapi.json -g typescript -o ./sdk/typescript

# C# client
openapi-generator generate -i /openapi.json -g csharp -o ./sdk/csharp
```
