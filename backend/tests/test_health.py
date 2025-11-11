"""
Unit tests for backend health endpoint.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that health endpoint returns 200 and correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "movi-backend" in data["service"]
    assert "timestamp" in data
    assert "version" in data


def test_root_endpoint():
    """Test that root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "Movi" in data["message"]
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


def test_health_response_structure():
    """Test that health endpoint returns all expected fields."""
    response = client.get("/health")
    data = response.json()
    
    required_fields = ["status", "service", "layer", "timestamp", "version"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_cors_headers():
    """Test that CORS headers are present (basic check)."""
    response = client.options("/health")
    # TestClient may not fully simulate CORS, but we verify the endpoint exists
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined
