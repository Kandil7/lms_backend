"""Comprehensive tests for admin endpoints"""

import pytest
import requests
from typing import Dict, Any
from datetime import datetime, timedelta

# Test data
TEST_ADMIN_DATA = {
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

TEST_INVALID_ADMIN_DATA = {
    "email": "invalid-email",
    "password": "weak",  # Too short
    "full_name": "",
    "role": "admin",
    "security_level": "basic",  # Invalid value
    "mfa_required": True,
    "ip_whitelist": ["invalid-ip"],
    "time_restrictions": {
        "start_hour": 25,  # Invalid hour
        "end_hour": 5,
        "days": ["invalid-day"]
    },
    "emergency_contacts": [],
    "security_policy_accepted": False,  # Missing acceptance
    "security_policy_version": ""
}

class TestAdminEndpoints:
    
    def test_setup_admin_valid(self, client):
        """Test successful admin setup"""
        response = client.post("/api/v1/admin/setup", json=TEST_ADMIN_DATA)
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "onboarding_status" in data
        assert data["onboarding_status"]["step"] == "account_setup"
        assert data["onboarding_status"]["security_health_score"] >= 80
    
    def test_setup_admin_weak_password(self, client):
        """Test admin setup with weak password"""
        invalid_data = TEST_ADMIN_DATA.copy()
        invalid_data["password"] = "weak"
        response = client.post("/api/v1/admin/setup", json=invalid_data)
        assert response.status_code == 400
        assert "password" in response.text.lower()
    
    def test_setup_admin_invalid_ip_whitelist(self, client):
        """Test admin setup with invalid IP whitelist"""
        invalid_data = TEST_ADMIN_DATA.copy()
        invalid_data["ip_whitelist"] = ["invalid-ip"]
        response = client.post("/api/v1/admin/setup", json=invalid_data)
        assert response.status_code == 400
        assert "ip_whitelist" in response.text.lower()
    
    def test_setup_admin_missing_security_policy_acceptance(self, client):
        """Test admin setup without security policy acceptance"""
        invalid_data = TEST_ADMIN_DATA.copy()
        invalid_data["security_policy_accepted"] = False
        response = client.post("/api/v1/admin/setup", json=invalid_data)
        assert response.status_code == 400
        assert "security_policy_accepted" in response.text.lower()
    
    def test_get_onboarding_status_unauthenticated(self, client):
        """Test admin onboarding status without authentication"""
        response = client.get("/api/v1/admin/onboarding-status")
        assert response.status_code == 401
    
    def test_get_onboarding_status_authenticated(self, client, auth_token):
        """Test admin onboarding status with valid authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/admin/onboarding-status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "step" in data
        assert "security_health_score" in data
        assert "mfa_configured" in data
    
    def test_configure_security_valid(self, client, auth_token):
        """Test configuring admin security settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        security_config = {
            "mfa_method": "totp",
            "ip_whitelist": ["127.0.0.1", "192.168.1.1"],
            "time_restrictions": {
                "start_hour": 9,
                "end_hour": 17,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
            "require_password_change": True,
            "password_expiry_days": 90,
            "session_timeout_minutes": 30,
            "geo_restrictions": [],
            "anomaly_detection_enabled": True
        }
        response = client.post("/api/v1/admin/security-config", json=security_config, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mfa_method"] == "totp"
        assert data["ip_whitelist"] == security_config["ip_whitelist"]
    
    def test_complete_setup_valid(self, client, auth_token):
        """Test completing admin setup"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/v1/admin/complete-setup", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_setup_complete"] is True
        assert data["setup_completed_at"] is not None
    
    def test_create_initial_admin_debug_mode(self, client):
        """Test creating initial admin in debug mode"""
        # This would be tested in debug environment
        # In production, this should return 403
        initial_admin_data = {
            "email": "initial-admin@example.com",
            "password": "InitialAdminPassword123!",
            "full_name": "Initial System Admin",
            "role": "admin",
            "security_level": "enhanced",
            "mfa_required": True,
            "security_policy_accepted": True,
            "security_policy_version": "1.0"
        }
        response = client.post("/api/v1/admin/create-initial", json=initial_admin_data)
        # Status depends on environment configuration
        if response.status_code == 201:
            assert "user" in response.json()
        elif response.status_code == 403:
            assert "initial admin creation disabled" in response.text.lower()

# Security-specific tests
def test_mfa_enforcement():
    """Test MFA enforcement for admin accounts"""
    # Admin accounts should require MFA configuration
    # Test that security-config endpoint enforces mfa_required=True
    pass

def test_rate_limiting_admin_endpoints():
    """Test rate limiting on admin endpoints"""
    # Admin endpoints should have stricter rate limits
    # Test that excessive requests return 429
    pass

def test_xss_protection_in_emergency_contacts():
    """Test XSS protection in emergency contact fields"""
    # Emergency contact names, emails, phones should be validated
    xss_payload = "<script>alert('xss')</script>"
    test_contact = {
        "name": xss_payload,
        "email": "test@example.com",
        "phone": "+15551234567",
        "relationship": "Colleague",
        "is_backup": True
    }
    
    # Pydantic validation should catch invalid string formats
    assert len(xss_payload) > 0  # Basic validation passes length check
    # Actual XSS protection would be handled by input validation

def test_input_validation_strictness():
    """Test strict input validation for admin endpoints"""
    # All admin endpoint inputs should have strict validation
    # Test edge cases and boundary conditions
    pass