# backend/app/core/audit.py
"""
Helper to write audit logs inside the same transaction.
"""
import json
from typing import Any, Dict, Optional
import asyncpg


async def record_audit(
    conn: asyncpg.Connection,
    action: str, 
    user_id: int, 
    entity_type: str, 
    entity_id: int, 
    details: Optional[Dict[str, Any]] = None
):
    """
    Record an audit log entry within a transaction.
    
    IMPORTANT: This function must be called with an active transaction connection
    to ensure atomicity. If the main operation fails, the audit log will be rolled back.
    
    Args:
        conn: Active asyncpg connection (usually from `async with transaction() as conn`)
        action: Action performed (e.g., "assign_vehicle", "cancel_trip", "remove_vehicle")
        user_id: ID of the user performing the action
        entity_type: Type of entity affected (e.g., "trip", "booking", "deployment")
        entity_id: ID of the affected entity
        details: Optional dictionary with additional context (will be stored as JSONB)
        
    Example:
        async with transaction() as conn:
            # Perform main operation
            await conn.execute("UPDATE trips SET status='CANCELLED' WHERE trip_id=$1", trip_id)
            
            # Record audit log in same transaction
            await record_audit(
                conn, 
                action="cancel_trip",
                user_id=admin_id,
                entity_type="trip",
                entity_id=trip_id,
                details={"reason": "weather_delay", "bookings_cancelled": 15}
            )
    """
    if conn is None:
        raise ValueError("record_audit requires an active connection from a transaction context")
    
    # Ensure details is serializable
    details_json = json.dumps(details or {})
    
    await conn.execute(
        """
        INSERT INTO audit_logs (action, user_id, entity_type, entity_id, details)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        """,
        action, user_id, entity_type, entity_id, details_json
    )


async def get_recent_audits(entity_type: str, entity_id: int, limit: int = 10):
    """
    Retrieve recent audit logs for a specific entity.
    
    Args:
        entity_type: Type of entity (e.g., "trip", "booking")
        entity_id: ID of the entity
        limit: Maximum number of logs to return (default 10)
        
    Returns:
        List of audit log dictionaries, most recent first
    """
    from .db import fetch
    
    query = """
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
    """
    
    return await fetch(query, entity_type, entity_id, limit)
