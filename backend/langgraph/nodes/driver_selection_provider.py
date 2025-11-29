"""
Driver Selection Provider Node
Provides list of available drivers for assignment to a trip.
"""
from typing import Dict, Any, List
import logging
from langgraph.tools import tool_list_available_drivers

logger = logging.getLogger(__name__)


async def driver_selection_provider(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provides a list of available drivers for assignment to a trip.
    
    Driver availability logic:
    - Driver is available if not assigned to any conflicting trip
    - Conflicts are trips within 90 minutes of the target trip time
    - Shows driver status and availability reason
    
    Returns options list for user selection.
    """
    
    trip_id = state.get("trip_id")
    trip_label = state.get("trip_label", f"Trip {trip_id}")
    
    logger.info(f"Providing driver selection for trip: {trip_label} (ID: {trip_id})")
    
    if not trip_id:
        state["error"] = "missing_trip_id"
        state["message"] = "I need to know which trip you want to assign a driver to. Please select a trip first."
        state["next_node"] = "report_result"
        return state
    
    try:
        # Get available drivers for this trip
        result = await tool_list_available_drivers(trip_id)
        
        if not result.get("ok"):
            state["error"] = "driver_lookup_failed"
            state["message"] = f"I couldn't get the list of available drivers: {result.get('message', 'Unknown error')}"
            state["next_node"] = "report_result"
            return state
        
        available_drivers = result.get("result", [])
        
        if not available_drivers:
            state["error"] = "no_available_drivers"
            state["message"] = f"No drivers are available for {trip_label} at this time. All drivers may be assigned to other trips."
            state["next_node"] = "report_result"
            return state
        
        # Format driver options
        options = []
        for driver in available_drivers:
            option = {
                "driver_id": driver["driver_id"],
                "driver_name": driver["driver_name"],
                "status": driver.get("status", "available"),
                "reason": driver.get("reason", "Available for assignment"),
                "phone": driver.get("phone", ""),
                "label": f"👤 {driver['driver_name']}",
                "description": driver.get("reason", "Available for assignment")
            }
            options.append(option)
        
        # Set state for driver selection
        state["options"] = options
        state["suggestions"] = options  # ✅ FIX: Set suggestions for final_output
        state["selection_type"] = "driver"
        state["awaiting_selection"] = True
        state["status"] = "options_provided"
        state["next_node"] = "report_result"
        
        # ✅ FIX: Set final_output suggestions
        if "final_output" not in state:
            state["final_output"] = {}
        state["final_output"]["suggestions"] = options
        
        # Create user-friendly message
        driver_list = "\n".join([
            f"**{i+1}.** {opt['driver_name']} - {opt['description']}" 
            for i, opt in enumerate(options)
        ])
        
        state["message"] = f"**Available drivers for {trip_label}:**\n\n{driver_list}\n\nPlease choose a driver by name or number (e.g., \"Choose driver 1\" or \"Assign Amit\")."
        
        logger.info(f"Provided {len(options)} available drivers for trip {trip_id}")
        
    except Exception as e:
        logger.error(f"Error in driver_selection_provider: {str(e)}")
        state["error"] = "driver_selection_failed"
        state["message"] = f"I encountered an error while getting available drivers: {str(e)}"
        state["next_node"] = "report_result"
    
    return state
