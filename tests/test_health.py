def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_up(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.api.check_database_health", lambda: True)
    response = client.get("/api/v1/ready")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "up"


def test_readiness_endpoint_down(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.api.check_database_health", lambda: False)
    response = client.get("/api/v1/ready")
    assert response.status_code == 503, response.text
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["database"] == "down"


def test_security_headers_are_present(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200, response.text
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
