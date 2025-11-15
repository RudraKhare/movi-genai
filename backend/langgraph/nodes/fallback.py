"""
Fallback Node
Handles errors and unknown states gracefully
"""
from typing import Dict
import logging

logger = logging.getLogger(__name__)


async def fallback(state: Dict) -> Dict:
    """
    Fallback handler for errors or unknown states.
    
    Args:
        state: Graph state
        
    Returns:
        State with friendly error message
    """
    logger.warning(f"Fallback triggered - state: {state.get('error')}")
    
    error = state.get("error", "unknown")
    action = state.get("action", "unknown")
    
    fallback_messages = {
        "trip_not_found": (
            "I couldn't find that trip. Please check the name and try again. "
            "Example: 'Remove vehicle from Bulk - 00:01'"
        ),
        "no_deployment": (
            "This trip doesn't have a vehicle assigned yet."
        ),
        "already_deployed": (
            "This trip already has a vehicle assigned. Remove it first if you want to reassign."
        ),
        "execution_failed": (
            "The action couldn't be completed. Please check the details and try again."
        ),
        "execution_error": (
            "An error occurred while processing your request. Please try again."
        ),
        "unknown": (
            "I'm not sure how to help with that. Try asking me to:\n"
            "- Remove vehicle from a trip\n"
            "- Cancel a trip\n"
            "- Assign vehicle to a trip"
        ),
    }
    
    message = fallback_messages.get(error, fallback_messages["unknown"])
    
    state["final_output"] = {
        "action": action,
        "status": "error",
        "success": False,
        "error": error,
        "message": message,
        "needs_confirmation": False,
    }
    
    return state
