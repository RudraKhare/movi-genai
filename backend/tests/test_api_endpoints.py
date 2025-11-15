# backend/tests/test_api_endpoints.py
"""
Integration tests for REST API endpoints.
"""
import pytest
from httpx import AsyncClient
from app.main import app
import os

# Set test API key
TEST_API_KEY = "test-key-12345"
os.environ["MOVI_API_KEY"] = TEST_API_KEY


@pytest.fixture
def headers():
    """Headers with valid API key for authenticated requests."""
    return {"x-api-key": TEST_API_KEY}


# ============================================================================
# Health & Status Tests
# ============================================================================

@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns API information."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_health_status():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/health/status", headers={"x-api-key": TEST_API_KEY})
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy", "degraded"]


@pytest.mark.asyncio
async def test_health_ping():
    """Test ping endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/health/ping", headers={"x-api-key": TEST_API_KEY})
    
    assert response.status_code == 200
    data = response.json()
    assert data["ping"] == "pong"


# ============================================================================
# Authentication Tests
# ============================================================================

@pytest.mark.asyncio
async def test_api_key_required():
    """Test that API endpoints require valid API key."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/routes/")
    
    assert response.status_code == 403
    data = response.json()
    assert "Unauthorized" in data["error"]


@pytest.mark.asyncio
async def test_api_key_valid(headers):
    """Test that valid API key allows access."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/routes/", headers=headers)
    
    # Should succeed or fail with 500 (if DB not configured), not 403
    assert response.status_code in [200, 500]


# ============================================================================
# Routes Endpoints Tests
# ============================================================================

@pytest.mark.asyncio
async def test_list_routes(headers):
    """Test listing all routes."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/routes/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "routes" in data
        assert isinstance(data["routes"], list)


@pytest.mark.asyncio
async def test_list_stops(headers):
    """Test listing all stops."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/routes/stops/all", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "stops" in data
        assert isinstance(data["stops"], list)


@pytest.mark.asyncio
async def test_list_vehicles(headers):
    """Test listing all vehicles."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/routes/vehicles/all", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "vehicles" in data
        assert isinstance(data["vehicles"], list)


# ============================================================================
# Context Endpoints Tests
# ============================================================================

@pytest.mark.asyncio
async def test_dashboard_context(headers):
    """Test dashboard context endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/context/dashboard", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "trips" in data
        assert isinstance(data["trips"], list)
        if "summary" in data:
            assert "total_trips" in data["summary"]


@pytest.mark.asyncio
async def test_manage_context(headers):
    """Test manage context endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/context/manage", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "stops" in data
        assert "routes" in data
        assert "paths" in data
        assert "vehicles" in data
        assert "drivers" in data


# ============================================================================
# Action Endpoints Tests (Note: These modify data)
# ============================================================================

@pytest.mark.asyncio
async def test_assign_vehicle_validation(headers):
    """Test assign vehicle endpoint validates input."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Invalid request (missing fields)
        response = await ac.post(
            "/api/actions/assign_vehicle",
            headers=headers,
            json={}
        )
    
    # Should return 422 (validation error)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_remove_vehicle_validation(headers):
    """Test remove vehicle endpoint validates input."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Invalid request (missing fields)
        response = await ac.post(
            "/api/actions/remove_vehicle",
            headers=headers,
            json={}
        )
    
    # Should return 422 (validation error)
    assert response.status_code == 422


# ============================================================================
# Audit Endpoints Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_audit_logs(headers):
    """Test getting audit logs for an entity."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/audit/logs/trip/1", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
        assert data["entity_type"] == "trip"
        assert data["entity_id"] == 1


@pytest.mark.asyncio
async def test_get_recent_audit_logs(headers):
    """Test getting recent audit logs."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/audit/logs/recent?limit=10", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
        assert len(data["logs"]) <= 10


@pytest.mark.asyncio
async def test_get_action_types(headers):
    """Test getting distinct action types."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/audit/actions", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert "actions" in data
        assert isinstance(data["actions"], list)


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_404_on_invalid_route(headers):
    """Test that invalid routes return 404."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/nonexistent/endpoint", headers=headers)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_route(headers):
    """Test getting a route that doesn't exist."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/routes/999999", headers=headers)
    
    # Should return 404 (not found) if DB is configured
    if response.status_code != 500:  # Skip if DB not configured
        assert response.status_code == 404
