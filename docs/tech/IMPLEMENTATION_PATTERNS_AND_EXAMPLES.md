# Implementation Patterns and Code Examples

This document provides practical implementation patterns and code examples used throughout the LMS Backend project. It serves as a reference for developers working on the codebase.

---

## Table of Contents

1. [Service Layer Patterns](#service-layer-patterns)
2. [Repository Layer Patterns](#repository-layer-patterns)
3. [Router Implementation Patterns](#router-implementation-patterns)
4. [Database Model Patterns](#database-model-patterns)
5. [Schema Patterns](#schema-patterns)
6. [Dependency Injection Patterns](#dependency-injection-patterns)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Testing Patterns](#testing-patterns)
9. [Background Task Patterns](#background-task-patterns)

---

## Service Layer Patterns

Services contain business logic and orchestrate operations across repositories. They should remain thin wrappers around repository calls, with business rules and validation logic.

### Basic Service Structure

```python
class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CourseRepository(db)
    
    def get_course(self, course_id: UUID, current_user: Optional[User]) -> Course:
        course = self.repository.get_by_id(course_id)
        
        if not course:
            raise NotFoundException(f"Course {course_id} not found")
        
        # Check visibility
        if not course.is_published and current_user:
            if course.instructor_id != current_user.id:
                if current_user.role != Role.ADMIN:
                    raise NotFoundException(f"Course {course_id} not found")
        
        return course
```

### Service with Caching

```python
class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CourseRepository(db)
        self.cache = get_app_cache()
    
    def list_courses(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> dict:
        # Build cache key based on parameters
        cache_key = f"courses:list:page={page}:size={page_size}:cat={category}"
        
        # Try cache first
        cached = self.cache.get_json(cache_key)
        if cached:
            return cached
        
        # Get from database
        courses = self.repository.list_courses(
            page=page,
            page_size=page_size,
            category=category,
            published_only=not current_user
        )
        
        # Transform to response format
        result = {
            "items": [CourseResponse.model_validate(c) for c in courses],
            "total": len(courses)
        }
        
        # Cache result
        self.cache.set_json(
            cache_key, 
            result, 
            ttl_seconds=settings.COURSE_CACHE_TTL_SECONDS
        )
        
        return result
```

### Service with Business Rules

```python
class EnrollmentService:
    def __init__(self, db: Session):
        self.db = db
        self.enrollment_repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)
    
    def enroll_student(
        self, 
        student_id: UUID, 
        course_id: UUID
    ) -> Enrollment:
        # Business rule: Check if already enrolled
        existing = self.enrollment_repo.find_by_student_and_course(
            student_id, course_id
        )
        if existing:
            raise ConflictException("Already enrolled in this course")
        
        # Business rule: Check if course exists and is published
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")
        
        if not course.is_published:
            raise ConflictException("Cannot enroll in unpublished course")
        
        # Create enrollment
        enrollment = self.enrollment_repo.create(
            student_id=student_id,
            course_id=course_id
        )
        
        # Create lesson progress records for all lessons
        self._create_progress_records(enrollment, course.lessons)
        
        return enrollment
    
    def _create_progress_records(
        self, 
        enrollment: Enrollment, 
        lessons: List[Lesson]
    ) -> None:
        for lesson in lessons:
            progress = LessonProgress(
                enrollment_id=enrollment.id,
                lesson_id=lesson.id
            )
            self.db.add(progress)
        
        self.db.commit()
```

---

## Repository Layer Patterns

Repositories handle all database operations. They should be focused on data access, with no business logic.

### Basic Repository Structure

```python
class CourseRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, course_id: UUID) -> Optional[Course]:
        return (
            self.db.query(Course)
            .filter(Course.id == course_id)
            .first()
        )
    
    def get_by_slug(self, slug: str) -> Optional[Course]:
        return (
            self.db.query(Course)
            .filter(Course.slug == slug)
            .first()
        )
    
    def list_courses(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        published_only: bool = True
    ) -> List[Course]:
        query = self.db.query(Course)
        
        if published_only:
            query = query.filter(Course.is_published == True)
        
        if category:
            query = query.filter(Course.category == category)
        
        if difficulty:
            query = query.filter(Course.difficulty_level == difficulty)
        
        query = query.order_by(Course.created_at.desc())
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        return query.all()
    
    def create(self, course_data: dict) -> Course:
        course = Course(**course_data)
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def update(self, course: Course, update_data: dict) -> Course:
        for key, value in update_data.items():
            if value is not None:
                setattr(course, key, value)
        
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def delete(self, course: Course) -> None:
        self.db.delete(course)
        self.db.commit()
```

### Repository with Relationships

```python
class EnrollmentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, enrollment_id: UUID) -> Optional[Enrollment]:
        return (
            self.db.query(Enrollment)
            .options(
                joinedload(Enrollment.student),
                joinedload(Enrollment.course)
            )
            .filter(Enrollment.id == enrollment_id)
            .first()
        )
    
    def get_student_enrollments(
        self, 
        student_id: UUID,
        completed: Optional[bool] = None
    ) -> List[Enrollment]:
        query = (
            self.db.query(Enrollment)
            .options(
                joinedload(Enrollment.course).joinedload(Course.instructor)
            )
            .filter(Enrollment.student_id == student_id)
        )
        
        if completed is not None:
            if completed:
                query = query.filter(Enrollment.completed_at.isnot(None))
            else:
                query = query.filter(Enrollment.completed_at.is_(None))
        
        return query.order_by(Enrollment.enrolled_at.desc()).all()
```

---

## Router Implementation Patterns

Routers define API endpoints. They handle HTTP concerns like request parsing and response formatting, delegating business logic to services.

### Basic Router Pattern

```python
router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=CourseListResponse)
def list_courses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> CourseListResponse:
    service = CourseService(db)
    result = service.list_courses(
        page=page,
        page_size=page_size,
        category=category,
        current_user=current_user
    )
    return CourseListResponse(**result)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> CourseResponse:
    service = CourseService(db)
    course = service.get_course(course_id, current_user)
    return CourseResponse.model_validate(course)


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CourseResponse:
    if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can create courses"
        )
    
    service = CourseService(db)
    course = service.create_course(payload, current_user)
    return CourseResponse.model_validate(course)
```

### Router with Permission Checks

```python
@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CourseResponse:
    service = CourseService(db)
    
    # Get course to check ownership
    course = service.get_course_for_update(course_id)
    
    # Permission check: owner or admin
    if course.instructor_id != current_user.id:
        if current_user.role != Role.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this course"
            )
    
    course = service.update_course(course_id, payload)
    return CourseResponse.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    service = CourseService(db)
    course = service.get_course_for_update(course_id)
    
    if course.instructor_id != current_user.id:
        if current_user.role != Role.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this course"
            )
    
    service.delete_course(course_id)
```

---

## Database Model Patterns

Models define the database schema using SQLAlchemy. They include relationships, constraints, and indexes.

### Basic Model Pattern

```python
class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "difficulty_level IS NULL OR "
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_courses_difficulty_level"
        ),
        Index("ix_courses_published_created", "is_published", "created_at"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        unique=True, 
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
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
    
    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="courses")
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson", 
        back_populates="course", 
        cascade="all, delete-orphan",
        order_by="Lesson.order"
    )
```

### Model with JSON Metadata

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # JSON metadata for extensibility
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    
    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
```

---

## Schema Patterns

Pydantic schemas define request/response validation. They use type hints, validators, and configuration for automatic documentation.

### Request Schema Pattern

```python
class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    difficulty_level: Optional[str] = Field(
        None, 
        pattern="^(beginner|intermediate|advanced)$"
    )
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    metadata: Optional[dict] = None
    
    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip()
    
    @field_validator("slug", mode="before")
    @classmethod
    def generate_slug(cls, v: Optional[str], info: data) -> str:
        if v:
            return v.lower().replace(" ", "-")
        # Generate from title if not provided
        if "title" in info.data:
            return info.data["title"].lower().replace(" ", "-")
        return v
    
    model_config = ConfigDict(str_strip_whitespace=True)
```

### Response Schema Pattern

```python
class CourseResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: Optional[str]
    category: Optional[str]
    difficulty_level: Optional[str]
    is_published: bool
    thumbnail_url: Optional[str]
    estimated_duration_minutes: Optional[int]
    instructor_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Include related data
    lessons: List[LessonResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    items: List[CourseResponse]
    total: int
    page: int
    page_size: int
    pages: int
    
    @classmethod
    def from_pagination(
        cls,
        items: List[Course],
        total: int,
        page: int,
        page_size: int
    ) -> "CourseListResponse":
        return cls(
            items=[CourseResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
```

---

## Dependency Injection Patterns

FastAPI's dependency injection system provides reusable components for route handlers.

### Current User Dependencies

```python
# Get current user (required)
def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> User:
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException("Invalid authorization header")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        payload = security.decode_token(token)
        user_id = payload.get("sub")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedException("User not found")
        
        if not user.is_active:
            raise UnauthorizedException("User account is disabled")
        
        return user
    except JWTError:
        raise UnauthorizedException("Invalid token")


# Get current user (optional)
def get_current_user_optional(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not authorization:
        return None
    
    try:
        return get_current_user(authorization, db)
    except UnauthorizedException:
        return None
```

### Database Session Dependency

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Usage in router
@router.get("/items")
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

---

## Error Handling Patterns

The project uses custom exceptions that are converted to HTTP responses by exception handlers.

### Custom Exception

```python
class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
```

### Exception Handler Registration

```python
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(ConflictException)
    async def conflict_handler(request: Request, exc: ConflictException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request: Request, exc: UnauthorizedException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={"WWW-Authenticate": "Bearer"}
        )
```

---

## Testing Patterns

Tests use pytest fixtures and the FastAPI TestClient for integration testing.

### Test Fixtures

```python
# conftest.py
@pytest.fixture
def db_session():
    """Create a test database session."""
    # Use SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=security.hash_password("password123"),
        role="student"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authorization headers for test user."""
    token = security.create_access_token(
        test_user.email, 
        test_user.role
    )
    return {"Authorization": f"Bearer {token}"}
```

### Integration Test

```python
# test_courses.py
def test_list_courses(client, db_session):
    """Test listing courses."""
    # Create test courses
    course = Course(
        title="Test Course",
        slug="test-course",
        description="A test course",
        is_published=True,
        instructor_id=uuid.uuid4()
    )
    db_session.add(course)
    db_session.commit()
    
    # Make request
    response = client.get("/api/v1/courses")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test Course"


def test_create_course_as_student(client, db_session, auth_headers):
    """Test that students cannot create courses."""
    response = client.post(
        "/api/v1/courses",
        headers=auth_headers,
        json={
            "title": "New Course",
            "description": "Course description"
        }
    )
    
    assert response.status_code == 403


def test_create_course_as_instructor(client, db_session, test_user):
    """Test that instructors can create courses."""
    # Update user to instructor
    test_user.role = "instructor"
    db_session.commit()
    
    # Get auth headers
    token = security.create_access_token(test_user.email, test_user.role)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make request
    response = client.post(
        "/api/v1/courses",
        headers=headers,
        json={
            "title": "New Course",
            "description": "Course description",
            "category": "Programming"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Course"
    assert data["instructor_id"] == str(test_user.id)
```

---

## Background Task Patterns

Celery tasks handle asynchronous operations like email sending and certificate generation.

### Basic Task Pattern

```python
# tasks/email_tasks.py
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_welcome_email(self, user_id: str, email: str, full_name: str):
    try:
        # Prepare email
        subject = "Welcome to LMS Platform"
        body = f"Hello {full_name}, welcome to our platform!"
        
        # Send email (simulated)
        _send_email(email, subject, body)
        
        logger.info(f"Welcome email sent to {email}")
        
    except Exception as exc:
        logger.error(f"Failed to send welcome email: {exc}")
        raise self.retry(exc=exc)


def _send_email(to: str, subject: str, body: str):
    """Simulated email sending."""
    # In production, use actual email service
    logger.info(f"Email to {to}: {subject}")
```

### Chained Tasks

```python
# tasks/certificate_tasks.py
@celery_app.task
def generate_certificate(enrollment_id: str):
    """Generate certificate for completed course."""
    from app.core.database import session_scope
    from app.modules.certificates.service import CertificateService
    
    with session_scope() as db:
        service = CertificateService(db)
        certificate = service.generate_certificate(enrollment_id)
        
        # Notify user in next task
        send_certificate_email.delay(
            certificate.user_email,
            str(certificate.id)
        )
    
    return str(certificate.id)


@celery_app.task
def send_certificate_email(email: str, certificate_id: str):
    """Send certificate to user."""
    logger.info(f"Sending certificate {certificate_id} to {email}")
    # Email sending logic here
```

### Scheduled Tasks

```python
# Celery beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "app.tasks.maintenance.cleanup_expired_tokens",
        "schedule": 3600.0,  # Every hour
    },
    "update-course-statistics": {
        "task": "app.tasks.progress.update_course_statistics",
        "schedule": 300.0,  # Every 5 minutes
    },
}
```

---

## Summary

These implementation patterns provide consistent approaches for building features in the LMS Backend. Following these patterns ensures:

1. **Consistency**: All code follows the same structure and conventions.
2. **Testability**: Patterns like dependency injection make testing easier.
3. **Maintainability**: Clear separation of concerns makes the codebase easier to understand and modify.
4. **Reliability**: Error handling and transaction patterns prevent data integrity issues.

When adding new features, use these patterns as templates and adapt them to the specific requirements of the new functionality.
