from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import register_exception_handlers
from app.core.security import TokenType, decode_token
from app.modules.auth.router_cookie import router as cookie_auth_router


@pytest.fixture(scope="function")
def cookie_client(db_session: Session, monkeypatch) -> Generator[TestClient, None, None]:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(cookie_auth_router, prefix=settings.API_V1_PREFIX)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        "app.modules.auth.router_cookie.enqueue_task_with_fallback",
        lambda *args, **kwargs: "inline",
    )

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_cookie_login_refresh_flow(cookie_client: TestClient):
    register_response = cookie_client.post(
        "/api/v1/auth/register",
        json={
            "email": "cookie-refresh@example.com",
            "password": "StrongPass123",
            "full_name": "Cookie Refresh User",
            "role": "student",
        },
    )
    assert register_response.status_code == 201, register_response.text

    login_response = cookie_client.post(
        "/api/v1/auth/login",
        json={"email": "cookie-refresh@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200, login_response.text
    login_payload = login_response.json()
    assert cookie_client.cookies.get("refresh_token")

    refresh_response = cookie_client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {login_payload['tokens']['access_token']}"},
    )
    assert refresh_response.status_code == 200, refresh_response.text
    refresh_payload = refresh_response.json()
    assert isinstance(refresh_payload["access_token"], str)
    assert refresh_payload["token_type"] == "bearer"
    assert refresh_payload["user"]["email"] == "cookie-refresh@example.com"


def test_cookie_logout_without_body_revokes_refresh_token(cookie_client: TestClient):
    register_response = cookie_client.post(
        "/api/v1/auth/register",
        json={
            "email": "cookie-logout@example.com",
            "password": "StrongPass123",
            "full_name": "Cookie Logout User",
            "role": "student",
        },
    )
    assert register_response.status_code == 201, register_response.text

    login_response = cookie_client.post(
        "/api/v1/auth/login",
        json={"email": "cookie-logout@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200, login_response.text
    login_payload = login_response.json()
    refresh_token = cookie_client.cookies.get("refresh_token")
    assert refresh_token

    logout_response = cookie_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_payload['tokens']['access_token']}"},
    )
    assert logout_response.status_code == 204, logout_response.text

    # Fallback to body token should still fail because logout revoked it.
    refresh_after_logout = cookie_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_after_logout.status_code == 401


def test_cookie_mfa_verify_returns_cookie_auth_response(cookie_client: TestClient):
    register_response = cookie_client.post(
        "/api/v1/auth/register",
        json={
            "email": "cookie-mfa@example.com",
            "password": "StrongPass123",
            "full_name": "Cookie MFA User",
            "role": "student",
        },
    )
    assert register_response.status_code == 201, register_response.text
    register_payload = register_response.json()
    user_id = register_payload["user"]["id"]
    access_token = register_payload["tokens"]["access_token"]

    enable_request_response = cookie_client.post(
        "/api/v1/auth/mfa/enable/request",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"password": "StrongPass123"},
    )
    assert enable_request_response.status_code == 200, enable_request_response.text

    mfa_setup_payload = get_app_cache().get_json(f"auth:mfa:setup:{user_id}")
    assert isinstance(mfa_setup_payload, dict)
    setup_code = mfa_setup_payload["code"]

    enable_confirm_response = cookie_client.post(
        "/api/v1/auth/mfa/enable/confirm",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"code": setup_code},
    )
    assert enable_confirm_response.status_code == 200, enable_confirm_response.text

    login_response = cookie_client.post(
        "/api/v1/auth/login",
        json={"email": "cookie-mfa@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200, login_response.text
    login_payload = login_response.json()
    assert login_payload["mfa_required"] is True

    challenge_token = login_payload["challenge_token"]
    challenge_claims = decode_token(
        challenge_token,
        expected_type=TokenType.MFA_CHALLENGE,
        check_blacklist=False,
    )
    challenge_jti = challenge_claims["jti"]

    mfa_login_payload = get_app_cache().get_json(f"auth:mfa:login:{challenge_jti}")
    assert isinstance(mfa_login_payload, dict)
    login_code = mfa_login_payload["code"]

    verify_response = cookie_client.post(
        "/api/v1/auth/login/mfa",
        json={"challenge_token": challenge_token, "code": login_code},
    )
    assert verify_response.status_code == 200, verify_response.text
    verify_payload = verify_response.json()
    assert isinstance(verify_payload["tokens"]["access_token"], str)
    assert verify_payload["user"]["mfa_enabled"] is True
    assert "refresh_token" not in verify_payload["tokens"]
    assert "refresh_token=" in (verify_response.headers.get("set-cookie") or "")
