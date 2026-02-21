# Testing Strategy

## Complete Testing Approach and Implementation

This document explains the testing philosophy, test organization, coverage targets, and testing tools used in this LMS backend.

---

## 1. Testing Philosophy

### Testing Goals

```
┌─────────────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                              ┌─────────┐                       │
│                             /           \                      │
│                            /   E2E      \                     │
│                           /   Tests      \                     │
│                          └───────────────┘                      │
│                         /                  \                   │
│                        /   Integration      \                  │
│                       /      Tests          \                 │
│                      └───────────────────────┘                │
│                    /                          \                │
│                   /      Unit Tests            \               │
│                  /           +                  \              │
│                 /       Service Tests            \             │
│                /                                   \           │
│               └────────────────────────────────────┘          │
│                                                                 │
│  • Many fast unit tests                                        │
│  • Fewer integration tests                                     │
│  • Few E2E tests (expensive)                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Testing Principles

| Principle | Description |
|-----------|-------------|
| **Fast** | Tests should run quickly |
| **Isolated** | Each test is independent |
| **Repeatable** | Same results every time |
| **Self-Validating** | Pass/Fail is clear |
| **Timely** | Written with code |

---

## 2. Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── test_auth.py               # Authentication tests
├── test_users.py              # User management tests
├── test_courses.py             # Course tests
├── test_lessons.py             # Lesson tests
├── test_enrollments.py         # Enrollment tests
├── test_quizzes.py             # Quiz system tests
├── test_certificates.py        # Certificate tests
├── test_files.py               # File upload tests
├── test_payments.py            # Payment tests
├── test_analytics.py           # Analytics tests
├── test_health.py              # Health check tests
├── test_rate_limit_rules.py   # Rate limiting tests
├── test_response_envelope.py   # Response format tests
├── test_config.py              # Configuration tests
├── test_webhooks.py            # Webhook tests
├── test_emails.py              # Email tests
├── test_permissions.py         # Permission tests
└── pytest.ini                  # Pytest configuration
```

### Test Naming Convention

```
test_<module>_<action>_<expected_result>

Examples:
test_auth_login_success
test_auth_login_invalid_password
test_course_create_as_student_forbidden
test_enrollment_progress_update
```

---

## 3. Testing Tools

### Dependencies

```python
# requirements.txt
pytest>=8.3.0              # Testing framework
pytest-asyncio>=0.25.0     # Async test support
pytest-cov>=6.0.0          # Coverage reporting
pytest-mock>=3.14.0         # Mocking
pytest-timeout>=2.3.0       # Test timeout
httpx>=0.28.0               # Async HTTP client
faker>=30.0.0               # Fake data generation
```

### Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
pythonpath = .
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    e2e: marks tests as end-to-end tests
```

---

## 4. Test Fixtures

### Shared Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.modules.users.models import User
from app.modules.users.service import UserService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    """Get database session"""
    async with test_db() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """Get test client"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user():
    """Create admin user"""
    return User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        is_active=True
    )

@pytest.fixture
def instructor_user():
    """Create instructor user"""
    return User(
        id=uuid4(),
        email="instructor@example.com",
        full_name="Instructor User",
        role="instructor",
        is_active=True
    )

@pytest.fixture
def student_user():
    """Create student user"""
    return User(
        id=uuid4(),
        email="student@example.com",
        full_name="Student User",
        role="student",
        is_active=True
    )

@pytest.fixture
def admin_token(admin_user):
    """Create admin access token"""
    return create_access_token(admin_user.id, admin_user.role)

@pytest.fixture
def instructor_token(instructor_user):
    """Create instructor access token"""
    return create_access_token(instructor_user.id, instructor_user.role)

@pytest.fixture
def student_token(student_user):
    """Create student access token"""
    return create_access_token(student_user.id, student_user.role)
```

---

## 5. Test Examples

### 5.1 Authentication Tests

```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

class TestAuthentication:
    """Authentication endpoint tests"""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "SecurePass123",
                "role": "student"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert "access_token" in data
        assert "refresh_token" in data
    
    async def test_register_duplicate_email(self, client: AsyncClient, db_session):
        """Test registration with duplicate email fails"""
        # Create user first
        await create_test_user(db_session, email="existing@example.com")
        
        # Try to register with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "full_name": "Another User",
                "password": "SecurePass123",
                "role": "student"
            }
        )
        
        assert response.status_code == 409
    
    async def test_login_success(self, client: AsyncClient, db_session):
        """Test successful login"""
        # Create and save user with hashed password
        user = await create_test_user(db_session, email="login@example.com")
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    async def test_login_invalid_password(self, client: AsyncClient, db_session):
        """Test login with invalid password fails"""
        user = await create_test_user(db_session, email="test@example.com")
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    async def test_logout(self, client: AsyncClient, db_session, student_token):
        """Test logout revokes refresh token"""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "some-token"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 204
```

### 5.2 Course Tests

```python
# tests/test_courses.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

class TestCourses:
    """Course endpoint tests"""
    
    async def test_list_courses(self, client: AsyncClient):
        """Test listing published courses"""
        response = await client.get("/api/v1/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    async def test_create_course_as_instructor(
        self, client: AsyncClient, db_session, instructor_token
    ):
        """Test instructor can create course"""
        response = await client.post(
            "/api/v1/courses",
            json={
                "title": "Python Basics",
                "description": "Learn Python",
                "category": "programming",
                "difficulty_level": "beginner"
            },
            headers={"Authorization": f"Bearer {instructor_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Python Basics"
    
    async def test_create_course_as_student_forbidden(
        self, client: AsyncClient, db_session, student_token
    ):
        """Test student cannot create course"""
        response = await client.post(
            "/api/v1/courses",
            json={"title": "Test Course"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403
    
    async def test_publish_course(
        self, client: AsyncClient, db_session, instructor_token
    ):
        """Test instructor can publish course"""
        # Create course first
        course = await create_test_course(db_session, instructor_id=instructor_user.id)
        
        response = await client.post(
            f"/api/v1/courses/{course.id}/publish",
            headers={"Authorization": f"Bearer {instructor_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["is_published"] is True
```

### 5.3 Enrollment Tests

```python
# tests/test_enrollments.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

class TestEnrollments:
    """Enrollment endpoint tests"""
    
    async def test_enroll_in_course(
        self, client: AsyncClient, db_session, student_token
    ):
        """Test student can enroll in course"""
        course = await create_test_course(db_session, is_published=True)
        
        response = await client.post(
            "/api/v1/enrollments",
            json={"course_id": str(course.id)},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"
    
    async def test_enroll_duplicate(
        self, client: AsyncClient, db_session, student_token
    ):
        """Test cannot enroll twice in same course"""
        course = await create_test_course(db_session, is_published=True)
        
        # First enrollment
        await client.post(
            "/api/v1/enrollments",
            json={"course_id": str(course.id)},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Second enrollment attempt
        response = await client.post(
            "/api/v1/enrollments",
            json={"course_id": str(course.id)},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 409
```

---

## 6. Test Coverage

### Coverage Requirements

```ini
# pytest.ini
[coverage:run]
source = app
omit =
    */tests/*
    */migrations/*
    */__init__.py

[coverage:report]
precision = 2
show_missing = True
skip_covered = False

[coverage:html]
directory = htmlcov
```

### Coverage Targets

```
┌─────────────────────────────────────────────────────────────────┐
│                    COVERAGE TARGETS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Overall Coverage: 75%                                          │
│                                                                 │
│  ┌─────────────────────┬──────────────┐                       │
│  │ Module               │ Target       │                       │
│  ├─────────────────────┼──────────────┤                       │
│  │ auth                │ 85%          │                       │
│  │ users               │ 80%          │                       │
│  │ courses             │ 80%          │                       │
│  │ enrollments         │ 80%          │                       │
│  │ quizzes             │ 75%          │                       │
│  │ certificates        │ 75%          │                       │
│  │ payments            │ 70%          │                       │
│  │ analytics           │ 60%          │                       │
│  │ core                │ 70%          │                       │
│  │ middleware          │ 80%          │                       │
│  └─────────────────────┴──────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html

# Coverage fails if below target
pytest --cov=app --cov-fail-under=75
```

---

## 7. Integration Tests

### Database Integration Tests

```python
# tests/test_integration.py
import pytest

@pytest.mark.integration
async def test_full_enrollment_flow(client: AsyncClient, db_session):
    """Test complete enrollment flow"""
    
    # 1. Register user
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={...}
    )
    assert register_resp.status_code == 201
    token = register_resp.json()["access_token"]
    
    # 2. Create course as instructor
    course_resp = await client.post(
        "/api/v1/courses",
        json={...},
        headers={"Authorization": f"Bearer {instructor_token}"}
    )
    course_id = course_resp.json()["id"]
    
    # 3. Publish course
    await client.post(
        f"/api/v1/courses/{course_id}/publish",
        headers={"Authorization": f"Bearer {instructor_token}"}
    )
    
    # 4. Enroll as student
    enroll_resp = await client.post(
        "/api/v1/enrollments",
        json={"course_id": course_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert enroll_resp.status_code == 201
    
    # 5. Get enrollment
    get_resp = await client.get(
        f"/api/v1/enrollments/{enroll_resp.json()['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 200
```

---

## 8. Mocking

### External Services

```python
# tests/test_payments.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_create_payment_intent(client: AsyncClient, student_token):
    """Test payment intent creation with mocked Stripe"""
    
    with patch('app.modules.payments.stripe.PaymentIntent.create') as mock_create:
        mock_create.return_value = {
            "id": "pi_test123",
            "client_secret": "secret_test123",
            "status": "requires_payment_method"
        }
        
        response = await client.post(
            "/api/v1/payments/create-payment-intent",
            json={
                "enrollment_id": str(enrollment_id),
                "amount": 499.99,
                "currency": "EGP"
            },
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["client_secret"] == "secret_test123"
```

---

## 9. Test Execution

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run tests matching pattern
pytest -k "test_auth"

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run only fast tests (exclude slow)
pytest -m "not slow"

# Run only unit tests
pytest -m "unit"

# Run with verbose output
pytest -v -s

# Stop on first failure
pytest -x

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_lms
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_lms
          REDIS_URL: redis://localhost:6379/0
        run: pytest --cov=app --cov-fail-under=75
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## 10. Best Practices

### Test Writing Guidelines

| Guideline | Description |
|-----------|-------------|
| **AAA Pattern** | Arrange, Act, Assert |
| **One assertion** | Per test when possible |
| **Descriptive names** | Test name explains what it tests |
| **Isolated** | No dependencies between tests |
| **Fast** | Under 1 second per test |
| **Repeatable** | Same results every run |

### Common Patterns

```python
# Good: Clear, focused test
async def test_login_success(client: AsyncClient, db_session):
    user = await create_user(db_session, email="test@example.com")
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()

# Bad: Too much in one test
async def test_everything(client: AsyncClient, db_session):
    # Creates user, logs in, creates course, enrolls, takes quiz...
    # This should be multiple tests
```

---

## Summary

This testing strategy provides:

| Aspect | Implementation |
|--------|----------------|
| Framework | Pytest with async support |
| Fixtures | Shared database, client, tokens |
| Coverage Target | 75% minimum |
| Test Types | Unit, Integration, E2E |
| CI/CD | GitHub Actions |
| Mocking | unittest.mock |

The test suite ensures code quality while maintaining reasonable development velocity.
