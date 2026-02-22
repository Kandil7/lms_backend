# Complete LMS Backend Project Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Architecture Decisions](#architecture-decisions)
5. [Module-by-Module Documentation](#module-by-module-documentation)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Security Implementation](#security-implementation)
9. [Background Jobs and Celery](#background-jobs-and-celery)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Guide](#deployment-guide)
12. [How to Build the Project](#how-to-build-the-project)

---

## Project Overview

The LMS Backend is a comprehensive Learning Management System built with modern web technologies. It provides a complete platform for creating and managing educational content, including course management, student enrollments, quizzes and assessments, progress tracking, certificates, and analytics.

### Key Features

This backend system implements a full-featured Learning Management System with the following capabilities:

- **User Management**: Role-based access control with three user roles (admin, instructor, student), secure authentication with JWT tokens, and optional Multi-Factor Authentication (MFA) for enhanced security.
- **Course Management**: Complete CRUD operations for courses with categories, difficulty levels, and publishing workflows. Support for lessons with multiple content types including videos and documents.
- **Enrollment System**: Students can enroll in courses, track their progress through lessons, and receive completion certificates upon finishing.
- **Quiz System**: Comprehensive quiz functionality with multiple question types, timed quizzes, random question ordering, and detailed attempt tracking with scoring.
- **Analytics**: Three levels of analytics for students, instructors, and administrators to track learning progress, course performance, and system usage.
- **File Management**: Secure file upload and storage with support for multiple storage backends (local and Azure Blob Storage).
- **Certificate Generation**: Automated PDF certificate generation for course completions.
- **Observability**: Built-in metrics, logging, health checks, and integration with Sentry for error tracking.

---

## Technology Stack

### Core Framework

The project uses FastAPI as the primary web framework, chosen for its exceptional performance, automatic API documentation with Swagger UI, native support for asynchronous programming, and excellent type validation through Pydantic models.

```python
# requirements.txt - Core dependencies
fastapi>=0.115.0,<1.0.0
uvicorn[standard]>=0.34.0,<1.0.0
```

### Database Layer

PostgreSQL serves as the primary relational database, providing robust ACID compliance, excellent JSON support for flexible metadata storage, and superior performance for complex queries. SQLAlchemy ORM handles database operations with Alembic for migrations.

```python
sqlalchemy>=2.0.36,<3.0.0
alembic>=1.14.0,<2.0.0
psycopg2-binary>=2.9.10,<3.0.0
```

### Caching and Sessions

Redis provides high-performance caching for frequently accessed data and serves as the message broker for background tasks. It also handles rate limiting and token blacklisting.

```python
redis>=5.2.1,<6.0.0
```

### Background Processing

Celery handles asynchronous task processing with Redis as the broker. This enables email sending, certificate generation, progress updates, and webhook delivery without blocking the main API.

```python
celery>=5.4.0,<6.0.0
```

### Security

The project implements comprehensive security with JWT tokens (python-jose), password hashing (passlib with bcrypt), and comprehensive input validation (pydantic-settings).

```python
python-jose[cryptography]>=3.3.0,<4.0.0
passlib[bcrypt]>=1.7.4,<2.0.0
pydantic-settings>=2.7.1,<3.0.0
```

### Observability

Sentry provides error tracking and performance monitoring, while Prometheus client exposes metrics for monitoring systems.

```python
sentry-sdk[fastapi]>=2.18.0,<3.0.0
prometheus-client>=0.20.0,<1.0.0
```

### Additional Libraries

Azure Blob Storage SDK handles cloud file storage, Jinja2 templates are used for email content, and FPDF2 generates PDF certificates.

```python
azure-storage-blob>=12.26.0,<13.0.0
jinja2>=3.1.5,<4.0.0
fpdf2>=2.8.2,<3.0.0
```

### Testing

Pytest serves as the testing framework with plugins for async support, coverage reporting, and fake data generation.

```python
pytest>=8.3.4,<9.0.0
pytest-asyncio>=0.25.0,<1.0.0
pytest-cov>=6.0.0,<7.0.0
faker>=33.1.0,<34.0.0
```

---

## Project Structure

The project follows a modular monolith architecture with clear separation of concerns. The directory structure is organized as follows:

```
lms_backend/
├── app/                          # Main application package
│   ├── __init__.py              # App initialization
│   ├── main.py                  # FastAPI application entry point
│   ├── api/                     # API routing layer
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── api.py           # Main API router with health checks
│   ├── core/                    # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py            # Settings and configuration
│   │   ├── secrets.py           # Secrets management
│   │   ├── database.py          # Database connection and session management
│   │   ├── security.py          # JWT and password handling
│   │   ├── permissions.py        # Role-based access control
│   │   ├── cache.py             # Redis caching layer
│   │   ├── exceptions.py        # Custom exception handling
│   │   ├── dependencies.py      # FastAPI dependency injection
│   │   ├── health.py            # Health check utilities
│   │   ├── metrics.py           # Prometheus metrics
│   │   ├── observability.py     # Sentry integration
│   │   ├── model_registry.py    # SQLAlchemy model loading
│   │   ├── webhooks.py         # Webhook delivery system
│   │   └── middleware/          # Custom middleware
│   │       ├── __init__.py
│   │       ├── rate_limit.py    # Rate limiting
│   │       ├── security_headers.py
│   │       ├── request_logging.py
│   │       └── response_envelope.py
│   ├── modules/                 # Feature modules (vertical slices)
│   │   ├── auth/               # Authentication module
│   │   ├── users/              # User management module
│   │   ├── courses/            # Course management module
│   │   ├── enrollments/        # Enrollment module
│   │   ├── quizzes/            # Quiz and assessment module
│   │   ├── analytics/          # Analytics module
│   │   ├── files/              # File management module
│   │   └── certificates/       # Certificate generation module
│   ├── tasks/                   # Celery background tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py       # Celery configuration
│   │   ├── dispatcher.py      # Task dispatching utilities
│   │   ├── email_tasks.py      # Email sending tasks
│   │   ├── certificate_tasks.py
│   │   ├── progress_tasks.py
│   │   └── webhook_tasks.py
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       ├── pagination.py        # Pagination helpers
│       ├── constants.py        # Application constants
│       └── validators.py       # Custom validators
├── alembic/                     # Database migrations
│   ├── env.py
│   └── versions/
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_auth.py
│   ├── test_courses.py
│   ├── test_quizzes.py
│   ├── test_enrollments.py
│   ├── test_analytics.py
│   ├── test_certificates.py
│   ├── test_files.py
│   ├── test_permissions.py
│   ├── test_rate_limit_rules.py
│   ├── test_response_envelope.py
│   ├── test_webhooks.py
│   ├── test_secrets.py
│   ├── test_health.py
│   └── perf/
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── postman/                      # Postman collections
├── uploads/                      # Uploaded files directory
├── certificates/                # Generated certificates
├── docker-compose.yml           # Docker Compose for development
├── docker-compose.prod.yml     # Docker Compose for production
├── docker-compose.staging.yml
├── docker-compose.observability.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## Architecture Decisions

### Modular Monolith Architecture

The project follows a modular monolith architecture, which represents the best of both worlds between microservices and monolithic applications. Each feature is implemented as a self-contained vertical slice (module) with its own routes, services, repositories, models, and schemas.

**Why this approach?** This architecture provides clear boundaries between features, making the codebase easier to understand and maintain. It allows for independent development of features while keeping deployment simple as a single unit. The modular structure also facilitates future migration to microservices if needed, as each module can be extracted into its own service.

### Layered Architecture

Within each module, the code follows a layered architecture pattern:

1. **Router Layer**: Handles HTTP requests and responses, performs input validation using Pydantic schemas, and delegates business logic to services.
2. **Service Layer**: Contains business logic, orchestrates operations across repositories, and enforces business rules.
3. **Repository Layer**: Handles database operations, implements data access patterns, and manages SQLAlchemy queries.
4. **Model Layer**: Defines SQLAlchemy ORM models that map to database tables.

**Why this approach?** This separation ensures that business logic is centralized in services, making it easier to test and maintain. Routers remain thin and focused on HTTP concerns, while repositories abstract database complexity.

### Repository Pattern

The repository pattern abstracts database operations behind service interfaces. Each repository class handles all database interactions for a specific model.

**Why this approach?** This provides a clean separation between business logic and data access, making it easier to switch database implementations or add caching without affecting the service layer. It also facilitates unit testing by allowing mock repositories.

### Dependency Injection

FastAPI's dependency injection system is used extensively throughout the application. Dependencies are declared in function parameters and automatically resolved by the framework.

**Why this approach?** This approach promotes loose coupling, makes code more testable by allowing easy mocking of dependencies, and provides a clean way to manage shared resources like database sessions and current user context.

### API-First Design

All API endpoints follow RESTful conventions with proper HTTP methods, status codes, and response envelopes. The API uses Pydantic models for both request validation and response serialization.

**Why this approach?** This ensures consistent API behavior, automatic request/response documentation, and catches validation errors early at the API boundary.

### Background Task Processing

Long-running operations such as sending emails, generating certificates, and delivering webhooks are processed asynchronously using Celery with Redis as the message broker.

**Why this approach?** This prevents blocking the main API thread for time-consuming operations, improves response times for clients, and provides reliability through task retry mechanisms.

---

## Module-by-Module Documentation

### 1. Authentication Module (app/modules/auth/)

The authentication module handles all user authentication operations including registration, login, token refresh, logout, and MFA management.

#### Files

**models.py**
- `RefreshToken`: Stores refresh tokens for session management with automatic expiration tracking.

**schemas.py**
- `UserRegistration`: Pydantic schema for user registration with email, password, and full name validation.
- `LoginRequest`: Schema for login credentials.
- `TokenResponse`: Schema for JWT token responses with access and refresh tokens.
- `MFAEnableRequest`: Schema for enabling MFA with validation code.
- `MFALoginRequest`: Schema for MFA-protected login.

**service.py**
- `AuthService`: Main service class providing registration, login, token management, MFA operations, and logout functionality. Implements password hashing, JWT token creation/validation, and token blacklisting.

**router.py**
- Defines all authentication endpoints: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/mfa/enable`, `/auth/mfa/disable`, `/auth/mfa/login`.

#### Design Decisions

The authentication module uses JWT tokens with short-lived access tokens (15 minutes) and long-lived refresh tokens (30 days). This balances security with usability. Access tokens are blacklisted on logout to enable immediate session termination. MFA support uses time-based one-time passwords (TOTP) for enhanced security.

---

### 2. Users Module (app/modules/users/)

The users module manages user profiles and account settings.

#### Files

**models.py**
- `User`: Main user model with email, password hash, full name, role (admin, instructor, student), MFA settings, profile metadata, and timestamps.

**schemas.py**
- `UserCreate`: Schema for creating new users.
- `UserResponse`: Schema for user data in responses (excludes sensitive data).
- `UserUpdate`: Schema for updating user profile.
- `PasswordChangeRequest`: Schema for password change.

**repositories/user_repository.py**
- `UserRepository`: Database operations for users including create, read, update, delete, and find by email.

**services/user_service.py**
- `UserService`: Business logic for user management including profile updates, password changes, and role management.

**router.py**
- Endpoints for user operations: `/users/me` (get current user), `/users/me` (update profile), `/users/me/password`.

---

### 3. Courses Module (app/modules/courses/)

The courses module provides complete course management functionality with lessons, categories, and publishing workflows.

#### Files

**models/course.py**
- `Course`: Course model with title, slug, description, instructor relationship, category, difficulty level, published status, thumbnail, duration, and metadata.

**models/lesson.py**
- `Lesson`: Lesson model with course relationship, title, content type, video URL, content text, duration, order, and metadata.

**schemas/course.py**
- `CourseCreate`, `CourseUpdate`, `CourseResponse`, `CourseListResponse`: Pydantic schemas for course operations.

**schemas/lesson.py**
- `LessonCreate`, `LessonUpdate`, `LessonResponse`, `LessonListResponse`: Pydantic schemas for lesson operations.

**repositories/course_repository.py**
- `CourseRepository`: Database operations for courses including filtering by category, difficulty, instructor, and published status.

**repositories/lesson_repository.py**
- `LessonRepository`: Database operations for lessons including ordering and course filtering.

**services/course_service.py**
- `CourseService`: Business logic for course CRUD, publishing workflow, slug generation, and caching.

**services/lesson_service.py**
- `LessonService`: Business logic for lesson management and ordering.

**routers/course_router.py**
- Endpoints: `GET /courses`, `POST /courses`, `GET /courses/{id}`, `PATCH /courses/{id}`, `POST /courses/{id}/publish`, `DELETE /courses/{id}`.

**routers/lesson_router.py**
- Endpoints: `GET /courses/{course_id}/lessons`, `POST /courses/{course_id}/lessons`, `GET /lessons/{id}`, `PATCH /lessons/{id}`, `DELETE /lessons/{id}`, `PATCH /lessons/reorder`.

#### Design Decisions

Courses use a slug field for SEO-friendly URLs that is unique across the system. The publishing workflow allows instructors to draft courses before making them visible. Caching is implemented at both the course list and individual course level with automatic cache invalidation on updates.

---

### 4. Enrollments Module (app/modules/enrollments/)

The enrollments module manages student course enrollments and progress tracking.

#### Files

**models.py**
- `Enrollment`: Enrollment model linking students to courses with enrollment date and completion status.
- `LessonProgress`: Tracks individual lesson completion status for each student.

**schemas.py**
- `EnrollmentCreate`, `EnrollmentResponse`, `EnrollmentListResponse`: Schemas for enrollment operations.
- `LessonProgressResponse`, `LessonProgressUpdate`: Schemas for progress tracking.

**repository.py**
- `EnrollmentRepository`: Database operations for enrollments and progress queries.

**service.py**
- `EnrollmentService`: Business logic for enrolling in courses, completing lessons, calculating completion percentages, and checking enrollment status.

**router.py**
- Endpoints: `POST /enrollments`, `GET /enrollments/my-courses`, `GET /enrollments/{id}`, `POST /enrollments/{id}/lessons/{lesson_id}/complete`.

#### Design Decisions

Enrollment automatically creates lesson progress records for all lessons in a course. Progress tracking is at the lesson level, allowing students to resume from where they left off. Completion is calculated based on finished lessons rather than time spent.

---

### 5. Quizzes Module (app/modules/quizzes/)

The quizzes module provides comprehensive assessment functionality with questions, quizzes, and attempt tracking.

#### Files

**models/quiz.py**
- `Quiz`: Quiz model with course/lesson relationship, title, description, time limit, passing score, shuffle questions flag, and metadata.

**models/question.py**
- `QuizQuestion`: Question model with quiz relationship, question text, question type (multiple choice, true/false, etc.), options as JSON, correct answer, points, and order.

**models/attempt.py**
- `QuizAttempt`: Attempt model tracking student quiz attempts with answers, score, start/end times, and completion status.

**schemas/quiz.py**
- `QuizCreate`, `QuizUpdate`, `QuizResponse`, `QuizListResponse`: Schemas for quiz operations.

**schemas/question.py**
- `QuestionCreate`, `QuestionUpdate`, `QuestionResponse`: Schemas for question operations.

**schemas/attempt.py**
- `AttemptStart`, `AttemptSubmit`, `AttemptResponse`, `AttemptResult`: Schemas for quiz attempts.

**repositories/quiz_repository.py**
- `QuizRepository`: Database operations for quizzes.

**repositories/question_repository.py**
- `QuestionRepository`: Database operations for questions including ordering.

**repositories/attempt_repository.py**
- `AttemptRepository`: Database operations for quiz attempts including scoring.

**services/quiz_service.py**
- `QuizService`: Business logic for quiz management, validation, and scoring.

**services/question_service.py**
- `QuestionService`: Business logic for question management.

**services/attempt_service.py**
- `AttemptService`: Business logic for starting, submitting, and grading quiz attempts with automatic timeout handling.

**routers/quiz_router.py**
- Endpoints: `GET /quizzes`, `POST /quizzes`, `GET /quizzes/{id}`, `PATCH /quizzes/{id}`, `DELETE /quizzes/{id}`.

**routers/question_router.py**
- Endpoints: `GET /quizzes/{quiz_id}/questions`, `POST /quizzes/{quiz_id}/questions`, etc.

**routers/attempt_router.py**
- Endpoints: `POST /quizzes/{quiz_id}/attempts`, `GET /attempts/{attempt_id}`, `POST /attempts/{attempt_id}/submit`.

#### Design Decisions

Questions are stored with all options and correct answers, allowing for flexible question types. Attempts capture all answers for later review. Time limits are enforced both client-side and server-side. Shuffle questions option randomizes question order per attempt to prevent cheating.

---

### 6. Analytics Module (app/modules/analytics/)

The analytics module provides three levels of analytics for students, instructors, and administrators.

#### Files

**schemas.py**
- Schemas for analytics responses including student progress, course statistics, and system metrics.

**services/student_analytics_service.py**
- `StudentAnalyticsService`: Individual student progress, completed courses, quiz scores, time spent learning.

**services/instructor_analytics_service.py**
- `InstructorAnalyticsService`: Course enrollment statistics, average progress, quiz performance by course, student engagement metrics.

**services/course_analytics_service.py**
- `CourseAnalyticsService`: Detailed course analytics including enrollment trends, completion rates, popular lessons.

**services/system_analytics_service.py**
- `SystemAnalyticsService`: System-wide metrics including total users, active users, course count, revenue metrics.

**router.py**
- Endpoints: `GET /analytics/student`, `GET /analytics/instructor`, `GET /analytics/courses/{id}/analytics`, `GET /analytics/system`.

#### Design Decisions

Analytics are computed in real-time from the database to ensure accuracy. Different service classes handle different authorization levels to ensure data privacy. Caching is used for expensive aggregate queries.

---

### 7. Files Module (app/modules/files/)

The files module handles file uploads and storage with support for multiple storage backends.

#### Files

**models.py**
- `File`: File metadata model with original filename, storage path, file size, content type, and uploader relationship.

**schemas.py**
- `FileUploadResponse`, `FileListResponse`: Schemas for file operations.

**storage/base.py**
- `StorageBackend`: Abstract base class defining the storage interface.

**storage/local.py**
- `LocalStorageBackend`: Local filesystem storage implementation.

**storage/azure_blob.py**
- `AzureBlobStorageBackend`: Azure Blob Storage implementation for production.

**service.py**
- `FileService`: Business logic for file uploads, downloads, and deletion with storage backend abstraction.

**router.py**
- Endpoints: `POST /files/upload`, `GET /files`, `GET /files/{id}`, `GET /files/{id}/download`, `DELETE /files/{id}`.

#### Design Decisions

The storage backend is abstracted to allow easy switching between local storage (development) and cloud storage (production). Files are stored with UUID names to prevent filename conflicts. Download URLs are signed with expiration for security.

---

### 8. Certificates Module (app/modules/certificates/)

The certificates module generates PDF certificates for course completions.

#### Files

**models.py**
- `Certificate`: Certificate model linking to enrollment, with certificate number, issue date, and PDF path.

**schemas.py**
- `CertificateResponse`, `CertificateGenerateRequest`: Schemas for certificate operations.

**service.py**
- `CertificateService`: Business logic for certificate generation with PDF creation using FPDF2.

**router.py**
- Endpoints: `POST /certificates/generate`, `GET /certificates/{id}`, `GET /certificates/{id}/download`, `GET /certificates/my-certificates`.

#### Design Decisions

Certificates are generated as PDF documents with customizable templates. Each certificate has a unique certificate number for verification. The PDF generation is handled asynchronously via Celery to avoid blocking API responses.

---

## Database Schema

### Entity Relationship Diagram

The database consists of the following main entities with relationships:

```
User (1) ──────< (M) Course
User (1) ──────< (M) Enrollment
User (1) ──────< (M) RefreshToken
Course (1) ────< (M) Lesson
Course (1) ────< (M) Enrollment
Course (1) ────< (M) Quiz
Course (1) ────< (M) Certificate
Lesson (1) ────< (M) LessonProgress
Enrollment (1) ─< (M) LessonProgress
Enrollment (1) ─< (1) Certificate
Quiz (1) ──────< (M) QuizQuestion
Quiz (1) ──────< (M) QuizAttempt
QuizAttempt (M)>─< (M) QuizQuestion (through answers)
User (1) ──────< (M) QuizAttempt
Lesson (1) ────< (M) Quiz
File (1) ──────< (M) Course (as thumbnail)
```

### Detailed Schema

**users**: Core user table with role-based access (admin, instructor, student), MFA settings, and email verification status.

**courses**: Course content with instructor relationship, category, difficulty level, published status, and JSON metadata for extensibility.

**lessons**: Individual lessons within courses with ordering, content types (video, text), and duration tracking.

**enrollments**: Student-course relationships with enrollment timestamps and completion tracking.

**lesson_progress**: Per-student lesson completion status with timestamps.

**quizzes**: Quiz configurations with time limits, passing scores, and shuffle options.

**quiz_questions**: Question bank with multiple question types, point values, and ordering.

**quiz_attempts**: Student quiz attempts with answers, scores, and timing information.

**certificates**: Generated certificates linked to completed enrollments.

**refresh_tokens**: Token management for session continuation.

---

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/auth/register | Register new user | No |
| POST | /api/v1/auth/login | User login | No |
| POST | /api/v1/auth/refresh | Refresh access token | No |
| POST | /api/v1/auth/logout | User logout | Yes |
| POST | /api/v1/auth/mfa/enable | Enable MFA | Yes |
| POST | /api/v1/auth/mfa/disable | Disable MFA | Yes |
| POST | /api/v1/auth/mfa/login | MFA challenge verification | No |

### User Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/v1/users/me | Get current user | Yes |
| PATCH | /api/v1/users/me | Update current user | Yes |
| POST | /api/v1/users/me/password | Change password | Yes |

### Course Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/v1/courses | List courses | No |
| POST | /api/v1/courses | Create course | Yes (Instructor/Admin) |
| GET | /api/v1/courses/{id} | Get course | No |
| PATCH | /api/v1/courses/{id} | Update course | Yes (Owner/Admin) |
| POST | /api/v1/courses/{id}/publish | Publish course | Yes (Owner/Admin) |
| DELETE | /api/v1/courses/{id} | Delete course | Yes (Owner/Admin) |

### Lesson Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/v1/courses/{id}/lessons | List lessons | No |
| POST | /api/v1/courses/{id}/lessons | Create lesson | Yes (Owner/Admin) |
| GET | /api/v1/lessons/{id} | Get lesson | No |
| PATCH | /api/v1/lessons/{id} | Update lesson | Yes (Owner/Admin) |
| DELETE | /api/v1/lessons/{id} | Delete lesson | Yes (Owner/Admin) |

### Enrollment Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/enrollments | Enroll in course | Yes |
| GET | /api/v1/enrollments/my-courses | My enrollments | Yes |
| GET | /api/v1/enrollments/{id} | Get enrollment | Yes |
| POST | /api/v1/enrollments/{id}/lessons/{lesson_id}/complete | Complete lesson | Yes |

### Quiz Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/v1/quizzes | List quizzes | No |
| POST | /api/v1/quizzes | Create quiz | Yes (Instructor/Admin) |
| GET | /api/v1/quizzes/{id} | Get quiz | No |
| PATCH | /api/v1/quizzes/{id} | Update quiz | Yes |
| DELETE | /api/v1/quizzes/{id} | Delete quiz | Yes |

### Quiz Attempt Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/quizzes/{id}/attempts | Start attempt | Yes |
| GET | /api/v1/attempts/{id} | Get attempt | Yes |
| POST | /api/v1/attempts/{id}/submit | Submit attempt | Yes |

### Analytics Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/v1/analytics/student | Student analytics | Yes |
| GET | /api/v1/analytics/instructor | Instructor analytics | Yes (Instructor/Admin) |
| GET | /api/v1/analytics/courses/{id}/analytics | Course analytics | Yes (Owner/Admin) |
| GET | /api/v1/analytics/system | System analytics | Yes (Admin) |

### File Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/files/upload | Upload file | Yes |
| GET | /api/v1/files | List files | Yes |
| GET | /api/v1/files/{id} | Get file metadata | Yes |
| GET | /api/v1/files/{id}/download | Download file | Yes |
| DELETE | /api/v1/files/{id} | Delete file | Yes |

### Certificate Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/certificates/generate | Generate certificate | Yes |
| GET | /api/v1/certificates/{id} | Get certificate | Yes |
| GET | /api/v1/certificates/{id}/download | Download certificate | Yes |
| GET | /api/v1/certificates/my-certificates | My certificates | Yes |

---

## Security Implementation

### Authentication

The system uses JWT (JSON Web Tokens) for stateless authentication. Each request includes an Authorization header with a Bearer token. Tokens contain the user ID, role, and unique token identifier (jti) for blacklisting.

**Token Types**:
- Access tokens: 15-minute expiration for API access
- Refresh tokens: 30-day expiration for session continuation
- Password reset tokens: 30-minute expiration
- Email verification tokens: 24-hour expiration
- MFA challenge tokens: 10-minute expiration

### Password Security

Passwords are hashed using bcrypt with appropriate salt rounds. The passlib library provides the CryptContext for consistent hashing across the application.

### Authorization

Role-based access control (RBAC) is implemented through the permissions module. Three roles exist:

- **Admin**: Full system access
- **Instructor**: Can create and manage own courses, view analytics for own courses
- **Student**: Can enroll, learn, take quizzes, view own progress

### Rate Limiting

Rate limiting is implemented at the middleware level with configurable limits:

- General API: 100 requests per minute per IP
- Auth endpoints: 60 requests per minute per IP
- File uploads: 100 requests per hour per user

Rate limiting can use Redis for distributed limiting or fall back to in-memory implementation.

### Token Blacklisting

Logout invalidates access tokens by adding them to a blacklist in Redis (or memory for development). This enables immediate session termination.

### MFA (Multi-Factor Authentication)

Optional MFA uses TOTP (Time-based One-Time Password) compatible with Google Authenticator and similar apps. Users enable MFA through their profile, receiving a secret to configure their authenticator app.

---

## Background Jobs and Celery

### Task Queues

Three Celery queues handle different task types:

1. **emails**: Email sending tasks (welcome emails, password resets, notifications)
2. **certificates**: Certificate generation tasks
3. **progress**: Progress tracking and analytics updates
4. **webhooks**: External webhook delivery

### Task Types

**email_tasks.py**:
- `send_welcome_email`: Sends welcome email to new users
- `send_password_reset_email`: Sends password reset link
- `send_enrollment_confirmation`: Confirms course enrollment
- `send_course_completion_email`: Notifies completion and certificate

**certificate_tasks.py**:
- `generate_certificate`: Asynchronous PDF certificate generation

**progress_tasks.py**:
- `update_enrollment_progress`: Recalculates completion percentage
- `update_course_statistics`: Updates cached course metrics

**webhook_tasks.py**:
- `deliver_webhook`: Delivers events to registered webhook URLs

### Task Configuration

Celery is configured with Redis as both broker and result backend. Tasks are configured with retry policies, time limits, and result expiration.

---

## Testing Strategy

### Test Structure

The test suite follows the same modular structure as the application:

```
tests/
├── conftest.py              # Shared fixtures
├── helpers.py               # Test utilities
├── test_auth.py            # Authentication tests
├── test_courses.py         # Course module tests
├── test_quizzes.py         # Quiz module tests
├── test_enrollments.py     # Enrollment tests
├── test_analytics.py       # Analytics tests
├── test_certificates.py    # Certificate tests
├── test_files.py           # File handling tests
├── test_permissions.py     # RBAC tests
├── test_rate_limit_rules.py
├── test_response_envelope.py
├── test_webhooks.py
├── test_secrets.py
├── test_health.py
└── perf/                   # Performance tests
```

### Test Fixtures

Key fixtures include:

- `db_session`: Database session for tests
- `client`: TestClient for API testing
- `test_user`: Sample user for authentication
- `test_course`: Sample course for course tests
- `test_enrollment`: Sample enrollment

### Test Coverage

The project maintains comprehensive test coverage including:

- Unit tests for services and repositories
- Integration tests for API endpoints
- Authentication flow tests
- Permission and authorization tests
- Rate limiting tests

---

## Deployment Guide

### Development Environment

For local development:

```bash
# Clone repository
git clone <repo-url>
cd lms_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Start supporting services
docker-compose up -d db redis

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Docker Deployment

The project includes Docker Compose configuration for development and production:

**Development**:
```bash
docker-compose up -d
```

**Production**:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Environment Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql+psycopg2://lms:lms@localhost:5432/lms |
| REDIS_URL | Redis connection string | redis://localhost:6379/0 |
| SECRET_KEY | JWT signing key | (required, 32+ characters) |
| ENVIRONMENT | deployment environment | development |
| DEBUG | Enable debug mode | True |

### Production Considerations

For production deployment:

1. Set DEBUG=False
2. Use strong SECRET_KEY (32+ random characters)
3. Configure proper CORS origins
4. Enable rate limiting with Redis
5. Set up Sentry for error tracking
6. Configure file storage (Azure Blob recommended)
7. Use production database with SSL
8. Set up monitoring and alerts

---

## How to Build the Project

This section provides a complete step-by-step guide to building and running the LMS Backend project from scratch.

### Prerequisites

Before building the project, ensure you have the following installed:

1. **Python 3.11 or higher**: The project requires Python 3.11+ for type hints and modern language features.
2. **PostgreSQL 14+**: For the primary database.
3. **Redis 7+**: For caching, rate limiting, and Celery message broker.
4. **Docker and Docker Compose** (optional but recommended): For containerized deployment.
5. **Git**: For version control.

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd lms_backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Key variables to configure:
# - DATABASE_URL: PostgreSQL connection string
# - SECRET_KEY: Generate a secure random key
# - REDIS_URL: Redis connection string
```

### Step 3: Database Setup

**Option A: Using Docker Compose**:
```bash
# Start only database and Redis
docker-compose up -d db redis

# Run migrations
alembic upgrade head

# Seed initial data (optional)
python -m scripts.seed_data
```

**Option B: Local PostgreSQL**:
```bash
# Create database
createdb lms

# Run migrations
alembic upgrade head
```

### Step 4: Running the Application

**Development Server**:
```bash
# Start FastAPI with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Background Tasks (Celery)**:
```bash
# Start Celery worker
celery -A app.tasks.celery_app.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

### Step 5: Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Step 6: Docker Production Build

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Run production containers
docker-compose -f docker-compose.prod.yml up -d
```

### Complete Docker Setup

For a complete development environment with all services:

```bash
# Start all services (API, Celery workers, PostgreSQL, Redis)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Verification

After setup, verify the application is running:

1. **Health Check**: Visit http://localhost:8000/api/v1/health
2. **API Documentation**: Visit http://localhost:8000/docs
3. **Ready Check**: Visit http://localhost:8000/api/v1/ready

### Common Build Issues

**Database Connection Error**:
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database user has proper permissions

**Redis Connection Error**:
- Verify Redis is running
- Check REDIS_URL in .env
- Ensure Redis port 6379 is accessible

**Import Errors**:
- Ensure virtual environment is activated
- Reinstall dependencies: pip install -r requirements.txt

**Port Already in Use**:
- Stop existing process using the port
- Or modify PORT in .env

---

## Conclusion

This comprehensive documentation covers all aspects of the LMS Backend project. The system is designed with modern best practices including modular architecture, comprehensive security, extensive testing, and production-ready deployment options.

For additional information, refer to the individual module documentation files in the docs/tech/ directory or examine the source code directly.
