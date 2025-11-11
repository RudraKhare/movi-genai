# backend/app/routers/debug.py
"""
Debug endpoints for testing core functionality.
These endpoints are useful during development and should be disabled in production.
"""
from fastapi import APIRouter, HTTPException
from app.core.consequences import get_trip_consequences
from app.core.service import get_trip_info, ServiceError
from app.core.supabase_client import init_db_pool, get_conn
from app.core.audit import get_recent_audits

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/trip_status/{trip_id}")
async def debug_trip_status(trip_id: int):
    """
    Get detailed trip status including consequences.
    
    Returns comprehensive information about a trip:
    - Current deployment (vehicle, driver)
    - Booking statistics (count, seats booked)
    - Status flags (has_deployment, has_bookings)
    
    This endpoint is used by the LangGraph agent's check_consequences node.
    
    Args:
        trip_id: ID of the daily trip
        
    Returns:
        JSON with trip consequences
        
    Example:
        GET /api/debug/trip_status/1
        
        Response:
        {
            "trip_id": 1,
            "display_name": "Morning Shift - Gavipuram to Electronic City",
            "live_status": "SCHEDULED",
            "vehicle_id": 5,
            "driver_id": 3,
            "booked_count": 12,
            "seats_booked": 15,
            "has_deployment": true,
            "has_bookings": true
        }
    """
    # Ensure pool is initialized
    await init_db_pool()
    
    result = await get_trip_consequences(trip_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    
    return result


@router.get("/trip_info/{trip_id}")
async def debug_trip_info(trip_id: int):
    """
    Alias for trip_status endpoint (for backward compatibility).
    """
    return await debug_trip_status(trip_id)


@router.get("/audit/{entity_type}/{entity_id}")
async def debug_audit_logs(entity_type: str, entity_id: int, limit: int = 10):
    """
    Get recent audit logs for an entity.
    
    Args:
        entity_type: Type of entity (e.g., "trip", "booking", "deployment")
        entity_id: ID of the entity
        limit: Maximum number of logs to return (default 10)
        
    Returns:
        List of audit log entries, most recent first
        
    Example:
        GET /api/debug/audit/trip/1?limit=5
        
        Response:
        [
            {
                "log_id": 42,
                "action": "assign_vehicle",
                "user_id": 999,
                "entity_type": "trip",
                "entity_id": 1,
                "details": {"vehicle_id": 5, "driver_id": 3},
                "logged_at": "2025-11-11T10:30:00Z"
            },
            ...
        ]
    """
    await init_db_pool()
    
    logs = await get_recent_audits(entity_type, entity_id, limit)
    
    if not logs:
        return []
    
    # Convert datetime objects to ISO strings for JSON serialization
    for log in logs:
        if log.get('created_at'):
            log['created_at'] = log['created_at'].isoformat()
    
    return logs


@router.get("/pool_status")
async def debug_pool_status():
    """
    Get connection pool statistics.
    
    Returns:
        JSON with pool size, free connections, etc.
    """
    pool = await get_conn()
    
    return {
        "pool_size": pool.get_size(),
        "pool_max_size": pool.get_max_size(),
        "pool_min_size": pool.get_min_size(),
        "free_connections": pool.get_size() - pool.get_idle_size(),
        "idle_connections": pool.get_idle_size(),
    }


@router.get("/health")
async def debug_health():
    """
    Health check endpoint for database connectivity.
    
    Returns:
        JSON with status and database connection info
    """
    try:
        await init_db_pool()
        pool = await get_conn()
        
        # Test a simple query
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            
        return {
            "status": "healthy",
            "database": "connected",
            "pool_size": pool.get_size(),
            "test_query": result == 1
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Database connection failed: {str(e)}"
        )
