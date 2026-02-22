# Complete API Reference Guide

This document provides a comprehensive reference for all API endpoints in the LMS Backend, including request/response formats, authentication requirements, and usage examples.

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [User Endpoints](#user-endpoints)
3. [Course Endpoints](#course-endpoints)
4. [Lesson Endpoints](#lesson-endpoints)
5. [Enrollment Endpoints](#enrollment-endpoints)
6. [Quiz Endpoints](#quiz-endpoints)
7. [Attempt Endpoints](#attempt-endpoints)
8. [Analytics Endpoints](#analytics-endpoints)
9. [File Endpoints](#file-endpoints)
10. [Certificate Endpoints](#certificate-endpoints)
11. [Health Check Endpoints](#health-check-endpoints)

---

## Base URL

| Environment | URL |
|-------------|-----|
| Development | http://localhost:8000/api/v1 |
| Staging | https://staging-api.example.com/api/v1 |
| Production | https://api.example.com/api/v1 |

## Authentication

Most endpoints require authentication using JWT Bearer tokens:

```http
Authorization: Bearer <access_token>
```

---

## Authentication Endpoints

### Register User

Register a new user account.

**Endpoint**: `POST /auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

**Response** (201 Created):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Validation**:
- `email`: Valid email address, unique in system
- `password`: Minimum 8 characters, must contain uppercase, lowercase, and digit
- `full_name`: 1-255 characters

---

### Login

Authenticate and receive access tokens.

**Endpoint**: `POST /auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**:
- 401: Invalid credentials
- 423: Account locked (too many failed attempts)

---

### Refresh Token

Exchange refresh token for new access token.

**Endpoint**: `POST /auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### Logout

Invalidate current access token.

**Endpoint**: `POST /auth/logout`

**Headers**: `Authorization: Bearer <access_token>`

**Response**: 204 No Content

---

### Enable MFA

Enable multi-factor authentication for account.

**Endpoint**: `POST /auth/mfa/enable`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_url": "otpauth://totp/LMS%20Backend:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=LMS%20Backend"
}
```

**Next Step**: Verify with TOTP code using `/auth/mfa/verify`

---

### Verify MFA

Verify TOTP code and activate MFA.

**Endpoint**: `POST /auth/mfa/verify`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "code": "123456"
}
```

**Response** (200 OK):
```json
{
  "message": "MFA enabled successfully"
}
```

---

### Disable MFA

Disable multi-factor authentication.

**Endpoint**: `POST /auth/mfa/disable`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "code": "123456"
}
```

**Response**: 204 No Content

---

### MFA Login

Complete login with MFA code.

**Endpoint**: `POST /auth/mfa/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "mfa_code": "123456"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

## User Endpoints

### Get Current User

Retrieve authenticated user's profile.

**Endpoint**: `GET /users/me`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "student",
  "is_active": true,
  "mfa_enabled": false,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login_at": "2024-01-20T15:45:00Z"
}
```

---

### Update Current User

Update user's own profile.

**Endpoint**: `PATCH /users/me`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "full_name": "John Smith"
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Smith",
  "role": "student",
  "is_active": true,
  "mfa_enabled": false,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login_at": "2024-01-20T15:45:00Z"
}
```

---

### Change Password

Change user's password.

**Endpoint**: `POST /users/me/password`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword123"
}
```

**Response**: 204 No Content

**Errors**:
- 400: Current password is incorrect

---

## Course Endpoints

### List Courses

Retrieve paginated list of courses.

**Endpoint**: `GET /courses`

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |
| category | string | - | Filter by category |
| difficulty_level | string | - | Filter by difficulty |
| mine | bool | false | Only instructor's courses |

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Python Basics",
      "slug": "python-basics",
      "description": "Learn Python fundamentals",
      "category": "Programming",
      "difficulty_level": "beginner",
      "is_published": true,
      "thumbnail_url": "https://example.com/thumb.jpg",
      "estimated_duration_minutes": 120,
      "instructor_id": "550e8400-e29b-41d4-a716-446655440001",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

### Create Course

Create a new course (instructor/admin only).

**Endpoint**: `POST /courses`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "title": "Python Basics",
  "description": "Learn Python fundamentals",
  "category": "Programming",
  "difficulty_level": "beginner",
  "estimated_duration_minutes": 120,
  "thumbnail_url": "https://example.com/thumb.jpg"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Python Basics",
  "slug": "python-basics",
  "description": "Learn Python fundamentals",
  "category": "Programming",
  "difficulty_level": "beginner",
  "is_published": false,
  "thumbnail_url": "https://example.com/thumb.jpg",
  "estimated_duration_minutes": 120,
  "instructor_id": "550e8400-e29b-41d4-a716-446655440001",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Authorization**: Requires `instructor` or `admin` role

---

### Get Course

Retrieve single course details.

**Endpoint**: `GET /courses/{course_id}`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Python Basics",
  "slug": "python-basics",
  "description": "Learn Python fundamentals",
  "category": "Programming",
  "difficulty_level": "beginner",
  "is_published": true,
  "thumbnail_url": "https://example.com/thumb.jpg",
  "estimated_duration_minutes": 120,
  "instructor_id": "550e8400-e29b-41d4-a716-446655440001",
  "lessons": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "title": "Introduction",
      "order": 1,
      "duration_minutes": 15
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### Update Course

Update course details (owner/admin only).

**Endpoint**: `PATCH /courses/{course_id}`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "title": "Python Fundamentals",
  "description": "Updated description"
}
```

**Response** (200 OK): Updated course object

**Authorization**: Course owner or `admin` role

---

### Publish Course

Publish a course (owner/admin only).

**Endpoint**: `POST /courses/{course_id}/publish`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Python Basics",
  "is_published": true,
  ...
}
```

---

### Delete Course

Delete a course (owner/admin only).

**Endpoint**: `DELETE /courses/{course_id}`

**Headers**: `Authorization: Bearer <access_token>`

**Response**: 204 No Content

---

## Lesson Endpoints

### List Lessons

Get all lessons for a course.

**Endpoint**: `GET /courses/{course_id}/lessons`

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Introduction to Python",
      "content_type": "video",
      "video_url": "https://youtube.com/watch?v=...",
      "content": "Welcome to the course...",
      "duration_minutes": 15,
      "order": 1,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### Create Lesson

Add lesson to course (owner/admin only).

**Endpoint**: `POST /courses/{course_id}/lessons`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "title": "Introduction to Python",
  "content_type": "video",
  "video_url": "https://youtube.com/watch?v=...",
  "content": "Welcome to the course...",
  "duration_minutes": 15
}
```

---

### Get Lesson

Retrieve single lesson.

**Endpoint**: `GET /lessons/{lesson_id}`

---

### Update Lesson

Update lesson (owner/admin only).

**Endpoint**: `PATCH /lessons/{lesson_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

### Delete Lesson

Delete lesson (owner/admin only).

**Endpoint**: `DELETE /lessons/{lesson_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

### Reorder Lessons

Reorder lessons within a course.

**Endpoint**: `PATCH /lessons/reorder`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "course_id": "550e8400-e29b-41d4-a716-446655440000",
  "lesson_ids": [
    "550e8400-e29b-41d4-a716-446655440002",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440003"
  ]
}
```

---

## Enrollment Endpoints

### Enroll in Course

Enroll in a course.

**Endpoint**: `POST /enrollments`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "course_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "course_id": "550e8400-e29b-41d4-a716-446655440001",
  "student_id": "550e8400-e29b-41d4-a716-446655440002",
  "enrolled_at": "2024-01-20T15:45:00Z",
  "completed_at": null
}
```

---

### Get My Enrollments

List enrolled courses.

**Endpoint**: `GET /enrollments/my-courses`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "course": {
        "id": "...",
        "title": "Python Basics"
      },
      "enrolled_at": "2024-01-20T15:45:00Z",
      "completed_at": null,
      "progress_percentage": 30
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### Get Enrollment

Get specific enrollment details.

**Endpoint**: `GET /enrollments/{enrollment_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

### Complete Lesson

Mark lesson as complete.

**Endpoint**: `POST /enrollments/{enrollment_id}/lessons/{lesson_id}/complete`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "lesson_id": "550e8400-e29b-41d4-a716-446655440001",
  "completed": true,
  "completed_at": "2024-01-20T16:00:00Z"
}
```

---

## Quiz Endpoints

### List Quizzes

List available quizzes.

**Endpoint**: `GET /quizzes`

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| course_id | uuid | Filter by course |
| lesson_id | uuid | Filter by lesson |
| published_only | bool | Show published only |

---

### Create Quiz

Create quiz (instructor/admin only).

**Endpoint**: `POST /quizzes`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "course_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Python Basics Quiz",
  "description": "Test your knowledge",
  "time_limit_minutes": 30,
  "passing_score_percentage": 70,
  "shuffle_questions": false
}
```

---

### Get Quiz

Get quiz details with questions.

**Endpoint**: `GET /quizzes/{quiz_id}`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Python Basics Quiz",
  "description": "Test your knowledge",
  "time_limit_minutes": 30,
  "passing_score_percentage": 70,
  "shuffle_questions": false,
  "is_published": true,
  "question_count": 10,
  "questions": [
    {
      "id": "...",
      "question_text": "What is Python?",
      "question_type": "multiple_choice",
      "options": ["A", "B", "C", "D"],
      "points": 1,
      "order": 1
    }
  ]
}
```

---

### Update Quiz

Update quiz (owner/admin only).

**Endpoint**: `PATCH /quizzes/{quiz_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

### Delete Quiz

Delete quiz (owner/admin only).

**Endpoint**: `DELETE /quizzes/{quiz_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

## Attempt Endpoints

### Start Quiz Attempt

Begin taking a quiz.

**Endpoint**: `POST /quizzes/{quiz_id}/attempts`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "quiz_id": "550e8400-e29b-41d4-a716-446655440001",
  "started_at": "2024-01-20T16:00:00Z",
  "ended_at": null,
  "answers": [],
  "score": null,
  "passed": null
}
```

---

### Get Attempt

Get attempt details.

**Endpoint**: `GET /attempts/{attempt_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

### Submit Attempt

Submit quiz answers.

**Endpoint**: `POST /attempts/{attempt_id}/submit`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "answers": [
    {
      "question_id": "550e8400-e29b-41d4-a716-446655440001",
      "answer": "A"
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "quiz_id": "...",
  "started_at": "2024-01-20T16:00:00Z",
  "ended_at": "2024-01-20T16:30:00Z",
  "score": 80,
  "passed": true,
  "answers": [
    {
      "question_id": "...",
      "answer": "A",
      "correct": true,
      "points_earned": 1
    }
  ]
}
```

---

## Analytics Endpoints

### Student Analytics

Get personal analytics.

**Endpoint**: `GET /analytics/student`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "courses_enrolled": 5,
  "courses_completed": 2,
  "total_lessons_completed": 45,
  "quizzes_taken": 10,
  "average_quiz_score": 85,
  "learning_time_minutes": 600
}
```

---

### Instructor Analytics

Get analytics for instructor's courses.

**Endpoint**: `GET /analytics/instructor`

**Headers**: `Authorization: Bearer <access_token>`

**Authorization**: Requires `instructor` or `admin` role

---

### Course Analytics

Get detailed analytics for a course.

**Endpoint**: `GET /analytics/courses/{course_id}/analytics`

**Headers**: `Authorization: Bearer <access_token>`

---

### System Analytics

Get platform-wide analytics (admin only).

**Endpoint**: `GET /analytics/system`

**Headers**: `Authorization: Bearer <access_token>`

**Authorization**: Requires `admin` role

---

## File Endpoints

### Upload File

Upload a file.

**Endpoint**: `POST /files/upload`

**Headers**: `Authorization: Bearer <access_token>`

**Content-Type**: multipart/form-data

**Form Data**:
- `file`: The file to upload

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "document.pdf",
  "stored_filename": "abc123.pdf",
  "file_size": 1024000,
  "content_type": "application/pdf",
  "uploaded_at": "2024-01-20T16:00:00Z"
}
```

---

### List Files

List uploaded files.

**Endpoint**: `GET /files`

**Headers**: `Authorization: Bearer <access_token>`

---

### Get File

Get file metadata.

**Endpoint**: `GET /files/{file_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

### Download File

Download file.

**Endpoint**: `GET /files/{file_id}/download`

**Headers**: `Authorization: Bearer <access_token>`

**Response**: Redirect to signed download URL

---

### Delete File

Delete uploaded file.

**Endpoint**: `DELETE /files/{file_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

## Certificate Endpoints

### Generate Certificate

Generate certificate for completed course.

**Endpoint**: `POST /certificates/generate`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "enrollment_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "enrollment_id": "...",
  "certificate_number": "CERT-2024-001234",
  "issued_at": "2024-01-20T16:00:00Z",
  "course_title": "Python Basics",
  "student_name": "John Doe"
}
```

---

### Get Certificate

Get certificate details.

**Endpoint**: `GET /certificates/{certificate_id}`

**Headers**: `Authorization: Bearer <access_token>`

---

### Download Certificate

Download certificate PDF.

**Endpoint**: `GET /certificates/{certificate_id}/download`

**Headers**: `Authorization: Bearer <access_token>`

**Response**: Redirect to PDF download URL

---

### My Certificates

List my certificates.

**Endpoint**: `GET /certificates/my-certificates`

**Headers**: `Authorization: Bearer <access_token>`

---

## Health Check Endpoints

### Health Check

Basic liveness check.

**Endpoint**: `GET /health`

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

---

### Readiness Check

Readiness check with dependency status.

**Endpoint**: `GET /ready`

**Response** (200 OK):
```json
{
  "status": "ok",
  "database": "up",
  "redis": "up"
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
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
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 429 Rate Limited

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Summary

This API reference covers all endpoints in the LMS Backend:

- **Authentication**: 9 endpoints for registration, login, MFA
- **Users**: 3 endpoints for profile management
- **Courses**: 6 endpoints for course CRUD and publishing
- **Lessons**: 6 endpoints for lesson management
- **Enrollments**: 4 endpoints for enrollment and progress
- **Quizzes**: 5 endpoints for quiz management
- **Attempts**: 3 endpoints for quiz taking
- **Analytics**: 4 endpoints for different analytics views
- **Files**: 5 endpoints for file operations
- **Certificates**: 4 endpoints for certificate management
- **Health**: 2 endpoints for monitoring

For interactive testing, use the Swagger UI at `/docs` when the server is running.
