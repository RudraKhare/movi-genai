"""
LangGraph Tools Package
Contains utility functions and LLM clients for the agent
"""

# Import directly from the tools.py file using importlib to avoid circular import
import importlib.util
import os

# Get the path to the tools.py file (sibling of this directory)
tools_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools.py')

# Load the tools.py module directly
spec = importlib.util.spec_from_file_location("langgraph_tools_module", tools_file_path)
tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools_module)

# Re-export all tool functions
tool_get_trip_status = tools_module.tool_get_trip_status
tool_get_bookings = tools_module.tool_get_bookings
tool_assign_vehicle = tools_module.tool_assign_vehicle
tool_remove_vehicle = tools_module.tool_remove_vehicle
tool_cancel_trip = tools_module.tool_cancel_trip
tool_identify_trip_from_label = tools_module.tool_identify_trip_from_label
tool_get_vehicles = tools_module.tool_get_vehicles
tool_get_drivers = tools_module.tool_get_drivers

# New tools for 16 actions
tool_get_unassigned_vehicles = tools_module.tool_get_unassigned_vehicles
tool_get_trip_details = tools_module.tool_get_trip_details
tool_list_all_stops = tools_module.tool_list_all_stops
tool_list_stops_for_path = tools_module.tool_list_stops_for_path
tool_list_routes_using_path = tools_module.tool_list_routes_using_path
tool_create_stop = tools_module.tool_create_stop
tool_create_path = tools_module.tool_create_path
tool_create_route = tools_module.tool_create_route
tool_update_trip_time = tools_module.tool_update_trip_time
tool_rename_stop = tools_module.tool_rename_stop
tool_duplicate_route = tools_module.tool_duplicate_route
tool_get_path_by_label = tools_module.tool_get_path_by_label
tool_get_route_by_label = tools_module.tool_get_route_by_label

# Phase 3: Wizard support tools
tool_get_available_vehicles = tools_module.tool_get_available_vehicles
tool_get_available_drivers = tools_module.tool_get_available_drivers
tool_get_all_paths = tools_module.tool_get_all_paths
tool_get_all_routes = tools_module.tool_get_all_routes

# Make these available for import
__all__ = [
    'tool_get_trip_status',
    'tool_get_bookings',
    'tool_assign_vehicle',
    'tool_remove_vehicle',
    'tool_cancel_trip',
    'tool_identify_trip_from_label',
    'tool_get_vehicles',
    'tool_get_drivers',
    'tool_get_unassigned_vehicles',
    'tool_get_trip_details',
    'tool_list_all_stops',
    'tool_list_stops_for_path',
    'tool_list_routes_using_path',
    'tool_create_stop',
    'tool_create_path',
    'tool_create_route',
    'tool_update_trip_time',
    'tool_rename_stop',
    'tool_duplicate_route',
    'tool_get_path_by_label',
    'tool_get_route_by_label',
    # Phase 3: Wizard support tools
    'tool_get_available_vehicles',
    'tool_get_available_drivers',
    'tool_get_all_paths',
    'tool_get_all_routes',
]

