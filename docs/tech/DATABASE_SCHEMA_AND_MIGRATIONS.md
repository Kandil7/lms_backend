# Database Schema and Migrations

This document provides comprehensive documentation of the LMS Backend database schema, including entity relationships, migration history, and data management patterns.

---

## Table of Contents

1. [Database Overview](#database-overview)
2. [Entity Definitions](#entity-definitions)
3. [Entity Relationships](#entity-relationships)
4. [Migration History](#migration-history)
5. [Data Management](#data-management)
6. [Performance Considerations](#performance-considerations)

---

## Database Overview

The LMS Backend uses PostgreSQL as its primary relational database. PostgreSQL was chosen for its robust feature set including JSON support, full-text search capabilities, ACID compliance, and excellent performance for complex queries.

### Database Configuration

The database connection is configured through the `DATABASE_URL` environment variable:

```env
DATABASE_URL=postgresql+psycopg2://username:password@host:port/database_name
```

Connection pooling is configured with:

- `DB_POOL_SIZE`: Number of connections to maintain (default: 20)
- `DB_MAX_OVERFLOW`: Additional connections when pool is exhausted (default: 40)

SQLAlchemy's `pool_pre_ping` is enabled to verify connections before use, handling stale connections gracefully.

---

## Entity Definitions

### User Entity

The User entity is the foundation of the authentication and authorization system.

```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="student",
        index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False
    )
    profile_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", 
        JSON, 
        nullable=True
    )
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
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        index=True
    )
```

**Key Design Decisions**:

- UUID primary keys provide security through obscurity and enable distributed generation
- Email is unique and indexed for fast lookups
- Role is indexed for permission queries
- JSON metadata field allows flexible profile extensions
- Timestamps use `server_default=func.now()` for database-side timestamp generation

### Course Entity

```python
class Course(Base):
    __tablename__ = "courses"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        unique=True, 
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        index=True
    )
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        index=True
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        index=True
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True
    )
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    course_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", 
        JSON, 
        nullable=True
    )
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
```

**Indexes**:

- `ix_courses_is_published_created_at`: Composite index for listing published courses
- `ix_courses_instructor_created_at`: Composite index for instructor course lists

**Constraints**:

- Check constraint on difficulty_level: must be NULL or one of 'beginner', 'intermediate', 'advanced'

### Lesson Entity

```python
class Lesson(Base):
    __tablename__ = "lessons"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    content_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    video_url: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    order: Mapped[int] = mapped_column(
        Integer, 
        nullable=False
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )
```

**Relationships**:

- `CASCADE` delete ensures lessons are removed when course is deleted
- Ordered by `order` field within each course

### Enrollment Entity

```python
class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
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
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )
```

**Constraints**:

- Unique constraint on (student_id, course_id) prevents duplicate enrollments

### LessonProgress Entity

```python
class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
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
    completed: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )
```

**Constraints**:

- Unique constraint on (enrollment_id, lesson_id) ensures one progress record per lesson

### Quiz Entities

```python
class Quiz(Base):
    __tablename__ = "quizzes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    passing_score_percentage: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=70
    )
    shuffle_questions: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_text: Mapped[str] = mapped_column(
        Text, 
        nullable=False
    )
    question_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )
    options: Mapped[Optional[list]] = mapped_column(
        JSON, 
        nullable=True
    )
    correct_answer: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    points: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=1
    )
    order: Mapped[int] = mapped_column(
        Integer, 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    answers: Mapped[Optional[list]] = mapped_column(
        JSON, 
        nullable=True
    )
    score: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    passed: Mapped[Optional[bool]] = mapped_column(
        Boolean, 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
```

### RefreshToken Entity

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(
        String(500), 
        nullable=False,
        unique=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
```

### Certificate Entity

```python
class Certificate(Base):
    __tablename__ = "certificates"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    certificate_number: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        unique=True
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    pdf_path: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
```

---

## Entity Relationships

### Relationship Diagram

```
User (1) ──────< (M) Course (instructor_id)
User (1) ──────< (M) Enrollment (student_id)
User (1) ──────< (M) RefreshToken (user_id)
User (1) ──────< (M) QuizAttempt (student_id)

Course (1) ────< (M) Lesson (course_id)
Course (1) ────< (M) Enrollment (course_id)
Course (1) ────< (M) Quiz (course_id)
Course (1) ────< (M) Certificate (course_id)

Lesson (1) ────< (M) LessonProgress (lesson_id)
Lesson (1) ────< (M) Quiz (lesson_id)

Enrollment (1) ─< (M) LessonProgress (enrollment_id)
Enrollment (1) ─< (1) Certificate (enrollment_id)

Quiz (1) ──────< (M) QuizQuestion (quiz_id)
Quiz (1) ──────< (M) QuizAttempt (quiz_id)
```

### Cascade Rules

| Parent | Child | On Delete |
|--------|-------|-----------|
| User | Course | RESTRICT (instructors can't be deleted with courses) |
| User | Enrollment | CASCADE |
| User | RefreshToken | CASCADE |
| User | QuizAttempt | CASCADE |
| Course | Lesson | CASCADE |
| Course | Enrollment | CASCADE |
| Course | Quiz | SET NULL |
| Course | Certificate | CASCADE |
| Lesson | LessonProgress | CASCADE |
| Lesson | Quiz | SET NULL |
| Enrollment | LessonProgress | CASCADE |
| Enrollment | Certificate | CASCADE |
| Quiz | QuizQuestion | CASCADE |
| Quiz | QuizAttempt | CASCADE |

---

## Migration History

### Migration Files

The database schema evolved through these migrations:

| Migration | Description |
|-----------|-------------|
| 0001_initial_schema | Initial tables: users, courses, lessons, enrollments |
| 0002_phase1_security_and_performance | Indexes for performance, security constraints |
| 0003_phase1_infrastructure_indexes | Additional indexes for queries |
| 0004_phase1_quiz_indexes | Quiz, question, attempt tables |
| 0005_phase1_remaining_indexes | Final indexes for Phase 1 |
| 0006_add_users_email_verified_at | Email verification field |
| 0007_add_users_mfa_enabled | MFA support field |

### Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "description"

# Check current version
alembic current
```

### Migration Best Practices

1. **Never modify existing migrations**: Create new migrations for changes
2. **Test migrations locally**: Ensure they work before deploying
3. **Include downgrades**: Implement downgrade for each migration
4. **Use meaningful names**: Migration names should describe the change
5. **Keep migrations small**: Large migrations are harder to review and debug

---

## Data Management

### Seeding Data

For development and testing, use seed scripts:

```python
# scripts/seed_data.py
def seed_users():
    users = [
        {"email": "admin@lms.com", "role": "admin", "full_name": "Admin User"},
        {"email": "instructor@lms.com", "role": "instructor", "full_name": "Instructor User"},
        {"email": "student@lms.com", "role": "student", "full_name": "Student User"},
    ]
    # Create users with hashed passwords

def seed_courses():
    # Create sample courses

def seed_lessons():
    # Create sample lessons
```

### Data Retention

| Data Type | Retention Policy |
|-----------|-----------------|
| Refresh tokens | 30 days or until revoked |
| Quiz attempts | Forever |
| Session logs | 90 days |
| Audit logs | 1 year |
| Certificate records | Forever |

### Data Cleanup

```python
# Cleanup expired refresh tokens
DELETE FROM refresh_tokens 
WHERE expires_at < NOW() 
AND revoked = true;

# Cleanup old session data
DELETE FROM refresh_tokens 
WHERE expires_at < NOW() - INTERVAL '30 days';
```

---

## Performance Considerations

### Indexing Strategy

Indexes are created strategically for common query patterns:

**User Queries**:
- Email lookups: unique index on email
- Role filtering: index on role

**Course Queries**:
- Published courses: composite index on (is_published, created_at)
- Instructor courses: composite index on (instructor_id, created_at)
- Category filtering: index on category

**Enrollment Queries**:
- Student enrollments: index on student_id
- Course enrollments: index on course_id
- Unique constraint: (student_id, course_id)

**Quiz Queries**:
- Published quizzes: index on is_published
- Student attempts: composite index on (student_id, quiz_id)

### Query Optimization

**N+1 Problem Prevention**:

Use eager loading for relationships:

```python
# Bad: N+1 query
courses = db.query(Course).all()
for course in courses:
    print(course.instructor.name)  # Each iteration queries instructor

# Good: Eager loading
courses = db.query(Course).options(
    joinedload(Course.instructor)
).all()
```

**Pagination**:

Always use pagination for large datasets:

```python
def list_courses(page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    return db.query(Course).offset(offset).limit(page_size).all()
```

### Connection Pooling

Configure appropriate pool settings:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Maintain 20 connections
    max_overflow=40,      # Allow 40 overflow connections
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600,   # Recycle connections hourly
)
```

---

## Summary

The LMS Backend database schema is designed for flexibility, performance, and data integrity. Key design principles include:

1. **UUID Primary Keys**: Provide security and enable distributed generation
2. **Soft Deletes**: Preserve historical data while filtering in queries
3. **JSON Columns**: Allow flexible metadata without schema changes
4. **Cascading Deletes**: Maintain referential integrity automatically
5. **Strategic Indexes**: Optimize common query patterns

The migration system ensures schema changes are tracked and reversible. Regular maintenance including index optimization and data cleanup ensures continued performance as the database grows.
