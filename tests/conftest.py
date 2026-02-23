"""PyTest configuration for LMS backend tests"""

import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session")
def client():
    """Test client fixture"""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def auth_token():
    """Mock authentication token for testing"""
    # In real tests, this would be a valid JWT token
    # For now, return a mock token that passes validation
    return "mock-jwt-token-for-testing"

@pytest.fixture(scope="session")
def test_user_data():
    """Test user data for integration tests"""
    return {
        "email": "test-user@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": "student"
    }

@pytest.fixture(scope="session")
def test_instructor_data():
    """Test instructor data"""
    return {
        "email": "test-instructor@example.com",
        "password": "StrongPassword123!",
        "full_name": "Test Instructor",
        "role": "instructor",
        "bio": "Experienced educator with expertise in computer science.",
        "expertise": ["Computer Science", "Data Science"],
        "teaching_experience_years": 5,
        "education_level": "Master's",
        "institution": "Test University"
    }

@pytest.fixture(scope="session")
def test_admin_data():
    """Test admin data"""
    return {
        "email": "test-admin@example.com",
        "password": "VeryStrongPassword123456!",
        "full_name": "Test Admin",
        "role": "admin",
        "security_level": "enhanced",
        "mfa_required": True,
        "ip_whitelist": ["127.0.0.1", "192.168.1.1"],
        "time_restrictions": {
            "start_hour": 9,
            "end_hour": 17,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        },
        "emergency_contacts": [
            {
                "name": "Backup Admin",
                "email": "backup-test@example.com",
                "phone": "+15551234567",
                "relationship": "Colleague",
                "is_backup": True
            }
        ],
        "security_policy_accepted": True,
        "security_policy_version": "1.0"
    }

# Test environment configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Override settings for testing
    os.environ["DEBUG"] = "true"
    os.environ["ENABLE_API_DOCS"] = "true"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    # Ensure test database is used
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_lms"
    
    yield
    
    # Cleanup
    os.environ.pop("DEBUG", None)
    os.environ.pop("ENABLE_API_DOCS", None)
    os.environ.pop("REDIS_URL", None)
    os.environ.pop("DATABASE_URL", None)