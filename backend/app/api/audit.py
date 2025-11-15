# backend/app/api/audit.py
"""
Audit log endpoints for tracking system actions.
"""
from fastapi import APIRouter, HTTPException, status, Query
from app.core.supabase_client import get_conn
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/logs/{entity_type}/{entity_id}")
async def get_audit_logs(
    entity_type: str,
    entity_id: int,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of logs to return")
):
    """
    Get audit logs for a specific entity.
    
    Args:
        entity_type: Type of entity (e.g., "trip", "route", "booking")
        entity_id: ID of the entity
        limit: Maximum number of logs to return (1-100, default 20)
    
    Returns:
        List of audit log entries, most recent first
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    log_id,
                    action,
                    user_id,
                    entity_type,
                    entity_id,
                    details,
                    created_at
                FROM audit_logs
                WHERE entity_type = $1 AND entity_id = $2
                ORDER BY created_at DESC
                LIMIT $3
            """, entity_type, entity_id, limit)
        
        # Serialize datetime objects
        logs = []
        for row in rows:
            log = dict(row)
            if log.get('created_at'):
                log['created_at'] = log['created_at'].isoformat()
            logs.append(log)
        
        return {
            "logs": logs,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "count": len(logs)
        }
    
    except Exception as e:
        logger.error(f"Error fetching audit logs for {entity_type}/{entity_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit logs: {str(e)}"
        )


@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of logs to return"),
    action: Optional[str] = Query(None, description="Filter by action type")
):
    """
    Get recent audit logs across all entities.
    
    Args:
        limit: Maximum number of logs to return (1-200, default 50)
        action: Optional filter by action type (e.g., "assign_vehicle", "cancel_trip")
    
    Returns:
        List of recent audit log entries
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            if action:
                rows = await conn.fetch("""
                    SELECT 
                        log_id,
                        action,
                        user_id,
                        entity_type,
                        entity_id,
                        details,
                        created_at
                    FROM audit_logs
                    WHERE action = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, action, limit)
            else:
                rows = await conn.fetch("""
                    SELECT 
                        log_id,
                        action,
                        user_id,
                        entity_type,
                        entity_id,
                        details,
                        created_at
                    FROM audit_logs
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
        
        # Serialize datetime objects
        logs = []
        for row in rows:
            log = dict(row)
            if log.get('created_at'):
                log['created_at'] = log['created_at'].isoformat()
            logs.append(log)
        
        return {
            "logs": logs,
            "count": len(logs),
            "filter": {"action": action} if action else None
        }
    
    except Exception as e:
        logger.error(f"Error fetching recent audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent audit logs: {str(e)}"
        )


@router.get("/actions")
async def get_action_types():
    """
    Get distinct action types from audit logs.
    
    Returns:
        List of unique action types that have been logged
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT action
                FROM audit_logs
                ORDER BY action
            """)
        
        return {
            "actions": [row['action'] for row in rows],
            "count": len(rows)
        }
    
    except Exception as e:
        logger.error(f"Error fetching action types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch action types: {str(e)}"
        )
