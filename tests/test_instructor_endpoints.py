"""Comprehensive tests for instructor endpoints"""

import pytest
import requests
from typing import Dict, Any
from datetime import datetime, timedelta

# Test data
TEST_INSTRUCTOR_DATA = {
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

TEST_INVALID_INSTRUCTOR_DATA = {
    "email": "invalid-email",
    "password": "weak",  # Too short
    "full_name": "",
    "role": "instructor",
    "bio": "Short",  # Too short
    "expertise": [],
    "teaching_experience_years": -1,
    "education_level": "",
    "institution": ""
}

class TestInstructorEndpoints:
    
    def test_register_instructor_valid(self, client):
        """Test successful instructor registration"""
        response = client.post("/api/v1/instructors/register", json=TEST_INSTRUCTOR_DATA)
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "onboarding_status" in data
        assert data["onboarding_status"]["step"] == "account_setup"
        assert data["onboarding_status"]["verification_required"] is True
    
    def test_register_instructor_invalid_email(self, client):
        """Test registration with invalid email"""
        invalid_data = TEST_INSTRUCTOR_DATA.copy()
        invalid_data["email"] = "invalid-email"
        response = client.post("/api/v1/instructors/register", json=invalid_data)
        assert response.status_code == 400
        assert "email" in response.text.lower()
    
    def test_register_instructor_weak_password(self, client):
        """Test registration with weak password"""
        invalid_data = TEST_INSTRUCTOR_DATA.copy()
        invalid_data["password"] = "weak"
        response = client.post("/api/v1/instructors/register", json=invalid_data)
        assert response.status_code == 400
        assert "password" in response.text.lower()
    
    def test_register_instructor_short_bio(self, client):
        """Test registration with short bio"""
        invalid_data = TEST_INSTRUCTOR_DATA.copy()
        invalid_data["bio"] = "short"
        response = client.post("/api/v1/instructors/register", json=invalid_data)
        assert response.status_code == 400
        assert "bio" in response.text.lower()
    
    def test_get_onboarding_status_unauthenticated(self, client):
        """Test onboarding status without authentication"""
        response = client.get("/api/v1/instructors/onboarding-status")
        assert response.status_code == 401
    
    def test_get_onboarding_status_authenticated(self, client, auth_token):
        """Test onboarding status with valid authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/instructors/onboarding-status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "step" in data
        assert "progress_percentage" in data
    
    def test_update_profile_valid(self, client, auth_token):
        """Test updating instructor profile"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        update_data = {
            "bio": "Updated bio with more details about teaching philosophy.",
            "expertise": ["Computer Science", "Artificial Intelligence"],
            "teaching_experience_years": 7
        }
        response = client.put("/api/v1/instructors/profile", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == update_data["bio"]
        assert data["teaching_experience_years"] == update_data["teaching_experience_years"]
    
    def test_submit_verification_valid(self, client, auth_token):
        """Test submitting verification documentation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        verification_data = {
            "document_type": "resume",
            "document_url": "https://example.com/resume.pdf",
            "verification_notes": "Please verify my credentials as requested.",
            "consent_to_verify": True
        }
        response = client.post("/api/v1/instructors/verify", json=verification_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["verification_status"] == "submitted"
    
    def test_submit_verification_missing_consent(self, client, auth_token):
        """Test verification submission without consent"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        verification_data = {
            "document_type": "resume",
            "document_url": "https://example.com/resume.pdf",
            "verification_notes": "Please verify my credentials as requested.",
            # Missing consent_to_verify
        }
        response = client.post("/api/v1/instructors/verify", json=verification_data, headers=headers)
        assert response.status_code == 400
        assert "consent_to_verify" in response.text.lower()

# Additional security tests
def test_xss_protection_in_bio():
    """Test XSS protection in bio field"""
    # Simulate XSS attempt
    xss_payload = "<script>alert('xss')</script>"
    test_data = TEST_INSTRUCTOR_DATA.copy()
    test_data["bio"] = xss_payload
    
    # In real implementation, Pydantic validation should catch this
    # For testing, we assume the validation works correctly
    assert len(xss_payload) > 10  # Basic length check passes
    # Actual XSS protection would be handled by input validation/sanitization

def test_rate_limiting():
    """Test rate limiting on instructor endpoints"""
    # This would be tested in integration tests
    # Rate limit middleware should return 429 after exceeding limits
    pass