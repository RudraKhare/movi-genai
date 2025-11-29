"""
Decision Router Node
Routes conversation flow based on intent, resolution status, and context.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# PAGE-CONTEXT ACTION MAPPING (Tribal Knowledge)
# ============================================================================

# Actions ONLY allowed on Bus Dashboard (40 actions)
BUS_DASHBOARD_ACTIONS = {
    # A. Trip Management (10 actions)
    "assign_vehicle", "assign_driver", "remove_vehicle", "remove_driver",
    "cancel_trip", "update_trip_time", "update_trip_status", "delay_trip",
    "reschedule_trip", "get_trip_details",
    # Tutorial: Add our new action
    "get_trip_summary",
    # B. Vehicle Management (8 actions)
    "list_all_vehicles", "get_unassigned_vehicles", "get_vehicle_status",
    "get_vehicle_trips_today", "block_vehicle", "unblock_vehicle",
    "add_vehicle", "recommend_vehicle_for_trip",
    # C. Driver Management (7 actions)
    "list_all_drivers", "get_available_drivers", "get_driver_status",
    "get_driver_trips_today", "set_driver_availability",
    "add_driver", "suggest_alternate_vehicle",
    # D. Booking Management (7 actions)
    "get_booking_count", "check_seat_availability", "add_bookings", "reduce_bookings",
    "list_passengers", "cancel_all_bookings", "find_employee_trips",
    # E. Dashboard Intelligence (7 actions)
    "get_trips_needing_attention", "get_today_summary", "get_recent_changes",
    "get_high_demand_offices", "get_most_used_vehicles", "detect_overbooking",
    "predict_problem_trips",
    # F. Automation & Insights (4 actions)
    "check_trip_readiness", "simulate_action", "explain_decision", "get_trip_status",
}

# Actions ONLY allowed on Manage Route page (15 actions)
MANAGE_ROUTE_ACTIONS = {
    # A. Stop/Path/Route Configuration (11 actions)
    "list_all_stops", "list_all_paths", "list_all_routes",
    "list_stops_for_path", "list_routes_using_path",
    "create_stop", "create_path", "create_route",
    "rename_stop", "duplicate_route", "validate_route",
    # B. Delete Operations (3 actions)
    "delete_stop", "delete_path", "delete_route",
    # C. Path Management (1 action)
    "update_path_stops",
    # Helper
    "create_new_route_help",
}

# Actions allowed on both pages (global actions)
GLOBAL_ACTIONS = {
    "unknown", "context_mismatch", "wizard_step_input",
    "create_trip_from_scratch",  # Special wizard
}


def _check_page_context(action: str, current_page: str) -> tuple:
    """
    Check if action is allowed on current page.
    Returns (is_allowed, error_message)
    """
    if not current_page:
        return True, None  # No context, allow
    
    if action in GLOBAL_ACTIONS:
        return True, None  # Global actions allowed everywhere
    
    if current_page == "busDashboard":
        if action in MANAGE_ROUTE_ACTIONS:
            return False, f"⚠️ The action '{action}' is only available on the **Manage Route** page. Please navigate there to manage routes, paths, and stops."
        return True, None
    
    if current_page == "manageRoute":
        if action in BUS_DASHBOARD_ACTIONS:
            return False, f"⚠️ The action '{action}' is only available on the **Bus Dashboard**. Please navigate there for trip, vehicle, and driver management."
        return True, None
    
    return True, None  # Unknown page, allow


async def decision_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route the conversation flow based on:
    - Whether trip/entity was resolved
    - Whether request came from image
    - What action was detected
    - Current page context
    
    Routing Logic:
    0) PAGE CONTEXT CHECK (Tribal Knowledge) - Block invalid actions for current page
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
    parsed_params = state.get("parsed_params", {})
    
    logger.info(f"Decision Router - action: {action}, trip_id: {trip_id}, from_image: {from_image}, resolve_result: {resolve_result}")
    logger.info(f"Decision Router - currentPage: {current_page}, parsed_params: {parsed_params}")
    
    # ========================================================================
    # ROUTE 0: PAGE CONTEXT VALIDATION (Tribal Knowledge - CRITICAL)
    # ========================================================================
    is_allowed, error_message = _check_page_context(action, current_page)
    if not is_allowed:
        logger.warning(f"🚫 PAGE CONTEXT MISMATCH: Action '{action}' not allowed on page '{current_page}'")
        state["next_node"] = "report_result"
        state["status"] = "context_mismatch"
        state["message"] = error_message
        state["action"] = "context_mismatch"  # Override action
        return state
    
    # ========================================================================
    # ROUTE 0.5: SELECTION UI - User selected a vehicle/driver from list
    # ========================================================================
    # If user selected from selection UI (context=selection_ui), execute the action!
    ocr_context = parsed_params.get("context")
    is_selection_ui = ocr_context == "selection_ui"
    
    # Check if entity is already selected (vehicle_id or driver_id provided)
    vehicle_id = parsed_params.get("vehicle_id") or state.get("entity_id")
    driver_id = parsed_params.get("driver_id") or state.get("entity_id")
    
    if is_selection_ui and trip_id:
        logger.info(f"Route SELECTION-UI: User selected entity, executing '{action}' → check_consequences")
        state["next_node"] = "check_consequences"
        return state
    
    # ========================================================================
    # ROUTE 0.6: OCR ACTION BUTTON CLICKED (User selected action from OCR menu)
    # ========================================================================
    # If user clicked an action button after OCR (context=ocr_image), route to appropriate handler
    is_ocr_action = ocr_context == "ocr_image"
    
    # Also check if this is a text command with OCR context (from_image=True but no ocr_context)
    # This happens when user types "assign vehicle" after uploading an image
    is_text_with_ocr_context = from_image and trip_id and not is_ocr_action and ocr_context != "selection_ui" and action != "unknown"
    
    if (is_ocr_action or is_text_with_ocr_context) and trip_id and action != "unknown":
        logger.info(f"Route OCR-ACTION: User action '{action}' with OCR trip context → route to action handler")
        
        # Route to appropriate handler based on action
        if action == "assign_vehicle":
            logger.info("Route OCR-ACTION: assign_vehicle → vehicle_selection_provider")
            state["next_node"] = "vehicle_selection_provider"
            return state
        elif action == "assign_driver":
            logger.info("Route OCR-ACTION: assign_driver → driver_selection_provider")
            state["next_node"] = "driver_selection_provider"
            return state
        elif action in ["remove_vehicle", "remove_driver", "cancel_trip", "update_trip_status"]:
            logger.info(f"Route OCR-ACTION: {action} → check_consequences")
            state["next_node"] = "check_consequences"
            return state
        # Fall through for other actions (like get_trip_status, etc.)
        else:
            logger.info(f"Route OCR-ACTION: {action} → check_consequences (default)")
            state["next_node"] = "check_consequences"
            return state
    
    # A) Trip found from image (INITIAL OCR SCAN ONLY) → show suggestions
    # This only triggers when action is "unknown" or not specified - meaning initial scan
    # If user already specified an action (assign_vehicle, etc.), we handled it above
    if trip_id and from_image and resolve_result == "found" and action == "unknown":
        logger.info("Route A: Initial OCR scan - Trip found, no action specified → suggestion_provider")
        state["next_node"] = "suggestion_provider"
        state["message"] = f"I found this trip. What would you like to do?"
        return state
    
    # B) Trip not found but image provided → offer to create
    if from_image and resolve_result == "none" and not trip_id:
        logger.info("Route B: Trip not found from image → create_trip_suggester")
        state["next_node"] = "create_trip_suggester"
        return state
    
    # C) Multiple matches from OCR → need clarification (trip selection UI)
    if resolve_result == "multiple":
        logger.info("Route C: Multiple matches from OCR → report_result (shows selection)")
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
    
    # D2) Wizard step input → collect_user_input
    if action == "wizard_step_input":
        logger.info("Route D2: Wizard input → collect_user_input")
        state["next_node"] = "collect_user_input"
        return state
    
    # D3) Delete/Rename actions → check_consequences (potentially destructive)
    destructive_actions = [
        "delete_stop",
        "delete_path", 
        "delete_route",
    ]
    
    if action in destructive_actions:
        logger.info(f"Route D3: Destructive action '{action}' → check_consequences")
        state["next_node"] = "check_consequences"
        return state
    
    # D4) Rename actions are safe - go directly to execute
    if action == "rename_stop":
        logger.info(f"Route D4: Rename action '{action}' → check_consequences (safe)")
        state["next_node"] = "check_consequences"
        return state
    
    # TUTORIAL: get_trip_summary is a read-only action, goes directly to our custom node
    if action == "get_trip_summary":
        logger.info(f"Route TUTORIAL: get_trip_summary → get_trip_summary node")
        state["next_node"] = "get_trip_summary"
        return state

    # D5) Compound assign_vehicle_and_driver → check_consequences (executes both in sequence)
    if action == "assign_vehicle_and_driver" and trip_id:
        logger.info(f"Route D5: Compound action assign_vehicle_and_driver for trip {trip_id}")
        
        # Check deployment status first
        from langgraph.tools import tool_get_trip_status
        trip_status = await tool_get_trip_status(trip_id)
        
        has_vehicle = trip_status.get("vehicle_id")
        has_driver = trip_status.get("driver_id")
        
        if has_vehicle and has_driver:
            state["next_node"] = "report_result"
            state["status"] = "failed"
            state["message"] = f"Trip {trip_id} already has vehicle and driver assigned. Remove them first to reassign."
            return state
        
        # Check if we have vehicle and driver info
        vehicle_reg = parsed_params.get("vehicle_registration")
        driver_name = parsed_params.get("driver_name")
        
        if not vehicle_reg or not driver_name:
            # Missing info - provide helpful message
            missing = []
            if not vehicle_reg:
                missing.append("vehicle registration")
            if not driver_name:
                missing.append("driver name")
            state["next_node"] = "report_result"
            state["status"] = "failed"
            state["message"] = f"Please provide the {' and '.join(missing)} to assign."
            return state
        
        # Route to execute_action for compound execution
        state["next_node"] = "check_consequences"
        return state
    
    # E) Unknown action with no target → fallback
    if action == "unknown" and not trip_id:
        logger.info("Route E: Unknown action, no target → fallback")
        state["next_node"] = "report_result"
        state["message"] = "I'm not sure what you want to do. Could you rephrase that?"
        state["status"] = "unknown"
        return state
    
    # F) Context mismatch → provide helpful message about correct page
    if action == "context_mismatch":
        logger.info("Route F: Context mismatch → report_result")
        state["next_node"] = "report_result"
        state["status"] = "context_mismatch"
        
        # Use LLM explanation if available, otherwise provide default message
        llm_explanation = state.get("llm_explanation", "")
        current_page = state.get("currentPage", "unknown")
        
        # Map actions to appropriate pages
        page_suggestions = {
            "busDashboard": "You can manage trip status, bookings, vehicles, and drivers here.",
            "manageRoute": "You can view and edit routes, paths, and stops here.",
            "tripManagement": "You can create and schedule trips here."
        }
        
        if "path" in state.get("text", "").lower() or "stop" in state.get("text", "").lower():
            state["message"] = f"To view stops for a path, please go to the **Manage Route** page. On the Bus Dashboard, I can help you with trip status, bookings, vehicles, and drivers."
        elif "route" in state.get("text", "").lower():
            state["message"] = f"Route management is available on the **Manage Route** page. Here on the Bus Dashboard, I can help you with trip operations."
        else:
            state["message"] = llm_explanation if llm_explanation else f"This action is not available on the current page. {page_suggestions.get(current_page, '')}"
        
        return state
    
    # G) Assign vehicle - ALWAYS check deployment first (for all vehicle assignments)
    if action == "assign_vehicle" and trip_id:
        logger.info(f"Route G: Processing assign_vehicle with trip_id={trip_id}, parsed_params={parsed_params}")
        
        # Universal deployment check for ALL vehicle assignments (structured commands and natural language)
        from langgraph.tools import tool_get_trip_status
        trip_status = await tool_get_trip_status(trip_id)
        logger.info(f"Route G: Trip {trip_id} status check: {trip_status}")
        
        # Check for COMPLETE deployment (both vehicle_id and deployment_id)
        # Allow assignment if deployment exists but no vehicle assigned (orphaned deployment)
        has_vehicle = trip_status.get("vehicle_id")
        has_deployment = trip_status.get("deployment_id")
        
        if has_vehicle and has_deployment:
            # Complete deployment - block assignment
            logger.info("Route G: assign_vehicle rejected → trip has complete deployment")
            state["next_node"] = "report_result"
            state["error"] = "already_deployed"
            state["status"] = "failed"
            state["message"] = (
                f"This trip already has vehicle {has_vehicle} assigned. "
                "Remove it first if you want to assign a different vehicle."
            )
            return state
        elif has_deployment and not has_vehicle:
            # Orphaned deployment - allow assignment but warn
            logger.info(f"Route G: Found orphaned deployment {has_deployment} for trip {trip_id} - allowing vehicle assignment")
        elif has_vehicle and not has_deployment:
            # Vehicle without deployment (shouldn't happen, but handle it)
            logger.warning(f"Route G: Trip {trip_id} has vehicle but no deployment - unusual state")
        else:
            # No deployment, no vehicle - normal case
            logger.info(f"Route G: Trip {trip_id} has no deployment - allowing vehicle assignment")
        
        vehicle_id = parsed_params.get("vehicle_id") or parsed_params.get("target_vehicle_id")
        logger.info(f"Route G: Extracted vehicle_id={vehicle_id}")
        
        # If no vehicle_id specified, show vehicle selection
        if not vehicle_id:
            logger.info("Route G: assign_vehicle missing vehicle_id → vehicle_selection_provider")
            state["next_node"] = "vehicle_selection_provider"
            return state
        else:
            # Vehicle specified and no deployment conflict → proceed to consequences
            logger.info(f"Route G: assign_vehicle with vehicle_id {vehicle_id} (no conflict) → check_consequences")
            state["next_node"] = "check_consequences"
            return state
    
    # H) Assign driver without driver_id → show driver options
    if action == "assign_driver" and trip_id:
        # Skip driver selection if this is a structured command with driver already selected
        if state.get("from_selection_ui") and state.get("selectedEntityId"):
            logger.info(f"Route H: Structured command with driver_id {state['selectedEntityId']} → check_consequences")
            state["next_node"] = "check_consequences"
            return state
        
        driver_id = (parsed_params.get("driver_id") or 
                    parsed_params.get("target_driver_id") or 
                    state.get("selectedEntityId") or 
                    state.get("driver_id"))
        
        # If no driver_id specified, show driver selection
        if not driver_id:
            logger.info("Route H: assign_driver missing driver_id → driver_selection_provider")
            state["next_node"] = "driver_selection_provider"
            return state
        
        # Driver ID is available, continue to normal flow
        logger.info(f"Route H: assign_driver with driver_id {driver_id} → check_consequences")
    
    # I) Assign driver error handling (from resolve_target)
    if action == "assign_driver" and trip_id:
        # Check if driver assignment failed resolution
        if state.get("error") in ["driver_not_found", "missing_driver", "driver_lookup_failed"]:
            logger.info("Route I: assign_driver failed resolution → report_result")
            state["next_node"] = "report_result"
            return state
    
    # J) Normal dynamic actions → existing flow (consequences → confirm → execute)
    logger.info(f"Route J: Dynamic action '{action}' → check_consequences")
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
