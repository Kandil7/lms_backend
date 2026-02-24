# Database Schema Documentation

This document covers the complete database schema for the LMS Backend.

## Table of Contents

1. [Entity Relationship Diagram](#entity-relationship-diagram)
2. [Core Tables](#core-tables)
3. [Module Tables](#module-tables)
4. [Indexes](#indexes)
5. [Relationships](#relationships)

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Users    │       │  Courses    │       │  Payments   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)    │◄──────│instructor_id│       │ id (PK)     │
│ email       │       │ id (PK)     │◄──────│ order_id    │
│ password_hash│      │             │       │ user_id (FK)│
│ full_name   │       └──────┬──────┘       └─────────────┘
│ role        │              │
│ is_active   │       ┌──────┴──────┐
│ mfa_enabled │       │             │
└──────┬──────┘       │  Enrollments│
       │              │             │
       │              │ user_id (FK) │
       │              │ course_id(FK)│
       │              └──────┬──────┘
       │                     │
       │              ┌──────┴──────┐
       │              │             │
       │              │  Lessons    │
       │              │             │
       │              │ course_id(FK)│
       │              │ id (PK)     │
       │              └─────────────┘
       │
       │              ┌─────────────┐       ┌─────────────┐
       │              │   Quizzes   │       │ Assignments │
       │              ├─────────────┤       ├─────────────┤
       │              │ id (PK)     │       │ id (PK)     │
       └──────────────│ course_id(FK)│       │ course_id(FK│
                      │             │       │ instructor_ │
                      └──────┬──────┘       │ id (FK)     │
                             │              └──────┬──────┘
                    ┌───────┴───────┐              │
                    │               │              │
              ┌─────┴─────┐ ┌─────┴─────┐        │
              │ Questions  │ │Attempts   │        │
              ├───────────┤ ├───────────┤        │
              │ quiz_id(FK)│ │quiz_id(FK)│        │
              │ id (PK)   │ │user_id(FK)│        │
              └───────────┘ └───────────┘        │
                                                │
                                        ┌───────┴───────┐
                                        │  Submissions  │
                                        ├───────────────┤
                                        │ assignment_id │
                                        │ user_id (FK)  │
                                        │ id (PK)       │
                                        └───────────────┘
```

---

## Core Tables

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'instructor', 'student')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT ck_users_role CHECK (role IN ('admin', 'instructor', 'student'))
);

CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_role ON users(role);
CREATE INDEX ix_users_created_at ON users(created_at);
CREATE INDEX ix_users_email_verified_at ON users(email_verified_at);
```

### Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(token_jti)
);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX ix_refresh_tokens_token_jti ON refresh_tokens(token_jti);
CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

### Administrators Table

```sql
CREATE TABLE admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_admin_user FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Instructors Table

```sql
CREATE TABLE instructors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    bio TEXT,
    expertise TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_instructor_user FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Module Tables

### Courses Table

```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    short_description VARCHAR(1000),
    thumbnail_url VARCHAR(1000),
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    is_free BOOLEAN NOT NULL DEFAULT FALSE,
    category VARCHAR(100),
    tags TEXT[],
    instructor_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_courses_instructor_id ON courses(instructor_id);
CREATE INDEX ix_courses_is_published ON courses(is_published);
CREATE INDEX ix_courses_category ON courses(category);
CREATE INDEX ix_courses_created_at ON courses(created_at);
```

### Lessons Table

```sql
CREATE TABLE lessons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    video_url VARCHAR(1000),
    duration_minutes INTEGER,
    lesson_order INTEGER NOT NULL,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_lessons_course_id ON lessons(course_id);
CREATE INDEX ix_lessons_lesson_order ON lessons(course_id, lesson_order);
```

### Enrollments Table

```sql
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    progress_percentage INTEGER NOT NULL DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    payment_id UUID REFERENCES payments(id) ON DELETE SET NULL,
    
    CONSTRAINT uq_enrollment_user_course UNIQUE (user_id, course_id)
);

CREATE INDEX ix_enrollments_user_id ON enrollments(user_id);
CREATE INDEX ix_enrollments_course_id ON enrollments(course_id);
CREATE INDEX ix_enrollments_payment_id ON enrollments(payment_id);
```

### Quizzes Table

```sql
CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(id) ON DELETE SET NULL,
    time_limit_minutes INTEGER,
    passing_score_percentage INTEGER NOT NULL DEFAULT 70,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_quizzes_course_id ON quizzes(course_id);
CREATE INDEX ix_quizzes_lesson_id ON quizzes(lesson_id);
```

### Questions Table

```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL CHECK (question_type IN ('multiple_choice', 'true_false', 'short_answer')),
    options JSONB,
    correct_answer TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 1,
    question_order INTEGER NOT NULL,
    
    CONSTRAINT ck_question_type CHECK (question_type IN ('multiple_choice', 'true_false', 'short_answer'))
);

CREATE INDEX ix_questions_quiz_id ON questions(quiz_id);
CREATE INDEX ix_questions_order ON questions(quiz_id, question_order);
```

### Quiz Attempts Table

```sql
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    score INTEGER,
    passed BOOLEAN,
    answers JSONB,
    
    CONSTRAINT uq_attempt_user_quiz UNIQUE (quiz_id, user_id, started_at)
);

CREATE INDEX ix_quiz_attempts_quiz_id ON quiz_attempts(quiz_id);
CREATE INDEX ix_quiz_attempts_user_id ON quiz_attempts(user_id);
```

### Assignments Table

```sql
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(id) ON DELETE SET NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    points INTEGER NOT NULL DEFAULT 100,
    allow_late_submission BOOLEAN NOT NULL DEFAULT TRUE,
    late_penalty_percentage INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_assignments_course_id ON assignments(course_id);
CREATE INDEX ix_assignments_due_date ON assignments(due_date);
```

### Submissions Table

```sql
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    content TEXT,
    file_url VARCHAR(1000),
    grade INTEGER,
    feedback TEXT,
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by UUID REFERENCES users(id),
    
    CONSTRAINT uq_submission_user_assignment UNIQUE (assignment_id, user_id)
);

CREATE INDEX ix_submissions_assignment_id ON submissions(assignment_id);
CREATE INDEX ix_submissions_user_id ON submissions(user_id);
```

### Files Table

```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100),
    storage_provider VARCHAR(20) NOT NULL DEFAULT 'local',
    storage_path VARCHAR(1000) NOT NULL,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    assignment_id UUID REFERENCES assignments(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_files_uploaded_by ON files(uploaded_by);
CREATE INDEX ix_files_course_id ON files(course_id);
CREATE INDEX ix_files_assignment_id ON files(assignment_id);
```

### Orders Table

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    stripe_payment_intent_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT ck_order_status CHECK (status IN ('pending', 'completed', 'failed', 'refunded'))
);

CREATE INDEX ix_orders_user_id ON orders(user_id);
CREATE INDEX ix_orders_course_id ON orders(course_id);
CREATE INDEX ix_orders_status ON orders(status);
CREATE INDEX ix_orders_stripe_id ON orders(stripe_payment_intent_id);
```

### Payments Table

```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_method VARCHAR(50),
    stripe_payment_method_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    transaction_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_payments_order_id ON payments(order_id);
CREATE INDEX ix_payments_user_id ON payments(user_id);
CREATE INDEX ix_payments_status ON payments(status);
```

### Certificates Table

```sql
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    certificate_number VARCHAR(50) UNIQUE NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pdf_url VARCHAR(1000),
    
    CONSTRAINT uq_certificate_user_course UNIQUE (user_id, course_id)
);

CREATE INDEX ix_certificates_user_id ON certificates(user_id);
CREATE INDEX ix_certificates_course_id ON certificates(course_id);
CREATE INDEX ix_certificates_number ON certificates(certificate_number);
```

---

## Indexes

### Composite Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `ix_lessons_course_order` | `course_id, lesson_order` | Lesson ordering |
| `ix_enrollments_user_course` | `user_id, course_id` | User enrollments |
| `ix_submissions_assignment_user` | `assignment_id, user_id` | Student submissions |
| `ix_quiz_attempts_user_quiz` | `user_id, quiz_id` | Quiz history |

### Partial Indexes

```sql
-- Published courses only
CREATE INDEX ix_courses_published ON courses(created_at) 
WHERE is_published = TRUE;

-- Active enrollments
CREATE INDEX ix_enrollments_active ON enrollments(user_id, course_id) 
WHERE is_active = TRUE;

-- Completed enrollments
CREATE INDEX ix_enrollments_completed ON enrollments(user_id) 
WHERE completed_at IS NOT NULL;
```

---

## Relationships

### One-to-One

| Relationship | Table | Foreign Key |
|---------------|-------|-------------|
| User → Admin | `admins` | `user_id` |
| User → Instructor | `instructors` | `user_id` |

### One-to-Many

| Parent | Child | Foreign Key |
|--------|-------|-------------|
| User | RefreshToken | `user_id` |
| User | Enrollment | `user_id` |
| User | File | `uploaded_by` |
| Course | Lesson | `course_id` |
| Course | Quiz | `course_id` |
| Course | Assignment | `course_id` |
| Quiz | Question | `quiz_id` |
| Quiz | QuizAttempt | `quiz_id` |
| Assignment | Submission | `assignment_id` |
| Order | Payment | `order_id` |

### Many-to-Many

No direct many-to-many tables in current design. Relationships handled through:
- Enrollment linking User ↔ Course
- QuizAttempt linking User ↔ Quiz

---

## Migrations (Alembic)

### Migration Configuration

```python
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://user:pass@localhost:5432/lms
```

### Common Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "add courses table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show migration status
alembic current
alembic history
```

---

## Data Types

### UUID

All primary keys use UUID:
```python
id: UUID = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

### JSON/JSONB

Used for flexible data:
```python
profile_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
```

### Timestamps

All timestamps include timezone:
```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    nullable=False, 
    server_default=func.now()
)
```

---

## Constraints

### Check Constraints

```python
# User role
CheckConstraint("role IN ('admin','instructor','student')")

# Progress percentage
CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100")

# Order status
CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')")
```

### Unique Constraints

```python
# User email
UniqueConstraint('email', name='uq_user_email')

# Enrollment
UniqueConstraint('user_id', 'course_id', name='uq_enrollment_user_course')
```

---

## Performance Considerations

### Partitioning

For high-volume tables (future consideration):

```sql
-- Quiz attempts by time
CREATE TABLE quiz_attempts (
    ...
) PARTITION BY RANGE (started_at);

-- Monthly partitions
CREATE TABLE quiz_attempts_2024_01 PARTITION OF quiz_attempts
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Row Level Security

For multi-tenant scenarios:

```sql
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;

CREATE POLICY enrollments_user_policy ON enrollments
    FOR ALL
    USING (user_id = current_user_id());
```
