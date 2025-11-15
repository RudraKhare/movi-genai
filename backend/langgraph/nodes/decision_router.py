"""
Decision Router Node
Routes conversation flow based on intent, resolution status, and context.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def decision_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route the conversation flow based on:
    - Whether trip/entity was resolved
    - Whether request came from image
    - What action was detected
    - Current page context
    
    Routing Logic:
    A) Trip found + from_image → suggestion_provider
    B) Trip not found + from_image → create_trip_suggester
    C) Action = unknown + no target → fallback
    D) Static creation actions → trip_creation_wizard
    E) Dynamic actions → check_consequences → confirm → execute
    """
    
    action = state.get("action", "unknown")
    trip_id = state.get("trip_id")
    from_image = state.get("from_image", False)
    resolve_result = state.get("resolve_result", "none")  # found/multiple/none
    current_page = state.get("currentPage")
    
    logger.info(f"Decision Router - action: {action}, trip_id: {trip_id}, from_image: {from_image}, resolve_result: {resolve_result}")
    
    # A) Trip found from image → show suggestions
    if trip_id and from_image and resolve_result == "found":
        logger.info("Route A: Trip found from image → suggestion_provider")
        state["next_node"] = "suggestion_provider"
        state["message"] = f"I found this trip. What would you like to do?"
        return state
    
    # B) Trip not found but image provided → offer to create
    if from_image and resolve_result == "none" and not trip_id:
        logger.info("Route B: Trip not found from image → create_trip_suggester")
        state["next_node"] = "create_trip_suggester"
        return state
    
    # C) Multiple matches → need clarification (already handled in resolve_target)
    if resolve_result == "multiple":
        logger.info("Route C: Multiple matches → needs_clarification (already set)")
        state["next_node"] = "report_result"
        return state
    
    # D) Static creation actions → wizard
    creation_actions = [
        "create_stop",
        "create_path",
        "create_route",
        "create_trip_from_scratch",
        "create_new_route_help"
    ]
    
    if action in creation_actions:
        logger.info(f"Route D: Creation action '{action}' → trip_creation_wizard")
        state["next_node"] = "trip_creation_wizard"
        state["wizard_type"] = action
        return state
    
    # E) Unknown action with no target → fallback
    if action == "unknown" and not trip_id:
        logger.info("Route E: Unknown action, no target → fallback")
        state["next_node"] = "report_result"
        state["message"] = "I'm not sure what you want to do. Could you rephrase that?"
        state["status"] = "unknown"
        return state
    
    # F) Context mismatch → already handled
    if action == "context_mismatch":
        logger.info("Route F: Context mismatch → report_result")
        state["next_node"] = "report_result"
        return state
    
    # G) Assign vehicle without vehicle_id → show vehicle options
    parsed_params = state.get("parsed_params", {})
    if action == "assign_vehicle" and trip_id:
        vehicle_id = parsed_params.get("vehicle_id") or parsed_params.get("target_vehicle_id")
        # If no vehicle_id specified, show vehicle selection
        if not vehicle_id:
            logger.info("Route G: assign_vehicle missing vehicle_id → vehicle_selection_provider")
            state["next_node"] = "vehicle_selection_provider"
            return state
    
    # H) Normal dynamic actions → existing flow (consequences → confirm → execute)
    logger.info(f"Route H: Dynamic action '{action}' → check_consequences")
    state["next_node"] = "check_consequences"
    return state


def route_decision(state: Dict[str, Any]) -> str:
    """
    LangGraph conditional edge function.
    Returns the next node name based on decision_router output.
    """
    next_node = state.get("next_node", "report_result")
    logger.info(f"Routing to: {next_node}")
    return next_node
