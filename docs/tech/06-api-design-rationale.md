# API Design Rationale

This document explains the API design patterns, REST conventions, response formats, and the reasoning behind each decision.

---

## Table of Contents

1. [API Structure](#1-api-structure)
2. [RESTful Conventions](#2-restful-conventions)
3. [Endpoint Design](#3-endpoint-design)
4. [Request/Response Formats](#4-requestresponse-formats)
5. [Error Handling](#5-error-handling)
6. [Pagination](#6-pagination)
7. [Filtering and Sorting](#7-filtering-and-sorting)
8. [Versioning](#8-versioning)
9. [Authentication Endpoints](#9-authentication-endpoints)
10. [API Design Examples](#10-api-design-examples)

---

## 1. API Structure

### Base URL

```
https://api.example.com/api/v1/
```

### URL Structure

```
/api/v1/{resource}/{id}/{sub-resource}
```

### Available Resources

| Resource | Endpoints |
|----------|-----------|
| `auth` | Authentication (login, register, refresh) |
| `users` | User management |
| `courses` | Courses and lessons |
| `enrollments` | Student enrollments |
| `quizzes` | Quiz management |
| `analytics` | Reporting and analytics |
| `files` | File uploads |
| `certificates` | Certificate management |

---

## 2. RESTful Conventions

### HTTP Methods

| Method | Usage | Example |
|--------|-------|---------|
| `GET` | Retrieve resources | `GET /courses` |
| `POST` | Create new resources | `POST /courses` |
| `PATCH` | Partial update | `PATCH /courses/{id}` |
| `PUT` | Full replacement | `PUT /courses/{id}` |
| `DELETE` | Remove resources | `DELETE /courses/{id}` |

### Resource Naming

```python
# Use plural nouns for collections
/courses          # NOT /course
/users            # NOT /user
/enrollments      # NOT /enrollment

# Use kebab-case for multi-word resources
/course-categories   # Avoid: courseCategories
/user-profiles       # Avoid: userProfiles
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| `200` | Success (GET, PATCH, PUT) |
| `201` | Created (POST) |
| `204` | No Content (DELETE) |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `422` | Validation Error |
| `429` | Too Many Requests |
| `500` | Internal Server Error |

---

## 3. Endpoint Design

### Course Endpoints

```
# Courses
GET    /courses                     # List courses
POST   /courses                     # Create course
GET    /courses/{course_id}         # Get course details
PATCH  /courses/{course_id}         # Update course
DELETE /courses/{course_id}         # Delete course
POST   /courses/{course_id}/publish # Publish course

# Lessons (nested under course)
GET    /courses/{course_id}/lessons                    # List lessons
POST   /courses/{course_id}/lessons                    # Create lesson
GET    /courses/{course_id}/lessons/{lesson_id}        # Get lesson
PATCH  /courses/{course_id}/lessons/{lesson_id}        # Update lesson
DELETE /courses/{course_id}/lessons/{lesson_id}        # Delete lesson
```

### Why Nested Endpoints?

| Approach | Example | When to Use |
|----------|---------|-------------|
| Nested | `/courses/{id}/lessons` | Child belongs to parent |
| Flat | `/lessons?course_id={id}` | Independent resources |

**Decision:** Use nested endpoints when:
- Child cannot exist without parent
- Operations are always in context of parent
- Authorization depends on parent

---

### Enrollment Endpoints

```
# Enrollments
POST   /enrollments                                    # Enroll in course
GET    /enrollments/my-courses                         # My enrollments
GET    /enrollments/{enrollment_id}                   # Get enrollment
PUT    /enrollments/{enrollment_id}/lessons/{lesson_id}/progress  # Update progress
POST   /enrollments/{enrollment_id}/lessons/{lesson_id}/complete   # Mark complete
POST   /enrollments/{enrollment_id}/review            # Add review

# Course enrollments
GET    /enrollments/courses/{course_id}                # Course enrollments
GET    /enrollments/courses/{course_id}/stats         # Enrollment stats
```

### Quiz Endpoints

```
# Quizzes
GET    /courses/{course_id}/quizzes                    # List quizzes
POST   /courses/{course_id}/quizzes                    # Create quiz
GET    /courses/{course_id}/quizzes/{quiz_id}          # Get quiz
PATCH  /courses/{course_id}/quizzes/{quiz_id}         # Update quiz
POST   /courses/{course_id}/quizzes/{quiz_id}/publish  # Publish quiz

# Questions
GET    /courses/{course_id}/quizzes/{quiz_id}/questions             # List questions
POST   /courses/{course_id}/quizzes/{quiz_id}/questions              # Create question
GET    /courses/{course_id}/quizzes/{quiz_id}/questions/{question_id} # Get question
PATCH  /courses/{course_id}/quizzes/{quiz_id}/questions/{question_id} # Update question
DELETE /courses/{course_id}/quizzes/{quiz_id}/questions/{question_id} # Delete question

# Attempts
GET    /enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts        # List attempts
POST   /enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts       # Start attempt
GET    /enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts/{attempt_id} # Get attempt
POST   /enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts/{attempt_id}/submit # Submit attempt
```

---

## 4. Request/Response Formats

### Request: Create Course

```json
POST /api/v1/courses
{
  "title": "Introduction to Python",
  "description": "Learn Python from scratch",
  "category": "programming",
  "difficulty_level": "beginner",
  "estimated_duration_minutes": 120
}
```

### Response: Course Created (201)

```json
POST /api/v1/courses
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Introduction to Python",
    "slug": "introduction-to-python",
    "description": "Learn Python from scratch",
    "category": "programming",
    "difficulty_level": "beginner",
    "estimated_duration_minutes": 120,
    "is_published": false,
    "instructor_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "Course created successfully"
}
```

### Response: Course List (200)

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Introduction to Python",
      "slug": "introduction-to-python",
      "thumbnail_url": "https://...",
      "category": "programming",
      "difficulty_level": "beginner",
      "estimated_duration_minutes": 120,
      "is_published": true,
      "instructor": {
        "id": "...",
        "full_name": "John Doe"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### Response Wrapper Pattern

```python
class APIResponse(BaseModel):
    success: bool
    data: Any = None
    message: str | None = None

class PaginatedResponse(BaseModel):
    success: bool = True
    data: List[Any]
    pagination: PaginationInfo
```

**Why wrapper pattern?**
- Consistent response format
- Easy to add metadata
- Clear success/error states

---

## 5. Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Permission denied |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

### Validation Errors

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "title",
        "message": "Title is required"
      },
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

---

## 6. Pagination

### Request Parameters

```
GET /api/v1/courses?page=1&page_size=20&sort=created_at&order=desc
```

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `page` | 1 | - | Page number |
| `page_size` | 20 | 100 | Items per page |
| `sort` | created_at | - | Sort field |
| `order` | desc | - | Sort order (asc/desc) |

### Paginated Response

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Implementation

```python
async def paginate(query, page: int = 1, page_size: int = 20):
    # Get total count
    total = await query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    return {
        "items": await query.all(),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": page * page_size < total,
        "has_prev": page > 1
    }
```

---

## 7. Filtering and Sorting

### Filter Parameters

```
GET /api/v1/courses?category=programming&difficulty=beginner&is_published=true
```

### Filter Patterns

| Pattern | Example | Description |
|---------|---------|-------------|
| Exact match | `is_published=true` | Boolean filter |
| Category | `category=programming` | Single value |
| Search | `search=python` | Text search |
| Date range | `created_after=2024-01-01` | Date filtering |

### Sort Parameters

```
GET /api/v1/courses?sort=title&order=asc
GET /api/v1/courses?sort=created_at&order=desc
```

---

## 8. Versioning

### URL Versioning

```
/api/v1/courses
/api/v2/courses  # Future versions
```

### Why URL Versioning?

| Method | Example | Pros | Cons |
|--------|---------|------|------|
| URL Path | `/api/v1/...` | Explicit, easy to route | URL changes |
| Header | `Accept: v1` | Cleaner URLs | Complex client |
| Query | `/courses?version=1` | No URL change | Caching issues |

**Decision:** URL path versioning
- Clear and explicit
- Easy to implement
- Visible in documentation

---

## 9. Authentication Endpoints

### Registration

```
POST /api/v1/auth/register

Request:
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "role": "student"  // optional, defaults to student
}

Response (201):
{
  "success": true,
  "data": {
    "id": "...",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "student"
  },
  "message": "Registration successful"
}
```

### Login

```
POST /api/v1/auth/login

Request:
{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response (200):
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

### Token Refresh

```
POST /api/v1/auth/refresh

Request:
{
  "refresh_token": "eyJ..."
}

Response (200):
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

### Logout

```
POST /api/v1/auth/logout

Headers:
Authorization: Bearer <access_token>

Response (200):
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 10. API Design Examples

### Example 1: Create Resource

```python
@router.post("/courses", response_model=CourseResponse, status_code=201)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_COURSE)),
    course_service: CourseService = Depends(get_course_service)
):
    # Validate permissions
    if current_user.role not in [Role.ADMIN, Role.INSTRUCTOR]:
        raise ForbiddenError("Only instructors can create courses")
    
    # Create course
    course = await course_service.create(
        course_data=course_data,
        instructor_id=current_user.id
    )
    
    return CourseResponse.model_validate(course)
```

### Example 2: List Resources with Filters

```python
@router.get("/courses", response_model=PaginatedCourseList)
async def list_courses(
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    difficulty: str | None = None,
    search: str | None = None,
    is_published: bool = True,
    course_service: CourseService = Depends(get_course_service)
):
    # Build filters
    filters = CourseFilters(
        category=category,
        difficulty=difficulty,
        search=search,
        is_published=is_published
    )
    
    # Get paginated results
    result = await course_service.list_courses(
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    return result
```

### Example 3: Nested Resource

```python
@router.get("/courses/{course_id}/lessons", response_model=PaginatedLessonList)
async def list_lessons(
    course_id: UUID,
    page: int = 1,
    page_size: int = 50,
    course_service: CourseService = Depends(get_course_service)
):
    # Verify course exists
    course = await course_service.get_by_id(course_id)
    if not course:
        raise NotFoundError("Course", course_id)
    
    # Get lessons
    lessons = await course_service.get_lessons(
        course_id=course_id,
        page=page,
        page_size=page_size
    )
    
    return lessons
```

### Example 4: Action Endpoint

```python
@router.post("/courses/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: UUID,
    current_user: User = Depends(require_permission(Permission.UPDATE_COURSE)),
    course_service: CourseService = Depends(get_course_service)
):
    # Get course
    course = await course_service.get_by_id(course_id)
    if not course:
        raise NotFoundError("Course", course_id)
    
    # Verify ownership
    if course.instructor_id != current_user.id and current_user.role != Role.ADMIN:
        raise ForbiddenError("You don't own this course")
    
    # Publish
    course = await course_service.publish(course_id)
    
    return CourseResponse.model_validate(course)
```

---

## Summary

| Design Decision | Implementation |
|-----------------|----------------|
| **Versioning** | URL path: `/api/v1/` |
| **Response Format** | Wrapped: `{success, data, message}` |
| **Error Format** | `{success, error: {code, message, details}}` |
| **Pagination** | Page/page_size with metadata |
| **Filtering** | Query parameters |
| **Sorting** | sort/order parameters |
| **Authentication** | JWT Bearer tokens |
| **Authorization** | Role-based with permissions |

This API design provides:
- **Consistency** - Standard patterns across all endpoints
- **Developer Experience** - Clear, predictable URLs
- **Documentation** - Auto-generated from code
- **Scalability** - Pagination and filtering for large datasets
