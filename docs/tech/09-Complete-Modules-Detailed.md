# Complete Module Reference Guide

This comprehensive documentation provides an exhaustive reference for all application modules in the LMS Backend. Each module is documented with its purpose, components, data models, API endpoints, and integration points.

---

## Module Architecture Overview

The LMS Backend follows a modular monolith architecture where related functionality is grouped into vertical modules. Each module follows a consistent structure:

```
module_name/
├── __init__.py
├── models.py           # SQLAlchemy ORM models
├── schemas.py          # Pydantic request/response schemas
├── repository.py       # Data access layer
├── service.py          # Business logic
├── router.py           # API route handlers
└── (additional files as needed)
```

This pattern promotes separation of concerns, testability, and maintainability. Each layer has clear responsibilities and can be tested independently.

---

## Authentication Module (app/modules/auth/)

### Purpose

The authentication module handles all identity and access management including user registration, login, token management, password reset, email verification, and optional multi-factor authentication. This is the security foundation of the entire application.

### Components

**models.py**: User model with authentication fields:
- email, password_hash
- role (admin, instructor, student)
- is_active, email_verified_at
- mfa_secret (optional)
- failed_login_attempts, locked_until
- password_reset_token, password_reset_expires

**schemas.py**: Request/response validation:
- UserCreate: Registration input
- UserLogin: Authentication credentials
- TokenResponse: JWT tokens
- PasswordResetRequest/Confirm: Password reset flow
- EmailVerificationRequest/Confirm: Email verification flow

**service.py**: Business logic:
- register_user(): Create new user account
- authenticate_user(): Validate credentials
- create_access_token(): Generate JWT
- create_refresh_token(): Generate refresh token
- verify_password(): Password validation
- initiate_password_reset(): Start password reset
- verify_email(): Complete email verification

**router.py**: API endpoints:
- POST /auth/register: Create account
- POST /auth/login: Authenticate
- POST /auth/logout: Invalidate tokens
- POST /auth/refresh: Exchange refresh token
- POST /auth/password-reset-request: Request reset
- POST /auth/password-reset-confirm: Complete reset
- POST /auth/email-verification-request: Request verification
- POST /auth/email-verification-confirm: Complete verification

### Security Features

- JWT tokens with short-lived access (15 min) and long-lived refresh (30 days)
- Bcrypt password hashing with salt
- Account lockout after failed attempts
- Token blacklist for logout
- Optional MFA support

---

## Users Module (app/modules/users/)

### Purpose

The users module manages user profiles and administrative user management. It provides profile viewing and updates for regular users and full user CRUD operations for administrators.

### Components

**models.py**: Extended user profile:
- Inherits from auth User
- Adds: full_name, avatar_url, bio, created_at, updated_at

**schemas.py**: Profile and admin schemas:
- UserResponse: User profile view
- UserUpdate: Profile update input
- UserAdminCreate: Admin user creation
- UserListResponse: Paginated user list

**repository.py**: User data access:
- get_by_email(): Find by email
- get_by_id(): Find by UUID
- create(): New user
- update(): Modify user
- delete(): Soft delete (set is_active=false)
- list_with_pagination(): Paginated listing

**service.py**: Business logic:
- update_profile(): User profile update
- admin_create_user(): Admin user creation
- admin_update_user(): Admin user modification
- admin_list_users(): User listing with filters

**router.py**: API endpoints:
- GET /users/me: Current user profile
- PUT /users/me: Update own profile
- GET /users: List all users (admin)
- POST /users: Create user (admin)
- GET /users/{id}: Get user (admin)
- PUT /users/{id}: Update user (admin)
- DELETE /users/{id}: Delete user (admin)

---

## Courses Module (app/modules/courses/)

### Purpose

The courses module is the core content management system. It handles course creation and lifecycle, lesson management, and course publishing. This module distinguishes between published courses (visible to students) and draft courses (visible only to instructors).

### Components

**models.py**: 
- Course: title, slug, description, instructor_id, category, difficulty_level, thumbnail_url, estimated_duration_minutes, is_published
- Lesson: course_id, title, slug, content, lesson_type (video/text/quiz), duration_minutes, order_index, video_url, is_preview

**schemas.py**:
- CourseCreate, CourseUpdate, CourseResponse
- LessonCreate, LessonUpdate, LessonResponse

**repositories**:
- CourseRepository: Course CRUD, search, filtering
- LessonRepository: Lesson CRUD, ordering

**services**:
- CourseService: Course lifecycle, enrollment counting
- LessonService: Lesson management, completion tracking

**routers**:
- course_router.py: Course endpoints
- lesson_router.py: Lesson endpoints

**API Endpoints**:
- GET /courses: List published courses
- GET /courses/{id}: Course details
- POST /courses: Create course
- PUT /courses/{id}: Update course
- DELETE /courses/{id}: Delete course
- GET /courses/{id}/lessons: List lessons
- POST /courses/{id}/lessons: Create lesson
- PUT /courses/{id}/lessons/{lesson_id}: Update lesson
- DELETE /courses/{id}/lessons/{lesson_id}: Delete lesson

---

## Enrollments Module (app/modules/enrollments/)

### Purpose

The enrollments module tracks student participation in courses. It manages the enrollment lifecycle, progress tracking, and completion detection. This module bridges students and courses, recording engagement metrics.

### Components

**models.py**: Enrollment with progress:
- course_id, student_id
- status (active, completed, dropped)
- enrolled_at, completed_at
- progress_percent

**schemas.py**:
- EnrollmentCreate: Student enrollment request
- EnrollmentResponse: Enrollment details
- EnrollmentProgress: Progress details

**repository.py**:
- get_by_student(): Student's enrollments
- get_by_course(): Course enrollments
- get_by_student_and_course(): Specific enrollment

**service.py**:
- enroll(): Create enrollment
- mark_lesson_completed(): Update progress
- check_completion(): Detect course completion
- calculate_progress(): Compute progress percentage

**router.py**: API endpoints:
- GET /enrollments: List user's enrollments
- POST /enrollments: Enroll in course
- GET /enrollments/{id}: Enrollment details
- POST /enrollments/{id}/lessons/{lesson_id}/complete: Mark complete

---

## Quizzes Module (app/modules/quizzes/)

### Purpose

The quizzes module provides assessment capabilities including quiz creation, question management, attempt tracking, and automatic grading. It supports multiple question types and configurable quiz behavior.

### Components

**models**:
- Quiz: lesson_id, title, description, quiz_type (practice/graded), passing_score, time_limit_minutes, max_attempts, shuffle_questions, shuffle_options, show_correct_answers, is_published
- Question: quiz_id, question_text, question_type (multiple_choice/true_false/short_answer), points, options (JSON), correct_answer, explanation, order_index
- Attempt: quiz_id, enrollment_id, attempt_number, status (in_progress/submitted/graded), score, started_at, submitted_at, graded_at, answers (JSON)

**schemas**:
- QuizCreate, QuizUpdate, QuizResponse
- QuestionCreate, QuestionUpdate, QuestionResponse
- AttemptStart, AttemptSubmit, AttemptResponse

**repositories**:
- QuizRepository: Quiz CRUD
- QuestionRepository: Question CRUD
- AttemptRepository: Attempt tracking

**services**:
- QuizService: Quiz management
- QuestionService: Question handling
- AttemptService: Attempt lifecycle, grading

**routers**:
- quiz_router.py: Quiz CRUD
- question_router.py: Question management
- attempt_router.py: Attempt handling

**API Endpoints**:
- GET /courses/{id}/lessons/{lesson_id}/quiz: Get quiz
- POST /quizzes/{id}/attempts: Start attempt
- GET /quizzes/{id}/attempts/{attempt_id}: Get attempt
- PUT /quizzes/{id}/attempts/{attempt_id}: Submit attempt

---

## Assignments Module (app/modules/assignments/)

### Purpose

The assignments module handles student assignments and instructor grading. Unlike quizzes (which are automated), assignments allow free-form submissions and manual grading by instructors.

### Components

**models.py**:
- Assignment: course_id, lesson_id (optional), title, description, due_date, max_points
- Submission: assignment_id, student_id, submitted_at, content, grade, feedback, graded_at, graded_by

**schemas.py**:
- AssignmentCreate, AssignmentUpdate, AssignmentResponse
- SubmissionCreate, SubmissionGrade, SubmissionResponse

**repositories.py**: Assignment and Submission CRUD

**services.py**: Assignment and grading logic

**routers.py**: API endpoints for CRUD and grading

---

## Certificates Module (app/modules/certificates/)

### Purpose

The certificates module automatically generates PDF certificates when students complete courses. Certificates include course name, student name, completion date, and a unique certificate number for verification.

### Components

**models.py**:
- Certificate: enrollment_id, certificate_number (unique), pdf_path, issued_at, is_revoked, revoked_at, revoked_reason

**schemas.py**:
- CertificateResponse: Certificate details
- CertificateVerify: Verification request

**service.py**:
- check_eligibility(): Verify completion requirements
- generate_certificate(): Create PDF certificate
- verify_certificate(): Check validity
- revoke_certificate(): Invalidate certificate

**router.py**: API endpoints:
- GET /certificates: List user's certificates
- GET /certificates/{id}: Certificate details
- GET /certificates/{id}/download: Download PDF
- GET /certificates/verify/{number}: Verify certificate

---

## Files Module (app/modules/files/)

### Purpose

The files module handles file uploads for course materials, assignments, and user avatars. It supports both local storage and Azure Blob Storage backends.

### Components

**models.py**:
- File: original_filename, stored_filename, file_path, file_size, mime_type, uploaded_by_id, course_id, lesson_id, created_at

**schemas.py**:
- FileUploadResponse: Upload confirmation
- FileListResponse: Paginated file list

**router.py**: API endpoints:
- POST /files/upload: Upload file
- GET /files: List files
- GET /files/{id}/download: Download file
- DELETE /files/{id}: Delete file

**Storage Backends**:
- Local: Files stored in uploads/ directory
- Azure: Files stored in Azure Blob Storage

---

## Analytics Module (app/modules/analytics/)

### Purpose

The analytics module provides dashboards and reporting for students, instructors, and administrators. It aggregates data to provide insights into learning progress, course performance, and system usage.

### Components

**schemas.py**: Response schemas for various analytics views

**services**:
- StudentAnalyticsService: Student dashboard data
- InstructorAnalyticsService: Course analytics
- CourseAnalyticsService: Per-course metrics
- SystemAnalyticsService: System-wide metrics

**router.py**: API endpoints:
- GET /analytics/student: Student dashboard
- GET /analytics/courses/{id}: Course analytics
- GET /analytics/instructor: Instructor overview
- GET /analytics/system: Admin system stats

**Metrics Provided**:
- Enrollment counts and trends
- Completion rates
- Quiz performance
- User activity
- System health

---

## Module Integration Points

### Authentication Flow

1. User registers → auth module creates user
2. User logs in → auth module validates and issues tokens
3. Token used for all authenticated requests
4. Dependencies extract user from token
5. Authorization checks use user's role

### Course Enrollment Flow

1. Student views course → courses module returns published course
2. Student enrolls → enrollments module creates enrollment
3. Student completes lessons → enrollments module tracks progress
4. Course completed → certificates module generates certificate

### Quiz Flow

1. Instructor creates quiz → quizzes module creates quiz with questions
2. Student starts attempt → attempt service creates attempt record
3. Student submits answers → attempt service grades automatically
4. Score calculated → results returned to student

### File Upload Flow

1. Instructor uploads material → files module stores file
2. File associated with course/lesson
3. Students enrolled can download → files module serves file

---

## Module Dependencies

```
auth
  ↓
users ← auth (for user data)
courses ← users (instructor reference)
  ↓
enrollments ← courses, users
  ↓
quizzes ← courses, enrollments
certificates ← enrollments
assignments ← courses, enrollments
files ← courses, users
analytics ← all modules (for aggregation)
```

---

## Module Testing Strategy

Each module has corresponding tests in tests/:
- test_auth.py: Authentication tests
- test_courses.py: Course tests
- test_quizzes.py: Quiz tests
- test_certificates.py: Certificate tests
- test_assignments.py: Assignment tests
- test_assignments_grading.py: Grading tests
- test_analytics.py: Analytics tests

Tests follow the module structure and test each layer (repository, service, router).

---

## Adding New Modules

To add a new module:

1. Create directory: app/modules/new_module/
2. Create __init__.py
3. Add models.py with SQLAlchemy models
4. Add schemas.py with Pydantic models
5. Add repository.py for data access
6. Add service.py for business logic
7. Add router.py for API endpoints
8. Register router in app/api/v1/api.py
9. Add tests in tests/test_new_module.py

---

This comprehensive module reference provides complete documentation of all application components. Each module is designed for independence while integrating seamlessly through shared patterns and dependencies.
