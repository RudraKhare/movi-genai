"""
Resolve Target Node
Identifies the specific trip/route being referenced
"""
from typing import Dict
import logging
from langgraph.tools import tool_identify_trip_from_label

logger = logging.getLogger(__name__)


async def resolve_target(state: Dict) -> Dict:
    """
    Resolve which trip the user is referring to.
    
    PRIORITY ORDER:
    1. OCR selectedTripId (highest priority)
    2. LLM target_trip_id (numeric ID from LLM)
    3. LLM target_label (text label from LLM) ← PRIMARY PATH
    4. Regex fallback (only if LLM parsing is disabled)
    
    Args:
        state: Graph state with 'text' and 'action', optionally 'selectedTripId'
        
    Returns:
        Updated state with 'trip_id' and 'trip_label'
    """
    # Skip if action is unknown or already has error
    if state.get("action") == "unknown" or state.get("error"):
        return state
    
    # === PRIORITY 1: OCR selectedTripId ===
    # If selectedTripId is provided from OCR, use it directly
    selected_trip_id = state.get("selectedTripId")
    if selected_trip_id:
        logger.info(f"[BYPASS] Using OCR-resolved trip_id: {selected_trip_id}")
        
        # Fetch trip details from database
        from app.core.supabase_client import get_conn
        pool = await get_conn()
        async with pool.acquire() as conn:
            trip_row = await conn.fetchrow("""
                SELECT t.trip_id, t.display_name, t.trip_date, t.live_status
                FROM daily_trips t
                WHERE t.trip_id = $1
            """, selected_trip_id)
        
        if trip_row:
            state["trip_id"] = trip_row["trip_id"]
            state["trip_label"] = trip_row["display_name"]
            state["trip_date"] = str(trip_row.get("trip_date", ""))
            state["live_status"] = trip_row.get("live_status", "")
            logger.info(f"[BYPASS] Resolved to: {trip_row['display_name']} (ID: {trip_row['trip_id']})")
            return state
        else:
            logger.warning(f"[BYPASS] Trip ID {selected_trip_id} not found in database")
            state["status"] = "not_found"
            state["error"] = "trip_not_found"
            state["message"] = f"Trip ID {selected_trip_id} not found in system."
            return state
    
    # === PRIORITY 2: LLM numeric trip_id ===
    parsed_params = state.get("parsed_params", {})
    llm_trip_id = parsed_params.get("target_trip_id")
    
    if llm_trip_id:
        logger.info(f"[LLM_VERIFY] Checking LLM-suggested trip_id: {llm_trip_id}")
        
        # Verify with DB
        from app.core.supabase_client import get_conn
        pool = await get_conn()
        async with pool.acquire() as conn:
            trip_row = await conn.fetchrow("""
                SELECT t.trip_id, t.display_name, t.trip_date, t.live_status
                FROM daily_trips t
                WHERE t.trip_id = $1
            """, llm_trip_id)
        
        if trip_row:
            logger.info(f"[LLM_VERIFY] ✅ Trip exists: {trip_row['display_name']} (ID: {trip_row['trip_id']})")
            state["trip_id"] = trip_row["trip_id"]
            state["trip_label"] = trip_row["display_name"]
            state["trip_date"] = str(trip_row.get("trip_date", ""))
            state["live_status"] = trip_row.get("live_status", "")
            return state
        else:
            logger.warning(f"[LLM_VERIFY] ❌ Trip {llm_trip_id} does not exist. "
                          f"LLM hallucinated this ID. Falling back to label-based search.")
            # Don't return error, just fall through to label-based matching
    
    # === PRIORITY 3: LLM target_label (PRIMARY PATH) ===
    llm_target_label = state.get("target_label")
    
    if llm_target_label:
        logger.info(f"🤖 [LLM_LABEL] Using LLM-extracted label: '{llm_target_label}'")
        
        # Use the label directly - NO regex manipulation
        trip = await tool_identify_trip_from_label(llm_target_label)
        
        if trip:
            state["trip_id"] = trip["trip_id"]
            state["trip_label"] = trip["display_name"]
            state["trip_date"] = str(trip.get("trip_date", ""))
            state["live_status"] = trip.get("live_status", "")
            logger.info(f"✅ [LLM_LABEL] Resolved to trip_id: {trip['trip_id']} ({trip['display_name']})")
            return state
        else:
            # LLM provided label but DB lookup failed
            logger.warning(f"❌ [LLM_LABEL] Could not find trip with label: '{llm_target_label}'")
            confidence = state.get("confidence", 1.0)
            
            if confidence < 0.8:
                state["status"] = "needs_clarification"
                state["needs_clarification"] = True
                state["message"] = f"I'm not sure which trip you mean by '{llm_target_label}'. Could you please clarify?"
            else:
                state["status"] = "not_found"
                state["error"] = "trip_not_found"
                state["message"] = f"I couldn't find a trip matching '{llm_target_label}'. Please check the trip name and try again."
            
            logger.warning(f"Could not resolve trip from LLM label: {llm_target_label}")
            return state
    
    # === PRIORITY 4: Regex fallback (only if LLM parsing is disabled) ===
    # If we reach here, LLM didn't provide a target_label
    # This should only happen when USE_LLM_PARSE=false
    logger.info("⚠️  No LLM target_label provided, falling back to regex extraction")
    
    target_text = state.get("text", "")
    import re
    
    # Extract trip name from common patterns
    trip_label = target_text
    
    # Try: "from [trip_name]"
    from_match = re.search(r'\bfrom\s+(.+?)(?:\s+vehicle|\s+at|\s*$)', target_text, re.IGNORECASE)
    if from_match:
        trip_label = from_match.group(1).strip()
        logger.info(f"[REGEX] Extracted from 'from' pattern: '{trip_label}'")
    # Try: "cancel [trip_name]"
    elif re.search(r'\bcancel\s+', target_text, re.IGNORECASE):
        cancel_match = re.search(r'\bcancel\s+(?:trip\s+)?(?:the\s+)?(.+?)(?:\s+trip)?$', target_text, re.IGNORECASE)
        if cancel_match:
            trip_label = cancel_match.group(1).strip()
            logger.info(f"[REGEX] Extracted from 'cancel' pattern: '{trip_label}'")
    # Try: "trip [trip_name]" or "assign [trip_name]"
    elif re.search(r'\b(trip|to|assign)\s+', target_text, re.IGNORECASE):
        trip_match = re.search(r'\b(?:trip|to|assign)\s+(?:vehicle\s+)?(?:to\s+)?(.+?)$', target_text, re.IGNORECASE)
        if trip_match:
            trip_label = trip_match.group(1).strip()
            logger.info(f"[REGEX] Extracted from 'trip/to/assign' pattern: '{trip_label}'")
    
    # Try to find trip
    trip = await tool_identify_trip_from_label(trip_label)
    
    if trip:
        state["trip_id"] = trip["trip_id"]
        state["trip_label"] = trip["display_name"]
        state["trip_date"] = str(trip.get("trip_date", ""))
        state["live_status"] = trip.get("live_status", "")
        logger.info(f"[REGEX] Resolved to trip_id: {trip['trip_id']} ({trip['display_name']})")
    else:
        state["status"] = "not_found"
        state["error"] = "trip_not_found"
        state["message"] = f"I couldn't find a trip matching '{trip_label}'. Please check the trip name and try again."
        logger.warning(f"Could not resolve trip from: {target_text}")
    
    return state
