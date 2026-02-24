# Module Reference Documentation

This document provides comprehensive documentation for every module in the LMS Backend application.

## Table of Contents

1. [Auth Module](#auth-module)
2. [Users Module](#users-module)
3. [Courses Module](#courses-module)
4. [Enrollments Module](#enrollments-module)
5. [Quizzes Module](#quizzes-module)
6. [Assignments Module](#assignments-module)
7. [Files Module](#files-module)
8. [Certificates Module](#certificates-module)
9. [Payments Module](#payments-module)
10. [Analytics Module](#analytics-module)
11. [Admin Module](#admin-module)
12. [Instructors Module](#instructors-module)
13. [WebSocket Module](#websocket-module)

---

## Auth Module

**Location**: `app/modules/auth/`

### Purpose and Business Logic

The Auth module handles all authentication-related functionality including:
- User login/logout
- Token management (access and refresh tokens)
- Password reset and recovery
- Email verification
- Multi-factor authentication (MFA)
- Account lockout after failed attempts

### Architecture

```
auth/
├── __init__.py
├── models.py              # RefreshToken model
├── schemas.py             # Request/response schemas (JWT-based)
├── schemas_cookie.py     # Request/response schemas (cookie-based)
├── service.py            # Authentication business logic
├── service_cookie.py     # Cookie-based auth service
├── router.py             # JWT-based auth routes
└── router_cookie.py      # Cookie-based auth routes
```

### Models

#### RefreshToken

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: UUID (primary key)
    user_id: UUID (foreign key to users)
    token_jti: str (JWT ID for tracking)
    expires_at: datetime
    revoked_at: datetime (nullable)
    created_at: datetime
```

**Design Decision**: Refresh tokens are stored in the database to enable:
- Token revocation
- User session management
- Tracking of active sessions

### Schemas

#### Request Schemas

```python
# Login request
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Token refresh request  
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Password reset request
class PasswordResetRequest(BaseModel):
    email: EmailStr

# MFA verification
class MFAVerifyRequest(BaseModel):
    challenge_token: str
    code: str  # 6-digit numeric code
```

#### Response Schemas

```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int  # seconds

class MFAChallengeResponse(BaseModel):
    challenge_token: str
    code: str  # For testing/demo purposes
    expires_in_seconds: int
```

### Services

#### AuthService

The main authentication service providing:

**Login Flow**:
1. Check account lockout status
2. Authenticate user credentials
3. Reset failed attempts on success
4. If MFA enabled, create challenge and return
5. Otherwise, issue tokens and update last login

**Token Refresh Flow**:
1. Validate refresh token
2. Verify user exists and is active
3. Revoke old refresh token
4. Issue new access and refresh tokens
5. Optionally blacklist old access token

**Password Reset Flow**:
1. Find user by email
2. Generate password reset token
3. Return email/name/token (email sent via Celery task)

**MFA Flow**:
1. Request: Generate 6-digit code, store in cache with TTL
2. Confirm: Verify code, enable MFA on user record
3. Login: Create challenge token, require code verification

### API Endpoints

#### JWT-Based Routes (`app/modules/auth/router.py`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/auth/token` | Login and get tokens | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | Logout and revoke tokens | Yes |
| POST | `/auth/login/mfa` | Verify MFA code | No |
| POST | `/auth/password/reset` | Request password reset | No |
| POST | `/auth/password/reset/confirm` | Confirm password reset | No |
| POST | `/auth/email/verify` | Request email verification | No |
| POST | `/auth/email/verify/confirm` | Confirm email verification | Yes |
| POST | `/auth/mfa/enable` | Enable MFA | Yes |
| POST | `/auth/mfa/disable` | Disable MFA | Yes |

#### Cookie-Based Routes (`app/modules/auth/router_cookie.py`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/auth/login-cookie` | Login with cookie response | No |
| POST | `/auth/refresh-cookie` | Refresh with cookie | No |
| POST | `/auth/logout-cookie` | Logout and clear cookies | Yes |

### Key Design Decisions

#### 1. Dual Auth Implementation

**Decision**: Support both JWT (Bearer token) and cookie-based authentication.

**Rationale**:
- JWT: Better for API-first clients, mobile apps
- Cookies: Better for browser-based apps, built-in CSRF protection

**Implementation**:
- Development uses JWT (`app/modules/auth/router.py`)
- Production uses cookies (`app/modules/auth/router_cookie.py`)
- Selection made in `app/api/v1/api.py` based on `ENVIRONMENT`

#### 2. Token Storage Strategy

**Decision**: Store refresh tokens in database, access tokens in memory.

**Rationale**:
- Refresh tokens need to be revocable (logout, password change)
- Access tokens are short-lived (15 min), can use in-memory blacklist
- Reduces database load for high-frequency requests

#### 3. MFA Implementation

**Decision**: Use TOTP-like implementation with cached codes.

**Rationale**:
- Simpler than real TOTP (no authenticator app needed)
- Codes sent via email or displayed for setup
- Cache-based for simplicity and speed

---

## Users Module

**Location**: `app/modules/users/`

### Purpose and Business Logic

The Users module handles:
- User profile management
- User creation and retrieval
- User search and listing
- Profile metadata management

### Architecture

```
users/
├── __init__.py
├── models.py              # User model
├── schemas.py             # Request/response schemas
├── router.py              # API routes
├── repositories/
│   ├── __init__.py
│   └── user_repository.py # Data access layer
└── services/
    ├── __init__.py
    └── user_service.py    # Business logic
```

### Models

#### User

```python
class User(Base):
    __tablename__ = "users"
    
    id: UUID (primary key)
    email: str (unique, indexed)
    password_hash: str
    full_name: str
    role: str ('admin', 'instructor', 'student')
    is_active: bool
    mfa_enabled: bool
    profile_metadata: dict (JSON)
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime (nullable)
    email_verified_at: datetime (nullable)
    
    # Relationships
    refresh_tokens: List[RefreshToken]
    courses: List[Course] (as instructor)
    enrollments: List[Enrollment]
    payments: List[Payment]
    orders: List[Order]
    instructor: Instructor (one-to-one)
    admin: Admin (one-to-one)
```

### Schemas

```python
# User response
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: datetime | None

# User create
class UserCreate(BaseModel):
    email: EmailStr
    password: str (min 8 chars)
    full_name: str
    role: str = 'student'

# User update
class UserUpdate(BaseModel):
    full_name: str | None
    profile_metadata: dict | None
```

### Services

#### UserService

**Key Methods**:

```python
class UserService:
    def authenticate(self, email: str, password: str) -> User:
        """Authenticate user with email/password"""
        
    def create_user(self, user_data: UserCreate) -> User:
        """Create new user"""
        
    def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID"""
        
    def get_by_email(self, email: str) -> User | None:
        """Get user by email"""
        
    def update_user(self, user_id: UUID, updates: dict) -> User:
        """Update user profile"""
        
    def delete_user(self, user_id: UUID) -> None:
        """Soft or hard delete user"""
```

### API Endpoints

| Method | Path | Description | Auth Required | Roles |
|--------|------|-------------|---------------|-------|
| GET | `/users/me` | Get current user profile | Yes | All |
| PUT | `/users/me` | Update current user profile | Yes | All |
| GET | `/users/{user_id}` | Get user by ID | Yes | Admin |
| GET | `/users/` | List users (paginated) | Yes | Admin, Instructor |
| POST | `/users/` | Create user | No* | - |
| DELETE | `/users/{user_id}` | Delete user | Yes | Admin |

*Public registration can be enabled via `ALLOW_PUBLIC_ROLE_REGISTRATION` setting.

---

## Courses Module

**Location**: `app/modules/courses/`

### Purpose and Business Logic

The Courses module manages:
- Course CRUD operations
- Course categories and metadata
- Course publishing workflow
- Instructor course management

### Architecture

```
courses/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── course.py         # Course model
│   └── lesson.py         # Lesson model
├── schemas/
│   ├── __init__.py
│   ├── course.py         # Course schemas
│   └── lesson.py         # Lesson schemas
├── repositories/
│   ├── __init__.py
│   ├── course_repository.py
│   └── lesson_repository.py
├── routers/
│   ├── __init__.py
│   ├── course_router.py
│   └── lesson_router.py
└── services/
    ├── __init__.py
    ├── course_service.py
    └── lesson_service.py
```

### Models

#### Course

```python
class Course(Base):
    __tablename__ = "courses"
    
    id: UUID (primary key)
    title: str
    description: str
    short_description: str
    thumbnail_url: str | None
    price: Decimal
    is_published: bool
    is_free: bool
    category: str | None
    tags: list[str]
    instructor_id: UUID (foreign key)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    instructor: User
    lessons: List[Lesson] (one-to-many)
    enrollments: List[Enrollment]
```

#### Lesson

```python
class Lesson(Base):
    __tablename__ = "lessons"
    
    id: UUID (primary key)
    title: str
    content: str (HTML/Markdown)
    video_url: str | None
    duration_minutes: int
    order: int
    is_published: bool
    course_id: UUID (foreign key)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    course: Course
```

### Schemas

```python
# Course response
class CourseResponse(BaseModel):
    id: UUID
    title: str
    description: str
    short_description: str
    thumbnail_url: str | None
    price: Decimal
    is_published: bool
    is_free: bool
    category: str | None
    tags: list[str]
    instructor_id: UUID
    lessons_count: int
    enrollments_count: int
    created_at: datetime

# Course with lessons
class CourseDetailResponse(CourseResponse):
    lessons: list[LessonResponse]
```

### Services

#### CourseService

**Key Methods**:

```python
class CourseService:
    def create_course(self, data: CourseCreate, instructor_id: UUID) -> Course:
        """Create new course"""
        
    def get_course(self, course_id: UUID) -> Course | None:
        """Get course by ID"""
        
    def list_courses(self, filters: CourseFilter, pagination: tuple) -> list[Course]:
        """List courses with filters"""
        
    def update_course(self, course_id: UUID, updates: dict) -> Course:
        """Update course"""
        
    def publish_course(self, course_id: UUID) -> Course:
        """Publish course"""
        
    def get_instructor_courses(self, instructor_id: UUID) -> list[Course]:
        """Get courses by instructor"""
```

### API Endpoints

| Method | Path | Description | Auth Required | Roles |
|--------|------|-------------|---------------|-------|
| GET | `/courses/` | List courses | No | - |
| GET | `/courses/{course_id}` | Get course details | No* | - |
| POST | `/courses/` | Create course | Yes | Instructor, Admin |
| PUT | `/courses/{course_id}` | Update course | Yes | Instructor (own), Admin |
| DELETE | `/courses/{course_id}` | Delete course | Yes | Instructor (own), Admin |
| POST | `/courses/{course_id}/publish` | Publish course | Yes | Instructor (own), Admin |

*Course must be published to view without auth.

---

## Enrollments Module

**Location**: `app/modules/enrollments/`

### Purpose and Business Logic

The Enrollments module handles:
- Student course enrollments
- Enrollment tracking and progress
- Enrollment history
- Completion certificates trigger

### Architecture

```
enrollments/
├── __init__.py
├── models.py              # Enrollment model
├── schemas.py             # Request/response schemas
├── router.py              # API routes
├── repository.py          # Data access
└── service.py             # Business logic
```

### Models

#### Enrollment

```python
class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id: UUID (primary key)
    user_id: UUID (foreign key)
    course_id: UUID (foreign key)
    enrolled_at: datetime
    completed_at: datetime | None
    progress_percentage: int (0-100)
    is_active: bool
    payment_id: UUID | None (foreign key)
    
    # Relationships
    student: User
    course: Course
    payment: Payment | None
```

### Schemas

```python
class EnrollmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID
    enrolled_at: datetime
    completed_at: datetime | None
    progress_percentage: int
    is_active: bool

class EnrollmentCreate(BaseModel):
    course_id: UUID
    payment_id: UUID | None  # For paid courses
```

### Services

```python
class EnrollmentService:
    def enroll_student(self, user_id: UUID, course_id: UUID, payment_id: UUID | None = None) -> Enrollment:
        """Enroll student in course"""
        
    def get_enrollment(self, enrollment_id: UUID) -> Enrollment | None:
        """Get enrollment by ID"""
        
    def get_user_enrollments(self, user_id: UUID) -> list[Enrollment]:
        """Get user's enrollments"""
        
    def update_progress(self, enrollment_id: UUID, lesson_id: UUID) -> Enrollment:
        """Update progress after lesson completion"""
        
    def mark_complete(self, enrollment_id: UUID) -> Enrollment:
        """Mark course as complete"""
```

### API Endpoints

| Method | Path | Description | Auth Required | Roles |
|--------|------|-------------|---------------|-------|
| GET | `/enrollments/` | List my enrollments | Yes | Student |
| GET | `/enrollments/{enrollment_id}` | Get enrollment | Yes | Student (own), Admin |
| POST | `/enrollments/` | Enroll in course | Yes | Student |
| PUT | `/enrollments/{enrollment_id}/progress` | Update progress | Yes | Student |
| POST | `/enrollments/{enrollment_id}/complete` | Mark complete | Yes | Student |

---

## Quizzes Module

**Location**: `app/modules/quizzes/`

### Purpose and Business Logic

The Quizzes module handles:
- Quiz creation and management
- Question types (multiple choice, true/false, etc.)
- Quiz attempts and scoring
- Time limits and retake policies

### Architecture

```
quizzes/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── quiz.py
│   ├── question.py
│   └── attempt.py
├── schemas/
│   ├── __init__.py
│   └── quiz.py
├── routers/
│   ├── __init__.py
│   ├── quiz_router.py
│   ├── question_router.py
│   └── attempt_router.py
└── services/
    ├── __init__.py
    ├── quiz_service.py
    ├── question_service.py
    └── attempt_service.py
```

### Models

#### Quiz

```python
class Quiz(Base):
    __tablename__ = "quizzes"
    
    id: UUID
    title: str
    description: str | None
    course_id: UUID (foreign key)
    lesson_id: UUID | None (foreign key)
    time_limit_minutes: int | None
    passing_score_percentage: int
    max_attempts: int
    is_published: bool
    created_at: datetime
    
    # Relationships
    course: Course
    questions: List[Question]
    attempts: List[QuizAttempt]
```

#### Question

```python
class Question(Base):
    __tablename__ = "questions"
    
    id: UUID
    quiz_id: UUID (foreign key)
    question_text: str
    question_type: str ('multiple_choice', 'true_false', 'short_answer')
    options: list[dict]  # For multiple choice
    correct_answer: str
    points: int
    order: int
    
    # Relationships
    quiz: Quiz
```

#### QuizAttempt

```python
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id: UUID
    quiz_id: UUID (foreign key)
    user_id: UUID (foreign key)
    started_at: datetime
    submitted_at: datetime | None
    score: int | None
    passed: bool | None
    answers: dict  # User's answers
    
    # Relationships
    quiz: Quiz
    user: User
```

### API Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/quizzes/` | List quizzes | Yes |
| GET | `/quizzes/{quiz_id}` | Get quiz details | Yes |
| POST | `/quizzes/` | Create quiz | Yes (Instructor) |
| PUT | `/quizzes/{quiz_id}` | Update quiz | Yes (Instructor) |
| POST | `/quizzes/{quiz_id}/attempts` | Start attempt | Yes |
| POST | `/quizzes/{quiz_id}/attempts/{attempt_id}/submit` | Submit attempt | Yes |
| GET | `/quizzes/{quiz_id}/attempts/` | List attempts | Yes |

---

## Assignments Module

**Location**: `app/modules/assignments/`

### Purpose and Business Logic

The Assignments module handles:
- Assignment creation by instructors
- File-based submissions by students
- Grading and feedback
- Submission deadlines and late penalties

### Architecture

```
assignments/
├── __init__.py
├── models.py              # Assignment, Submission models
├── schemas/
│   ├── __init__.py
│   └── schemas.py         # Request/response schemas
├── repositories/
│   ├── __init__.py
│   └── repositories.py    # Data access
├── routers/
│   ├── __init__.py
│   └── routers.py         # API routes
└── services/
    ├── __init__.py
    └── services.py        # Business logic
```

### Models

#### Assignment

```python
class Assignment(Base):
    __tablename__ = "assignments"
    
    id: UUID
    title: str
    description: str
    course_id: UUID (foreign key)
    lesson_id: UUID | None
    due_date: datetime | None
    points: int
    allow_late_submission: bool
    late_penalty_percentage: int
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    course: Course
    instructor: User
    submissions: List[Submission]
```

#### Submission

```python
class Submission(Base):
    __tablename__ = "submissions"
    
    id: UUID
    assignment_id: UUID (foreign key)
    user_id: UUID (foreign key)
    submitted_at: datetime
    content: str | None
    file_url: str | None
    grade: int | None
    feedback: str | None
    graded_at: datetime | None
    graded_by: UUID | None
    
    # Relationships
    assignment: Assignment
    student: User
    grader: User | None
```

### Services

```python
class AssignmentService:
    def create_assignment(self, data: AssignmentCreate, instructor_id: UUID) -> Assignment:
        """Create new assignment"""
        
    def submit_assignment(self, assignment_id: UUID, user_id: UUID, content: str, file) -> Submission:
        """Submit assignment"""
        
    def grade_submission(self, submission_id: UUID, grade: int, feedback: str, grader_id: UUID) -> Submission:
        """Grade submission"""
        
    def get_submissions(self, assignment_id: UUID) -> list[Submission]:
        """Get all submissions for assignment"""
```

### API Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/assignments/` | List assignments | Yes |
| GET | `/assignments/{assignment_id}` | Get assignment | Yes |
| POST | `/assignments/` | Create assignment | Yes (Instructor) |
| PUT | `/assignments/{assignment_id}` | Update assignment | Yes (Instructor) |
| POST | `/assignments/{assignment_id}/submit` | Submit assignment | Yes (Student) |
| GET | `/assignments/{assignment_id}/submissions` | List submissions | Yes (Instructor) |
| POST | `/assignments/submissions/{submission_id}/grade` | Grade submission | Yes (Instructor) |

---

## Files Module

**Location**: `app/modules/files/`

### Purpose and Business Logic

The Files module handles:
- File uploads (course materials, assignments, user avatars)
- Multiple storage backends (local, Azure Blob)
- File type validation
- Signed URL generation for secure downloads
- File metadata management

### Architecture

```
files/
├── __init__.py
├── models.py              # File metadata model
├── schemas.py             # Request/response schemas
├── router.py              # API routes
├── service.py             # Business logic
└── storage/
    ├── __init__.py
    ├── base.py           # Abstract storage interface
    ├── local.py          # Local filesystem storage
    └── azure_blob.py     # Azure Blob Storage
```

### Models

```python
class File(Base):
    __tablename__ = "files"
    
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    storage_provider: str ('local', 'azure')
    storage_path: str
    uploaded_by: UUID (foreign key)
    course_id: UUID | None
    assignment_id: UUID | None
    created_at: datetime
    
    # Relationships
    uploader: User
```

### Storage Backends

#### Local Storage (`storage/local.py`)

```python
class LocalStorage(BaseStorage):
    """Store files on local filesystem"""
    
    def upload(self, file: UploadFile, path: str) -> str:
        """Upload file to local storage"""
        
    def download(self, path: str) -> bytes:
        """Download file from local storage"""
        
    def delete(self, path: str) -> None:
        """Delete file from local storage"""
        
    def get_url(self, path: str, expires: int) -> str:
        """Get download URL (serves locally)"""
```

#### Azure Blob Storage (`storage/azure_blob.py`)

```python
class AzureBlobStorage(BaseStorage):
    """Store files in Azure Blob Storage"""
    
    def upload(self, file: UploadFile, path: str) -> str:
        """Upload to Azure Blob"""
        
    def download(self, path: str) -> bytes:
        """Download from Azure Blob"""
        
    def delete(self, path: str) -> None:
        """Delete from Azure Blob"""
        
    def get_url(self, path: str, expires: int) -> str:
        """Generate SAS token URL"""
```

### Configuration

```python
# Settings in app/core/config.py
FILE_STORAGE_PROVIDER: Literal["local", "azure"] = "azure"
AZURE_STORAGE_CONNECTION_STRING: str | None
AZURE_STORAGE_CONTAINER_NAME: str | None
FILE_DOWNLOAD_URL_EXPIRE_SECONDS: int = 900
```

### API Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/files/upload` | Upload file | Yes |
| GET | `/files/{file_id}` | Get file metadata | Yes |
| GET | `/files/{file_id}/download` | Download file | Yes |
| DELETE | `/files/{file_id}` | Delete file | Yes |

---

## Certificates Module

**Location**: `app/modules/certificates/`

### Purpose and Business Logic

The Certificates module handles:
- Certificate generation upon course completion
- PDF certificate creation
- Unique certificate verification codes
- Public certificate verification API
- Certificate templates

### Architecture

```
certificates/
├── __init__.py
├── models.py              # Certificate model
├── schemas.py             # Request/response schemas
├── router.py              # Private API routes
├── routers/
│   ├── __init__.py
│   └── certificate_public_router.py  # Public verification
└── service.py             # Business logic + PDF generation
```

### Models

```python
class Certificate(Base):
    __tablename__ = "certificates"
    
    id: UUID
    user_id: UUID (foreign key)
    course_id: UUID (foreign key)
    certificate_number: str (unique)
    issued_at: datetime
    pdf_url: str | None
    
    # Relationships
    user: User
    course: Course
```

### Certificate Generation Flow

```python
class CertificateService:
    def generate_certificate(self, enrollment_id: UUID) -> Certificate:
        """Generate certificate for completed enrollment"""
        # 1. Verify enrollment is complete
        # 2. Check if certificate already exists
        # 3. Generate unique certificate number
        # 4. Create PDF with reportlab
        # 5. Upload PDF to storage
        # 6. Save certificate record
        # 7. Dispatch email notification (Celery)
```

### PDF Generation

Uses `reportlab` for PDF creation:

```python
def create_certificate_pdf(certificate: Certificate, course: Course, user: User) -> bytes:
    """Generate PDF certificate"""
    # Create PDF with:
    # - Course title
    # - Student name
    # - Completion date
    # - Certificate number
    # - Verification URL
    # - Instructor signature
```

### API Endpoints

#### Private Routes

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/certificates/` | List my certificates | Yes |
| GET | `/certificates/{certificate_id}` | Get certificate | Yes |
| POST | `/certificates/generate/{enrollment_id}` | Generate certificate | Yes |

#### Public Routes

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/certificates/verify/{certificate_number}` | Verify certificate | No |

---

## Payments Module

**Location**: `app/modules/payments/`

### Purpose and Business Logic

The Payments module handles:
- Payment processing via Stripe
- Order creation and management
- Webhook handling for payment events
- Refund processing

### Architecture

```
payments/
├── __init__.py
├── models.py              # Payment, Order models
├── schemas.py             # Request/response schemas
├── router.py              # API routes
├── routers/
│   ├── __init__.py
│   └── payment_router.py
└── service.py             # Business logic + Stripe integration
```

### Models

#### Order

```python
class Order(Base):
    __tablename__ = "orders"
    
    id: UUID
    user_id: UUID (foreign key)
    course_id: UUID (foreign key)
    amount: int (cents)
    currency: str
    status: str ('pending', 'completed', 'failed', 'refunded')
    stripe_payment_intent_id: str | None
    created_at: datetime
    completed_at: datetime | None
    
    # Relationships
    user: User
    course: Course
    payment: Payment
```

#### Payment

```python
class Payment(Base):
    __tablename__ = "payments"
    
    id: UUID
    order_id: UUID (foreign key)
    user_id: UUID (foreign key)
    amount: int
    currency: str
    payment_method: str
    stripe_payment_method_id: str | None
    status: str
    transaction_id: str | None
    metadata: dict
    created_at: datetime
    
    # Relationships
    order: Order
    user: User
```

### Stripe Integration

```python
class PaymentService:
    def create_payment_intent(self, order_id: UUID) -> dict:
        """Create Stripe PaymentIntent"""
        
    def confirm_payment(self, payment_intent_id: str) -> Payment:
        """Confirm payment from Stripe"""
        
    def handle_webhook(self, payload: bytes, signature: str) -> None:
        """Handle Stripe webhook events"""
        
    def create_refund(self, payment_id: UUID) -> dict:
        """Process refund"""
```

### API Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/payments/create-intent/{order_id}` | Create payment intent | Yes |
| POST | `/payments/webhook` | Stripe webhook | No (signed) |
| GET | `/payments/{payment_id}` | Get payment details | Yes |
| POST | `/payments/{payment_id}/refund` | Refund payment | Yes (Admin) |

---

## Analytics Module

**Location**: `app/modules/analytics/`

### Purpose and Business Logic

The Analytics module provides:
- Course enrollment analytics
- Student progress tracking
- Revenue reports
- Instructor performance metrics
- Custom date range filtering

### Architecture

```
analytics/
├── __init__.py
├── schemas.py             # Response schemas
└── router.py              # API routes
```

### API Endpoints

| Method | Path | Description | Auth Required | Roles |
|--------|------|-------------|---------------|-------|
| GET | `/analytics/overview` | Dashboard overview | Yes | Admin |
| GET | `/analytics/courses/{course_id}` | Course analytics | Yes | Instructor, Admin |
| GET | `/analytics/enrollments` | Enrollment stats | Yes | Admin |
| GET | `/analytics/revenue` | Revenue report | Yes | Admin |
| GET | `/analytics/users/{user_id}` | User activity | Yes | User (own), Admin |

### Response Schemas

```python
class AnalyticsOverview(BaseModel):
    total_users: int
    total_courses: int
    total_enrollments: int
    total_revenue: int
    active_users_30d: int
    new_enrollments_30d: int

class CourseAnalytics(BaseModel):
    course_id: UUID
    total_enrollments: int
    completion_rate: float
    average_progress: float
    average_rating: float | None
    revenue: int
```

---

## Admin Module

**Location**: `app/modules/admin/`

### Purpose and Business Logic

The Admin module provides:
- Administrative user management
- System-wide configuration
- User impersonation (for support)
- Audit logging
- System health monitoring

### Architecture

```
admin/
├── __init__.py
├── models.py              # Admin-specific models
├── schemas.py             # Admin request/response schemas
├── router.py              # API routes
└── service.py             # Admin business logic
```

### Models

#### Admin

```python
class Admin(Base):
    __tablename__ = "admins"
    
    id: UUID
    user_id: UUID (foreign key)
    permissions: list[str]
    created_at: datetime
    
    # Relationships
    user: User
```

### API Endpoints

| Method | Path | Description | Auth Required | Roles |
|--------|------|-------------|---------------|-------|
| GET | `/admin/users` | List all users | Yes | Admin |
| PUT | `/admin/users/{user_id}` | Update user | Yes | Admin |
| POST | `/admin/users/{user_id}/impersonate` | Impersonate user | Yes | Admin |
| GET | `/admin/audit-logs` | View audit logs | Yes | Admin |
| GET | `/admin/stats` | System statistics | Yes | Admin |

---

## Instructors Module

**Location**: `app/modules/instructors/`

### Purpose and Business Logic

The Instructors module handles:
- Instructor profiles
- Instructor dashboard
- Course management specific to instructors
- Student metrics per course

### Architecture

```
instructors/
├── __init__.py
├── models.py              # Instructor model
├── schemas.py             # Request/response schemas
├── router.py              # API routes
└── service.py             # Business logic
```

### Models

```python
class Instructor(Base):
    __tablename__ = "instructors"
    
    id: UUID
    user_id: UUID (foreign key)
    title: str | None
    bio: str | None
    expertise: list[str]
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    user: User
    courses: List[Course]
```

### API Endpoints

| Method | Path | Description | Auth Required | Roles |
|--------|------|-------------|---------------|-------|
| GET | `/instructors/me` | Get my instructor profile | Yes | Instructor |
| PUT | `/instructors/me` | Update profile | Yes | Instructor |
| GET | `/instructors/me/dashboard` | Instructor dashboard | Yes | Instructor |
| GET | `/instructors/{instructor_id}` | Public instructor profile | No | - |

---

## WebSocket Module

**Location**: `app/modules/websocket/`

### Purpose and Business Logic

The WebSocket module provides:
- Real-time notifications
- Live course updates
- Chat functionality
- Progress synchronization

### Architecture

```
websocket/
├── __init__.py
├── middleware.py          # WebSocket middleware
├── models/
│   ├── __init__.py
│   ├── connection.py      # Connection model
│   └── message.py        # Message model
├── routers/
│   ├── __init__.py
│   └── websocket_router.py
└── services/
    ├── __init__.py
    ├── client_registry.py    # Manage connections
    ├── broadcast_service.py   # Broadcast messages
    └── business_service.py   # Business logic
```

### Connection Management

```python
class ClientRegistry:
    """Manages active WebSocket connections"""
    
    def register(self, user_id: UUID, websocket: WebSocket) -> None:
        """Register new connection"""
        
    def unregister(self, user_id: UUID) -> None:
        """Remove connection"""
        
    def get_user_connection(self, user_id: UUID) -> WebSocket | None:
        """Get user's connection"""
        
    def broadcast_to_course(self, course_id: UUID, message: dict) -> None:
        """Broadcast to all users in course"""
```

### Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `lesson_completed` | Server → Client | `{lesson_id, progress}` |
| `course_updated` | Server → Client | `{course_id, changes}` |
| `new_enrollment` | Server → Client | `{course_id, student_name}` |
| `assignment_graded` | Server → Client | `{assignment_id, grade}` |

### API Endpoint

| Path | Description |
|------|-------------|
| `/ws/notifications` | WebSocket for real-time notifications |

### Authentication

WebSocket connections authenticated via JWT in query string:

```
wss://api.example.com/ws/notifications?token=<jwt_token>
```

---

## Cross-Module Patterns

### Repository Pattern

All modules follow the repository pattern for data access:

```python
class CourseRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, course_id: UUID) -> Course | None:
        return self.db.query(Course).filter(Course.id == course_id).first()
    
    def list(self, filters: CourseFilter, skip: int, limit: int) -> list[Course]:
        query = self.db.query(Course)
        # Apply filters
        return query.offset(skip).limit(limit).all()
```

### Service Layer Pattern

Business logic isolated in service classes:

```python
class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CourseRepository(db)
    
    def create_course(self, data: CourseCreate, instructor_id: UUID) -> Course:
        # Business logic
        # Validation
        # Authorization
        # Return result
```

### Dependency Injection

FastAPI dependencies used throughout:

```python
def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    return CourseService(db)

@router.get("/courses/{course_id}")
def get_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service)
):
    return service.get_course(course_id)
```

---

## Module Dependencies Summary

```
Auth ──────┬──► Users (uses User model)
           │
           ├──► Courses (instructor verification)
           │
           ├──► Enrollments (user verification)
           │
           ├──► Payments (user verification)
           │
           └──► Certificates (user verification)

Users ─────┬──► Courses (instructor relationship)
           │
           ├──► Enrollments (student relationship)
           │
           ├──► Assignments (student/instructor)
           │
           └──► Files (uploader relationship)

Courses ───┬──► Lessons (one-to-many)
           │
           ├──► Enrollments (one-to-many)
           │
           ├──► Quizzes (one-to-many)
           │
           ├──► Assignments (one-to-many)
           │
           └──► Certificates (one-to-many)
```

This modular architecture ensures loose coupling between modules while maintaining clear dependencies where necessary.
