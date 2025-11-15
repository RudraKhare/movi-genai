"""
Vehicle Selection Provider Node
Fetches available vehicles and drivers for assignment
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def vehicle_selection_provider(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provides list of available vehicles and drivers for user to choose from.
    
    This node is triggered when:
    - User wants to assign_vehicle but hasn't specified which one
    - clarify=True and parameters are missing
    
    Returns options in a selectable format for frontend
    """
    
    trip_id = state.get("trip_id")
    action = state.get("action")
    
    logger.info(f"Fetching vehicle options for action: {action}, trip: {trip_id}")
    
    # Fetch unassigned vehicles
    try:
        from langgraph.tools import tool_get_unassigned_vehicles
        vehicles_result = await tool_get_unassigned_vehicles()
        
        logger.info(f"Vehicles result: {vehicles_result}")
        
        if not vehicles_result.get("ok"):
            state["message"] = "❌ Unable to fetch available vehicles"
            state["status"] = "failed"
            return state
        
        vehicles = vehicles_result.get("result", [])  # ✅ FIX: Use 'result' not 'data'
        logger.info(f"Found {len(vehicles)} unassigned vehicles")
        
        if not vehicles:
            state["message"] = ("⚠️ No unassigned vehicles available right now.\n\n"
                              "All vehicles are currently deployed to active trips. You can:\n"
                              "• Remove a vehicle from another trip first\n"
                              "• Wait for a trip to complete\n"
                              "• Add a new vehicle to the system")
            state["status"] = "no_options"
            state["success"] = True  # Not an error, just no options
            state["suggestions"] = [
                {
                    "action": "get_unassigned_vehicles",
                    "label": "📋 View All Vehicles",
                    "description": "See all vehicles and their deployment status"
                },
                {
                    "action": "cancel",
                    "label": "❌ Cancel",
                    "description": "Go back without making changes"
                }
            ]
            return state
        
        # Build message
        state["message"] = f"📋 Found {len(vehicles)} available vehicle(s).\n\nWhich vehicle would you like to assign to trip {trip_id}?"
        
        # Build options for frontend
        options = []
        for vehicle in vehicles[:10]:  # Limit to 10 for UI
            vehicle_id = vehicle.get("vehicle_id")
            reg_num = vehicle.get("registration_number", "Unknown")
            capacity = vehicle.get("capacity", "?")
            driver_name = vehicle.get("driver_name", "No driver")
            driver_id = vehicle.get("driver_id")
            
            option_label = f"🚗 {reg_num}"
            option_desc = f"{capacity} seats"
            if driver_name and driver_name != "No driver":
                option_desc += f" • 👤 {driver_name}"
            
            options.append({
                "id": vehicle_id,
                "label": option_label,
                "description": option_desc,
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "registration_number": reg_num,
                "capacity": capacity,
                "driver_name": driver_name
            })
        
        state["options"] = options
        state["awaiting_selection"] = True
        state["selection_type"] = "vehicle"
        state["status"] = "options_provided"
        state["next_node"] = "report_result"
        
        logger.info(f"Provided {len(options)} vehicle options")
        
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}", exc_info=True)
        state["message"] = f"❌ Error fetching vehicles: {str(e)}"
        state["status"] = "failed"
    
    return state
