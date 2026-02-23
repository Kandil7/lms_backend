# Complete Testing Strategy and Quality Assurance Documentation

This comprehensive documentation details the complete testing strategy for the LMS Backend project. It covers test organization, test types, test infrastructure, coverage requirements, and quality assurance processes.

---

## Testing Philosophy

The LMS Backend follows a pragmatic testing philosophy that balances test coverage with development velocity. Tests are designed to catch regressions, verify functionality, and enable safe refactoring. The testing strategy emphasizes integration tests over unit tests for business logic, as the complexity lies in database and external service interactions rather than pure logic.

The project requires a minimum of 75% code coverage as a quality gate in the CI pipeline. This threshold ensures reasonable test investment while acknowledging that some code (like error handlers) is difficult to test meaningfully. Tests run against both SQLite (for speed in development) and PostgreSQL (for compatibility verification).

---

## Test Organization

### Directory Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── helpers.py               # Test helper functions
├── test_auth.py             # Authentication tests
├── test_courses.py          # Course management tests
├── test_quizzes.py          # Quiz functionality tests
├── test_certificates.py     # Certificate generation tests
├── test_analytics.py        # Analytics endpoint tests
├── test_assignments.py      # Assignment tests
├── test_assignments_grading.py  # Grading tests
├── test_config.py           # Configuration tests
├── test_auth_cookie_router.py   # Cookie auth tests
├── perf/
│   ├── k6_smoke.js          # Smoke load test
│   └── k6_realistic.js      # Realistic load test
```

### Test Categories

**Unit Tests**: Individual function and class testing with mocked dependencies. Located in test files alongside implementation.

**Integration Tests**: API endpoint testing with live database. Uses FastAPI's TestClient.

**Database Tests**: Tests requiring PostgreSQL-specific features. Marked for separate execution.

**Performance Tests**: Load testing with k6. Located in perf/ directory.

---

## Test Infrastructure

### conftest.py - Configuration and Fixtures

The conftest.py file provides shared fixtures and pytest configuration:

```python
@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as client:
        yield client
```

**Fixtures Provided**:
- `db_session`: Database session for each test
- `client`: FastAPI TestClient instance
- `admin_user`: Admin user fixture
- `instructor_user`: Instructor user fixture
- `student_user`: Student user fixture

### helpers.py - Test Utilities

Helper functions for common test operations:

```python
def create_test_user(db_session, role="student", **kwargs):
    """Create a test user with specified attributes."""
    # Implementation
```

**Helper Functions**:
- User creation helpers
- Authentication helpers
- Response assertion helpers
- Test data factories

---

## Test Types and Coverage

### Authentication Tests (test_auth.py)

**Coverage Areas**:
- User registration with validation
- Login with correct credentials
- Login with incorrect credentials
- Token refresh
- Logout and token blacklisting
- Password reset flow
- Email verification
- MFA challenge (if enabled)

**Test Examples**:
```python
def test_login_success(client, student_user):
    """Test successful login returns tokens."""
    response = client.post("/api/v1/auth/login", json={
        "email": student_user.email,
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_password(client, student_user):
    """Test login fails with wrong password."""
    response = client.post("/api/v1/auth/login", json={
        "email": student_user.email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401
```

### Course Tests (test_courses.py)

**Coverage Areas**:
- Course listing (published only)
- Course creation by instructors
- Course update by owner/instructor
- Course deletion
- Lesson management
- Course enrollment
- Enrollment progress tracking

### Quiz Tests (test_quizzes.py)

**Coverage Areas**:
- Quiz creation by instructors
- Question management
- Quiz attempt starting
- Answer submission
- Automatic grading
- Score calculation
- Attempt history

### Certificate Tests (test_certificates.py)

**Coverage Areas**:
- Certificate generation on completion
- Certificate download
- Certificate verification
- Certificate revocation

### Analytics Tests (test_analytics.py)

**Coverage Areas**:
- Student dashboard data
- Instructor course analytics
- System-wide admin analytics
- Data aggregation accuracy

### Configuration Tests (test_config.py)

**Coverage Areas**:
- Environment variable validation
- Production setting validation
- Configuration defaults
- Secret management integration

---

## Database Testing

### SQLite vs PostgreSQL

The test suite primarily uses SQLite for speed. SQLite provides in-memory databases that are created and destroyed for each test, providing isolation and speed.

**When PostgreSQL is Required**:
- JSON column operations
- Full-text search
- Specific SQL features
- Transaction isolation levels

### PostgreSQL Test Execution

```bash
# Run tests with PostgreSQL
TEST_DATABASE_URL=postgresql://user:pass@localhost/db pytest
```

The CI pipeline includes a separate job that runs tests against PostgreSQL to catch SQLite-incompatible code.

---

## Performance Testing

### k6 Load Tests

The project includes k6-based load tests for performance validation:

#### Smoke Test (tests/perf/k6_smoke.js)

Purpose: Verify basic endpoint availability under light load

```javascript
export const options = {
    stages: [
        { duration: '30s', target: 20 },
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
    },
};
```

**Scenarios**:
- Health check endpoint
- Course listing
- Single course retrieval

#### Realistic Test (tests/perf/k6_realistic.js)

Purpose: Simulate realistic user behavior

```javascript
export const options = {
    stages: [
        { duration: '2m', target: 10 },
        { duration: '5m', target: 10 },
        { duration: '2m', target: 0 },
    ],
};
```

**User Journeys**:
1. Login as student
2. Browse courses
3. Enroll in course
4. View lessons
5. Take quiz
6. View progress
7. Logout

**Execution**:
```bash
k6 run tests/perf/k6_realistic.js
```

---

## Test Execution

### Running All Tests

```bash
# Basic execution
pytest -q

# With coverage
pytest -q --cov=app --cov-report=term-missing --cov-fail-under=75

# With verbose output
pytest -v
```

### Running Specific Tests

```bash
# By file
pytest tests/test_auth.py

# By marker
pytest -m auth

# By keyword
pytest -k "login"

# Database tests only
pytest --postgres
```

### Test Markers

Custom markers for test organization:

```python
@pytest.mark.auth
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.postgres
```

---

## Coverage Requirements

### CI Gate

The CI pipeline enforces 75% minimum code coverage:

```bash
pytest -q --cov=app --cov-fail-under=75
```

### Coverage Reports

Generate various coverage reports:

```bash
# Terminal report
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html

# XML report (CI integration)
pytest --cov=app --cov-report=xml
```

### Coverage Exclusions

Some code is excluded from coverage:

```python
# pytest.ini or conftest.py
[tool.pytest.ini_options]
addopts = "--ignore=tests/perf"
```

---

## Quality Assurance Processes

### Pre-commit Quality Checks

Before code is committed:

1. All tests must pass
2. Coverage must meet threshold
3. Code must compile without errors
4. No security vulnerabilities in dependencies

### CI Pipeline Quality Gates

The CI pipeline executes:

1. Static sanity checks (compileall, pip check)
2. Postman collection generation
3. Unit tests with coverage
4. PostgreSQL integration tests

### Code Review Quality

Pull requests require:

1. All CI checks passing
2. At least one reviewer approval
3. No unresolved comments

---

## Test Data Management

### Fixtures

Test data is created through fixtures in conftest.py:

```python
@pytest.fixture
def admin_user(db_session):
    """Create admin user for tests."""
    user = User(
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user
```

### Factories

For complex test data, factory functions create objects:

```python
def create_course(db_session, instructor, **kwargs):
    """Factory for creating courses."""
    course_data = {
        "title": "Test Course",
        "slug": "test-course",
        "description": "Test description",
        "instructor_id": instructor.id,
        **kwargs
    }
    course = Course(**course_data)
    db_session.add(course)
    db_session.commit()
    return course
```

### Cleanup

Tests clean up after themselves:

```python
@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
```

---

## Mocking Strategy

### When to Mock

Mock external services:
- SMTP servers
- Redis (in unit tests)
- Firebase SDK

### When Not to Mock

Don't mock the database in integration tests. The whole point is to test database interactions.

### Mock Examples

```python
from unittest.mock import patch

@patch('app.tasks.email_tasks.send_email')
def test_welcome_email(mock_send):
    """Test email is queued on user registration."""
    # Test logic
    mock_send.assert_called_once()
```

---

## Troubleshooting Tests

### Database Reset Issues

If tests fail due to stale data:

```bash
# Clear all databases
pytest --cleandb
```

### Fixture Not Found

Ensure conftest.py is in the tests directory or configure pytest to find it.

### Slow Tests

Identify slow tests:

```bash
pytest --durations=10
```

### Flaky Tests

Flaky tests are marked for investigation:

```python
@pytest.mark.flaky(reruns=3)
def test_sometimes_fails():
    pass
```

---

## Performance Benchmarks

### Response Time Targets

| Endpoint Type | Target p95 |
|--------------|------------|
| Health check | < 50ms |
| Course listing | < 200ms |
| Course detail | < 300ms |
| Quiz submission | < 500ms |

### Load Testing Thresholds

| Metric | Threshold |
|--------|-----------|
| Error rate | < 1% |
| p95 latency | < 1s |
| Throughput | > 50 rps |

---

## Continuous Improvement

### Test Coverage Analysis

Regularly review coverage reports to identify:
- Untested edge cases
- Missing integration tests
- Areas needing more test investment

### Performance Regression Detection

Compare k6 results over time:
- Establish baseline metrics
- Alert on significant regressions
- Optimize slow endpoints

### Test Maintenance

- Remove obsolete tests
- Update tests for new features
- Refactor duplicated test code

---

This comprehensive testing documentation covers all aspects of quality assurance in the LMS Backend project. The testing strategy balances thoroughness with development velocity while maintaining production reliability.
