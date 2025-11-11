# backend/tests/test_core_service.py
"""
Tests for core service layer (assign_vehicle, remove_vehicle, cancel_trip).

These tests use the real seeded database. They are designed to be idempotent
by cleaning up after themselves.
"""
import pytest
import asyncio
from app.core.service import (
    assign_vehicle, 
    remove_vehicle, 
    cancel_trip, 
    ServiceError,
    get_trip_info
)
from app.core.consequences import (
    get_trip_consequences,
    check_vehicle_availability,
    check_driver_availability
)
from app.core.supabase_client import init_db_pool, close_pool
from app.core.db import fetch, execute, transaction


# Fixture to initialize DB pool once for all tests
@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    """Initialize database pool before tests and close after."""
    await init_db_pool(min_size=1, max_size=5)
    yield
    await close_pool()


# Test fixtures: Get available test data from seeded DB
@pytest.fixture(scope="module")
async def test_trip_id():
    """Get an available trip ID from seeded data."""
    trips = await fetch("SELECT trip_id FROM daily_trips WHERE live_status='SCHEDULED' LIMIT 1")
    if not trips:
        pytest.skip("No SCHEDULED trips in database for testing")
    return trips[0]['trip_id']


@pytest.fixture(scope="module")
async def test_vehicle_id():
    """Get an available vehicle ID."""
    vehicles = await fetch("SELECT vehicle_id FROM vehicles LIMIT 1")
    if not vehicles:
        pytest.skip("No vehicles in database for testing")
    return vehicles[0]['vehicle_id']


@pytest.fixture(scope="module")
async def test_driver_id():
    """Get an available driver ID."""
    drivers = await fetch("SELECT driver_id FROM drivers LIMIT 1")
    if not drivers:
        pytest.skip("No drivers in database for testing")
    return drivers[0]['driver_id']


# ============================================================================
# Consequence Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_trip_consequences_structure(test_trip_id):
    """Test that get_trip_consequences returns expected structure."""
    data = await get_trip_consequences(test_trip_id)
    
    # Check all expected keys are present
    assert "trip_id" in data
    assert "display_name" in data
    assert "live_status" in data
    assert "booked_count" in data
    assert "seats_booked" in data
    assert "has_deployment" in data
    assert "has_bookings" in data
    
    # Check types
    assert isinstance(data["trip_id"], int)
    assert isinstance(data["booked_count"], int)
    assert isinstance(data["seats_booked"], int)
    assert isinstance(data["has_deployment"], bool)
    assert isinstance(data["has_bookings"], bool)


@pytest.mark.asyncio
async def test_get_trip_consequences_nonexistent():
    """Test that get_trip_consequences returns empty dict for nonexistent trip."""
    data = await get_trip_consequences(999999)
    assert data == {}


@pytest.mark.asyncio
async def test_check_vehicle_availability():
    """Test vehicle availability checking."""
    # This test assumes vehicle 1 exists but may or may not be deployed
    result = await check_vehicle_availability(1, "2025-11-15")
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_check_driver_availability():
    """Test driver availability checking."""
    # This test assumes driver 1 exists but may or may not be deployed
    result = await check_driver_availability(1, "2025-11-15")
    assert isinstance(result, bool)


# ============================================================================
# Service Operation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_assign_and_remove_vehicle_cycle():
    """
    Test complete cycle: assign vehicle -> verify -> remove vehicle.
    
    This test creates a new trip specifically for testing to avoid conflicts.
    """
    # Create a test trip
    async with transaction() as conn:
        # Get a route and date for test trip
        route = await conn.fetchrow("SELECT route_id FROM routes LIMIT 1")
        if not route:
            pytest.skip("No routes available for test trip creation")
        
        route_id = route['route_id']
        
        # Create test trip
        test_trip = await conn.fetchrow(
            """
            INSERT INTO daily_trips (route_id, trip_date, live_status, display_name)
            VALUES ($1, '2025-11-20', 'SCHEDULED', 'Test Trip - Auto Delete')
            RETURNING trip_id
            """,
            route_id
        )
        
        test_trip_id = test_trip['trip_id']
    
    try:
        # Get available vehicle and driver
        vehicles = await fetch("SELECT vehicle_id FROM vehicles LIMIT 1")
        drivers = await fetch("SELECT driver_id FROM drivers LIMIT 1")
        
        if not vehicles or not drivers:
            pytest.skip("No vehicles or drivers available")
        
        vehicle_id = vehicles[0]['vehicle_id']
        driver_id = drivers[0]['driver_id']
        user_id = 9999  # Test user ID
        
        # Step 1: Assign vehicle
        result = await assign_vehicle(test_trip_id, vehicle_id, driver_id, user_id)
        
        assert result["ok"] is True
        assert result["trip_id"] == test_trip_id
        assert result["vehicle_id"] == vehicle_id
        assert result["driver_id"] == driver_id
        assert "deployment_id" in result
        
        # Verify deployment was created
        consequences = await get_trip_consequences(test_trip_id)
        assert consequences["has_deployment"] is True
        assert consequences["vehicle_id"] == vehicle_id
        
        # Step 2: Try to assign again (should fail)
        with pytest.raises(ServiceError, match="already has a deployment"):
            await assign_vehicle(test_trip_id, vehicle_id, driver_id, user_id)
        
        # Step 3: Remove vehicle
        result2 = await remove_vehicle(test_trip_id, user_id, cancel_bookings=True)
        
        assert result2["ok"] is True
        assert result2["trip_id"] == test_trip_id
        assert result2["vehicle_id"] == vehicle_id
        
        # Verify deployment was removed
        consequences2 = await get_trip_consequences(test_trip_id)
        assert consequences2["has_deployment"] is False
        assert consequences2["vehicle_id"] is None
        
    finally:
        # Cleanup: Delete test trip
        await execute("DELETE FROM daily_trips WHERE trip_id=$1", test_trip_id)


@pytest.mark.asyncio
async def test_remove_vehicle_without_deployment():
    """Test that removing vehicle from trip without deployment raises error."""
    # Create a trip without deployment
    async with transaction() as conn:
        route = await conn.fetchrow("SELECT route_id FROM routes LIMIT 1")
        if not route:
            pytest.skip("No routes available")
        
        test_trip = await conn.fetchrow(
            """
            INSERT INTO daily_trips (route_id, trip_date, live_status, display_name)
            VALUES ($1, '2025-11-21', 'SCHEDULED', 'Test Trip - No Deployment')
            RETURNING trip_id
            """,
            route['route_id']
        )
        
        test_trip_id = test_trip['trip_id']
    
    try:
        # Try to remove vehicle (should fail - no deployment)
        with pytest.raises(ServiceError, match="No deployment found"):
            await remove_vehicle(test_trip_id, user_id=9999)
    finally:
        # Cleanup
        await execute("DELETE FROM daily_trips WHERE trip_id=$1", test_trip_id)


@pytest.mark.asyncio
async def test_cancel_trip():
    """Test trip cancellation."""
    # Create a test trip
    async with transaction() as conn:
        route = await conn.fetchrow("SELECT route_id FROM routes LIMIT 1")
        if not route:
            pytest.skip("No routes available")
        
        test_trip = await conn.fetchrow(
            """
            INSERT INTO daily_trips (route_id, trip_date, live_status, display_name)
            VALUES ($1, '2025-11-22', 'SCHEDULED', 'Test Trip - Cancel')
            RETURNING trip_id
            """,
            route['route_id']
        )
        
        test_trip_id = test_trip['trip_id']
    
    try:
        # Cancel the trip
        result = await cancel_trip(test_trip_id, user_id=9999)
        
        assert result["ok"] is True
        assert result["trip_id"] == test_trip_id
        assert "bookings_cancelled" in result
        
        # Verify trip is cancelled
        consequences = await get_trip_consequences(test_trip_id)
        assert consequences["live_status"] == "CANCELLED"
        
    finally:
        # Cleanup
        await execute("DELETE FROM daily_trips WHERE trip_id=$1", test_trip_id)


@pytest.mark.asyncio
async def test_cancel_trip_with_bookings():
    """Test that cancelling trip also cancels bookings."""
    # Create test trip with booking
    async with transaction() as conn:
        route = await conn.fetchrow("SELECT route_id FROM routes LIMIT 1")
        if not route:
            pytest.skip("No routes available")
        
        test_trip = await conn.fetchrow(
            """
            INSERT INTO daily_trips (route_id, trip_date, live_status, display_name)
            VALUES ($1, '2025-11-23', 'SCHEDULED', 'Test Trip - Bookings')
            RETURNING trip_id
            """,
            route['route_id']
        )
        
        test_trip_id = test_trip['trip_id']
        
        # Create a test booking (bookings only has trip_id, user_id, seats, status)
        await conn.execute(
            """
            INSERT INTO bookings (trip_id, user_id, user_name, seats, status)
            VALUES ($1, 1001, 'Test User', 2, 'CONFIRMED')
            """,
            test_trip_id
        )
    
    try:
        # Verify booking exists
        consequences_before = await get_trip_consequences(test_trip_id)
        assert consequences_before["booked_count"] > 0
        
        # Cancel trip
        result = await cancel_trip(test_trip_id, user_id=9999)
        
        assert result["bookings_cancelled"] > 0
        
        # Verify booking was cancelled
        bookings = await fetch(
            "SELECT status FROM bookings WHERE trip_id=$1",
            test_trip_id
        )
        assert all(b['status'] == 'CANCELLED' for b in bookings)
        
    finally:
        # Cleanup
        await execute("DELETE FROM bookings WHERE trip_id=$1", test_trip_id)
        await execute("DELETE FROM daily_trips WHERE trip_id=$1", test_trip_id)


# ============================================================================
# Audit Log Tests
# ============================================================================

@pytest.mark.asyncio
async def test_audit_log_creation():
    """Test that operations create audit logs."""
    from app.core.audit import get_recent_audits
    
    # Create and immediately assign/remove vehicle
    async with transaction() as conn:
        route = await conn.fetchrow("SELECT route_id FROM routes LIMIT 1")
        if not route:
            pytest.skip("No routes available")
        
        test_trip = await conn.fetchrow(
            """
            INSERT INTO daily_trips (route_id, trip_date, live_status, display_name)
            VALUES ($1, '2025-11-24', 'SCHEDULED', 'Test Trip - Audit')
            RETURNING trip_id
            """,
            route['route_id']
        )
        
        test_trip_id = test_trip['trip_id']
    
    try:
        vehicles = await fetch("SELECT vehicle_id FROM vehicles LIMIT 1")
        drivers = await fetch("SELECT driver_id FROM drivers LIMIT 1")
        
        if not vehicles or not drivers:
            pytest.skip("No vehicles or drivers available")
        
        # Perform operations that should create audit logs
        await assign_vehicle(test_trip_id, vehicles[0]['vehicle_id'], drivers[0]['driver_id'], 9999)
        await remove_vehicle(test_trip_id, 9999)
        
        # Check audit logs
        audits = await get_recent_audits("trip", test_trip_id, limit=10)
        
        assert len(audits) >= 2  # At least assign and remove
        
        actions = [a['action'] for a in audits]
        assert "assign_vehicle" in actions
        assert "remove_vehicle" in actions
        
    finally:
        # Cleanup
        await execute("DELETE FROM audit_logs WHERE entity_type='trip' AND entity_id=$1", test_trip_id)
        await execute("DELETE FROM daily_trips WHERE trip_id=$1", test_trip_id)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_trip_info():
    """Test get_trip_info convenience function."""
    trips = await fetch("SELECT trip_id FROM daily_trips LIMIT 1")
    if not trips:
        pytest.skip("No trips in database")
    
    trip_id = trips[0]['trip_id']
    
    info = await get_trip_info(trip_id)
    
    assert info is not None
    assert "trip_id" in info
    assert info["trip_id"] == trip_id
