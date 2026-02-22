from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware.rate_limit import RateLimitMiddleware, RateLimitRule
from app.core.security import create_access_token


def _build_rate_limited_app(*, rules: list[RateLimitRule]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        limit=100,
        period_seconds=60,
        use_redis=False,
        key_prefix="test-ratelimit",
        excluded_paths=[],
        custom_rules=rules,
    )

    @app.post("/api/v1/auth/login")
    def login() -> dict:
        return {"ok": True}

    @app.post("/api/v1/files/upload")
    def upload() -> dict:
        return {"ok": True}

    return app


def test_auth_custom_rate_limit_rule() -> None:
    app = _build_rate_limited_app(
        rules=[
            RateLimitRule(
                name="auth",
                path_prefixes=["/api/v1/auth/login"],
                limit=2,
                period_seconds=60,
                key_mode="ip",
            )
        ]
    )

    with TestClient(app) as client:
        first = client.post("/api/v1/auth/login")
        second = client.post("/api/v1/auth/login")
        third = client.post("/api/v1/auth/login")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.headers["X-RateLimit-Limit"] == "2"


def test_upload_rate_limit_uses_user_identity_when_token_exists() -> None:
    app = _build_rate_limited_app(
        rules=[
            RateLimitRule(
                name="upload",
                path_prefixes=["/api/v1/files/upload"],
                limit=1,
                period_seconds=60,
                key_mode="user_or_ip",
            )
        ]
    )

    token_a = create_access_token(subject=str(uuid4()), role="student")
    token_b = create_access_token(subject=str(uuid4()), role="student")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    with TestClient(app) as client:
        first_a = client.post("/api/v1/files/upload", headers=headers_a)
        second_a = client.post("/api/v1/files/upload", headers=headers_a)
        first_b = client.post("/api/v1/files/upload", headers=headers_b)

    assert first_a.status_code == 200
    assert second_a.status_code == 429
    assert first_b.status_code == 200

