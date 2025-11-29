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
    
    # Get parsed params (from LLM parsing)
    parsed_params = state.get("parsed_params", {})
    target_label = state.get("target_label")  # Fallback for entity names
    action = state.get("action")
    
    # Determine entity names with target_label as fallback
    stop_name = parsed_params.get("stop_name") or parsed_params.get("stop_id")
    path_name = parsed_params.get("path_name") or parsed_params.get("path_id")
    route_name = parsed_params.get("route_name") or parsed_params.get("route_id")
    
    # Use target_label as fallback for the appropriate entity type
    if target_label:
        if action == "delete_stop" and not stop_name:
            stop_name = target_label
        elif action == "delete_path" and not path_name:
            path_name = target_label
        elif action == "delete_route" and not route_name:
            route_name = target_label
    
    # Store the pending action details - ensure all data is JSON serializable
    pending_action = json_serializable({
        "action": action,
        "trip_id": state.get("trip_id"),
        "trip_label": state.get("trip_label"),
        "consequences": state.get("consequences", {}),
        "llm_parsed": {  # NEW: Store full LLM output
            "confidence": state.get("confidence", 0.0),
            "explanation": state.get("llm_explanation", ""),
            "target_label": target_label,
        },
        "user_id": state.get("user_id"),
        "vehicle_id": state.get("vehicle_id"),
        "driver_id": state.get("driver_id") or parsed_params.get("driver_id"),
        # Include params needed for confirmation execution
        "new_status": parsed_params.get("new_status"),
        "new_time": parsed_params.get("new_time"),
        "delay_minutes": parsed_params.get("delay_minutes"),
        "reason": parsed_params.get("reason"),
        # Entity-specific params for delete operations (with target_label fallback)
        "stop_name": stop_name,
        "path_name": path_name,
        "route_name": route_name,
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
