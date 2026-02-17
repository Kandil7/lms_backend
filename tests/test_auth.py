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
