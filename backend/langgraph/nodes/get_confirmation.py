"""
Get Confirmation Node
Handles confirmation workflow for high-impact actions
"""
from typing import Dict, Any
import logging
import json
from datetime import date, datetime
from app.core.supabase_client import get_conn

logger = logging.getLogger(__name__)


def json_serializable(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable format.
    Handles date, datetime, and other non-serializable types.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_serializable(item) for item in obj]
    return obj


async def get_confirmation(state: Dict) -> Dict:
    """
    Prepare the state for confirmation workflow.
    
    This node saves the pending action to the database and prepares
    the response for the user to confirm. The actual confirmation will
    be handled by the /api/agent/confirm endpoint.
    
    Args:
        state: Graph state
        
    Returns:
        Updated state with confirmation details and session_id
    """
    logger.info("Action requires confirmation - preparing confirmation state")
    
    state["status"] = "awaiting_confirmation"
    state["confirmation_required"] = True
    state["needs_confirmation"] = True  # Frontend checks this field
    
    # Store the pending action details - ensure all data is JSON serializable
    pending_action = json_serializable({
        "action": state.get("action"),
        "trip_id": state.get("trip_id"),
        "trip_label": state.get("trip_label"),
        "consequences": state.get("consequences", {}),
        "llm_parsed": {  # NEW: Store full LLM output
            "confidence": state.get("confidence", 0.0),
            "explanation": state.get("llm_explanation", ""),
            "target_label": state.get("target_label"),
        },
        "user_id": state.get("user_id"),
        "vehicle_id": state.get("vehicle_id"),
        "driver_id": state.get("driver_id"),
    })
    
    state["pending_action"] = pending_action
    
    # Save to database for confirmation flow
    try:
        logger.info(f"[DEBUG] About to save session to DB for user {state.get('user_id', 1)}")
        pool = await get_conn()
        async with pool.acquire() as conn:
            logger.info("[DEBUG] Got database connection")
            session = await conn.fetchrow("""
                INSERT INTO agent_sessions (user_id, pending_action, status)
                VALUES ($1, $2, 'PENDING')
                RETURNING session_id
            """, state.get("user_id", 1), json.dumps(pending_action))
            
            if session:
                session_id = str(session["session_id"])
                state["session_id"] = session_id
                logger.info(f"✅ Created confirmation session: {session_id}")
            else:
                logger.warning("[DEBUG] No session returned from INSERT")
                state["session_id"] = None
    except Exception as e:
        logger.error(f"❌ Failed to create confirmation session: {e}", exc_info=True)
        # Continue without session - confirmation will still work via state
        state["session_id"] = None
    
    return state
