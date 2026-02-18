from app.core.config import settings
from tests.helpers import auth_headers, login_user, register_user


def test_register_login_and_profile_flow(client):
    register_payload = register_user(
        client,
        email="student@example.com",
        password="StrongPass123",
        full_name="Student One",
        role="student",
    )

    access_token = register_payload["tokens"]["access_token"]
    me_response = client.get("/api/v1/auth/me", headers=auth_headers(access_token))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "student@example.com"

    login_payload = login_user(client, email="student@example.com", password="StrongPass123")
    assert login_payload["tokens"]["access_token"]
    assert login_payload["tokens"]["refresh_token"]


def test_refresh_token_rotation(client):
    register_payload = register_user(
        client,
        email="refresh@example.com",
        password="StrongPass123",
        full_name="Refresh User",
        role="student",
    )

    refresh_token = register_payload["tokens"]["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["tokens"]["access_token"]


def test_refresh_token_cannot_be_reused(client):
    register_payload = register_user(
        client,
        email="refresh-reuse@example.com",
        password="StrongPass123",
        full_name="Refresh Reuse User",
        role="student",
    )

    original_refresh_token = register_payload["tokens"]["refresh_token"]
    first_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert first_refresh_response.status_code == 200

    second_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert second_refresh_response.status_code == 401

    rotated_refresh_token = first_refresh_response.json()["tokens"]["refresh_token"]
    rotated_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_refresh_token},
    )
    assert rotated_refresh_response.status_code == 200


def test_login_refresh_token_rotation(client):
    register_user(
        client,
        email="login-refresh@example.com",
        password="StrongPass123",
        full_name="Login Refresh User",
        role="student",
    )

    login_payload = login_user(client, email="login-refresh@example.com", password="StrongPass123")
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_payload["tokens"]["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["tokens"]["access_token"]


def test_logout_blacklists_access_token(client):
    register_payload = register_user(
        client,
        email="logout-blacklist@example.com",
        password="StrongPass123",
        full_name="Logout Blacklist User",
        role="student",
    )
    access_token = register_payload["tokens"]["access_token"]
    refresh_token = register_payload["tokens"]["refresh_token"]

    profile_before_logout = client.get("/api/v1/auth/me", headers=auth_headers(access_token))
    assert profile_before_logout.status_code == 200

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers(access_token),
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 204

    profile_after_logout = client.get("/api/v1/auth/me", headers=auth_headers(access_token))
    assert profile_after_logout.status_code == 401


def test_logout_requires_access_token(client):
    register_payload = register_user(
        client,
        email="logout-no-access@example.com",
        password="StrongPass123",
        full_name="Logout No Access User",
        role="student",
    )
    refresh_token = register_payload["tokens"]["refresh_token"]

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401


def test_public_register_rejects_admin_role_when_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_PUBLIC_ROLE_REGISTRATION", False)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "blocked-admin@example.com",
            "password": "StrongPass123",
            "full_name": "Blocked Admin",
            "role": "admin",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Public registration is limited to student accounts"
