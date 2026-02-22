# API Design Patterns

## REST API Architecture and Conventions

This document explains the API design patterns, versioning strategy, and conventions used in this LMS backend.

---

## 1. API Versioning Strategy

### Why Versioning?

API versioning allows the backend to evolve without breaking existing clients. This LMS uses **URL-based versioning** for clarity and stability.

### Version Structure

```
Base URL: /api/v1/

┌─────────────────────────────────────────────────────────────────┐
│                    API VERSION EVOLUTION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  /api/v1/...    <- Current stable version                      │
│       │                                                          │
│       │  (Future evolution)                                     │
│       ▼                                                          │
│  /api/v2/...    <- Future version (if breaking changes)        │
│                                                                 │
│  Best Practices:                                               │
│  - Never remove old versions abruptly                          │
│  - Deprecation warnings before removing                        │
│  - Support multiple versions simultaneously                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# app/main.py
from fastapi import FastAPI
from app.api.v1 import api as api_v1

app = FastAPI(title="LMS Backend API")

# Versioned API router
app.include_router(api_v1.router, prefix="/api/v1")
```

---

## 2. URL Structure Convention

### Resource Naming

```
┌─────────────────────────────────────────────────────────────────┐
│                    URL STRUCTURE PATTERNS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Collection Endpoints:                                          │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ GET /courses    │  │ List all courses│                      │
│  │ POST /courses   │  │ Create course   │                      │
│  └─────────────────┘  └─────────────────┘                      │
│                                                                 │
│  Member Endpoints:                                              │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ GET /courses/id │  │ Get course     │                      │
│  │ PATCH /courses/id│  │ Update course  │                      │
│  │ DELETE /courses/id│ │ Delete course │                      │
│  └─────────────────┘  └─────────────────┘                      │
│                                                                 │
│  Nested Resources:                                              │
│  ┌─────────────────────────────────────────┐                    │
│  │ GET /courses/{id}/lessons               │                   │
│  │ POST /courses/{id}/lessons              │                   │
│  │ GET /courses/{id}/lessons/{lesson_id}   │                   │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
│  Actions:                                                       │
│  ┌─────────────────────────────────────────┐                    │
│  │ POST /courses/{id}/publish              │                   │
│  │ POST /courses/{id}/enroll               │                   │
│  │ POST /courses/{id}/lessons/{id}/complete│                   │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### HTTP Methods

| Method | Usage | Idempotent |
|--------|-------|------------|
| GET | Retrieve resources | Yes |
| POST | Create resources | No |
| PATCH | Partial update | No |
| PUT | Full replacement | Yes |
| DELETE | Remove resources | Yes |

---

## 3. Request/Response Patterns

### Standard Response Envelope

```python
# Optional response wrapper
{
    "success": true,
    "data": { ... },
    "message": "Operation successful",
    "meta": {
        "page": 1,
        "page_size": 20,
        "total": 100
    }
}
```

### Pagination

```python
# Request
GET /api/v1/courses?page=2&page_size=10

# Response
{
    "data": [
        { "id": "uuid", "title": "Course 1", ... },
        { "id": "uuid", "title": "Course 2", ... }
    ],
    "meta": {
        "page": 2,
        "page_size": 10,
        "total": 50,
        "total_pages": 5
    }
}
```

### Filtering

```python
# Single filter
GET /api/v1/courses?category=programming

# Multiple filters
GET /api/v1/courses?category=programming&difficulty_level=beginner&is_published=true

# Range filter
GET /api/v1/courses?created_at__gte=2024-01-01&created_at__lte=2024-12-31
```

### Sorting

```python
# Single sort
GET /api/v1/courses?sort=created_at

# Descending sort
GET /api/v1/courses?sort=-created_at

# Multiple sorts
GET /api/v1/courses?sort=-created_at,title
```

---

## 4. Error Response Format

### Standard Error Structure

```json
{
    "error": "error_code",
    "message": "Human-readable error message",
    "details": {
        "field": "Additional context about the error"
    }
}
```

### HTTP Status Codes

| Code | Usage | Example |
|------|-------|---------|
| 200 | Success | GET courses |
| 201 | Created | POST create course |
| 204 | No Content | DELETE success |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Validation Error | Schema validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error |

### Error Examples

```json
// 401 Unauthorized
{
    "error": "unauthorized",
    "message": "Invalid authentication credentials"
}

// 403 Forbidden
{
    "error": "forbidden",
    "message": "You don't have permission to access this resource"
}

// 404 Not Found
{
    "error": "not_found",
    "message": "Course with id 'uuid' not found"
}

// 422 Validation Error
{
    "error": "validation_error",
    "message": "Invalid input data",
    "details": {
        "email": "Invalid email format",
        "password": "Password must be at least 8 characters"
    }
}

// 429 Rate Limit
{
    "error": "rate_limit_exceeded",
    "message": "Too many requests",
    "details": {
        "retry_after": 60
    }
}
```

---

## 5. Authentication Endpoints

### Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Register                                                    │
│  ┌──────────────────┐                                          │
│  │ POST /auth/register │                                       │
│  │ Body: { email, password, full_name, role }                │
│  │ Response: { user, access_token, refresh_token }             │
│  └──────────────────┘                                          │
│                                                                 │
│  2. Login (Password)                                           │
│  ┌──────────────────┐                                          │
│  │ POST /auth/login    │                                       │
│  │ Body: { email, password }                                  │
│  │ Response: { access_token, refresh_token } OR MFA challenge │
│  └──────────────────┘                                          │
│                                                                 │
│  3. MFA Login (if enabled)                                     │
│  ┌──────────────────┐                                          │
│  │ POST /auth/login/mfa │                                     │
│  │ Body: { challenge_token, code }                            │
│  │ Response: { access_token, refresh_token }                  │
│  └──────────────────┘                                          │
│                                                                 │
│  4. Get New Tokens                                             │
│  ┌──────────────────┐                                          │
│  │ POST /auth/refresh  │                                       │
│  │ Body: { refresh_token }                                    │
│  │ Response: { access_token, refresh_token }                  │
│  └──────────────────┘                                          │
│                                                                 │
│  5. Logout                                                      │
│  ┌──────────────────┐                                          │
│  │ POST /auth/logout   │                                       │
│  │ Body: { refresh_token }                                    │
│  │ Response: 204 No Content                                   │
│  └──────────────────┘                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Protected Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                   PROTECTED ENDPOINTS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  All endpoints require Authorization header:                   │
│                                                                 │
│    Authorization: Bearer <access_token>                        │
│                                                                 │
│  Optional authentication (public data with user context):     │
│                                                                 │
│    Uses get_current_user_optional dependency                   │
│                                                                 │
│  Role-based access:                                            │
│                                                                 │
│    Admin:     /users/* (all operations)                        │
│    Instructor: /courses/* (own courses)                         │
│    Student:   /enrollments/*, /quizzes/* (take)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Course Management Endpoints

### Course CRUD

```
Endpoints: /api/v1/courses

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint           │  Description                  │
├──────────┼─────────────────────┼───────────────────────────────┤
│  GET     │  /courses           │  List courses (with filters)  │
│  POST    │  /courses           │  Create new course            │
│  GET     │  /courses/{id}      │  Get course details           │
│  PATCH   │  /courses/{id}      │  Update course                │
│  DELETE  │  /courses/{id}      │  Delete course                │
│  POST    │  /courses/{id}/publish   │  Publish course         │
└──────────┴─────────────────────┴───────────────────────────────┘
```

### Lesson Management

```
Endpoints: /api/v1/courses/{course_id}/lessons

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                    │  Description          │
├──────────┼───────────────────────────────┼───────────────────────┤
│  GET     │  /courses/{id}/lessons       │  List lessons         │
│  POST    │  /courses/{id}/lessons       │  Create lesson        │
│  GET     │  /lessons/{lesson_id}       │  Get lesson           │
│  PATCH   │  /lessons/{lesson_id}       │  Update lesson        │
│  DELETE  │  /lessons/{lesson_id}       │  Delete lesson        │
└──────────┴───────────────────────────────┴───────────────────────┘
```

---

## 7. Quiz System Endpoints

### Quiz Management

```
Endpoints: /api/v1/courses/{course_id}/quizzes

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                    │  Description          │
├──────────┼───────────────────────────────┼───────────────────────┤
│  GET     │  /courses/{id}/quizzes       │  List quizzes         │
│  POST    │  /courses/{id}/quizzes       │  Create quiz          │
│  GET     │  /courses/{id}/quizzes/{id}  │  Get quiz             │
│  PATCH   │  /courses/{id}/quizzes/{id}  │  Update quiz          │
│  POST    │  /courses/{id}/quizzes/{id}/publish │  Publish quiz │
└──────────┴───────────────────────────────┴───────────────────────┘
```

### Quiz Taking

```
Endpoints: /api/v1/quizzes/{quiz_id}/attempts

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                    │  Description          │
├──────────┼───────────────────────────────┼───────────────────────┤
│  POST    │  /attempts                   │  Start quiz attempt   │
│  GET     │  /attempts/start             │  Get quiz for taking  │
│  POST    │  /attempts/{id}/submit       │  Submit answers       │
│  GET     │  /attempts/{id}              │  Get attempt result   │
│  GET     │  /attempts/my-attempts       │  List my attempts     │
└──────────┴───────────────────────────────┴───────────────────────┘
```

---

## 8. Enrollment & Progress

### Enrollment Flow

```
Endpoints: /api/v1/enrollments

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                    │  Description          │
├──────────┼───────────────────────────────┼───────────────────────┤
│  POST    │  /enrollments                │  Enroll in course     │
│  GET     │  /enrollments/my-courses     │  My enrollments       │
│  GET     │  /enrollments/{id}           │  Get enrollment       │
│  PUT     │  /enrollments/{id}/lessons/{lesson_id}/progress│ Update progress │
│  POST    │  /enrollments/{id}/lessons/{lesson_id}/complete │ Mark complete │
│  POST    │  /enrollments/{id}/review     │  Submit review        │
│  GET     │  /enrollments/courses/{id}   │  Course enrollments   │
│  GET     │  /enrollments/courses/{id}/stats │  Course stats   │
└──────────┴───────────────────────────────┴───────────────────────┘
```

---

## 9. Payment Endpoints

### Payment Processing

```
Endpoints: /api/v1/payments

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                          │  Description    │
├──────────┼─────────────────────────────────────┼─────────────────┤
│  POST    │  /payments/create-payment-intent  │  Create payment │
│  POST    │  /payments/create-subscription    │  Create sub     │
│  GET     │  /payments/my-payments            │  My payments    │
│  GET     │  /payments/my-subscriptions       │  My subs        │
│  GET     │  /payments/revenue/summary       │  Revenue (admin)│
│  POST    │  /payments/webhooks/myfatoorah   │  MF webhook     │
│  POST    │  /payments/webhooks/paymob       │  Paymob webhook │
└──────────┴─────────────────────────────────────┴─────────────────┘
```

---

## 10. Analytics Endpoints

### Dashboard & Reports

```
Endpoints: /api/v1/analytics

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                        │  Description      │
├──────────┼───────────────────────────────────┼──────────────────┤
│  GET     │  /analytics/my-progress          │  My progress     │
│  GET     │  /analytics/my-dashboard          │  Student dashboard│
│  GET     │  /analytics/courses/{id}          │  Course analytics │
│  GET     │  /analytics/instructors/{id}/overview│ Instructor  │
│  GET     │  /analytics/system/overview       │  System overview │
└──────────┴───────────────────────────────────┴──────────────────┘
```

---

## 11. File Upload Endpoints

### File Management

```
Endpoints: /api/v1/files

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                    │  Description          │
├──────────┼───────────────────────────────┼───────────────────────┤
│  POST    │  /files/upload               │  Upload file          │
│  GET     │  /files/my-files             │  My files             │
│  GET     │  /files/download/{id}        │  Download file        │
└──────────┴───────────────────────────────┴───────────────────────┘
```

---

## 12. Certificate Endpoints

### Certificate Management

```
Endpoints: /api/v1/certificates

┌─────────────────────────────────────────────────────────────────┐
│  Method  │  Endpoint                        │  Description      │
├──────────┼───────────────────────────────────┼───────────────────┤
│  GET     │  /certificates/my-certificates   │  My certificates  │
│  GET     │  /certificates/{id}/download     │  Download PDF      │
│  GET     │  /certificates/verify/{number}   │  Verify cert      │
│  POST    │  /certificates/{id}/revoke        │  Revoke certificate│
│  POST    │  /certificates/enrollments/{id}/generate│ Generate  │
└──────────┴───────────────────────────────────┴───────────────────┘
```

---

## 13. API Documentation

### Available Documentation

| Endpoint | Description |
|----------|-------------|
| `/docs` | Swagger UI (interactive) |
| `/redoc` | ReDoc (alternative) |
| `/openapi.json` | OpenAPI schema (machine-readable) |

### Swagger UI Features

- Interactive API testing
- Request/response schema display
- Authentication integration
- Code generation (multiple languages)

---

## 14. Request/Response Examples

### Create Course Example

```http
POST /api/v1/courses
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "Introduction to Python",
    "description": "Learn Python from scratch",
    "category": "programming",
    "difficulty_level": "beginner",
    "estimated_duration_minutes": 1200
}
```

### Response (201 Created)

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Introduction to Python",
    "slug": "introduction-to-python",
    "description": "Learn Python from scratch",
    "category": "programming",
    "difficulty_level": "beginner",
    "is_published": false,
    "instructor_id": "660e8400-e29b-41d4-a716-446655440000",
    "estimated_duration_minutes": 1200,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### List Courses Example

```http
GET /api/v1/courses?page=1&page_size=10&category=programming&sort=-created_at
```

### Response (200 OK)

```json
{
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Introduction to Python",
            "slug": "introduction-to-python",
            "category": "programming",
            "difficulty_level": "beginner",
            "thumbnail_url": "https://...",
            "instructor": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "full_name": "John Doe"
            },
            "lessons_count": 10,
            "enrollments_count": 150,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "meta": {
        "page": 1,
        "page_size": 10,
        "total": 50,
        "total_pages": 5
    }
}
```

---

## Summary

This API design follows industry best practices:

| Principle | Implementation |
|-----------|----------------|
| RESTful | Standard HTTP methods, resource-based URLs |
| Versioned | URL-based versioning (/api/v1/) |
| Pagination | page/page_size on all list endpoints |
| Filtering | Query parameters for filters |
| Error Format | Consistent error response structure |
| Authentication | JWT Bearer tokens |
| Documentation | Auto-generated Swagger/ReDoc |

The API is designed to be intuitive, consistent, and easy to integrate with any client application.
