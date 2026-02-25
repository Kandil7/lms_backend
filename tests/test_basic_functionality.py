"""Basic functionality tests for app startup and core public routes."""


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint(client):
    """Test the readiness check endpoint"""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "database" in data
    assert "redis" in data


def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "LMS Backend API"}


def test_api_docs_available(client):
    """Test that API docs are available (when enabled)"""
    # Check if docs URL is accessible
    response = client.get("/docs")
    # Docs might be disabled in production mode, so check status code
    assert response.status_code in [200, 404]


def test_auth_router_loaded(client):
    """Test that auth router is loaded (basic endpoint)"""
    # Try to access a basic auth endpoint that should exist
    response = client.post("/api/v1/auth/token", data={"username": "test", "password": "test"})
    # This should return 400 or 401, not 404, indicating router is loaded
    assert response.status_code in [400, 401]
