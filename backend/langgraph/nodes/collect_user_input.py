"""
Collect User Input Node
Handles user responses during wizard or option selection.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def _get_wizard_field_for_step(wizard_type: str, step: int) -> str:
    """Get the wizard field name for a given wizard type and step index."""
    # Define wizard steps for each type (must match trip_creation_wizard.py)
    # STOP_WIZARD_STEPS: stop_name (0) → confirmed (1)
    # PATH_WIZARD_STEPS: path_name (0) → stop_ids (1) → confirmed (2)
    # ROUTE_WIZARD_STEPS: route_name (0) → path_id (1) → departure_time (2) → direction (3) → confirmed (4)
    WIZARD_FIELDS = {
        "create_stop": ["stop_name", "confirmed"],
        "create_path": ["path_name", "stop_ids", "confirmed"],
        "create_route": ["route_name", "path_id", "departure_time", "direction", "confirmed"],
    }
    
    fields = WIZARD_FIELDS.get(wizard_type, [])
    if step < len(fields):
        return fields[step]
    return "confirmed"  # Default to confirmed for final steps


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
    wizard_type = state.get("wizard_type")
    
    # If wizard_field is not in state, derive it from wizard_type and step
    if wizard_field is None and wizard_type:
        wizard_field = _get_wizard_field_for_step(wizard_type, current_step)
        logger.info(f"Derived wizard_field '{wizard_field}' from type={wizard_type}, step={current_step}")
    
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
    """Handle user selecting an option from suggestions or specific selections"""
    
    # Check if this is a specific selection (vehicle, driver, etc.)
    selection_type = state.get("selection_type")
    
    if selection_type == "driver":
        return await _handle_driver_selection(state, user_input)
    elif selection_type == "vehicle":
        return await _handle_vehicle_selection(state, user_input)
    
    # Default: handle suggestion selection
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


async def _handle_driver_selection(state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """Handle user selecting a driver from the options list"""
    
    options = state.get("options", [])
    selected_driver = None
    
    logger.info(f"Driver selection from {len(options)} options: '{user_input}'")
    
    # Parse user input for driver selection
    import re
    
    # Match by number (e.g., "1", "Choose 2", "Select driver 3")
    number_match = re.search(r'\b(\d+)\b', user_input)
    if number_match:
        idx = int(number_match.group(1)) - 1
        if 0 <= idx < len(options):
            selected_driver = options[idx]
            logger.info(f"Selected driver by number {idx+1}: {selected_driver['driver_name']}")
    
    # Match by name (e.g., "Amit", "Choose Amit", "Assign driver Amit")
    if not selected_driver:
        user_lower = user_input.lower()
        # Extract potential name from user input by removing common action words
        potential_name = user_lower
        for word in ["assign", "choose", "select", "pick", "driver", "the"]:
            potential_name = potential_name.replace(word, "").strip()
        
        for option in options:
            driver_name = option["driver_name"].lower()
            first_name = driver_name.split()[0] if driver_name.split() else driver_name
            
            # Check if any part of the driver name matches the user input
            if (driver_name in user_lower or 
                first_name in user_lower or 
                potential_name in driver_name or
                first_name in potential_name):
                selected_driver = option
                logger.info(f"Selected driver by name: {selected_driver['driver_name']}")
                break
    
    if selected_driver:
        # Set driver information in state
        state["driver_id"] = selected_driver["driver_id"]
        state["driver_name"] = selected_driver["driver_name"]
        state["selectedEntityId"] = selected_driver["driver_id"]
        state["entityName"] = selected_driver["driver_name"]
        
        # Clear selection state
        state["awaiting_selection"] = False
        state["selection_type"] = None
        state["needs_clarification"] = False
        
        # Route to check consequences for assignment
        state["action"] = "assign_driver"
        state["next_node"] = "check_consequences"
        
        logger.info(f"Driver selected: {selected_driver['driver_name']} (ID: {selected_driver['driver_id']})")
        
        return state
    else:
        # Could not match selection
        logger.warning(f"Could not match driver selection: '{user_input}'")
        state["message"] = "I couldn't find that driver. Please choose by number (e.g., '1') or name (e.g., 'Amit')."
        state["next_node"] = "report_result"
        return state


async def _handle_vehicle_selection(state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """Handle user selecting a vehicle from the options list"""
    
    options = state.get("options", [])
    selected_vehicle = None
    
    logger.info(f"Vehicle selection from {len(options)} options: '{user_input}'")
    
    # Parse user input for vehicle selection
    import re
    
    # Match by number
    number_match = re.search(r'\b(\d+)\b', user_input)
    if number_match:
        idx = int(number_match.group(1)) - 1
        if 0 <= idx < len(options):
            selected_vehicle = options[idx]
    
    # Match by registration or name
    if not selected_vehicle:
        user_lower = user_input.lower()
        for option in options:
            if ("registration" in option and option["registration"].lower() in user_lower) or \
               ("vehicle_name" in option and option["vehicle_name"].lower() in user_lower):
                selected_vehicle = option
                break
    
    if selected_vehicle:
        # Set vehicle information in state
        state["vehicle_id"] = selected_vehicle.get("vehicle_id")
        state["registration"] = selected_vehicle.get("registration")
        
        # Clear selection state
        state["awaiting_selection"] = False
        state["selection_type"] = None
        state["needs_clarification"] = False
        
        # Route to check consequences for assignment
        state["action"] = "assign_vehicle"
        state["next_node"] = "check_consequences"
        
        return state
    else:
        state["message"] = "I couldn't find that vehicle. Please choose by number or registration."
        state["next_node"] = "report_result"
        return state


async def _validate_wizard_input(state: Dict[str, Any], field: str, value: str) -> Dict[str, Any]:
    """
    Validate wizard input based on field type.
    Returns: {"valid": bool, "value": any, "error": str}
    """
    
    # Time validation (HH:MM)
    if field in ["scheduled_time", "trip_time", "departure_time"]:
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
        if value.lower() in ["up", "down"]:
            return {"valid": True, "value": value.lower()}  # Database expects lowercase
        else:
            return {"valid": False, "error": "Direction must be UP or DOWN"}
    
    # Path ID validation - accepts name OR ID
    if field == "path_id":
        # First try as number
        try:
            int_value = int(value)
            return {"valid": True, "value": int_value}
        except ValueError:
            # Try to resolve by name
            from app.core.service import list_all_paths
            all_paths = await list_all_paths()
            for path in all_paths:
                if path.get("path_name", "").lower() == value.lower():
                    logger.info(f"Resolved path name '{value}' to path_id={path['path_id']}")
                    return {"valid": True, "value": path["path_id"]}
            # No match found
            path_names = [p.get("path_name", "") for p in all_paths[:5]]
            return {"valid": False, "error": f"Path '{value}' not found. Available paths: {', '.join(path_names)}..."}
    
    # ID validation (numeric) - for other _id fields
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
    
    # Stop IDs (comma-separated) - accepts names OR IDs
    if field == "stop_ids":
        # Check if all are numbers (IDs)
        parts = [x.strip() for x in value.split(",") if x.strip()]
        try:
            ids = [int(x) for x in parts]
            return {"valid": True, "value": ids}
        except ValueError:
            # Treat as stop names - return as-is for wizard to resolve
            return {"valid": True, "value": parts}
    
    # Default: accept any non-empty string
    if value:
        return {"valid": True, "value": value}
    else:
        return {"valid": False, "error": "This field cannot be empty"}
