"""PyTest configuration for LMS backend tests"""

import os
import uuid
from contextlib import contextmanager
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.middleware.rate_limit import RateLimitMiddleware
from app.utils.cache import cache_manager
from tests import helpers as test_helpers


def _reset_bootstrap_auth_state() -> None:
    test_helpers._BOOTSTRAP_ADMIN_EMAIL = None
    test_helpers._BOOTSTRAP_ADMIN_ACCESS_TOKEN = None


def _reset_rate_limit_state() -> None:
    node = app.middleware_stack
    visited: set[int] = set()
    while node is not None and id(node) not in visited:
        visited.add(id(node))
        if isinstance(node, RateLimitMiddleware):
            node._requests.clear()
        node = getattr(node, "app", None)


@pytest.fixture(scope="function")
def client(db_session):
    """Isolated test client fixture with per-test DB override."""

    def override_get_db() -> Generator:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    original_file_storage_provider = settings.FILE_STORAGE_PROVIDER
    settings.FILE_STORAGE_PROVIDER = "local"
    app.middleware_stack = None
    _reset_bootstrap_auth_state()
    cache_manager._memory_cache.clear()
    get_app_cache.cache_clear()
    with TestClient(app) as c:
        _reset_rate_limit_state()
        yield c
    _reset_rate_limit_state()
    app.dependency_overrides.clear()
    settings.FILE_STORAGE_PROVIDER = original_file_storage_provider
    app.middleware_stack = None
    _reset_bootstrap_auth_state()
    cache_manager._memory_cache.clear()
    get_app_cache.cache_clear()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test to ensure isolation.

    This fixture creates a new database engine with a test database and
    provides a session that is rolled back after each test to ensure
    complete isolation between tests.
    """
    # Create test database URL (use SQLite for testing)
    test_db_url = "sqlite:///./test_lms_{}.db".format(uuid.uuid4().hex[:8])

    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    # Create tables
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def generate_unique_email() -> Generator[callable, None, None]:
    """Generate unique email addresses for tests to avoid conflicts."""

    def _generate() -> str:
        return f"test-{uuid.uuid4().hex[:8]}@example.com"

    return _generate


@pytest.fixture
def auth_context(client, generate_unique_email):
    """Create a real authenticated student context for API tests."""
    email = generate_unique_email()
    password = "TestPassword123!"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Payment Test User",
            "role": "student",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    return {
        "token": payload["tokens"]["access_token"],
        "user_id": payload["user"]["id"],
    }


@pytest.fixture
def auth_token(auth_context):
    return auth_context["token"]


@pytest.fixture
def test_user_data(generate_unique_email):
    """Test user data for integration tests"""
    email = generate_unique_email()
    return {
        "email": email,
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": "student",
    }


@pytest.fixture
def test_instructor_data(generate_unique_email):
    """Test instructor data"""
    email = generate_unique_email()
    return {
        "email": email,
        "password": "StrongPassword123!",
        "full_name": "Test Instructor",
        "role": "instructor",
        "bio": "Experienced educator with expertise in computer science.",
        "expertise": ["Computer Science", "Data Science"],
        "teaching_experience_years": 5,
        "education_level": "Master's",
        "institution": "Test University",
    }


@pytest.fixture
def test_admin_data(generate_unique_email):
    """Test admin data"""
    email = generate_unique_email()
    return {
        "email": email,
        "password": "VeryStrongPassword123456!",
        "full_name": "Test Admin",
        "role": "admin",
        "security_level": "enhanced",
        "mfa_required": True,
        "ip_whitelist": ["127.0.0.1", "192.168.1.1"],
        "time_restrictions": {
            "start_hour": 9,
            "end_hour": 17,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        },
        "emergency_contacts": [
            {
                "name": "Backup Admin",
                "email": "backup-test@example.com",
                "phone": "+15551234567",
                "relationship": "Colleague",
                "is_backup": True,
            }
        ],
        "security_policy_accepted": True,
        "security_policy_version": "1.0",
    }


# Test environment configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Store original values
    original_debug = os.environ.get("DEBUG")
    original_docs = os.environ.get("ENABLE_API_DOCS")
    original_redis = os.environ.get("REDIS_URL")
    original_db = os.environ.get("DATABASE_URL")

    # Override settings for testing
    os.environ["DEBUG"] = "true"
    os.environ["ENABLE_API_DOCS"] = "true"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["CSRF_ENABLED"] = "false"  # Disable CSRF for testing

    # Ensure test database is used
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_lms"

    yield

    # Restore original values
    if original_debug is not None:
        os.environ["DEBUG"] = original_debug
    else:
        os.environ.pop("DEBUG", None)

    if original_docs is not None:
        os.environ["ENABLE_API_DOCS"] = original_docs
    else:
        os.environ.pop("ENABLE_API_DOCS", None)

    if original_redis is not None:
        os.environ["REDIS_URL"] = original_redis
    else:
        os.environ.pop("REDIS_URL", None)

    if original_db is not None:
        os.environ["DATABASE_URL"] = original_db
    else:
        os.environ.pop("DATABASE_URL", None)


@pytest.fixture
def override_settings():
    """Override settings for specific tests."""

    @contextmanager
    def _override(**kwargs):
        original_values = {}
        for key, value in kwargs.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = str(value)
        yield
        # Restore
        for key, original in original_values.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original

    return _override
