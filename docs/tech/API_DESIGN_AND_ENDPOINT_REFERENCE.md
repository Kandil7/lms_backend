# API Design and Endpoint Reference

This document provides comprehensive documentation of the LMS Backend REST API, including endpoint specifications, request/response formats, authentication requirements, and usage examples.

---

## Table of Contents

1. [API Conventions](#api-conventions)
2. [Authentication](#authentication)
3. [User Endpoints](#user-endpoints)
4. [Course Endpoints](#course-endpoints)
5. [Lesson Endpoints](#lesson-endpoints)
6. [Enrollment Endpoints](#enrollment-endpoints)
7. [Quiz Endpoints](#quiz-endpoints)
8. [Attempt Endpoints](#attempt-endpoints)
9. [Analytics Endpoints](#analytics-endpoints)
10. [File Endpoints](#file-endpoints)
11. [Certificate Endpoints](#certificate-endpoints)
12. [Health Check Endpoints](#health-check-endpoints)

---

## API Conventions

### Base URL

All API endpoints are prefixed with the API version:

```
https://api.example.com/api/v1
```

For local development:
```
http://localhost:8000/api/v1
```

### Response Format

All responses follow a consistent JSON structure:

**Successful Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "student",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Response**:
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Paginated Response**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

### HTTP Methods

| Method | Usage |
|--------|-------|
| GET | Retrieve resources |
| POST | Create new resources |
| PATCH | Partial update (use JSON Merge Patch) |
| PUT | Full replacement (not typically used) |
| DELETE | Remove resources |

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (new resource) |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid or missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate or invalid state) |
| 422 | Unprocessable Entity (validation failure) |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |

### Query Parameters

Common query parameters for list endpoints:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |
| sort | string | created_at | Sort field |
| order | string | desc | Sort order (asc/desc) |

---

## Authentication

### Overview

The API uses JWT (JSON Web Tokens) for authentication. Most endpoints require a valid access token in the Authorization header.

### Authentication Flow

1. **Register**: Create a new user account
2. **Login**: Receive access and refresh tokens
3. **Use Access Token**: Include in Authorization header for API requests
4. **Refresh**: Use refresh token to get new access token when expired
5. **Logout**: Blacklist the access token

### Login

**Endpoint**: `POST /api/v1/auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Register

**Endpoint**: `POST /api/v1/auth/register`

**Request**:
```json
{
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "full_name": "New User"
}
```

**Response**: Same as login

### Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response**: New access and refresh tokens

### Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: 204 No Content

---

## User Endpoints

### Get Current User

**Endpoint**: `GET /api/v1/users/me`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "student",
  "is_active": true,
  "mfa_enabled": false,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login_at": "2024-01-20T15:45:00Z"
}
```

### Update Current User

**Endpoint**: `PATCH /api/v1/users/me`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "full_name": "John Smith"
}
```

**Response**: Updated user object

### Change Password

**Endpoint**: `POST /api/v1/users/me/password`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword123"
}
```

**Response**: 204 No Content

---

## Course Endpoints

### List Courses

**Endpoint**: `GET /api/v1/courses`

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number |
| page_size | int | Items per page |
| category | string | Filter by category |
| difficulty_level | string | Filter by difficulty |
| mine | bool | Only my courses (authenticated) |

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Python Basics",
      "slug": "python-basics",
      "description": "Learn Python fundamentals",
      "category": "Programming",
      "difficulty_level": "beginner",
      "is_published": true,
      "thumbnail_url": "https://...",
      "estimated_duration_minutes": 120,
      "instructor_id": "uuid",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### Create Course

**Endpoint**: `POST /api/v1/courses`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "title": "Python Basics",
  "description": "Learn Python fundamentals",
  "category": "Programming",
  "difficulty_level": "beginner",
  "estimated_duration_minutes": 120
}
```

**Response**: 201 Created with course object

**Note**: Requires instructor or admin role

### Get Course

**Endpoint**: `GET /api/v1/courses/{course_id}`

**Response**:
```json
{
  "id": "uuid",
  "title": "Python Basics",
  "slug": "python-basics",
  "description": "Learn Python fundamentals",
  "category": "Programming",
  "difficulty_level": "beginner",
  "is_published": true,
  "thumbnail_url": "https://...",
  "estimated_duration_minutes": 120,
  "instructor_id": "uuid",
  "lessons": [
    {
      "id": "uuid",
      "title": "Introduction",
      "order": 1,
      "duration_minutes": 15
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Update Course

**Endpoint**: `PATCH /api/v1/courses/{course_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "title": "Python Fundamentals"
}
```

**Response**: Updated course object

**Note**: Requires course owner or admin

### Publish Course

**Endpoint**: `POST /api/v1/courses/{course_id}/publish`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: Updated course object with is_published=true

### Delete Course

**Endpoint**: `DELETE /api/v1/courses/{course_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: 204 No Content

**Note**: Requires course owner or admin

---

## Lesson Endpoints

### List Lessons

**Endpoint**: `GET /api/v1/courses/{course_id}/lessons`

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Introduction to Python",
      "content_type": "video",
      "video_url": "https://...",
      "duration_minutes": 15,
      "order": 1
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

### Create Lesson

**Endpoint**: `POST /api/v1/courses/{course_id}/lessons`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "title": "Introduction to Python",
  "content_type": "video",
  "video_url": "https://youtube.com/...",
  "duration_minutes": 15,
  "content": "Welcome to the course..."
}
```

**Response**: 201 Created with lesson object

### Get Lesson

**Endpoint**: `GET /api/v1/lessons/{lesson_id}`

**Response**: Lesson object

### Update Lesson

**Endpoint**: `PATCH /api/v1/lessons/{lesson_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**: Fields to update

**Response**: Updated lesson object

### Delete Lesson

**Endpoint**: `DELETE /api/v1/lessons/{lesson_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: 204 No Content

### Reorder Lessons

**Endpoint**: `PATCH /api/v1/lessons/reorder`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "lesson_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response**: 204 No Content

---

## Enrollment Endpoints

### Enroll in Course

**Endpoint**: `POST /api/v1/enrollments`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "course_id": "uuid-of-course"
}
```

**Response**: 201 Created with enrollment object
```json
{
  "id": "uuid",
  "course_id": "uuid",
  "student_id": "uuid",
  "enrolled_at": "2024-01-20T15:45:00Z",
  "completed_at": null
}
```

### Get My Enrollments

**Endpoint**: `GET /api/v1/enrollments/my-courses`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "course": {
        "id": "uuid",
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

### Get Enrollment

**Endpoint**: `GET /api/v1/enrollments/{enrollment_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: Enrollment object with progress details

### Complete Lesson

**Endpoint**: `POST /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/complete`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: Updated lesson progress
```json
{
  "id": "uuid",
  "lesson_id": "uuid",
  "completed": true,
  "completed_at": "2024-01-20T16:00:00Z"
}
```

---

## Quiz Endpoints

### List Quizzes

**Endpoint**: `GET /api/v1/quizzes`

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| course_id | uuid | Filter by course |
| lesson_id | uuid | Filter by lesson |
| published_only | bool | Show published quizzes |

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Python Basics Quiz",
      "description": "Test your knowledge",
      "time_limit_minutes": 30,
      "passing_score_percentage": 70,
      "question_count": 10
    }
  ],
  "total": 5
}
```

### Create Quiz

**Endpoint**: `POST /api/v1/quizzes`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "course_id": "uuid",
  "title": "Python Basics Quiz",
  "description": "Test your knowledge",
  "time_limit_minutes": 30,
  "passing_score_percentage": 70,
  "shuffle_questions": false
}
```

### Get Quiz

**Endpoint**: `GET /api/v1/quizzes/{quiz_id}`

**Response**:
```json
{
  "id": "uuid",
  "title": "Python Basics Quiz",
  "description": "Test your knowledge",
  "time_limit_minutes": 30,
  "passing_score_percentage": 70,
  "shuffle_questions": false,
  "is_published": true,
  "question_count": 10,
  "questions": [
    {
      "id": "uuid",
      "question_text": "What is Python?",
      "question_type": "multiple_choice",
      "options": [
        "A programming language",
        "A snake",
        "A framework"
      ],
      "points": 1,
      "order": 1
    }
  ]
}
```

### Update Quiz

**Endpoint**: `PATCH /api/v1/quizzes/{quiz_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**: Fields to update

### Delete Quiz

**Endpoint**: `DELETE /api/v1/quizzes/{quiz_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: 204 No Content

---

## Attempt Endpoints

### Start Quiz Attempt

**Endpoint**: `POST /api/v1/quizzes/{quiz_id}/attempts`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: 201 Created
```json
{
  "id": "uuid",
  "quiz_id": "uuid",
  "started_at": "2024-01-20T16:00:00Z",
  "ended_at": null,
  "answers": [],
  "score": null,
  "passed": null
}
```

### Get Attempt

**Endpoint**: `GET /api/v1/attempts/{attempt_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: Attempt object with questions

### Submit Attempt

**Endpoint**: `POST /api/v1/attempts/{attempt_id}/submit`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "answers": [
    {
      "question_id": "uuid",
      "answer": "A programming language"
    }
  ]
}
```

**Response**:
```json
{
  "id": "uuid",
  "quiz_id": "uuid",
  "started_at": "2024-01-20T16:00:00Z",
  "ended_at": "2024-01-20T16:30:00Z",
  "answers": [...],
  "score": 80,
  "passed": true
}
```

---

## Analytics Endpoints

### Student Analytics

**Endpoint**: `GET /api/v1/analytics/student`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "courses_enrolled": 5,
  "courses_completed": 2,
  "total_lessons_completed": 45,
  "quizzes_taken": 10,
  "average_quiz_score": 85,
  "learning_time_minutes": 600,
  "recent_activity": [
    {
      "date": "2024-01-20",
      "lessons_completed": 3,
      "quizzes_taken": 1
    }
  ]
}
```

### Instructor Analytics

**Endpoint**: `GET /api/v1/analytics/instructor`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "total_courses": 3,
  "published_courses": 2,
  "total_students": 150,
  "total_enrollments": 200,
  "average_completion_rate": 65,
  "average_quiz_score": 78,
  "course_performance": [
    {
      "course_id": "uuid",
      "course_title": "Python Basics",
      "enrollments": 50,
      "completion_rate": 70,
      "average_score": 82
    }
  ]
}
```

### Course Analytics

**Endpoint**: `GET /api/v1/analytics/courses/{course_id}/analytics`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: Detailed course analytics

### System Analytics

**Endpoint**: `GET /api/v1/analytics/system`

**Headers**:
```
Authorization: Bearer <access_token> (Admin only)
```

**Response**: Platform-wide statistics

---

## File Endpoints

### Upload File

**Endpoint**: `POST /api/v1/files/upload`

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request**: Form data with file field

**Response**:
```json
{
  "id": "uuid",
  "original_filename": "document.pdf",
  "file_size": 1024000,
  "content_type": "application/pdf",
  "uploaded_at": "2024-01-20T16:00:00Z"
}
```

### List Files

**Endpoint**: `GET /api/v1/files`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: Paginated list of user's files

### Get File Metadata

**Endpoint**: `GET /api/v1/files/{file_id}`

**Response**: File metadata

### Download File

**Endpoint**: `GET /api/v1/files/{file_id}/download`

**Response**: File binary (redirect to signed URL)

### Delete File

**Endpoint**: `DELETE /api/v1/files/{file_id}`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: 204 No Content

---

## Certificate Endpoints

### Generate Certificate

**Endpoint**: `POST /api/v1/certificates/generate`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "enrollment_id": "uuid-of-completed-enrollment"
}
```

**Response**: Certificate object
```json
{
  "id": "uuid",
  "enrollment_id": "uuid",
  "certificate_number": "CERT-2024-001234",
  "issued_at": "2024-01-20T16:00:00Z",
  "course_title": "Python Basics",
  "student_name": "John Doe"
}
```

### Get Certificate

**Endpoint**: `GET /api/v1/certificates/{certificate_id}`

### Download Certificate

**Endpoint**: `GET /api/v1/certificates/{certificate_id}/download`

**Response**: PDF file (redirect to signed URL)

### My Certificates

**Endpoint**: `GET /api/v1/certificates/my-certificates`

**Headers**:
```
Authorization: Bearer <access_token>
```

---

## Health Check Endpoints

### Health Check

**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "status": "ok"
}
```

**Authentication**: Not required

### Readiness Check

**Endpoint**: `GET /api/v1/ready`

**Response**:
```json
{
  "status": "ok",
  "database": "up",
  "redis": "up"
}
```

**Authentication**: Not required

---

## Error Responses

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

### 409 Conflict

```json
{
  "detail": "Already enrolled in this course"
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

This API reference covers all endpoints in the LMS Backend. Key patterns to remember:

1. **Authentication**: Include Bearer token in Authorization header
2. **Pagination**: Use page and page_size parameters
3. **Filtering**: Use query parameters to filter results
4. **Updates**: Use PATCH for partial updates
5. **IDs**: Use UUIDs for all resource identifiers
6. **Errors**: Check HTTP status codes and detail field

For interactive testing, use the Swagger UI at `/docs` when the server is running.
