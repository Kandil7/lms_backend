# Testing Strategy Documentation

This document covers the complete testing strategy for the LMS Backend.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Types](#test-types)
3. [Test Organization](#test-organization)
4. [Test Coverage](#test-coverage)
5. [Testing Tools](#testing-tools)
6. [Running Tests](#running-tests)
7. [CI/CD Integration](#cicd-integration)

---

## Testing Philosophy

### Principles

1. **Test Behavior, Not Implementation** - Focus on what the code does, not how
2. **Fast Feedback** - Run fast tests frequently, slow tests less often
3. **Isolate Tests** - Each test should be independent
4. **Clear Intent** - Test names should describe the scenario
5. **Maintain Test Suite** - Tests are code; apply same standards

### Testing Pyramid

```
           ┌─────────────┐
           │     E2E     │  ← Few, slow, comprehensive
           │   (Playwright)│
          ┌──────────────┐
          │  Integration │  ← Medium, test module interaction
          │   Tests      │
         ┌───────────────┐
         │   Unit Tests  │  ← Many, fast, isolated
         │ (pytest)     │
        ┌────────────────┐
        │   Linting     │  ← Code quality
        │ (ruff/black)  │
        └────────────────┘
```

---

## Test Types

### Unit Tests

**Purpose**: Test individual functions and methods in isolation

**Location**: `tests/` (various files)

**Example**:

```python
def test_password_hashing():
    """Test password hashing and verification"""
    password = "test_password123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_create_access_token():
    """Test JWT token creation"""
    token = create_access_token("user-123", "student")
    
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "student"
    assert payload["typ"] == "access"
```

### Integration Tests

**Purpose**: Test interaction between components

**Example**:

```python
def test_user_registration_flow(client, db_session):
    """Test complete user registration flow"""
    # 1. Create user
    response = client.post("/api/v1/users/", json={
        "email": "newuser@test.com",
        "password": "password123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    
    # 2. Verify user exists
    user = db_session.query(User).filter_by(email="newuser@test.com").first()
    assert user is not None
    assert user.full_name == "New User"
```

### Endpoint Tests

**Purpose**: Test API endpoints with HTTP requests

**Example**:

```python
def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post("/api/v1/auth/token", json={
        "email": test_user.email,
        "password": "password123",
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["expires_in"] == 900

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    response = client.post("/api/v1/auth/token", json={
        "email": test_user.email,
        "password": "wrong_password",
    })
    
    assert response.status_code == 401
```

---

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── helpers.py               # Test utilities
├── unit/                   # Unit tests
│   ├── test_security.py
│   ├── test_permissions.py
│   └── test_validators.py
├── integration/            # Integration tests
│   ├── test_courses.py
│   ├── test_enrollments.py
│   └── test_auth_flow.py
├── api/                   # API/Endpoint tests
│   ├── test_auth_endpoints.py
│   ├── test_courses_endpoints.py
│   └── test_user_endpoints.py
└── perf/                  # Performance tests
    ├── k6_smoke.js
    └── k6_realistic.js
```

### Test Naming Convention

```
test_<module>_<scenario>_<expected_result>

Examples:
- test_auth_login_success
- test_auth_login_invalid_password
- test_courses_create_as_student_forbidden
- test_enrollment_progress_update
```

---

## Test Coverage

### Current Coverage Areas

| Module | Coverage | Notes |
|--------|----------|-------|
| Authentication | 95% | Login, logout, tokens, MFA |
| Users | 90% | CRUD, profile management |
| Courses | 85% | CRUD, publishing |
| Enrollments | 90% | Enrollment, progress |
| Assignments | 85% | Create, submit, grade |
| Quizzes | 80% | Create, attempt, submit |
| Files | 75% | Upload, download |
| Certificates | 80% | Generation, verification |
| Payments | 70% | Stripe integration |
| Analytics | 60% | Basic reporting |
| Admin | 70% | User management |
| Permissions | 90% | RBAC implementation |
| Middleware | 80% | Rate limiting, security |

### Coverage Goals

| Level | Target | Description |
|-------|--------|-------------|
| Unit Tests | 80% | Core business logic |
| Integration | 70% | Module interactions |
| API Endpoints | 85% | All routes |

---

## Testing Tools

### Pytest Configuration

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    api: marks tests as API tests
```

### Fixtures

**Location**: `tests/conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)()
    Base.metadata.drop_all(engine)

@pytest.fixture
def client(test_db):
    """Create test client with overridden dependencies"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        role="student"
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture
def admin_user(test_db):
    """Create admin user"""
    user = User(
        email="admin@example.com",
        password_hash=hash_password("adminpass123"),
        full_name="Admin User",
        role="admin"
    )
    test_db.add(user)
    test_db.commit()
    return user
```

### Test Helpers

**Location**: `tests/helpers.py`

```python
def create_auth_headers(token: str) -> dict:
    """Create authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def login_and_get_token(client, email: str, password: str) -> str:
    """Helper to login and get token"""
    response = client.post("/api/v1/auth/token", json={
        "email": email,
        "password": password,
    })
    return response.json()["access_token"]

def assert_response_success(response, expected_status=200):
    """Assert successful response"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
```

---

## Running Tests

### Run All Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Fast tests only (exclude slow)
pytest tests/ -v -m "not slow"

# Specific test file
pytest tests/test_auth.py -v

# Specific test
pytest tests/test_auth.py::test_login_success -v

# With verbose output
pytest tests/ -vv -s
```

### Run by Category

```bash
# Unit tests only
pytest tests/ -v -m unit

# Integration tests
pytest tests/ -v -m integration

# API tests
pytest tests/ -v -m api

# Slow tests
pytest tests/ -v -m slow
```

### Test Output

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Generate XML coverage (CI)
pytest tests/ --cov=app --cov-report=xml

# Show coverage summary
pytest tests/ --cov=app --cov-report=term-missing
```

---

## CI/CD Integration

### GitHub Actions Workflow

**Location**: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

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
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov httpx
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/ -v --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Test Stages

```
┌────────────────────────────────────────────┐
│                  CI Pipeline                │
├────────────────────────────────────────────┤
│  1. Lint (ruff/black)                      │
│     └─ Fast, catches style issues           │
│                                             │
│  2. Type Check (mypy)                       │
│     └─ Catches type errors                  │
│                                             │
│  3. Unit Tests                             │
│     └─ Fast feedback, isolated tests        │
│                                             │
│  4. Integration Tests                      │
│     └─ Module interactions                 │
│                                             │
│  5. API Tests                              │
│     └─ HTTP endpoint testing               │
│                                             │
│  6. Security Scan (bandit)                 │
│     └─ Vulnerability detection             │
└────────────────────────────────────────────┘
```

---

## Performance Testing

### K6 Load Tests

**Location**: `tests/perf/`

### Smoke Test

```javascript
// k6_smoke.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '30s',
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```

### Realistic Load Test

```javascript
// k6_realistic.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 }, // Steady
    { duration: '2m', target: 0 },   // Ramp down
  ],
};

export default function () {
  // Test various endpoints
  const endpoints = [
    '/api/v1/health',
    '/api/v1/courses/',
    '/api/v1/users/me',
  ];
  
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(`http://localhost:8000${endpoint}`);
  
  check(res, {
    'status is 2xx or 4xx': (r) => r.status >= 200 && r.status < 500,
  });
  
  sleep(1);
}
```

### Running K6 Tests

```bash
# Smoke test
k6 run tests/perf/k6_smoke.js

# Realistic load test
k6 run tests/perf/k6_realistic.js

# With thresholds
k6 run --threshold http_req_duration=p95:500 tests/perf/k6_realistic.js
```

---

## Test Maintenance

### When to Update Tests

1. **New Feature** - Add tests for new functionality
2. **Bug Fix** - Add regression test
3. **Refactoring** - Ensure tests still pass
4. **Performance Issue** - Add performance test

### Test Code Review

Checklist for test code review:
- [ ] Tests are isolated
- [ ] Test names are descriptive
- [ ] Edge cases covered
- [ ] No hardcoded values (use fixtures)
- [ ] Proper assertions
- [ ] Clean teardown

### Test Debt

Track and address:
- Flaky tests
- Slow tests
- Missing coverage areas
- Outdated tests

---

## Best Practices

### Do's

```python
# ✓ Use descriptive names
def test_login_with_valid_credentials_returns_token():
    ...

# ✓ Use fixtures for setup
def test_course_creation(instructor_user, db_session):
    ...

# ✓ Test edge cases
def test_password_minimum_length_enforced():
    ...

# ✓ Use assertions with descriptive messages
assert response.status_code == 201, "Should create successfully"
```

### Don'ts

```python
# ✗ Don't use magic numbers
assert len(users) == 5  # Why 5?

# ✗ Don't test implementation details
def test_user_has_password_hash():
    assert hasattr(user, 'password_hash')  # What if we change to external auth?

# ✗ Don't share state between tests
# Each test should be independent
```

---

## Debugging Tests

### Common Issues

| Issue | Solution |
|-------|----------|
| Tests hang | Check for unclosed connections |
| Flaky tests | Add proper waits, check timing |
| Fixture not found | Check pytest fixtures |
| Import errors | Check PYTHONPATH |
| Database errors | Reset test database |

### Debug Commands

```bash
# Run single test with output
pytest tests/test_auth.py::test_login -v -s

# Show local variables on failure
pytest tests/ -l

# Drop into debugger on failure
pytest tests/ --pdb

# Show slowest tests
pytest tests/ --durations=10

# Run in parallel (if pytest-xdist installed)
pytest tests/ -n auto
```
