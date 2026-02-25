"""Integration tests for instructor endpoints and onboarding flow."""

from uuid import uuid4

from tests.helpers import auth_headers, bootstrap_admin_headers, login_user


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def _instructor_payload(email: str) -> dict:
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


class TestInstructorEndpoints:
    def test_register_instructor_valid(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert response.status_code == 201, response.text

        data = response.json()
        assert data["user"]["email"] == payload["email"]
        assert data["user"]["role"] == "instructor"
        assert data["instructor"]["verification_status"] == "pending"
        assert data["verification_required"] is True
        assert data["onboarding_status"]["step"] == "profile"

    def test_register_instructor_unauthenticated(self, client):
        payload = _instructor_payload(_email("instructor"))
        response = client.post("/api/v1/instructors/register", json=payload)
        assert response.status_code == 401

    def test_register_instructor_invalid_email(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        payload["email"] = "invalid-email"

        response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert response.status_code == 422
        assert "email" in response.text.lower()

    def test_register_instructor_weak_password(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        payload["password"] = "weak"

        response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert response.status_code == 422
        assert "password" in response.text.lower()

    def test_register_instructor_short_bio(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        payload["bio"] = "short"

        response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert response.status_code == 422
        assert "bio" in response.text.lower()

    def test_get_onboarding_status_unauthenticated(self, client):
        response = client.get("/api/v1/instructors/onboarding-status")
        assert response.status_code == 401

    def test_get_onboarding_status_authenticated(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        register_response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert register_response.status_code == 201, register_response.text

        login = login_user(client, email=payload["email"], password=payload["password"])
        headers = auth_headers(login["tokens"]["access_token"])

        response = client.get("/api/v1/instructors/onboarding-status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["step"] == "profile"
        assert data["progress_percentage"] == 50

    def test_update_profile_valid(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        register_response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert register_response.status_code == 201, register_response.text

        login = login_user(client, email=payload["email"], password=payload["password"])
        headers = auth_headers(login["tokens"]["access_token"])

        update_data = {
            "bio": "Updated bio with more details about teaching philosophy.",
            "expertise": ["Computer Science", "Artificial Intelligence"],
            "teaching_experience_years": 7,
            "education_level": "Doctorate",
            "institution": "Updated University",
        }
        response = client.put("/api/v1/instructors/profile", json=update_data, headers=headers)
        assert response.status_code == 200, response.text

        body = response.json()
        assert body["instructor"]["bio"] == update_data["bio"]
        assert body["instructor"]["teaching_experience_years"] == update_data["teaching_experience_years"]

    def test_submit_verification_valid(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        register_response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert register_response.status_code == 201, register_response.text

        login = login_user(client, email=payload["email"], password=payload["password"])
        headers = auth_headers(login["tokens"]["access_token"])

        verification_data = {
            "document_type": "resume",
            "document_url": "https://example.com/resume.pdf",
            "verification_notes": "Please verify my credentials as requested.",
            "consent_to_verify": True,
        }
        response = client.post("/api/v1/instructors/verify", json=verification_data, headers=headers)
        assert response.status_code == 200, response.text

        body = response.json()
        assert body["instructor"]["verification_status"] == "submitted"
        assert body["onboarding_status"]["verification_submitted"] is True

    def test_submit_verification_missing_consent(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        register_response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert register_response.status_code == 201, register_response.text

        login = login_user(client, email=payload["email"], password=payload["password"])
        headers = auth_headers(login["tokens"]["access_token"])

        verification_data = {
            "document_type": "resume",
            "document_url": "https://example.com/resume.pdf",
            "verification_notes": "Please verify my credentials as requested.",
        }
        response = client.post("/api/v1/instructors/verify", json=verification_data, headers=headers)
        assert response.status_code == 422
        assert "consent_to_verify" in response.text.lower()

    def test_submit_verification_requires_true_consent(self, client):
        admin_headers = bootstrap_admin_headers(client)
        payload = _instructor_payload(_email("instructor"))
        register_response = client.post("/api/v1/instructors/register", json=payload, headers=admin_headers)
        assert register_response.status_code == 201, register_response.text

        login = login_user(client, email=payload["email"], password=payload["password"])
        headers = auth_headers(login["tokens"]["access_token"])

        verification_data = {
            "document_type": "resume",
            "document_url": "https://example.com/resume.pdf",
            "verification_notes": "Please verify my credentials as requested.",
            "consent_to_verify": False,
        }
        response = client.post("/api/v1/instructors/verify", json=verification_data, headers=headers)
        assert response.status_code == 422
        assert "consent_to_verify" in response.text.lower()
