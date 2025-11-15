"""
Resolve Target Node
Identifies the specific trip/route/path being referenced
"""
from typing import Dict
import logging
from langgraph.tools import tool_identify_trip_from_label, tool_get_path_by_label, tool_get_route_by_label

logger = logging.getLogger(__name__)


async def resolve_target(state: Dict) -> Dict:
    """
    Resolve which trip/path/route the user is referring to.
    
    PRIORITY ORDER FOR TRIPS:
    1. OCR selectedTripId (highest priority)
    2. LLM target_trip_id (numeric ID from LLM)
    3. LLM target_time (time-based search)
    4. LLM target_label (text label from LLM) ← PRIMARY PATH
    5. Regex fallback (only if LLM parsing is disabled)
    
    PRIORITY ORDER FOR PATHS:
    1. LLM target_path_id (numeric)
    2. LLM target_label (text)
    
    PRIORITY ORDER FOR ROUTES:
    1. LLM target_route_id (numeric)
    2. LLM target_label (text)
    
    Args:
        state: Graph state with 'text' and 'action'
        
    Returns:
        Updated state with resolved IDs
    """
    # Skip if action is unknown or already has error
    if state.get("action") == "unknown" or state.get("error"):
        return state
    
    action = state.get("action", "")
    
    # === ACTIONS THAT DON'T NEED TARGET RESOLUTION ===
    no_target_actions = [
        "list_all_stops",
        "get_unassigned_vehicles",
        "create_new_route_help",
        "create_stop",
        "create_path",
        "create_route",
        "rename_stop",
        "context_mismatch",
        "unknown",
        # Phase 3: Wizard and suggestion actions
        "wizard_step_input",        # User input during wizard
        "show_trip_suggestions",    # Request suggestions
        "create_trip_from_scratch", # Start trip wizard
        "start_trip_wizard",        # Alias for create_trip_from_scratch
        "cancel_wizard",            # Cancel wizard
    ]
    if action in no_target_actions:
        logger.info(f"[SKIP] Action '{action}' doesn't need target resolution")
        # Mark as wizard-related if applicable
        if action in ["wizard_step_input", "start_trip_wizard", "create_trip_from_scratch"]:
            state["is_wizard_action"] = True
        return state
    
    # === DEFINE ACTION CATEGORIES ===
    trip_actions = [
        "cancel_trip", "remove_vehicle", "assign_vehicle", "update_trip_time",
        "get_trip_status", "get_trip_details",
        # Phase 3: Additional trip actions
        "get_trip_bookings", "change_driver", "duplicate_trip", "create_followup_trip"
    ]
    path_actions = [
        "list_stops_for_path", "list_routes_using_path"
    ]
    route_actions = [
        "duplicate_route"
    ]
    
    # === ROUTE TO APPROPRIATE RESOLUTION BASED ON ACTION TYPE ===
    
    # === PATH ACTIONS: Resolve path entity ===
    if action in path_actions:
        logger.info(f"[PATH] Resolving path for action: {action}")
        
        # Try numeric path_id first
        llm_path_id = state.get("target_path_id")
        if llm_path_id:
            logger.info(f"[PATH] Using LLM-provided path_id: {llm_path_id}")
            from app.core.supabase_client import get_conn
            pool = await get_conn()
            async with pool.acquire() as conn:
                path_row = await conn.fetchrow("""
                    SELECT path_id, path_name, created_at
                    FROM paths
                    WHERE path_id = $1
                """, llm_path_id)
            
            if path_row:
                state["path_id"] = path_row["path_id"]
                state["path_name"] = path_row["path_name"]
                logger.info(f"✅ [PATH] Resolved to: {path_row['path_name']}")
                return state
        
        # Try label-based search
        path_label = state.get("target_label")
        if path_label:
            logger.info(f"[PATH] Searching by label: '{path_label}'")
            path = await tool_get_path_by_label(path_label)
            if path:
                state["path_id"] = path["path_id"]
                state["path_name"] = path["path_name"]
                logger.info(f"✅ [PATH] Resolved to path_id: {path['path_id']}")
                return state
            else:
                state["status"] = "not_found"
                state["error"] = "path_not_found"
                state["message"] = f"I couldn't find a path matching '{path_label}'."
                return state
        
        # No path identifier provided
        state["error"] = "missing_path"
        state["message"] = "Please specify which path you're referring to."
        return state
    
    # === ROUTE ACTIONS: Resolve route entity ===
    if action in route_actions:
        logger.info(f"[ROUTE] Resolving route for action: {action}")
        
        # For duplicate_route: need existing route
        if action == "duplicate_route":
            llm_route_id = state.get("target_route_id")
            if llm_route_id:
                from app.core.supabase_client import get_conn
                pool = await get_conn()
                async with pool.acquire() as conn:
                    route_row = await conn.fetchrow("""
                        SELECT route_id, route_name, path_id
                        FROM routes
                        WHERE route_id = $1
                    """, llm_route_id)
                
                if route_row:
                    state["route_id"] = route_row["route_id"]
                    state["route_name"] = route_row["route_name"]
                    logger.info(f"✅ [ROUTE] Resolved to: {route_row['route_name']}")
                    return state
            
            # Try label-based search
            route_label = state.get("target_label")
            if route_label:
                route = await tool_get_route_by_label(route_label)
                if route:
                    state["route_id"] = route["route_id"]
                    state["route_name"] = route["route_name"]
                    logger.info(f"✅ [ROUTE] Resolved to route_id: {route['route_id']}")
                    return state
                else:
                    state["error"] = "route_not_found"
                    state["message"] = f"I couldn't find a route matching '{route_label}'."
                    return state
        
        # For create_route: need path (not route)
        if action == "create_route":
            path_label = state.get("target_label")
            if path_label:
                logger.info(f"[ROUTE/CREATE] Looking for path: '{path_label}'")
                path = await tool_get_path_by_label(path_label)
                if path:
                    state["path_id"] = path["path_id"]
                    state["path_name"] = path["path_name"]
                    logger.info(f"✅ [ROUTE/CREATE] Found path: {path['path_name']}")
                    return state
                else:
                    state["error"] = "path_not_found"
                    state["message"] = f"I couldn't find a path matching '{path_label}'."
                    return state
        
        state["error"] = "missing_route"
        state["message"] = "Please specify which route you're referring to."
        return state
    
    # === TRIP ACTIONS: Continue with trip resolution ===
    if action not in trip_actions:
        logger.warning(f"[UNKNOWN] Action '{action}' doesn't match any category")
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
            state["resolve_result"] = "found"  # Phase 3: Mark as successfully found
            logger.info(f"[BYPASS] Resolved to: {trip_row['display_name']} (ID: {trip_row['trip_id']})")
            return state
        else:
            logger.warning(f"[BYPASS] Trip ID {selected_trip_id} not found in database")
            state["status"] = "not_found"
            state["error"] = "trip_not_found"
            state["resolve_result"] = "none"  # Phase 3: Mark as not found
            state["message"] = f"Trip ID {selected_trip_id} not found in system."
            return state
    
    # === PRIORITY 2: LLM numeric trip_id ===
    llm_trip_id = state.get("target_trip_id")
    
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
            state["resolve_result"] = "found"  # Phase 3: Mark as successfully found
            return state
        else:
            logger.warning(f"[LLM_VERIFY] ❌ Trip {llm_trip_id} does not exist. "
                          f"LLM hallucinated this ID. Falling back to label-based search.")
            # Don't return error, just fall through to label-based matching
    
    # === PRIORITY 2.5: LLM target_time (time-based search) ===
    llm_target_time = state.get("target_time")
    
    if llm_target_time:
        logger.info(f"🕐 [LLM_TIME] Searching for trips at time: '{llm_target_time}'")
        
        from app.core.supabase_client import get_conn
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Search for trips with time in display_name (format: "Path-1 - 08:00")
            # Use LIKE pattern to match time in display_name
            time_pattern = f"%{llm_target_time}%"
            matching_trips = await conn.fetch("""
                SELECT t.trip_id, t.display_name, t.trip_date, t.live_status
                FROM daily_trips t
                WHERE t.display_name LIKE $1
                ORDER BY t.display_name
            """, time_pattern)
        
        if matching_trips:
            if len(matching_trips) == 1:
                # Exactly one match - resolve it
                trip = matching_trips[0]
                logger.info(f"✅ [LLM_TIME] Found unique trip: {trip['display_name']} (ID: {trip['trip_id']})")
                state["trip_id"] = trip["trip_id"]
                state["trip_label"] = trip["display_name"]
                state["trip_date"] = str(trip.get("trip_date", ""))
                state["live_status"] = trip.get("live_status", "")
                return state
            else:
                # Multiple matches - need clarification
                logger.warning(f"⚠️  [LLM_TIME] Found {len(matching_trips)} trips at {llm_target_time}")
                state["status"] = "needs_clarification"
                state["needs_clarification"] = True
                state["resolve_result"] = "multiple"  # Phase 3: Mark as multiple matches
                state["clarify_options"] = [
                    {
                        "trip_id": t["trip_id"],
                        "display_name": t["display_name"]
                    }
                    for t in matching_trips
                ]
                state["message"] = f"I found {len(matching_trips)} trips at {llm_target_time}. Which one did you mean?"
                return state
        else:
            logger.warning(f"❌ [LLM_TIME] No trips found at time: {llm_target_time}")
            # Fall through to label-based search
    
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
            state["resolve_result"] = "found"  # Phase 3: Mark as successfully found
            logger.info(f"✅ [LLM_LABEL] Resolved to trip_id: {trip['trip_id']} ({trip['display_name']})")
            return state
        else:
            # LLM provided label but DB lookup failed
            logger.warning(f"❌ [LLM_LABEL] Could not find trip with label: '{llm_target_label}'")
            confidence = state.get("confidence", 1.0)
            
            if confidence < 0.8:
                state["status"] = "needs_clarification"
                state["needs_clarification"] = True
                state["resolve_result"] = "none"  # Phase 3: Mark as not found
                state["message"] = f"I'm not sure which trip you mean by '{llm_target_label}'. Could you please clarify?"
            else:
                state["status"] = "not_found"
                state["error"] = "trip_not_found"
                state["resolve_result"] = "none"  # Phase 3: Mark as not found
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
        state["resolve_result"] = "found"  # Phase 3: Mark as successfully found
        logger.info(f"[REGEX] Resolved to trip_id: {trip['trip_id']} ({trip['display_name']})")
    else:
        state["status"] = "not_found"
        state["error"] = "trip_not_found"
        state["resolve_result"] = "none"  # Phase 3: Mark as not found
        state["message"] = f"I couldn't find a trip matching '{trip_label}'. Please check the trip name and try again."
        logger.warning(f"Could not resolve trip from: {target_text}")
    
    return state
