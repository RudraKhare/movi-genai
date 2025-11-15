"""
Parse Intent Node
Extracts user intent and action type from natural language input
"""
import re
from typing import Dict
import logging

logger = logging.getLogger(__name__)


async def parse_intent(state: Dict) -> Dict:
    """
    Parse the user's text input to identify the intended action.
    
    Supports:
    - Remove vehicle: "remove vehicle from...", "unassign...", "clear deployment..."
    - Cancel trip: "cancel...", "abort...", "stop trip..."
    - Assign vehicle: "assign...", "deploy...", "add vehicle..."
    
    Args:
        state: Graph state with 'text' field, optionally 'selectedTripId'
        
    Returns:
        Updated state with 'action' and extracted parameters
    """
    text = state.get("text", "").lower().strip()
    selected_trip_id = state.get("selectedTripId")
    
    if not text:
        state["action"] = "unknown"
        state["error"] = "No input text provided"
        return state
    
    logger.info(f"Parsing intent from: {text}")
    if selected_trip_id:
        logger.info(f"[OCR] selectedTripId provided: {selected_trip_id}")
    
    # Remove vehicle patterns
    remove_patterns = [
        r"remove\s+vehicle",
        r"unassign\s+vehicle",
        r"clear\s+deployment",
        r"remove\s+deployment",
        r"unassign",
    ]
    
    # Cancel trip patterns
    cancel_patterns = [
        r"cancel\s+trip",
        r"cancel\s+bulk",
        r"abort\s+trip",
        r"stop\s+trip",
        r"cancel",
    ]
    
    # Assign vehicle patterns
    assign_patterns = [
        r"assign\s+vehicle",
        r"deploy\s+vehicle",
        r"add\s+vehicle",
        r"assign\s+bus",
    ]
    
    # Check patterns in order of specificity
    action = "unknown"
    
    for pattern in remove_patterns:
        if re.search(pattern, text):
            action = "remove_vehicle"
            break
    
    if action == "unknown":
        for pattern in cancel_patterns:
            if re.search(pattern, text):
                action = "cancel_trip"
                break
    
    if action == "unknown":
        for pattern in assign_patterns:
            if re.search(pattern, text):
                action = "assign_vehicle"
                break
    
    state["action"] = action
    
    if action == "unknown":
        state["message"] = (
            "I didn't understand that request. Try:\n"
            "- 'Remove vehicle from Bulk - 00:01'\n"
            "- 'Cancel trip Bulk - 00:01'\n"
            "- 'Assign vehicle to Bulk - 00:01'"
        )
        state["needs_clarification"] = True
    else:
        logger.info(f"Identified action: {action}")
    
    return state
