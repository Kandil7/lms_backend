# Database Design and Schema

This document explains the database schema design, entity relationships, indexing strategies, and the reasoning behind each decision.

---

## Table of Contents

1. [Entity Relationship Diagram](#1-entity-relationship-diagram)
2. [Core Entities](#2-core-entities)
3. [User Management](#3-user-management)
4. [Course Structure](#4-course-structure)
5. [Enrollment and Progress](#5-enrollment-and-progress)
6. [Quiz System](#6-quiz-system)
7. [Files and Certificates](#7-files-and-certificates)
8. [Indexing Strategy](#8-indexing-strategy)
9. [Data Types and Constraints](#9-data-types-and-constraints)
10. [Design Decisions Explained](#10-design-decisions-explained)

---

## 1. Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐
│    User     │────▶│    Course   │
│  (roles)    │     │ (instructor)│
└─────────────┘     └──────┬──────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │   Lesson    │
       │            │  (nested)   │
       │            └──────┬──────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │    Quiz     │
       │            │ (per lesson)│
       │            └──────┬──────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │  Question   │
       └───────────▶│  (quiz)     │
              │     └─────────────┘
              ▼
┌─────────────────────┐
│    Enrollment       │───────┐
│  (student-course)   │       │
└──────────┬──────────┘       │
           │                  ▼
           │          ┌─────────────┐
           │          │LessonProgress│
           │          └─────────────┘
           │
           │          ┌─────────────┐
           └─────────▶│QuizAttempt │
                      │  (grading)  │
                      └─────────────┘
                               │
                               ▼
                      ┌─────────────┐
                      │ Certificate │
                      └─────────────┘
```

---

## 2. Core Entities

### User Entity

```python
class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")  # admin|instructor|student
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata (flexible JSON)
    metadata = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
```

### Why This Design?

| Field | Decision | Reason |
|-------|----------|--------|
| `id` as UUID | UUID4 | Distributed ID generation, not guessable |
| `email` unique | Index + Unique constraint | Required for login, no duplicates |
| `password_hash` | Separate column | Never store plain passwords |
| `role` as String | Flexible roles | Easy to add new roles |
| `metadata` JSONB | Flexible schema | Store extra user data without migrations |
| `timestamps` | Auto-managed | Consistency across all entities |

---

## 3. User Management

### Refresh Token Entity

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Token tracking
    token_jti = Column(String(255), unique=True, index=True, nullable=False)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
```

### Token Strategy

| Feature | Implementation |
|---------|----------------|
| Unique token per session | `token_jti` (UUID) |
| Expiration tracking | `expires_at` column |
| Revocation support | `revoked_at` column |
| Audit trail | `user_agent`, `ip_address` |

---

## 4. Course Structure

### Course Entity

```python
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    instructor = relationship("User", back_populates="courses")
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)
    difficulty_level = Column(String(50), nullable=True)  # beginner|intermediate|advanced
    
    # Publishing
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    
    # Media
    thumbnail_url = Column(String(1000), nullable=True)
    
    # Content
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Flexible data
    metadata = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course")
```

### Lesson Entity

```python
class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Markdown or HTML
    
    # Lesson type
    lesson_type = Column(String(50), nullable=False, default="text")  # video|text|quiz|assignment
    
    # Ordering
    order_index = Column(Integer, nullable=False, default=0)
    
    # Nested lessons (optional)
    parent_lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True)
    
    # Video content
    duration_minutes = Column(Integer, nullable=True)
    video_url = Column(String(1000), nullable=True)
    
    # Preview
    is_preview = Column(Boolean, default=False, nullable=False)
    
    # Flexible data
    metadata = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    quiz = relationship("Quiz", back_populates="lesson", uselist=False)
```

### Why This Design?

| Feature | Decision | Reason |
|---------|----------|--------|
| Course slug | Unique index | SEO-friendly URLs |
| Nested lessons | Self-referential FK | Hierarchical content |
| Lesson order | `order_index` | Explicit ordering, not dependent on ID |
| Lesson types | Type column | Different rendering for each type |
| `is_preview` | Free preview lessons | Marketing/instructional |

---

## 5. Enrollment and Progress

### Enrollment Entity

```python
class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    
    # Status
    status = Column(String(50), nullable=False, default="active")  # active|completed|dropped|expired
    
    # Progress tracking
    progress_percentage = Column(DECIMAL(5, 2), default=0)
    completed_lessons_count = Column(Integer, default=0)
    total_lessons_count = Column(Integer, default=0)
    total_time_spent_seconds = Column(Integer, default=0)
    
    # Review
    rating = Column(Integer, nullable=True)  # 1-5
    review = Column(Text, nullable=True)
    
    # Certificate
    certificate_issued_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    lesson_progress = relationship("LessonProgress", back_populates="enrollment", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="enrollment")
    certificate = relationship("Certificate", back_populates="enrollment", uselist=False)
```

### Lesson Progress Entity

```python
class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, index=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False, index=True)
    
    # Status
    status = Column(String(50), nullable=False, default="not_started")  # not_started|in_progress|completed
    
    # Time tracking
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    
    # Completion
    completion_percentage = Column(DECIMAL(5, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="lesson_progress")
    lesson = relationship("Lesson")
```

### Progress Calculation Logic

```python
def calculate_progress(enrollment: Enrollment) -> Enrollment:
    """Calculate enrollment progress based on lesson progress."""
    
    # Get all lessons in course
    total_lessons = len(enrollment.course.lessons)
    
    # Count completed lessons
    completed = sum(
        1 for lp in enrollment.lesson_progress 
        if lp.status == "completed"
    )
    
    # Calculate percentage
    progress = (completed / total_lessons * 100) if total_lessons > 0 else 0
    
    # Update enrollment
    enrollment.completed_lessons_count = completed
    enrollment.total_lessons_count = total_lessons
    enrollment.progress_percentage = progress
    
    if progress >= 100 and enrollment.status != "completed":
        enrollment.status = "completed"
        enrollment.completed_at = datetime.utcnow()
    
    return enrollment
```

---

## 6. Quiz System

### Quiz Entity

```python
class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), unique=True, index=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Quiz settings
    quiz_type = Column(String(50), nullable=False, default="practice")  # practice|graded
    passing_score = Column(Integer, default=70)  # Percentage
    time_limit_minutes = Column(Integer, nullable=True)
    max_attempts = Column(Integer, default=3)
    
    # Display settings
    shuffle_questions = Column(Boolean, default=False)
    shuffle_options = Column(Boolean, default=False)
    show_correct_answers = Column(Boolean, default=False)
    
    # Publishing
    is_published = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
```

### Quiz Question Entity

```python
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False, index=True)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice|true_false|short_answer
    points = Column(Integer, default=1)
    order_index = Column(Integer, nullable=False, default=0)
    
    # Content stored as JSON for flexibility
    # Multiple choice: {"options": [{"text": "...", "is_correct": true}], "explanation": "..."}
    options = Column(JSONB, nullable=True)
    correct_answer = Column(JSONB, nullable=True)  # For non-multiple choice
    
    explanation = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
```

### Quiz Attempt Entity

```python
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, index=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False, index=True)
    
    # Attempt tracking
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="in_progress")  # in_progress|submitted|graded
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scoring
    score = Column(DECIMAL(10, 2), nullable=True)
    max_score = Column(DECIMAL(10, 2), nullable=True)
    percentage = Column(DECIMAL(5, 2), nullable=True)
    is_passed = Column(Boolean, nullable=True)
    
    # Time tracking
    time_taken_seconds = Column(Integer, nullable=True)
    
    # Answers stored as JSON
    answers = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="quiz_attempts")
    quiz = relationship("Quiz")
```

---

## 7. Files and Certificates

### Uploaded File Entity

```python
class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    
    # File metadata
    file_type = Column(String(100), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    
    # Organization
    folder = Column(String(255), nullable=True)
    
    # Storage provider
    storage_provider = Column(String(50), default="local")  # local|s3
    
    # Access
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Certificate Entity

```python
class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), unique=True, index=True)
    
    # Links
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    
    # Certificate data
    certificate_number = Column(String(100), unique=True, nullable=False)
    pdf_path = Column(String(1000), nullable=True)
    
    # Dates
    completion_date = Column(DateTime(timezone=True), nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Revocation
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="certificate")
```

---

## 8. Indexing Strategy

### Indexes by Table

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| `users` | `email` | Unique | Login lookups |
| `courses` | `slug` | Unique | SEO URLs |
| `courses` | `is_published` | BTree | Published courses filter |
| `courses` | `category` | BTree | Category browsing |
| `lessons` | `course_id` | BTree | Course lessons |
| `enrollments` | `student_id` | BTree | Student enrollments |
| `enrollments` | `course_id` | BTree | Course enrollments |
| `lesson_progress` | `enrollment_id` | BTree | Enrollment progress |
| `lesson_progress` | `lesson_id` | BTree | Lesson progress |
| `quiz_attempts` | `enrollment_id` | BTree | Student attempts |
| `quiz_attempts` | `quiz_id` | BTree | Quiz attempts |

### Why These Indexes?

1. **Foreign Keys** - All FK columns are indexed for JOIN performance
2. **Unique Constraints** - Unique indexes for email, slug, etc.
3. **Filter Columns** - `is_published`, `status` frequently filtered
4. **Query Patterns** - Indexes match actual query patterns

---

## 9. Data Types and Constraints

### UUID vs Integer IDs

```python
# Using UUID
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

# Why not Integer?
# - Integer: Simple, smaller, but predictable
# - UUID: Distributed, not guessable, no collision
```

**Decision:** UUID for all primary keys. Security through obscurity, easier distributed systems.

### JSONB for Flexible Data

```python
# Use JSONB for flexible fields
metadata = Column(JSONB, default={})
options = Column(JSONB, nullable=True)
```

**Decision:** JSONB when:
- Schema may evolve
- Different entities have different fields
- Need to store nested data

**Alternative:** Use separate columns when:
- Always present
- Queried frequently
- Need indexing

### DECIMAL for Money/Percentages

```python
# Use DECIMAL, not FLOAT
progress_percentage = Column(DECIMAL(5, 2))  # 0.00 to 100.00
score = Column(DECIMAL(10, 2))
```

**Decision:** DECIMAL for:
- Money (never use FLOAT for money!)
- Percentages
- Any value requiring exact precision

---

## 10. Design Decisions Explained

### Decision 1: Course-Lesson Hierarchy

**Question:** Why nest lessons under courses with FK instead of separate tables?

**Answer:**
- Simpler queries: Get all lessons for a course
- Cascading: Delete course deletes lessons
- Consistency: Lessons always belong to a course

---

### Decision 2: Separate Progress Table

**Question:** Why not store progress directly in Enrollment?

**Answer:**
- Granular tracking per lesson
- Supports resuming from specific lesson
- Historical record of activity
- Better analytics

---

### Decision 3: Quiz per Lesson

**Question:** Why one quiz per lesson limit?

**Answer:**
- Simpler user experience
- Clear assessment after each lesson
- Can be extended to multiple quizzes if needed

---

### Decision 4: Certificate per Enrollment

**Question:** Why unique constraint on enrollment_id for certificates?

**Answer:**
- One certificate per course completion
- Prevents duplicate certificates
- Easy verification

---

### Decision 5: Soft Delete Pattern

**Question:** Is there soft delete?

**Answer:** Currently no, but can be added:

```python
class Course(Base):
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    __mapper_args__ = {"exclude_properties": ["is_deleted"]}
```

---

## Database Summary

| Entity | Purpose | Key Fields |
|--------|---------|------------|
| `User` | Authentication & profiles | email, role, metadata |
| `RefreshToken` | Auth token management | token_jti, expires_at |
| `Course` | Course content | title, slug, instructor |
| `Lesson` | Course modules | content, order, video |
| `Enrollment` | Student-course link | status, progress |
| `LessonProgress` | Per-lesson tracking | status, time_spent |
| `Quiz` | Assessment config | passing_score, time_limit |
| `QuizQuestion` | Quiz content | question, options, answer |
| `QuizAttempt` | Student submissions | score, answers |
| `UploadedFile` | File management | storage_path, mime_type |
| `Certificate` | Completion proof | certificate_number |

This schema design provides:
- **Normalization** - Reduced data redundancy
- **Relationships** - Clear entity connections
- **Flexibility** - JSONB for evolving data
- **Performance** - Strategic indexing
- **Scalability** - UUID for distributed systems
