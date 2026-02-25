"""Integration tests for user endpoints and role-based access."""

from uuid import uuid4

from tests.helpers import auth_headers, register_user


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def test_get_my_profile_returns_authenticated_user(client):
    email = _email("users-me")
    payload = register_user(
        client,
        email=email,
        password="StrongPass123",
        full_name="Users Me Student",
        role="student",
    )
    headers = auth_headers(payload["tokens"]["access_token"])

    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == email
    assert body["role"] == "student"


def test_admin_can_create_list_get_and_update_users(client):
    admin_email = _email("users-admin")
    admin_payload = register_user(
        client,
        email=admin_email,
        password="StrongPass123",
        full_name="Users Admin",
        role="admin",
    )
    admin_headers = auth_headers(admin_payload["tokens"]["access_token"])

    student_email = _email("users-student")
    create_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": student_email,
            "password": "StrongPass123",
            "full_name": "Managed Student",
            "role": "student",
        },
    )
    assert create_response.status_code == 201, create_response.text
    created_user = create_response.json()
    user_id = created_user["id"]
    assert created_user["email"] == student_email

    list_response = client.get("/api/v1/users", headers=admin_headers)
    assert list_response.status_code == 200, list_response.text
    list_body = list_response.json()
    assert list_body["total"] >= 1
    assert any(item["id"] == user_id for item in list_body["items"])

    get_response = client.get(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["email"] == student_email

    patch_response = client.patch(
        f"/api/v1/users/{user_id}",
        headers=admin_headers,
        json={"full_name": "Updated Managed Student", "is_active": True},
    )
    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json()["full_name"] == "Updated Managed Student"


def test_non_admin_cannot_create_users(client):
    student = register_user(
        client,
        email=_email("users-non-admin"),
        password="StrongPass123",
        full_name="Regular Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    response = client.post(
        "/api/v1/users",
        headers=student_headers,
        json={
            "email": _email("users-created-by-student"),
            "password": "StrongPass123",
            "full_name": "Should Fail",
            "role": "student",
        },
    )
    assert response.status_code == 403


def test_admin_without_completed_setup_cannot_manage_users(client):
    email = _email("users-incomplete-admin")
    create_response = client.post(
        "/api/v1/admin/create-initial",
        json={
            "email": email,
            "password": "VeryStrongPassword123456!",
            "full_name": "Incomplete Admin",
            "role": "admin",
            "security_level": "enhanced",
            "mfa_required": True,
            "ip_whitelist": ["127.0.0.1"],
            "time_restrictions": {
                "start_hour": 9,
                "end_hour": 17,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            },
            "emergency_contacts": [
                {
                    "name": "Backup Admin",
                    "email": _email("users-incomplete-backup-admin"),
                    "phone": "+15551234567",
                    "relationship": "Colleague",
                    "is_backup": True,
                }
            ],
            "security_policy_accepted": True,
            "security_policy_version": "1.0",
        },
    )
    assert create_response.status_code == 201, create_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "VeryStrongPassword123456!"},
    )
    assert login_response.status_code == 200, login_response.text
    headers = auth_headers(login_response.json()["tokens"]["access_token"])

    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin setup must be completed before performing this action"
