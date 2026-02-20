# API Documentation

This reference matches the current implementation in code and OpenAPI.

## 1. API Overview

### Base URL
- Production: `https://api.yourdomain.com/api/v1`
- Development: `http://localhost:8000/api/v1`

### Authentication
- Type: Bearer Token (JWT)
- Header: `Authorization: Bearer <access_token>`
- Swagger OAuth2 token endpoint: `POST /api/v1/auth/token`

### Response Format
- If `API_RESPONSE_ENVELOPE_ENABLED=true`, successful JSON responses are wrapped:
```json
{
  "success": true,
  "data": {},
  "message": "Success"
}
```
- In local development (`.env.example`) this is disabled by default.

### Error Format
```json
{
  "detail": "Error message"
}
```

Validation errors use FastAPI default:
```json
{
  "detail": [
    {
      "loc": ["body", "field"],
      "msg": "validation message",
      "type": "validation_error_type"
    }
  ]
}
```

## 2. Authentication Endpoints

### Register
- `POST /auth/register`
- Response: `201 Created`
- Returns:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "User Name",
    "role": "student",
    "is_active": true,
    "mfa_enabled": false,
    "created_at": "2026-02-20T10:00:00Z",
    "email_verified_at": null
  },
  "tokens": {
    "access_token": "jwt",
    "refresh_token": "jwt",
    "token_type": "bearer"
  }
}
```

### Login
- `POST /auth/login`
- Response: `200 OK`
- Returns either:
1. `AuthResponse` (`user` + `tokens`)
2. `MfaChallengeResponse`:
```json
{
  "mfa_required": true,
  "challenge_token": "token",
  "expires_in_seconds": 600,
  "message": "MFA verification required"
}
```

### OAuth Token (Swagger Authorize)
- `POST /auth/token`
- Form fields: `username`, `password`
- Response: `TokenResponse`

### Verify MFA Login
- `POST /auth/login/mfa`
- Request:
```json
{
  "challenge_token": "token",
  "code": "123456"
}
```
- Response: `AuthResponse`

### Refresh Tokens
- `POST /auth/refresh`
- Request:
```json
{
  "refresh_token": "jwt"
}
```
- Response: `AuthResponse`

### Logout
- `POST /auth/logout`
- Request:
```json
{
  "refresh_token": "jwt"
}
```
- Response: `204 No Content`

### Forgot Password
- `POST /auth/forgot-password`

### Reset Password
- `POST /auth/reset-password`

### Email Verification
- `POST /auth/verify-email/request`
- `POST /auth/verify-email/confirm`

### MFA Settings
- `POST /auth/mfa/enable/request`
- `POST /auth/mfa/enable/confirm`
- `POST /auth/mfa/disable`

### Current User
- `GET /auth/me`
- Response: `UserResponse`

## 3. Users Endpoints (Admin)

- `GET /users` (admin only, paginated)
- `POST /users` (admin only)
- `GET /users/{user_id}` (admin only)
- `PATCH /users/{user_id}` (admin only)
- `GET /users/me` (authenticated)

Paginated format:
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

## 4. Courses Endpoints

### List Courses
- `GET /courses`
- Query params:
  - `page` (default 1)
  - `page_size` (default 20, max 100)
  - `category`
  - `difficulty_level` (`beginner|intermediate|advanced`)
  - `mine` (default `false`)

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Course title",
      "slug": "course-title",
      "description": "text",
      "instructor_id": "uuid",
      "category": "Programming",
      "difficulty_level": "beginner",
      "is_published": true,
      "thumbnail_url": null,
      "estimated_duration_minutes": 600,
      "created_at": "2026-02-20T10:00:00Z",
      "updated_at": "2026-02-20T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Course CRUD
- `POST /courses` (instructor/admin)
- `GET /courses/{course_id}`
- `PATCH /courses/{course_id}` (owner/admin)
- `POST /courses/{course_id}/publish` (owner/admin)
- `DELETE /courses/{course_id}` (owner/admin, `204`)

## 5. Lessons Endpoints

- `GET /courses/{course_id}/lessons`
- `POST /courses/{course_id}/lessons` (owner/admin)
- `GET /lessons/{lesson_id}`
- `PATCH /lessons/{lesson_id}` (owner/admin)
- `DELETE /lessons/{lesson_id}` (owner/admin, `204`)

List response:
```json
{
  "items": [],
  "total": 0
}
```

Note:
- Lessons use `parent_lesson_id` (not `section_id`) for hierarchy.

## 6. Enrollments Endpoints

- `POST /enrollments`
- `GET /enrollments/my-courses`
- `GET /enrollments/{enrollment_id}`
- `PUT /enrollments/{enrollment_id}/lessons/{lesson_id}/progress`
- `POST /enrollments/{enrollment_id}/lessons/{lesson_id}/complete`
- `POST /enrollments/{enrollment_id}/review`
- `GET /enrollments/courses/{course_id}` (instructor/admin course scope)
- `GET /enrollments/courses/{course_id}/stats` (instructor/admin course scope)

Review rules:
- `rating`: 1..5
- `review`: min 10 chars
- progress must be at least 20%

## 7. Quizzes Endpoints

### Quiz CRUD
- `GET /courses/{course_id}/quizzes`
- `POST /courses/{course_id}/quizzes`
- `GET /courses/{course_id}/quizzes/{quiz_id}`
- `PATCH /courses/{course_id}/quizzes/{quiz_id}`
- `POST /courses/{course_id}/quizzes/{quiz_id}/publish`

Important:
- `QuizCreate` requires `lesson_id`.

### Questions
- `GET /courses/{course_id}/quizzes/{quiz_id}/questions` (public shape, no correct answers)
- `GET /courses/{course_id}/quizzes/{quiz_id}/questions/manage` (management shape with answer keys)
- `POST /courses/{course_id}/quizzes/{quiz_id}/questions`
- `PATCH /courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}`

### Attempts
- `POST /quizzes/{quiz_id}/attempts`
- `GET /quizzes/{quiz_id}/attempts/start`
- `POST /quizzes/{quiz_id}/attempts/{attempt_id}/submit`
- `GET /quizzes/{quiz_id}/attempts/{attempt_id}`
- `GET /quizzes/{quiz_id}/attempts/my-attempts`

## 8. Analytics Endpoints

- `GET /analytics/my-progress`
- `GET /analytics/my-dashboard`
- `GET /analytics/courses/{course_id}`
- `GET /analytics/instructors/{instructor_id}/overview`
- `GET /analytics/system/overview`

## 9. Files Endpoints

- `POST /files/upload` (`multipart/form-data`)
  - form fields: `file`, `folder` (default `uploads`), `is_public` (default `false`)
- `GET /files/my-files`
- `GET /files/download/{file_id}`
  - returns file stream or `307` redirect for remote storage target

## 10. Certificates Endpoints

- `POST /certificates/enrollments/{enrollment_id}/generate` (`201`)
- `GET /certificates/my-certificates`
- `GET /certificates/{certificate_id}/download`
- `POST /certificates/{certificate_id}/revoke`
- `GET /certificates/verify/{certificate_number}` (public)

Verify response:
```json
{
  "valid": true,
  "certificate": {
    "id": "uuid",
    "certificate_number": "CERT-...",
    "student_id": "uuid",
    "course_id": "uuid",
    "completion_date": "2026-02-20T10:00:00Z",
    "issued_at": "2026-02-20T10:00:00Z",
    "pdf_url": "/certificates/{certificate_id}/download",
    "is_revoked": false
  },
  "message": "Certificate is valid"
}
```

## 11. System Endpoints

- `GET /health`
- `GET /ready`
- `GET /metrics`

## 12. HTTP Status Codes Used

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## 13. Rate Limiting

Current implementation is global, path-aware, and based on:
- `RATE_LIMIT_REQUESTS_PER_MINUTE` (default `100`)
- `RATE_LIMIT_WINDOW_SECONDS` (default `60`)
- Optional specialized limits:
  - auth endpoints (`AUTH_RATE_LIMIT_*`)
  - upload endpoints (`FILE_UPLOAD_RATE_LIMIT_*`)

Headers:
```text
X-RateLimit-Limit
X-RateLimit-Remaining
X-RateLimit-Reset
Retry-After (on 429)
```

429 body:
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

## 14. Webhooks (Optional)

Event dispatch is available when:
- `WEBHOOKS_ENABLED=true`
- `WEBHOOK_TARGET_URLS` configured

Event types:
- `enrollment.created`
- `enrollment.completed`
- `certificate.issued`
- `quiz.submitted`
- `course.published`

Payload format:
```json
{
  "event": "enrollment.completed",
  "timestamp": "2026-02-20T12:00:00+00:00",
  "data": {}
}
```

## 15. Pagination

Standard paginated endpoints return:
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

## 16. Postman and SDK Notes

### Postman files
- `postman/LMS Backend.postman_collection.json`
- `postman/LMS Backend.postman_environment.json`
- `postman/LMS Backend Demo.postman_collection.json`
- `postman/LMS Backend Demo.postman_environment.json`

Generate:
```bash
python scripts/generate_postman_collection.py
python scripts/generate_demo_postman.py --seed-file postman/demo_seed_snapshot.json
```

### Python client note
When using login, access token is under:
- `response["tokens"]["access_token"]`
- not at top-level `response["access_token"]`

## 17. Interactive Docs

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

In production (`ENVIRONMENT=production`), docs are disabled by default.
