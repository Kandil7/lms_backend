# Modules Detailed Guide

## Complete Module-by-Module Documentation

This document provides in-depth details about every module in the LMS backend, including their functionality, API endpoints, data models, and business logic.

---

## 1. Authentication Module (auth)

### Purpose
Handle all authentication-related operations including registration, login, token management, MFA, password reset, and email verification.

### Features

| Feature | Description |
|---------|-------------|
| User Registration | Create new user accounts |
| Login | Authenticate with email/password |
| Token Management | JWT access and refresh tokens |
| MFA | Email-based multi-factor authentication |
| Password Reset | Secure password reset flow |
| Email Verification | Verify user email addresses |

### Data Models

```python
# app/modules/auth/models.py

class RefreshToken(Base):
    """Refresh tokens for session management"""
    __tablename__ = "refresh_tokens"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    token_jti: Mapped[str] = mapped_column(unique=True)  # Token unique ID
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

### API Endpoints

```
POST   /api/v1/auth/register              - Register new user
POST   /api/v1/auth/login                 - Login with credentials
POST   /api/v1/auth/token                 - OAuth2 token endpoint
POST   /api/v1/auth/login/mfa             - Verify MFA code
POST   /api/v1/auth/refresh               - Refresh access token
POST   /api/v1/auth/logout                - Logout (revoke tokens)
POST   /api/v1/auth/forgot-password        - Request password reset
POST   /api/v1/auth/reset-password         - Reset password
POST   /api/v1/auth/verify-email/request   - Request email verification
POST   /api/v1/auth/verify-email/confirm   - Confirm email verification
POST   /api/v1/auth/mfa/enable/request     - Request MFA enable
POST   /api/v1/auth/mfa/enable/confirm     - Confirm MFA enable
POST   /api/v1/auth/mfa/disable           - Disable MFA
GET    /api/v1/auth/me                    - Get current user
```

### Authentication Flow

```python
# Registration
@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Validate email not exists
    existing = await user_repo.get_by_email(db, user_data.email)
    if existing:
        raise DuplicateEmailError()
    
    # 2. Hash password
    password_hash = hash_password(user_data.password)
    
    # 3. Create user
    user = User(
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role
    )
    await db.commit()
    
    # 4. Generate tokens
    access_token = create_access_token(user.id, user.role)
    refresh_token = await create_refresh_token(db, user.id)
    
    return AuthResponse(user=user, access_token=access_token, refresh_token=refresh_token)
```

### Security Features

- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with short expiry (15 min)
- Refresh tokens stored in database
- Token blacklist in Redis
- MFA support via email OTP
- Rate limiting on auth endpoints

---

## 2. Users Module

### Purpose
Manage user accounts, profiles, and admin-level user operations.

### Features

| Feature | Description |
|---------|-------------|
| User Profile | View and update own profile |
| Admin Management | Create, read, update users |
| Role Management | Assign roles to users |
| Account Status | Activate/deactivate users |

### Data Models

```python
# app/modules/users/models.py

class User(Base):
    """Main user model"""
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="student")  # admin, instructor, student
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email_verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="instructor")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="student")
```

### API Endpoints

```
GET    /api/v1/users                    - List all users (admin)
POST   /api/v1/users                    - Create user (admin)
GET    /api/v1/users/{user_id}         - Get user by ID (admin)
PATCH  /api/v1/users/{user_id}         - Update user (admin)
GET    /api/v1/users/me                - Get my profile
PATCH  /api/v1/users/me                - Update my profile
```

### User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full system access, user management |
| `instructor` | Create/manage courses, view analytics |
| `student` | Enroll in courses, take quizzes |

---

## 3. Courses Module

### Purpose
Manage courses and lessons, including content creation, organization, and publishing.

### Features

| Feature | Description |
|---------|-------------|
| Course CRUD | Create, read, update, delete courses |
| Lesson Management | Add lessons to courses |
| Categories | Organize courses by category |
| Difficulty Levels | beginner, intermediate, advanced |
| Publishing | Draft/published workflow |
| Thumbnails | Course cover images |

### Data Models

```python
# app/modules/courses/models/course.py

class Course(Base):
    """Course model"""
    __tablename__ = "courses"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    instructor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    difficulty_level: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=True)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    course_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="courses")
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="course")

# app/modules/courses/models/lesson.py

class Lesson(Base):
    """Lesson model"""
    __tablename__ = "lessons"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)  # For text lessons
    lesson_type: Mapped[str] = mapped_column(String(50))  # video, text, quiz, assignment
    order_index: Mapped[int] = mapped_column(Integer)
    parent_lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id"), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    video_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False)  # Free preview
    lesson_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="lesson", uselist=False)
    progress: Mapped[List["LessonProgress"]] = relationship("LessonProgress", back_populates="lesson")
```

### Lesson Types

| Type | Description |
|------|-------------|
| `video` | Video content with URL |
| `text` | Text/markdown content |
| `quiz` | Quiz assessment |
| `assignment` | Assignment submission |

### API Endpoints

```
GET    /api/v1/courses                          - List courses (with filters)
POST   /api/v1/courses                         - Create course
GET    /api/v1/courses/{course_id}             - Get course
PATCH  /api/v1/courses/{course_id}             - Update course
DELETE /api/v1/courses/{course_id}             - Delete course
POST   /api/v1/courses/{course_id}/publish     - Publish course

GET    /api/v1/courses/{course_id}/lessons     - List lessons
POST   /api/v1/courses/{course_id}/lessons     - Create lesson
GET    /api/v1/lessons/{lesson_id}             - Get lesson
PATCH  /api/v1/lessons/{lesson_id}             - Update lesson
DELETE /api/v1/lessons/{lesson_id}             - Delete lesson
```

---

## 4. Enrollments Module

### Purpose
Track student enrollments, progress, and course completion.

### Features

| Feature | Description |
|---------|-------------|
| Enrollment | Student enrolls in course |
| Progress Tracking | Track lesson completion |
| Time Tracking | Time spent on lessons |
| Course Reviews | Rating and review system |
| Completion | Certificate issuance on completion |

### Data Models

```python
# app/modules/enrollments/models.py

class Enrollment(Base):
    """Enrollment model"""
    __tablename__ = "enrollments"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, completed, dropped, expired
    progress_percentage: Mapped[float] = mapped_column(Numeric(5,2), default=0)
    completed_lessons_count: Mapped[int] = mapped_column(Integer, default=0)
    total_lessons_count: Mapped[int] = mapped_column(Integer, default=0)
    total_time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    certificate_issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)  # 1-5
    review: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    lesson_progress: Mapped[List["LessonProgress"]] = relationship("LessonProgress", back_populates="enrollment")
    quiz_attempts: Mapped[List["QuizAttempt"]] = relationship("QuizAttempt", back_populates="enrollment")

class LessonProgress(Base):
    """Track progress on individual lessons"""
    __tablename__ = "lesson_progress"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"))
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id"))
    status: Mapped[str] = mapped_column(String(50), default="not_started")  # not_started, in_progress, completed
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    last_position_seconds: Mapped[int] = mapped_column(Integer, default=0)  # Video position
    completion_percentage: Mapped[float] = mapped_column(Numeric(5,2), default=0)
    attempts_count: Mapped[int] = mapped_column(Integer, default=0)
    progress_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="progress")
```

### API Endpoints

```
POST   /api/v1/enrollments                           - Enroll in course
GET    /api/v1/enrollments/my-courses                - My enrollments
GET    /api/v1/enrollments/{enrollment_id}          - Get enrollment
PUT    /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress - Update progress
POST   /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/complete - Mark complete
POST   /api/v1/enrollments/{enrollment_id}/review    - Submit review
GET    /api/v1/enrollments/courses/{course_id}      - Course enrollments
GET    /api/v1/enrollments/courses/{course_id}/stats - Course statistics
```

---

## 5. Quizzes Module

### Purpose
Create and manage quizzes with various question types, grading, and attempts.

### Features

| Feature | Description |
|---------|-------------|
| Quiz Creation | Create quizzes attached to lessons |
| Question Types | Multiple choice, true/false, short answer, essay |
| Attempts | Multiple attempts with limits |
| Grading | Automatic grading for objective questions |
| Time Limits | Optional time limits |
| Randomization | Shuffle questions and options |

### Data Models

```python
# app/modules/quizzes/models/quiz.py

class Quiz(Base):
    """Quiz model"""
    __tablename__ = "quizzes"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id"), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    quiz_type: Mapped[str] = mapped_column(String(50), default="graded")  # practice, graded
    passing_score: Mapped[float] = mapped_column(Numeric(5,2), default=70.0)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=True)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=True)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, default=True)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="quiz")
    questions: Mapped[List["QuizQuestion"]] = relationship("QuizQuestion", back_populates="quiz")
    attempts: Mapped[List["QuizAttempt"]] = relationship("QuizAttempt", back_populates="quiz")

# app/modules/quizzes/models/question.py

class QuizQuestion(Base):
    """Quiz question model"""
    __tablename__ = "quiz_questions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id"))
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(50))  # multiple_choice, true_false, short_answer, essay
    points: Mapped[float] = mapped_column(Numeric(5,2), default=1.0)
    order_index: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    options: Mapped[list] = mapped_column(JSONB, nullable=True)  # For multiple choice
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=True)
    question_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")

# app/modules/quizzes/models/attempt.py

class QuizAttempt(Base):
    """Quiz attempt model"""
    __tablename__ = "quiz_attempts"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"))
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id"))
    attempt_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="in_progress")  # in_progress, submitted, graded
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    graded_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    score: Mapped[float] = mapped_column(Numeric(6,2), nullable=True)
    max_score: Mapped[float] = mapped_column(Numeric(6,2), nullable=True)
    percentage: Mapped[float] = mapped_column(Numeric(6,2), nullable=True)
    is_passed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    answers: Mapped[list] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="quiz_attempts")
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="attempts")
```

### Question Types

| Type | Grading | Options |
|------|---------|---------|
| `multiple_choice` | Automatic | JSON array of options |
| `true_false` | Automatic | true/false |
| `short_answer` | Manual | Text match (optional) |
| `essay` | Manual | No auto-grading |

### API Endpoints

```
GET    /api/v1/courses/{course_id}/quizzes                - List quizzes
POST   /api/v1/courses/{course_id}/quizzes                - Create quiz
GET    /api/v1/courses/{course_id}/quizzes/{quiz_id}     - Get quiz
PATCH  /api/v1/courses/{course_id}/quizzes/{quiz_id}     - Update quiz
POST   /api/v1/courses/{course_id}/quizzes/{quiz_id}/publish - Publish quiz

GET    /api/v1/quizzes/{quiz_id}/questions                - List questions (public)
GET    /api/v1/quizzes/{quiz_id}/questions/manage         - List questions (manage)
POST   /api/v1/quizzes/{quiz_id}/questions                 - Add question
PATCH  /api/v1/quizzes/{quiz_id}/questions/{question_id}  - Update question

POST   /api/v1/quizzes/{quiz_id}/attempts                  - Start attempt
GET    /api/v1/quizzes/{quiz_id}/attempts/start           - Get quiz for taking
POST   /api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit - Submit answers
GET    /api/v1/quizzes/{quiz_id}/attempts/{attempt_id}     - Get attempt result
GET    /api/v1/quizzes/{quiz_id}/attempts/my-attempts     - My attempts
```

---

## 6. Certificates Module

### Purpose
Generate and manage course completion certificates.

### Features

| Feature | Description |
|---------|-------------|
| Auto-Generation | Generate on course completion |
| PDF Generation | Professional PDF certificates |
| Verification | Public certificate verification |
| Revocation | Revoke invalid certificates |

### Data Model

```python
# app/modules/certificates/models.py

class Certificate(Base):
    """Certificate model"""
    __tablename__ = "certificates"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"), unique=True)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    certificate_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    pdf_path: Mapped[str] = mapped_column(String(1024))
    completion_date: Mapped[datetime] = mapped_column(DateTime)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="certificate")
    student: Mapped["User"] = relationship("User")
    course: Mapped["Course"] = relationship("Course")
```

### Certificate Number Format

```
Certificate Number: CERT-YYYYMMDD-XXXXXXXX
Example: CERT-20240115-A7F3B2C1
```

### API Endpoints

```
GET    /api/v1/certificates/my-certificates              - My certificates
GET    /api/v1/certificates/{certificate_id}/download    - Download PDF
GET    /api/v1/certificates/verify/{certificate_number} - Verify certificate
POST   /api/v1/certificates/{certificate_id}/revoke     - Revoke certificate
POST   /api/v1/certificates/enrollments/{enrollment_id}/generate - Generate certificate
```

---

## 7. Analytics Module

### Purpose
Provide dashboards and reporting for students, instructors, and administrators.

### Features

| Feature | Description |
|---------|-------------|
| Student Dashboard | Personal progress and courses |
| Instructor Analytics | Course performance, student counts |
| System Overview | Platform-wide metrics (admin) |

### API Endpoints

```
GET    /api/v1/analytics/my-progress                     - My progress summary
GET    /api/v1/analytics/my-dashboard                     - Student dashboard
GET    /api/v1/analytics/courses/{course_id}             - Course analytics
GET    /api/v1/analytics/instructors/{instructor_id}/overview - Instructor overview
GET    /api/v1/analytics/system/overview                 - System overview (admin)
```

### Analytics Response Examples

```python
# Student Dashboard
{
    "total_courses_enrolled": 5,
    "courses_completed": 2,
    "total_time_spent_seconds": 36000,
    "average_progress": 65.5,
    "certificates_earned": 2,
    "recent_activity": [...]
}

# Course Analytics
{
    "total_enrollments": 150,
    "active_students": 120,
    "completion_rate": 45.5,
    "average_rating": 4.2,
    "average_progress": 68.0,
    "lesson_completion_rates": {...}
}
```

---

## 8. Files Module

### Purpose
Handle file uploads for course materials and user content.

### Features

| Feature | Description |
|---------|-------------|
| File Upload | Upload to local or S3 storage |
| File Types | Images, videos, documents |
| Public/Private | Access control per file |
| Download | Stream or redirect downloads |

### Data Model

```python
# app/modules/files/models.py

class UploadedFile(Base):
    """Uploaded file model"""
    __tablename__ = "uploaded_files"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    uploader_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(1024))
    storage_path: Mapped[str] = mapped_column(String(1024))
    file_type: Mapped[str] = mapped_column(String(50), default="other")
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(BigInteger)
    folder: Mapped[str] = mapped_column(String(100), default="uploads")
    storage_provider: Mapped[str] = mapped_column(String(50), default="local")  # local or s3
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader: Mapped["User"] = relationship("User")
```

### Storage Backends

```python
# Local Storage (default)
storage_path = "uploads/{year}/{month}/{filename}"

# S3 Storage (production)
# Uses pre-signed URLs for secure access
```

### API Endpoints

```
POST   /api/v1/files/upload                    - Upload file
GET    /api/v1/files/my-files                   - My files
GET    /api/v1/files/download/{file_id}         - Download file
```

---

## 9. Payments Module

### Purpose
Process payments and manage subscriptions with multiple payment providers.

### Supported Providers

| Provider | Type | Use Case |
|----------|------|----------|
| MyFatoorah | Regional | Primary EGP payments |
| Stripe | Global | International, subscriptions |
| Paymob | Regional | Alternative Egyptian provider |

### Data Models

```python
# app/modules/payments/models.py

class Payment(Base):
    """Payment model"""
    __tablename__ = "payments"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), nullable=True)
    stripe_invoice_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"), nullable=True)
    subscription_id: Mapped[UUID] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)
    payment_type: Mapped[str] = mapped_column(String(20))  # one_time, recurring, trial
    amount: Mapped[float] = mapped_column(Numeric(10,2))
    currency: Mapped[str] = mapped_column(String(3), default="EGP")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, succeeded, failed, refunded
    plan_name: Mapped[str] = mapped_column(String(100), nullable=True)
    plan_price_id: Mapped[str] = mapped_column(String(255), nullable=True)
    tax_amount: Mapped[float] = mapped_column(Numeric(10,2), default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(10,2))
    payment_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    enrollment: Mapped["Enrollment"] = relationship("Enrollment")
    subscription: Mapped["Subscription"] = relationship("Subscription")

class Subscription(Base):
    """Subscription model"""
    __tablename__ = "subscriptions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    plan_name: Mapped[str] = mapped_column(String(100))
    plan_price_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="incomplete")  # trial, active, past_due, canceled, incomplete
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    courses_accessed: Mapped[int] = mapped_column(Integer, default=0)
    total_usage: Mapped[int] = mapped_column(Integer, default=0)
    subscription_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    canceled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class PaymentWebhookEvent(Base):
    """Payment webhook event model"""
    __tablename__ = "payment_webhook_events"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    stripe_event_id: Mapped[str] = mapped_column(String(255), unique=True)
    event_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing, processed, failed
    payload: Mapped[str] = mapped_column(Text)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
```

### API Endpoints

```
POST   /api/v1/payments/create-payment-intent          - Create payment intent
POST   /api/v1/payments/create-subscription            - Create subscription
GET    /api/v1/payments/my-payments                    - My payments
GET    /api/v1/payments/my-subscriptions              - My subscriptions
GET    /api/v1/payments/revenue/summary               - Revenue summary (admin)
POST   /api/v1/payments/webhooks/myfatoorah            - MyFatoorah webhook
POST   /api/v1/payments/webhooks/paymob                - Paymob webhook
POST   /api/v1/payments/webhooks/stripe                - Stripe webhook
```

---

## 10. Emails Module

### Purpose
Send transactional emails using templates via background tasks.

### Email Templates

| Template | Trigger |
|----------|----------|
| Welcome | User registration |
| Password Reset | Forgot password request |
| Email Verification | Registration, email change |
| Course Enrolled | Enrollment confirmation |
| Course Completed | Completion notification |
| Certificate Issued | Certificate generation |
| Weekly Progress | Weekly summary |
| Course Reminder | Inactive student reminder |

### Template Structure

```html
<!-- app/modules/emails/templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { background: #4F46E5; color: white; padding: 20px; }
        .content { padding: 20px; }
        .footer { background: #f3f4f6; padding: 20px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
        </div>
        <div class="content">
            {{ content }}
        </div>
        <div class="footer">
            {{ footer }}
        </div>
    </div>
</body>
</html>
```

### Sending Emails

```python
# Via Celery task
@celery_app.task
def send_email_task(recipient: str, subject: str, template: str, context: dict):
    # Render template
    html = render_email_template(template, context)
    
    # Send via FastAPI-Mail
    send_email(
        recipients=[recipient],
        subject=subject,
        html=html
    )
```

---

## Summary

This LMS backend includes 10 comprehensive modules:

| Module | Key Features |
|--------|--------------|
| Auth | JWT, MFA, Password reset, Email verification |
| Users | Profile, Admin management, Roles |
| Courses | CRUD, Lessons, Publishing, Categories |
| Enrollments | Progress tracking, Reviews, Completion |
| Quizzes | Questions, Attempts, Grading, Time limits |
| Certificates | PDF generation, Verification, Revocation |
| Analytics | Dashboards, Reports, Metrics |
| Files | Upload, Storage (Local/S3), Download |
| Payments | Multiple providers, Subscriptions, Webhooks |
| Emails | Templates, Background sending, Multiple triggers |

Each module follows consistent patterns for:
- Data models (SQLAlchemy)
- Schemas (Pydantic)
- API routes (FastAPI)
- Business logic (Services)
