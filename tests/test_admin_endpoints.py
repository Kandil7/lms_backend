"""Integration tests for admin endpoints and setup flow."""

from uuid import uuid4

from tests.helpers import bootstrap_admin_headers


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def _admin_payload(email: str) -> dict:
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
                "email": _email("backup-admin"),
                "phone": "+15551234567",
                "relationship": "Colleague",
                "is_backup": True,
            }
        ],
        "security_policy_accepted": True,
        "security_policy_version": "1.0",
    }


class TestAdminEndpoints:
    def test_setup_admin_valid(self, client):
        headers = bootstrap_admin_headers(client)
        payload = _admin_payload(_email("setup-admin"))

        response = client.post("/api/v1/admin/setup", json=payload, headers=headers)
        assert response.status_code == 201, response.text

        data = response.json()
        assert data["user"]["email"] == payload["email"]
        assert data["onboarding_status"]["step"] in {"verification", "complete"}
        assert data["admin"]["security_health_score"] >= 50

    def test_setup_admin_weak_password(self, client):
        headers = bootstrap_admin_headers(client)
        payload = _admin_payload(_email("weak-admin"))
        payload["password"] = "weak"

        response = client.post("/api/v1/admin/setup", json=payload, headers=headers)
        assert response.status_code == 422
        assert "password" in response.text.lower()

    def test_setup_admin_invalid_ip_whitelist(self, client):
        headers = bootstrap_admin_headers(client)
        payload = _admin_payload(_email("invalid-ip-admin"))
        payload["ip_whitelist"] = ["invalid-ip"]

        response = client.post("/api/v1/admin/setup", json=payload, headers=headers)
        assert response.status_code == 422
        assert "ip_whitelist" in response.text.lower()

    def test_setup_admin_missing_security_policy_acceptance(self, client):
        headers = bootstrap_admin_headers(client)
        payload = _admin_payload(_email("missing-policy-admin"))
        payload["security_policy_accepted"] = False

        response = client.post("/api/v1/admin/setup", json=payload, headers=headers)
        assert response.status_code == 422
        assert "security_policy_accepted" in response.text.lower()

    def test_get_onboarding_status_unauthenticated(self, client):
        response = client.get("/api/v1/admin/onboarding-status")
        assert response.status_code == 401

    def test_get_onboarding_status_authenticated(self, client):
        headers = bootstrap_admin_headers(client)
        response = client.get("/api/v1/admin/onboarding-status", headers=headers)
        assert response.status_code == 200, response.text

        data = response.json()
        assert "step" in data
        assert "mfa_configured" in data

    def test_configure_security_valid(self, client):
        headers = bootstrap_admin_headers(client)
        security_config = {
            "mfa_method": "totp",
            "ip_whitelist": ["127.0.0.1", "192.168.1.1"],
            "time_restrictions": {
                "start_hour": 9,
                "end_hour": 17,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            },
            "require_password_change": True,
            "password_expiry_days": 90,
            "session_timeout_minutes": 30,
            "geo_restrictions": [],
            "anomaly_detection_enabled": True,
        }

        response = client.post("/api/v1/admin/security-config", json=security_config, headers=headers)
        assert response.status_code == 200, response.text

        data = response.json()
        assert data["admin"]["ip_whitelist"] == security_config["ip_whitelist"]
        assert data["admin"]["mfa_required"] is True

    def test_complete_setup_valid(self, client):
        headers = bootstrap_admin_headers(client)

        response = client.post("/api/v1/admin/complete-setup", headers=headers)
        assert response.status_code == 200, response.text

        data = response.json()
        assert data["admin"]["is_setup_complete"] is True
        assert data["admin"]["setup_completed_at"] is not None
        assert data["onboarding_status"]["is_complete"] is True

    def test_create_initial_admin_debug_mode(self, client):
        payload = _admin_payload(_email("initial-admin"))
        response = client.post("/api/v1/admin/create-initial", json=payload)

        # In debug mode this should be enabled; production-like configs may disable it.
        assert response.status_code in {201, 403}
        if response.status_code == 201:
            assert response.json()["user"]["email"] == payload["email"]
