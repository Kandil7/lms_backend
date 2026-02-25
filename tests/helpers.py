from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


_BOOTSTRAP_ADMIN_EMAIL: str | None = None
_BOOTSTRAP_ADMIN_PASSWORD = "VeryStrongPassword123456!"
_BOOTSTRAP_ADMIN_ACCESS_TOKEN: str | None = None


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _with_unique_suffix(email: str) -> str:
    local, _, domain = email.partition("@")
    suffix = uuid4().hex[:8]
    if domain:
        return f"{local}+{suffix}@{domain}"
    return f"{email}-{suffix}"


def _ensure_admin_setup_complete(client: TestClient, access_token: str) -> None:
    headers = auth_headers(access_token)
    status_response = client.get("/api/v1/admin/onboarding-status", headers=headers)
    assert status_response.status_code == 200, status_response.text
    if status_response.json().get("is_complete"):
        return

    complete_response = client.post("/api/v1/admin/complete-setup", headers=headers)
    assert complete_response.status_code == 200, complete_response.text


def _ensure_admin_access_token(client: TestClient) -> str:
    global _BOOTSTRAP_ADMIN_ACCESS_TOKEN, _BOOTSTRAP_ADMIN_EMAIL

    if _BOOTSTRAP_ADMIN_ACCESS_TOKEN:
        me_response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(_BOOTSTRAP_ADMIN_ACCESS_TOKEN),
        )
        if me_response.status_code == 200:
            return _BOOTSTRAP_ADMIN_ACCESS_TOKEN

    if _BOOTSTRAP_ADMIN_EMAIL:
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": _BOOTSTRAP_ADMIN_EMAIL,
                "password": _BOOTSTRAP_ADMIN_PASSWORD,
            },
        )
        if login_response.status_code == 200:
            access_token = login_response.json()["tokens"]["access_token"]
            _ensure_admin_setup_complete(client, access_token)
            _BOOTSTRAP_ADMIN_ACCESS_TOKEN = access_token
            return access_token

    _BOOTSTRAP_ADMIN_EMAIL = _with_unique_suffix("tests-bootstrap-admin@example.com")
    create_response = client.post(
        "/api/v1/admin/create-initial",
        json={
            "email": _BOOTSTRAP_ADMIN_EMAIL,
            "password": _BOOTSTRAP_ADMIN_PASSWORD,
            "full_name": "Tests Bootstrap Admin",
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
                    "email": _with_unique_suffix("backup-admin@example.com"),
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
        json={
            "email": _BOOTSTRAP_ADMIN_EMAIL,
            "password": _BOOTSTRAP_ADMIN_PASSWORD,
        },
    )
    assert login_response.status_code == 200, login_response.text
    access_token = login_response.json()["tokens"]["access_token"]
    _ensure_admin_setup_complete(client, access_token)
    _BOOTSTRAP_ADMIN_ACCESS_TOKEN = access_token
    return access_token


def bootstrap_admin_headers(client: TestClient) -> dict[str, str]:
    return auth_headers(_ensure_admin_access_token(client))


def _create_instructor_via_admin(
    client: TestClient,
    *,
    email: str,
    password: str,
    full_name: str,
):
    admin_headers = bootstrap_admin_headers(client)
    register_response = client.post(
        "/api/v1/instructors/register",
        headers=admin_headers,
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": "instructor",
            "bio": "Experienced educator focused on practical outcomes.",
            "expertise": ["Software Engineering"],
            "teaching_experience_years": 3,
            "education_level": "Bachelor's",
            "institution": "LMS Test Institute",
        },
    )
    if register_response.status_code == 201:
        instructor_id = register_response.json()["instructor"]["id"]
        approve_response = client.post(
            f"/api/v1/instructors/verify/approve/{instructor_id}",
            headers=admin_headers,
        )
        assert approve_response.status_code == 200, approve_response.text

    elif register_response.status_code not in {400, 409}:
        raise AssertionError(register_response.text)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()


def _create_admin_via_admin(
    client: TestClient,
    *,
    email: str,
    password: str,
    full_name: str,
):
    admin_headers = bootstrap_admin_headers(client)
    setup_response = client.post(
        "/api/v1/admin/setup",
        headers=admin_headers,
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
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
                    "email": _with_unique_suffix("backup-admin@example.com"),
                    "phone": "+15551234567",
                    "relationship": "Colleague",
                    "is_backup": True,
                }
            ],
            "security_policy_accepted": True,
            "security_policy_version": "1.0",
        },
    )
    if setup_response.status_code not in {201, 400, 409}:
        raise AssertionError(setup_response.text)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    access_token = login_response.json()["tokens"]["access_token"]
    _ensure_admin_setup_complete(client, access_token)
    return login_response.json()


def _create_user_via_admin(
    client: TestClient,
    *,
    email: str,
    password: str,
    full_name: str,
    role: str,
):
    if role == "instructor":
        return _create_instructor_via_admin(
            client,
            email=email,
            password=password,
            full_name=full_name,
        )

    if role == "admin":
        return _create_admin_via_admin(
            client,
            email=email,
            password=password,
            full_name=full_name,
        )

    admin_access_token = _ensure_admin_access_token(client)
    create_response = client.post(
        "/api/v1/users",
        headers=auth_headers(admin_access_token),
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
        },
    )

    if create_response.status_code not in {201, 409}:
        raise AssertionError(create_response.text)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()


def register_user(client: TestClient, *, email: str, password: str, full_name: str, role: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
        },
    )

    if response.status_code == 201:
        return response.json()

    detail = response.text

    if response.status_code == 409 and "Email is already registered" in detail:
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        if login_response.status_code == 200:
            return login_response.json()
        raise AssertionError(detail)

    if (
        response.status_code == 403
        and role != "student"
        and "Public registration is limited to student accounts" in detail
    ):
        return _create_user_via_admin(
            client,
            email=email,
            password=password,
            full_name=full_name,
            role=role,
        )

    raise AssertionError(detail)


def login_user(client: TestClient, *, email: str, password: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()
