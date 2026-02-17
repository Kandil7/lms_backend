from fastapi.testclient import TestClient


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
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client: TestClient, *, email: str, password: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
