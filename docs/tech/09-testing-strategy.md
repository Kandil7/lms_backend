# Testing Strategy

This document explains the testing approach, test organization, fixtures, and best practices for this LMS Backend project.

---

## Table of Contents

1. [Testing Philosophy](#1-testing-philosophy)
2. [Test Structure](#2-test-structure)
3. [Test Types](#3-test-types)
4. [Fixtures and Configuration](#4-fixtures-and-configuration)
5. [Writing Tests](#5-writing-tests)
6. [Running Tests](#6-running-tests)
7. [Code Coverage](#7-code-coverage)
8. [Test Best Practices](#8-test-best-practices)

---

## 1. Testing Philosophy

### Testing Goals

| Goal | Description |
|------|-------------|
| **Confidence** | Verify code works as expected |
| **Regression** | Prevent breaking existing features |
| **Documentation** | Tests serve as executable documentation |
| **Refactoring** | Enable safe code changes |

### Test Pyramid

```
         ╱╲
        ╱  ╲       E2E Tests (few)
       ╱────╲      - Critical user paths
      ╱      ╲
     ╱────────╲   Integration Tests (some)
    ╱          ╲  - Module interactions
   ╱────────────╲
  ╱              ╲ Unit Tests (many)
 ╱                ╲ - Individual functions/classes
────────────────────
```

---

## 2. Test Structure

### Directory Layout

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── pytest.ini                  # Pytest configuration
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_auth/
│   │   ├── __init__.py
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── test_courses/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_schemas.py
│   ├── test_enrollments/
│   ├── test_quizzes/
│   └── ...
├── integration/               # Integration tests
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_courses.py
│   │   ├── test_auth.py
│   │   └── test_enrollments.py
│   └── database/
│       ├── __init__.py
│       └── test_migrations.py
└── fixtures/                 # Test data
    ├── __init__.py
    ├── users.json
    └── courses.json
```

### Pytest Configuration

```ini
# pytest.ini
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"

# Markers
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "e2e: marks tests as end-to-end tests",
]

# Coverage
[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
]
```

---

## 3. Test Types

### Unit Tests

Test individual functions and methods in isolation.

```python
# tests/unit/test_courses/test_services.py
import pytest
from app.modules.courses.services import CourseService
from app.modules.courses.schemas import CourseCreate

@pytest.mark.unit
class TestCourseService:
    @pytest.fixture
    def course_service(self, mock_course_repo):
        return CourseService(course_repo=mock_course_repo)
    
    async def test_create_course(self, course_service):
        # Arrange
        course_data = CourseCreate(
            title="Test Course",
            description="Test description",
            category="programming"
        )
        
        # Act
        result = await course_service.create_course(
            course_data=course_data,
            instructor_id="uuid"
        )
        
        # Assert
        assert result.title == "Test Course"
        assert result.slug == "test-course"
```

### Integration Tests

Test multiple components working together.

```python
# tests/integration/api/test_courses.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.integration
class TestCourseAPI:
    async def test_create_course_endpoint(self, client: AsyncClient, auth_token):
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "title": "Test Course",
            "description": "Test",
            "category": "programming"
        }
        
        # Act
        response = await client.post(
            "/api/v1/courses",
            json=payload,
            headers=headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Test Course"
```

---

## 4. Fixtures and Configuration

### Main Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_db():
    """Create test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def auth_token(client: AsyncClient, db_session) -> str:
    """Create and return auth token for testing."""
    # Create test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=hash_password("testpassword")
    )
    db_session.add(user)
    await db_session.commit()
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    
    return response.json()["data"]["access_token"]
```

### Module-Specific Fixtures

```python
# tests/unit/test_courses/conftest.py
import pytest
from unittest.mock import Mock
from app.modules.courses.repositories import CourseRepository

@pytest.fixture
def mock_course_repo():
    """Create mock course repository."""
    repo = Mock(spec=CourseRepository)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo
```

---

## 5. Writing Tests

### Test Naming Convention

```python
# Format: test_<feature>_<expected_behavior>
test_create_course_returns_201()
test_create_course_requires_authentication()
test_create_course_validates_title_not_empty()
test_list_courses_supports_pagination()
```

### Example: Complete Test

```python
# tests/integration/api/test_courses.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestCourseEndpoints:
    """Test course API endpoints."""
    
    async def test_create_course_success(
        self,
        client: AsyncClient,
        auth_token: str
    ):
        """Test successful course creation."""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "title": "Python Basics",
            "description": "Learn Python fundamentals",
            "category": "programming",
            "difficulty_level": "beginner",
            "estimated_duration_minutes": 120
        }
        
        # Act
        response = await client.post(
            "/api/v1/courses",
            json=payload,
            headers=headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == payload["title"]
        assert data["data"]["slug"] == "python-basics"
    
    async def test_create_course_without_auth_returns_401(
        self,
        client: AsyncClient
    ):
        """Test course creation without auth returns 401."""
        response = await client.post(
            "/api/v1/courses",
            json={"title": "Test"}
        )
        
        assert response.status_code == 401
    
    async def test_create_course_with_invalid_data_returns_422(
        self,
        client: AsyncClient,
        auth_token: str
    ):
        """Test course creation with invalid data returns 422."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await client.post(
            "/api/v1/courses",
            json={"title": ""},  # Invalid: empty title
            headers=headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
```

---

## 6. Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth/test_services.py

# Run tests matching pattern
pytest -k "test_create"

# Run tests by marker
pytest -m "unit"
pytest -m "integration"

# Exclude slow tests
pytest -m "not slow"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### With Coverage

```bash
# Run with coverage
pytest --cov=app --cov-report=html

# Generate coverage report
pytest --cov=app --cov-report=term-missing

# Run specific coverage
pytest --cov=app.modules.courses --cov-report=html
```

### CI/CD

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
        run: pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 7. Code Coverage

### Coverage Configuration

```ini
# pytest.ini
[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
    "*/main.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "pass",
]
```

### Coverage Targets

| Type | Target | Description |
|------|--------|-------------|
| **Overall** | 80% | Minimum acceptable coverage |
| **Core** | 90% | Critical infrastructure |
| **Modules** | 75% | Feature modules |

---

## 8. Test Best Practices

### Do's

```python
# ✅ Use descriptive test names
async def test_enrollment_progress_updates_when_lesson_completed():

# ✅ Test edge cases
async def test_list_courses_returns_empty_for_no_courses():

# ✅ Use fixtures for setup
async def test_create_course(instructor_user, course_data):

# ✅ Assert multiple aspects
async def test_login_success_returns_tokens():
    assert "access_token" in response
    assert "refresh_token" in response
    assert response["token_type"] == "bearer"

# ✅ Test error cases
async def test_login_wrong_password_returns_401():
```

### Don'ts

```python
# ❌ Don't test implementation details
async def test_course_service_creates_with_slug():
    # Don't: test internal implementation
    # Do: test the outcome

# ❌ Don't write overly complex tests
async def test_everything():
    # Don't: test entire system in one test
    # Do: break into focused tests

# ❌ Don't ignore test failures
# ❌ Don't write tests that only pass sometimes (flaky tests)
```

---

## Testing Summary

| Aspect | Implementation |
|--------|----------------|
| Framework | pytest |
| Async Support | pytest-asyncio |
| Fixtures | conftest.py |
| Test Types | Unit, Integration |
| Database | SQLite in-memory for tests |
| Coverage | pytest-cov |
| CI/CD | GitHub Actions |

This testing strategy ensures:
- **Reliability** - Comprehensive test coverage
- **Maintainability** - Clear test structure
- **Speed** - Fast unit tests, targeted integration tests
- **Confidence** - Safe to refactor and extend
