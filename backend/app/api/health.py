# backend/app/api/health.py
"""
Health check and system status endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from app.models import HealthStatus
from app.core.supabase_client import get_conn
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status", response_model=HealthStatus)
async def health_status():
    """
    Check system health status.
    
    Verifies:
    - Database connectivity
    - Connection pool status
    - Basic query execution
    
    Returns:
        Health status with database connection info
    """
    try:
        pool = await get_conn()
        
        # Test database connectivity with a simple query
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
        
        # Get pool statistics
        pool_size = pool.get_size()
        
        if result == 1:
            return HealthStatus(
                status="healthy",
                database="connected",
                pool_size=pool_size,
                timestamp=datetime.utcnow().isoformat()
            )
        else:
            return HealthStatus(
                status="degraded",
                database="unexpected_response",
                pool_size=pool_size,
                timestamp=datetime.utcnow().isoformat()
            )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthStatus(
            status="unhealthy",
            database=f"error: {str(e)}",
            timestamp=datetime.utcnow().isoformat()
        )


@router.get("/database")
async def database_status():
    """
    Get detailed database status information.
    
    Returns:
    - Connection pool statistics
    - Database version
    - Schema information
    """
    try:
        pool = await get_conn()
        
        async with pool.acquire() as conn:
            # Get PostgreSQL version
            pg_version = await conn.fetchval("SELECT version()")
            
            # Get table count
            table_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            
            # Get total row counts (quick estimate)
            row_counts = {}
            tables = ['stops', 'paths', 'routes', 'vehicles', 'drivers', 
                     'daily_trips', 'deployments', 'bookings', 'audit_logs']
            
            for table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                row_counts[table] = count
        
        return {
            "status": "connected",
            "pool": {
                "size": pool.get_size(),
                "max_size": pool.get_max_size(),
                "min_size": pool.get_min_size(),
                "idle": pool.get_idle_size()
            },
            "database": {
                "version": pg_version.split()[0:2],  # Just "PostgreSQL 15.x"
                "table_count": table_count,
                "row_counts": row_counts
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Database status check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database status: {str(e)}"
        )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for liveness checks.
    
    Returns:
        Simple pong response
    """
    return {"ping": "pong", "timestamp": datetime.utcnow().isoformat()}
