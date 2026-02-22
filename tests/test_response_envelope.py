from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from app.core.middleware.response_envelope import ResponseEnvelopeMiddleware


def test_response_envelope_wraps_json_success() -> None:
    app = FastAPI()
    app.add_middleware(ResponseEnvelopeMiddleware, success_message="Success", excluded_paths=["/excluded"])

    @app.get("/ok")
    def ok() -> dict:
        return {"value": 1}

    with TestClient(app) as client:
        response = client.get("/ok")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"value": 1},
        "message": "Success",
    }


def test_response_envelope_skips_excluded_and_non_json() -> None:
    app = FastAPI()
    app.add_middleware(ResponseEnvelopeMiddleware, success_message="Success", excluded_paths=["/excluded"])

    @app.get("/excluded")
    def excluded() -> dict:
        return {"value": 2}

    @app.get("/plain")
    def plain() -> PlainTextResponse:
        return PlainTextResponse("ok")

    with TestClient(app) as client:
        excluded_response = client.get("/excluded")
        plain_response = client.get("/plain")

    assert excluded_response.status_code == 200
    assert excluded_response.json() == {"value": 2}
    assert plain_response.status_code == 200
    assert plain_response.text == "ok"

