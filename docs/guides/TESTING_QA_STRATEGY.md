# Testing & QA Strategy

Ensuring the reliability of the LMS requires a multi-layered testing approach. This guide covers how we test the backend from units to full integration.

---

## 📋 Table of Contents
1. [Testing Layers](#1-testing-layers)
2. [Local Test Environment](#2-local-test-environment)
3. [Running Tests](#3-running-tests)
4. [Writing a New Test](#4-writing-a-new-test)
5. [Code Coverage](#5-code-coverage)
6. [CI/CD Integration](#6-cicd-integration)

---

## 1. Testing Layers
- **Unit Tests**: Test individual functions or methods in isolation (e.g., scoring logic).
- **Integration Tests**: Test the interaction between modules and the database.
- **API Tests**: Test actual HTTP endpoints using `TestClient`.
- **E2E Tests**: Test full user journeys (usually handled by the frontend team using Playwright).

---

## 2. Local Test Environment
The test suite uses a separate database to ensure your development data isn't affected.

### Prerequisites:
- A PostgreSQL instance running (separate from your dev DB).
- Redis running.

### Configuration:
Tests look for these environment variables (automatically set in `conftest.py` if missing):
- `DATABASE_URL`: `postgresql://test:test@localhost:5432/test_lms`
- `REDIS_URL`: `redis://localhost:6379/0`

---

## 3. Running Tests
We use **PyTest** as our test runner.

```bash
# Run all tests
pytest

# Run tests for a specific module
pytest tests/test_courses.py

# Run only tests marked as 'smoke'
pytest -m smoke

# Run tests and show logs
pytest -s
```

---

## 4. Writing a New Test
Tests should follow the **Arrange -> Act -> Assert** pattern.

### Example API Test:
```python
def test_create_course(client, auth_token):
    # Arrange
    payload = {"title": "New Course", "description": "Awesome content"}
    
    # Act
    response = client.post(
        "/api/v1/courses/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=payload
    )
    
    # Assert
    assert response.status_code == 201
    assert response.json()["title"] == "New Course"
```

### Key Fixtures (in `tests/conftest.py`):
- `client`: A FastAPI `TestClient` instance.
- `auth_token`: A pre-authenticated token for a test student.
- `db_session`: A fresh database session for every test.

---

## 5. Code Coverage
We aim for **>80%** test coverage on all new modules.

```bash
# Generate a coverage report
pytest --cov=app --cov-report=html
```
Open `htmlcov/index.html` in your browser to see which lines are untested.

---

## 6. CI/CD Integration
Tests are automatically run on every Pull Request via **GitHub Actions** (`.github/workflows/ci.yml`).
- A build will fail if any test fails.
- Critical thresholds for coverage are enforced.

---

## ✅ Testing Checklist
- [ ] Test the "Happy Path" (success).
- [ ] Test "Edge Cases" (invalid input, missing fields).
- [ ] Test "Permissions" (unauthorized role trying to access).
- [ ] Test "Database Constraints" (duplicate emails, invalid foreign keys).
- [ ] Clean up any files created during the test.
