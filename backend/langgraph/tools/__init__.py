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
tool_assign_driver = tools_module.tool_assign_driver
tool_list_available_drivers = tools_module.tool_list_available_drivers
tool_remove_vehicle = tools_module.tool_remove_vehicle
tool_remove_driver = tools_module.tool_remove_driver
tool_cancel_trip = tools_module.tool_cancel_trip
tool_identify_trip_from_label = tools_module.tool_identify_trip_from_label
tool_get_vehicles = tools_module.tool_get_vehicles
tool_get_drivers = tools_module.tool_get_drivers
tool_find_driver_by_name = tools_module.tool_find_driver_by_name

# New tools for 16 actions
tool_get_unassigned_vehicles = tools_module.tool_get_unassigned_vehicles
tool_get_available_vehicles_for_trip = tools_module.tool_get_available_vehicles_for_trip
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
tool_update_trip_status = tools_module.tool_update_trip_status

# Dashboard Intelligence tools
tool_get_trips_needing_attention = tools_module.tool_get_trips_needing_attention
tool_get_today_summary = tools_module.tool_get_today_summary
tool_get_recent_changes = tools_module.tool_get_recent_changes
tool_get_high_demand_offices = tools_module.tool_get_high_demand_offices
tool_get_most_used_vehicles = tools_module.tool_get_most_used_vehicles

# Vehicle Management tools
tool_get_vehicle_status = tools_module.tool_get_vehicle_status
tool_block_vehicle = tools_module.tool_block_vehicle
tool_unblock_vehicle = tools_module.tool_unblock_vehicle
tool_get_vehicle_trips_today = tools_module.tool_get_vehicle_trips_today
tool_recommend_vehicle_for_trip = tools_module.tool_recommend_vehicle_for_trip

# Driver Management tools
tool_get_driver_status = tools_module.tool_get_driver_status
tool_get_driver_trips_today = tools_module.tool_get_driver_trips_today
tool_set_driver_availability = tools_module.tool_set_driver_availability

# Booking Management tools
tool_get_booking_count = tools_module.tool_get_booking_count
tool_check_seat_availability = tools_module.tool_check_seat_availability
tool_add_bookings = tools_module.tool_add_bookings
tool_reduce_bookings = tools_module.tool_reduce_bookings
tool_get_trip_stops = tools_module.tool_get_trip_stops
tool_list_passengers = tools_module.tool_list_passengers
tool_cancel_all_bookings = tools_module.tool_cancel_all_bookings
tool_find_employee_trips = tools_module.tool_find_employee_trips

# Smart Automation tools
tool_check_trip_readiness = tools_module.tool_check_trip_readiness
tool_detect_overbooking = tools_module.tool_detect_overbooking
tool_predict_problem_trips = tools_module.tool_predict_problem_trips
tool_suggest_alternate_vehicle = tools_module.tool_suggest_alternate_vehicle

# Stop/Path/Route Management tools
tool_delete_stop = tools_module.tool_delete_stop
tool_update_path_stops = tools_module.tool_update_path_stops
tool_delete_path = tools_module.tool_delete_path
tool_delete_route = tools_module.tool_delete_route
tool_validate_route = tools_module.tool_validate_route

# System tools
tool_simulate_action = tools_module.tool_simulate_action
tool_explain_decision = tools_module.tool_explain_decision

# Trip Scheduling tools
tool_delay_trip = tools_module.tool_delay_trip
tool_reschedule_trip = tools_module.tool_reschedule_trip

# Fleet Management tools
tool_add_vehicle = tools_module.tool_add_vehicle
tool_add_driver = tools_module.tool_add_driver

# Make these available for import
__all__ = [
    'tool_get_trip_status',
    'tool_get_bookings',
    'tool_assign_vehicle',
    'tool_assign_driver',
    'tool_remove_vehicle',
    'tool_remove_driver',
    'tool_cancel_trip',
    'tool_update_trip_status',
    'tool_identify_trip_from_label',
    'tool_get_vehicles',
    'tool_get_drivers',
    'tool_find_driver_by_name',
    'tool_get_unassigned_vehicles',
    'tool_get_available_vehicles_for_trip',
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
    'tool_list_available_drivers',
    # Dashboard Intelligence
    'tool_get_trips_needing_attention',
    'tool_get_today_summary',
    'tool_get_recent_changes',
    'tool_get_high_demand_offices',
    'tool_get_most_used_vehicles',
    # Vehicle Management
    'tool_get_vehicle_status',
    'tool_block_vehicle',
    'tool_unblock_vehicle',
    'tool_get_vehicle_trips_today',
    'tool_recommend_vehicle_for_trip',
    # Driver Management
    'tool_get_driver_status',
    'tool_get_driver_trips_today',
    'tool_set_driver_availability',
    # Booking Management
    'tool_get_booking_count',
    'tool_check_seat_availability',
    'tool_add_bookings',
    'tool_reduce_bookings',
    'tool_get_trip_stops',
    'tool_list_passengers',
    'tool_cancel_all_bookings',
    'tool_find_employee_trips',
    # Smart Automation
    'tool_check_trip_readiness',
    'tool_detect_overbooking',
    'tool_predict_problem_trips',
    'tool_suggest_alternate_vehicle',
    # Stop/Path/Route Management
    'tool_delete_stop',
    'tool_update_path_stops',
    'tool_delete_path',
    'tool_delete_route',
    'tool_validate_route',
    # System
    'tool_simulate_action',
    'tool_explain_decision',
    # Trip Scheduling
    'tool_delay_trip',
    'tool_reschedule_trip',
    # Fleet Management
    'tool_add_vehicle',
    'tool_add_driver',
]

