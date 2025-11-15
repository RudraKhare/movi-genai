"""
Execute Action Node
Performs the actual backend operation for all 20 actions (16 Phase 1 + 4 Phase 3)
"""
from typing import Dict
import logging
from langgraph.tools import (
    tool_assign_vehicle,
    tool_remove_vehicle,
    tool_cancel_trip,
    tool_get_unassigned_vehicles,
    tool_get_trip_details,
    tool_list_all_stops,
    tool_list_stops_for_path,
    tool_list_routes_using_path,
    tool_create_stop,
    tool_create_path,
    tool_create_route,
    tool_update_trip_time,
    tool_rename_stop,
    tool_duplicate_route,
    # Phase 3: Conversational action tools
    tool_get_bookings,
    tool_get_available_drivers,
)

logger = logging.getLogger(__name__)


async def execute_action(state: Dict) -> Dict:
    """
    Execute the action using backend tools.
    
    Handles all 16 actions:
    - READ actions: Execute instantly, return data
    - SAFE MUTATE actions: Execute instantly
    - RISKY MUTATE actions: Already confirmed by this point
    
    Args:
        state: Graph state with action details
        
    Returns:
        Updated state with execution results
    """
    # Skip if there's an error
    if state.get("error"):
        return state
    
    # Check if clarification is needed
    if state.get("needs_clarification"):
        logger.info("[EXECUTE] Clarification needed - skipping execution")
        clarify_options = state.get("clarify_options", [])
        state["status"] = "needs_clarification"
        state["message"] = clarify_options[0] if clarify_options else "Additional information needed"
        return state
    
    action = state.get("action")
    user_id = state.get("user_id", 1)
    
    logger.info(f"[EXECUTE] Action: {action}, User: {user_id}")
    
    result = {}
    
    try:
        # ========== DYNAMIC READ ACTIONS ==========
        if action == "get_unassigned_vehicles":
            result = await tool_get_unassigned_vehicles()
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["vehicle_id", "registration_number", "capacity", "status"]
                }
                state["message"] = f"Found {len(result.get('result', []))} unassigned vehicles"
        
        elif action == "get_trip_status":
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            
            from langgraph.tools import tool_get_trip_status
            result = await tool_get_trip_status(trip_id)
            if result:
                state["final_output"] = {
                    "type": "object",
                    "data": result
                }
                state["message"] = f"Trip {trip_id}: {result.get('live_status', 'UNKNOWN')}"
        
        elif action == "get_trip_details":
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            
            result = await tool_get_trip_details(trip_id)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "object",
                    "data": result.get("result", {})
                }
                state["message"] = f"Details for trip {trip_id}"
        
        # ========== STATIC READ ACTIONS ==========
        elif action == "list_all_stops":
            result = await tool_list_all_stops()
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["stop_id", "stop_name", "latitude", "longitude"]
                }
                state["message"] = f"Found {len(result.get('result', []))} stops"
        
        elif action == "list_stops_for_path":
            path_id = state.get("path_id")
            if not path_id:
                state["error"] = "missing_path_id"
                state["message"] = "Path ID is required"
                return state
            
            result = await tool_list_stops_for_path(path_id)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["stop_order", "stop_name", "latitude", "longitude"]
                }
                state["message"] = f"Path has {len(result.get('result', []))} stops"
        
        elif action == "list_routes_using_path":
            path_id = state.get("path_id")
            if not path_id:
                state["error"] = "missing_path_id"
                state["message"] = "Path ID is required"
                return state
            
            result = await tool_list_routes_using_path(path_id)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["route_id", "route_name", "path_name", "trip_count"]
                }
                state["message"] = f"Found {len(result.get('result', []))} routes"
        
        # ========== DYNAMIC MUTATE ACTIONS (RISKY - Already Confirmed) ==========
        elif action == "cancel_trip":
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                return state
            result = await tool_cancel_trip(trip_id, user_id)
            state["message"] = f"✅ Trip {trip_id} cancelled successfully" if result.get("ok") else result.get("error")
        
        elif action == "remove_vehicle":
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                return state
            result = await tool_remove_vehicle(trip_id, user_id)
            state["message"] = f"✅ Vehicle removed from trip {trip_id}" if result.get("ok") else result.get("error")
        
        elif action == "assign_vehicle":
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            vehicle_id = parsed_params.get("vehicle_id")
            driver_id = parsed_params.get("driver_id")
            vehicle_registration = parsed_params.get("vehicle_registration")
            driver_name = parsed_params.get("driver_name")
            
            logger.info(f"[ASSIGN_VEHICLE] trip_id={trip_id}, vehicle_id={vehicle_id}, driver_id={driver_id}, vehicle_registration={vehicle_registration}, driver_name={driver_name}")
            
            # If we have registration number but no vehicle_id, look it up
            if not vehicle_id and vehicle_registration:
                from app.core.supabase_client import get_conn
                pool = await get_conn()
                async with pool.acquire() as conn:
                    vehicle_row = await conn.fetchrow("""
                        SELECT vehicle_id FROM vehicles
                        WHERE LOWER(registration_number) = LOWER($1)
                        LIMIT 1
                    """, vehicle_registration.strip())
                    if vehicle_row:
                        vehicle_id = vehicle_row['vehicle_id']
                        logger.info(f"[VEHICLE_LOOKUP] ✅ Resolved '{vehicle_registration}' to vehicle_id={vehicle_id}")
                    else:
                        logger.error(f"[VEHICLE_LOOKUP] ❌ Could not find vehicle with registration '{vehicle_registration}'")
                        state["error"] = "vehicle_not_found"
                        state["message"] = f"Could not find vehicle with registration '{vehicle_registration}'"
                        state["status"] = "failed"
                        return state
            
            # If we have driver name but no driver_id, look it up
            if not driver_id and driver_name:
                from app.core.supabase_client import get_conn
                pool = await get_conn()
                async with pool.acquire() as conn:
                    driver_row = await conn.fetchrow("""
                        SELECT driver_id FROM drivers
                        WHERE LOWER(name) LIKE LOWER($1)
                        LIMIT 1
                    """, f"%{driver_name.strip()}%")
                    if driver_row:
                        driver_id = driver_row['driver_id']
                        logger.info(f"[DRIVER_LOOKUP] ✅ Resolved '{driver_name}' to driver_id={driver_id}")
                    else:
                        # Driver is optional, so just log warning
                        logger.warning(f"[DRIVER_LOOKUP] ⚠️ Could not find driver matching '{driver_name}', proceeding without driver")
            
            if not trip_id or not vehicle_id:
                state["error"] = "missing_parameters"
                state["message"] = "Trip ID and Vehicle ID (or registration number) are required"
                state["status"] = "failed"
                logger.error(f"[ASSIGN_VEHICLE] ❌ Missing parameters: trip_id={trip_id}, vehicle_id={vehicle_id}")
                return state
            
            logger.info(f"[ASSIGN_VEHICLE] Calling tool_assign_vehicle(trip_id={trip_id}, vehicle_id={vehicle_id}, driver_id={driver_id}, user_id={user_id})")
            result = await tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id)
            
            if result.get("ok"):
                state["message"] = f"✅ Assigned vehicle {vehicle_id} to trip {trip_id}"
                state["status"] = "completed"
                logger.info(f"[ASSIGN_VEHICLE] ✅ Success: {state['message']}")
            else:
                state["message"] = result.get("error", "Failed to assign vehicle")
                state["error"] = "assignment_failed"
                state["status"] = "failed"
                logger.error(f"[ASSIGN_VEHICLE] ❌ Failed: {state['message']}")
        
        elif action == "update_trip_time":
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            new_time = parsed_params.get("new_time")
            
            if not trip_id or not new_time:
                state["error"] = "missing_parameters"
                state["message"] = "Trip ID and new time are required"
                return state
            
            result = await tool_update_trip_time(trip_id, new_time, user_id)
            state["message"] = f"✅ Trip time updated to {new_time}" if result.get("ok") else result.get("error")
        
        # ========== STATIC MUTATE ACTIONS (SAFE - Execute Instantly) ==========
        elif action == "create_stop":
            parsed_params = state.get("parsed_params", {})
            stop_name = parsed_params.get("stop_name")
            latitude = parsed_params.get("latitude")  # Optional
            longitude = parsed_params.get("longitude")  # Optional
            
            if not stop_name:
                state["error"] = "missing_parameters"
                state["message"] = "Stop name is required"
                state["status"] = "failed"
                return state
            
            result = await tool_create_stop(stop_name, latitude, longitude, user_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result")}
                state["message"] = f"✅ Created stop '{stop_name}'"
                state["status"] = "completed"
            else:
                state["error"] = "creation_failed"
                state["message"] = result.get("error", "Failed to create stop")
                state["status"] = "failed"
        
        elif action == "create_path":
            parsed_params = state.get("parsed_params", {})
            path_name = parsed_params.get("path_name")
            stop_names = parsed_params.get("stop_names", [])
            
            if not path_name or not stop_names:
                state["error"] = "missing_parameters"
                state["message"] = "Path name and stop names are required"
                return state
            
            result = await tool_create_path(path_name, stop_names, user_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result")}
                state["message"] = f"✅ Created path '{path_name}' with {result.get('result', {}).get('stop_count', 0)} stops"
        
        elif action == "create_route":
            path_id = state.get("path_id")
            parsed_params = state.get("parsed_params", {})
            route_name = parsed_params.get("route_name")
            
            if not path_id or not route_name:
                state["error"] = "missing_parameters"
                state["message"] = "Path and route name are required"
                return state
            
            result = await tool_create_route(route_name, path_id, user_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result")}
                state["message"] = f"✅ Created route '{route_name}'"
        
        elif action == "rename_stop":
            parsed_params = state.get("parsed_params", {})
            target_label = state.get("target_label")
            new_name = parsed_params.get("stop_name")
            
            if not target_label or not new_name:
                state["error"] = "missing_parameters"
                state["message"] = "Old stop name and new name are required"
                return state
            
            # Find stop by label
            from app.core.supabase_client import get_conn
            pool = await get_conn()
            async with pool.acquire() as conn:
                stop_row = await conn.fetchrow("""
                    SELECT stop_id FROM stops
                    WHERE LOWER(name) LIKE LOWER($1)
                    LIMIT 1
                """, f"%{target_label}%")
            
            if not stop_row:
                state["error"] = "stop_not_found"
                state["message"] = f"Stop '{target_label}' not found"
                return state
            
            result = await tool_rename_stop(stop_row['stop_id'], new_name, user_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result")}
                state["message"] = f"✅ Renamed stop to '{new_name}'"
        
        elif action == "duplicate_route":
            route_id = state.get("route_id")
            if not route_id:
                state["error"] = "missing_route_id"
                state["message"] = "Route ID is required"
                return state
            
            result = await tool_duplicate_route(route_id, user_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result")}
                state["message"] = f"✅ Duplicated route (new ID: {result.get('result', {}).get('route_id')})"
        
        # ========== HELPER ACTIONS ==========
        # ========== SPECIAL ACTIONS ==========
        elif action == "context_mismatch":
            # User requested action on wrong page
            explanation = state.get("llm_explanation", "This action is not available on the current page.")
            state["message"] = explanation
            state["status"] = "context_mismatch"
            state["error"] = "wrong_page"
            logger.info(f"[CONTEXT_MISMATCH] {explanation}")
        
        elif action == "create_new_route_help":
            state["final_output"] = {
                "type": "help",
                "data": {
                    "title": "How to Create a New Route",
                    "steps": [
                        "1. Go to Manage Routes page",
                        "2. Create stops first if they don't exist: 'Create stop <name> at <lat>, <lon>'",
                        "3. Create a path with ordered stops: 'Create path <name> with stops <stop1>, <stop2>, <stop3>'",
                        "4. Create a route using the path: 'Create route <name> using <path_name>'"
                    ]
                }
            }
            state["message"] = "Here's how to create a new route"
            state["status"] = "completed"
        
        # ========== PHASE 3: CONVERSATIONAL ACTIONS ==========
        elif action == "get_trip_bookings":
            trip_id = state.get("trip_id")
            logger.info(f"[GET_TRIP_BOOKINGS] Fetching bookings for trip {trip_id}")
            result = await tool_get_bookings(trip_id)
            
            if result.get("ok"):
                bookings = result.get("result", [])
                state["final_output"] = {
                    "type": "table",
                    "data": bookings,
                    "columns": ["booking_id", "user_name", "seats_booked", "booking_status", "created_at"]
                }
                state["message"] = f"📋 Found {len(bookings)} booking(s) for trip #{trip_id}"
                state["status"] = "success"
            else:
                state["message"] = f"❌ Failed to fetch bookings: {result.get('message')}"
                state["status"] = "failed"
        
        elif action == "change_driver":
            trip_id = state.get("trip_id")
            logger.info(f"[CHANGE_DRIVER] Initiating driver change for trip {trip_id}")
            
            # Get available drivers
            drivers_result = await tool_get_available_drivers()
            
            if drivers_result.get("ok"):
                drivers = drivers_result.get("result", [])
                if drivers:
                    state["needs_clarification"] = True
                    state["clarify_options"] = [
                        {"id": d["driver_id"], "name": d["name"]} 
                        for d in drivers
                    ]
                    state["message"] = f"👤 Available drivers ({len(drivers)}). Which driver would you like to assign?"
                    state["pending_action"] = "assign_new_driver"
                    state["pending_trip_id"] = trip_id
                else:
                    state["message"] = "⚠️ No available drivers at the moment"
                    state["status"] = "failed"
            else:
                state["message"] = f"❌ Failed to fetch drivers: {drivers_result.get('message')}"
                state["status"] = "failed"
        
        elif action == "duplicate_trip":
            trip_id = state.get("trip_id")
            target_date = state.get("parameters", {}).get("date")
            logger.info(f"[DUPLICATE_TRIP] Duplicating trip {trip_id} to date {target_date}")
            
            # Get trip details first
            trip_result = await tool_get_trip_details(trip_id)
            
            if trip_result.get("ok"):
                trip_details = trip_result.get("result", {})
                
                # If date provided, ask for confirmation
                if target_date:
                    state["needs_clarification"] = True
                    state["message"] = f"🔄 Confirm: Duplicate trip #{trip_id} ({trip_details.get('trip_name')}) to {target_date}?"
                    state["pending_action"] = "confirm_duplicate_trip"
                    state["wizard_data"] = {
                        **trip_details,
                        "trip_date": target_date,
                        "original_trip_id": trip_id
                    }
                else:
                    # Ask for date
                    state["needs_clarification"] = True
                    state["message"] = f"📅 What date should we duplicate trip #{trip_id} ({trip_details.get('trip_name')}) to? (YYYY-MM-DD)"
                    state["pending_action"] = "provide_duplicate_date"
                    state["wizard_data"] = {
                        **trip_details,
                        "original_trip_id": trip_id
                    }
            else:
                state["message"] = f"❌ Failed to fetch trip details: {trip_result.get('message')}"
                state["status"] = "failed"
        
        elif action == "create_followup_trip":
            trip_id = state.get("trip_id")
            logger.info(f"[CREATE_FOLLOWUP_TRIP] Creating follow-up trip for {trip_id}")
            
            # Get trip details first
            trip_result = await tool_get_trip_details(trip_id)
            
            if trip_result.get("ok"):
                trip_details = trip_result.get("result", {})
                state["wizard_active"] = True
                state["wizard_type"] = "create_followup_trip"
                state["wizard_data"] = {
                    "route_id": trip_details.get("route_id"),
                    "trip_date": trip_details.get("trip_date"),
                    "original_trip_name": trip_details.get("trip_name")
                }
                state["wizard_step"] = 0
                state["message"] = f"🔄 Creating follow-up trip after '{trip_details.get('trip_name')}'. What time should the next trip depart? (HH:MM)"
                state["needs_clarification"] = True
            else:
                state["message"] = f"❌ Failed to fetch trip details: {trip_result.get('message')}"
                state["status"] = "failed"
        
        else:
            result = {
                "ok": False,
                "message": f"Unknown action: {action}",
                "action": action
            }
            state["status"] = "failed"
        
        # Update state with result
        state["execution_result"] = result
        state["status"] = "executed" if result.get("ok", True) else "failed"
        
        if not result.get("ok", True) and action not in ["get_trip_status", "get_trip_details", "get_unassigned_vehicles", "list_all_stops", "list_stops_for_path", "list_routes_using_path", "create_new_route_help"]:
            state["error"] = "execution_failed"
            if "message" not in state:
                state["message"] = result.get("message", "Action execution failed")
        
        logger.info(f"[EXECUTE] Result: {result.get('ok', True)} - {state.get('message')}")
        
    except Exception as e:
        logger.error(f"Error executing action: {e}", exc_info=True)
        state["error"] = "execution_error"
        state["status"] = "failed"
        state["message"] = f"Failed to execute action: {str(e)}"
        state["execution_result"] = {"ok": False, "message": str(e)}
    
    return state
