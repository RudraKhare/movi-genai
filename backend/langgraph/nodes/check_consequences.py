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
    "get_unassigned_vehicles", "get_trip_status", "get_trip_details",
    "list_all_stops", "list_stops_for_path", "list_routes_using_path",
    # Safe CREATE/UPDATE actions
    "create_stop", "create_path", "create_route", 
    "rename_stop", "duplicate_route",
    # Helper & special
    "create_new_route_help", "context_mismatch", "unknown"
]

RISKY_ACTIONS = [
    # Actions that affect live trips or passengers
    "remove_vehicle", "cancel_trip", "update_trip_time", "assign_vehicle"
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
    
    # RISKY ACTIONS: Need trip_id for analysis
    if not state.get("trip_id") or state.get("error"):
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
            
    elif action == "cancel_trip":
        if consequences["booking_count"] > 0:
            needs_confirmation = True
            warning_messages.append(
                f"⚠️ Cancelling will affect {consequences['booking_count']} passenger(s)"
            )
        if consequences["live_status"] == "in_transit":
            needs_confirmation = True
            warning_messages.append("⚠️ This trip is currently IN TRANSIT")
            
    elif action == "assign_vehicle":
        if consequences["has_deployment"]:
            state["error"] = "already_deployed"
            state["message"] = (
                f"This trip already has vehicle {trip_status.get('vehicle_id')} assigned. "
                "Remove it first or use a different command."
            )
            return state
    
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
