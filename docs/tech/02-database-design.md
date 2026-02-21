# Database Design

## Complete Database Schema Documentation

This document provides comprehensive details about the database design, including all models, relationships, indexes, and design decisions.

---

## 1. Database Technology Stack

### Technologies Used

| Component | Technology | Version |
|-----------|------------|---------|
| Database | PostgreSQL | 16 |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.14+ |
| Async Driver | asyncpg | 0.30+ |
| Sync Driver | psycopg2-binary | 2.9+ |

### Why This Stack?

- **PostgreSQL 16**: ACID compliance for payments, JSON support for metadata, robust indexing
- **SQLAlchemy 2.0**: Type-safe queries, async support, declarative models
- **Alembic**: Version-controlled schema changes, rollback support

---

## 2. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LMS DATABASE SCHEMA                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                          │
│  │     users    │                                                          │
│  ├──────────────┤                                                          │
│  │ id (PK)      │◄────────────────┐                                        │
│  │ email        │                 │                                        │
│  │ password_hash│                │                                        │
│  │ full_name    │                │                                        │
│  │ role         │                │                                        │
│  │ is_active   │                │                                        │
│  │ mfa_enabled │                │                                        │
│  │ created_at   │                │                                        │
│  │ updated_at   │                │                                        │
│  └──────────────┘                │                                        │
│         │                        │                                        │
│         │ (1:N)                  │ (1:N)                                  │
│         │                        │                                        │
│         ▼                        │                                        │
│  ┌──────────────┐               │                                        │
│  │refresh_tokens│               │                                        │
│  ├──────────────┤               │                                        │
│  │ id (PK)      │               │                                        │
│  │ user_id (FK) │               │                                        │
│  │ token_jti    │               │                                        │
│  │ expires_at   │               │                                        │
│  │ revoked_at   │               │                                        │
│  └──────────────┘               │                                        │
│                                  │                                        │
│    (instructor)                 │                                        │
│         │                        │                                        │
│         │ (1:N)                 │ (1:N)                                  │
│         │                        │                                        │
│         ▼                        │                                        │
│  ┌──────────────┐    ┌──────────────┐                                    │
│  │   courses    │    │  enrollments │                                    │
│  ├──────────────┤    ├──────────────┤                                    │
│  │ id (PK)      │    │ id (PK)      │                                    │
│  │ title        │    │ student_id(FK)│◄────┐                            │
│  │ slug (UQ)    │    │ course_id (FK)├─────┼────┐                        │
│  │ description  │    │ status        │    │    │                        │
│  │ instructor_id│───►│ progress_%    │    │    │                        │
│  │ category     │    │ enrolled_at   │    │    │                        │
│  │ is_published │    └──────┬────────┘    │    │                        │
│  │ created_at   │           │             │    │                        │
│  └──────┬───────┘           │             │    │                        │
│         │                   │ (1:N)       │    │                        │
│         │ (1:N)             │             │    │                        │
│         ▼                   ▼             │    │                        │
│  ┌──────────────┐    ┌──────────────┐      │    │                        │
│  │   lessons    │    │lesson_progress│    │    │                        │
│  ├──────────────┤    ├──────────────┤      │    │                        │
│  │ id (PK)      │    │ id (PK)      │      │    │                        │
│  │ course_id(FK)│───►│ enrollment_id │─────┘    │                        │
│  │ title        │    │ lesson_id(FK) │◄─────────┘                        │
│  │ slug         │    │ status        │                                  │
│  │ lesson_type  │    │ completed_at  │                                  │
│  │ order_index  │    │ time_spent    │                                  │
│  │ video_url    │    └───────────────┘                                  │
│  │ is_preview   │                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                  │
│         │ (1:1)                                                            │
│         ▼                                                                  │
│  ┌──────────────┐                                                          │
│  │   quizzes    │                                                          │
│  ├──────────────┤                                                          │
│  │ id (PK)      │◄─────────────┐                                         │
│  │ lesson_id(FK)│ (1:N)        │                                         │
│  │ title        │              │                                         │
│  │ quiz_type    │              │                                         │
│  │ passing_score│              │                                         │
│  └──────┬───────┘              │                                         │
│         │                      │                                         │
│         │ (1:N)                │                                         │
│         ▼                      │                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │quiz_questions│    │quiz_attempts │    │ certificates │               │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤               │
│  │ id (PK)      │    │ id (PK)      │    │ id (PK)      │               │
│  │ quiz_id(FK)  │◄───│ enrollment_id│◄───│ enrollment_id│               │
│  │ question_text│    │ quiz_id(FK)  │    │ student_id(FK)│               │
│  │ question_type│    │ attempt_num  │    │ course_id(FK)│               │
│  │ options (JSON)   │ status        │    │ cert_number  │               │
│  │ correct_answer   │ score         │    │ pdf_path     │               │
│  └──────────────────│ is_passed     │    │ issued_at    │               │
│                     └───────────────┘    └──────────────┘               │
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │uploaded_files│    │   payments   │    │subscriptions │               │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤               │
│  │ id (PK)      │    │ id (PK)      │    │ id (PK)      │               │
│  │ uploader_id  │    │ user_id(FK)  │    │ user_id(FK)  │               │
│  │ filename     │    │ enrollment_id │    │ stripe_sub_id│               │
│  │ file_url     │    │ payment_type │    │ plan_name    │               │
│  │ file_size    │    │ amount       │    │ status       │               │
│  │ mime_type    │    │ currency     │    │ current_per..│               │
│  │ storage_path │    │ status       │    └──────────────┘               │
│  └──────────────┘    └──────┬───────┘                                   │
│                             │                                            │
│                             │ (1:N)                                      │
│                             ▼                                            │
│                    ┌──────────────┐                                    │
│                    │payment_web..│                                    │
│                    ├──────────────┤                                    │
│                    │ id (PK)      │                                    │
│                    │ stripe_event_│                                    │
│                    │ event_type   │                                    │
│                    │ payload      │                                    │
│                    │ status       │                                    │
│                    └──────────────┘                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Models

### 3.1 Users Table

**Purpose**: Store all user accounts (students, instructors, admins)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'student',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    profile_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP,
    email_verified_at TIMESTAMP
);

-- Indexes
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_role ON users(role);
CREATE INDEX ix_users_email_verified_at ON users(email_verified_at);
CREATE INDEX ix_users_is_active_created_at ON users(is_active, created_at);
```

### Model Definition

```python
# app/modules/users/models.py
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email_verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| UUID as PK | Global uniqueness, no central ID server |
| Separate password_hash | Never store plain passwords |
| JSONB for metadata | Flexible profile data without schema changes |
| email_verified_at | Track email verification status |
| last_login_at | Security audit trail |

---

### 3.2 Refresh Tokens Table

**Purpose**: Store issued refresh tokens for session management

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX ix_refresh_tokens_token_jti ON refresh_tokens(token_jti);
CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX ix_refresh_tokens_revoked_at ON refresh_tokens(revoked_at);
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| token_jti UNIQUE | Prevent token reuse |
| ON DELETE CASCADE | Clean up tokens when user deleted |
| expires_at indexed | Efficient cleanup queries |
| revoked_at | Track token revocation |

---

### 3.3 Courses Table

**Purpose**: Store course information

```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    instructor_id UUID NOT NULL REFERENCES users(id),
    category VARCHAR(100),
    difficulty_level VARCHAR(50),
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    thumbnail_url VARCHAR(500),
    estimated_duration_minutes INTEGER,
    course_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_courses_instructor_id ON courses(instructor_id);
CREATE INDEX ix_courses_slug ON courses(slug);
CREATE INDEX ix_courses_category ON courses(category);
CREATE INDEX ix_courses_difficulty_level ON courses(difficulty_level);
CREATE INDEX ix_courses_is_published_created_at ON courses(is_published, created_at);
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| slug UNIQUE | SEO-friendly URLs |
| is_published | Draft/published workflow |
| course_metadata | Flexible course attributes |
| Composite index on is_published + created_at | Common query pattern |

---

### 3.4 Lessons Table

**Purpose**: Store individual lessons within courses

```sql
CREATE TABLE lessons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT,
    lesson_type VARCHAR(50) NOT NULL,
    order_index INTEGER NOT NULL,
    parent_lesson_id UUID REFERENCES lessons(id),
    duration_minutes INTEGER,
    video_url VARCHAR(500),
    is_preview BOOLEAN NOT NULL DEFAULT FALSE,
    lesson_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(course_id, order_index)
);

CREATE INDEX ix_lessons_course_id ON lessons(course_id);
CREATE INDEX ix_lessons_parent_lesson_id ON lessons(parent_lesson_id);
```

### Lesson Types

```python
class LessonType(str, Enum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
```

---

### 3.5 Enrollments Table

**Purpose**: Track student enrollments in courses

```sql
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    progress_percentage NUMERIC(5,2) NOT NULL DEFAULT 0,
    completed_lessons_count INTEGER NOT NULL DEFAULT 0,
    total_lessons_count INTEGER NOT NULL DEFAULT 0,
    total_time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP,
    certificate_issued_at TIMESTAMP,
    rating INTEGER,
    review TEXT,
    
    UNIQUE(student_id, course_id)
);

CREATE INDEX ix_enrollments_student_id ON enrollments(student_id);
CREATE INDEX ix_enrollments_course_id ON enrollments(course_id);
CREATE INDEX ix_enrollments_status ON enrollments(status);
```

### Enrollment Status

```python
class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    EXPIRED = "expired"
```

---

### 3.6 Lesson Progress Table

**Purpose**: Track individual lesson progress per enrollment

```sql
CREATE TABLE lesson_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    lesson_id UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    last_position_seconds INTEGER NOT NULL DEFAULT 0,
    completion_percentage NUMERIC(5,2) NOT NULL DEFAULT 0,
    attempts_count INTEGER NOT NULL DEFAULT 0,
    progress_metadata JSONB,
    
    UNIQUE(enrollment_id, lesson_id)
);

CREATE INDEX ix_lesson_progress_enrollment_id ON lesson_progress(enrollment_id);
CREATE INDEX ix_lesson_progress_lesson_id ON lesson_progress(lesson_id);
```

---

### 3.7 Quizzes Table

**Purpose**: Store quiz configurations

```sql
CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID NOT NULL UNIQUE REFERENCES lessons(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    quiz_type VARCHAR(50) NOT NULL DEFAULT 'graded',
    passing_score NUMERIC(5,2) NOT NULL DEFAULT 70.00,
    time_limit_minutes INTEGER,
    max_attempts INTEGER,
    shuffle_questions BOOLEAN NOT NULL DEFAULT TRUE,
    shuffle_options BOOLEAN NOT NULL DEFAULT TRUE,
    show_correct_answers BOOLEAN NOT NULL DEFAULT TRUE,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_quizzes_lesson_id ON quizzes(lesson_id);
```

### Quiz Types

```python
class QuizType(str, Enum):
    PRACTICE = "practice"  # Not graded, for learning
    GRADED = "graded"     # Counts toward completion
```

---

### 3.8 Quiz Questions Table

**Purpose**: Store quiz questions

```sql
CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    points NUMERIC(5,2) NOT NULL DEFAULT 1.00,
    order_index INTEGER NOT NULL,
    explanation TEXT,
    options JSONB,  -- For multiple choice
    correct_answer TEXT,
    question_metadata JSONB,
    
    UNIQUE(quiz_id, order_index)
);

CREATE INDEX ix_quiz_questions_quiz_id ON quiz_questions(quiz_id);
```

### Question Types

```python
class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
```

---

### 3.9 Quiz Attempts Table

**Purpose**: Track student quiz attempts

```sql
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMP,
    graded_at TIMESTAMP,
    score NUMERIC(6,2),
    max_score NUMERIC(6,2),
    percentage NUMERIC(6,2),
    is_passed BOOLEAN,
    time_taken_seconds INTEGER,
    answers JSONB,
    
    UNIQUE(enrollment_id, quiz_id, attempt_number)
);

CREATE INDEX ix_quiz_attempts_enrollment_id ON quiz_attempts(enrollment_id);
CREATE INDEX ix_quiz_attempts_quiz_id ON quiz_attempts(quiz_id);
CREATE INDEX ix_quiz_attempts_submitted_at ON quiz_attempts(submitted_at);
```

### Attempt Status

```python
class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
```

---

### 3.10 Certificates Table

**Purpose**: Store issued certificates

```sql
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL UNIQUE REFERENCES enrollments(id),
    student_id UUID NOT NULL REFERENCES users(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    certificate_number VARCHAR(50) NOT NULL UNIQUE,
    pdf_path VARCHAR(1024) NOT NULL,
    completion_date TIMESTAMP NOT NULL,
    issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMP
);

CREATE INDEX ix_certificates_student_id ON certificates(student_id);
CREATE INDEX ix_certificates_course_id ON certificates(course_id);
CREATE INDEX ix_certificates_certificate_number ON certificates(certificate_number);
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| certificate_number UNIQUE | Public verification code |
| enrollment_id UNIQUE | One certificate per completion |
| pdf_path | Store generated PDF location |
| is_revoked | Support certificate revocation |

---

### 3.11 Uploaded Files Table

**Purpose**: Track uploaded files (course materials)

```sql
CREATE TABLE uploaded_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploader_id UUID NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL UNIQUE,
    original_filename VARCHAR(255) NOT NULL,
    file_url VARCHAR(1024) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL,
    file_type VARCHAR(50) NOT NULL DEFAULT 'other',
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    folder VARCHAR(100) NOT NULL DEFAULT 'uploads',
    storage_provider VARCHAR(50) NOT NULL DEFAULT 'local',
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_uploaded_files_uploader_id ON uploaded_files(uploader_id);
CREATE INDEX ix_uploaded_files_file_type ON uploaded_files(file_type);
```

---

### 3.12 Payments Table

**Purpose**: Store payment records

```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    user_id UUID NOT NULL REFERENCES users(id),
    enrollment_id UUID REFERENCES enrollments(id),
    subscription_id UUID REFERENCES subscriptions(id),
    payment_type VARCHAR(20) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EGP',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    plan_name VARCHAR(100),
    plan_price_id VARCHAR(255),
    tax_amount NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    total_amount NUMERIC(10,2) NOT NULL,
    payment_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP
);

CREATE INDEX ix_payments_user_id ON payments(user_id);
CREATE INDEX ix_payments_enrollment_id ON payments(enrollment_id);
CREATE INDEX ix_payments_status ON payments(status);
CREATE INDEX ix_payments_stripe_payment_intent_id ON payments(stripe_payment_intent_id);
```

### Payment Status

```python
class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
```

---

### 3.13 Subscriptions Table

**Purpose**: Store subscription information

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_subscription_id VARCHAR(255) NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(255),
    user_id UUID NOT NULL REFERENCES users(id),
    plan_name VARCHAR(100) NOT NULL,
    plan_price_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'incomplete',
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    courses_accessed INTEGER NOT NULL DEFAULT 0,
    total_usage INTEGER NOT NULL DEFAULT 0,
    subscription_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    canceled_at TIMESTAMP
);

CREATE INDEX ix_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX ix_subscriptions_status ON subscriptions(status);
CREATE INDEX ix_subscriptions_current_period_end ON subscriptions(current_period_end);
```

### Subscription Status

```python
class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
```

---

### 3.14 Payment Webhook Events Table

**Purpose**: Store webhook events for audit and replay

```sql
CREATE TABLE payment_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    payload TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP
);

CREATE INDEX ix_payment_webhook_events_event_type ON payment_webhook_events(event_type);
CREATE INDEX ix_payment_webhook_events_status ON payment_webhook_events(status);
```

---

## 4. Database Migrations

### Migration Files

```
alembic/
├── env.py
├── script.py.mako
└── versions/
    ├── 0001_initial_schema.py        # Users, courses, lessons, enrollments
    ├── 0002_phase1_security_and_performance.py  # Security indexes
    ├── 0003_phase1_infrastructure_indexes.py    # Performance indexes
    ├── 0004_phase1_quiz_indexes.py              # Quiz indexes
    ├── 0005_phase1_remaining_indexes.py          # Remaining indexes
    ├── 0006_add_users_email_verified_at.py       # Email verification
    ├── 0007_add_users_mfa_enabled.py             # MFA support
    └── 0008_add_payments_module.py               # Payments and subscriptions
```

### Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "description"
```

---

## 5. Indexing Strategy

### Why Indexes Matter

| Query Pattern | Index Used |
|---------------|------------|
| Login by email | `ix_users_email` |
| User role filtering | `ix_users_role` |
| Published courses | `ix_courses_is_published_created_at` |
| Instructor courses | `ix_courses_instructor_id` |
| Student enrollments | `ix_enrollments_student_id` |
| Quiz attempts | `ix_quiz_attempts_enrollment_id` |

### Composite Indexes

```sql
-- Courses: Published + recent first
CREATE INDEX ix_courses_is_published_created_at 
ON courses(is_published, created_at DESC);

-- Enrollments: Active + recent
CREATE INDEX ix_enrollments_status_enrolled_at 
ON enrollments(status, enrolled_at DESC);
```

---

## 6. Data Integrity

### Constraints Used

| Constraint | Tables | Purpose |
|------------|--------|---------|
| UNIQUE | users.email | One account per email |
| UNIQUE | courses.slug | SEO-friendly URLs |
| UNIQUE | enrollments.student_id + course_id | One enrollment per student per course |
| UNIQUE | certificates.enrollment_id | One certificate per completion |
| UNIQUE | refresh_tokens.token_jti | Prevent token reuse |
| UNIQUE | quiz_attempts.enrollment_id + quiz_id + attempt_number | Track attempts |
| CHECK | lessons.order_index >= 0 | Valid order |
| CHECK | quiz_attempts.percentage >= 0 AND <= 100 | Valid percentage |

---

## 7. Performance Optimizations

### Connection Pooling

```python
# app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,          # Maintain 20 connections
    max_overflow=40,       # Allow 40 overflow connections
    pool_pre_ping=True,    # Test connections before use
    pool_recycle=3600,     # Recycle connections hourly
)
```

### Query Optimization

1. **Eager Loading**: Use `selectinload` for relationships
2. **Pagination**: Always paginate list endpoints
3. **Partial Indexes**: For filtered queries
4. **Covering Indexes**: For frequently accessed columns

---

## 8. Backup Strategy

### Backup Commands

```bash
# Full backup
pg_dump -U lms_user -h localhost lms > backup_$(date +%Y%m%d).sql

# Incremental (WAL archiving)
# Configured in PostgreSQL
```

### Retention

| Backup Type | Frequency | Retention |
|-------------|-----------|-----------|
| Full | Daily | 7 days |
| Incremental | Hourly | 24 hours |
| WAL | Continuous | 7 days |

---

## Summary

This database design provides:

- **ACID Compliance**: Critical for payments and enrollments
- **Performance**: Strategic indexes for common queries
- **Flexibility**: JSONB columns for metadata
- **Auditability**: Timestamps on all records
- **Scalability**: Connection pooling, proper constraints
- **Security**: Foreign keys, unique constraints, encrypted connections

The schema supports all LMS features including courses, lessons, quizzes, enrollments, progress tracking, certificates, and payments.
