# Module Reference Guide

This document provides a comprehensive reference for all modules in the LMS Backend, explaining their purpose, components, relationships, and usage.

---

## Table of Contents

1. [Authentication Module](#authentication-module)
2. [Users Module](#users-module)
3. [Courses Module](#courses-module)
4. [Enrollments Module](#enrollments-module)
5. [Quizzes Module](#quizzes-module)
6. [Analytics Module](#analytics-module)
7. [Files Module](#files-module)
8. [Certificates Module](#certificates-module)

---

## Authentication Module

### Overview

The authentication module handles all user authentication operations including registration, login, token management, MFA, and session control. It provides secure JWT-based authentication with optional multi-factor authentication.

### Components

**models.py**:
- `RefreshToken`: Stores refresh tokens for session management

**schemas.py**:
- `UserRegistration`: User registration request
- `LoginRequest`: Login credentials
- `TokenResponse`: JWT token response
- `MFAEnableRequest`: MFA enable request
- `MFALoginRequest`: MFA login request
- `MFAChallengeResponse`: MFA challenge response

**service.py** (`AuthService`):
- `register()`: Create new user account
- `login()`: Authenticate user, check MFA
- `refresh()`: Exchange refresh token
- `logout()`: Blacklist access token
- `enable_mfa()`: Generate MFA secret
- `verify_mfa()`: Verify and enable MFA
- `disable_mfa()`: Disable MFA

**router.py**:
- `POST /auth/register`: Register new user
- `POST /auth/login`: User login
- `POST /auth/refresh`: Refresh tokens
- `POST /auth/logout`: Logout
- `POST /auth/mfa/enable`: Enable MFA
- `POST /auth/mfa/disable`: Disable MFA
- `POST /auth/mfa/verify`: Verify MFA code
- `POST /auth/mfa/login`: MFA login

### Usage Example

```python
# Registration
response = client.post("/api/v1/auth/register", json={
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
})

# Login
response = client.post("/api/v1/auth/login", json={
    "email": "user@example.com",
    "password": "SecurePass123"
})

# Use access token
headers = {"Authorization": f"Bearer {access_token}"}
```

---

## Users Module

### Overview

The users module manages user profiles and account settings. It provides endpoints for retrieving and updating user information, changing passwords, and managing account settings.

### Components

**models.py** (`User`):
- `id`: UUID primary key
- `email`: Unique email address
- `password_hash`: Bcrypt hashed password
- `full_name`: Display name
- `role`: admin/instructor/student
- `is_active`: Account status
- `mfa_enabled`: MFA configuration
- `metadata`: JSON profile data
- `created_at`, `updated_at`: Timestamps
- `last_login_at`: Last login time
- `email_verified_at`: Email verification status

**schemas.py**:
- `UserCreate`: Admin user creation
- `UserResponse`: Public user data
- `UserUpdate`: Profile update fields
- `PasswordChangeRequest`: Password change

**repository.py** (`UserRepository`):
- `create()`: Create new user
- `get_by_id()`: Find by UUID
- `get_by_email()`: Find by email
- `update()`: Modify user
- `delete()`: Remove user

**service.py** (`UserService`):
- `get_profile()`: Get current user
- `update_profile()`: Update profile
- `change_password()`: Change password

**router.py**:
- `GET /users/me`: Get profile
- `PATCH /users/me`: Update profile
- `POST /users/me/password`: Change password

### Relationships

```
User (1) ──────< (M) Course (as instructor)
User (1) ──────< (M) Enrollment (as student)
User (1) ──────< (M) RefreshToken
User (1) ──────< (M) QuizAttempt
```

---

## Courses Module

### Overview

The courses module provides comprehensive course management functionality. It supports creating courses with multiple lessons, organizing content by categories and difficulty levels, and managing publication workflows.

### Components

**models/course.py** (`Course`):
- `id`: UUID primary key
- `title`, `slug`: Course identification
- `description`: Course overview
- `instructor_id`: Foreign key to instructor
- `category`: Course category
- `difficulty_level`: beginner/intermediate/advanced
- `is_published`: Publication status
- `thumbnail_url`: Cover image
- `estimated_duration_minutes`: Duration
- `metadata`: JSON extensibility

**models/lesson.py** (`Lesson`):
- `id`: UUID primary key
- `course_id`: Foreign key to course
- `title`: Lesson title
- `content_type`: video/text/document
- `content`: Lesson content
- `video_url`: Video URL
- `duration_minutes`: Length
- `order`: Position in course

**schemas/course.py**:
- `CourseCreate`: Course creation request
- `CourseUpdate`: Course update fields
- `CourseResponse`: Full course data
- `CourseListResponse`: Paginated list

**schemas/lesson.py**:
- `LessonCreate`: Lesson creation request
- `LessonUpdate`: Lesson update fields
- `LessonResponse`: Full lesson data

**repositories**:
- `CourseRepository`: Course data access
- `LessonRepository`: Lesson data access

**services**:
- `CourseService`: Course business logic
- `LessonService`: Lesson business logic

**routers**:
- `GET /courses`: List courses
- `POST /courses`: Create course
- `GET /courses/{id}`: Get course
- `PATCH /courses/{id}`: Update course
- `POST /courses/{id}/publish`: Publish
- `DELETE /courses/{id}`: Delete course
- `GET /courses/{id}/lessons`: List lessons
- `POST /courses/{id}/lessons`: Create lesson
- `GET /lessons/{id}`: Get lesson
- `PATCH /lessons/{id}`: Update lesson
- `DELETE /lessons/{id}`: Delete lesson
- `PATCH /lessons/reorder`: Reorder lessons

### Features

- **Slug generation**: Auto-generates URL-friendly slugs
- **Publishing workflow**: Draft → Published
- **Categories**: Organize courses by category
- **Difficulty levels**: beginner/intermediate/advanced
- **Lesson ordering**: Ordered lessons within courses
- **Caching**: Redis caching for course lists

---

## Enrollments Module

### Overview

The enrollments module manages student course enrollments and progress tracking. It automatically creates lesson progress records when students enroll and tracks completion status.

### Components

**models.py**:
- `Enrollment`: Student-course relationship
  - `student_id`: Foreign key to student
  - `course_id`: Foreign key to course
  - `enrolled_at`: Enrollment timestamp
  - `completed_at`: Completion timestamp
  
- `LessonProgress`: Per-lesson progress
  - `enrollment_id`: Foreign key to enrollment
  - `lesson_id`: Foreign key to lesson
  - `completed`: Completion status
  - `completed_at`: Completion timestamp

**schemas.py**:
- `EnrollmentCreate`: Enrollment request
- `EnrollmentResponse`: Enrollment data
- `EnrollmentListResponse`: Paginated list
- `LessonProgressUpdate`: Mark complete

**repository.py** (`EnrollmentRepository`):
- `create()`: Create enrollment
- `find_by_student()`: Student's enrollments
- `find_by_course()`: Course enrollments
- `find_by_student_and_course()`: Check enrollment

**service.py** (`EnrollmentService`):
- `enroll()`: Create enrollment with progress
- `get_enrollments()`: Student's courses
- `complete_lesson()`: Mark lesson complete
- `calculate_progress()`: Completion percentage

**router.py**:
- `POST /enrollments`: Enroll in course
- `GET /enrollments/my-courses`: My enrollments
- `GET /enrollments/{id}`: Get enrollment
- `POST /enrollments/{id}/lessons/{lesson_id}/complete`: Complete lesson

### Features

- **Auto progress creation**: Creates progress for all lessons on enrollment
- **Completion tracking**: Tracks completed lessons
- **Percentage calculation**: Calculates completion percentage

---

## Quizzes Module

### Overview

The quizzes module provides a comprehensive assessment system with multiple question types, timed quizzes, randomized questions, and detailed attempt tracking with automatic scoring.

### Components

**models/quiz.py** (`Quiz`):
- `id`: UUID primary key
- `course_id`, `lesson_id`: Optional associations
- `title`, `description`: Quiz info
- `time_limit_minutes`: Time limit
- `passing_score_percentage`: Passing threshold
- `shuffle_questions`: Randomize order
- `is_published`: Availability

**models/question.py** (`QuizQuestion`):
- `id`: UUID primary key
- `quiz_id`: Foreign key to quiz
- `question_text`: The question
- `question_type`: Type (multiple_choice, true_false, etc.)
- `options`: JSON array of choices
- `correct_answer`: Correct answer
- `points`: Point value
- `order`: Position

**models/attempt.py** (`QuizAttempt`):
- `id`: UUID primary key
- `quiz_id`: Foreign key to quiz
- `student_id`: Foreign key to student
- `started_at`: Start time
- `ended_at`: End time
- `answers`: JSON responses
- `score`: Calculated score
- `passed`: Pass/fail status

**schemas/**:
- Quiz, question, and attempt schemas

**repositories**:
- `QuizRepository`: Quiz CRUD
- `QuestionRepository`: Question CRUD
- `AttemptRepository`: Attempt tracking

**services**:
- `QuizService`: Quiz management
- `QuestionService`: Question management
- `AttemptService`: Attempt handling, grading

**routers**:
- `GET /quizzes`: List quizzes
- `POST /quizzes`: Create quiz
- `GET /quizzes/{id}`: Get quiz
- `PATCH /quizzes/{id}`: Update quiz
- `DELETE /quizzes/{id}`: Delete quiz
- `GET /quizzes/{id}/questions`: List questions
- `POST /quizzes/{id}/questions`: Create question
- `POST /quizzes/{id}/attempts`: Start attempt
- `GET /attempts/{id}`: Get attempt
- `POST /attempts/{id}/submit`: Submit attempt

### Question Types

- `multiple_choice`: Single correct answer from options
- `true_false`: True or false questions
- `short_answer`: Text answer

### Features

- **Time limits**: Optional time constraints
- **Question shuffling**: Randomize question order
- **Automatic grading**: Score calculated on submission
- **Pass/fail**: Based on passing score percentage
- **Attempt tracking**: Multiple attempts allowed

---

## Analytics Module

### Overview

The analytics module provides three-tier analytics for students, instructors, and administrators. Each tier provides appropriate data access based on user role.

### Components

**schemas.py**:
- Student analytics schemas
- Instructor analytics schemas
- Course analytics schemas
- System analytics schemas

**services/**:
- `StudentAnalyticsService`: Personal progress
  - Courses enrolled/completed
  - Lessons completed
  - Quiz scores
  - Learning time
  
- `InstructorAnalyticsService`: Course metrics
  - Enrollment counts
  - Completion rates
  - Average scores
  - Student engagement
  
- `CourseAnalyticsService`: Course details
  - Enrollment trends
  - Popular lessons
  - Performance distribution
  
- `SystemAnalyticsService`: Platform metrics
  - Total users
  - Active users
  - Course counts
  - Revenue metrics

**router.py**:
- `GET /analytics/student`: Personal analytics
- `GET /analytics/instructor`: Instructor's courses
- `GET /analytics/courses/{id}/analytics`: Course analytics
- `GET /analytics/system`: Platform-wide (admin)

### Access Control

| Endpoint | Required Role |
|----------|---------------|
| /analytics/student | Any authenticated |
| /analytics/instructor | instructor, admin |
| /analytics/courses/{id}/analytics | course owner, admin |
| /analytics/system | admin |

---

## Files Module

### Overview

The files module handles file uploads and storage with support for multiple storage backends. It provides abstraction for local storage (development) and cloud storage (production).

### Components

**models.py** (`File`):
- `id`: UUID primary key
- `original_filename`: User-facing name
- `stored_filename`: UUID-based name
- `file_path`: Storage location
- `file_size`: Size in bytes
- `content_type`: MIME type
- `uploaded_by_id`: Uploader user

**storage/base.py** (`StorageBackend`):
- Abstract interface defining:
  - `upload()`: Save file
  - `download()`: Retrieve file
  - `delete()`: Remove file
  - `get_download_url()`: Generate URL

**storage/local.py** (`LocalStorageBackend`):
- Filesystem storage implementation
- Stores in configured upload directory

**storage/azure_blob.py** (`AzureBlobStorageBackend`):
- Azure Blob Storage implementation
- SAS URL generation for downloads

**service.py** (`FileService`):
- `upload()`: Handle file upload
- `get_file()`: Get metadata
- `download()`: Get file or URL
- `delete()`: Remove file

**router.py**:
- `POST /files/upload`: Upload file
- `GET /files`: List files
- `GET /files/{id}`: Get metadata
- `GET /files/{id}/download`: Download
- `DELETE /files/{id}`: Delete

### Configuration

```env
FILE_STORAGE_PROVIDER=local  # or azure
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=100
ALLOWED_UPLOAD_EXTENSIONS=mp4,avi,mov,pdf,doc,docx,jpg,jpeg,png
```

---

## Certificates Module

### Overview

The certificates module generates PDF certificates for course completions. It creates unique certificate numbers and generates formatted PDF documents.

### Components

**models.py** (`Certificate`):
- `id`: UUID primary key
- `enrollment_id`: Foreign key to enrollment
- `certificate_number`: Unique identifier
- `issued_at`: Issue date
- `pdf_path`: PDF file location

**schemas.py**:
- `CertificateGenerateRequest`: Generation request
- `CertificateResponse`: Certificate data

**service.py** (`CertificateService`):
- `generate()`: Create certificate and PDF
- `get()`: Retrieve certificate
- `verify()`: Verify by certificate number

**router.py**:
- `POST /certificates/generate`: Generate certificate
- `GET /certificates/{id}`: Get certificate
- `GET /certificates/{id}/download`: Download PDF
- `GET /certificates/my-certificates`: List certificates

### PDF Generation

The module uses FPDF2 to generate certificates with:
- Course name
- Student name
- Instructor name
- Completion date
- Unique certificate number
- Professional formatting

### Certificate Number Format

```
CERT-YYYY-NNNNNN
```

Example: `CERT-2024-001234`

---

## Module Interactions

### User Journey

1. **Registration**: User registers via Auth module
2. **Course Discovery**: User browses courses
3. **Enrollment**: User enrolls in course via Enrollments module
4. **Learning**: User views lessons in Course module
5. **Assessment**: User takes quizzes via Quizzes module
6. **Completion**: User completes all lessons
7. **Certificate**: Certificate generated via Certificates module
8. **Analytics**: User views progress via Analytics module

### Data Flow

```
Auth → Users → Courses → Enrollments → Lessons
                        ↓
                      Quizzes → Attempts
                        ↓
                    Certificates
                        ↓
                     Analytics
```

---

## Summary

The LMS Backend consists of 8 main modules:

| Module | Purpose | Key Features |
|--------|---------|--------------|
| Auth | Authentication | JWT, MFA, tokens |
| Users | Profile management | Roles, passwords |
| Courses | Course content | Lessons, publishing |
| Enrollments | Student enrollment | Progress tracking |
| Quizzes | Assessments | Questions, attempts |
| Analytics | Reporting | Three-tier views |
| Files | File storage | Multiple backends |
| Certificates | Completion | PDF generation |

Each module follows consistent architecture with models, schemas, repositories, services, and routers. Modules interact through clear interfaces and share common infrastructure for database, caching, and security.

For detailed API endpoints, see the API Reference documentation. For implementation patterns, see the Implementation Patterns guide.
