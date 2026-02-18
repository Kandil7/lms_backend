# Complete Module Documentation - Full Details

This comprehensive guide documents every module in the LMS Backend, explaining the purpose, design decisions, database schema, API endpoints, and business logic for each component.

---

## Table of Contents

1. [Auth Module](#1-auth-module)
2. [Users Module](#2-users-module)
3. [Courses Module](#3-courses-module)
4. [Enrollments Module](#4-enrollments-module)
5. [Quizzes Module](#5-quizzes-module)
6. [Certificates Module](#6-certificates-module)
7. [Files Module](#7-files-module)
8. [Analytics Module](#8-analytics-module)

---

## 1. Auth Module

### Purpose

The **Auth Module** handles all authentication and authorization operations including user registration, login, token management, password reset, email verification, and Multi-Factor Authentication (MFA).

### Why This Module Exists

- **Security**: Centralized authentication logic
- **Token Management**: JWT access and refresh tokens with proper expiration
- **MFA Support**: Optional two-factor authentication
- **Email Verification**: Account verification flow
- **Password Reset**: Secure password recovery

### Database Models

#### RefreshToken Model

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    # Primary key - UUID for distributed systems
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User reference - cascade delete when user is deleted
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # JWT Token ID - unique for token tracking
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    
    # Expiration tracking - indexed for efficient queries
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Revocation tracking - allows logout without expiration
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="refresh_tokens")
```

**Design Decisions:**

| Field | Decision | Reason |
|-------|----------|--------|
| `id` as UUID | UUID4 | Distributed ID generation, not guessable |
| `token_jti` | Unique index | Track individual tokens for revocation |
| `expires_at` | Indexed | Efficient expiration queries |
| `revoked_at` | Nullable | Support both expiration and manual revocation |

### Schemas

```python
# Token response
class TokenResponse(BaseModel):
    access_token: str      # Short-lived JWT (15 minutes)
    refresh_token: str     # Long-lived JWT (30 days)
    token_type: str = "bearer"

# Login request
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# MFA challenge response
class MfaChallengeResponse(BaseModel):
    mfa_required: bool = True
    challenge_token: str          # JWT for MFA verification
    expires_in_seconds: int       # Challenge expiration
    message: str = "MFA verification required"

# Password reset request
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str                    # Password reset JWT
    new_password: str = Field(min_length=8, max_length=128)
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. LOGIN                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐        │
│  │  Client  │───▶│  /auth/login│───▶│ Verify password  │        │
│  └──────────┘    └─────────────┘    └────────┬─────────┘        │
│                                               │                   │
│                    ┌───────────────────────────┤                   │
│                    │                           │                   │
│                    ▼                           ▼                   │
│           ┌──────────────┐           ┌─────────────────┐          │
│           │ MFA Enabled? │           │ No MFA          │          │
│           └──────┬───────┘           └────────┬────────┘          │
│                  │                             │                   │
│           ┌──────▼───────┐                     │                   │
│           │ MFA Challenge│                     ▼                   │
│           │ + Return code│            ┌─────────────────┐          │
│           └──────┬───────┘            │ Return tokens   │          │
│                  │                     │ + Create token  │          │
│                  ▼                     │ record          │          │
│           ┌──────────────┐             └─────────────────┘          │
│           │ MFA Verify  │                                         │
│           │ + Return    │                                         │
│           │ tokens      │                                         │
│           └─────────────┘                                         │
│                                                                     │
│  2. TOKEN REFRESH                                                  │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐        │
│  │  Client  │───▶│/auth/refresh│───▶│ Validate refresh │        │
│  └──────────┘    └─────────────┘    │ token            │        │
│                                      └────────┬─────────┘        │
│                                               │                   │
│                                               ▼                   │
│                                      ┌──────────────────┐       │
│                                      │ Revoke old token │       │
│                                      │ + Issue new      │       │
│                                      │ tokens           │       │
│                                      └──────────────────┘       │
│                                                                     │
│  3. LOGOUT                                                         │
│  ┌──────────┐    ┌───────────┐    ┌─────────────────┐           │
│  │  Client  │───▶│/auth/logout│───▶│ Revoke token   │           │
│  └──────────┘    └───────────┘    │ + Blacklist    │           │
│                                    │ access token   │           │
│                                    └─────────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user account |
| POST | `/auth/login` | Authenticate user |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke tokens |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| POST | `/auth/verify-email` | Request email verification |
| POST | `/auth/confirm-email` | Confirm email with token |
| POST | `/auth/mfa/enable` | Enable MFA |
| POST | `/auth/mfa/disable` | Disable MFA |
| POST | `/auth/mfa/verify` | Verify MFA login |

### MFA Implementation

The module implements Time-based One-Time Password (TOTP) style MFA:

```python
# MFA Challenge Flow
def _create_mfa_login_challenge(self, user_id: UUID):
    # 1. Create challenge token
    challenge_token = create_mfa_challenge_token(subject=str(user_id))
    
    # 2. Generate numeric code (6 digits)
    code = self._generate_numeric_code(6)  # e.g., "482931"
    
    # 3. Store in Redis with TTL
    cache_key = f"auth:mfa:login:{jti}"
    self.cache.set_json(
        cache_key,
        {"user_id": str(user_id), "code": code},
        ttl_seconds=ttl_seconds
    )
    
    return challenge_token, code, ttl_seconds
```

---

## 2. Users Module

### Purpose

The **Users Module** manages user accounts, profiles, and roles. It provides CRUD operations for user management and integrates with the auth module for authentication.

### Why This Module Exists

- **User Management**: Create, read, update, delete user accounts
- **Role Management**: Three roles (admin, instructor, student)
- **Profile Metadata**: Flexible profile data storage
- **Last Login Tracking**: Security and analytics

### Database Models

#### User Model

```python
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # Role constraint - only valid roles allowed
        CheckConstraint("role IN ('admin','instructor','student')", name="ck_users_role"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Role-based access - indexed for role queries
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="student", index=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Flexible metadata (JSON) - for custom profile fields
    profile_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        index=True  # For user listings
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="instructor")
    enrollments = relationship("Enrollment", back_populates="student")
```

**Design Decisions:**

| Feature | Implementation | Reason |
|---------|---------------|--------|
| UUID Primary Key | uuid4 | Distributed systems, security |
| Email Unique | Index + constraint | Login requirement, no duplicates |
| Role Constraint | Check constraint | Data integrity |
| JSON Metadata | JSONB column | Flexible profile fields |
| Soft Deletes | is_active flag | Preserve data, audit trail |

### User Roles

```python
class Role(str, Enum):
    ADMIN = "admin"         # Full system access
    INSTRUCTOR = "instructor" # Course creation, analytics
    STUDENT = "student"     # Course enrollment, learning
```

### Schemas

```python
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    role: Role = Role.STUDENT

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    role: Role | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    mfa_enabled: bool = False
    created_at: datetime
    email_verified_at: datetime | None = None
```

### API Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/users/register` | Register new user | Public |
| GET | `/users/me` | Get current user | Authenticated |
| PATCH | `/users/me` | Update own profile | Authenticated |
| GET | `/users` | List users | Admin |
| GET | `/users/{user_id}` | Get user by ID | Admin |
| PATCH | `/users/{user_id}` | Update user | Admin |
| DELETE | `/users/{user_id}` | Deactivate user | Admin |

---

## 3. Courses Module

### Purpose

The **Courses Module** manages course content including courses, lessons, and course categories. It provides the core content management functionality for the LMS.

### Why This Module Exists

- **Course Management**: Create and organize courses
- **Lesson Content**: Multiple content types (video, text, quiz, assignment)
- **Hierarchy**: Support for nested lessons
- **Publishing**: Draft/publish workflow

### Database Models

#### Course Model

```python
class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        # Difficulty level constraint
        CheckConstraint(
            "difficulty_level IS NULL OR difficulty_level IN ('beginner','intermediate','advanced')",
            name="ck_courses_difficulty_level"
        ),
        # Composite indexes for common queries
        Index("ix_courses_is_published_created_at", "is_published", "created_at"),
        Index("ix_courses_instructor_created_at", "instructor_id", "created_at"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Instructor (FK with RESTRICT - can't delete instructor with courses)
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Categorization
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    difficulty_level: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    
    # Publishing workflow
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    
    # Media
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Flexible metadata
    course_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    instructor = relationship("User", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
```

#### Lesson Model

```python
class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        # Lesson type constraint
        CheckConstraint("lesson_type IN ('video','text','quiz','assignment')", name="ck_lessons_lesson_type"),
        # Unique order within course
        UniqueConstraint("course_id", "order_index", name="uq_lessons_course_order"),
        # Composite index for queries
        Index("ix_lessons_course_lesson_type_order", "course_id", "lesson_type", "order_index"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Course reference - cascade delete
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown/HTML
    
    # Lesson type
    lesson_type: Mapped[str] = mapped_column(String(50), nullable=False)  # video|text|quiz|assignment
    
    # Ordering - explicit position
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Hierarchical lessons (parent/child)
    parent_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Video content
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Preview - free lessons
    is_preview: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Flexible metadata
    lesson_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    parent = relationship("Lesson", remote_side=[id], back_populates="children")
    children = relationship("Lesson", back_populates="parent")
    lesson_progress_entries = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    quiz = relationship("Quiz", back_populates="lesson", uselist=False, cascade="all, delete-orphan")
```

### Lesson Types

| Type | Description | Special Fields |
|------|-------------|----------------|
| `video` | Video content | video_url, duration_minutes |
| `text` | Text/Markdown content | content |
| `quiz` | Quiz assessment | quiz (relationship) |
| `assignment` | Assignment submission | content, duration_minutes |

### Course Publishing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COURSE PUBLISHING FLOW                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐     ┌─────────────┐     ┌──────────────────┐       │
│  │  Draft   │────▶│  Published  │────▶│ Students can     │       │
│  │  Course  │     │  Course     │     │ enroll           │       │
│  │          │     │             │     │                  │       │
│  │ is_publ- │     │ is_publ-   │     │ Course appears   │       │
│  │ ished=   │     │ ished=     │     │ in public list   │       │
│  │ false    │     │ true       │     │                  │       │
│  └──────────┘     └─────────────┘     └──────────────────┘       │
│                                                                     │
│  Admin/Instructor can:                                              │
│  - Create course (draft)                                            │
│  - Add/edit lessons                                                 │
│  - Preview course                                                   │
│  - Publish course                                                   │
│  - Unpublish course                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### API Endpoints

#### Course Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses` | List courses (with filters) |
| POST | `/courses` | Create course |
| GET | `/courses/{course_id}` | Get course details |
| PATCH | `/courses/{course_id}` | Update course |
| DELETE | `/courses/{course_id}` | Delete course |
| POST | `/courses/{course_id}/publish` | Publish course |
| POST | `/courses/{course_id}/unpublish` | Unpublish course |

#### Lesson Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses/{course_id}/lessons` | List lessons |
| POST | `/courses/{course_id}/lessons` | Create lesson |
| GET | `/courses/{course_id}/lessons/{lesson_id}` | Get lesson |
| PATCH | `/courses/{course_id}/lessons/{lesson_id}` | Update lesson |
| DELETE | `/courses/{course_id}/lessons/{lesson_id}` | Delete lesson |
| PATCH | `/courses/{course_id}/lessons/reorder` | Reorder lessons |

---

## 4. Enrollments Module

### Purpose

The **Enrollments Module** manages student enrollments in courses and tracks progress through lessons. It handles the student learning journey from enrollment to completion.

### Why This Module Exists

- **Enrollment Management**: Link students to courses
- **Progress Tracking**: Track completed lessons and overall progress
- **Time Tracking**: Monitor time spent learning
- **Reviews**: Allow students to rate/review courses
- **Certificates**: Trigger certificate generation on completion

### Database Models

#### Enrollment Model

```python
class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        # Status constraint
        CheckConstraint("status IN ('active','completed','dropped','expired')", name="ck_enrollments_status"),
        # One enrollment per student per course
        UniqueConstraint("student_id", "course_id", name="uq_enrollments_student_course"),
        # Indexes for common queries
        Index("ix_enrollments_student_enrolled_at", "student_id", "enrolled_at"),
        Index("ix_enrollments_course_enrolled_at", "course_id", "enrolled_at"),
        Index("ix_enrollments_course_status", "course_id", "status"),
        Index("ix_enrollments_student_status", "student_id", "status"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Timestamps
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    
    # Progress tracking
    progress_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    completed_lessons_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_lessons_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Activity tracking
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    certificate_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Review
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    lesson_progress_entries = relationship("LessonProgress", back_populates="enrollment", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="enrollment", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="enrollment", cascade="all, delete-orphan")
```

#### LessonProgress Model

```python
class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        # Status constraint
        CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_lesson_progress_status"),
        # One progress record per enrollment per lesson
        UniqueConstraint("enrollment_id", "lesson_id", name="uq_lesson_progress_enrollment_lesson"),
        # Indexes
        Index("ix_lesson_progress_enrollment_status", "enrollment_id", "status"),
        Index("ix_lesson_progress_enrollment_completed_at", "enrollment_id", "completed_at"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="not_started")
    
    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Progress details
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_position_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # For video
    completion_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Flexible metadata
    progress_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="lesson_progress_entries")
    lesson = relationship("Lesson", back_populates="lesson_progress_entries")
```

### Progress Calculation

```python
def calculate_enrollment_progress(enrollment: Enrollment) -> Enrollment:
    """
    Calculate overall enrollment progress based on lesson progress.
    
    Progress = (Completed Lessons / Total Lessons) * 100
    """
    total_lessons = enrollment.total_lessons_count
    completed_lessons = enrollment.completed_lessons_count
    
    if total_lessons > 0:
        progress = (completed_lessons / total_lessons) * 100
    else:
        progress = 0
    
    enrollment.progress_percentage = Decimal(str(progress))
    
    # Update status if completed
    if progress >= 100 and enrollment.status == "active":
        enrollment.status = "completed"
        enrollment.completed_at = datetime.utcnow()
    
    return enrollment
```

### Enrollment Status Flow

```
┌──────────┐     ┌──────────┐     ┌─────────────┐
│  Active  │────▶│Completed │────▶│ Certificate │
│          │     │ (100%)   │     │  Generated  │
│ Progress │     │          │     │             │
│ 0-99%    │     │ Progress │     │             │
│          │     │ =100%    │     │             │
└──────────┘     └──────────┘     └─────────────┘
     │                                    ▲
     │                                    │
     └──────────────┐  ┌─────────────────┘
                    │  │
                    ▼  │
              ┌──────────┐
              │  Dropped │
              │          │
              │ Student  │
              │ dropped  │
              │ out      │
              └──────────┘
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/enrollments` | Enroll in course |
| GET | `/enrollments/my-courses` | Get my enrollments |
| GET | `/enrollments/{enrollment_id}` | Get enrollment details |
| PATCH | `/enrollments/{enrollment_id}` | Update enrollment |
| DELETE | `/enrollments/{enrollment_id}` | Drop enrollment |
| POST | `/enrollments/{enrollment_id}/lessons/{lesson_id}/complete` | Mark lesson complete |
| PATCH | `/enrollments/{enrollment_id}/lessons/{lesson_id}/progress` | Update progress |
| POST | `/enrollments/{enrollment_id}/review` | Submit review |
| GET | `/enrollments/courses/{course_id}` | Get course enrollments |
| GET | `/enrollments/courses/{course_id}/stats` | Get enrollment stats |

---

## 5. Quizzes Module

### Purpose

The **Quizzes Module** provides assessment functionality including quiz creation, question management, quiz attempts, and automatic grading.

### Why This Module Exists

- **Assessment**: Test student understanding
- **Multiple Question Types**: Support various question formats
- **Attempt Tracking**: Limit attempts, track history
- **Automatic Grading**: Score quizzes automatically
- **Practice vs Graded**: Different quiz modes

### Database Models

#### Quiz Model

```python
class Quiz(Base):
    __tablename__ = "quizzes"
    __table_args__ = (
        # Quiz type constraint
        CheckConstraint("quiz_type IN ('practice','graded')", name="ck_quizzes_quiz_type"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # One quiz per lesson
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quiz_type: Mapped[str] = mapped_column(String(50), nullable=False, default="graded")
    
    # Quiz settings
    passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("70.00"))
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Display options
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Publishing
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
```

#### QuizQuestion Model

```python
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        # Question type constraint
        CheckConstraint(
            "question_type IN ('multiple_choice','true_false','short_answer','essay')",
            name="ck_quiz_questions_type"
        ),
        # Unique order within quiz
        UniqueConstraint("quiz_id", "order_index", name="uq_quiz_questions_order"),
        # Index for queries
        Index("ix_quiz_questions_quiz_type_order", "quiz_id", "question_type", "order_index"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Quiz reference
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Question content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    points: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("1.00"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Answer storage (JSON for flexibility)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)  # [{"text": "...", "is_correct": true}]
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Flexible metadata
    question_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    
    # Relationship
    quiz = relationship("Quiz", back_populates="questions")
```

#### QuizAttempt Model

```python
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        # Status constraint
        CheckConstraint("status IN ('in_progress','submitted','graded')", name="ck_quiz_attempts_status"),
        # Unique attempt number per enrollment/quiz
        UniqueConstraint("enrollment_id", "quiz_id", "attempt_number", name="uq_quiz_attempt_number"),
        # Indexes
        Index("ix_quiz_attempts_enrollment_status_submitted_at", "enrollment_id", "status", "submitted_at"),
        Index("ix_quiz_attempts_quiz_status_submitted_at", "quiz_id", "status", "submitted_at"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Attempt tracking
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress")
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Scoring
    score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    max_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    is_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Answers (JSON)
    answers: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
```

### Question Types

| Type | Description | Scoring |
|------|-------------|---------|
| `multiple_choice` | Select from options | Auto-graded |
| `true_false` | True/False questions | Auto-graded |
| `short_answer` | Text answer | Auto-graded (keyword matching) |
| `essay` | Long form answer | Manual grading |

### Quiz Types

| Type | Purpose | Attempts | Grade Recording |
|------|---------|----------|-----------------|
| `practice` | Learning practice | Unlimited | Best score only |
| `graded` | Formal assessment | Limited (max_attempts) | All attempts |

### Quiz Attempt Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      QUIZ ATTEMPT FLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. START ATTEMPT                                                  │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────────┐      │
│  │ Student  │───▶│ POST /attempts │───▶│ Check:           │      │
│  │ starts   │    │                 │    │ - Already enroll?│      │
│  │ quiz     │    │                 │    │ - Attempts left? │      │
│  └──────────┘    └─────────────────┘    │ - Time limit?   │      │
│                                          └────────┬─────────┘      │
│                                                   │                 │
│                                                   ▼                 │
│                                          ┌──────────────────┐      │
│                                          │ Create attempt   │      │
│                                          │ (in_progress)    │      │
│                                          │ + Start timer    │      │
│                                          └──────────────────┘      │
│                                                                     │
│  2. ANSWER QUESTIONS                                               │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────────┐      │
│  │ Student  │───▶│ Get questions   │───▶│ Shuffle if       │      │
│  │ answers  │    │                 │    │ configured       │      │
│  └──────────┘    └─────────────────┘    └──────────────────┘      │
│                                                                     │
│  3. SUBMIT                                                         │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────────┐      │
│  │ Student  │───▶│ POST /submit    │───▶│ Grade answers    │      │
│  │ submits  │    │                 │    │ (auto or manual) │      │
│  └──────────┘    └─────────────────┘    └────────┬─────────┘      │
│                                                   │                 │
│                                                   ▼                 │
│                                          ┌──────────────────┐      │
│                                          │ Calculate score  │      │
│                                          │ + percentage    │      │
│                                          │ + is_passed     │      │
│                                          └────────┬─────────┘      │
│                                                   │                 │
│                                                   ▼                 │
│                                          ┌──────────────────┐      │
│                                          │ Update attempt  │      │
│                                          │ (graded)         │      │
│                                          └──────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### API Endpoints

#### Quiz Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses/{course_id}/quizzes` | List quizzes |
| POST | `/courses/{course_id}/quizzes` | Create quiz |
| GET | `/courses/{course_id}/quizzes/{quiz_id}` | Get quiz |
| PATCH | `/courses/{course_id}/quizzes/{quiz_id}` | Update quiz |
| POST | `/courses/{course_id}/quizzes/{quiz_id}/publish` | Publish quiz |

#### Question Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses/{course_id}/quizzes/{quiz_id}/questions` | List questions |
| POST | `/courses/{course_id}/quizzes/{quiz_id}/questions` | Create question |
| GET | `/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}` | Get question |
| PATCH | `/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}` | Update question |
| DELETE | `/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}` | Delete question |

#### Attempt Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts` | List attempts |
| POST | `/enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts` | Start attempt |
| GET | `/enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts/{attempt_id}` | Get attempt |
| POST | `/enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts/{attempt_id}/submit` | Submit attempt |
| POST | `/enrollments/{enrollment_id}/quizzes/{quiz_id}/attempts/{attempt_id}/grade` | Manual grade |

---

## 6. Certificates Module

### Purpose

The **Certificates Module** generates and manages completion certificates for students who finish courses. It creates PDF certificates and provides verification functionality.

### Why This Module Exists

- **Credential Generation**: PDF certificates for course completion
- **Unique Certificates**: Unique certificate numbers for verification
- **Verification API**: Public endpoint to verify certificates
- **Revocation**: Ability to revoke invalid certificates

### Database Model

```python
class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        # Index for verification queries
        Index("ix_certificates_student_revoked_issued_at", "student_id", "is_revoked", "issued_at"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # One certificate per enrollment
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # References
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Certificate data
    certificate_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    pdf_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    # Dates
    completion_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Revocation
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="certificates")
    student = relationship("User")
    course = relationship("Course")
```

### Certificate Generation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                 CERTIFICATE GENERATION FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐     ┌─────────────────┐                      │
│  │ Enrollment       │     │ Student         │                      │
│  │ reaches 100%     │────▶│ completes       │                      │
│  │ progress         │     │ course          │                      │
│  └──────────────────┘     └────────┬────────┘                      │
│                                     │                               │
│                                     ▼                               │
│  ┌──────────────────────────────────────────────┐                  │
│  │ Trigger Certificate Generation               │                  │
│  │ (Background Task)                            │                  │
│  └────────────────────┬─────────────────────────┘                  │
│                       │                                             │
│                       ▼                                             │
│  ┌──────────────────────────────────────────────┐                  │
│  │ 1. Generate unique certificate number        │                  │
│  │    Format: CERT-YYYYMMDD-XXXXXX             │                  │
│  │    Example: CERT-20240115-A7B3C2             │                  │
│  └────────────────────┬─────────────────────────┘                  │
│                       │                                             │
│                       ▼                                             │
│  ┌──────────────────────────────────────────────┐                  │
│  │ 2. Create PDF Certificate                     │                  │
│  │    - Student name                            │                  │
│  │    - Course name                            │                  │
│  │    - Completion date                       │                  │
│  │    - Certificate number                     │                  │
│  │    - QR code for verification               │                  │
│  └────────────────────┬─────────────────────────┘                  │
│                       │                                             │
│                       ▼                                             │
│  ┌──────────────────────────────────────────────┐                  │
│  │ 3. Save to storage (local/S3)                │                  │
│  │    + Store record in database                │                  │
│  └────────────────────┬─────────────────────────┘                  │
│                       │                                             │
│                       ▼                                             │
│  ┌──────────────────────────────────────────────┐                  │
│  │ 4. Send notification email                   │                  │
│  │    + Include download link                    │                  │
│  └──────────────────────────────────────────────┘                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Certificate Number Generation

```python
def generate_certificate_number() -> str:
    """Generate unique certificate number."""
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(secrets.choice("ABCDEF0123456789") for _ in range(6))
    return f"CERT-{date_part}-{random_part}"
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/certificates/my-certificates` | Get my certificates |
| GET | `/certificates/{certificate_id}` | Get certificate details |
| GET | `/certificates/{certificate_id}/download` | Download PDF |
| GET | `/certificates/verify/{certificate_number}` | Verify certificate |
| POST | `/certificates/enrollments/{enrollment_id}/generate` | Generate certificate |
| POST | `/certificates/{certificate_id}/revoke` | Revoke certificate |

---

## 7. Files Module

### Purpose

The **Files Module** handles file uploads and storage for course materials, user avatars, and other files. It supports multiple storage providers (local and S3).

### Why This Module Exists

- **File Upload**: Secure file upload handling
- **Multiple Storage**: Local and cloud storage support
- **File Type Validation**: Prevent malicious uploads
- **Organization**: Folder-based file organization

### Database Model

```python
class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    __table_args__ = (
        # Indexes for queries
        Index("ix_uploaded_files_uploader_created_at", "uploader_id", "created_at"),
        Index("ix_uploaded_files_uploader_type_created_at", "uploader_id", "file_type", "created_at"),
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Uploader reference
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    # File metadata
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Organization
    folder: Mapped[str] = mapped_column(String(100), nullable=False, default="uploads")
    storage_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationship
    uploader = relationship("User")
```

### Storage Abstraction

```python
class FileStorage(ABC):
    """Abstract file storage interface."""
    
    @abstractmethod
    async def upload(self, file: UploadFile, path: str) -> str:
        """Upload file and return URL."""
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file."""
        pass
    
    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Get file URL."""
        pass

class LocalStorage(FileStorage):
    """Local filesystem storage."""
    
    async def upload(self, file: UploadFile, path: str) -> str:
        # Save to local disk
        full_path = Path(UPLOAD_DIR) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        await self._write_file(file, full_path)
        return f"/uploads/{path}"

class S3Storage(FileStorage):
    """AWS S3 storage."""
    
    async def upload(self, file: UploadFile, path: str) -> str:
        # Upload to S3
        s3_client.upload_fileobj(
            file.file,
            AWS_S3_BUCKET,
            path,
            ExtraArgs={"ContentType": file.content_type}
        )
        return f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/{path}"
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/files/upload` | Upload file |
| GET | `/files/my-files` | List my files |
| GET | `/files/{file_id}` | Get file info |
| GET | `/files/{file_id}/download` | Download file |
| DELETE | `/files/{file_id}` | Delete file |

---

## 8. Analytics Module

### Purpose

The **Analytics Module** provides reporting and analytics for students, instructors, and administrators. It tracks learning progress, course performance, and system usage.

### Why This Module Exists

- **Student Dashboard**: Personal progress and recommendations
- **Instructor Analytics**: Course performance and student engagement
- **Admin Overview**: System-wide metrics and trends
- **Decision Making**: Data-driven course improvements

### Analytics Types

#### Student Analytics
- Course progress
- Time spent learning
- Quiz performance
- Completion rates

#### Instructor Analytics
- Course enrollments
- Student engagement
- Quiz completion rates
- Average ratings

#### System Analytics
- Total users
- Active courses
- Enrollment trends
- Popular courses

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/my-progress` | Student progress summary |
| GET | `/analytics/my-dashboard` | Student dashboard data |
| GET | `/analytics/courses/{course_id}` | Course analytics |
| GET | `/analytics/instructors/{instructor_id}/overview` | Instructor analytics |
| GET | `/analytics/system/overview` | System-wide analytics |

---

## Module Summary

| Module | Purpose | Key Entities |
|--------|---------|---------------|
| **Auth** | Authentication & security | User, RefreshToken |
| **Users** | User management | User |
| **Courses** | Course content | Course, Lesson |
| **Enrollments** | Student progress | Enrollment, LessonProgress |
| **Quizzes** | Assessments | Quiz, QuizQuestion, QuizAttempt |
| **Certificates** | Completion credentials | Certificate |
| **Files** | File management | UploadedFile |
| **Analytics** | Reporting | N/A (aggregations) |

This comprehensive module documentation provides complete understanding of how each component works and why it was designed that way.
