# LMS Backend - Complete Project Documentation

This document provides a comprehensive guide to understanding, building, and deploying the LMS (Learning Management System) Backend. It covers the complete architecture, every module in detail, all technical decisions, and the rationale behind each choice.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Technology Stack Deep Dive](#3-technology-stack-deep-dive)
4. [Module-by-Module Documentation](#4-module-by-module-documentation)
5. [Database Schema and Data Model](#5-database-schema-and-data-model)
6. [API Endpoints Reference](#6-api-endpoints-reference)
7. [Authentication and Security](#7-authentication-and-security)
8. [Background Jobs and Task Queue](#8-background-jobs-and-task-queue)
9. [File Storage System](#9-file-storage-system)
10. [Payment Integration](#10-payment-integration)
11. [Testing Strategy](#11-testing-strategy)
12. [Deployment Guide](#12-deployment-guide)
13. [Configuration Reference](#13-configuration-reference)

---

## 1. Project Overview

### 1.1 What is This Project?

This is a production-ready **Learning Management System (LMS) Backend** built with modern Python technologies. It provides a complete set of APIs for managing online education platforms, including user management, course creation, quiz assessments, progress tracking, certificate generation, and payment processing.

### 1.2 Core Features

The LMS Backend provides the following core capabilities:

| Feature | Description |
|---------|-------------|
| **User Management** | Registration, authentication, role-based access control (Admin, Instructor, Student) |
| **Course Management** | Create, publish, and manage courses with lessons and multimedia content |
| **Enrollment System** | Student enrollment with progress tracking |
| **Quiz System** | Create quizzes with multiple question types, time limits, and automatic grading |
| **Progress Tracking** | Track lesson completion, time spent, and overall course progress |
| **Certificate Generation** | Automatically generate PDF certificates upon course completion |
| **Analytics Dashboard** | Comprehensive analytics for students, instructors, and administrators |
| **Payment Processing** | Integration with multiple payment gateways (MyFatoorah, Paymob, Stripe) |
| **Email Notifications** | Automated emails for enrollments, completions, reminders |
| **File Management** | Upload and serve course materials (videos, PDFs, images) |
| **API Rate Limiting** | Protect API endpoints from abuse |
| **Observability** | Metrics, logging, and error tracking with Sentry |

### 1.3 Project Structure

```
lms_backend/
├── app/                          # Main application package
│   ├── api/                      # API route registration
│   │   └── v1/                   # API version 1
│   │       └── api.py            # Main router aggregator
│   ├── core/                     # Core infrastructure
│   │   ├── config.py             # Configuration management
│   │   ├── database.py           # Database connection
│   │   ├── security.py           # JWT and password handling
│   │   ├── permissions.py        # Role-based permissions
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   ├── middleware/           # Custom middleware
│   │   │   ├── rate_limit.py     # Rate limiting
│   │   │   ├── security_headers.py
│   │   │   ├── request_logging.py
│   │   │   └── response_envelope.py
│   │   ├── cache.py              # Redis caching
│   │   ├── health.py             # Health checks
│   │   ├── metrics.py            # Prometheus metrics
│   │   └── observability.py      # Sentry integration
│   ├── modules/                  # Business logic modules
│   │   ├── auth/                 # Authentication module
│   │   ├── users/                # User management module
│   │   ├── courses/              # Course management module
│   │   ├── enrollments/          # Enrollment tracking module
│   │   ├── quizzes/              # Quiz and assessment module
│   │   ├── certificates/         # Certificate generation module
│   │   ├── analytics/            # Analytics and reporting module
│   │   ├── files/               # File upload and storage module
│   │   ├── payments/             # Payment processing module
│   │   └── emails/               # Email sending module
│   ├── tasks/                    # Celery background tasks
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── email_tasks.py        # Email sending tasks
│   │   ├── certificate_tasks.py  # Certificate generation tasks
│   │   ├── progress_tasks.py     # Progress calculation tasks
│   │   └── webhook_tasks.py      # Payment webhook processing
│   └── utils/                    # Utility functions
│       ├── validators.py
│       ├── pagination.py
│       └── constants.py
├── tests/                        # Test suite
│   ├── test_auth.py
│   ├── test_courses.py
│   ├── test_quizzes.py
│   ├── test_payments.py
│   └── perf/                     # Performance tests
├── docs/                         # Documentation
│   └── tech/                     # Technical documentation
├── docker-compose.yml            # Local development setup
├── docker-compose.prod.yml       # Production setup
├── docker-compose.staging.yml   # Staging setup
├── requirements.txt              # Python dependencies
└── README.md                     # Project readme
```

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

The LMS Backend follows a **modular monolith** architecture with clear separation of concerns. It uses a layered approach where each layer has specific responsibilities.

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Clients                              │
│            (Web App, Mobile App, External Services)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Middleware Stack                          ││
│  │  CORS → GZip → Security Headers → Rate Limit → Logging       ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Route Handlers                            ││
│  │  /api/v1/auth/*  /api/v1/courses/*  /api/v1/payments/*    ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Business Logic (Services)                ││
│  │  AuthService  CourseService  PaymentService  QuizService   ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Data Access (Repositories)               ││
│  │  UserRepository  CourseRepository  QuizRepository          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐│
│  │ PostgreSQL   │  │   Redis     │  │  File System / S3      ││
│  │ (Primary DB) │  │ (Cache/Broker)│  │  (Media Storage)      ││
│  └─────────────┘  └─────────────┘  └─────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Background Workers                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Celery Workers                            ││
│  │  Emails Queue  Certificates Queue  Webhooks Queue           ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Celery Beat (Scheduler)                  ││
│  │  Weekly Reports  Daily Reminders                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Design Principles

The architecture follows these key design principles:

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Modularity** | Each feature is isolated in its own module | Separate folders under `app/modules/` |
| **Dependency Injection** | Dependencies are injected, not created | FastAPI's `Depends()` system |
| **Repository Pattern** | Data access is abstracted | Separate repository classes |
| **Service Layer** | Business logic is centralized | Service classes handle logic |
| **Configuration Management** | All config is environment-based | Pydantic Settings with `.env` |
| **Async-First** | Non-blocking operations where possible | `async/await` throughout |

### 2.3 Why This Architecture?

**Why Modular Monolith?**

- **Simplicity**: Easier to develop and debug than microservices
- **Data Consistency**: ACID transactions across modules without distributed complexity
- **Deployment**: Single deployment unit, simpler operations
- **Future-Ready**: Can be split into microservices later if needed

**Why Layered Architecture?**

- Clear separation of concerns
- Easier to test each layer independently
- Maintainable code structure
- Standard Python web application pattern

---

## 3. Technology Stack Deep Dive

### 3.1 Programming Language: Python

**Version**: Python 3.11+

**Why Python?**
- Rapid development with clean syntax
- Excellent ecosystem for web development
- First-class async/await support
- Rich type hinting support for better IDE experience
- Strong AI/ML libraries for future analytics enhancements

**Key Libraries Used:**
- `fastapi`: Modern async web framework
- `sqlalchemy`: SQL toolkit and ORM
- `pydantic`: Data validation using Python type hints

### 3.2 Web Framework: FastAPI

**Why FastAPI?**
- High performance (comparable to Node.js and Go)
- Automatic OpenAPI/Swagger documentation
- Built-in request/response validation with Pydantic
- Native async/await support
- Dependency injection system

**Key Features Used:**
```python
# Automatic documentation
app = FastAPI(
    title="LMS Backend",
    version="1.0.0",
    docs_url="/docs"
)

# Type-safe request/response
class CourseCreate(BaseModel):
    title: str
    description: str | None

@app.post("/courses")
def create_course(course: CourseCreate) -> CourseResponse:
    # Validation happens automatically
    pass

# Dependency injection
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Easy dependency management
    pass
```

### 3.3 Database: PostgreSQL

**Why PostgreSQL?**
- ACID compliance for data integrity
- Excellent JSON support for flexible metadata
- Strong indexing capabilities
- Mature and stable (30+ years)
- Great performance for relational queries

**Why Not Other Databases?**
- **MySQL**: Weaker JSON support, less feature-rich
- **MongoDB**: Data is highly relational, ACID important
- **SQLite**: Not suitable for production/ concurrency

### 3.4 ORM: SQLAlchemy 2.0

**Why SQLAlchemy?**
- Most mature Python ORM (15+ years)
- Full control over SQL when needed
- Excellent async support in 2.0
- Native Alembic migration integration

**Code Example:**
```python
from sqlalchemy import select
from sqlalchemy.orm import Session

# Modern SQLAlchemy 2.0 style
result = await db.execute(
    select(Course)
    .where(Course.is_published == True)
    .order_by(Course.created_at.desc())
)
```

### 3.5 Caching and Message Broker: Redis

**Why Redis?**
- Dual purpose: caching AND message broker
- Extremely fast in-memory operations
- Built-in pub/sub for Celery
- Perfect for rate limiting

**Use Cases in This Project:**
1. API response caching
2. JWT token blacklist storage
3. Rate limiting counters
4. Celery task queue broker

### 3.6 Background Tasks: Celery

**Why Celery?**
- Python-native, best integration
- Redis already available
- Celery Beat for scheduling
- Built-in retry logic
- Flower for monitoring

**Task Queues Used:**
- `emails`: All email sending tasks
- `certificates`: PDF certificate generation
- `webhooks`: Payment webhook processing
- `progress`: Progress calculation tasks

### 3.7 Authentication: JWT with python-jose

**Token Strategy:**
| Token Type | Lifetime | Purpose |
|------------|----------|---------|
| Access Token | 15 minutes | API authentication |
| Refresh Token | 30 days | Get new access tokens |
| Password Reset | 30 minutes | One-time password reset |
| Email Verification | 24 hours | Verify email address |
| MFA Challenge | 10 minutes | Two-factor authentication |

**Security Features:**
- JWT token blacklisting for logout
- Token type validation
- JTI (JWT ID) for token identification

### 3.8 Password Hashing: bcrypt

**Why bcrypt?**
- Industry-standard security
- Configurable work factor
- Mature and well-tested (20+ years)
- Protected against rainbow table attacks

### 3.9 File Storage: Local + AWS S3

**Why Dual Storage?**
- **Local**: Easy development, no cloud costs
- **S3**: Production scalability, CDN integration

**Storage Abstraction:**
```python
class StorageBackend(ABC):
    @abstractmethod
    def save(self, folder: str, filename: str, content: bytes) -> str:
        pass

class LocalStorage(StorageBackend):
    # Saves to local filesystem
    
class S3Storage(StorageBackend):
    # Saves to AWS S3
```

### 3.10 Containerization: Docker

**Docker Compose Services:**
- `api`: FastAPI application server
- `celery-worker`: Background task workers
- `celery-beat`: Task scheduler
- `flower`: Celery monitoring UI
- `db`: PostgreSQL database
- `redis`: Redis cache and broker

---

## 4. Module-by-Module Documentation

### 4.1 Authentication Module (`app/modules/auth/`)

**Purpose**: Handle all authentication-related operations including registration, login, logout, password reset, email verification, and MFA.

**Key Components:**

| File | Purpose |
|------|---------|
| `models.py` | RefreshToken database model |
| `router.py` | API endpoints for auth |
| `service.py` | Authentication business logic |
| `schemas.py` | Request/response Pydantic models |

**API Endpoints:**

```
POST   /api/v1/auth/register              # User registration
POST   /api/v1/auth/login                # User login
POST   /api/v1/auth/token                # OAuth2 token endpoint
POST   /api/v1/auth/login/mfa           # MFA login verification
POST   /api/v1/auth/refresh              # Refresh access token
POST   /api/v1/auth/logout               # Logout (revoke tokens)
POST   /api/v1/auth/forgot-password      # Request password reset
POST   /api/v1/auth/reset-password       # Reset password with token
POST   /api/v1/auth/verify-email/request # Request email verification
POST   /api/v1/auth/verify-email/confirm # Confirm email verification
POST   /api/v1/auth/mfa/enable/request    # Request MFA setup
POST   /api/v1/auth/mfa/enable/confirm    # Confirm MFA setup
POST   /api/v1/auth/mfa/disable           # Disable MFA
GET    /api/v1/auth/me                    # Get current user
```

**Why This Design?**
- **Token-based**: Stateless, scalable authentication
- **Refresh tokens**: Long-lived sessions without security compromise
- **MFA support**: Enhanced security for sensitive accounts
- **Email verification**: Ensures valid user emails

### 4.2 Users Module (`app/modules/users/`)

**Purpose**: Manage user profiles, roles, and user-related operations.

**Key Components:**

| File | Purpose |
|------|---------|
| `models.py` | User database model |
| `router.py` | User API endpoints |
| `schemas.py` | User-related Pydantic models |
| `services/user_service.py` | User business logic |
| `repositories/user_repository.py` | User data access |

**User Roles:**
```python
class Role(str, Enum):
    ADMIN = "admin"        # Full system access
    INSTRUCTOR = "instructor"  # Create/manage courses
    STUDENT = "student"    # Consume courses
```

**Database Schema:**
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    full_name: Mapped[str]
    role: Mapped[str] = mapped_column(default="student")
    is_active: Mapped[bool] = mapped_column(default=True)
    mfa_enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    last_login_at: Mapped[datetime | None]
    email_verified_at: Mapped[datetime | None]
```

**Why This Design?**
- **Role-based access**: Clear permission separation
- **Soft user state**: is_active allows disabling without deletion
- **Timestamps**: Track user lifecycle events

### 4.3 Courses Module (`app/modules/courses/`)

**Purpose**: Manage courses, lessons, and course content.

**Key Components:**

| File | Purpose |
|------|---------|
| `models/course.py` | Course database model |
| `models/lesson.py` | Lesson database model |
| `routers/course_router.py` | Course API endpoints |
| `routers/lesson_router.py` | Lesson API endpoints |
| `services/course_service.py` | Course business logic |
| `services/lesson_service.py` | Lesson business logic |
| `repositories/course_repository.py` | Course data access |

**Course Model:**
```python
class Course(Base):
    __tablename__ = "courses"
    
    id: Mapped[UUID]
    title: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    instructor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    category: Mapped[str | None]
    difficulty_level: Mapped[str | None]  # beginner, intermediate, advanced
    is_published: Mapped[bool] = mapped_column(default=False)
    thumbnail_url: Mapped[str | None]
    estimated_duration_minutes: Mapped[int | None]
    metadata: Mapped[dict | None] = mapped_column(JSON)  # Flexible data
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**Lesson Model:**
```python
class Lesson(Base):
    __tablename__ = "lessons"
    
    id: Mapped[UUID]
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str]
    slug: Mapped[str]
    content_type: Mapped[str]  # video, text, quiz
    content: Mapped[str | None]  # Video URL or text content
    duration_minutes: Mapped[int | None]
    order: Mapped[int]
    is_free: Mapped[bool] = mapped_column(default=False)
    is_published: Mapped[bool] = mapped_column(default=False)
```

**API Endpoints:**

```
# Course endpoints
GET    /api/v1/courses                    # List all courses
POST   /api/v1/courses                    # Create course (instructor/admin)
GET    /api/v1/courses/{id}               # Get course details
PUT    /api/v1/courses/{id}               # Update course
DELETE /api/v1/courses/{id}               # Delete course
GET    /api/v1/courses/{id}/lessons       # Get course lessons
GET    /api/v1/courses/me                 # Get my courses (instructor)

# Lesson endpoints
GET    /api/v1/lessons                    # List lessons
POST   /api/v1/lessons                    # Create lesson
GET    /api/v1/lessons/{id}               # Get lesson details
PUT    /api/v1/lessons/{id}               # Update lesson
DELETE /api/v1/lessons/{id}               # Delete lesson
POST   /api/v1/lessons/{id}/complete      # Mark lesson complete
```

**Why This Design?**
- **Slug-based URLs**: SEO-friendly course URLs
- **Course/Lesson separation**: Reusable lessons across courses
- **Content types**: Support for different lesson formats
- **Draft/Published**: Content workflow management

### 4.4 Enrollments Module (`app/modules/enrollments/`)

**Purpose**: Track student enrollment in courses and monitor progress.

**Key Components:**

| File | Purpose |
|------|---------|
| `models.py` | Enrollment and LessonProgress models |
| `router.py` | Enrollment API endpoints |
| `service.py` | Enrollment business logic |
| `repository.py` | Enrollment data access |

**Enrollment Model:**
```python
class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id: Mapped[UUID]
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    enrolled_at: Mapped[datetime]
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    status: Mapped[str]  # active, completed, dropped, expired
    progress_percentage: Mapped[Decimal]  # 0-100
    completed_lessons_count: Mapped[int]
    total_lessons_count: Mapped[int]
    total_time_spent_seconds: Mapped[int]
    last_accessed_at: Mapped[datetime | None]
    certificate_issued_at: Mapped[datetime | None]
    rating: Mapped[int | None]  # 1-5 stars
    review: Mapped[str | None]
```

**LessonProgress Model:**
```python
class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    
    id: Mapped[UUID]
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"))
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id"))
    status: Mapped[str]  # not_started, in_progress, completed
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    time_spent_seconds: Mapped[int]
    last_position_seconds: Mapped[int]  # For video progress
    completion_percentage: Mapped[Decimal]
    attempts_count: Mapped[int]
```

**API Endpoints:**

```
GET    /api/v1/enrollments                    # List my enrollments
POST   /api/v1/enrollments                    # Enroll in course
GET    /api/v1/enrollments/{id}               # Get enrollment details
PUT    /api/v1/enrollments/{id}               # Update enrollment
DELETE /api/v1/enrollments/{id}               # Unenroll from course
POST   /api/v1/enrollments/{id}/complete      # Mark course complete
POST   /api/v1/enrollments/{id}/progress      # Update lesson progress
POST   /api/v1/enrollments/{id}/review        # Submit course review
GET    /api/v1/enrollments/{id}/certificate   # Get certificate
```

**Why This Design?**
- **Granular progress**: Track individual lesson completion
- **Time tracking**: Monitor student engagement
- **Completion percentage**: Real-time progress indicator
- **Reviews/Ratings**: Student feedback system

### 4.5 Quizzes Module (`app/modules/quizzes/`)

**Purpose**: Create and manage quizzes, questions, and attempts with automatic grading.

**Key Components:**

| File | Purpose |
|------|---------|
| `models/quiz.py` | Quiz database model |
| `models/question.py` | Question model |
| `models/attempt.py` | Quiz attempt model |
| `routers/quiz_router.py` | Quiz API endpoints |
| `routers/question_router.py` | Question API endpoints |
| `routers/attempt_router.py` | Attempt API endpoints |
| `services/quiz_service.py` | Quiz business logic |
| `services/question_service.py` | Question business logic |
| `services/attempt_service.py` | Attempt grading logic |

**Quiz Model:**
```python
class Quiz(Base):
    __tablename__ = "quizzes"
    
    id: Mapped[UUID]
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id"), unique=True)
    title: Mapped[str]
    description: Mapped[str | None]
    quiz_type: Mapped[str]  # practice, graded
    passing_score: Mapped[Decimal]  # e.g., 70.00
    time_limit_minutes: Mapped[int | None]
    max_attempts: Mapped[int | None]
    shuffle_questions: Mapped[bool]
    shuffle_options: Mapped[bool]
    show_correct_answers: Mapped[bool]
    is_published: Mapped[bool]
```

**Question Model:**
```python
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id: Mapped[UUID]
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id"))
    question_text: Mapped[str]
    question_type: Mapped[str]  # multiple_choice, true_false, short_answer
    options: Mapped[list[dict] | None]  # JSON array of options
    correct_answer: Mapped[dict | None]  # JSON with correct answer
    points: Mapped[Decimal]
    explanation: Mapped[str | None]
    order: Mapped[int]
```

**QuizAttempt Model:**
```python
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id: Mapped[UUID]
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"))
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id"))
    attempt_number: Mapped[int]
    status: Mapped[str]  # in_progress, submitted, graded
    started_at: Mapped[datetime]
    submitted_at: Mapped[datetime | None]
    graded_at: Mapped[datetime | None]
    score: Mapped[Decimal | None]
    max_score: Mapped[Decimal | None]
    percentage: Mapped[Decimal | None]
    is_passed: Mapped[bool | None]
    time_taken_seconds: Mapped[int | None]
    answers: Mapped[list[dict] | None]  # Student answers
```

**API Endpoints:**

```
# Quiz endpoints
GET    /api/v1/quizzes                     # List quizzes
POST   /api/v1/quizzes                     # Create quiz
GET    /api/v1/quizzes/{id}                 # Get quiz details
PUT    /api/v1/quizzes/{id}                 # Update quiz
DELETE /api/v1/quizzes/{id}                 # Delete quiz

# Question endpoints
GET    /api/v1/questions                    # List questions
POST   /api/v1/questions                    # Create question
GET    /api/v1/questions/{id}               # Get question
PUT    /api/v1/questions/{id}              # Update question
DELETE /api/v1/questions/{id}              # Delete question

# Attempt endpoints
GET    /api/v1/attempts                     # List attempts
POST   /api/v1/attempts                     # Start quiz attempt
GET    /api/v1/attempts/{id}               # Get attempt details
PUT    /api/v1/attempts/{id}/submit        # Submit quiz answers
GET    /api/v1/attempts/{id}/results       # Get attempt results
```

**Why This Design?**
- **Multiple question types**: Flexible quiz formats
- **Automatic grading**: Instant feedback for students
- **Attempt tracking**: Enforce max attempts, track retries
- **Time limits**: Controlled assessment environment

### 4.6 Certificates Module (`app/modules/certificates/`)

**Purpose**: Generate and manage PDF certificates upon course completion.

**Key Components:**

| File | Purpose |
|------|---------|
| `models.py` | Certificate database model |
| `router.py` | Certificate API endpoints |
| `service.py` | Certificate generation logic |

**Certificate Model:**
```python
class Certificate(Base):
    __tablename__ = "certificates"
    
    id: Mapped[UUID]
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"), unique=True)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    certificate_number: Mapped[str] = mapped_column(unique=True)
    pdf_path: Mapped[str]
    completion_date: Mapped[datetime]
    issued_at: Mapped[datetime]
    is_revoked: Mapped[bool] = mapped_column(default=False)
    revoked_at: Mapped[datetime | None]
```

**Certificate Generation Process:**
```python
def generate_certificate(enrollment: Enrollment) -> Certificate:
    # 1. Generate unique certificate number
    cert_number = generate_unique_number()
    
    # 2. Create PDF using fpdf2
    pdf = CertificatePDF()
    pdf.add_page()
    pdf.add_content(
        student_name=enrollment.student.full_name,
        course_name=enrollment.course.title,
        completion_date=enrollment.completed_at
    )
    
    # 3. Save PDF to storage
    pdf_path = save_pdf(pdf, cert_number)
    
    # 4. Create database record
    certificate = Certificate(
        certificate_number=cert_number,
        pdf_path=pdf_path,
        ...
    )
    
    return certificate
```

**API Endpoints:**

```
GET    /api/v1/certificates                 # List certificates
GET    /api/v1/certificates/{id}           # Get certificate details
GET    /api/v1/certificates/{id}/download  # Download PDF
GET    /api/v1/certificates/verify/{number} # Verify certificate
```

**Why This Design?**
- **PDF generation**: Professional-looking certificates
- **Unique numbers**: Certificate verification system
- **Revocation support**: Handle certificate invalidation
- **Enrollment-linked**: One certificate per completion

### 4.7 Analytics Module (`app/modules/analytics/`)

**Purpose**: Provide comprehensive analytics and reporting for all user types.

**Key Components:**

| File | Purpose |
|------|---------|
| `router.py` | Analytics API endpoints |
| `services/student_analytics_service.py` | Student-specific analytics |
| `services/course_analytics_service.py` | Course-specific analytics |
| `services/instructor_analytics_service.py` | Instructor dashboard |
| `services/system_analytics_service.py` | Admin analytics |

**Analytics Types:**

**Student Analytics:**
- Current enrollments
- Course progress summary
- Quiz performance history
- Time spent learning

**Instructor Analytics:**
- Course enrollment stats
- Student engagement metrics
- Quiz performance by course
- Revenue summary

**Admin Analytics:**
- Total users by role
- System-wide enrollment stats
- Revenue across all courses
- System health metrics

**API Endpoints:**

```
GET    /api/v1/analytics/my-progress          # Student's progress
GET    /api/v1/analytics/my-dashboard         # Student's dashboard
GET    /api/v1/analytics/courses/{id}         # Course analytics
GET    /api/v1/analytics/instructors/{id}/overview  # Instructor overview
GET    /api/v1/analytics/system/overview      # System-wide analytics
```

**Why This Design?**
- **Role-based views**: Each user sees relevant data
- **Comprehensive metrics**: Track engagement and performance
- **Real-time**: Live progress tracking

### 4.8 Files Module (`app/modules/files/`)

**Purpose**: Handle file uploads and storage with multiple backend support.

**Key Components:**

| File | Purpose |
|------|---------|
| `models.py` | UploadedFile database model |
| `router.py` | File API endpoints |
| `service.py` | File handling logic |
| `storage/base.py` | Storage backend interface |
| `storage/local.py` | Local filesystem storage |
| `storage/s3.py` | AWS S3 storage |

**Storage Backend Pattern:**
```python
class StorageBackend(ABC):
    provider: str
    
    @abstractmethod
    def save(self, folder: str, filename: str, content: bytes, content_type: str = None) -> str:
        pass
    
    @abstractmethod
    def build_file_url(self, storage_path: str) -> str:
        pass
    
    @abstractmethod
    def resolve_local_path(self, storage_path: str) -> Path | None:
        pass
    
    @abstractmethod
    def create_download_url(self, storage_path: str, expires_seconds: int) -> str | None:
        pass
```

**API Endpoints:**

```
POST   /api/v1/files/upload               # Upload a file
GET    /api/v1/files/my-files             # List user's files
GET    /api/v1/files/download/{id}         # Download file
```

**Why This Design?**
- **Storage abstraction**: Easy to switch providers
- **Local + S3**: Development and production ready
- **Presigned URLs**: Secure S3 downloads with expiration
- **File metadata**: Track uploads in database

### 4.9 Payments Module (`app/modules/payments/`)

**Purpose**: Process payments and manage subscriptions through multiple payment gateways.

**Key Components:**

| File | Purpose |
|------|---------|
| `models.py` | Payment and Subscription models |
| `router.py` | Payment API endpoints |
| `service.py` | Payment processing logic |
| `stripe_service.py` | Stripe integration |
| `myfatoorah_service.py` | MyFatoorah integration |
| `paymob_service.py` | Paymob integration |

**Payment Model:**
```python
class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    enrollment_id: Mapped[UUID | None] = mapped_column(ForeignKey("enrollments.id"))
    amount: Mapped[Decimal]
    currency: Mapped[str]  # EGP, USD, etc.
    gateway: Mapped[str]  # stripe, myfatoorah, paymob
    status: Mapped[str]  # pending, completed, failed, refunded
    transaction_id: Mapped[str | None]  # Gateway's transaction ID
    payment_method: Mapped[str | None]
    metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]
```

**Subscription Model:**
```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    plan_name: Mapped[str]
    amount: Mapped[Decimal]
    currency: Mapped[str]
    gateway: Mapped[str]
    status: Mapped[str]  # active, cancelled, expired
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    gateway_subscription_id: Mapped[str | None]
```

**Payment Gateways:**

**MyFatoorah:**
- Popular in Middle East
- Supports multiple payment methods
- Webhook-based notifications

**Paymob:**
- Egyptian payment processor
- Various payment options
- iframe integration

**Stripe (Planned):**
- Global payment processor
- Extensive features
- Well-documented API

**API Endpoints:**

```
POST   /api/v1/payments/create-payment-intent   # Create payment
POST   /api/v1/payments/create-subscription     # Create subscription
GET    /api/v1/payments/my-payments             # List user's payments
GET    /api/v1/payments/my-subscriptions        # List user's subscriptions
GET    /api/v1/payments/revenue/summary         # Revenue report (admin)
POST   /api/v1/payments/webhooks/myfatoorah     # MyFatoorah webhook
POST   /api/v1/payments/webhooks/paymob         # Paymob webhook
```

**Why This Design?**
- **Multiple gateways**: Payment method flexibility
- **Webhook handling**: Async payment confirmation
- **Subscription support**: Recurring payments
- **Revenue analytics**: Track earnings

### 4.10 Emails Module (`app/modules/emails/`)

**Purpose**: Send transactional emails with templates.

**Key Components:**

| File | Purpose |
|------|---------|
| `service.py` | Email sending logic |

**Email Types:**
- Welcome emails
- Password reset
- Email verification
- MFA codes
- Enrollment confirmation
- Course completion
- Quiz results
- Payment confirmation
- Weekly progress reports
- Course reminders

**Email Service:**
```python
class EmailService:
    def send_welcome_email(self, email: str, full_name: str) -> str:
        # Send welcome email
        
    def send_password_reset_email(self, email: str, full_name: str, reset_token: str, reset_url: str) -> str:
        # Send password reset email
        
    def send_enrollment_confirmation_email(self, *, email: str, student_name: str, course_title: str, ...) -> str:
        # Send enrollment confirmation
```

**Why This Design?**
- **Async sending**: Don't block API responses
- **Templates**: Consistent email formatting
- **Retry logic**: Handle transient failures

---

## 5. Database Schema and Data Model

### 5.1 Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │   Course    │       │   Lesson    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──────│ id (PK)     │◄──────│ id (PK)     │
│ email       │       │ title       │       │ course_id   │
│ full_name   │       │ slug        │       │ (FK)        │
│ role        │       │ description │       │ title       │
│ password_hash│      │ instructor_ │       │ content     │
│ is_active   │       │ id (FK)     │       │ order       │
│ mfa_enabled │       │ category    │       │ content_type│
│ created_at  │       │ is_published│       │ duration    │
└──────┬──────┘       └──────┬──────┘       └──────┬──────┘
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│Enrollment  │       │   Quiz       │       │LessonProgress│
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ student_id  │       │ lesson_id   │       │ enrollment_ │
│ (FK)        │       │ (FK)        │       │ id (FK)     │
│ course_id   │       │ title       │       │ lesson_id   │
│ (FK)        │       │ quiz_type   │       │ (FK)        │
│ status      │       │ passing_    │       │ status      │
│ progress_%  │       │ score       │       │ time_spent  │
│ enrolled_at │       │ time_limit  │       │ completed   │
└──────┬──────┘       └──────┬──────┘       └─────────────┘
       │                    │
       │                    ▼
       │              ┌─────────────┐
       │              │QuizQuestion │
       │              ├─────────────┤
       │              │ id (PK)     │
       └─────────────►│ quiz_id(FK) │
                      │ question    │
                      │ options     │
                      │ correct_ans │
                      └──────┬──────┘
                             │
                             ▼
                      ┌─────────────┐
                      │QuizAttempt │
                      ├─────────────┤
                      │ id (PK)     │
                      │ enrollment_ │
                      │ id (FK)     │
                      │ quiz_id(FK) │
                      │ score       │
                      │ status      │
                      └─────────────┘
```

### 5.2 Database Indexing Strategy

The project uses strategic indexes for query optimization:

```python
# Course indexes
Index("ix_courses_is_published_created_at", "is_published", "created_at")
Index("ix_courses_instructor_created_at", "instructor_id", "created_at")

# Enrollment indexes
Index("ix_enrollments_student_enrolled_at", "student_id", "enrolled_at")
Index("ix_enrollments_course_enrolled_at", "course_id", "enrolled_at")
Index("ix_enrollments_course_status", "course_id", "status")

# Quiz attempt indexes
Index("ix_quiz_attempts_enrollment_status_submitted_at", "enrollment_id", "status", "submitted_at")
Index("ix_quiz_attempts_quiz_status_submitted_at", "quiz_id", "status", "submitted_at")
```

**Why These Indexes?**
- **Composite indexes**: Support common query patterns
- **Foreign key indexes**: Speed up joins
- **Status + date**: Filter by status sorted by date

---

## 6. API Endpoints Reference

### 6.1 Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/token` | OAuth2 token endpoint |
| POST | `/api/v1/auth/login/mfa` | MFA verification |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout and revoke tokens |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password |
| POST | `/api/v1/auth/verify-email/request` | Request email verification |
| POST | `/api/v1/auth/verify-email/confirm` | Confirm email verification |
| POST | `/api/v1/auth/mfa/enable/request` | Request MFA setup |
| POST | `/api/v1/auth/mfa/enable/confirm` | Confirm MFA setup |
| POST | `/api/v1/auth/mfa/disable` | Disable MFA |
| GET | `/api/v1/auth/me` | Get current user |

### 6.2 Course Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/courses` | List courses |
| POST | `/api/v1/courses` | Create course |
| GET | `/api/v1/courses/{id}` | Get course |
| PUT | `/api/v1/courses/{id}` | Update course |
| DELETE | `/api/v1/courses/{id}` | Delete course |
| GET | `/api/v1/courses/{id}/lessons` | Get course lessons |
| GET | `/api/v1/courses/me` | Get instructor's courses |

### 6.3 Lesson Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/lessons` | List lessons |
| POST | `/api/v1/lessons` | Create lesson |
| GET | `/api/v1/lessons/{id}` | Get lesson |
| PUT | `/api/v1/lessons/{id}` | Update lesson |
| DELETE | `/api/v1/lessons/{id}` | Delete lesson |
| POST | `/api/v1/lessons/{id}/complete` | Mark complete |

### 6.4 Enrollment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/enrollments` | List enrollments |
| POST | `/api/v1/enrollments` | Enroll in course |
| GET | `/api/v1/enrollments/{id}` | Get enrollment |
| PUT | `/api/v1/enrollments/{id}` | Update enrollment |
| DELETE | `/api/v1/enrollments/{id}` | Unenroll |
| POST | `/api/v1/enrollments/{id}/complete` | Complete course |
| POST | `/api/v1/enrollments/{id}/progress` | Update progress |
| POST | `/api/v1/enrollments/{id}/review` | Submit review |

### 6.5 Quiz Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quizzes` | List quizzes |
| POST | `/api/v1/quizzes` | Create quiz |
| GET | `/api/v1/quizzes/{id}` | Get quiz |
| PUT | `/api/v1/quizzes/{id}` | Update quiz |
| DELETE | `/api/v1/quizzes/{id}` | Delete quiz |
| GET | `/api/v1/questions` | List questions |
| POST | `/api/v1/questions` | Create question |
| GET | `/api/v1/questions/{id}` | Get question |
| PUT | `/api/v1/questions/{id}` | Update question |
| DELETE | `/api/v1/questions/{id}` | Delete question |
| GET | `/api/v1/attempts` | List attempts |
| POST | `/api/v1/attempts` | Start attempt |
| GET | `/api/v1/attempts/{id}` | Get attempt |
| PUT | `/api/v1/attempts/{id}/submit` | Submit attempt |

### 6.6 Payment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/payments/create-payment-intent` | Create payment |
| POST | `/api/v1/payments/create-subscription` | Create subscription |
| GET | `/api/v1/payments/my-payments` | List payments |
| GET | `/api/v1/payments/my-subscriptions` | List subscriptions |
| GET | `/api/v1/payments/revenue/summary` | Revenue (admin) |

### 6.7 Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/my-progress` | Student progress |
| GET | `/api/v1/analytics/my-dashboard` | Student dashboard |
| GET | `/api/v1/analytics/courses/{id}` | Course analytics |
| GET | `/api/v1/analytics/instructors/{id}/overview` | Instructor stats |
| GET | `/api/v1/analytics/system/overview` | System stats |

### 6.8 Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users` | List users (admin) |
| GET | `/api/v1/files/upload` | Upload file |
| GET | `/api/v1/files/my-files` | List files |
| GET | `/api/v1/files/download/{id}` | Download file |
| GET | `/api/v1/certificates` | List certificates |
| GET | `/api/v1/certificates/{id}/download` | Download certificate |

---

## 7. Authentication and Security

### 7.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Registration                           │
│  1. User submits email, password, name, role                    │
│  2. Password hashed with bcrypt                                 │
│  3. User created in database                                    │
│  4. Access + Refresh tokens issued                              │
│  5. Welcome email queued                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        User Login                               │
│  1. User submits email, password                                │
│  2. Verify password hash                                        │
│  3. Check MFA if enabled                                         │
│  4. Issue access token (15 min) + refresh token (30 days)      │
│  5. Update last_login_at                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Accessing Protected API                       │
│  1. Include token in Authorization header                      │
│  2. Validate token signature and expiry                        │
│  3. Check token not blacklisted                                │
│  4. Extract user from token                                     │
│  5. Check user role has required permission                    │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Token Management

**Access Token:**
- Short-lived (15 minutes)
- Used for all API requests
- Contains: user_id, role, jti (unique ID), expiry

**Refresh Token:**
- Long-lived (30 days)
- Used to obtain new access tokens
- Stored in database (RefreshToken model)
- Can be revoked individually

**Token Blacklisting:**
```python
class AccessTokenBlacklist:
    def revoke(self, jti: str, exp_epoch: int) -> None:
        # Store in Redis with TTL
        
    def is_revoked(self, jti: str) -> bool:
        # Check if token is blacklisted
```

### 7.3 Role-Based Access Control

```python
class Role(str, Enum):
    ADMIN = "admin"        # Full access
    INSTRUCTOR = "instructor"  # Course management
    STUDENT = "student"    # Course consumption

class Permission(str, Enum):
    CREATE_COURSE = "course:create"
    UPDATE_COURSE = "course:update"
    DELETE_COURSE = "course:delete"
    VIEW_ANALYTICS = "analytics:view"
    MANAGE_ENROLLMENTS = "enrollments:manage"
    MANAGE_USERS = "users:manage"
```

### 7.4 Security Features

| Feature | Implementation |
|---------|----------------|
| Password Hashing | bcrypt with cost factor 12 |
| Token Security | JWT with HS256 |
| Rate Limiting | Redis-backed sliding window |
| CORS | Configurable allowed origins |
| Security Headers | HSTS, X-Frame-Options, CSP |
| Input Validation | Pydantic models |
| SQL Injection | ORM with parameterized queries |
| XSS Prevention | Output encoding |

---

## 8. Background Jobs and Task Queue

### 8.1 Celery Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   API Server │─────►│    Redis     │─────►│   Celery     │
│              │      │  (Broker)    │      │   Worker     │
└──────────────┘      └──────────────┘      └──────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │ Celery Beat  │
                     │ (Scheduler) │
                     └──────────────┘
```

### 8.2 Task Queues

| Queue | Purpose | Examples |
|-------|---------|----------|
| `emails` | All email sending | Welcome, reset, notifications |
| `certificates` | PDF generation | Course completion certificates |
| `webhooks` | Payment processing | Gateway callbacks |
| `progress` | Bulk calculations | Progress recalculation |

### 8.3 Scheduled Tasks

**Weekly Progress Report:**
- Runs: Monday 9:00 AM
- Sends: Weekly summary to all active students
- Query: Students with active enrollments

**Daily Course Reminders:**
- Runs: Daily 10:00 AM
- Sends: Reminder to students inactive for 7+ days
- Query: Enrollments with no access in 7 days

### 8.4 Task Retry Logic

```python
@celery_app.task(
    autoretry_for=(SMTPException, TimeoutError),
    retry_backoff=True,  # Exponential backoff
    retry_jitter=True,   # Random jitter
    retry_kwargs={"max_retries": 5}
)
def send_email(email: str, subject: str, body: str):
    # Email sending logic
```

---

## 9. File Storage System

### 9.1 Storage Backends

**Local Storage:**
```python
class LocalStorage(StorageBackend):
    def save(self, folder: str, filename: str, content: bytes) -> str:
        path = Path(UPLOAD_DIR) / folder / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)
    
    def build_file_url(self, storage_path: str) -> str:
        return f"/uploads/{storage_path}"
```

**S3 Storage:**
```python
class S3Storage(StorageBackend):
    def save(self, folder: str, filename: str, content: bytes) -> str:
        key = f"{folder}/{filename}"
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=content)
        return key
    
    def create_download_url(self, storage_path: str, expires_seconds: int) -> str:
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': storage_path},
            ExpiresIn=expires_seconds
        )
```

### 9.2 File Upload Flow

```
1. Client sends POST to /api/v1/files/upload
   - Content-Type: multipart/form-data
   - File in "file" field
   - Optional "folder" and "is_public" parameters

2. API validates:
   - File size (max 100MB)
   - File extension (allowed: mp4, avi, mov, pdf, doc, docx, jpg, jpeg, png)
   - User authentication

3. Storage backend saves file:
   - Local: /uploads/{folder}/{uuid}.{ext}
   - S3: {bucket}/{folder}/{uuid}.{ext}

4. Database records file metadata:
   - Original filename
   - Storage path
   - MIME type
   - Size
   - Upload timestamp

5. Returns file URL to client
```

---

## 10. Payment Integration

### 10.1 Payment Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Client    │────►│   API Server  │────►│  Payment     │
│              │     │              │     │  Gateway     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Database    │◄────│   Webhook    │
                     │  (Record)   │     │  (Callback)  │
                     └──────────────┘     └──────────────┘
```

### 10.2 Payment Gateway Integration

**MyFatoorah:**
- Initialize payment with API call
- Redirect user to payment page
- Receive webhook on completion
- Verify and update payment status

**Paymob:**
- Similar flow to MyFatoorah
- Different API endpoints
- Supports iframe integration

### 10.3 Webhook Processing

```python
@router.post("/payments/webhooks/myfatoorah")
async def myfatoorah_webhook(
    request: Request,
    myfatoorah_signature: str | None = Header(...),
    db: Session = Depends(get_db)
) -> PaymentWebhookResponse:
    payload = await request.body()
    
    # 1. Verify signature
    if not verify_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # 2. Parse webhook data
    data = parse_webhook_payload(payload)
    
    # 3. Update payment status
    service = PaymentService(db)
    await service.handle_payment_update(data)
    
    # 4. Trigger后续 actions
    if data.status == "completed":
        await activate_enrollment(data)
        await send_confirmation_email(data)
    
    return PaymentWebhookResponse(status="success")
```

---

## 11. Testing Strategy

### 11.1 Test Types

| Type | Purpose | Tools |
|------|---------|-------|
| Unit Tests | Test individual functions | pytest |
| Integration Tests | Test module interactions | pytest + test DB |
| API Tests | Test HTTP endpoints | httpx + AsyncClient |
| Performance Tests | Load testing | k6 |
| Smoke Tests | Basic functionality | Manual/script |

### 11.2 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Authentication tests
├── test_courses.py          # Course module tests
├── test_quizzes.py          # Quiz module tests
├── test_payments.py         # Payment tests
├── test_enrollments.py      # Enrollment tests
├── test_analytics.py        # Analytics tests
├── test_permissions.py      # Permission tests
├── test_files.py            # File upload tests
├── test_emails.py           # Email tests
├── test_health.py           # Health check tests
└── perf/
    ├── k6_smoke.js          # Smoke tests
    └── k6_realistic.js      # Realistic load
```

### 11.3 Test Fixtures

```python
# conftest.py
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    # Create test database
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
async def test_user(db_session):
    user = User(email="test@example.com", password_hash=hash_password("password"))
    db_session.add(user)
    db_session.commit()
    return user
```

### 11.4 Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_auth.py

# With coverage
pytest --cov=app --cov-report=html

# Performance tests
k6 run tests/perf/k6_smoke.js
```

---

## 12. Deployment Guide

### 12.1 Development Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd lms_backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your settings

# 5. Start with Docker Compose
docker-compose up -d

# 6. Run migrations
alembic upgrade head

# 7. Access API
# http://localhost:8000/docs
```

### 12.2 Docker Compose Services

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://lms:lms@db:5432/lms
      - REDIS_URL=redis://redis:6379/0
    
  celery-worker:
    command: celery -A app.tasks.celery_app worker --loglevel=info
    
  celery-beat:
    command: celery -A app.tasks.celery_app beat --loglevel=info
    
  flower:
    ports:
      - "5555:5555"
    
  db:
    image: postgres:16-alpine
    
  redis:
    image: redis:7-alpine
```

### 12.3 Production Deployment

**Key Production Requirements:**

1. **Environment Variables:**
   ```
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=<64-character-random-string>
   DATABASE_URL=<production-database-url>
   REDIS_URL=<production-redis-url>
   ```

2. **Security Settings:**
   ```python
   # Must be disabled in production
   DEBUG = False
   ENABLE_API_DOCS = False
   STRICT_ROUTER_IMPORTS = True
   ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED = True
   TASKS_FORCE_INLINE = False
   ```

3. **HTTPS/TLS**: Enable SSL/TLS termination
4. **Monitoring**: Configure Sentry
5. **Backups**: Database backup strategy

### 12.4 Container Orchestration (Future)

For scaling beyond single server:
- Kubernetes with Helm charts
- Horizontal pod autoscaling
- Database connection pooling (PgBouncer)
- CDN for static files

---

## 13. Configuration Reference

### 13.1 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Runtime environment | development |
| `DEBUG` | Debug mode | true |
| `DATABASE_URL` | PostgreSQL connection | postgresql://... |
| `REDIS_URL` | Redis connection | redis://... |
| `SECRET_KEY` | JWT signing key | change-me |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | 15 |
| `CORS_ORIGINS` | Allowed origins | localhost:3000 |
| `SENTRY_DSN` | Sentry error tracking | - |
| `FILE_STORAGE_PROVIDER` | local or s3 | local |

### 13.2 Full Configuration

See `docs/tech/20-complete-configuration-reference.md` for complete configuration reference.

---

## Conclusion

This LMS Backend is a comprehensive, production-ready system built with modern technologies and best practices. The architecture supports:

- **Scalability**: Modular design, async operations, caching
- **Maintainability**: Clean code structure, comprehensive documentation
- **Security**: JWT auth, password hashing, rate limiting, input validation
- **Relability**: Background jobs, error tracking, health checks
- **Extensibility**: Modular structure, easy to add new features

The project follows industry standards and provides a solid foundation for building a full-featured Learning Management System.

---

## Related Documentation

- [Architecture Decisions](02-architecture-decisions.md)
- [Database Design](05-database-design.md)
- [API Design Rationale](06-api-design-rationale.md)
- [Security Implementation](07-security-implementation.md)
- [Background Jobs & Celery](08-background-jobs-celery.md)
- [Testing Strategy](09-testing-strategy.md)
- [Deployment Guide](10-deployment-guide.md)
- [Configuration Reference](20-complete-configuration-reference.md)
