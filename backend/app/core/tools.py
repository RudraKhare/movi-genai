# backend/app/core/tools.py
"""
Export lightweight function references that LangGraph can import as tools.
These are thin wrappers that call service functions and return serializable dicts.

LangGraph Integration Notes:
----------------------------
These tools are designed to be called directly by LangGraph nodes. Each function:
- Is async and returns JSON-serializable dictionaries
- Has clear input/output contracts
- Handles errors by raising ServiceError (which LangGraph should catch)

Recommended LangGraph Flow:
1. check_consequences node: calls get_trip_consequences()
2. If consequences exist (bookings > 0): route to get_confirmation node
3. If no consequences: route to execute_action node
4. execute_action: calls assign_vehicle/remove_vehicle/cancel_trip

Example LangGraph node:
    async def check_consequences_node(state: GraphState):
        trip_id = state["trip_id"]
        consequences = await TOOLS["get_trip_consequences"](trip_id)
        
        if consequences.get("has_bookings"):
            # Route to confirmation
            return {"consequences": consequences, "needs_confirmation": True}
        else:
            # Safe to proceed
            return {"consequences": consequences, "needs_confirmation": False}
"""
from .service import assign_vehicle, remove_vehicle, cancel_trip, get_trip_info
from .consequences import (
    get_trip_consequences, 
    get_vehicle_capacity,
    check_vehicle_availability,
    check_driver_availability
)
from typing import Dict, Callable, Any


# Main tool map for LangGraph
TOOLS: Dict[str, Callable] = {
    # Consequence checking (read-only, safe to call anytime)
    "get_trip_consequences": get_trip_consequences,
    "get_trip_info": get_trip_info,  # Alias for consistency
    "get_vehicle_capacity": get_vehicle_capacity,
    "check_vehicle_availability": check_vehicle_availability,
    "check_driver_availability": check_driver_availability,
    
    # Mutating operations (require confirmation if consequences exist)
    "assign_vehicle": assign_vehicle,
    "remove_vehicle": remove_vehicle,
    "cancel_trip": cancel_trip,
}


# Tool metadata for LangGraph (optional, helps with documentation)
TOOL_METADATA = {
    "get_trip_consequences": {
        "description": "Get detailed consequences of modifying a trip (bookings, deployment)",
        "parameters": ["trip_id: int"],
        "returns": "Dict with booked_count, seats_booked, has_deployment, etc.",
        "side_effects": False,
    },
    "get_vehicle_capacity": {
        "description": "Get the seating capacity of a vehicle",
        "parameters": ["vehicle_id: int"],
        "returns": "int (capacity) or None if not found",
        "side_effects": False,
    },
    "check_vehicle_availability": {
        "description": "Check if vehicle is available on a date",
        "parameters": ["vehicle_id: int", "trip_date: str (YYYY-MM-DD)"],
        "returns": "bool (True if available)",
        "side_effects": False,
    },
    "check_driver_availability": {
        "description": "Check if driver is available on a date",
        "parameters": ["driver_id: int", "trip_date: str (YYYY-MM-DD)"],
        "returns": "bool (True if available)",
        "side_effects": False,
    },
    "assign_vehicle": {
        "description": "Assign vehicle and driver to a trip (transactional)",
        "parameters": ["trip_id: int", "vehicle_id: int", "driver_id: int", "user_id: int"],
        "returns": "Dict with ok, trip_id, vehicle_id, driver_id, deployment_id",
        "side_effects": True,
        "requires_confirmation": "If trip has existing bookings",
    },
    "remove_vehicle": {
        "description": "Remove vehicle deployment from trip (transactional)",
        "parameters": ["trip_id: int", "user_id: int", "cancel_bookings: bool = True"],
        "returns": "Dict with ok, trip_id, vehicle_id, bookings_cancelled",
        "side_effects": True,
        "requires_confirmation": "If cancel_bookings=True and bookings exist",
    },
    "cancel_trip": {
        "description": "Cancel a trip and all its bookings (transactional)",
        "parameters": ["trip_id: int", "user_id: int"],
        "returns": "Dict with ok, trip_id, bookings_cancelled",
        "side_effects": True,
        "requires_confirmation": "Always (cancels bookings)",
    },
}


def get_tool(tool_name: str) -> Callable:
    """
    Get a tool function by name.
    
    Args:
        tool_name: Name of the tool (key in TOOLS dict)
        
    Returns:
        The callable tool function
        
    Raises:
        KeyError: If tool_name not found
    """
    return TOOLS[tool_name]


def list_tools() -> list[str]:
    """
    Get list of all available tool names.
    
    Returns:
        List of tool names
    """
    return list(TOOLS.keys())


def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """
    Get metadata about a tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Dictionary with description, parameters, returns, side_effects
    """
    return TOOL_METADATA.get(tool_name, {})
