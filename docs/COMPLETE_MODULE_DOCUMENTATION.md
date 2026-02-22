# Complete Module Documentation - Every Module Explained

This document provides exhaustive documentation of every module in the LMS Backend, explaining what each component does, how it works, and why certain design decisions were made.

---

## Table of Contents

1. [Core Infrastructure Module](#1-core-infrastructure-module)
2. [Authentication Module](#2-authentication-module)
3. [Users Module](#3-users-module)
4. [Courses Module](#4-courses-module)
5. [Enrollments Module](#5-enrollments-module)
6. [Quizzes Module](#6-quizzes-module)
7. [Analytics Module](#7-analytics-module)
8. [Files Module](#8-files-module)
9. [Certificates Module](#9-certificates-module)
10. [Payments Module](#10-payments-module)
11. [Emails Module](#11-emails-module)
12. [Background Tasks Module](#12-background-tasks-module)

---

## 1. Core Infrastructure Module

**Location**: `app/core/`

The Core Infrastructure module provides fundamental services used by all other modules. It includes configuration, database connectivity, security, and cross-cutting concerns.

### 1.1 Configuration (`app/core/config.py`)

**Purpose**: Centralized configuration management using Pydantic Settings

**What it does:**
- Loads configuration from environment variables
- Validates all settings with type checking
- Provides computed properties for derived values
- Enforces production safety checks

**Key Configuration Categories:**

| Category | Key Variables |
|----------|--------------|
| Application | PROJECT_NAME, VERSION, ENVIRONMENT, DEBUG |
| API | API_V1_PREFIX, METRICS_ENABLED, API_RESPONSE_ENVELOPE_ENABLED |
| Database | DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW |
| Security | SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES |
| Redis | REDIS_URL, CELERY_BROKER_URL |
| Email | SMTP_HOST, SMTP_PORT, EMAIL_FROM |
| Rate Limiting | RATE_LIMIT_REQUESTS_PER_MINUTE |
| File Storage | FILE_STORAGE_PROVIDER, MAX_UPLOAD_MB |
| Payments | MYFATOORAH_*, PAYMOB_*, STRIPE_* |
| Observability | SENTRY_DSN, SENTRY_TRACES_SAMPLE_RATE |

**Why Pydantic Settings?**
- Type validation at startup (fail fast)
- Automatic type coercion (string "true" → boolean True)
- IDE autocomplete support
- Default values with validation
- Documentation through type hints

### 1.2 Database (`app/core/database.py`)

**Purpose**: SQLAlchemy engine and session management

**What it does:**
- Creates SQLAlchemy engine with connection pooling
- Provides session factory
- Defines Base class for all models
- Offers health check functionality

**Key Components:**

```python
# Engine creation with pooling
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Database session dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Why Connection Pooling?**
- Reduces connection overhead (expensive to create)
- Limits concurrent connections (DB_POOL_SIZE)
- Handles overflow (DB_MAX_OVERFLOW)
- `pool_pre_ping=True` checks connection health

**Design Decision: Synchronous vs Async**
- Using synchronous SQLAlchemy (not async)
- Reason: Simpler for this scale, better tooling
- Can migrate to async-sqlalchemy later if needed

### 1.3 Security (`app/core/security.py`)

**Purpose**: JWT token management and password hashing

**What it does:**
- Creates and validates JWT tokens
- Hashes and verifies passwords using bcrypt
- Manages token blacklist for logout
- Provides token type validation

**Token Types:**

| Token Type | Purpose | Expiry (Default) |
|------------|---------|-----------------|
| access | API authentication | 15 minutes |
| refresh | Get new access tokens | 30 days |
| password_reset | Password recovery | 30 minutes |
| email_verification | Verify email address | 24 hours (1440 minutes) |
| mfa_challenge | Two-factor authentication | 10 minutes |

**Password Hashing Design:**
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

**Why bcrypt?**
- Industry-standard (20+ years of security review)
- Configurable work factor (cost parameter)
- Built-in salt generation
- Resistant to rainbow table attacks

**Token Blacklist Implementation:**
- Uses Redis for production (fast, distributed)
- Falls back to in-memory for development
- Stores JWT ID (jti) with TTL matching token expiry

### 1.4 Dependencies (`app/core/dependencies.py`)

**Purpose**: FastAPI dependency injection functions

**What it does:**
- `get_db()`: Database session injection
- `get_current_user()`: Extract and validate user from JWT
- `optional_oauth2_scheme()`: Optional authentication
- `get_current_active_user()`: Verify user is active

**How Authentication Works:**

```python
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # 1. Decode JWT token
    payload = decode_token(token, expected_type=TokenType.ACCESS)
    
    # 2. Extract user ID
    user_id: str = payload.get("sub")
    
    # 3. Fetch user from database
    user = db.get(User, UUID(user_id))
    
    # 4. Validate user exists and is active
    if not user or not user.is_active:
        raise UnauthorizedException()
    
    return user
```

### 1.5 Permissions (`app/core/permissions.py`)

**Purpose**: Role-Based Access Control (RBAC)

**User Roles:**

| Role | Description |
|------|-------------|
| admin | Full system access |
| instructor | Can create and manage courses |
| student | Can enroll and consume content |

**Permission System:**

```python
class Permission(str, Enum):
    CREATE_COURSE = "course:create"
    UPDATE_COURSE = "course:update"
    DELETE_COURSE = "course:delete"
    VIEW_ANALYTICS = "analytics:view"
    MANAGE_ENROLLMENTS = "enrollments:manage"
    MANAGE_USERS = "users:manage"
    MANAGE_QUIZZES = "quizzes:manage"

ROLE_PERMISSIONS = {
    Role.ADMIN: { all permissions },
    Role.INSTRUCTOR: { CREATE_COURSE, UPDATE_COURSE, VIEW_ANALYTICS, MANAGE_QUIZZES },
    Role.STUDENT: { }
}
```

**Why This Design?**
- Explicit permissions are more flexible than role checks
- Easy to add new permissions
- Clear audit trail of what each role can do

### 1.6 Middleware (`app/core/middleware/`)

**Purpose**: HTTP request/response processing

#### Rate Limit Middleware

**What it does:**
- Limits API requests per user/IP
- Uses Redis for distributed rate limiting
- Falls back to in-memory in development

**Configuration:**
```python
RateLimitRule(
    name="auth",
    path_prefixes=["/api/v1/auth/login"],
    limit=10,  # 10 requests
    period_seconds=60,  # per minute
    key_mode="ip"
)
```

**Why Separate Rules?**
- Authentication endpoints need stricter limits (prevent brute force)
- File uploads need different limits (per hour, not per minute)
- User-based limits for authenticated users

#### Security Headers Middleware

**What it adds:**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

#### Response Envelope Middleware

**What it does:**
- Wraps all API responses in consistent format
- Adds success message to responses

**Before:**
```json
{"id": "123", "name": "Course"}
```

**After:**
```json
{
  "success": true,
  "message": "Success",
  "data": {"id": "123", "name": "Course"}
}
```

### 1.7 Health Checks (`app/core/health.py`)

**Purpose**: Application health monitoring

**Endpoints:**
- `/api/v1/health` - Basic liveness check
- `/api/v1/ready` - Readiness check (includes DB and Redis)

---

## 2. Authentication Module

**Location**: `app/modules/auth/`

**Purpose**: Handle all authentication-related operations including registration, login, logout, password reset, email verification, and MFA.

### 2.1 Models

**RefreshToken Model:**
```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[uuid.UUID]  # Primary key
    user_id: Mapped[uuid.UUID]  # Foreign key to User
    token_jti: Mapped[str]  # Unique JWT identifier
    expires_at: Mapped[datetime]  # Expiration time
    revoked_at: Mapped[datetime | None]  # Revocation time
    created_at: Mapped[datetime]  # Creation time
```

**Why separate RefreshToken model?**
- Track valid refresh tokens
- Enable token revocation (logout from all devices)
- Audit token usage
- Limit concurrent sessions

### 2.2 Router Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/register` | POST | User registration |
| `/auth/login` | POST | User login |
| `/auth/token` | POST | OAuth2 token endpoint |
| `/auth/login/mfa` | POST | MFA verification |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/logout` | POST | Logout (revoke tokens) |
| `/auth/forgot-password` | POST | Request password reset |
| `/auth/reset-password` | POST | Reset password |
| `/auth/verify-email/request` | POST | Request email verification |
| `/auth/verify-email/confirm` | POST | Confirm email |
| `/auth/mfa/enable/request` | POST | Request MFA setup |
| `/auth/mfa/enable/confirm` | POST | Confirm MFA setup |
| `/auth/mfa/disable` | POST | Disable MFA |
| `/auth/me` | GET | Get current user |

### 2.3 Authentication Flow

**Registration Flow:**
```
1. User submits email, password, name, role
2. Validate input (email format, password strength)
3. Check if email already exists
4. Hash password with bcrypt
5. Create user in database
6. Generate access + refresh tokens
7. Queue welcome email
8. Return tokens + user data
```

**Login Flow:**
```
1. User submits email, password
2. Look up user by email
3. Verify password hash
4. If MFA enabled: generate MFA challenge, return challenge token
5. If no MFA: generate tokens, update last_login_at
6. Return tokens + user data
```

**Token Refresh Flow:**
```
1. User submits refresh token
2. Validate refresh token (not expired, not revoked)
3. Generate new access token
4. Optionally rotate refresh token (for security)
5. Return new access token
```

### 2.4 MFA Implementation

**Why offer MFA?**
- Extra security layer for sensitive accounts
- Instructor/admin accounts are valuable targets
- Email-based MFA (simpler than authenticator apps)

**MFA Flow:**
```
1. User enables MFA (requires password verification)
2. System generates MFA code, sends to email
3. User enters code to confirm
4. MFA enabled flag set on user

5. Login with password
6. System detects MFA enabled
7. Generates new MFA code, sends to email
8. User enters code
9. System verifies code, grants access
```

---

## 3. Users Module

**Location**: `app/modules/users/`

**Purpose**: Manage user profiles, roles, and user-related operations.

### 3.1 User Model

```python
class User(Base):
    __tablename__ = "users"
    
    # Authentication
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str]
    
    # Profile
    full_name: Mapped[str]
    role: Mapped[str] = mapped_column(String(50), default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Flexible metadata
    profile_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)
    
    # Timestamps
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    last_login_at: Mapped[datetime | None]
    email_verified_at: Mapped[datetime | None]
```

### 3.2 Design Decisions

**Why UUID for IDs?**
- Not guessable (security through obscurity)
- No collisions in distributed systems
- No need to query for max ID

**Why role as string?**
- Flexible (can add new roles without migrations)
- Easy to query by role
- Stored as enum in application code

**Why JSON metadata?**
- Store extra user data without migrations
- Different users can have different fields
- Future-proof for evolving requirements

**Why email_verified_at timestamp?**
- Track when verification happened
- Can filter verified users
- NULL means not verified

### 3.3 Repository Pattern

**Why Repository Pattern?**
- Abstracts data access
- Centralizes query logic
- Makes testing easier (can mock repository)
- Single place for complex queries

```python
class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()
    
    def get_active_users(self, db: Session, skip: int, limit: int) -> list[User]:
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
```

### 3.4 Service Layer

**Why separate Service from Repository?**
- Repository handles data access
- Service handles business logic
- Service can use multiple repositories
- Transaction management in service

---

## 4. Courses Module

**Location**: `app/modules/courses/`

**Purpose**: Manage courses and lessons - the core content of the LMS.

### 4.1 Course Model

```python
class Course(Base):
    __tablename__ = "courses"
    
    # Identity
    id: Mapped[uuid.UUID]
    title: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)  # SEO-friendly URL
    description: Mapped[str | None]
    
    # Relationships
    instructor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    # Categorization
    category: Mapped[str | None] = mapped_column(index=True)
    difficulty_level: Mapped[str | None]  # beginner, intermediate, advanced
    
    # Publishing
    is_published: Mapped[bool] = mapped_column(default=False, index=True)
    
    # Media
    thumbnail_url: Mapped[str | None]
    estimated_duration_minutes: Mapped[int | None]
    
    # Flexible data
    course_metadata: Mapped[dict | None] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### 4.2 Lesson Model

```python
class Lesson(Base):
    __tablename__ = "lessons"
    
    # Identity
    id: Mapped[uuid.UUID]
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str]
    slug: Mapped[str]
    
    # Content
    content_type: Mapped[str]  # video, text, quiz
    content: Mapped[str | None]  # Video URL or text/markdown
    
    # Video
    video_url: Mapped[str | None]
    duration_seconds: Mapped[int | None]
    
    # Organization
    order: Mapped[int]  # Position in course
    is_free: Mapped[bool]  # Preview before enrolling
    
    # Publishing
    is_published: Mapped[bool]
```

### 4.3 Design Decisions

**Why slug for courses?**
- SEO-friendly URLs: `/courses/python-101` vs `/courses/123`
- Human-readable in API documentation
- Unique constraint prevents duplicates

**Why separate Course and Lesson?**
- Course is the container
- Lessons are individual content pieces
- Can reorder lessons without changing IDs
- Each lesson can have its own quiz

**Why content_type field?**
- Different rendering for different types
- Video lessons: show player
- Text lessons: show markdown
- Quiz lessons: show quiz interface

**Why is_free field?**
- Allow previews without enrollment
- Marketing: show first lesson free
- Instructors control what to preview

### 4.4 Repository Pattern

```python
class CourseRepository:
    def get_published_courses(self, db: Session, category: str | None, skip: int, limit: int):
        query = db.query(Course).filter(Course.is_published == True)
        if category:
            query = query.filter(Course.category == category)
        return query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_instructor_courses(self, db: Session, instructor_id: UUID):
        return db.query(Course).filter(Course.instructor_id == instructor_id).all()
```

---

## 5. Enrollments Module

**Location**: `app/modules/enrollments/`

**Purpose**: Track student enrollment in courses and monitor learning progress.

### 5.1 Enrollment Model

```python
class Enrollment(Base):
    __tablename__ = "enrollments"
    
    # Identity
    id: Mapped[uuid.UUID]
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    
    # Status
    status: Mapped[str]  # active, completed, dropped, expired
    
    # Progress
    progress_percentage: Mapped[Decimal]  # 0-100
    completed_lessons_count: Mapped[int]
    total_lessons_count: Mapped[int]
    total_time_spent_seconds: Mapped[int]
    
    # Engagement
    last_accessed_at: Mapped[datetime | None]
    
    # Review
    rating: Mapped[int | None]  # 1-5 stars
    review: Mapped[str | None]
    
    # Certificate
    certificate_issued_at: Mapped[datetime | None]
    
    # Timestamps
    enrolled_at: Mapped[datetime]
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
```

### 5.2 LessonProgress Model

```python
class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    
    # Identity
    id: Mapped[uuid.UUID]
    enrollment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enrollments.id"))
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id"))
    
    # Status
    status: Mapped[str]  # not_started, in_progress, completed
    
    # Time tracking
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    time_spent_seconds: Mapped[int]
    
    # Video progress (for video lessons)
    last_position_seconds: Mapped[int]
    
    # Completion
    completion_percentage: Mapped[Decimal]
    attempts_count: Mapped[int]
```

### 5.3 Design Decisions

**Why separate Enrollment from User-Course relationship?**
- Tracks specific enrollment instance
- Different enrollments have different states
- Can enroll in same course multiple times (if allowed)
- Historical record of progress

**Why track time_spent_seconds?**
- Analytics: know engaged time vs. just logged in
- Identify struggling students
- Compliance requirements (minimum study time)
- Resume functionality (remember video position)

**Why LessonProgress separate table?**
- Granular per-lesson tracking
- Historical activity log
- Better analytics
- Resume from specific lesson

### 5.4 Progress Calculation

```python
def calculate_progress(enrollment: Enrollment) -> Enrollment:
    # Get total lessons in course
    total = enrollment.course.lessons.count()
    
    # Count completed lessons
    completed = enrollment.lesson_progress.filter(
        LessonProgress.status == "completed"
    ).count()
    
    # Calculate percentage
    enrollment.progress_percentage = (completed / total * 100) if total > 0 else 0
    enrollment.completed_lessons_count = completed
    enrollment.total_lessons_count = total
    
    # Mark complete if 100%
    if enrollment.progress_percentage >= 100:
        enrollment.status = "completed"
        enrollment.completed_at = datetime.utcnow()
    
    return enrollment
```

---

## 6. Quizzes Module

**Location**: `app/modules/quizzes/`

**Purpose**: Create and manage quizzes, questions, and attempts with automatic grading.

### 6.1 Quiz Model

```python
class Quiz(Base):
    __tablename__ = "quizzes"
    
    # Identity
    id: Mapped[uuid.UUID]
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id"), unique=True)
    title: Mapped[str]
    description: Mapped[str | None]
    
    # Quiz settings
    quiz_type: Mapped[str]  # practice, graded
    passing_score: Mapped[Decimal]  # e.g., 70.00
    time_limit_minutes: Mapped[int | None]
    max_attempts: Mapped[int | None]
    
    # Display settings
    shuffle_questions: Mapped[bool]
    shuffle_options: Mapped[bool]
    show_correct_answers: Mapped[bool]
    
    # Publishing
    is_published: Mapped[bool]
```

**Why quiz per lesson?**
- Simpler user experience
- Clear assessment after each lesson
- Natural progression in course

### 6.2 Question Model

```python
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    # Identity
    id: Mapped[uuid.UUID]
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id"))
    
    # Content
    question_text: Mapped[str]
    question_type: Mapped[str]  # multiple_choice, true_false, short_answer
    options: Mapped[list[dict] | None]  # JSON array
    correct_answer: Mapped[dict | None]  # JSON
    explanation: Mapped[str | None]
    
    # Points
    points: Mapped[Decimal]
    order: Mapped[int]
```

**Why JSON for options/answers?**
- Flexible for different question types
- Multiple correct answers possible
- Store additional metadata per option

### 6.3 Attempt Model

```python
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    # Identity
    id: Mapped[uuid.UUID]
    enrollment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enrollments.id"))
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id"))
    attempt_number: Mapped[int]
    
    # Status
    status: Mapped[str]  # in_progress, submitted, graded
    
    # Timing
    started_at: Mapped[datetime]
    submitted_at: Mapped[datetime | None]
    graded_at: Mapped[datetime | None]
    time_taken_seconds: Mapped[int | None]
    
    # Scoring
    score: Mapped[Decimal | None]
    max_score: Mapped[Decimal | None]
    percentage: Mapped[Decimal | None]
    is_passed: Mapped[bool | None]
    
    # Answers
    answers: Mapped[list[dict] | None]  # JSON
```

### 6.4 Automatic Grading

```python
def grade_attempt(attempt: QuizAttempt) -> QuizAttempt:
    quiz = attempt.quiz
    questions = quiz.questions.all()
    
    total_score = 0
    max_score = 0
    correct_count = 0
    
    for question, answer in zip(questions, attempt.answers):
        max_score += question.points
        
        if question.question_type == "multiple_choice":
            if answer.get("selected_option") == question.correct_answer.get("correct_option"):
                total_score += question.points
                correct_count += 1
    
    # Calculate percentage
    attempt.score = total_score
    attempt.max_score = max_score
    attempt.percentage = (total_score / max_score * 100) if max_score > 0 else 0
    attempt.is_passed = attempt.percentage >= quiz.passing_score
    
    return attempt
```

**Why auto-grade?**
- Instant feedback for students
- Reduces instructor workload
- Enables practice quizzes
- Scalable to many students

---

## 7. Analytics Module

**Location**: `app/modules/analytics/`

**Purpose**: Provide comprehensive analytics and reporting for all user types.

### 7.1 Analytics Types

**Student Analytics:**
- Current enrollments
- Progress across courses
- Quiz performance history
- Time spent learning
- Certificates earned

**Instructor Analytics:**
- Course enrollment counts
- Student engagement metrics
- Quiz performance by course
- Revenue from courses (if paid)
- Student ratings and reviews

**Admin Analytics:**
- Total users by role
- System-wide enrollment stats
- Revenue across all courses
- Active users over time
- Course completion rates

### 7.2 Services

| Service | Purpose |
|---------|---------|
| StudentAnalyticsService | Individual student metrics |
| CourseAnalyticsService | Course-level aggregations |
| InstructorAnalyticsService | Instructor dashboard data |
| SystemAnalyticsService | Admin system overview |

### 7.3 Design Decisions

**Why separate analytics services?**
- Different data needs per role
- Complex queries isolated
- Easy to add new metrics
- Performance optimization per use case

---

## 8. Files Module

**Location**: `app/modules/files/`

**Purpose**: Handle file uploads and storage with multiple backend support.

### 8.1 UploadedFile Model

```python
class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    # Identity
    id: Mapped[uuid.UUID]
    uploader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    # File info
    filename: Mapped[str]
    original_filename: Mapped[str]
    file_url: Mapped[str]
    storage_path: Mapped[str]
    
    # Metadata
    file_type: Mapped[str | None]
    mime_type: Mapped[str | None]
    file_size: Mapped[int]  # bytes
    
    # Organization
    folder: Mapped[str | None]
    storage_provider: Mapped[str]  # local, azure
    is_public: Mapped[bool]
```

### 8.2 Storage Backends

**Local Storage:**
```python
class LocalStorage(StorageBackend):
    def save(self, folder: str, filename: str, content: bytes) -> str:
        path = Path(UPLOAD_DIR) / folder / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)
```

**Azure Blob Storage:**
```python
class AzureBlobStorage(StorageBackend):
    def save(self, folder: str, filename: str, content: bytes) -> str:
        blob_path = f"{folder}/{filename}"
        self.container_client.upload_blob(name=blob_path, data=content, overwrite=True)
        return blob_path
```

**Why Abstract Storage?**
- Easy to switch between providers
- Can add more providers later if needed
- Testing is easier (mock storage)
- Consistent API regardless of backend

### 8.3 Configuration

```env
FILE_STORAGE_PROVIDER=local  # or azure
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=100
ALLOWED_UPLOAD_EXTENSIONS=mp4,avi,mov,pdf,doc,docx,jpg,jpeg,png
```

---

## 9. Certificates Module

**Location**: `app/modules/certificates/`

**Purpose**: Generate and manage PDF certificates upon course completion.

### 9.1 Certificate Model

```python
class Certificate(Base):
    __tablename__ = "certificates"
    
    # Identity
    id: Mapped[uuid.UUID]
    enrollment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enrollments.id"), unique=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    
    # Certificate data
    certificate_number: Mapped[str] = mapped_column(unique=True)
    pdf_path: Mapped[str]
    
    # Dates
    completion_date: Mapped[datetime]
    issued_at: Mapped[datetime]
    
    # Revocation
    is_revoked: Mapped[bool]
    revoked_at: Mapped[datetime | None]
```

### 9.2 PDF Generation

Uses `fpdf2` library for PDF creation:

```python
class CertificatePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 36)
        self.cell(0, 40, 'Certificate of Completion', 0, 1, 'C')
    
    def add_content(self, student_name: str, course_name: str, date: str):
        self.set_font('Arial', '', 18)
        self.cell(0, 20, 'This is to certify that', 0, 1, 'C')
        
        self.set_font('Arial', 'B', 24)
        self.cell(0, 20, student_name, 0, 1, 'C')
        
        self.set_font('Arial', '', 18)
        self.cell(0, 20, 'has successfully completed', 0, 1, 'C')
        
        self.set_font('Arial', 'B', 24)
        self.cell(0, 20, course_name, 0, 1, 'C')
        
        self.set_font('Arial', '', 14)
        self.cell(0, 15, f'Completed on {date}', 0, 1, 'C')
```

**Why fpdf2?**
- Pure Python (no external dependencies)
- Lightweight
- Easy to customize
- Active maintenance

### 9.3 Certificate Verification

```python
# Public endpoint to verify certificate
GET /api/v1/certificates/verify/{certificate_number}

# Returns:
{
  "valid": true,
  "student_name": "John Doe",
  "course_name": "Python 101",
  "completion_date": "2024-01-15",
  "issued_at": "2024-01-15"
}
```

---

## 10. Payments Module

**Location**: `app/modules/payments/`

**Purpose**: Process payments and manage subscriptions through multiple payment gateways.

### 10.1 Payment Model

```python
class Payment(Base):
    __tablename__ = "payments"
    
    # Identity
    id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    enrollment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("enrollments.id"))
    
    # Amount
    amount: Mapped[Decimal]
    currency: Mapped[str]  # EGP, USD
    
    # Gateway
    gateway: Mapped[str]  # stripe, myfatoorah, paymob
    status: Mapped[str]  # pending, completed, failed, refunded
    transaction_id: Mapped[str | None]
    payment_method: Mapped[str | None]
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]
```

### 10.2 Subscription Model

```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    # Identity
    id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    # Plan
    plan_name: Mapped[str]
    amount: Mapped[Decimal]
    currency: Mapped[str]
    gateway: Mapped[str]
    
    # Status
    status: Mapped[str]  # active, cancelled, expired
    
    # Dates
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    
    # Gateway ID
    gateway_subscription_id: Mapped[str | None]
```

### 10.3 Payment Gateways

**Supported Gateways:**

| Gateway | Region | Features |
|---------|--------|----------|
| MyFatoorah | Middle East | Cards, KNET, MADA, Apple Pay |
| Paymob | Egypt | Cards, Mobile Wallet |
| Stripe | Global | Cards, Apple Pay, Google Pay |

**Why Multiple Gateways?**
- Target different markets
- Different fee structures
- Local payment methods
- Backup if one is down

### 10.4 Webhook Handling

```python
@router.post("/payments/webhooks/myfatoorah")
async def myfatoorah_webhook(
    request: Request,
    myfatoorah_signature: str | None = Header(...),
    db: Session = Depends(get_db)
):
    # 1. Verify webhook signature
    if not verify_signature(payload, signature):
        raise HTTPException(status_code=400)
    
    # 2. Parse payment data
    data = parse_webhook_payload(payload)
    
    # 3. Update payment status
    payment = await update_payment_status(data)
    
    # 4. Trigger后续 actions
    if data.status == "completed":
        await activate_enrollment(data.enrollment_id)
        await send_confirmation_email(data.user_id)
    
    return {"status": "success"}
```

---

## 11. Emails Module

**Location**: `app/modules/emails/`

**Purpose**: Send transactional emails with templates.

### 11.1 Email Types

| Email Type | Trigger | Queue |
|------------|---------|-------|
| Welcome | User registration | emails |
| Password Reset | Password reset request | emails |
| Email Verification | Email verification request | emails |
| MFA Code | MFA login/setup | emails |
| Enrollment Confirmation | Course enrollment | emails |
| Course Completion | 100% progress | emails |
| Quiz Results | Quiz submission (graded) | emails |
| Payment Confirmation | Successful payment | emails |
| Weekly Progress | Scheduled (Monday 9am) | emails |
| Course Reminder | Scheduled (daily 10am) | emails |

### 11.2 Email Service

```python
class EmailService:
    def send_welcome_email(self, email: str, full_name: str) -> str:
        subject = "Welcome to LMS Platform"
        html_content = render_template("welcome.html", full_name=full_name)
        return self._send_email(email, subject, html_content)
    
    def send_enrollment_confirmation_email(
        self,
        email: str,
        student_name: str,
        course_title: str,
        ...
    ) -> str:
        subject = f"You're enrolled in {course_title}"
        html_content = render_template(
            "enrollment.html",
            student_name=student_name,
            course_title=course_title,
            ...
        )
        return self._send_email(email, subject, html_content)
```

### 11.3 Why Queue Emails?

- Don't block API response
- Retry on failure
- Rate limiting (don't overwhelm SMTP server)
- Background processing for bulk emails

---

## 12. Background Tasks Module

**Location**: `app/tasks/`

**Purpose**: Handle long-running or deferred tasks asynchronously.

### 12.1 Celery Configuration

```python
celery_app = Celery(
    "lms_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.progress_tasks",
        "app.tasks.certificate_tasks",
        "app.tasks.webhook_tasks",
    ]
)

celery_app.conf.update(
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.progress_tasks.*": {"queue": "progress"},
        "app.tasks.certificate_tasks.*": {"queue": "certificates"},
        "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
    task_acks_late=True,  # Acknowledge after processing
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)
```

### 12.2 Task Queues

| Queue | Purpose | Example Tasks |
|-------|---------|--------------|
| emails | All email sending | Welcome, reset, notifications |
| certificates | PDF generation | Certificate creation |
| webhooks | Payment callbacks | Payment confirmation |
| progress | Bulk calculations | Progress recalculation |

### 12.3 Scheduled Tasks

```python
beat_schedule={
    "weekly-progress-report": {
        "task": "app.tasks.email_tasks.send_weekly_progress_report",
        "schedule": crontab(minute=0, hour=9, day_of_week="monday"),
    },
    "daily-course-reminders": {
        "task": "app.tasks.email_tasks.send_course_reminders",
        "schedule": crontab(minute=0, hour=10),
    },
}
```

### 12.4 Retry Logic

```python
@celery_app.task(
    autoretry_for=(SMTPException, TimeoutError, OSError),
    retry_backoff=True,  # Exponential backoff
    retry_jitter=True,   # Random jitter
    retry_kwargs={"max_retries": 5}
)
def send_email_task(email: str, subject: str, body: str):
    # Email sending logic
```

**Why Exponential Backoff?**
- Don't overwhelm failing service
- Give time to recover
- Jitter prevents thundering herd

---

## Summary

This document covered every module in the LMS Backend:

| Module | Files | Key Features |
|--------|-------|-------------|
| Core | config.py, database.py, security.py, middleware/ | Configuration, DB, Auth, Security |
| Auth | models.py, router.py, service.py | JWT, MFA, Password reset |
| Users | models.py, router.py, repository.py, service.py | User management |
| Courses | models/, routers/, services/, repositories/ | Course & lesson management |
| Enrollments | models.py, router.py, service.py, repository.py | Enrollment & progress |
| Quizzes | models/, routers/, services/, repositories/ | Quiz & grading |
| Analytics | router.py, services/ | Dashboards & metrics |
| Files | models.py, router.py, service.py, storage/ | File upload & storage |
| Certificates | models.py, router.py, service.py | PDF generation |
| Payments | models.py, router.py, service.py, *_service.py | Multi-gateway payments |
| Emails | service.py | Transactional emails |
| Tasks | celery_app.py, *_tasks.py | Background processing |

Each module follows consistent patterns:
- Models for data
- Routers for HTTP endpoints
- Services for business logic
- Repositories for data access
- Celery tasks for async operations
