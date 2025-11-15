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
    WizardStep("select_path", "Which path should this route follow?", "path_id"),
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
    WizardStep("latitude", "Latitude? (optional)", "latitude"),
    WizardStep("longitude", "Longitude? (optional)", "longitude"),
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
    
    # Show collected data so far
    if wizard_data:
        message += "\n\n*Collected so far:*"
        for key, value in wizard_data.items():
            if not key.startswith("_"):
                message += f"\n• {key}: {value}"
    
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
    state["next_node"] = "collect_user_input"
    
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
        create_trip
    )
    
    logger.info(f"Executing {wizard_type} with data: {wizard_data}")
    
    try:
        if wizard_type in ["create_trip_from_scratch", "start_trip_wizard"]:
            # Create trip
            result = await create_trip(
                route_id=int(wizard_data.get("route_id")),
                trip_date=wizard_data.get("trip_date"),
                scheduled_time=wizard_data.get("scheduled_time"),
                vehicle_id=wizard_data.get("vehicle_id"),
                driver_id=wizard_data.get("driver_id")
            )
            state["message"] = f"✅ Trip created successfully!\n\n**Trip ID**: {result.get('trip_id')}"
            state["trip_id"] = result.get("trip_id")
            
        elif wizard_type in ["create_route", "create_new_route_help"]:
            # Create route
            result = await create_route(
                route_name=wizard_data.get("route_name"),
                path_id=int(wizard_data.get("path_id")),
                direction=wizard_data.get("direction", "UP")
            )
            state["message"] = f"✅ Route created successfully!\n\n**Route**: {wizard_data.get('route_name')}"
            
        elif wizard_type == "create_path":
            # Create path
            result = await create_path(
                path_name=wizard_data.get("path_name"),
                stop_ids=wizard_data.get("stop_ids", [])
            )
            state["message"] = f"✅ Path created successfully!\n\n**Path**: {wizard_data.get('path_name')}"
            
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
