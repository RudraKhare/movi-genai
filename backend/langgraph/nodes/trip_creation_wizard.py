"""
Trip Creation Wizard Node
Multi-step guided flow for creating trips, routes, paths, and stops.
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class WizardStep:
    """Represents a single wizard step"""
    def __init__(self, step_id: str, question: str, field: str, options: List = None, validator=None):
        self.step_id = step_id
        self.question = question
        self.field = field
        self.options = options or []
        self.validator = validator


# Define wizard flows
TRIP_WIZARD_STEPS = [
    WizardStep("trip_name", "What should we call this trip?", "trip_name"),
    WizardStep("trip_date", "What date? (YYYY-MM-DD)", "trip_date"),
    WizardStep("trip_time", "What time? (HH:MM)", "scheduled_time"),
    WizardStep("select_route", "Which route should this trip use?", "route_id"),
    WizardStep("select_vehicle", "Which vehicle?", "vehicle_id"),
    WizardStep("select_driver", "Which driver?", "driver_id"),
    WizardStep("confirm_trip", "Review and confirm", "confirmed"),
]

ROUTE_WIZARD_STEPS = [
    WizardStep("route_name", "What should we call this route?", "route_name"),
    WizardStep("select_path", "Which path should this route follow? (Enter path name or ID)", "path_id"),
    WizardStep("departure_time", "What time should this route depart? (e.g., 08:00, 14:30)", "departure_time"),
    WizardStep("direction", "What direction? (UP/DOWN)", "direction"),
    WizardStep("confirm_route", "Review and confirm", "confirmed"),
]

PATH_WIZARD_STEPS = [
    WizardStep("path_name", "What should we call this path?", "path_name"),
    WizardStep("select_stops", "Select stops in order (comma-separated IDs or names)", "stop_ids"),
    WizardStep("confirm_path", "Review and confirm", "confirmed"),
]

STOP_WIZARD_STEPS = [
    WizardStep("stop_name", "What should we call this stop?", "stop_name"),
    # Latitude and longitude are optional - skip for now since maps aren't integrated
    # WizardStep("latitude", "Latitude? (optional)", "latitude"),
    # WizardStep("longitude", "Longitude? (optional)", "longitude"),
    WizardStep("confirm_stop", "Review and confirm", "confirmed"),
]


async def trip_creation_wizard(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multi-step wizard for creating trips, routes, paths, or stops.
    
    Manages wizard state:
    - wizard_type: trip/route/path/stop
    - wizard_step: current step index
    - wizard_data: collected data so far
    - wizard_steps: list of steps
    """
    
    wizard_type = state.get("wizard_type", "create_trip_from_scratch")
    wizard_data = state.get("wizard_data", {})
    current_step_idx = state.get("wizard_step", 0)
    
    logger.info(f"Wizard: type={wizard_type}, step={current_step_idx}, data={list(wizard_data.keys())}")
    logger.info(f"[DEBUG] State parsed_params: {state.get('parsed_params', {})}")
    logger.info(f"[DEBUG] State parameters: {state.get('parameters', {})}")
    logger.info(f"[DEBUG] State extracted_info: {state.get('extracted_info', {})}")
    
    # Determine which wizard flow
    if wizard_type in ["create_trip_from_scratch", "start_trip_wizard"]:
        steps = TRIP_WIZARD_STEPS
        wizard_name = "Trip Creation"
    elif wizard_type in ["create_route", "create_new_route_help"]:
        steps = ROUTE_WIZARD_STEPS
        wizard_name = "Route Creation"
    elif wizard_type == "create_path":
        steps = PATH_WIZARD_STEPS
        wizard_name = "Path Creation"
    elif wizard_type == "create_stop":
        steps = STOP_WIZARD_STEPS
        wizard_name = "Stop Creation"
    else:
        logger.error(f"Unknown wizard type: {wizard_type}")
        state["message"] = "Unknown wizard type"
        state["status"] = "error"
        state["next_node"] = "report_result"
        return state
    
    # FIX 1: Map LLM parsed_params to extracted_info for wizard pre-fill
    # The LLM stores parameters in "parsed_params", not "parameters"
    if current_step_idx == 0:
        parsed_params = state.get("parsed_params", {})
        if parsed_params and not state.get("extracted_info"):
            logger.info(f"[FIX] Mapping LLM parsed_params to extracted_info: {parsed_params}")
            state["extracted_info"] = parsed_params.copy()
    
    # Initialize wizard if first step
    if current_step_idx == 0 and not wizard_data:
        logger.info(f"Initializing {wizard_name} wizard")
        state["wizard_active"] = True
        state["wizard_name"] = wizard_name
        
        # Pre-fill with extracted info if available
        extracted_info = state.get("extracted_info", {})
        if extracted_info:
            wizard_data.update(extracted_info)
            logger.info(f"Pre-filled wizard with: {extracted_info}")
    
    # FIX 2: Skip wizard steps that already have data
    while current_step_idx < len(steps):
        current_step = steps[current_step_idx]
        field = current_step.field
        
        # Check if this field already has data
        has_data = field in wizard_data and wizard_data[field]
        
        # Special case: stop_ids can be satisfied by stop_names
        if not has_data and field == "stop_ids" and wizard_data.get("stop_names"):
            wizard_data["stop_ids"] = wizard_data["stop_names"]  # Copy stop_names to stop_ids
            has_data = True
            logger.info(f"[FIX] Mapped stop_names to stop_ids: {wizard_data['stop_ids']}")
        
        if has_data:
            logger.info(f"[FIX] Skipping step {current_step_idx} ({field}) - already filled with: {wizard_data[field]}")
            current_step_idx += 1
            state["wizard_step"] = current_step_idx
        else:
            break
    
    # Check if wizard completed
    if current_step_idx >= len(steps):
        logger.info("Wizard completed, executing creation")
        return await _execute_wizard_creation(state, wizard_type, wizard_data)
    
    # Get current step
    current_step = steps[current_step_idx]
    
    # Check if this step needs options from DB
    if current_step.step_id == "select_route":
        state["needs_db_options"] = "routes"
    elif current_step.step_id == "select_vehicle":
        state["needs_db_options"] = "vehicles"
    elif current_step.step_id == "select_driver":
        state["needs_db_options"] = "drivers"
    elif current_step.step_id == "select_path":
        state["needs_db_options"] = "paths"
    elif current_step.step_id == "select_stops":
        state["needs_db_options"] = "stops"
    
    # Build question message
    message = f"**{wizard_name}** (Step {current_step_idx + 1}/{len(steps)})\n\n"
    message += f"**{current_step.question}**"
    
    # Show collected data so far (only non-None, non-private values)
    if wizard_data:
        collected_items = [(k, v) for k, v in wizard_data.items() 
                          if not k.startswith("_") and v is not None and v != ""]
        if collected_items:
            message += "\n\n*Collected so far:*"
            for key, value in collected_items:
                # Use friendly display names
                display_name = key.replace("_", " ").title()
                message += f"\n• {display_name}: {value}"
    
    # Show confirmation summary if final step
    if current_step.step_id.startswith("confirm_"):
        message += "\n\n**Please review and confirm:**"
        message += "\n\nReply with **'confirm'** to create, or **'cancel'** to abort."
    
    state["message"] = message
    state["wizard_question"] = current_step.question
    state["wizard_field"] = current_step.field
    state["wizard_data"] = wizard_data
    state["wizard_step"] = current_step_idx
    state["wizard_steps_total"] = len(steps)
    state["awaiting_wizard_input"] = True
    state["status"] = "wizard_active"
    # IMPORTANT: Go to report_result to return response to user
    # The next user message will continue the wizard via parse_intent detecting wizard_active
    state["next_node"] = "report_result"
    
    logger.info(f"Wizard step {current_step_idx}: asking for {current_step.field}")
    
    return state


async def _execute_wizard_creation(state: Dict[str, Any], wizard_type: str, wizard_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the actual creation after wizard completion.
    Calls appropriate service layer function.
    """
    from app.core.service import (
        create_stop,
        create_path,
        create_route,
    )
    
    logger.info(f"Executing {wizard_type} with data: {wizard_data}")
    
    # Get user_id from state (default to 1 for agent operations)
    user_id = state.get("user_id", 1)
    
    try:
        if wizard_type in ["create_trip_from_scratch", "start_trip_wizard"]:
            # Trip creation not yet implemented via wizard
            state["message"] = "❌ Trip creation via wizard is not yet implemented. Please use the dashboard to create trips."
            state["status"] = "not_implemented"
            state["wizard_active"] = False
            return state
            
        elif wizard_type in ["create_route", "create_new_route_help"]:
            # Create route with shift_time and direction
            direction = wizard_data.get("direction", "up")
            if direction:
                direction = direction.lower()  # Database expects lowercase
            
            result = await create_route(
                route_name=wizard_data.get("route_name"),
                path_id=int(wizard_data.get("path_id")),
                user_id=user_id,
                shift_time=wizard_data.get("departure_time"),
                direction=direction
            )
            
            # Build success message
            msg_parts = [f"✅ Route created successfully!", "", f"**Route**: {wizard_data.get('route_name')}"]
            if wizard_data.get("departure_time"):
                msg_parts.append(f"**Departure Time**: {wizard_data.get('departure_time')}")
            msg_parts.append(f"**Direction**: {direction.upper() if direction else 'UP'}")
            
            # Include trip info if created
            if result.get("trip"):
                trip = result["trip"]
                msg_parts.append("")
                msg_parts.append(f"📅 **Daily trip created** for today (Trip ID: {trip.get('trip_id')})")
                msg_parts.append("You can now see it on the Dashboard and assign vehicles/drivers.")
            
            state["message"] = "\n".join(msg_parts)
            
        elif wizard_type == "create_path":
            # Create path - stop_ids can be names or IDs, service handles by name
            stop_input = wizard_data.get("stop_ids", [])
            # Parse stop_ids: could be comma-separated string or list
            if isinstance(stop_input, str):
                stop_names = [s.strip() for s in stop_input.split(",") if s.strip()]
            else:
                stop_names = stop_input
                
            result = await create_path(
                path_name=wizard_data.get("path_name"),
                stop_names=stop_names,
                user_id=user_id
            )
            state["message"] = f"✅ Path created successfully!\n\n**Path**: {wizard_data.get('path_name')}\n**Stops**: {', '.join(stop_names)}"
            
        elif wizard_type == "create_stop":
            # Create stop
            result = await create_stop(
                stop_name=wizard_data.get("stop_name"),
                latitude=wizard_data.get("latitude"),
                longitude=wizard_data.get("longitude")
            )
            state["message"] = f"✅ Stop created successfully!\n\n**Stop**: {wizard_data.get('stop_name')}"
        
        state["status"] = "success"
        state["wizard_active"] = False
        state["wizard_completed"] = True
        
    except Exception as e:
        logger.error(f"Wizard execution failed: {e}", exc_info=True)
        state["message"] = f"❌ Failed to create {wizard_type}: {str(e)}"
        state["status"] = "error"
        state["wizard_active"] = False
    
    state["next_node"] = "report_result"
    return state
