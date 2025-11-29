"""
Suggestion Provider Node
Shows contextual actions for existing trips/entities.
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


async def suggestion_provider(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provides suggestions for what the user can do with an existing trip.
    
    Returns a list of action options based on trip state:
    - Has vehicle? → Remove vehicle
    - No vehicle? → Assign vehicle
    - Has bookings? → View bookings, Cancel (with warning)
    - Always → View details, View status, Duplicate, etc.
    """
    
    trip_id = state.get("trip_id")
    trip_details = state.get("trip_details", {})
    display_name = trip_details.get("display_name") or state.get("target_label", f"Trip {trip_id}")
    
    logger.info(f"Providing suggestions for trip: {display_name}")
    
    # Base message
    state["message"] = f"I found **{display_name}**.\n\nWhat would you like to do?"
    
    # Build suggestions based on trip state
    suggestions = []
    
    # Vehicle management - Enhanced logic
    has_vehicle = trip_details.get("vehicle_id")
    has_driver = trip_details.get("driver_id")
    
    if has_vehicle:
        # Trip has vehicle → offer to remove it
        suggestions.append({
            "action": "remove_vehicle",
            "label": "🚫 Remove Vehicle",
            "description": f"Remove {trip_details.get('registration_number', 'vehicle')} from this trip"
        })
    elif has_driver:
        # ✅ FIX: Trip has driver but no vehicle → hide "assign vehicle"
        # Don't offer vehicle assignment if driver is already assigned
        # This prevents the "Trip already has deployment" error
        logger.info(f"Trip has driver but no vehicle - not offering vehicle assignment to prevent deployment conflict")
    else:
        # No vehicle and no driver → offer vehicle assignment
        suggestions.append({
            "action": "assign_vehicle",
            "label": "🚗 Assign Vehicle",
            "description": "Assign a vehicle and driver to deploy this trip"
        })
    
    # Driver management - Enhanced for separate driver assignment
    if has_driver:
        suggestions.append({
            "action": "change_driver",
            "label": "👤 Change Driver",
            "description": f"Change driver from {trip_details.get('driver_name', 'current driver')}"
        })
    else:
        # No driver assigned - offer driver assignment
        suggestions.append({
            "action": "assign_driver",
            "label": "👤 Assign Driver",
            "description": "Assign a driver to this trip"
        })
    
    # Vehicle and driver combo (if neither assigned)
    if not has_vehicle and not has_driver:
        suggestions.append({
            "action": "assign_vehicle",
            "label": "🚗 Assign Vehicle & Driver",
            "description": "Assign both vehicle and driver together"
        })
    
    # Booking management
    booking_count = trip_details.get("booking_count", 0)
    if booking_count > 0:
        suggestions.append({
            "action": "get_trip_bookings",
            "label": "👥 View Bookings",
            "description": f"View {booking_count} confirmed bookings"
        })
    
    # Status and details (always available)
    suggestions.extend([
        {
            "action": "get_trip_status",
            "label": "ℹ️ View Status",
            "description": "View current trip status and live updates"
        },
        {
            "action": "get_trip_details",
            "label": "📋 View Details",
            "description": "View comprehensive trip information"
        }
    ])
    
    # Path and route
    if trip_details.get("route_name"):
        suggestions.extend([
            {
                "action": "list_path_stops",
                "label": "📍 View Stops",
                "description": f"View stops for {trip_details.get('path_name', 'this path')}"
            },
            {
                "action": "list_routes_using_path",
                "label": "🛣️ View Routes",
                "description": "View all routes using this path"
            }
        ])
    
    # Time management (only for scheduled trips)
    if trip_details.get("live_status") == "scheduled":
        suggestions.append({
            "action": "update_trip_time",
            "label": "⏰ Delay Trip",
            "description": "Change scheduled departure time"
        })
    
    # Duplication and creation
    suggestions.extend([
        {
            "action": "duplicate_trip",
            "label": "📑 Duplicate Trip",
            "description": "Create a copy of this trip for another date"
        },
        {
            "action": "create_followup_trip",
            "label": "➕ Create Follow-up",
            "description": "Create a follow-up trip after this one"
        }
    ])
    
    # Cancellation (always available, but warn if bookings)
    cancel_label = "🗑️ Cancel Trip"
    cancel_desc = "Cancel this trip"
    cancel_warning = False
    
    if booking_count > 0:
        cancel_desc = f"Cancel trip (⚠️ Will affect {booking_count} confirmed bookings)"
        cancel_warning = True
    
    suggestions.append({
        "action": "cancel_trip",
        "label": cancel_label,
        "description": cancel_desc,
        "warning": cancel_warning
    })
    
    # Set suggestions in state
    state["suggestions"] = suggestions
    state["awaiting_user_selection"] = True
    state["status"] = "suggestions_provided"
    state["next_node"] = "report_result"
    
    logger.info(f"Provided {len(suggestions)} suggestions for trip {trip_id}")
    
    return state
