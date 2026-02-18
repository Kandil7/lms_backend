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


def test_refresh_rejects_mismatched_access_token(client):
    user_one = register_user(
        client,
        email="refresh-mismatch-one@example.com",
        password="StrongPass123",
        full_name="Refresh Mismatch One",
        role="student",
    )
    user_two = register_user(
        client,
        email="refresh-mismatch-two@example.com",
        password="StrongPass123",
        full_name="Refresh Mismatch Two",
        role="student",
    )

    mismatched_response = client.post(
        "/api/v1/auth/refresh",
        headers=auth_headers(user_two["tokens"]["access_token"]),
        json={"refresh_token": user_one["tokens"]["refresh_token"]},
    )
    assert mismatched_response.status_code == 401

    valid_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": user_one["tokens"]["refresh_token"]},
    )
    assert valid_refresh_response.status_code == 200


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


def test_logout_rejects_mismatched_access_and_refresh_tokens(client):
    user_one = register_user(
        client,
        email="logout-mismatch-one@example.com",
        password="StrongPass123",
        full_name="Logout Mismatch One",
        role="student",
    )
    user_two = register_user(
        client,
        email="logout-mismatch-two@example.com",
        password="StrongPass123",
        full_name="Logout Mismatch Two",
        role="student",
    )

    response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers(user_one["tokens"]["access_token"]),
        json={"refresh_token": user_two["tokens"]["refresh_token"]},
    )
    assert response.status_code == 401

    still_valid = client.get("/api/v1/auth/me", headers=auth_headers(user_one["tokens"]["access_token"]))
    assert still_valid.status_code == 200


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


def test_forgot_and_reset_password_flow(client, monkeypatch):
    register_payload = register_user(
        client,
        email="reset-flow@example.com",
        password="StrongPass123",
        full_name="Reset Flow User",
        role="student",
    )
    old_refresh_token = register_payload["tokens"]["refresh_token"]

    captured: dict[str, object] = {}

    def fake_enqueue(task_name: str, *args, **kwargs):
        captured["task_name"] = task_name
        captured["args"] = args
        captured["kwargs"] = kwargs
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    forgot_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset-flow@example.com"},
    )
    assert forgot_response.status_code == 200, forgot_response.text
    assert forgot_response.json()["message"] == "If the email is registered, a reset link has been sent"
    assert captured["task_name"] == "app.tasks.email_tasks.send_password_reset_email"

    reset_kwargs = captured["kwargs"]
    assert isinstance(reset_kwargs, dict)
    reset_token = reset_kwargs["reset_token"]
    assert isinstance(reset_token, str)

    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "NewStrongPass123"},
    )
    assert reset_response.status_code == 200, reset_response.text
    assert reset_response.json()["message"] == "Password has been reset successfully"

    old_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "reset-flow@example.com", "password": "StrongPass123"},
    )
    assert old_login_response.status_code == 401

    new_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "reset-flow@example.com", "password": "NewStrongPass123"},
    )
    assert new_login_response.status_code == 200, new_login_response.text

    old_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert old_refresh_response.status_code == 401


def test_forgot_password_does_not_reveal_user_existence(client, monkeypatch):
    calls: list[tuple[str, tuple, dict]] = []

    def fake_enqueue(task_name: str, *args, **kwargs):
        calls.append((task_name, args, kwargs))
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "unknown-user@example.com"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "If the email is registered, a reset link has been sent"
    assert calls == []


def test_reset_password_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token", "new_password": "NewStrongPass123"},
    )
    assert response.status_code == 401


def test_register_sends_email_verification_task(client, monkeypatch):
    calls: list[tuple[str, tuple, dict]] = []

    def fake_enqueue(task_name: str, *args, **kwargs):
        calls.append((task_name, args, kwargs))
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "verify-task@example.com",
            "password": "StrongPass123",
            "full_name": "Verify Task User",
            "role": "student",
        },
    )
    assert response.status_code == 201, response.text
    task_names = [item[0] for item in calls]
    assert "app.tasks.email_tasks.send_welcome_email" in task_names
    assert "app.tasks.email_tasks.send_email_verification_email" in task_names

    verification_call = next(
        item for item in calls if item[0] == "app.tasks.email_tasks.send_email_verification_email"
    )
    verification_kwargs = verification_call[2]
    assert verification_kwargs["email"] == "verify-task@example.com"
    assert isinstance(verification_kwargs["verification_token"], str)


def test_verify_email_request_and_confirm_flow(client, monkeypatch):
    register_user(
        client,
        email="verify-flow@example.com",
        password="StrongPass123",
        full_name="Verify Flow User",
        role="student",
    )

    captured: dict[str, str] = {}

    def fake_enqueue(task_name: str, *args, **kwargs):
        if task_name == "app.tasks.email_tasks.send_email_verification_email":
            captured["token"] = kwargs["verification_token"]
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    request_response = client.post(
        "/api/v1/auth/verify-email/request",
        json={"email": "verify-flow@example.com"},
    )
    assert request_response.status_code == 200, request_response.text
    assert request_response.json()["message"] == "If the email is registered, a verification link has been sent"
    assert isinstance(captured.get("token"), str)

    confirm_response = client.post(
        "/api/v1/auth/verify-email/confirm",
        json={"token": captured["token"]},
    )
    assert confirm_response.status_code == 200, confirm_response.text
    assert confirm_response.json()["message"] == "Email has been verified successfully"

    login_payload = login_user(client, email="verify-flow@example.com", password="StrongPass123")
    me_response = client.get("/api/v1/auth/me", headers=auth_headers(login_payload["tokens"]["access_token"]))
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["email_verified_at"] is not None


def test_verify_email_request_does_not_reveal_user_existence(client, monkeypatch):
    calls: list[tuple[str, tuple, dict]] = []

    def fake_enqueue(task_name: str, *args, **kwargs):
        calls.append((task_name, args, kwargs))
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    response = client.post(
        "/api/v1/auth/verify-email/request",
        json={"email": "unknown-verify@example.com"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "If the email is registered, a verification link has been sent"
    assert calls == []


def test_verify_email_confirm_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/verify-email/confirm",
        json={"token": "invalid-token"},
    )
    assert response.status_code == 401


def test_login_requires_verified_email_when_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN", True)

    calls: list[tuple[str, tuple, dict]] = []

    def fake_enqueue(task_name: str, *args, **kwargs):
        calls.append((task_name, args, kwargs))
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "verify-required@example.com",
            "password": "StrongPass123",
            "full_name": "Verify Required User",
            "role": "student",
        },
    )
    assert register_response.status_code == 201, register_response.text

    blocked_login = client.post(
        "/api/v1/auth/login",
        json={"email": "verify-required@example.com", "password": "StrongPass123"},
    )
    assert blocked_login.status_code == 401
    assert blocked_login.json()["detail"] == "Email is not verified"

    verification_call = next(
        item for item in calls if item[0] == "app.tasks.email_tasks.send_email_verification_email"
    )
    verification_token = verification_call[2]["verification_token"]

    confirm_response = client.post(
        "/api/v1/auth/verify-email/confirm",
        json={"token": verification_token},
    )
    assert confirm_response.status_code == 200, confirm_response.text

    allowed_login = client.post(
        "/api/v1/auth/login",
        json={"email": "verify-required@example.com", "password": "StrongPass123"},
    )
    assert allowed_login.status_code == 200, allowed_login.text


def test_mfa_enable_and_login_challenge_flow(client, monkeypatch):
    register_payload = register_user(
        client,
        email="mfa-flow@example.com",
        password="StrongPass123",
        full_name="MFA Flow User",
        role="student",
    )
    access_token = register_payload["tokens"]["access_token"]

    calls: list[tuple[str, tuple, dict]] = []

    def fake_enqueue(task_name: str, *args, **kwargs):
        calls.append((task_name, args, kwargs))
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    enable_request = client.post(
        "/api/v1/auth/mfa/enable/request",
        headers=auth_headers(access_token),
        json={"password": "StrongPass123"},
    )
    assert enable_request.status_code == 200, enable_request.text
    assert enable_request.json()["message"] == "A verification code has been sent to your email"

    setup_call = next(item for item in calls if item[0] == "app.tasks.email_tasks.send_mfa_setup_code_email")
    setup_code = setup_call[2]["code"]

    enable_confirm = client.post(
        "/api/v1/auth/mfa/enable/confirm",
        headers=auth_headers(access_token),
        json={"code": setup_code},
    )
    assert enable_confirm.status_code == 200, enable_confirm.text
    assert enable_confirm.json()["message"] == "MFA has been enabled successfully"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "mfa-flow@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200, login_response.text
    login_payload = login_response.json()
    assert login_payload["mfa_required"] is True
    assert isinstance(login_payload["challenge_token"], str)

    login_code_call = next(item for item in calls if item[0] == "app.tasks.email_tasks.send_mfa_login_code_email")
    login_code = login_code_call[2]["code"]

    verify_response = client.post(
        "/api/v1/auth/login/mfa",
        json={"challenge_token": login_payload["challenge_token"], "code": login_code},
    )
    assert verify_response.status_code == 200, verify_response.text
    assert verify_response.json()["tokens"]["access_token"]
    assert verify_response.json()["user"]["mfa_enabled"] is True


def test_mfa_login_rejects_invalid_code(client, monkeypatch):
    register_payload = register_user(
        client,
        email="mfa-invalid@example.com",
        password="StrongPass123",
        full_name="MFA Invalid User",
        role="student",
    )
    access_token = register_payload["tokens"]["access_token"]

    calls: list[tuple[str, tuple, dict]] = []

    def fake_enqueue(task_name: str, *args, **kwargs):
        calls.append((task_name, args, kwargs))
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    request_response = client.post(
        "/api/v1/auth/mfa/enable/request",
        headers=auth_headers(access_token),
        json={"password": "StrongPass123"},
    )
    assert request_response.status_code == 200, request_response.text
    setup_code = next(item for item in calls if item[0] == "app.tasks.email_tasks.send_mfa_setup_code_email")[2]["code"]

    confirm_response = client.post(
        "/api/v1/auth/mfa/enable/confirm",
        headers=auth_headers(access_token),
        json={"code": setup_code},
    )
    assert confirm_response.status_code == 200, confirm_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "mfa-invalid@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200, login_response.text
    challenge_token = login_response.json()["challenge_token"]

    verify_response = client.post(
        "/api/v1/auth/login/mfa",
        json={"challenge_token": challenge_token, "code": "000000"},
    )
    assert verify_response.status_code == 401
    assert verify_response.json()["detail"] == "Invalid MFA code"


def test_mfa_disable_restores_direct_login(client, monkeypatch):
    register_payload = register_user(
        client,
        email="mfa-disable@example.com",
        password="StrongPass123",
        full_name="MFA Disable User",
        role="student",
    )
    access_token = register_payload["tokens"]["access_token"]

    calls: list[tuple[str, tuple, dict]] = []

    def fake_enqueue(task_name: str, *args, **kwargs):
        calls.append((task_name, args, kwargs))
        return "inline"

    monkeypatch.setattr("app.modules.auth.router.enqueue_task_with_fallback", fake_enqueue)

    enable_request = client.post(
        "/api/v1/auth/mfa/enable/request",
        headers=auth_headers(access_token),
        json={"password": "StrongPass123"},
    )
    assert enable_request.status_code == 200, enable_request.text
    setup_code = next(item for item in calls if item[0] == "app.tasks.email_tasks.send_mfa_setup_code_email")[2]["code"]

    enable_confirm = client.post(
        "/api/v1/auth/mfa/enable/confirm",
        headers=auth_headers(access_token),
        json={"code": setup_code},
    )
    assert enable_confirm.status_code == 200, enable_confirm.text

    disable_response = client.post(
        "/api/v1/auth/mfa/disable",
        headers=auth_headers(access_token),
        json={"password": "StrongPass123"},
    )
    assert disable_response.status_code == 200, disable_response.text
    assert disable_response.json()["message"] == "MFA has been disabled successfully"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "mfa-disable@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200, login_response.text
    assert login_response.json()["tokens"]["access_token"]
    assert login_response.json()["user"]["mfa_enabled"] is False
