# Complete API Routes Reference

This comprehensive reference documents every API endpoint in the LMS Backend. Each endpoint is described with its path, HTTP method, request parameters, request body, response format, authentication requirements, and authorization rules. This documentation serves as the complete API reference for frontend developers, API consumers, and anyone integrating with the LMS Backend.

---

## Authentication Endpoints (app/modules/auth/)

The authentication module provides comprehensive identity management including registration, login, logout, token refresh, password management, and optional multi-factor authentication.

### POST /api/v1/auth/register

**Description**: Register a new user account in the system. The endpoint validates email format and password strength. If public registration is disabled (ALLOW_PUBLIC_ROLE_REGISTRATION=false), only admin users can create accounts through the admin interface.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "User Full Name",
  "role": "student"
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "User Full Name",
  "role": "student",
  "is_active": true,
  "email_verified_at": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Authentication**: Not required

**Authorization**: Public when registration is enabled; otherwise admin only

**Validation Rules**:
- Email must be valid format and unique
- Password must meet minimum strength requirements
- Role must be one of: admin, instructor, student
- Full name is required with 1-200 characters

---

### POST /api/v1/auth/login

**Description**: Authenticate user and receive access and refresh tokens. Supports regular password authentication and optional MFA challenge. The endpoint rate limits authentication attempts to prevent brute force attacks.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Authentication**: Not required

**Authorization**: None

**Error Responses**:
- 401 Unauthorized: Invalid credentials
- 423 Locked: Account locked due to failed attempts

---

### POST /api/v1/auth/logout

**Description**: Invalidate the current access token by adding it to the blacklist. This ensures the token cannot be used after logout. Both access and refresh tokens should be invalidated.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200 OK)**:
```json
{
  "message": "Successfully logged out"
}
```

**Authentication**: Required (Bearer token)

**Authorization**: Authenticated user

---

### POST /api/v1/auth/refresh

**Description**: Exchange a valid refresh token for a new access token. This enables session extension without re-authentication. Refresh tokens have longer expiration (30 days) than access tokens (15 minutes).

**Request Body**:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Authentication**: Not required (refresh token provides authentication)

**Authorization**: None

---

### POST /api/v1/auth/password-reset-request

**Description**: Request a password reset email. The endpoint sends an email with a reset link to the user's registered email address. This initiates the password reset flow.

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK)**:
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

**Authentication**: Not required

**Security Note**: Always returns success to prevent email enumeration attacks

---

### POST /api/v1/auth/password-reset-confirm

**Description**: Confirm password reset with the token from email. The endpoint validates the token and updates the user's password. Tokens expire after 30 minutes.

**Request Body**:
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePassword123"
}
```

**Response (200 OK)**:
```json
{
  "message": "Password has been reset successfully"
}
```

**Authentication**: Not required (token provides authentication)

---

### POST /api/v1/auth/email-verification-request

**Description**: Request email verification email. Users must verify their email before accessing certain features when REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN is enabled.

**Response (200 OK)**:
```json
{
  "message": "Verification email sent"
}
```

**Authentication**: Required

**Authorization**: Authenticated user

---

### POST /api/v1/auth/email-verification-confirm

**Description**: Confirm email verification with token from email.

**Request Body**:
```json
{
  "token": "verification-token-from-email"
}
```

**Response (200 OK)**:
```json
{
  "message": "Email verified successfully"
}
```

**Authentication**: Not required (token provides authentication)

---

### POST /api/v1/auth/login/mfa

**Description**: Complete MFA challenge after initial login. Users with MFA enabled must provide the MFA code after password verification.

**Request Body**:
```json
{
  "mfa_token": "mfa-challenge-token",
  "mfa_code": "123456"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Authentication**: Required (MFA token from login response)

---

## User Endpoints (app/modules/users/)

### GET /api/v1/users/me

**Description**: Get current user profile information. Returns the authenticated user's profile data.

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "User Full Name",
  "role": "student",
  "avatar_url": "https://...",
  "bio": "User bio",
  "is_active": true,
  "email_verified_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Authentication**: Required

**Authorization**: Authenticated user (own profile)

---

### PUT /api/v1/users/me

**Description**: Update current user profile. Users can update their full_name, avatar_url, and bio. Email changes may require re-verification.

**Request Body**:
```json
{
  "full_name": "Updated Name",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Updated bio"
}
```

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Updated Name",
  "role": "student",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Updated bio",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

**Authentication**: Required

**Authorization**: Authenticated user (own profile)

---

### GET /api/v1/users

**Description**: List all users (admin only). Returns paginated list of users with filtering options.

**Query Parameters**:
- page: Page number (default: 1)
- page_size: Items per page (default: 20, max: 100)
- role: Filter by role (admin, instructor, student)
- is_active: Filter by active status
- search: Search by email or full_name

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "User Name",
      "role": "student",
      "is_active": true,
      "created_at": "2024-01-10T08:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

**Authentication**: Required

**Authorization**: Admin only

---

### POST /api/v1/users

**Description**: Create a new user (admin only). Admin users can create users of any role.

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "full_name": "New User",
  "role": "instructor"
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "full_name": "New User",
  "role": "instructor",
  "is_active": true,
  "created_at": "2024-01-15T14:00:00Z"
}
```

**Authentication**: Required

**Authorization**: Admin only

---

### GET /api/v1/users/{user_id}

**Description**: Get user by ID (admin only).

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "User Name",
  "role": "student",
  "is_active": true,
  "email_verified_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Authentication**: Required

**Authorization**: Admin only

---

### PUT /api/v1/users/{user_id}

**Description**: Update user (admin only). Admin can update any user including role and active status.

**Request Body**:
```json
{
  "full_name": "Updated Name",
  "role": "instructor",
  "is_active": false
}
```

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Updated Name",
  "role": "instructor",
  "is_active": false,
  "updated_at": "2024-01-15T15:00:00Z"
}
```

**Authentication**: Required

**Authorization**: Admin only

---

### DELETE /api/v1/users/{user_id}

**Description**: Delete user (admin only). Soft delete sets is_active to false.

**Response (200 OK)**:
```json
{
  "message": "User deleted successfully"
}
```

**Authentication**: Required

**Authorization**: Admin only

---

## Course Endpoints (app/modules/courses/)

### GET /api/v1/courses

**Description**: List published courses. Returns courses that are published and visible to students. Supports filtering by category and difficulty level.

**Query Parameters**:
- page: Page number
- page_size: Items per page
- category: Filter by category
- difficulty_level: Filter by difficulty (beginner, intermediate, advanced)
- search: Search in title and description

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Python Basics",
      "slug": "python-basics",
      "description": "Learn Python from scratch",
      "thumbnail_url": "https://...",
      "instructor_id": "uuid",
      "instructor_name": "Instructor Name",
      "category": "Programming",
      "difficulty_level": "beginner",
      "estimated_duration_minutes": 120,
      "is_published": true,
      "enrollment_count": 50,
      "rating": 4.5,
      "created_at": "2024-01-10T08:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

**Authentication**: Not required

---

### GET /api/v1/courses/{course_id}

**Description**: Get course details. Returns full course information including lessons list. Preview lessons are visible to unauthenticated users.

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "title": "Python Basics",
  "slug": "python-basics",
  "description": "Learn Python from scratch",
  "thumbnail_url": "https://...",
  "instructor_id": "uuid",
  "instructor_name": "Instructor Name",
  "category": "Programming",
  "difficulty_level": "beginner",
  "estimated_duration_minutes": 120,
  "is_published": true,
  "enrollment_count": 50,
  "rating": 4.5,
  "lessons": [
    {
      "id": "uuid",
      "title": "Introduction",
      "slug": "introduction",
      "lesson_type": "video",
      "duration_minutes": 15,
      "order_index": 1,
      "is_preview": true
    }
  ],
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Authentication**: Not required for published courses

---

### POST /api/v1/courses

**Description**: Create a new course. Only instructors and admins can create courses.

**Request Body**:
```json
{
  "title": "Python for Beginners",
  "slug": "python-for-beginners",
  "description": "A comprehensive Python course",
  "category": "Programming",
  "difficulty_level": "beginner",
  "estimated_duration_minutes": 180,
  "thumbnail_url": "https://..."
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "title": "Python for Beginners",
  "slug": "python-for-beginners",
  "description": "A comprehensive Python course",
  "instructor_id": "uuid",
  "category": "Programming",
  "difficulty_level": "beginner",
  "is_published": false,
  "created_at": "2024-01-15T14:00:00Z"
}
```

**Authentication**: Required

**Authorization**: Instructor or Admin

---

### PUT /api/v1/courses/{course_id}

**Description**: Update course. Only the course instructor or admin can update.

**Request Body**:
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "is_published": true
}
```

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "title": "Updated Title",
  "description": "Updated description",
  "is_published": true,
  "updated_at": "2024-01-15T15:00:00Z"
}
```

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

### DELETE /api/v1/courses/{course_id}

**Description**: Delete course. Only the course instructor or admin can delete. Deleting a course also deletes all related lessons, enrollments, and quiz data.

**Response (200 OK)**:
```json
{
  "message": "Course deleted successfully"
}
```

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

## Lesson Endpoints (app/modules/courses/)

### GET /api/v1/courses/{course_id}/lessons

**Description**: List all lessons in a course. Returns lessons in order with metadata.

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Introduction",
      "slug": "introduction",
      "description": "Course introduction",
      "lesson_type": "video",
      "content": "Video content URL",
      "duration_minutes": 15,
      "order_index": 1,
      "is_preview": true,
      "video_url": "https://..."
    }
  ]
}
```

**Authentication**: Not required for published courses

---

### GET /api/v1/courses/{course_id}/lessons/{lesson_id}

**Description**: Get lesson details including content. Preview lessons are accessible to everyone. Full content requires enrollment.

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "course_id": "uuid",
  "title": "Introduction",
  "slug": "introduction",
  "description": "Course introduction",
  "lesson_type": "video",
  "content": "Full lesson content",
  "duration_minutes": 15,
  "order_index": 1,
  "is_preview": true,
  "video_url": "https://...",
  "is_completed": true
}
```

**Authentication**: Required for full content

**Authorization**: Enrolled student for non-preview lessons

---

### POST /api/v1/courses/{course_id}/lessons

**Description**: Create a new lesson. Only course instructor or admin can add lessons.

**Request Body**:
```json
{
  "title": "New Lesson",
  "slug": "new-lesson",
  "description": "Lesson description",
  "lesson_type": "video",
  "content": "Lesson content",
  "duration_minutes": 20,
  "is_preview": false,
  "video_url": "https://..."
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "course_id": "uuid",
  "title": "New Lesson",
  "slug": "new-lesson",
  "lesson_type": "video",
  "order_index": 3,
  "created_at": "2024-01-15T14:00:00Z"
}
```

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

### PUT /api/v1/courses/{course_id}/lessons/{lesson_id}

**Description**: Update lesson. Only course instructor or admin can update.

**Request Body**:
```json
{
  "title": "Updated Lesson Title",
  "content": "Updated content",
  "is_preview": true
}
```

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

### DELETE /api/v1/courses/{course_id}/lessons/{lesson_id}

**Description**: Delete lesson. Only course instructor or admin can delete.

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

## Enrollment Endpoints (app/modules/enrollments/)

### GET /api/v1/enrollments

**Description**: List user's enrollments. Returns courses the authenticated user is enrolled in.

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "course_id": "uuid",
      "course_title": "Python Basics",
      "student_id": "uuid",
      "status": "active",
      "progress_percent": 45,
      "enrolled_at": "2024-01-10T08:00:00Z",
      "completed_at": null
    }
  ]
}
```

**Authentication**: Required

**Authorization**: Authenticated user (own enrollments)

---

### POST /api/v1/enrollments

**Description**: Enroll in a course. Students can enroll in published courses.

**Request Body**:
```json
{
  "course_id": "uuid"
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "course_id": "uuid",
  "student_id": "uuid",
  "status": "active",
  "progress_percent": 0,
  "enrolled_at": "2024-01-15T14:00:00Z"
}
```

**Authentication**: Required

**Authorization**: Student role

---

### GET /api/v1/enrollments/{enrollment_id}

**Description**: Get enrollment details including progress through lessons.

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "course_id": "uuid",
  "course_title": "Python Basics",
  "student_id": "uuid",
  "student_name": "Student Name",
  "status": "active",
  "progress_percent": 45,
  "completed_lessons": 5,
  "total_lessons": 10,
  "lessons": [
    {
      "lesson_id": "uuid",
      "title": "Lesson 1",
      "is_completed": true,
      "completed_at": "2024-01-12T10:00:00Z"
    }
  ],
  "enrolled_at": "2024-01-10T08:00:00Z",
  "completed_at": null
}
```

**Authentication**: Required

**Authorization**: Enrollment owner, course instructor, or admin

---

### POST /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/complete

**Description**: Mark a lesson as completed. Updates enrollment progress and triggers certificate check if course is completed.

**Response (200 OK)**:
```json
{
  "message": "Lesson marked as completed",
  "progress_percent": 50,
  "course_completed": false
}
```

**Authentication**: Required

**Authorization**: Enrollment owner

---

### POST /api/v1/enrollments/{enrollment_id}/complete

**Description**: Manually mark enrollment as completed (admin/instructor only). Used for offline course completions or credit awards.

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

## Quiz Endpoints (app/modules/quizzes/)

### GET /api/v1/courses/{course_id}/lessons/{lesson_id}/quiz

**Description**: Get quiz for a lesson. Returns quiz configuration and questions (based on quiz settings).

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "lesson_id": "uuid",
  "title": "Course Quiz",
  "description": "Test your knowledge",
  "quiz_type": "graded",
  "passing_score": 70,
  "time_limit_minutes": 20,
  "max_attempts": 3,
  "shuffle_questions": true,
  "shuffle_options": true,
  "show_correct_answers": true,
  "questions": [
    {
      "id": "uuid",
      "question_text": "What is Python?",
      "question_type": "multiple_choice",
      "points": 10,
      "options": [
        {"option_id": "1", "option_text": "A programming language"}
      ]
    }
  ]
}
```

**Authentication**: Required (enrolled student)

---

### POST /api/v1/quizzes/{quiz_id}/attempts

**Description**: Start a new quiz attempt. Creates an attempt record and starts the timer if timed quiz.

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "quiz_id": "uuid",
  "enrollment_id": "uuid",
  "attempt_number": 1,
  "status": "in_progress",
  "started_at": "2024-01-15T14:00:00Z",
  "time_remaining_seconds": 1200
}
```

**Authentication**: Required

**Authorization**: Enrolled student who hasn't exceeded max attempts

---

### GET /api/v1/quizzes/{quiz_id}/attempts/{attempt_id}

**Description**: Get attempt details. Returns current state of attempt including answered questions.

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "quiz_id": "uuid",
  "enrollment_id": "uuid",
  "attempt_number": 1,
  "status": "in_progress",
  "score": null,
  "started_at": "2024-01-15T14:00:00Z",
  "time_remaining_seconds": 900,
  "answers": [
    {
      "question_id": "uuid",
      "selected_option_id": "1"
    }
  ]
}
```

**Authentication**: Required

**Authorization**: Attempt owner

---

### PUT /api/v1/quizzes/{quiz_id}/attempts/{attempt_id}

**Description**: Submit quiz attempt. Grades the attempt and returns results.

**Request Body**:
```json
{
  "answers": [
    {
      "question_id": "uuid",
      "selected_option_id": "1"
    },
    {
      "question_id": "uuid-2",
      "answer_text": "Python"
    }
  ]
}
```

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "quiz_id": "uuid",
  "status": "graded",
  "score": 85,
  "passed": true,
  "total_points": 100,
  "earned_points": 85,
  "submitted_at": "2024-01-15T14:30:00Z",
  "graded_at": "2024-01-15T14:30:05Z",
  "results": [
    {
      "question_id": "uuid",
      "question_text": "What is Python?",
      "correct": true,
      "points_earned": 10,
      "points_possible": 10,
      "explanation": "Python is a programming language"
    }
  ]
}
```

**Authentication**: Required

**Authorization**: Attempt owner

---

### GET /api/v1/quizzes/{quiz_id}/attempts

**Description**: List all attempts for a quiz. Students see their own attempts; instructors see all attempts.

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "attempt_number": 1,
      "status": "graded",
      "score": 85,
      "passed": true,
      "started_at": "2024-01-15T14:00:00Z",
      "submitted_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

**Authentication**: Required

**Authorization**: Attempt owner or course instructor/admin

---

## Quiz Management Endpoints (Instructor/Admin)

### POST /api/v1/courses/{course_id}/lessons/{lesson_id}/quiz

**Description**: Create a quiz for a lesson.

**Request Body**:
```json
{
  "title": "Chapter 1 Quiz",
  "description": "Test your understanding",
  "quiz_type": "graded",
  "passing_score": 70,
  "time_limit_minutes": 30,
  "max_attempts": 3,
  "shuffle_questions": true,
  "shuffle_options": true,
  "show_correct_answers": false,
  "is_published": false
}
```

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

### POST /api/v1/quizzes/{quiz_id}/questions

**Description**: Add a question to a quiz.

**Request Body**:
```json
{
  "question_text": "What is Python?",
  "question_type": "multiple_choice",
  "points": 10,
  "explanation": "Python is a high-level programming language",
  "options": [
    {"option_text": "A programming language", "is_correct": true},
    {"option_text": "A snake", "is_correct": false},
    {"option_text": "A database", "is_correct": false}
  ]
}
```

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

## Certificate Endpoints (app/modules/certificates/)

### GET /api/v1/certificates

**Description**: List user's certificates. Returns all certificates earned by the authenticated user.

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "enrollment_id": "uuid",
      "course_title": "Python Basics",
      "certificate_number": "CERT-20240115-ABC123",
      "issued_at": "2024-01-15T14:00:00Z",
      "is_revoked": false,
      "download_url": "/api/v1/certificates/uuid/download"
    }
  ]
}
```

**Authentication**: Required

---

### GET /api/v1/certificates/{certificate_id}

**Description**: Get certificate details.

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "enrollment_id": "uuid",
  "student_id": "uuid",
  "student_name": "Student Name",
  "course_title": "Python Basics",
  "course_completed_at": "2024-01-15T13:00:00Z",
  "certificate_number": "CERT-20240115-ABC123",
  "issued_at": "2024-01-15T14:00:00Z",
  "is_revoked": false,
  "download_url": "/api/v1/certificates/uuid/download"
}
```

**Authentication**: Required

**Authorization**: Certificate owner, course instructor, or admin

---

### GET /api/v1/certificates/{certificate_id}/download

**Description**: Download certificate PDF.

**Response (200 OK)**: PDF file download

**Authentication**: Required

**Authorization**: Certificate owner, course instructor, or admin

---

### GET /api/v1/certificates/verify/{certificate_number}

**Description**: Verify certificate authenticity. Public endpoint for anyone to verify certificates.

**Response (200 OK)**:
```json
{
  "valid": true,
  "certificate_number": "CERT-20240115-ABC123",
  "student_name": "Student Name",
  "course_title": "Python Basics",
  "issued_at": "2024-01-15T14:00:00Z",
  "is_revoked": false
}
```

**Authentication**: Not required

---

## File Endpoints (app/modules/files/)

### POST /api/v1/files/upload

**Description**: Upload a file. Supports course materials, assignments, and other uploads.

**Request**: multipart/form-data
- file: File content
- course_id: (optional) Associated course
- lesson_id: (optional) Associated lesson

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "original_filename": "document.pdf",
  "stored_filename": "abc123.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "upload_url": "/api/v1/files/uuid/download"
}
```

**Authentication**: Required

**Authorization**: Instructor or Admin for course materials

---

### GET /api/v1/files

**Description**: List uploaded files. Supports filtering by course or lesson.

**Query Parameters**:
- course_id: Filter by course
- lesson_id: Filter by lesson
- page, page_size: Pagination

**Authentication**: Required

---

### GET /api/v1/files/{file_id}/download

**Description**: Download a file.

**Response**: File download

**Authentication**: Required

**Authorization**: Enrollment owner for course materials, or instructor/admin

---

### DELETE /api/v1/files/{file_id}

**Description**: Delete a file.

**Authentication**: Required

**Authorization**: File owner or Admin

---

## Analytics Endpoints (app/modules/analytics/)

### GET /api/v1/analytics/student

**Description**: Student dashboard analytics. Returns enrolled courses, progress, recent activity.

**Response (200 OK)**:
```json
{
  "enrolled_courses": 3,
  "completed_courses": 1,
  "in_progress_courses": 2,
  "total_quiz_attempts": 10,
  "average_quiz_score": 82,
  "recent_activity": [
    {
      "type": "lesson_completed",
      "course_title": "Python Basics",
      "lesson_title": "Functions",
      "timestamp": "2024-01-15T14:00:00Z"
    }
  ]
}
```

**Authentication**: Required

**Authorization**: Student role

---

### GET /api/v1/analytics/courses/{course_id}

**Description**: Course analytics for instructors. Returns enrollment stats, completion rates, quiz performance.

**Response (200 OK)**:
```json
{
  "course_id": "uuid",
  "title": "Python Basics",
  "total_enrollments": 50,
  "active_enrollments": 45,
  "completed_enrollments": 20,
  "completion_rate": 40,
  "average_progress": 65,
  "average_quiz_score": 78,
  "lesson_completion_rates": [
    {"lesson_id": "uuid", "title": "Intro", "completion_rate": 95},
    {"lesson_id": "uuid-2", "title": "Advanced", "completion_rate": 45}
  ]
}
```

**Authentication**: Required

**Authorization**: Course instructor or Admin

---

### GET /api/v1/analytics/instructor

**Description**: Instructor analytics across all their courses.

**Response (200 OK)**:
```json
{
  "total_courses": 5,
  "published_courses": 3,
  "total_students": 150,
  "total_enrollments": 200,
  "completion_rate": 45,
  "average_rating": 4.3,
  "courses": [
    {
      "course_id": "uuid",
      "title": "Python Basics",
      "enrollments": 50,
      "completion_rate": 40,
      "rating": 4.5
    }
  ]
}
```

**Authentication**: Required

**Authorization**: Instructor role

---

### GET /api/v1/analytics/system

**Description**: System-wide analytics (admin only).

**Response (200 OK)**:
```json
{
  "total_users": 500,
  "active_users_30d": 200,
  "total_courses": 50,
  "published_courses": 40,
  "total_enrollments": 1000,
  "completion_rate": 35,
  "system_health": {
    "database": "healthy",
    "redis": "healthy",
    "api": "healthy"
  }
}
```

**Authentication**: Required

**Authorization**: Admin only

---

## Health Check Endpoints

### GET /api/v1/health

**Description**: Basic health check. Returns OK if application is running.

**Response (200 OK)**:
```json
{
  "status": "ok"
}
```

**Authentication**: Not required

---

### GET /api/v1/ready

**Description**: Readiness check. Verifies database and Redis connectivity.

**Response (200 OK)**:
```json
{
  "status": "ok",
  "database": "up",
  "redis": "up"
}
```

**Response (503 Service Unavailable)**:
```json
{
  "status": "degraded",
  "database": "up",
  "redis": "down"
}
```

**Authentication**: Not required

---

## Error Response Formats

All error responses follow a consistent format:

**Validation Error (422)**:
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

**Authentication Error (401)**:
```json
{
  "detail": "Could not validate credentials"
}
```

**Authorization Error (403)**:
```json
{
  "detail": "Not enough permissions"
}
```

**Not Found Error (404)**:
```json
{
  "detail": "Resource not found"
}
```

---

This API reference provides complete documentation for all endpoints in the LMS Backend. For implementation details, refer to the router files in each module directory.
