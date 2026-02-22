# Complete API Routes Documentation

This document provides a comprehensive reference for all API endpoints in the LMS Backend system.

---

## Table of Contents

1. Authentication Routes (/auth)
2. User Routes (/users)
3. Course Routes (/courses)
4. Lesson Routes (/lessons)
5. Enrollment Routes (/enrollments)
6. Quiz Routes (/quizzes)
7. Quiz Question Routes
8. Quiz Attempt Routes
9. Certificate Routes (/certificates)
10. File Routes (/files)
11. Analytics Routes (/analytics)
12. Health Routes

---

## 1. Authentication Routes

Base Path: /api/v1/auth

### POST /auth/register
Register a new user account.

**Request:**
```json
{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "securepassword123",
    "role": "student"
}
```

**Auth:** None required

---

### POST /auth/login
Login with email and password.

**Auth:** None required

---

### POST /auth/login/mfa
Verify MFA code during login.

**Auth:** None required

---

### POST /auth/refresh
Refresh access token.

**Auth:** None required

---

### POST /auth/logout
Logout and revoke tokens.

**Auth:** Access token required

---

### POST /auth/forgot-password
Request password reset.

**Auth:** None required

---

### POST /auth/reset-password
Reset password with token.

**Auth:** None required

---

### POST /auth/verify-email/request
Request email verification.

**Auth:** None required

---

### POST /auth/verify-email/confirm
Confirm email verification.

**Auth:** None required

---

### POST /auth/mfa/enable/request
Request MFA enablement.

**Auth:** Access token required

---

### POST /auth/mfa/enable/confirm
Confirm MFA enablement.

**Auth:** Access token required

---

### POST /auth/mfa/disable
Disable MFA.

**Auth:** Access token required

---

### GET /auth/me
Get current authenticated user.

**Auth:** Access token required

---

## 2. User Routes

Base Path: /api/v1/users

### GET /users/me
Get own profile.

**Auth:** Access token required

---

### GET /users
List all users (paginated).

**Auth:** Admin only

---

### GET /users/{user_id}
Get user by ID.

**Auth:** Admin only

---

### POST /users
Create new user.

**Auth:** Admin only

---

### PATCH /users/{user_id}
Update user.

**Auth:** Admin only

---

## 3. Course Routes

Base Path: /api/v1/courses

### GET /courses
List courses with optional filters.

**Query Parameters:**
- page (default: 1)
- page_size (default: 20)
- category (optional)
- difficulty_level (optional)
- mine (boolean)

**Auth:** Optional

---

### GET /courses/{course_id}
Get course by ID.

**Auth:** Optional

---

### POST /courses
Create new course.

**Auth:** Instructor or Admin

---

### PATCH /courses/{course_id}
Update course.

**Auth:** Course instructor or Admin

---

### POST /courses/{course_id}/publish
Publish a course.

**Auth:** Course instructor or Admin

---

### DELETE /courses/{course_id}
Delete a course.

**Auth:** Course instructor or Admin

---

## 4. Lesson Routes

### GET /courses/{course_id}/lessons
List lessons for a course.

**Auth:** Optional

---

### POST /courses/{course_id}/lessons
Create new lesson.

**Auth:** Course instructor or Admin

---

### GET /lessons/{lesson_id}
Get lesson by ID.

**Auth:** Optional

---

### PATCH /lessons/{lesson_id}
Update lesson.

**Auth:** Course instructor or Admin

---

### DELETE /lessons/{lesson_id}
Delete lesson.

**Auth:** Course instructor or Admin

---

## 5. Enrollment Routes

Base Path: /api/v1/enrollments

### POST /enrollments
Enroll in a course.

**Request:** { "course_id": "uuid" }

**Auth:** Student or Admin

---

### GET /enrollments/my-courses
List current user's enrollments.

**Auth:** Authenticated user

---

### GET /enrollments/{enrollment_id}
Get enrollment details.

**Auth:** Student (owner), Instructor, or Admin

---

### PUT /enrollments/{enrollment_id}/lessons/{lesson_id}/progress
Update lesson progress.

**Auth:** Student (owner) or Admin

---

### POST /enrollments/{enrollment_id}/lessons/{lesson_id}/complete
Mark lesson as completed.

**Auth:** Student (owner) or Admin

---

### POST /enrollments/{enrollment_id}/review
Add review to course.

**Auth:** Student (owner) - must complete 20%+

---

### GET /enrollments/courses/{course_id}
List enrollments for a course.

**Auth:** Course instructor or Admin

---

### GET /enrollments/courses/{course_id}/stats
Get enrollment statistics.

**Auth:** Course instructor or Admin

---

## 6. Quiz Routes

Base Path: /api/v1/courses/{course_id}/quizzes

### GET /quizzes
List quizzes for a course.

**Auth:** Optional

---

### GET /quizzes/{quiz_id}
Get quiz details.

**Auth:** Optional

---

### POST /quizzes
Create new quiz.

**Auth:** Course instructor or Admin

---

### PATCH /quizzes/{quiz_id}
Update quiz.

**Auth:** Course instructor or Admin

---

### POST /quizzes/{quiz_id}/publish
Publish quiz.

**Auth:** Course instructor or Admin

---

## 7. Quiz Question Routes

### GET /questions
List questions for a quiz.

**Auth:** Optional

---

### GET /questions/manage
List questions for management.

**Auth:** Course instructor or Admin

---

### POST /questions
Add question to quiz.

**Auth:** Course instructor or Admin

---

### PATCH /questions/{question_id}
Update question.

**Auth:** Course instructor or Admin

---

## 8. Quiz Attempt Routes

Base Path: /api/v1/quizzes/{quiz_id}/attempts

### POST /attempts
Start a quiz attempt.

**Auth:** Student (enrolled)

---

### GET /attempts/start
Get quiz for taking.

**Auth:** Student (enrolled)

---

### POST /attempts/{attempt_id}/submit
Submit quiz attempt.

**Auth:** Student (owner)

---

### GET /attempts/my-attempts
List own quiz attempts.

**Auth:** Student

---

### GET /attempts/{attempt_id}
Get attempt result.

**Auth:** Student (owner)

---

## 9. Certificate Routes

Base Path: /api/v1/certificates

### GET /certificates/my-certificates
List user's certificates.

**Auth:** Authenticated user

---

### GET /certificates/{certificate_id}/download
Download certificate PDF.

**Auth:** Certificate owner or Admin

---

### GET /certificates/verify/{certificate_number}
Verify certificate by number.

**Auth:** None (public verification)

---

### POST /certificates/{certificate_id}/revoke
Revoke a certificate.

**Auth:** Admin only

---

### POST /certificates/enrollments/{enrollment_id}/generate
Generate certificate.

**Auth:** Admin

---

## 10. File Routes

Base Path: /api/v1/files

### POST /files/upload
Upload a file.

**Auth:** Authenticated user

---

### GET /files/my-files
List user's uploaded files.

**Auth:** Authenticated user

---

### GET /files/download/{file_id}
Download a file.

**Auth:** File owner, public files, or Admin

---

## 11. Analytics Routes

Base Path: /api/v1/analytics

### GET /analytics/my-progress
Get current user's learning progress.

**Auth:** Authenticated user

---

### GET /analytics/my-dashboard
Get student's dashboard data.

**Auth:** Student

---

### GET /analytics/courses/{course_id}
Get course analytics.

**Auth:** Course instructor or Admin

---

### GET /analytics/instructors/{instructor_id}/overview
Get instructor overview.

**Auth:** Admin or the instructor

---

### GET /analytics/system/overview
Get system-wide analytics.

**Auth:** Admin

---

## 12. Health Routes

### GET /health
Basic health check.

**Auth:** None

---

### GET /ready
Readiness check (DB + Redis).

**Auth:** None

---

## Summary

| Module | Endpoints | Auth Required |
|--------|-----------|---------------|
| Auth | 12 | Mostly no |
| Users | 5 | Mostly Admin |
| Courses | 6 | Mixed |
| Lessons | 5 | Mixed |
| Enrollments | 8 | Mixed |
| Quizzes | 5 | Mixed |
| Questions | 4 | Mixed |
| Attempts | 5 | Student |
| Certificates | 5 | Mixed |
| Files | 3 | Yes |
| Analytics | 5 | Mixed |
| Health | 2 | No |

Total: 65+ API endpoints
