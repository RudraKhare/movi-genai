"""
Collect User Input Node
Handles user responses during wizard or option selection.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def collect_user_input(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collects and validates user input during:
    - Wizard steps
    - Option selections
    - Clarification requests
    
    Routes to:
    - Next wizard step (if wizard active)
    - Execute action (if option selected)
    - Clarification (if invalid input)
    """
    
    user_input = state.get("user_message", "").strip()
    wizard_active = state.get("wizard_active", False)
    awaiting_selection = state.get("awaiting_user_selection", False)
    
    logger.info(f"Collecting input: '{user_input}', wizard={wizard_active}, awaiting={awaiting_selection}")
    
    # Handle wizard input
    if wizard_active:
        return await _handle_wizard_input(state, user_input)
    
    # Handle option selection
    if awaiting_selection:
        return await _handle_option_selection(state, user_input)
    
    # Fallback: treat as new command
    logger.warning("collect_user_input called but no wizard/selection active")
    state["next_node"] = "parse_intent_llm"
    return state


async def _handle_wizard_input(state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """Handle user input during wizard flow"""
    
    wizard_field = state.get("wizard_field")
    wizard_data = state.get("wizard_data", {})
    current_step = state.get("wizard_step", 0)
    
    logger.info(f"Wizard input for field '{wizard_field}': {user_input}")
    
    # Check for cancel
    if user_input.lower() in ["cancel", "abort", "stop", "quit"]:
        logger.info("User cancelled wizard")
        state["message"] = "❌ Wizard cancelled."
        state["wizard_active"] = False
        state["status"] = "cancelled"
        state["next_node"] = "report_result"
        return state
    
    # Check for confirm (final step)
    if wizard_field == "confirmed":
        if user_input.lower() in ["confirm", "yes", "y", "ok"]:
            logger.info("User confirmed wizard completion")
            state["wizard_step"] = current_step + 1  # Trigger execution
            state["next_node"] = "trip_creation_wizard"
            return state
        else:
            state["message"] = "Please reply with 'confirm' to proceed or 'cancel' to abort."
            state["next_node"] = "report_result"
            return state
    
    # Validate and store input
    validation_result = await _validate_wizard_input(state, wizard_field, user_input)
    
    if validation_result.get("valid"):
        # Store the input
        wizard_data[wizard_field] = validation_result.get("value", user_input)
        state["wizard_data"] = wizard_data
        state["wizard_step"] = current_step + 1  # Move to next step
        
        logger.info(f"Stored {wizard_field}={user_input}, moving to step {current_step + 1}")
        
        # Continue wizard
        state["next_node"] = "trip_creation_wizard"
    else:
        # Invalid input, ask again
        error_msg = validation_result.get("error", "Invalid input")
        state["message"] = f"❌ {error_msg}\n\nPlease try again:"
        state["next_node"] = "report_result"
    
    return state


async def _handle_option_selection(state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """Handle user selecting an option from suggestions"""
    
    suggestions = state.get("suggestions", [])
    
    logger.info(f"Option selection from {len(suggestions)} options")
    
    # Try to match user input to an option
    selected_action = None
    
    # Match by number (1, 2, 3...)
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(suggestions):
            selected_action = suggestions[idx]
    
    # Match by action name
    for suggestion in suggestions:
        if user_input.lower() in suggestion["action"].lower():
            selected_action = suggestion
            break
        if user_input.lower() in suggestion["label"].lower():
            selected_action = suggestion
            break
    
    if selected_action:
        action = selected_action["action"]
        logger.info(f"User selected action: {action}")
        
        # Handle special actions
        if action == "start_trip_wizard":
            state["wizard_type"] = "start_trip_wizard"
            state["wizard_step"] = 0
            state["wizard_data"] = state.get("extracted_info", {})
            state["next_node"] = "trip_creation_wizard"
            return state
        
        if action == "cancel_wizard":
            state["message"] = "❌ Cancelled."
            state["status"] = "cancelled"
            state["awaiting_user_selection"] = False
            state["next_node"] = "report_result"
            return state
        
        # Normal action: set action and re-route through decision router
        state["action"] = action
        state["awaiting_user_selection"] = False
        state["next_node"] = "decision_router"
        return state
    
    else:
        # Couldn't match input
        logger.warning(f"Could not match selection: {user_input}")
        state["message"] = "I didn't understand that selection. Please choose by number or name."
        state["next_node"] = "report_result"
        return state


async def _validate_wizard_input(state: Dict[str, Any], field: str, value: str) -> Dict[str, Any]:
    """
    Validate wizard input based on field type.
    Returns: {"valid": bool, "value": any, "error": str}
    """
    
    # Time validation (HH:MM)
    if field in ["scheduled_time", "trip_time"]:
        import re
        if re.match(r'^\d{1,2}:\d{2}$', value):
            return {"valid": True, "value": value}
        else:
            return {"valid": False, "error": "Time must be in HH:MM format (e.g., 08:30)"}
    
    # Date validation (YYYY-MM-DD)
    if field in ["trip_date"]:
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            return {"valid": True, "value": value}
        else:
            return {"valid": False, "error": "Date must be in YYYY-MM-DD format (e.g., 2025-11-15)"}
    
    # Direction validation
    if field == "direction":
        if value.upper() in ["UP", "DOWN"]:
            return {"valid": True, "value": value.upper()}
        else:
            return {"valid": False, "error": "Direction must be UP or DOWN"}
    
    # ID validation (numeric)
    if field.endswith("_id"):
        try:
            int_value = int(value)
            return {"valid": True, "value": int_value}
        except ValueError:
            return {"valid": False, "error": f"{field} must be a number"}
    
    # Coordinates validation
    if field in ["latitude", "longitude"]:
        if not value or value.lower() in ["skip", "none", ""]:
            return {"valid": True, "value": None}
        try:
            float_value = float(value)
            return {"valid": True, "value": float_value}
        except ValueError:
            return {"valid": False, "error": f"{field} must be a number or 'skip'"}
    
    # Stop IDs (comma-separated)
    if field == "stop_ids":
        try:
            # Try to parse as comma-separated IDs
            ids = [int(x.strip()) for x in value.split(",")]
            return {"valid": True, "value": ids}
        except ValueError:
            return {"valid": False, "error": "Stop IDs must be comma-separated numbers (e.g., 1,2,3)"}
    
    # Default: accept any non-empty string
    if value:
        return {"valid": True, "value": value}
    else:
        return {"valid": False, "error": "This field cannot be empty"}
