# Complete Development and Operations Guide

This comprehensive guide covers the entire development lifecycle, operations procedures, and infrastructure management for the LMS Backend project.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Code Organization](#code-organization)
4. [Database Management](#database-management)
5. [API Development](#api-development)
6. [Testing](#testing)
7. [Security](#security)
8. [Deployment](#deployment)
9. [Monitoring and Observability](#monitoring-and-observability)
10. [Operations Procedures](#operations-procedures)

---

## Project Overview

### What is LMS Backend?

The LMS Backend is a comprehensive Learning Management System API built with modern web technologies. It provides:

- **User Management**: Role-based authentication with JWT tokens, optional MFA
- **Course Management**: Create, publish, and organize educational content
- **Enrollment System**: Student enrollment and progress tracking
- **Assessment System**: Quizzes with multiple question types and scoring
- **Analytics**: Three-tier analytics for students, instructors, and admins
- **File Management**: Upload and store course materials
- **Certificates**: Automated PDF certificate generation

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.115+ |
| Database | PostgreSQL | 14+ |
| ORM | SQLAlchemy | 2.0+ |
| Cache/Broker | Redis | 7+ |
| Tasks | Celery | 5.4+ |
| Containerization | Docker | 20.10+ |
| Reverse Proxy | Caddy | 2.6+ |
| Monitoring | Prometheus + Grafana | Latest |

---

## Development Environment Setup

### Prerequisites

Install the following on your development machine:

1. **Python 3.11+**: From python.org or use pyenv
2. **Docker Desktop**: For containerized services
3. **Git**: For version control
4. **PostgreSQL Client**: For direct database access (optional)

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd lms_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start services (PostgreSQL and Redis)
docker-compose up -d db redis

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Environment Configuration

The `.env` file controls all application settings. Key variables:

```env
# Application
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=development-secret-key-change-in-production
ALGORITHM=HS256

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# File Storage
UPLOAD_DIR=uploads
CERTIFICATES_DIR=certificates
```

### Running with Docker

For a complete development environment:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

---

## Code Organization

### Project Structure

```
lms_backend/
├── app/                      # Main application
│   ├── main.py              # FastAPI application
│   ├── api/                # API routing
│   │   └── v1/
│   │       └── api.py      # Router aggregation
│   ├── core/               # Core infrastructure
│   │   ├── config.py       # Configuration
│   │   ├── database.py    # Database connection
│   │   ├── security.py    # JWT & passwords
│   │   ├── permissions.py # RBAC
│   │   ├── cache.py       # Redis caching
│   │   ├── exceptions.py  # Error handling
│   │   └── middleware/    # Custom middleware
│   ├── modules/           # Feature modules
│   │   ├── auth/         # Authentication
│   │   ├── users/        # User management
│   │   ├── courses/      # Course content
│   │   ├── enrollments/  # Student enrollments
│   │   ├── quizzes/      # Assessments
│   │   ├── analytics/    # Reporting
│   │   ├── files/        # File uploads
│   │   └── certificates/ # PDF generation
│   ├── tasks/            # Celery tasks
│   └── utils/            # Shared utilities
├── alembic/              # Database migrations
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── ops/                  # Infrastructure configs
│   ├── caddy/           # Reverse proxy
│   └── observability/   # Monitoring
├── docker-compose*.yml   # Docker configs
├── Dockerfile
└── requirements.txt
```

### Module Architecture

Each module follows a consistent structure:

```
module_name/
├── __init__.py
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── repository.py          # Data access layer
├── service.py             # Business logic
└── router.py             # API endpoints
```

### Naming Conventions

- **Files**: snake_case (e.g., `course_service.py`)
- **Classes**: PascalCase (e.g., `CourseService`)
- **Functions**: snake_case (e.g., `get_course`)
- **Constants**: SCREAMING_SNAKE_CASE (e.g., `MAX_UPLOAD_SIZE`)
- **Database tables**: plural snake_case (e.g., `user_roles`)

---

## Database Management

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

### Creating a New Model

1. **Create model class**:
```python
# app/modules/courses/models/course.py
class Course(Base):
    __tablename__ = "courses"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # ... more fields
```

2. **Create migration**:
```bash
alembic revision --autogenerate -m "create_courses_table"
```

3. **Apply migration**:
```bash
alembic upgrade head
```

### Database Queries

**Basic Query**:
```python
course = db.query(Course).filter(Course.id == course_id).first()
```

**With Relationships**:
```python
course = (
    db.query(Course)
    .options(joinedload(Course.lessons))
    .filter(Course.id == course_id)
    .first()
)
```

**Complex Filtering**:
```python
courses = (
    db.query(Course)
    .filter(Course.is_published == True)
    .filter(Course.category == category)
    .order_by(Course.created_at.desc())
    .offset(offset)
    .limit(limit)
    .all()
)
```

---

## API Development

### Creating a New Endpoint

1. **Define Schema**:
```python
# app/modules/courses/schemas/course.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
```

2. **Create Service Method**:
```python
# app/modules/courses/services/course_service.py
class CourseService:
    def create_course(self, data: CourseCreate, user: User) -> Course:
        course = Course(
            title=data.title,
            description=data.description,
            instructor_id=user.id
        )
        self.db.add(course)
        self.db.commit()
        return course
```

3. **Add Router Endpoint**:
```python
# app/modules/courses/routers/course_router.py
@router.post("", response_model=CourseResponse, status_code=201)
def create_course(
    data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CourseResponse:
    service = CourseService(db)
    course = service.create_course(data, current_user)
    return CourseResponse.model_validate(course)
```

### Request Validation

Pydantic provides automatic validation:

```python
class UserRegistration(BaseModel):
    email: str = Field(..., email=True)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Custom validation logic
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase")
        return v
```

### Error Handling

Use custom exceptions:

```python
# In service
if not course:
    raise NotFoundException("Course not found")

# Exception handler converts to HTTP 404
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_courses.py -v

# Specific test
pytest tests/test_courses.py::test_create_course -v

# Watch mode
pytest-watch
```

### Writing Tests

**Unit Test**:
```python
def test_hash_password():
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
```

**Integration Test**:
```python
def test_create_course(client, auth_headers):
    response = client.post(
        "/api/v1/courses",
        headers=auth_headers,
        json={
            "title": "Test Course",
            "description": "Test description"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Course"
```

**Fixture Example**:
```python
@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(test_user.email, test_user.role)
    return {"Authorization": f"Bearer {token}"}
```

### Test Coverage Goals

- **Minimum**: 75% code coverage
- **Target**: 85% code coverage
- **Critical paths**: 100% coverage

---

## Security

### Authentication

The API uses JWT tokens for authentication:

```python
# Getting the current user
def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    return user
```

### Authorization

Check roles in endpoints:

```python
@router.post("/courses")
def create_course(
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in {"admin", "instructor"}:
        raise HTTPException(403, "Not authorized")
```

### Password Security

Always hash passwords:

```python
# Hashing
hashed = hash_password(password)

# Verification
if verify_password(password, hashed):
    # Continue login
```

### Rate Limiting

Rate limits are configured in settings:

```python
RATE_LIMIT_REQUESTS_PER_MINUTE = 100
AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE = 60
```

---

## Deployment

### Development Deployment

```bash
docker-compose up -d
```

### Production Deployment

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Azure VM Deployment

```bash
# Trigger deployment workflow
git push origin main
```

The GitHub Actions workflow will:
1. Run tests and security scans
2. Create release archive
3. Upload to Azure VM
4. Run deployment script
5. Verify health checks

---

## Monitoring and Observability

### Health Checks

```bash
# Basic health
curl http://localhost:8000/api/v1/health

# Readiness (includes DB and Redis)
curl http://localhost:8000/api/v1/ready
```

### Metrics

Prometheus metrics are exposed at `/metrics`:

- Request counts by endpoint
- Response time percentiles
- Error rates
- Active connections

### Grafana Dashboards

Access Grafana at http://localhost:3000 (when running observability stack):

- **API Overview**: Request rates, response times, errors
- **Course Performance**: Enrollment trends, completion rates
- **Student Progress**: Activity metrics, quiz performance
- **Security Events**: Failed logins, rate limits
- **System Health**: Resource usage, service status

### Alerting

Alerts are configured in Prometheus and routed through Alertmanager:

- High error rate (>5%)
- Slow response time (p95 > 2s)
- Service down
- High CPU/memory usage

---

## Operations Procedures

### Backup Database

```bash
# Create backup
docker-compose exec db pg_dump -U lms lms > backup.sql

# Restore backup
docker-compose exec -T db psql -U lms lms < backup.sql
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Restart Service

```bash
# Restart API
docker-compose restart api

# Restart specific service
docker-compose restart celery-worker
```

### Scale Services

```bash
# Scale API instances
docker-compose up -d --scale api=4

# Scale workers
docker-compose up -d --scale celery-worker=3
```

### Rollback Deployment

```bash
# List images
docker images | grep lms-backend

# Rollback to previous version
docker-compose -f docker-compose.prod.yml up -d --build api:previous-tag
```

### Database Migration

```bash
# Create migration
alembic revision --autogenerate -m "add_field"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Troubleshooting

### Common Issues

**Database Connection Error**:
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check logs
docker-compose logs db
```

**Import Errors**:
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**Port Already in Use**:
```bash
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

**Migration Errors**:
```bash
# Check current version
alembic current

# Check history
alembic history
```

### Getting Help

1. Check logs: `docker-compose logs`
2. Check health: `curl http://localhost:8000/api/v1/ready`
3. Check metrics: `curl http://localhost:8000/metrics`
4. Review documentation in `docs/tech/`

---

## Summary

This guide covered the complete development and operations workflow:

1. **Setup**: Environment configuration and dependencies
2. **Organization**: Code structure and conventions
3. **Database**: Migrations, models, and queries
4. **API**: Development patterns and validation
5. **Testing**: Writing and running tests
6. **Security**: Authentication and authorization
7. **Deployment**: Production and Azure VM
8. **Monitoring**: Metrics and observability
9. **Operations**: Common procedures and troubleshooting

For more detailed information, refer to the comprehensive documentation in `docs/tech/`.
