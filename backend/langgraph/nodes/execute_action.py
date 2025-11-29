"""
Execute Action Node
Performs the actual backend operation for all 20 actions (16 Phase 1 + 4 Phase 3)
"""
from typing import Dict
import logging
from langgraph.tools import (
    tool_assign_vehicle,
    tool_assign_driver,
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
        
        elif action == "get_available_drivers":
            drivers_list = await tool_get_available_drivers()
            result = {"ok": True, "result": drivers_list, "count": len(drivers_list)}
            if drivers_list:
                state["final_output"] = {
                    "type": "table",
                    "data": drivers_list,
                    "columns": ["driver_id", "name", "license_number", "status"]
                }
                state["message"] = f"Found {len(drivers_list)} available drivers"
            else:
                state["message"] = "No available drivers found"
        
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
                state["status"] = "completed"
                state["success"] = True
        
        elif action == "get_trip_stops":
            from langgraph.tools import tool_get_trip_stops
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            
            result = await tool_get_trip_stops(trip_id)
            if result.get("ok"):
                data = result.get("result", {})
                stops = data.get("stops", [])
                state["final_output"] = {
                    "type": "table",
                    "data": stops,
                    "columns": ["stop_order", "stop_name"]
                }
                state["message"] = f"Trip '{data.get('display_name')}' has {len(stops)} stops on path '{data.get('path_name')}'"
                state["status"] = "completed"
                state["success"] = True
            else:
                state["message"] = result.get("error", "Failed to get trip stops")
                state["status"] = "failed"
        
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
        
        elif action == "list_all_paths" or action == "get_all_paths":
            from langgraph.tools import tool_get_all_paths
            paths_list = await tool_get_all_paths()
            result = {"ok": True, "result": paths_list, "count": len(paths_list)}
            state["final_output"] = {
                "type": "table",
                "data": paths_list,
                "columns": ["path_id", "path_name", "stop_count"]
            }
            state["message"] = f"Found {len(paths_list)} paths"
        
        elif action == "list_all_routes" or action == "get_all_routes":
            from langgraph.tools import tool_get_all_routes
            routes_list = await tool_get_all_routes()
            result = {"ok": True, "result": routes_list, "count": len(routes_list)}
            state["final_output"] = {
                "type": "table",
                "data": routes_list,
                "columns": ["route_id", "route_name", "path_name", "departure_time"]
            }
            state["message"] = f"Found {len(routes_list)} routes"
        
        elif action == "list_all_vehicles" or action == "get_vehicles":
            from langgraph.tools import tool_get_vehicles
            vehicles_list = await tool_get_vehicles()
            result = {"ok": True, "result": vehicles_list, "count": len(vehicles_list)}
            state["final_output"] = {
                "type": "table",
                "data": vehicles_list,
                "columns": ["vehicle_id", "registration_number", "vehicle_type", "capacity", "status"]
            }
            state["message"] = f"Found {len(vehicles_list)} vehicles"
        
        elif action == "list_all_drivers" or action == "get_drivers":
            from langgraph.tools import tool_get_drivers
            drivers_list = await tool_get_drivers()
            result = {"ok": True, "result": drivers_list, "count": len(drivers_list)}
            state["final_output"] = {
                "type": "table",
                "data": drivers_list,
                "columns": ["driver_id", "name", "phone", "license_number", "status"]
            }
            state["message"] = f"Found {len(drivers_list)} drivers"
        
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
        
        elif action == "remove_driver":
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required to remove driver"
                state["status"] = "failed"
                return state
            
            from langgraph.tools import tool_remove_driver
            result = await tool_remove_driver(trip_id, user_id)
            
            if result.get("ok"):
                state["message"] = f"✅ Driver removed from trip {trip_id}"
                state["status"] = "completed"
            else:
                state["message"] = result.get("message", "Failed to remove driver")
                state["status"] = "failed"
        
        elif action == "update_trip_status":
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            new_status = parsed_params.get("new_status")
            
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required to update status"
                state["status"] = "failed"
                return state
            
            if not new_status:
                state["error"] = "missing_status"
                state["message"] = "New status is required (e.g., IN_PROGRESS, COMPLETED, CANCELLED)"
                state["status"] = "failed"
                return state
            
            from langgraph.tools import tool_update_trip_status
            result = await tool_update_trip_status(trip_id, new_status, user_id)
            
            if result.get("ok"):
                state["message"] = f"✅ Trip {trip_id} status updated to {new_status.upper()}"
                state["status"] = "completed"
            else:
                state["message"] = result.get("message", "Failed to update trip status")
                state["status"] = "failed"
        
        elif action == "assign_vehicle":
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            vehicle_id = parsed_params.get("vehicle_id")
            driver_id = parsed_params.get("driver_id")
            # ✅ FIX: Check both vehicle_registration and vehicle_name for structured commands
            vehicle_registration = parsed_params.get("vehicle_registration") or parsed_params.get("vehicle_name")
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
                # ✅ FIX: Include vehicle name/registration in success message
                vehicle_display = vehicle_registration or vehicle_id
                state["message"] = f"✅ Assigned vehicle {vehicle_display} to trip {trip_id}"
                state["status"] = "completed"
                logger.info(f"[ASSIGN_VEHICLE] ✅ Success: {state['message']}")
            else:
                state["message"] = result.get("error", "Failed to assign vehicle")
                state["error"] = "assignment_failed"
                state["status"] = "failed"
                logger.error(f"[ASSIGN_VEHICLE] ❌ Failed: {state['message']}")
        
        elif action == "assign_driver":
            trip_id = state.get("trip_id") or state.get("selectedTripId")
            parsed_params = state.get("parsed_params", {})
            # ✅ FIX: Get driver_id from parsed_params (LLM output) OR direct state
            driver_id = parsed_params.get("driver_id") or state.get("driver_id") or state.get("selectedEntityId")
            driver_name = parsed_params.get("driver_name") or state.get("driver_name") or state.get("entityName")
            
            logger.info(f"[ASSIGN_DRIVER] trip_id={trip_id}, driver_id={driver_id}, driver_name={driver_name}, parsed_params={parsed_params}")
            
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required to assign a driver"
                state["status"] = "failed"
                logger.error("[ASSIGN_DRIVER] ❌ Missing trip_id")
                return state
            
            if not driver_id:
                state["error"] = "missing_driver_id"
                state["message"] = "Driver ID is required (driver resolution should have happened in resolve_target)"
                state["status"] = "failed"
                logger.error("[ASSIGN_DRIVER] ❌ Missing driver_id")
                return state
            
            logger.info(f"[ASSIGN_DRIVER] Calling tool_assign_driver(trip_id={trip_id}, driver_id={driver_id}, user_id={user_id})")
            result = await tool_assign_driver(trip_id, driver_id, user_id)
            
            if result.get("ok"):
                display_driver_name = driver_name or f"Driver {driver_id}"
                state["message"] = f"✅ Assigned {display_driver_name} to trip {trip_id}"
                state["status"] = "completed"
                state["execution_result"] = result
                logger.info(f"[ASSIGN_DRIVER] ✅ Success: {state['message']}")
            else:
                state["message"] = result.get("message", "Failed to assign driver")
                state["error"] = "assignment_failed"
                state["status"] = "failed"
                logger.error(f"[ASSIGN_DRIVER] ❌ Failed: {state['message']}")
        
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
        
        # ========== DASHBOARD INTELLIGENCE ACTIONS ==========
        elif action == "get_trips_needing_attention":
            from langgraph.tools import tool_get_trips_needing_attention
            result = await tool_get_trips_needing_attention()
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["trip_id", "display_name", "attention_reason", "live_status"]
                }
                state["message"] = result.get("message", f"Found {result.get('count', 0)} trip(s) needing attention")
            else:
                state["message"] = result.get("error", "Failed to get trips needing attention")
                state["status"] = "failed"
        
        elif action == "get_today_summary":
            from langgraph.tools import tool_get_today_summary
            result = await tool_get_today_summary()
            if result.get("ok"):
                summary = result.get("result", {})
                trip_stats = summary.get("trip_stats", {})
                deploy_stats = summary.get("deployment_stats", {})
                state["final_output"] = {"type": "object", "data": summary}
                state["message"] = (
                    f"📊 Today's Summary:\n"
                    f"• Total trips: {trip_stats.get('total_trips', 0)}\n"
                    f"• Scheduled: {trip_stats.get('scheduled', 0)} | In Progress: {trip_stats.get('in_progress', 0)} | Completed: {trip_stats.get('completed', 0)}\n"
                    f"• Vehicles in use: {deploy_stats.get('vehicles_in_use', 0)} | Drivers on duty: {deploy_stats.get('drivers_on_duty', 0)}\n"
                    f"• Trips needing vehicle: {deploy_stats.get('trips_without_vehicle', 0)} | Needing driver: {deploy_stats.get('trips_without_driver', 0)}"
                )
            else:
                state["message"] = result.get("error", "Failed to get today's summary")
                state["status"] = "failed"
        
        elif action == "get_recent_changes":
            from langgraph.tools import tool_get_recent_changes
            parsed_params = state.get("parsed_params", {})
            minutes = parsed_params.get("minutes", 10)
            result = await tool_get_recent_changes(minutes)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["action_type", "table_name", "record_id", "changed_at"]
                }
                state["message"] = f"Found {result.get('count', 0)} changes in the last {minutes} minutes"
            else:
                state["message"] = result.get("error", "Failed to get recent changes")
                state["status"] = "failed"
        
        elif action == "get_high_demand_offices":
            from langgraph.tools import tool_get_high_demand_offices
            result = await tool_get_high_demand_offices()
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["office_name", "total_bookings", "trips_serving"]
                }
                state["message"] = f"Top {len(result.get('result', []))} high-demand offices"
            else:
                state["message"] = result.get("error", "Failed to get high demand offices")
                state["status"] = "failed"
        
        elif action == "get_most_used_vehicles":
            from langgraph.tools import tool_get_most_used_vehicles
            parsed_params = state.get("parsed_params", {})
            days = parsed_params.get("days", 7)
            result = await tool_get_most_used_vehicles(days)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["registration_number", "vehicle_type", "trip_count", "total_passengers"]
                }
                state["message"] = f"Top {len(result.get('result', []))} most used vehicles in the last {days} days"
            else:
                state["message"] = result.get("error", "Failed to get most used vehicles")
                state["status"] = "failed"
        
        elif action == "detect_overbooking":
            from langgraph.tools import tool_detect_overbooking
            result = await tool_detect_overbooking()
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["trip_id", "display_name", "booked_count", "vehicle_capacity", "over_by"]
                }
                state["message"] = result.get("message", "Overbooking check completed")
            else:
                state["message"] = result.get("error", "Failed to detect overbooking")
                state["status"] = "failed"
        
        elif action == "predict_problem_trips":
            from langgraph.tools import tool_predict_problem_trips
            result = await tool_predict_problem_trips()
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["trip_id", "display_name", "risk_type", "live_status"]
                }
                state["message"] = result.get("message", "Problem prediction completed")
            else:
                state["message"] = result.get("error", "Failed to predict problem trips")
                state["status"] = "failed"
        
        # ========== VEHICLE MANAGEMENT ACTIONS ==========
        elif action == "get_vehicle_status":
            from langgraph.tools import tool_get_vehicle_status
            parsed_params = state.get("parsed_params", {})
            vehicle_id = parsed_params.get("vehicle_id")
            if not vehicle_id:
                state["error"] = "missing_vehicle_id"
                state["message"] = "Vehicle ID is required"
                return state
            result = await tool_get_vehicle_status(vehicle_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result", {})}
                data = result.get("result", {})
                state["message"] = f"Vehicle {data.get('registration_number')}: {data.get('status')} - {data.get('assignment_count', 0)} trips today"
            else:
                state["message"] = result.get("error", "Failed to get vehicle status")
                state["status"] = "failed"
        
        elif action == "block_vehicle":
            from langgraph.tools import tool_block_vehicle
            parsed_params = state.get("parsed_params", {})
            vehicle_id = parsed_params.get("vehicle_id")
            reason = parsed_params.get("reason", "Blocked by operator")
            if not vehicle_id:
                state["error"] = "missing_vehicle_id"
                state["message"] = "Vehicle ID is required"
                return state
            result = await tool_block_vehicle(vehicle_id, reason, user_id)
            state["message"] = result.get("message", "Vehicle blocked")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "unblock_vehicle":
            from langgraph.tools import tool_unblock_vehicle
            parsed_params = state.get("parsed_params", {})
            vehicle_id = parsed_params.get("vehicle_id")
            if not vehicle_id:
                state["error"] = "missing_vehicle_id"
                state["message"] = "Vehicle ID is required"
                return state
            result = await tool_unblock_vehicle(vehicle_id, user_id)
            state["message"] = result.get("message", "Vehicle unblocked")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "get_vehicle_trips_today":
            from langgraph.tools import tool_get_vehicle_trips_today
            parsed_params = state.get("parsed_params", {})
            vehicle_id = parsed_params.get("vehicle_id")
            if not vehicle_id:
                state["error"] = "missing_vehicle_id"
                state["message"] = "Vehicle ID is required"
                return state
            result = await tool_get_vehicle_trips_today(vehicle_id)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["trip_id", "display_name", "live_status", "driver_name"]
                }
                state["message"] = f"Vehicle has {result.get('count', 0)} trip(s) today"
            else:
                state["message"] = result.get("error", "Failed to get vehicle trips")
                state["status"] = "failed"
        
        elif action == "recommend_vehicle_for_trip" or action == "suggest_alternate_vehicle":
            from langgraph.tools import tool_recommend_vehicle_for_trip
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            passenger_count = parsed_params.get("passenger_count")
            
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            
            # If no passenger count provided, ask for it
            if not passenger_count:
                state["status"] = "awaiting_input"
                state["awaiting_selection"] = True
                state["selection_type"] = "passenger_count"
                state["message"] = "🚌 How many passengers do you need to accommodate for this trip?\n\nPlease enter the number of passengers:"
                state["trip_id"] = trip_id  # Preserve trip_id for next iteration
                state["final_output"] = {
                    "type": "input_required",
                    "data": {  # Add data field so report_result includes this
                        "input_type": "number",
                        "field": "passenger_count",
                        "trip_id": trip_id,
                        "prompt": "Enter number of passengers"
                    },
                    "input_type": "number",
                    "field": "passenger_count",
                    "trip_id": trip_id,
                    "prompt": "Enter number of passengers"
                }
                return state
            
            # We have passenger count, get recommendations filtered by capacity
            result = await tool_recommend_vehicle_for_trip(trip_id, min_capacity=int(passenger_count))
            if result.get("ok"):
                vehicles = result.get("result", [])
                if vehicles:
                    state["final_output"] = {
                        "type": "table",
                        "data": vehicles,
                        "columns": ["registration_number", "vehicle_type", "capacity", "current_assignments"]
                    }
                    state["message"] = f"🚌 Found {len(vehicles)} vehicles with capacity ≥ {passenger_count} passengers:"
                else:
                    state["message"] = f"❌ No vehicles found with capacity ≥ {passenger_count} passengers. Try a smaller number or check vehicle availability."
                    state["status"] = "failed"
            else:
                state["message"] = result.get("error", "Failed to recommend vehicle")
                state["status"] = "failed"
        
        # ========== DRIVER MANAGEMENT ACTIONS ==========
        elif action == "get_driver_status":
            from langgraph.tools import tool_get_driver_status
            parsed_params = state.get("parsed_params", {})
            driver_id = parsed_params.get("driver_id")
            if not driver_id:
                state["error"] = "missing_driver_id"
                state["message"] = "Driver ID is required"
                return state
            result = await tool_get_driver_status(driver_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result", {})}
                data = result.get("result", {})
                state["message"] = f"Driver {data.get('name')}: {'Available' if data.get('is_available') else 'Unavailable'} - {data.get('assignment_count', 0)} trips today"
            else:
                state["message"] = result.get("error", "Failed to get driver status")
                state["status"] = "failed"
        
        elif action == "get_driver_trips_today":
            from langgraph.tools import tool_get_driver_trips_today
            parsed_params = state.get("parsed_params", {})
            driver_id = parsed_params.get("driver_id")
            if not driver_id:
                state["error"] = "missing_driver_id"
                state["message"] = "Driver ID is required"
                return state
            result = await tool_get_driver_trips_today(driver_id)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["trip_id", "display_name", "live_status", "registration_number"]
                }
                state["message"] = f"Driver has {result.get('count', 0)} trip(s) today"
            else:
                state["message"] = result.get("error", "Failed to get driver trips")
                state["status"] = "failed"
        
        elif action == "set_driver_availability":
            from langgraph.tools import tool_set_driver_availability
            parsed_params = state.get("parsed_params", {})
            driver_id = parsed_params.get("driver_id")
            is_available = parsed_params.get("is_available", True)
            if not driver_id:
                state["error"] = "missing_driver_id"
                state["message"] = "Driver ID is required"
                return state
            result = await tool_set_driver_availability(driver_id, is_available, user_id)
            state["message"] = result.get("message", "Driver availability updated")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        # ========== BOOKING MANAGEMENT ACTIONS ==========
        elif action == "get_booking_count":
            from langgraph.tools import tool_get_booking_count
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            result = await tool_get_booking_count(trip_id)
            if result.get("ok"):
                data = result.get("result", {})
                state["final_output"] = {"type": "object", "data": data}
                state["message"] = f"Trip {data.get('display_name')}: {data.get('booked_count', 0)} bookings ({data.get('booking_status_percentage', 0)}% capacity)"
                state["status"] = "completed"
                state["success"] = True
            else:
                state["message"] = result.get("error", "Failed to get booking count")
                state["status"] = "failed"
        
        elif action == "check_seat_availability":
            from langgraph.tools import tool_check_seat_availability
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required to check availability"
                return state
            result = await tool_check_seat_availability(trip_id)
            if result.get("ok"):
                data = result.get("result", {})
                state["final_output"] = {"type": "object", "data": data}
                if data.get("is_full"):
                    state["message"] = f"🚫 Trip **{data.get('display_name')}** is FULL ({data.get('seats_booked')}/{data.get('capacity')} seats booked)"
                else:
                    state["message"] = f"✅ Trip **{data.get('display_name')}**: {data.get('seats_available')} seats available ({data.get('seats_booked')}/{data.get('capacity')} booked, {data.get('percentage_booked')}%)"
                state["status"] = "completed"
                state["success"] = True
            else:
                state["message"] = result.get("error", "Failed to check availability")
                state["status"] = "failed"
        
        elif action == "add_bookings":
            from langgraph.tools import tool_add_bookings
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            booking_count = parsed_params.get("booking_count") or parsed_params.get("count") or 1
            
            # Try to convert to int if string
            try:
                booking_count = int(booking_count)
            except (ValueError, TypeError):
                booking_count = 1
            
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required to add bookings"
                return state
            
            logger.info(f"[ADD_BOOKINGS] trip_id={trip_id}, count={booking_count}")
            result = await tool_add_bookings(trip_id, booking_count, user_id)
            
            if result.get("ok"):
                data = result.get("result", {})
                state["final_output"] = {"type": "object", "data": data}
                state["message"] = f"✅ Added {data.get('bookings_added')} booking(s) to trip. New total: {data.get('new_count')}/{data.get('capacity')} ({data.get('seats_available')} seats available)"
                state["status"] = "completed"
                state["success"] = True
            else:
                state["message"] = result.get("error", "Failed to add bookings")
                state["status"] = "failed"
        
        elif action == "reduce_bookings":
            from langgraph.tools import tool_reduce_bookings
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            booking_count = parsed_params.get("booking_count") or parsed_params.get("count") or 1
            
            # Try to convert to int if string
            try:
                booking_count = int(booking_count)
            except (ValueError, TypeError):
                booking_count = 1
            
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required to reduce bookings"
                return state
            
            logger.info(f"[REDUCE_BOOKINGS] trip_id={trip_id}, count={booking_count}")
            result = await tool_reduce_bookings(trip_id, booking_count, user_id)
            
            if result.get("ok"):
                data = result.get("result", {})
                state["final_output"] = {"type": "object", "data": data}
                state["message"] = f"✅ Reduced {data.get('bookings_reduced')} booking(s) from trip. New total: {data.get('new_count')}/{data.get('capacity')} ({data.get('seats_available')} seats available)"
                state["status"] = "completed"
                state["success"] = True
            else:
                state["message"] = result.get("error", "Failed to reduce bookings")
                state["status"] = "failed"
        
        elif action == "list_passengers":
            from langgraph.tools import tool_list_passengers
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            result = await tool_list_passengers(trip_id)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["user_name", "seats", "status", "pickup_stop", "drop_stop"]
                }
                state["message"] = f"Found {result.get('count', 0)} passenger(s)"
                state["status"] = "completed"
                state["success"] = True
            else:
                state["message"] = result.get("error", "Failed to list passengers")
                state["status"] = "failed"
        
        elif action == "cancel_all_bookings":
            from langgraph.tools import tool_cancel_all_bookings
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            reason = parsed_params.get("reason", "Cancelled by operator")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            result = await tool_cancel_all_bookings(trip_id, reason, user_id)
            state["message"] = result.get("message", "Bookings cancelled")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "find_employee_trips":
            from langgraph.tools import tool_find_employee_trips
            parsed_params = state.get("parsed_params", {})
            employee_name = parsed_params.get("employee_name")
            if not employee_name:
                state["error"] = "missing_employee_name"
                state["message"] = "Employee name is required"
                return state
            result = await tool_find_employee_trips(employee_name)
            if result.get("ok"):
                state["final_output"] = {
                    "type": "table",
                    "data": result.get("result", []),
                    "columns": ["user_name", "display_name", "trip_date", "booking_status"]
                }
                state["message"] = f"Found {result.get('count', 0)} booking(s) for '{employee_name}'"
            else:
                state["message"] = result.get("error", "Failed to find employee trips")
                state["status"] = "failed"
        
        # ========== SMART AUTOMATION ACTIONS ==========
        elif action == "check_trip_readiness":
            from langgraph.tools import tool_check_trip_readiness
            trip_id = state.get("trip_id")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            result = await tool_check_trip_readiness(trip_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result", {})}
                state["message"] = result.get("message", "Trip readiness checked")
            else:
                state["message"] = result.get("error", "Failed to check trip readiness")
                state["status"] = "failed"
        
        elif action == "simulate_action":
            from langgraph.tools import tool_simulate_action
            parsed_params = state.get("parsed_params", {})
            simulated_action = parsed_params.get("action")
            trip_id = state.get("trip_id")
            result = await tool_simulate_action(simulated_action, trip_id, **parsed_params)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result", {})}
                state["message"] = result.get("message", "Simulation completed")
            else:
                state["message"] = result.get("error", "Failed to simulate action")
                state["status"] = "failed"
        
        elif action == "explain_decision":
            from langgraph.tools import tool_explain_decision
            parsed_params = state.get("parsed_params", {})
            explained_action = parsed_params.get("action", state.get("last_action", "unknown"))
            result = await tool_explain_decision(explained_action, parsed_params)
            if result.get("ok"):
                explanation = result.get("result", {}).get("explanation", "No explanation available")
                state["message"] = f"💡 {explanation}"
            else:
                state["message"] = result.get("error", "Failed to explain decision")
                state["status"] = "failed"
        
        # ========== STOP/PATH/ROUTE MANAGEMENT ==========
        elif action == "delete_stop":
            from langgraph.tools import tool_delete_stop
            from app.core.service import list_all_stops
            parsed_params = state.get("parsed_params", {})
            stop_id = parsed_params.get("stop_id")
            
            # If no stop_id, try to resolve from stop_name or stop_names
            if not stop_id:
                stop_name = parsed_params.get("stop_name")
                stop_names = parsed_params.get("stop_names", [])
                target_name = stop_name or (stop_names[0] if stop_names else None)
                
                if target_name:
                    # Resolve stop name to ID
                    all_stops = await list_all_stops()
                    for stop in all_stops:
                        if stop.get("stop_name", "").lower() == target_name.lower():
                            stop_id = stop.get("stop_id")
                            logger.info(f"[DELETE_STOP] Resolved '{target_name}' to stop_id={stop_id}")
                            break
            
            if not stop_id:
                state["error"] = "missing_stop_id"
                state["message"] = "❌ Could not find the stop to delete. Please specify a valid stop name or ID."
                state["status"] = "failed"
                return state
            result = await tool_delete_stop(stop_id, user_id)
            state["message"] = result.get("message") if result.get("ok") else result.get("error")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "delete_path":
            from langgraph.tools import tool_delete_path
            from app.core.service import list_all_paths
            parsed_params = state.get("parsed_params", {})
            path_id = parsed_params.get("path_id") or state.get("path_id")
            
            # If no path_id, try to resolve from path_name
            if not path_id:
                path_name = parsed_params.get("path_name")
                if path_name:
                    all_paths = await list_all_paths()
                    for path in all_paths:
                        if path.get("path_name", "").lower() == path_name.lower():
                            path_id = path.get("path_id")
                            logger.info(f"[DELETE_PATH] Resolved '{path_name}' to path_id={path_id}")
                            break
            
            if not path_id:
                state["error"] = "missing_path_id"
                state["message"] = "❌ Could not find the path to delete. Please specify a valid path name or ID."
                state["status"] = "failed"
                return state
            result = await tool_delete_path(path_id, user_id)
            state["message"] = result.get("message") if result.get("ok") else result.get("error")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "delete_route":
            from langgraph.tools import tool_delete_route
            from app.core.service import list_all_routes
            parsed_params = state.get("parsed_params", {})
            route_id = parsed_params.get("route_id") or state.get("route_id")
            
            # If no route_id, try to resolve from route_name
            if not route_id:
                route_name = parsed_params.get("route_name")
                if route_name:
                    all_routes = await list_all_routes()
                    for route in all_routes:
                        if route.get("route_name", "").lower() == route_name.lower():
                            route_id = route.get("route_id")
                            logger.info(f"[DELETE_ROUTE] Resolved '{route_name}' to route_id={route_id}")
                            break
            
            if not route_id:
                state["error"] = "missing_route_id"
                state["message"] = "❌ Could not find the route to delete. Please specify a valid route name or ID."
                state["status"] = "failed"
                return state
            result = await tool_delete_route(route_id, user_id)
            state["message"] = result.get("message") if result.get("ok") else result.get("error")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "update_path_stops":
            from langgraph.tools import tool_update_path_stops
            parsed_params = state.get("parsed_params", {})
            path_id = parsed_params.get("path_id") or state.get("path_id")
            stop_ids = parsed_params.get("stop_ids", [])
            if not path_id:
                state["error"] = "missing_path_id"
                state["message"] = "Path ID is required"
                return state
            if not stop_ids:
                state["error"] = "missing_stop_ids"
                state["message"] = "Stop IDs list is required"
                return state
            result = await tool_update_path_stops(path_id, stop_ids, user_id)
            state["message"] = result.get("message") if result.get("ok") else result.get("error")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "validate_route":
            from langgraph.tools import tool_validate_route
            parsed_params = state.get("parsed_params", {})
            route_id = parsed_params.get("route_id") or state.get("route_id")
            if not route_id:
                state["error"] = "missing_route_id"
                state["message"] = "Route ID is required"
                return state
            result = await tool_validate_route(route_id)
            if result.get("ok"):
                state["final_output"] = {"type": "object", "data": result.get("result", {})}
                state["message"] = result.get("message", "Route validated")
            else:
                state["message"] = result.get("error", "Failed to validate route")
                state["status"] = "failed"
        
        # ========== TRIP SCHEDULING ACTIONS ==========
        elif action == "delay_trip":
            from langgraph.tools import tool_delay_trip
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            delay_minutes = parsed_params.get("delay_minutes", 15)  # Default 15 minutes
            reason = parsed_params.get("reason", "Delayed by operator")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            result = await tool_delay_trip(trip_id, delay_minutes, reason)
            state["message"] = result.get("message") if result.get("ok") else result.get("error")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        elif action == "reschedule_trip":
            from langgraph.tools import tool_reschedule_trip
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            new_time = parsed_params.get("new_time")
            new_date = parsed_params.get("new_date")
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required"
                return state
            if not new_time and not new_date:
                state["error"] = "missing_schedule"
                state["message"] = "Please specify new time (HH:MM) or new date (YYYY-MM-DD)"
                return state
            result = await tool_reschedule_trip(trip_id, new_time, new_date)
            state["message"] = result.get("message") if result.get("ok") else result.get("error")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        # ========== FLEET MANAGEMENT ACTIONS ==========
        elif action == "add_vehicle":
            from langgraph.tools import tool_add_vehicle
            parsed_params = state.get("parsed_params", {})
            registration_number = parsed_params.get("registration_number") or parsed_params.get("vehicle_registration")
            vehicle_type = parsed_params.get("vehicle_type")
            capacity = parsed_params.get("capacity")
            
            # Check if we're continuing a wizard
            wizard_data = state.get("wizard_data", {})
            wizard_step = state.get("wizard_step", 0)
            
            if state.get("wizard_active") and state.get("wizard_type") == "add_vehicle":
                # We're in a wizard flow - merge wizard data
                registration_number = registration_number or wizard_data.get("registration_number")
                vehicle_type = vehicle_type or wizard_data.get("vehicle_type")
                capacity = capacity or wizard_data.get("capacity")
                
                # User is providing input for current step
                user_text = state.get("text", "").strip().upper()
                
                if wizard_step == 1:
                    # Step 1: Expecting vehicle type (Bus/Cab)
                    if user_text in ["BUS", "CAB"]:
                        vehicle_type = user_text.capitalize()  # "Bus" or "Cab"
                        wizard_data["vehicle_type"] = vehicle_type
                        # Move to step 2: Ask for capacity
                        state["wizard_active"] = True
                        state["wizard_type"] = "add_vehicle"
                        state["wizard_step"] = 2
                        state["wizard_steps_total"] = 3
                        state["wizard_data"] = wizard_data
                        state["status"] = "wizard_step"
                        state["message"] = f"Got it! {vehicle_type}. Now, what is the seating capacity?"
                        state["suggestions"] = ["20", "30", "40", "50"]
                        return state
                    else:
                        # Invalid input, ask again
                        state["wizard_active"] = True
                        state["wizard_type"] = "add_vehicle"
                        state["wizard_step"] = 1
                        state["wizard_steps_total"] = 3
                        state["wizard_data"] = wizard_data
                        state["status"] = "wizard_step"
                        state["message"] = "Please select a valid vehicle type: Bus or Cab"
                        state["suggestions"] = ["Bus", "Cab"]
                        return state
                
                elif wizard_step == 2:
                    # Step 2: Expecting capacity
                    try:
                        capacity = int(user_text) if user_text.isdigit() else int(state.get("text", "40"))
                        if capacity < 1 or capacity > 100:
                            raise ValueError("Capacity out of range")
                        wizard_data["capacity"] = capacity
                        # All data collected, execute!
                    except ValueError:
                        # Invalid input, ask again
                        state["wizard_active"] = True
                        state["wizard_type"] = "add_vehicle"
                        state["wizard_step"] = 2
                        state["wizard_steps_total"] = 3
                        state["wizard_data"] = wizard_data
                        state["status"] = "wizard_step"
                        state["message"] = "Please enter a valid capacity (1-100)"
                        state["suggestions"] = ["20", "30", "40", "50"]
                        return state
            
            # Check what info we're missing and start wizard if needed
            if not registration_number:
                state["error"] = "missing_registration"
                state["message"] = "Vehicle registration number is required. Please say something like 'Add vehicle MH-12-AB-1234'"
                return state
            
            # We have registration but missing type or capacity - start wizard
            if not vehicle_type:
                # Start wizard at step 1: Ask for vehicle type
                state["wizard_active"] = True
                state["wizard_type"] = "add_vehicle"
                state["wizard_step"] = 1
                state["wizard_steps_total"] = 3
                state["wizard_data"] = {
                    "registration_number": registration_number
                }
                state["status"] = "wizard_step"
                state["message"] = f"Adding vehicle **{registration_number}**. What type of vehicle is it?"
                state["suggestions"] = ["Bus", "Cab"]
                logger.info(f"[EXECUTE] Starting add_vehicle wizard for {registration_number}")
                return state
            
            if not capacity:
                # Start wizard at step 2: Ask for capacity (we have registration and type)
                state["wizard_active"] = True
                state["wizard_type"] = "add_vehicle"
                state["wizard_step"] = 2
                state["wizard_steps_total"] = 3
                state["wizard_data"] = {
                    "registration_number": registration_number,
                    "vehicle_type": vehicle_type
                }
                state["status"] = "wizard_step"
                state["message"] = f"Got it! {vehicle_type}. What is the seating capacity?"
                state["suggestions"] = ["20", "30", "40", "50"]
                return state
            
            # All data present - execute the action
            result = await tool_add_vehicle(registration_number, vehicle_type, capacity)
            if result.get("ok"):
                state["message"] = f"✅ Vehicle **{registration_number}** ({vehicle_type}, {capacity} seats) added successfully!"
                state["wizard_completed"] = True
                state["status"] = "completed"
            else:
                state["message"] = result.get("error", "Failed to add vehicle")
                state["status"] = "failed"
        
        elif action == "add_driver":
            from langgraph.tools import tool_add_driver
            parsed_params = state.get("parsed_params", {})
            name = parsed_params.get("driver_name") or parsed_params.get("name")
            phone = parsed_params.get("phone")
            license_number = parsed_params.get("license_number")
            if not name:
                state["error"] = "missing_name"
                state["message"] = "Driver name is required"
                return state
            result = await tool_add_driver(name, phone, license_number)
            state["message"] = result.get("message") if result.get("ok") else result.get("error")
            state["status"] = "completed" if result.get("ok") else "failed"
        
        # ========== COMPOUND ACTIONS ==========
        elif action == "assign_vehicle_and_driver":
            # Execute both vehicle and driver assignment in sequence
            trip_id = state.get("trip_id")
            parsed_params = state.get("parsed_params", {})
            vehicle_reg = parsed_params.get("vehicle_registration")
            driver_name = parsed_params.get("driver_name")
            
            logger.info(f"[EXECUTE] Compound action: assign vehicle '{vehicle_reg}' and driver '{driver_name}' to trip {trip_id}")
            
            if not trip_id:
                state["error"] = "missing_trip_id"
                state["message"] = "Trip ID is required for assignment"
                state["status"] = "failed"
                return state
            
            if not vehicle_reg:
                state["error"] = "missing_vehicle"
                state["message"] = "Vehicle registration is required"
                state["status"] = "failed"
                return state
            
            if not driver_name:
                state["error"] = "missing_driver"
                state["message"] = "Driver name is required"
                state["status"] = "failed"
                return state
            
            # Step 1: Find and assign the vehicle
            # Note: tool_assign_vehicle and tool_assign_driver are imported at the top of the file
            from app.core.supabase_client import get_conn
            
            # Look up vehicle by registration
            pool = await get_conn()
            async with pool.acquire() as conn:
                vehicle = await conn.fetchrow("""
                    SELECT vehicle_id, registration_number FROM vehicles 
                    WHERE LOWER(registration_number) = LOWER($1)
                """, vehicle_reg)
                
                if not vehicle:
                    state["error"] = "vehicle_not_found"
                    state["message"] = f"Vehicle '{vehicle_reg}' not found in the fleet"
                    state["status"] = "failed"
                    return state
                
                vehicle_id = vehicle["vehicle_id"]
                
                # Look up driver by name
                driver = await conn.fetchrow("""
                    SELECT driver_id, name FROM drivers 
                    WHERE LOWER(name) LIKE LOWER($1)
                """, f"%{driver_name}%")
                
                if not driver:
                    state["error"] = "driver_not_found"
                    state["message"] = f"Driver '{driver_name}' not found"
                    state["status"] = "failed"
                    return state
                
                driver_id = driver["driver_id"]
                actual_driver_name = driver["name"]
            
            # Use tool_assign_vehicle which already handles both vehicle AND driver assignment
            result = await tool_assign_vehicle(trip_id, vehicle_id, driver_id, state.get("user_id", 1))
            if not result.get("ok"):
                state["error"] = "assignment_failed"
                state["message"] = f"Failed to assign vehicle and driver: {result.get('message', 'Unknown error')}"
                state["status"] = "failed"
                return state
            
            # Success!
            state["message"] = f"✅ Successfully assigned vehicle **{vehicle_reg}** and driver **{actual_driver_name}** to trip {trip_id}"
            state["status"] = "completed"
            logger.info(f"[EXECUTE] Compound assignment successful for trip {trip_id}")
        
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
