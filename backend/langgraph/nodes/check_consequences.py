"""
Check Consequences Node
Analyzes the impact of the requested action
"""
from typing import Dict
import logging
from langgraph.tools import tool_get_trip_status, tool_get_bookings

logger = logging.getLogger(__name__)

# Action categories
SAFE_ACTIONS = [
    # All READ actions (no side effects)
    "get_unassigned_vehicles", "get_available_drivers", "get_trip_status", "get_trip_details",
    "list_all_stops", "list_stops_for_path", "list_routes_using_path",
    "list_all_paths", "get_all_paths", "list_all_routes", "get_all_routes",
    "list_all_vehicles", "get_vehicles", "list_all_drivers", "get_drivers",
    # Dashboard Intelligence (read-only)
    "get_trips_needing_attention", "get_today_summary", "get_recent_changes",
    "get_high_demand_offices", "get_most_used_vehicles", "detect_overbooking",
    "predict_problem_trips", "check_trip_readiness",
    # Vehicle/Driver Status (read-only)
    "get_vehicle_status", "get_driver_status", "get_vehicle_trips_today",
    "get_driver_trips_today", "get_booking_count", "check_seat_availability",
    "get_trip_stops", "list_passengers",
    "find_employee_trips", "recommend_vehicle_for_trip", "suggest_alternate_vehicle",
    # Validation (read-only)
    "validate_route", "simulate_action", "explain_decision",
    # Safe CREATE/UPDATE actions
    "create_stop", "create_path", "create_route", 
    "rename_stop", "duplicate_route",
    # Safe assignment actions (driver assignment is generally safe)
    "assign_driver",
    # Compound assignment (assigns vehicle + driver in one go)
    "assign_vehicle_and_driver",
    # Safe fleet management (creating is safe)
    "add_vehicle", "add_driver",
    # Booking management (adding is safe, reducing is risky)
    "add_bookings",
    # Helper & special
    "create_new_route_help", "context_mismatch", "unknown"
]

RISKY_ACTIONS = [
    # Actions that affect live trips or passengers
    "remove_vehicle", "remove_driver", "cancel_trip", "update_trip_time", 
    "update_trip_status", "assign_vehicle", "cancel_all_bookings",
    # Booking changes that reduce capacity
    "reduce_bookings",
    # Trip scheduling changes
    "delay_trip", "reschedule_trip",
    # Vehicle/Driver blocking
    "block_vehicle", "unblock_vehicle", "set_driver_availability",
    # Destructive actions
    "delete_stop", "delete_path", "delete_route", "update_path_stops"
]


async def check_consequences(state: Dict) -> Dict:
    """
    Check what will be affected by the requested action.
    
    Safe actions bypass this check entirely.
    Risky actions get consequence analysis.
    
    Args:
        state: Graph state with 'action' and optionally 'trip_id'
        
    Returns:
        Updated state with 'consequences' and 'needs_confirmation'
    """
    action = state.get("action")
    
    # SAFE ACTIONS: Skip consequence check, execute instantly
    if action in SAFE_ACTIONS:
        state["needs_confirmation"] = False
        state["consequences"] = {"safe_action": True}
        logger.info(f"Action '{action}' is SAFE - skipping consequence check")
        return state
    
    # Handle non-trip-related risky actions (delete_stop, delete_path, delete_route)
    if action in ["delete_stop", "delete_path", "delete_route"]:
        return await _check_entity_consequences(state, action)
    
    # RISKY ACTIONS that need trip_id for analysis
    if not state.get("trip_id") or state.get("error"):
        # If no trip_id but it's a risky action, still require confirmation
        if action in RISKY_ACTIONS:
            state["needs_confirmation"] = True
            state["message"] = f"⚠️ You are about to perform '{action}'. This is a risky action.\n\n❓ Do you want to proceed?"
            state["consequences"] = {"action": action, "requires_confirmation": True}
            logger.info(f"RISKY action '{action}' without trip_id - requiring confirmation")
        return state
    
    trip_id = state["trip_id"]
    
    logger.info(f"Checking consequences for RISKY action '{action}' on trip {trip_id}")
    
    # Get trip details
    trip_status = await tool_get_trip_status(trip_id)
    bookings = await tool_get_bookings(trip_id)
    
    consequences = {
        "trip_status": trip_status,
        "booking_count": len(bookings),
        "booking_percentage": trip_status.get("booking_status_percentage", 0),
        "has_deployment": bool(trip_status.get("vehicle_id")),
        "live_status": trip_status.get("live_status", "unknown"),
    }
    
    state["consequences"] = consequences
    
    # Determine if confirmation is needed based on action and impact
    needs_confirmation = False
    warning_messages = []
    
    if action == "remove_vehicle":
        if consequences["booking_count"] > 0:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ This trip has {consequences['booking_count']} active booking(s) "
                f"({consequences['booking_percentage']}% capacity)"
            )
        if not consequences["has_deployment"]:
            state["error"] = "no_deployment"
            state["message"] = "This trip doesn't have a vehicle assigned."
            return state
    
    elif action == "remove_driver":
        # Check if trip has a driver assigned
        if not trip_status.get("driver_id"):
            state["error"] = "no_driver"
            state["message"] = "This trip doesn't have a driver assigned."
            return state
        if consequences["booking_count"] > 0:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ This trip has {consequences['booking_count']} active booking(s). "
                "Removing the driver may affect trip operations."
            )
        if consequences["live_status"] == "IN_PROGRESS":
            needs_confirmation = True
            warning_messages.append("⚠️ This trip is currently IN PROGRESS")
            
    elif action == "cancel_trip":
        # Always confirm trip cancellation - it's destructive
        needs_confirmation = True
        warning_messages.append(f"⚠️ You are about to CANCEL trip '{trip_status.get('display_name', trip_id)}'")
        
        if consequences["booking_count"] > 0:
            warning_messages.append(
                f"⚠️ This will affect {consequences['booking_count']} passenger(s)"
            )
        if consequences["has_deployment"]:
            warning_messages.append(
                f"⚠️ Vehicle {trip_status.get('vehicle_registration', 'assigned')} will be unassigned"
            )
        if consequences["live_status"] == "in_transit":
            warning_messages.append("⚠️ This trip is currently IN TRANSIT")
            
    elif action == "assign_vehicle":
        if consequences["has_deployment"]:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ This trip already has vehicle {trip_status.get('vehicle_id')} assigned. "
                "Proceeding will replace the current vehicle assignment."
            )
    
    elif action == "update_trip_time":
        if consequences["booking_count"] > 0:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ Changing time will affect {consequences['booking_count']} passenger(s)"
            )
        if consequences["live_status"] in ["IN_PROGRESS", "COMPLETED"]:
            state["error"] = "invalid_status"
            state["message"] = "Cannot update time for trips that are in progress or completed"
            return state
    
    elif action == "update_trip_status":
        parsed_params = state.get("parsed_params", {})
        new_status = parsed_params.get("new_status", "").upper()
        current_status = consequences.get("live_status", "SCHEDULED")
        
        # Warn about booking impact if cancelling
        if new_status == "CANCELLED" and consequences["booking_count"] > 0:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ Changing status to CANCELLED will affect {consequences['booking_count']} passenger(s)"
            )
        
        # Warn about status changes for in-progress trips
        if current_status == "IN_PROGRESS" and new_status != "COMPLETED":
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ This trip is currently IN_PROGRESS. Changing to {new_status} may affect operations."
            )
        
        # Always confirm status changes
        if not needs_confirmation:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ This will change trip status from {current_status} to {new_status}"
            )
    
    elif action == "cancel_all_bookings":
        if consequences["booking_count"] > 0:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ This will cancel ALL {consequences['booking_count']} booking(s) for this trip. "
                "Passengers will need to be notified."
            )
        else:
            state["message"] = "This trip has no bookings to cancel."
            return state
    
    elif action == "reduce_bookings":
        parsed_params = state.get("parsed_params", {})
        count_to_reduce = parsed_params.get("booking_count") or parsed_params.get("count") or 1
        try:
            count_to_reduce = int(count_to_reduce)
        except (ValueError, TypeError):
            count_to_reduce = 1
        
        if consequences["booking_count"] == 0:
            state["error"] = "no_bookings"
            state["message"] = "This trip has no bookings to reduce."
            return state
        
        if count_to_reduce > consequences["booking_count"]:
            state["error"] = "invalid_count"
            state["message"] = f"Cannot reduce by {count_to_reduce}. Trip only has {consequences['booking_count']} booking(s)."
            return state
        
        needs_confirmation = True
        warning_messages.append(
            f"⚠️ This will reduce {count_to_reduce} booking(s) from the trip. "
            f"Current bookings: {consequences['booking_count']}"
        )
    
    elif action == "delete_stop":
        # Always confirm stop deletion
        needs_confirmation = True
        parsed_params = state.get("parsed_params", {})
        stop_name = parsed_params.get("stop_name") or parsed_params.get("stop_names", ["unknown"])[0] if parsed_params.get("stop_names") else "unknown"
        warning_messages.append(f"⚠️ You are about to DELETE stop '{stop_name}'")
        warning_messages.append("⚠️ This may affect paths and routes using this stop")
    
    elif action == "delete_path":
        # Always confirm path deletion
        needs_confirmation = True
        parsed_params = state.get("parsed_params", {})
        path_name = parsed_params.get("path_name") or f"Path {parsed_params.get('path_id', 'unknown')}"
        warning_messages.append(f"⚠️ You are about to DELETE path '{path_name}'")
        warning_messages.append("⚠️ This may affect routes using this path")
    
    elif action == "delete_route":
        # Always confirm route deletion
        needs_confirmation = True
        parsed_params = state.get("parsed_params", {})
        route_name = parsed_params.get("route_name") or f"Route {parsed_params.get('route_id', 'unknown')}"
        warning_messages.append(f"⚠️ You are about to DELETE route '{route_name}'")
        warning_messages.append("⚠️ This will also delete associated trips and affect bookings")
    
    # Fallback: Any risky action not explicitly handled should still confirm
    elif action in RISKY_ACTIONS and not needs_confirmation:
        needs_confirmation = True
        warning_messages.append(f"⚠️ You are about to perform '{action}'")
        if trip_id:
            warning_messages.append(f"⚠️ This will affect trip {trip_id}")
    
    state["needs_confirmation"] = needs_confirmation
    
    if needs_confirmation:
        state["message"] = "\n".join(warning_messages) + "\n\n❓ Do you want to proceed?"
    else:
        state["message"] = "Action can be executed safely."
    
    # Attach LLM explanation if present
    if state.get("llm_explanation"):
        state["consequences"]["llm_explanation"] = state["llm_explanation"]
        logger.info(f"Attached LLM explanation: {state['llm_explanation']}")
    
    logger.info(
        f"Consequences checked - needs_confirmation: {needs_confirmation}, "
        f"bookings: {consequences['booking_count']}"
    )
    
    return state


async def _check_entity_consequences(state: Dict, action: str) -> Dict:
    """
    Check consequences for entity-based actions (delete_stop, delete_path, delete_route).
    These actions don't require a trip_id, so we handle them separately.
    
    This function queries the database to find ACTUAL dependencies before asking
    for confirmation, so the user knows exactly what will be affected.
    
    Args:
        state: Graph state with 'parsed_params'
        action: The action being performed
        
    Returns:
        Updated state with 'consequences', 'needs_confirmation', and 'message'
    """
    from app.core.supabase_client import get_conn
    from app.core.service import list_all_stops, list_all_paths, list_all_routes
    
    parsed_params = state.get("parsed_params", {})
    target_label = state.get("target_label")  # Fallback for entity names
    warning_messages = []
    dependent_entities = []
    entity_type = None
    can_force_delete = False
    
    pool = await get_conn()
    
    if action == "delete_stop":
        stop_name = parsed_params.get("stop_name") or parsed_params.get("stop_id") or target_label or "unknown"
        if isinstance(stop_name, list):
            stop_name = stop_name[0] if stop_name else "unknown"
        
        # Find the stop ID
        stops = await list_all_stops()
        stop_id = None
        for stop in stops:
            if stop.get("stop_name", "").lower() == str(stop_name).lower():
                stop_id = stop.get("stop_id")
                break
        
        if stop_id:
            # Check which paths use this stop
            async with pool.acquire() as conn:
                dependent_paths = await conn.fetch("""
                    SELECT DISTINCT p.path_id, p.path_name 
                    FROM path_stops ps
                    JOIN paths p ON ps.path_id = p.path_id
                    WHERE ps.stop_id = $1
                    ORDER BY p.path_name
                """, stop_id)
                
                if dependent_paths:
                    dependent_entities = [{"path_id": p['path_id'], "path_name": p['path_name']} for p in dependent_paths]
                    entity_type = "paths"
                    can_force_delete = True
                    path_names = ", ".join([p['path_name'] for p in dependent_paths])
                    warning_messages.append(f"⚠️ You are about to DELETE stop '{stop_name}'")
                    warning_messages.append(f"⚠️ This stop is used in {len(dependent_paths)} path(s): **{path_names}**")
                    warning_messages.append("⚠️ Force deleting will remove this stop from all paths")
                else:
                    warning_messages.append(f"⚠️ You are about to DELETE stop '{stop_name}'")
                    warning_messages.append("✅ This stop is not used in any paths - safe to delete")
        else:
            warning_messages.append(f"⚠️ Stop '{stop_name}' not found in database")
        
    elif action == "delete_path":
        path_name = parsed_params.get("path_name") or parsed_params.get("path_id") or target_label or "unknown"
        
        # Find the path ID
        paths = await list_all_paths()
        path_id = None
        for path in paths:
            if path.get("path_name", "").lower() == str(path_name).lower():
                path_id = path.get("path_id")
                break
        
        if path_id:
            # Check which routes use this path
            async with pool.acquire() as conn:
                dependent_routes = await conn.fetch("""
                    SELECT route_id, route_name 
                    FROM routes 
                    WHERE path_id = $1
                    ORDER BY route_name
                """, path_id)
                
                if dependent_routes:
                    dependent_entities = [{"route_id": r['route_id'], "route_name": r['route_name']} for r in dependent_routes]
                    entity_type = "routes"
                    can_force_delete = True
                    route_names = ", ".join([r['route_name'] for r in dependent_routes])
                    warning_messages.append(f"⚠️ You are about to DELETE path '{path_name}'")
                    warning_messages.append(f"⚠️ This path is used by {len(dependent_routes)} route(s): **{route_names}**")
                    warning_messages.append("⚠️ Force deleting will also delete these routes and their trips")
                else:
                    warning_messages.append(f"⚠️ You are about to DELETE path '{path_name}'")
                    warning_messages.append("✅ This path is not used by any routes - safe to delete")
        else:
            warning_messages.append(f"⚠️ Path '{path_name}' not found in database")
        
    elif action == "delete_route":
        route_name = parsed_params.get("route_name") or parsed_params.get("route_id") or target_label or "unknown"
        
        # Find the route ID
        routes = await list_all_routes()
        route_id = None
        for route in routes:
            if route.get("route_name", "").lower() == str(route_name).lower():
                route_id = route.get("route_id")
                break
        
        if route_id:
            # Check how many trips and bookings this route has
            async with pool.acquire() as conn:
                trip_info = await conn.fetchrow("""
                    SELECT 
                        COUNT(DISTINCT t.trip_id) as trip_count,
                        COALESCE(SUM(CASE WHEN b.status = 'CONFIRMED' THEN 1 ELSE 0 END), 0) as booking_count
                    FROM trips t
                    LEFT JOIN bookings b ON t.trip_id = b.trip_id
                    WHERE t.route_id = $1
                """, route_id)
                
                trip_count = trip_info['trip_count'] if trip_info else 0
                booking_count = trip_info['booking_count'] if trip_info else 0
                
                warning_messages.append(f"⚠️ You are about to DELETE route '{route_name}'")
                if trip_count > 0:
                    warning_messages.append(f"⚠️ This will delete {trip_count} trip(s)")
                    if booking_count > 0:
                        warning_messages.append(f"⚠️ This will affect {booking_count} active booking(s)")
                else:
                    warning_messages.append("✅ This route has no trips - safe to delete")
        else:
            warning_messages.append(f"⚠️ Route '{route_name}' not found in database")
    
    # All delete actions require confirmation
    state["needs_confirmation"] = True
    state["consequences"] = {
        "action": action,
        "entity_type": action.replace("delete_", ""),
        "requires_confirmation": True,
        "dependent_entities": dependent_entities,
        "dependency_type": entity_type,
        "can_force_delete": can_force_delete
    }
    
    # Build the confirmation message
    if can_force_delete:
        state["message"] = "\n".join(warning_messages) + "\n\n❓ Do you want to **force delete** anyway?"
    else:
        state["message"] = "\n".join(warning_messages) + "\n\n❓ Do you want to proceed?"
    
    logger.info(f"Entity action '{action}' requires confirmation. Dependencies: {len(dependent_entities)}")
    
    return state
