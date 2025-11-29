"""
LangGraph Tool Wrappers for MOVI Agent
Wraps backend service functions and Supabase connections for agent use
"""
from app.core import service
from app.core.supabase_client import get_conn
from typing import Dict, List, Optional
from datetime import datetime, timedelta, time as dt_time
import logging

logger = logging.getLogger(__name__)


# === Tool Wrappers for Agent ===

async def tool_get_trip_status(trip_id: int) -> Dict:
    """
    Get current status of a trip including bookings and deployments.
    
    Args:
        trip_id: The trip ID to query
        
    Returns:
        Dictionary with trip status details
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT 
                    trip_id,
                    display_name,
                    booking_status_percentage,
                    live_status,
                    trip_date
                FROM daily_trips 
                WHERE trip_id = $1
            """, trip_id)
            
            if not result:
                return {}
            
            trip_data = dict(result)
            
            # Get deployment info
            deployment = await conn.fetchrow("""
                SELECT vehicle_id, driver_id, deployment_id
                FROM deployments
                WHERE trip_id = $1
            """, trip_id)
            
            if deployment:
                trip_data.update({
                    "vehicle_id": deployment["vehicle_id"],
                    "driver_id": deployment["driver_id"],
                    "deployment_id": deployment["deployment_id"]
                })
            
            return trip_data
            
    except Exception as e:
        logger.error(f"Error getting trip status: {e}")
        return {}


async def tool_get_bookings(trip_id: int) -> List[Dict]:
    """
    Get all ACTIVE bookings for a specific trip.
    Excludes cancelled bookings since they don't affect operations.
    
    Args:
        trip_id: The trip ID to query
        
    Returns:
        List of booking dictionaries (active only)
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    booking_id,
                    trip_id,
                    user_name,
                    seats,
                    status,
                    created_at
                FROM bookings 
                WHERE trip_id = $1
                  AND status != 'CANCELLED'
                ORDER BY created_at DESC
            """, trip_id)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        return []


async def tool_assign_vehicle(
    trip_id: int, 
    vehicle_id: int, 
    driver_id: int, 
    user_id: int
) -> Dict:
    """
    Assign a vehicle and driver to a trip.
    
    Args:
        trip_id: Trip to assign vehicle to
        vehicle_id: Vehicle to assign
        driver_id: Driver to assign
        user_id: User performing the action
        
    Returns:
        Result dictionary with status
    """
    try:
        await service.assign_vehicle(trip_id, vehicle_id, driver_id, user_id)
        return {
            "ok": True, 
            "message": f"Vehicle {vehicle_id} and driver {driver_id} assigned to trip {trip_id}",
            "action": "assign_vehicle"
        }
    except Exception as e:
        logger.error(f"Error assigning vehicle: {e}")
        return {
            "ok": False,
            "message": f"Failed to assign vehicle: {str(e)}",
            "action": "assign_vehicle"
        }


async def tool_assign_driver(trip_id: int, driver_id: int, user_id: int) -> Dict:
    """
    Assign a driver to a trip (keeping existing vehicle assignment if any).
    
    Args:
        trip_id: Trip to assign driver to
        driver_id: Driver to assign
        user_id: User performing the action
        
    Returns:
        Result dictionary with status
    """
    try:
        await service.assign_driver(trip_id, driver_id, user_id)
        return {
            "ok": True, 
            "message": f"Driver {driver_id} assigned to trip {trip_id}",
            "action": "assign_driver"
        }
    except Exception as e:
        logger.error(f"Error assigning driver: {e}")
        return {
            "ok": False,
            "message": f"Failed to assign driver: {str(e)}",
            "action": "assign_driver"
        }


async def tool_remove_vehicle(trip_id: int, user_id: int) -> Dict:
    """
    Remove vehicle assignment from a trip.
    
    Args:
        trip_id: Trip to remove vehicle from
        user_id: User performing the action
        
    Returns:
        Result dictionary with status
    """
    try:
        await service.remove_vehicle(trip_id, user_id)
        return {
            "ok": True, 
            "message": f"Vehicle removed from trip {trip_id}",
            "action": "remove_vehicle"
        }
    except Exception as e:
        logger.error(f"Error removing vehicle: {e}")
        return {
            "ok": False,
            "message": f"Failed to remove vehicle: {str(e)}",
            "action": "remove_vehicle"
        }


async def tool_remove_driver(trip_id: int, user_id: int) -> Dict:
    """
    Remove driver assignment from a trip.
    
    Args:
        trip_id: Trip to remove driver from
        user_id: User performing the action
        
    Returns:
        Result dictionary with status
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get current deployment
            deployment = await conn.fetchrow("""
                SELECT deployment_id, driver_id FROM deployments 
                WHERE trip_id = $1
            """, trip_id)
            
            if not deployment:
                return {
                    "ok": False,
                    "message": f"No deployment found for trip {trip_id}",
                    "action": "remove_driver"
                }
            
            if not deployment['driver_id']:
                return {
                    "ok": False,
                    "message": f"Trip {trip_id} has no driver assigned",
                    "action": "remove_driver"
                }
            
            # Remove driver from deployment
            await conn.execute("""
                UPDATE deployments SET driver_id = NULL WHERE trip_id = $1
            """, trip_id)
            
            logger.info(f"Removed driver from trip {trip_id} by user {user_id}")
            
            return {
                "ok": True,
                "message": f"Driver removed from trip {trip_id}",
                "action": "remove_driver"
            }
    except Exception as e:
        logger.error(f"Error removing driver: {e}")
        return {
            "ok": False,
            "message": f"Failed to remove driver: {str(e)}",
            "action": "remove_driver"
        }


async def tool_cancel_trip(trip_id: int, user_id: int) -> Dict:
    """
    Cancel a trip and handle bookings.
    
    Args:
        trip_id: Trip to cancel
        user_id: User performing the action
        
    Returns:
        Result dictionary with status
    """
    try:
        await service.cancel_trip(trip_id, user_id)
        return {
            "ok": True, 
            "message": f"Trip {trip_id} cancelled successfully",
            "action": "cancel_trip"
        }
    except Exception as e:
        logger.error(f"Error cancelling trip: {e}")
        return {
            "ok": False,
            "message": f"Failed to cancel trip: {str(e)}",
            "action": "cancel_trip"
        }


async def tool_update_trip_status(trip_id: int, new_status: str, user_id: int) -> Dict:
    """
    Manually update a trip's status.
    
    Args:
        trip_id: Trip to update
        new_status: New status (SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED)
        user_id: User performing the action
        
    Returns:
        Result dictionary with status
    """
    from app.core.status_updater import manually_update_trip_status
    
    try:
        # Validate status
        valid_statuses = ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
        status_upper = new_status.upper().replace(" ", "_")
        
        if status_upper not in valid_statuses:
            return {
                "ok": False,
                "message": f"Invalid status '{new_status}'. Valid statuses: {', '.join(valid_statuses)}",
                "action": "update_trip_status"
            }
        
        result = await manually_update_trip_status(trip_id, status_upper, user_id)
        
        if result.get("ok"):
            return {
                "ok": True,
                "message": f"Trip {trip_id} status updated to {status_upper}",
                "action": "update_trip_status"
            }
        else:
            return {
                "ok": False,
                "message": result.get("message", "Failed to update trip status"),
                "action": "update_trip_status"
            }
    except Exception as e:
        logger.error(f"Error updating trip status: {e}")
        return {
            "ok": False,
            "message": f"Failed to update trip status: {str(e)}",
            "action": "update_trip_status"
        }


async def tool_identify_trip_from_label(text: str) -> Optional[Dict]:
    """
    Find a trip by searching its display name.
    
    Args:
        text: Search text (e.g., "Bulk - 00:01")
        
    Returns:
        Trip dictionary if found, None otherwise
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Try exact match first
            result = await conn.fetchrow("""
                SELECT 
                    trip_id, 
                    display_name,
                    trip_date,
                    live_status
                FROM daily_trips 
                WHERE LOWER(display_name) = LOWER($1)
                LIMIT 1
            """, text.strip())
            
            # If no exact match, try fuzzy search
            if not result:
                result = await conn.fetchrow("""
                    SELECT 
                        trip_id, 
                        display_name,
                        trip_date,
                        live_status
                    FROM daily_trips 
                    WHERE LOWER(display_name) LIKE LOWER($1)
                    LIMIT 1
                """, f"%{text.strip()}%")
            
            return dict(result) if result else None
            
    except Exception as e:
        logger.error(f"Error identifying trip: {e}")
        return None


async def tool_get_vehicles() -> List[Dict]:
    """
    Get all available vehicles.
    
    Returns:
        List of vehicle dictionaries
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    vehicle_id,
                    registration_number,
                    vehicle_type,
                    capacity,
                    status
                FROM vehicles
                WHERE status = 'available'
                ORDER BY vehicle_type, registration_number
            """)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        return []


async def tool_get_drivers() -> List[Dict]:
    """
    Get all available drivers.
    
    Returns:
        List of driver dictionaries
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    driver_id,
                    name,
                    phone,
                    status
                FROM drivers
                WHERE status = 'available'
                ORDER BY name
            """)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting drivers: {e}")
        return []


async def tool_list_available_drivers(trip_id: int) -> Dict:
    """
    Get list of available drivers for a specific trip.
    
    A driver is available if:
    - Not assigned to any trip that has overlapping time with the target trip
    - Overlap logic: NOT (trip1_end <= trip2_start OR trip1_start >= trip2_end)
    - Uses trip time from display_name (e.g., "Path-1 - 08:00") or shift_time
    - Assumes 60-minute trip duration for overlap calculations
    
    Args:
        trip_id: ID of the trip to assign driver to
        
    Returns:
        {"ok": bool, "result": [{"driver_id": int, "driver_name": str, "status": str, "reason": str}]}
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get target trip details
            trip_row = await conn.fetchrow("""
                SELECT t.trip_date, r.shift_time, t.display_name
                FROM daily_trips t
                LEFT JOIN routes r ON t.route_id = r.route_id  
                WHERE t.trip_id = $1
            """, trip_id)
            
            if not trip_row:
                return {"ok": False, "message": f"Trip {trip_id} not found"}
            
            trip_date = trip_row["trip_date"]
            shift_time = trip_row["shift_time"] 
            display_name = trip_row["display_name"]
            
            # Extract time from display_name if shift_time is null
            target_time = shift_time
            if not target_time and display_name:
                import re
                time_match = re.search(r'(\d{1,2}:\d{2})', display_name)
                if time_match:
                    time_str = time_match.group(1)
                    # Convert to time object
                    from datetime import time
                    hour, minute = map(int, time_str.split(':'))
                    target_time = time(hour, minute)
            
            # Check if 'active' column exists, then get all drivers
            column_check = await conn.fetchrow("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'drivers' AND column_name = 'active'
                )
            """)
            
            has_active_column = column_check[0] if column_check else False
            
            if has_active_column:
                drivers = await conn.fetch("""
                    SELECT driver_id, name, phone
                    FROM drivers 
                    WHERE active = true
                    ORDER BY name
                """)
            else:
                drivers = await conn.fetch("""
                    SELECT driver_id, name, phone
                    FROM drivers 
                    ORDER BY name
                """)
            
            available_drivers = []
            
            for driver in drivers:
                driver_id = driver["driver_id"]
                driver_name = driver["name"]
                phone = driver.get("phone", "")
                
                # Check for conflicting deployments
                conflicting_trips = await conn.fetch("""
                    SELECT t.trip_id, t.display_name, r.shift_time
                    FROM deployments d
                    JOIN daily_trips t ON t.trip_id = d.trip_id
                    LEFT JOIN routes r ON t.route_id = r.route_id
                    WHERE d.driver_id = $1 
                      AND t.trip_date = $2
                      AND t.trip_id != $3
                """, driver_id, trip_date, trip_id)
                
                # Check for time conflicts using proper overlap logic
                has_conflict = False
                conflict_reason = None
                
                if target_time and conflicting_trips:
                    from datetime import datetime, timedelta, time as dt_time
                    
                    # Assume 60-minute trip duration
                    trip_duration_minutes = 60
                    
                    # Calculate target trip time window
                    base_date = datetime.combine(trip_date, target_time)
                    target_start = base_date
                    target_end = base_date + timedelta(minutes=trip_duration_minutes)
                    
                    for conflict_trip in conflicting_trips:
                        conflict_shift_time = conflict_trip["shift_time"]
                        conflict_display_name = conflict_trip["display_name"]
                        
                        # Extract time from display name if shift_time is null
                        conflict_time = conflict_shift_time
                        if not conflict_time and conflict_display_name:
                            import re
                            time_match = re.search(r'(\d{1,2}:\d{2})', conflict_display_name)
                            if time_match:
                                time_str = time_match.group(1)
                                hour, minute = map(int, time_str.split(':'))
                                conflict_time = dt_time(hour, minute)
                        
                        if conflict_time:
                            # Calculate conflict trip time window
                            conflict_date = datetime.combine(trip_date, conflict_time)
                            conflict_start = conflict_date
                            conflict_end = conflict_date + timedelta(minutes=trip_duration_minutes)
                            
                            # Check for overlap: NOT (trip1_end <= trip2_start OR trip1_start >= trip2_end)
                            # Overlaps if: trip1_end > trip2_start AND trip1_start < trip2_end
                            overlaps = (target_end > conflict_start and target_start < conflict_end)
                            
                            if overlaps:
                                has_conflict = True
                                conflict_reason = f"Busy {conflict_time.strftime('%H:%M')}-{(conflict_date + timedelta(minutes=trip_duration_minutes)).strftime('%H:%M')} ({conflict_display_name})"
                                break
                
                if has_conflict:
                    # Driver has conflict - don't include in available list for now
                    # But log for debugging
                    logger.info(f"Driver {driver_name} unavailable: {conflict_reason}")
                    continue
                else:
                    # Driver is available
                    if conflicting_trips:
                        reason = f"Free at {target_time.strftime('%H:%M') if target_time else 'this time'} (has other trips but no overlap)"
                    else:
                        reason = "Free entire shift"
                    
                    available_drivers.append({
                        "driver_id": driver_id,
                        "driver_name": driver_name,  # Use driver_name consistently
                        "phone": phone,
                        "status": "available", 
                        "reason": reason
                    })
            
            logger.info(f"Found {len(available_drivers)} available drivers for trip {trip_id} at {target_time}")
            
            return {"ok": True, "result": available_drivers}
            
    except Exception as e:
        logger.error(f"Error getting available drivers for trip {trip_id}: {str(e)}")
        return {"ok": False, "message": str(e)}


async def tool_find_driver_by_name(driver_name: str) -> Optional[Dict]:
    """
    Find a driver by name (supports partial matching).
    
    Args:
        driver_name: Driver name to search for
        
    Returns:
        Driver dictionary if found, None otherwise
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Check if 'status' column exists
            column_check = await conn.fetchrow("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'drivers' AND column_name = 'status'
                )
            """)
            
            has_status_column = column_check[0] if column_check else False
            
            if has_status_column:
                select_columns = "driver_id, name, phone, status"
            else:
                select_columns = "driver_id, name, phone"
            
            # Try exact match first
            result = await conn.fetchrow(f"""
                SELECT {select_columns}
                FROM drivers
                WHERE LOWER(name) = LOWER($1)
                LIMIT 1
            """, driver_name.strip())
            
            # If no exact match, try partial match
            if not result:
                result = await conn.fetchrow(f"""
                    SELECT {select_columns}
                    FROM drivers
                    WHERE LOWER(name) LIKE LOWER($1)
                    ORDER BY name
                    LIMIT 1
                """, f"%{driver_name.strip()}%")
            
            return dict(result) if result else None
            
    except Exception as e:
        logger.error(f"Error finding driver by name: {e}")
        return None


# ============ NEW TOOLS FOR 16 ACTIONS ============

async def tool_get_unassigned_vehicles() -> Dict:
    """Get all vehicles not currently assigned to any trip"""
    try:
        from app.core.service import get_unassigned_vehicles
        result = await get_unassigned_vehicles()
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error getting unassigned vehicles: {e}")
        return {"ok": False, "error": str(e)}


async def tool_get_available_vehicles_for_trip(trip_id: int) -> Dict:
    """Get vehicles available for a specific trip, considering time conflicts"""
    try:
        from app.core.service import get_available_vehicles_for_trip
        result = await get_available_vehicles_for_trip(trip_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error getting available vehicles for trip {trip_id}: {e}")
        return {"ok": False, "error": str(e)}


async def tool_get_trip_details(trip_id: int) -> Dict:
    """Get comprehensive trip details including bookings and deployment"""
    try:
        from app.core.service import get_trip_details
        result = await get_trip_details(trip_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error getting trip details: {e}")
        return {"ok": False, "error": str(e)}


async def tool_list_all_stops() -> Dict:
    """List all stops in the system"""
    try:
        from app.core.service import list_all_stops
        result = await list_all_stops()
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error listing stops: {e}")
        return {"ok": False, "error": str(e)}


async def tool_list_stops_for_path(path_id: int) -> Dict:
    """List all stops for a specific path in order"""
    try:
        from app.core.service import list_stops_for_path
        result = await list_stops_for_path(path_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error listing stops for path: {e}")
        return {"ok": False, "error": str(e)}


async def tool_list_routes_using_path(path_id: int) -> Dict:
    """List all routes that use a specific path"""
    try:
        from app.core.service import list_routes_using_path
        result = await list_routes_using_path(path_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error listing routes: {e}")
        return {"ok": False, "error": str(e)}


async def tool_create_stop(stop_name: str, latitude: float, longitude: float, user_id: int) -> Dict:
    """Create a new stop"""
    try:
        from app.core.service import create_stop
        result = await create_stop(stop_name, latitude, longitude, user_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error creating stop: {e}")
        return {"ok": False, "error": str(e)}


async def tool_create_path(path_name: str, stop_names: List[str], user_id: int) -> Dict:
    """Create a new path with ordered stops"""
    try:
        from app.core.service import create_path
        result = await create_path(path_name, stop_names, user_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error creating path: {e}")
        return {"ok": False, "error": str(e)}


async def tool_create_route(route_name: str, path_id: int, user_id: int) -> Dict:
    """Create a new route using an existing path"""
    try:
        from app.core.service import create_route
        result = await create_route(route_name, path_id, user_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error creating route: {e}")
        return {"ok": False, "error": str(e)}


async def tool_update_trip_time(trip_id: int, new_time: str, user_id: int) -> Dict:
    """Update trip departure time"""
    try:
        from app.core.service import update_trip_time
        result = await update_trip_time(trip_id, new_time, user_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error updating trip time: {e}")
        return {"ok": False, "error": str(e)}


async def tool_rename_stop(stop_id: int, new_name: str, user_id: int) -> Dict:
    """Rename an existing stop"""
    try:
        from app.core.service import rename_stop
        result = await rename_stop(stop_id, new_name, user_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error renaming stop: {e}")
        return {"ok": False, "error": str(e)}


async def tool_duplicate_route(route_id: int, user_id: int) -> Dict:
    """Duplicate an existing route with new path"""
    try:
        from app.core.service import duplicate_route
        result = await duplicate_route(route_id, user_id)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error(f"Error duplicating route: {e}")
        return {"ok": False, "error": str(e)}


async def tool_get_path_by_label(label: str) -> Optional[Dict]:
    """Find path by name/label"""
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT path_id, path_name, created_at
                FROM paths
                WHERE LOWER(path_name) LIKE LOWER($1)
                LIMIT 1
            """, f"%{label}%")
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error finding path: {e}")
        return None


async def tool_get_route_by_label(label: str) -> Optional[Dict]:
    """Find route by name/label"""
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT route_id, route_name, path_id, created_at
                FROM routes
                WHERE LOWER(route_name) LIKE LOWER($1)
                LIMIT 1
            """, f"%{label}%")
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error finding route: {e}")
        return None


# === NEW WIZARD SUPPORT TOOLS ===

async def tool_get_available_vehicles() -> List[Dict]:
    """
    Get all available vehicles (not currently assigned to active trips).
    Used for wizard suggestions.
    
    Returns:
        List of available vehicle dictionaries
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    v.vehicle_id,
                    v.registration_number,
                    v.capacity,
                    v.type,
                    v.status
                FROM vehicles v
                WHERE LOWER(v.status) = 'available'
                AND v.vehicle_id NOT IN (
                    SELECT DISTINCT vehicle_id 
                    FROM deployments d
                    JOIN daily_trips t ON d.trip_id = t.trip_id
                    WHERE t.live_status IN ('SCHEDULED', 'LIVE')
                    AND t.trip_date >= CURRENT_DATE
                )
                ORDER BY v.registration_number
            """)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting available vehicles: {e}")
        return []


async def tool_get_available_drivers() -> List[Dict]:
    """
    Get all available drivers (not currently assigned to active trips).
    Used for wizard suggestions.
    
    Returns:
        List of available driver dictionaries
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    d.driver_id,
                    d.name,
                    d.license_number,
                    d.status
                FROM drivers d
                WHERE LOWER(d.status) = 'available'
                AND d.driver_id NOT IN (
                    SELECT DISTINCT driver_id 
                    FROM deployments dep
                    JOIN daily_trips t ON dep.trip_id = t.trip_id
                    WHERE t.live_status IN ('SCHEDULED', 'LIVE')
                    AND t.trip_date >= CURRENT_DATE
                )
                ORDER BY d.name
            """)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting available drivers: {e}")
        return []


async def tool_get_all_paths() -> List[Dict]:
    """
    Get all paths with stop count.
    Used for wizard suggestions.
    
    Returns:
        List of path dictionaries with metadata
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    p.path_id,
                    p.path_name,
                    p.created_at,
                    COUNT(ps.stop_id) as stop_count
                FROM paths p
                LEFT JOIN path_stops ps ON p.path_id = ps.path_id
                GROUP BY p.path_id, p.path_name, p.created_at
                ORDER BY p.path_name
            """)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting all paths: {e}")
        return []


async def tool_get_all_routes() -> List[Dict]:
    """
    Get all routes with path information.
    Used for wizard suggestions.
    
    Returns:
        List of route dictionaries with path details
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    r.route_id,
                    r.route_name,
                    r.path_id,
                    p.path_name,
                    r.created_at
                FROM routes r
                LEFT JOIN paths p ON r.path_id = p.path_id
                ORDER BY r.route_name
            """)
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting all routes: {e}")
        return []


# ============================================================================
# DASHBOARD INTELLIGENCE TOOLS
# ============================================================================

async def tool_get_trips_needing_attention() -> Dict:
    """
    Get trips that need immediate attention (missing vehicle/driver, low capacity, etc.)
    
    Returns:
        Dictionary with trips needing attention
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.trip_date,
                    dt.live_status,
                    dt.booking_status_percentage,
                    d.vehicle_id,
                    d.driver_id,
                    CASE 
                        WHEN d.vehicle_id IS NULL THEN 'Missing Vehicle'
                        WHEN d.driver_id IS NULL THEN 'Missing Driver'
                        WHEN dt.booking_status_percentage > 90 THEN 'Near Full Capacity'
                        WHEN dt.live_status = 'DELAYED' THEN 'Delayed'
                        ELSE 'Needs Review'
                    END as attention_reason
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                AND (
                    d.vehicle_id IS NULL 
                    OR d.driver_id IS NULL 
                    OR dt.booking_status_percentage > 90
                    OR dt.live_status IN ('DELAYED', 'CANCELLED')
                )
                ORDER BY dt.display_name
            """)
            
            trips = [dict(r) for r in rows]
            return {
                "ok": True,
                "result": trips,
                "count": len(trips),
                "message": f"Found {len(trips)} trip(s) needing attention"
            }
    except Exception as e:
        logger.error(f"Error getting trips needing attention: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_get_today_summary() -> Dict:
    """
    Get summary of today's operations.
    
    Returns:
        Dictionary with today's operational summary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get trip counts by status (all active trips - they recur daily)
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_trips,
                    COUNT(*) FILTER (WHERE live_status = 'SCHEDULED') as scheduled,
                    COUNT(*) FILTER (WHERE live_status = 'IN_PROGRESS') as in_progress,
                    COUNT(*) FILTER (WHERE live_status = 'COMPLETED') as completed,
                    COUNT(*) FILTER (WHERE live_status = 'CANCELLED') as cancelled,
                    COUNT(*) FILTER (WHERE live_status = 'DELAYED') as delayed,
                    AVG(COALESCE(booking_status_percentage, 0)) as avg_booking_pct
                FROM daily_trips
            """)
            
            # Get vehicle/driver assignment stats
            deployment_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT d.vehicle_id) as vehicles_in_use,
                    COUNT(DISTINCT d.driver_id) as drivers_on_duty,
                    COUNT(*) FILTER (WHERE d.vehicle_id IS NULL) as trips_without_vehicle,
                    COUNT(*) FILTER (WHERE d.driver_id IS NULL) as trips_without_driver
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
            """)
            
            return {
                "ok": True,
                "result": {
                    "trip_stats": dict(stats) if stats else {},
                    "deployment_stats": dict(deployment_stats) if deployment_stats else {},
                    "date": str(await conn.fetchval("SELECT CURRENT_DATE"))
                }
            }
    except Exception as e:
        logger.error(f"Error getting today's summary: {e}")
        return {"ok": False, "error": str(e)}


async def tool_get_recent_changes(minutes: int = 10) -> Dict:
    """
    Get recent changes/updates in the system by looking at recently modified trips.
    
    Args:
        minutes: Look back period in minutes (default 10)
        
    Returns:
        Dictionary with recent changes
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get recently created trips (updated_at column may not exist)
            rows = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    dt.trip_date,
                    dt.created_at as changed_at,
                    'created' as change_type
                FROM daily_trips dt
                WHERE dt.created_at >= NOW() - INTERVAL '%s minutes'
                ORDER BY dt.created_at DESC
                LIMIT 50
            """ % (minutes,))
            
            changes = [dict(r) for r in rows]
            return {
                "ok": True,
                "result": changes,
                "count": len(changes),
                "period_minutes": minutes,
                "message": f"Found {len(changes)} trip(s) changed in the last {minutes} minutes"
            }
    except Exception as e:
        logger.error(f"Error getting recent changes: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_get_high_demand_offices() -> Dict:
    """
    Get offices/locations with highest booking demand.
    
    Returns:
        Dictionary with demand by office
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    COALESCE(s.name, 'Unknown') as office_name,
                    COUNT(b.booking_id) as total_bookings,
                    COUNT(DISTINCT dt.trip_id) as trips_serving
                FROM bookings b
                JOIN daily_trips dt ON b.trip_id = dt.trip_id
                LEFT JOIN routes r ON dt.route_id = r.route_id
                LEFT JOIN paths p ON r.path_id = p.path_id
                LEFT JOIN path_stops ps ON p.path_id = ps.path_id AND ps.stop_order = 1
                LEFT JOIN stops s ON ps.stop_id = s.stop_id
                GROUP BY s.name
                ORDER BY total_bookings DESC
                LIMIT 10
            """)
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows]
            }
    except Exception as e:
        logger.error(f"Error getting high demand offices: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_get_most_used_vehicles(days: int = 7) -> Dict:
    """
    Get most frequently used vehicles.
    
    Args:
        days: Look back period in days (default 7)
        
    Returns:
        Dictionary with vehicle usage stats
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    v.vehicle_id,
                    v.registration_number,
                    v.vehicle_type,
                    v.capacity,
                    COUNT(d.deployment_id) as trip_count,
                    ROUND(AVG(COALESCE(dt.booking_status_percentage, 0)), 1) as avg_booking_pct
                FROM vehicles v
                JOIN deployments d ON v.vehicle_id = d.vehicle_id
                JOIN daily_trips dt ON d.trip_id = dt.trip_id
                WHERE dt.trip_date >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY v.vehicle_id, v.registration_number, v.vehicle_type, v.capacity
                ORDER BY trip_count DESC
                LIMIT 10
            """ % days)
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows],
                "period_days": days
            }
    except Exception as e:
        logger.error(f"Error getting most used vehicles: {e}")
        return {"ok": False, "error": str(e), "result": []}


# ============================================================================
# VEHICLE MANAGEMENT TOOLS
# ============================================================================

async def tool_get_vehicle_status(vehicle_id: int) -> Dict:
    """
    Get detailed status of a specific vehicle.
    
    Args:
        vehicle_id: Vehicle ID to query
        
    Returns:
        Dictionary with vehicle status
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            vehicle = await conn.fetchrow("""
                SELECT 
                    v.vehicle_id,
                    v.registration_number,
                    v.vehicle_type,
                    v.capacity,
                    v.status
                FROM vehicles v
                WHERE v.vehicle_id = $1
            """, vehicle_id)
            
            if not vehicle:
                return {"ok": False, "error": f"Vehicle {vehicle_id} not found"}
            
            # Get current assignments (trips are daily recurring)
            assignments = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    d.driver_id
                FROM deployments d
                JOIN daily_trips dt ON d.trip_id = dt.trip_id
                WHERE d.vehicle_id = $1
                ORDER BY dt.trip_id
            """, vehicle_id)
            
            return {
                "ok": True,
                "result": {
                    **dict(vehicle),
                    "today_assignments": [dict(a) for a in assignments],
                    "assignment_count": len(assignments)
                }
            }
    except Exception as e:
        logger.error(f"Error getting vehicle status: {e}")
        return {"ok": False, "error": str(e)}


async def tool_block_vehicle(vehicle_id: int, reason: str, user_id: int) -> Dict:
    """
    Block a vehicle from being assigned to trips.
    
    Args:
        vehicle_id: Vehicle to block
        reason: Reason for blocking
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE vehicles 
                SET status = 'BLOCKED'
                WHERE vehicle_id = $1
            """, vehicle_id)
            
            logger.info(f"Vehicle {vehicle_id} blocked by user {user_id}. Reason: {reason}")
            return {
                "ok": True,
                "message": f"Vehicle {vehicle_id} has been blocked. Reason: {reason}",
                "action": "block_vehicle"
            }
    except Exception as e:
        logger.error(f"Error blocking vehicle: {e}")
        return {"ok": False, "error": str(e), "action": "block_vehicle"}


async def tool_unblock_vehicle(vehicle_id: int, user_id: int) -> Dict:
    """
    Unblock a vehicle to allow assignments.
    
    Args:
        vehicle_id: Vehicle to unblock
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE vehicles 
                SET status = 'AVAILABLE'
                WHERE vehicle_id = $1
            """, vehicle_id)
            
            logger.info(f"Vehicle {vehicle_id} unblocked by user {user_id}")
            return {
                "ok": True,
                "message": f"Vehicle {vehicle_id} is now available for assignments",
                "action": "unblock_vehicle"
            }
    except Exception as e:
        logger.error(f"Error unblocking vehicle: {e}")
        return {"ok": False, "error": str(e), "action": "unblock_vehicle"}


async def tool_get_vehicle_trips_today(vehicle_id: int) -> Dict:
    """
    Get all trips assigned to a vehicle today.
    
    Args:
        vehicle_id: Vehicle ID to query
        
    Returns:
        Dictionary with current trips for the vehicle (trips are daily recurring)
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Trips are daily recurring - get all trips where vehicle is assigned
            rows = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    dt.booking_status_percentage,
                    d.driver_id,
                    dr.name as driver_name
                FROM deployments d
                JOIN daily_trips dt ON d.trip_id = dt.trip_id
                LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
                WHERE d.vehicle_id = $1
                ORDER BY dt.trip_id
            """, vehicle_id)
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows],
                "count": len(rows),
                "vehicle_id": vehicle_id
            }
    except Exception as e:
        logger.error(f"Error getting vehicle trips: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_recommend_vehicle_for_trip(trip_id: int, min_capacity: int = None) -> Dict:
    """
    Recommend the best available vehicle for a trip based on capacity and availability.
    
    Args:
        trip_id: Trip to find vehicle for
        min_capacity: Minimum seating capacity required (optional)
        
    Returns:
        Dictionary with vehicle recommendations
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get trip details including booking percentage
            trip = await conn.fetchrow("""
                SELECT trip_id, booking_status_percentage, trip_date
                FROM daily_trips WHERE trip_id = $1
            """, trip_id)
            
            if not trip:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            booking_pct = trip['booking_status_percentage'] or 0
            
            # Build query with optional min_capacity filter
            if min_capacity:
                rows = await conn.fetch("""
                    SELECT 
                        v.vehicle_id,
                        v.registration_number,
                        v.vehicle_type,
                        v.capacity,
                        COUNT(d.deployment_id) as current_assignments
                    FROM vehicles v
                    LEFT JOIN deployments d ON v.vehicle_id = d.vehicle_id 
                        AND d.trip_id IN (SELECT trip_id FROM daily_trips WHERE trip_date = $1)
                    WHERE LOWER(v.status) = 'available' AND v.capacity >= $2
                    GROUP BY v.vehicle_id, v.registration_number, v.vehicle_type, v.capacity
                    ORDER BY 
                        v.capacity ASC,  -- Prefer smallest vehicle that fits (efficient)
                        current_assignments ASC  -- Prefer less busy vehicles
                    LIMIT 5
                """, trip['trip_date'], min_capacity)
            else:
                rows = await conn.fetch("""
                    SELECT 
                        v.vehicle_id,
                        v.registration_number,
                        v.vehicle_type,
                        v.capacity,
                        COUNT(d.deployment_id) as current_assignments
                    FROM vehicles v
                    LEFT JOIN deployments d ON v.vehicle_id = d.vehicle_id 
                        AND d.trip_id IN (SELECT trip_id FROM daily_trips WHERE trip_date = $1)
                    WHERE LOWER(v.status) = 'available'
                    GROUP BY v.vehicle_id, v.registration_number, v.vehicle_type, v.capacity
                    ORDER BY 
                        v.capacity DESC,  -- Prefer larger capacity
                        current_assignments ASC  -- Prefer less busy vehicles
                    LIMIT 5
                """, trip['trip_date'])
            
            recommendations = [dict(r) for r in rows]
            
            return {
                "ok": True,
                "result": recommendations,
                "trip_id": trip_id,
                "current_booking_pct": booking_pct,
                "message": f"Found {len(recommendations)} suitable vehicles" if recommendations else "No suitable vehicles available"
            }
    except Exception as e:
        logger.error(f"Error recommending vehicle: {e}")
        return {"ok": False, "error": str(e), "result": []}


# ============================================================================
# DRIVER MANAGEMENT TOOLS
# ============================================================================

async def tool_get_driver_status(driver_id: int) -> Dict:
    """
    Get detailed status of a specific driver.
    
    Args:
        driver_id: Driver ID to query
        
    Returns:
        Dictionary with driver status
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            driver = await conn.fetchrow("""
                SELECT 
                    driver_id,
                    name,
                    phone,
                    license_number,
                    status
                FROM drivers
                WHERE driver_id = $1
            """, driver_id)
            
            if not driver:
                return {"ok": False, "error": f"Driver {driver_id} not found"}
            
            # Get current assignments (trips are daily recurring)
            assignments = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    d.vehicle_id
                FROM deployments d
                JOIN daily_trips dt ON d.trip_id = dt.trip_id
                WHERE d.driver_id = $1
                ORDER BY dt.trip_id
            """, driver_id)
            
            return {
                "ok": True,
                "result": {
                    **dict(driver),
                    "today_assignments": [dict(a) for a in assignments],
                    "assignment_count": len(assignments)
                }
            }
    except Exception as e:
        logger.error(f"Error getting driver status: {e}")
        return {"ok": False, "error": str(e)}


async def tool_get_driver_trips_today(driver_id: int) -> Dict:
    """
    Get all trips assigned to a driver for today.
    Trips are daily recurring schedules - a driver assigned to a trip
    works that trip every day until removed.
    
    Args:
        driver_id: Driver ID to query
        
    Returns:
        Dictionary with today's trips for the driver
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Trips are daily recurring - get all trips where driver is currently assigned
            # The deployment represents the driver's assignment to a recurring trip
            rows = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    dt.booking_status_percentage,
                    d.vehicle_id,
                    v.registration_number
                FROM deployments d
                JOIN daily_trips dt ON d.trip_id = dt.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                WHERE d.driver_id = $1
                ORDER BY dt.trip_id
            """, driver_id)
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows],
                "count": len(rows),
                "driver_id": driver_id
            }
    except Exception as e:
        logger.error(f"Error getting driver trips: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_set_driver_availability(driver_id: int, is_available: bool, user_id: int) -> Dict:
    """
    Set driver availability status.
    
    Args:
        driver_id: Driver to update
        is_available: New availability status
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            new_status = 'AVAILABLE' if is_available else 'UNAVAILABLE'
            await conn.execute("""
                UPDATE drivers 
                SET status = $1
                WHERE driver_id = $2
            """, new_status, driver_id)
            
            status_str = "available" if is_available else "unavailable"
            logger.info(f"Driver {driver_id} set to {status_str} by user {user_id}")
            return {
                "ok": True,
                "message": f"Driver {driver_id} is now {status_str}",
                "action": "set_driver_availability"
            }
    except Exception as e:
        logger.error(f"Error setting driver availability: {e}")
        return {"ok": False, "error": str(e), "action": "set_driver_availability"}


# ============================================================================
# BOOKING MANAGEMENT TOOLS
# ============================================================================

async def tool_get_booking_count(trip_id: int) -> Dict:
    """
    Get booking count and capacity info for a trip.
    
    Args:
        trip_id: Trip to query
        
    Returns:
        Dictionary with booking information
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.booking_status_percentage,
                    v.capacity as vehicle_capacity,
                    v.registration_number,
                    CASE 
                        WHEN v.capacity IS NOT NULL 
                        THEN ROUND(v.capacity * dt.booking_status_percentage / 100.0)
                        ELSE NULL
                    END as estimated_bookings
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                WHERE dt.trip_id = $1
            """, trip_id)
            
            if not result:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            return {
                "ok": True,
                "result": dict(result)
            }
    except Exception as e:
        logger.error(f"Error getting booking count: {e}")
        return {"ok": False, "error": str(e)}


async def tool_check_seat_availability(trip_id: int) -> Dict:
    """
    Check seat availability for a trip.
    
    Args:
        trip_id: Trip to query
        
    Returns:
        Dictionary with availability information
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    v.capacity as vehicle_capacity,
                    v.registration_number,
                    COALESCE(SUM(b.seats) FILTER (WHERE b.status = 'CONFIRMED'), 0) as seats_booked,
                    COUNT(b.booking_id) FILTER (WHERE b.status = 'CONFIRMED') as booking_count
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                LEFT JOIN bookings b ON b.trip_id = dt.trip_id
                WHERE dt.trip_id = $1
                GROUP BY dt.trip_id, dt.display_name, v.capacity, v.registration_number
            """, trip_id)
            
            if not result:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            capacity = result['vehicle_capacity'] or 0
            booked = result['seats_booked'] or 0
            available = max(0, capacity - booked)
            
            return {
                "ok": True,
                "result": {
                    "trip_id": result['trip_id'],
                    "display_name": result['display_name'],
                    "vehicle": result['registration_number'],
                    "capacity": capacity,
                    "seats_booked": booked,
                    "seats_available": available,
                    "booking_count": result['booking_count'],
                    "is_full": available == 0,
                    "percentage_booked": round((booked / capacity * 100) if capacity > 0 else 0, 1)
                }
            }
    except Exception as e:
        logger.error(f"Error checking seat availability: {e}")
        return {"ok": False, "error": str(e)}


async def tool_add_bookings(trip_id: int, count: int, user_id: int = 1) -> Dict:
    """
    Add bookings to a trip (increase booking count).
    Creates placeholder booking records.
    
    Args:
        trip_id: Trip to add bookings to
        count: Number of bookings to add
        user_id: User performing the action
        
    Returns:
        Dictionary with result
    """
    try:
        if count <= 0:
            return {"ok": False, "error": "Booking count must be positive"}
        
        pool = await get_conn()
        async with pool.acquire() as conn:
            # First check capacity
            capacity_info = await conn.fetchrow("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    v.capacity as vehicle_capacity,
                    COALESCE(SUM(b.seats) FILTER (WHERE b.status = 'CONFIRMED'), 0) as seats_booked
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                LEFT JOIN bookings b ON b.trip_id = dt.trip_id
                WHERE dt.trip_id = $1
                GROUP BY dt.trip_id, dt.display_name, v.capacity
            """, trip_id)
            
            if not capacity_info:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            capacity = capacity_info['vehicle_capacity'] or 0
            current_booked = capacity_info['seats_booked'] or 0
            available = capacity - current_booked
            
            if capacity == 0:
                return {"ok": False, "error": "No vehicle assigned to this trip. Cannot add bookings."}
            
            if count > available:
                return {
                    "ok": False, 
                    "error": f"Cannot add {count} bookings. Only {available} seats available (capacity: {capacity}, booked: {current_booked})"
                }
            
            # Add booking records (1 seat each for simplicity)
            import datetime
            for i in range(count):
                await conn.execute("""
                    INSERT INTO bookings (trip_id, user_id, user_name, seats, status, created_at)
                    VALUES ($1, $2, $3, 1, 'CONFIRMED', $4)
                """, trip_id, user_id, f"Passenger_{datetime.datetime.now().strftime('%H%M%S')}_{i+1}", datetime.datetime.now())
            
            # Update booking percentage in daily_trips
            new_booked = current_booked + count
            new_percentage = round((new_booked / capacity * 100) if capacity > 0 else 0, 1)
            await conn.execute("""
                UPDATE daily_trips 
                SET booking_status_percentage = $1
                WHERE trip_id = $2
            """, new_percentage, trip_id)
            
            logger.info(f"Added {count} bookings to trip {trip_id} by user {user_id}")
            
            return {
                "ok": True,
                "message": f"Successfully added {count} booking(s) to trip {capacity_info['display_name']}",
                "result": {
                    "trip_id": trip_id,
                    "bookings_added": count,
                    "previous_count": current_booked,
                    "new_count": new_booked,
                    "capacity": capacity,
                    "seats_available": available - count
                }
            }
    except Exception as e:
        logger.error(f"Error adding bookings: {e}")
        return {"ok": False, "error": str(e)}


async def tool_reduce_bookings(trip_id: int, count: int, user_id: int = 1) -> Dict:
    """
    Reduce bookings from a trip (decrease booking count).
    Cancels the most recent booking records.
    
    Args:
        trip_id: Trip to reduce bookings from
        count: Number of bookings to reduce
        user_id: User performing the action
        
    Returns:
        Dictionary with result
    """
    try:
        if count <= 0:
            return {"ok": False, "error": "Booking count must be positive"}
        
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Check current bookings
            booking_info = await conn.fetchrow("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    v.capacity as vehicle_capacity,
                    COALESCE(SUM(b.seats) FILTER (WHERE b.status = 'CONFIRMED'), 0) as seats_booked,
                    COUNT(b.booking_id) FILTER (WHERE b.status = 'CONFIRMED') as booking_count
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                LEFT JOIN bookings b ON b.trip_id = dt.trip_id
                WHERE dt.trip_id = $1
                GROUP BY dt.trip_id, dt.display_name, v.capacity
            """, trip_id)
            
            if not booking_info:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            current_booked = booking_info['seats_booked'] or 0
            current_count = booking_info['booking_count'] or 0
            capacity = booking_info['vehicle_capacity'] or 40  # Default capacity
            
            if current_count == 0:
                return {"ok": False, "error": "No bookings to reduce. Trip has 0 confirmed bookings."}
            
            if count > current_count:
                return {
                    "ok": False, 
                    "error": f"Cannot reduce by {count}. Trip only has {current_count} confirmed booking(s)."
                }
            
            # Cancel the most recent bookings (set status to CANCELLED)
            await conn.execute("""
                UPDATE bookings 
                SET status = 'CANCELLED'
                WHERE booking_id IN (
                    SELECT booking_id 
                    FROM bookings 
                    WHERE trip_id = $1 AND status = 'CONFIRMED'
                    ORDER BY created_at DESC
                    LIMIT $2
                )
            """, trip_id, count)
            
            # Update booking percentage in daily_trips
            new_booked = current_booked - count
            new_percentage = round((new_booked / capacity * 100) if capacity > 0 else 0, 1)
            await conn.execute("""
                UPDATE daily_trips 
                SET booking_status_percentage = $1
                WHERE trip_id = $2
            """, new_percentage, trip_id)
            
            logger.info(f"Reduced {count} bookings from trip {trip_id} by user {user_id}")
            
            return {
                "ok": True,
                "message": f"Successfully reduced {count} booking(s) from trip {booking_info['display_name']}",
                "result": {
                    "trip_id": trip_id,
                    "bookings_reduced": count,
                    "previous_count": current_count,
                    "new_count": current_count - count,
                    "capacity": capacity,
                    "seats_available": capacity - new_booked
                }
            }
    except Exception as e:
        logger.error(f"Error reducing bookings: {e}")
        return {"ok": False, "error": str(e)}


async def tool_get_trip_stops(trip_id: int) -> Dict:
    """
    Get all stops for a trip by traversing trip → route → path → stops.
    
    Args:
        trip_id: Trip to query
        
    Returns:
        Dictionary with trip info and ordered list of stops
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # First get the trip and its path
            trip_info = await conn.fetchrow("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    r.route_id,
                    r.route_name,
                    p.path_id,
                    p.path_name
                FROM daily_trips dt
                JOIN routes r ON dt.route_id = r.route_id
                JOIN paths p ON r.path_id = p.path_id
                WHERE dt.trip_id = $1
            """, trip_id)
            
            if not trip_info:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            # Get all stops for the path in order
            stops = await conn.fetch("""
                SELECT 
                    s.stop_id,
                    s.name as stop_name,
                    s.latitude,
                    s.longitude,
                    ps.stop_order
                FROM path_stops ps
                JOIN stops s ON ps.stop_id = s.stop_id
                WHERE ps.path_id = $1
                ORDER BY ps.stop_order
            """, trip_info['path_id'])
            
            return {
                "ok": True,
                "result": {
                    "trip_id": trip_info['trip_id'],
                    "display_name": trip_info['display_name'],
                    "route_name": trip_info['route_name'],
                    "path_name": trip_info['path_name'],
                    "stops": [dict(s) for s in stops],
                    "stop_count": len(stops)
                }
            }
    except Exception as e:
        logger.error(f"Error getting trip stops: {e}")
        return {"ok": False, "error": str(e)}


async def tool_list_passengers(trip_id: int) -> Dict:
    """
    List all passengers/bookings for a trip.
    
    Args:
        trip_id: Trip to query
        
    Returns:
        Dictionary with passenger list
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    b.booking_id,
                    b.user_name,
                    b.seats,
                    b.status,
                    b.pickup_stop,
                    b.drop_stop,
                    b.created_at
                FROM bookings b
                WHERE b.trip_id = $1
                ORDER BY b.created_at
            """, trip_id)
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows],
                "count": len(rows),
                "trip_id": trip_id
            }
    except Exception as e:
        logger.error(f"Error listing passengers: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_cancel_all_bookings(trip_id: int, reason: str, user_id: int) -> Dict:
    """
    Cancel all bookings for a trip.
    
    Args:
        trip_id: Trip to cancel bookings for
        reason: Reason for cancellation
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get count before cancelling
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM bookings 
                WHERE trip_id = $1 AND status != 'CANCELLED'
            """, trip_id)
            
            if count == 0:
                return {
                    "ok": True,
                    "message": f"No active bookings to cancel for trip {trip_id}",
                    "count": 0,
                    "action": "cancel_all_bookings"
                }
            
            # Cancel all bookings (just update status - no cancellation_reason column)
            await conn.execute("""
                UPDATE bookings 
                SET status = 'CANCELLED'
                WHERE trip_id = $1 AND status != 'CANCELLED'
            """, trip_id)
            
            logger.info(f"Cancelled {count} bookings for trip {trip_id} by user {user_id}. Reason: {reason}")
            return {
                "ok": True,
                "message": f"Cancelled {count} booking(s) for trip {trip_id}",
                "count": count,
                "action": "cancel_all_bookings"
            }
    except Exception as e:
        logger.error(f"Error cancelling bookings: {e}")
        return {"ok": False, "error": str(e), "action": "cancel_all_bookings"}


async def tool_find_employee_trips(employee_name: str) -> Dict:
    """
    Find all trips booked by an employee.
    
    Args:
        employee_name: Name to search for
        
    Returns:
        Dictionary with employee's trips
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    b.booking_id,
                    b.user_name,
                    dt.trip_id,
                    dt.display_name,
                    dt.trip_date,
                    dt.live_status,
                    b.status as booking_status,
                    b.seats
                FROM bookings b
                JOIN daily_trips dt ON b.trip_id = dt.trip_id
                WHERE LOWER(b.user_name) LIKE LOWER($1)
                ORDER BY dt.trip_date DESC, dt.trip_id
                LIMIT 20
            """, f"%{employee_name}%")
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows],
                "count": len(rows),
                "search_term": employee_name
            }
    except Exception as e:
        logger.error(f"Error finding employee trips: {e}")
        return {"ok": False, "error": str(e), "result": []}


# ============================================================================
# SMART AUTOMATION TOOLS  
# ============================================================================

async def tool_check_trip_readiness(trip_id: int) -> Dict:
    """
    Check if a trip is ready to run (has vehicle, driver, capacity).
    
    Args:
        trip_id: Trip to check
        
    Returns:
        Dictionary with readiness assessment
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    dt.booking_status_percentage,
                    d.vehicle_id,
                    d.driver_id,
                    v.capacity as vehicle_capacity,
                    v.status as vehicle_status,
                    dr.status as driver_status
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
                WHERE dt.trip_id = $1
            """, trip_id)
            
            if not result:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            issues = []
            data = dict(result)
            
            if not data['vehicle_id']:
                issues.append("No vehicle assigned")
            elif data['vehicle_status'] != 'AVAILABLE':
                issues.append(f"Vehicle status is {data['vehicle_status']}")
                
            if not data['driver_id']:
                issues.append("No driver assigned")
            elif data['driver_status'] != 'AVAILABLE':
                issues.append("Assigned driver is not available")
                
            # Check for overbooking using percentage (>100% means overbooked)
            if data['booking_status_percentage'] and data['booking_status_percentage'] > 100:
                issues.append(f"Overbooked: booking at {data['booking_status_percentage']}% capacity")
            
            is_ready = len(issues) == 0
            
            return {
                "ok": True,
                "result": {
                    **data,
                    "is_ready": is_ready,
                    "issues": issues
                },
                "is_ready": is_ready,
                "message": "Trip is ready to run" if is_ready else f"Trip has {len(issues)} issue(s): " + ", ".join(issues)
            }
    except Exception as e:
        logger.error(f"Error checking trip readiness: {e}")
        return {"ok": False, "error": str(e)}


async def tool_detect_overbooking() -> Dict:
    """
    Detect trips that are overbooked (more bookings than vehicle capacity).
    
    Returns:
        Dictionary with overbooked trips
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.booking_status_percentage,
                    v.capacity as vehicle_capacity,
                    v.registration_number
                FROM daily_trips dt
                JOIN deployments d ON dt.trip_id = d.trip_id
                JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                WHERE dt.booking_status_percentage > 100
                ORDER BY dt.booking_status_percentage DESC
            """)
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows],
                "count": len(rows),
                "message": f"Found {len(rows)} overbooked trip(s)" if rows else "No overbooked trips found"
            }
    except Exception as e:
        logger.error(f"Error detecting overbooking: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_predict_problem_trips() -> Dict:
    """
    Predict trips that may have problems (missing resources, high demand, etc.)
    
    Returns:
        Dictionary with potential problem trips
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.booking_status_percentage,
                    dt.live_status,
                    d.vehicle_id,
                    d.driver_id,
                    v.capacity,
                    CASE 
                        WHEN d.vehicle_id IS NULL THEN 'NO_VEHICLE'
                        WHEN d.driver_id IS NULL THEN 'NO_DRIVER'
                        WHEN dt.booking_status_percentage > 100 THEN 'OVERBOOKED'
                        WHEN dt.booking_status_percentage > 85 THEN 'NEAR_CAPACITY'
                        ELSE 'AT_RISK'
                    END as risk_type
                FROM daily_trips dt
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                WHERE dt.live_status NOT IN ('COMPLETED', 'CANCELLED')
                AND (
                    d.vehicle_id IS NULL 
                    OR d.driver_id IS NULL 
                    OR dt.booking_status_percentage > 85
                )
                ORDER BY 
                    CASE 
                        WHEN d.vehicle_id IS NULL THEN 1
                        WHEN d.driver_id IS NULL THEN 2
                        WHEN dt.booking_status_percentage > 100 THEN 3
                        ELSE 4
                    END
            """)
            
            return {
                "ok": True,
                "result": [dict(r) for r in rows],
                "count": len(rows),
                "message": f"Found {len(rows)} trip(s) with potential problems"
            }
    except Exception as e:
        logger.error(f"Error predicting problem trips: {e}")
        return {"ok": False, "error": str(e), "result": []}


async def tool_suggest_alternate_vehicle(trip_id: int) -> Dict:
    """
    Suggest an alternate vehicle if current one is unsuitable.
    Alias for tool_recommend_vehicle_for_trip.
    """
    return await tool_recommend_vehicle_for_trip(trip_id)


# ============================================================================
# STOP/PATH MANAGEMENT TOOLS
# ============================================================================

async def tool_delete_stop(stop_id: int, user_id: int) -> Dict:
    """
    Delete a stop (with dependency check).
    
    Args:
        stop_id: Stop to delete
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Check if stop is used in any path
            path_count = await conn.fetchval("""
                SELECT COUNT(*) FROM path_stops WHERE stop_id = $1
            """, stop_id)
            
            if path_count > 0:
                return {
                    "ok": False,
                    "error": f"Cannot delete stop: it is used in {path_count} path(s)",
                    "action": "delete_stop"
                }
            
            # Delete the stop
            await conn.execute("DELETE FROM stops WHERE stop_id = $1", stop_id)
            
            logger.info(f"Stop {stop_id} deleted by user {user_id}")
            return {
                "ok": True,
                "message": f"Stop {stop_id} deleted successfully",
                "action": "delete_stop"
            }
    except Exception as e:
        logger.error(f"Error deleting stop: {e}")
        return {"ok": False, "error": str(e), "action": "delete_stop"}


async def tool_update_path_stops(path_id: int, stop_ids: List[int], user_id: int) -> Dict:
    """
    Update the stops in a path.
    
    Args:
        path_id: Path to update
        stop_ids: New ordered list of stop IDs
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Delete existing path stops
                await conn.execute("DELETE FROM path_stops WHERE path_id = $1", path_id)
                
                # Insert new path stops
                for order, stop_id in enumerate(stop_ids, 1):
                    await conn.execute("""
                        INSERT INTO path_stops (path_id, stop_id, stop_order)
                        VALUES ($1, $2, $3)
                    """, path_id, stop_id, order)
            
            logger.info(f"Path {path_id} stops updated by user {user_id}")
            return {
                "ok": True,
                "message": f"Path {path_id} updated with {len(stop_ids)} stops",
                "action": "update_path_stops"
            }
    except Exception as e:
        logger.error(f"Error updating path stops: {e}")
        return {"ok": False, "error": str(e), "action": "update_path_stops"}


async def tool_delete_path(path_id: int, user_id: int) -> Dict:
    """
    Delete a path (with dependency check).
    
    Args:
        path_id: Path to delete
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Check if path is used in any route
            route_count = await conn.fetchval("""
                SELECT COUNT(*) FROM routes WHERE path_id = $1
            """, path_id)
            
            if route_count > 0:
                return {
                    "ok": False,
                    "error": f"Cannot delete path: it is used in {route_count} route(s)",
                    "action": "delete_path"
                }
            
            async with conn.transaction():
                # Delete path stops first
                await conn.execute("DELETE FROM path_stops WHERE path_id = $1", path_id)
                # Delete the path
                await conn.execute("DELETE FROM paths WHERE path_id = $1", path_id)
            
            logger.info(f"Path {path_id} deleted by user {user_id}")
            return {
                "ok": True,
                "message": f"Path {path_id} deleted successfully",
                "action": "delete_path"
            }
    except Exception as e:
        logger.error(f"Error deleting path: {e}")
        return {"ok": False, "error": str(e), "action": "delete_path"}


async def tool_delete_route(route_id: int, user_id: int) -> Dict:
    """
    Delete a route (with dependency check).
    
    Args:
        route_id: Route to delete
        user_id: User performing the action
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Check if route has any trips
            trip_count = await conn.fetchval("""
                SELECT COUNT(*) FROM daily_trips WHERE route_id = $1
            """, route_id)
            
            if trip_count > 0:
                return {
                    "ok": False,
                    "error": f"Cannot delete route: it has {trip_count} trip(s) associated",
                    "action": "delete_route"
                }
            
            # Delete the route
            await conn.execute("DELETE FROM routes WHERE route_id = $1", route_id)
            
            logger.info(f"Route {route_id} deleted by user {user_id}")
            return {
                "ok": True,
                "message": f"Route {route_id} deleted successfully",
                "action": "delete_route"
            }
    except Exception as e:
        logger.error(f"Error deleting route: {e}")
        return {"ok": False, "error": str(e), "action": "delete_route"}


async def tool_validate_route(route_id: int) -> Dict:
    """
    Validate route configuration (path exists, has stops, etc.)
    
    Args:
        route_id: Route to validate
        
    Returns:
        Dictionary with validation results
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            route = await conn.fetchrow("""
                SELECT r.route_id, r.route_name, r.path_id, p.path_name
                FROM routes r
                LEFT JOIN paths p ON r.path_id = p.path_id
                WHERE r.route_id = $1
            """, route_id)
            
            if not route:
                return {"ok": False, "error": f"Route {route_id} not found"}
            
            issues = []
            
            if not route['path_id']:
                issues.append("Route has no path assigned")
            else:
                # Check if path has stops
                stop_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM path_stops WHERE path_id = $1
                """, route['path_id'])
                
                if stop_count == 0:
                    issues.append("Path has no stops")
                elif stop_count < 2:
                    issues.append("Path should have at least 2 stops")
            
            return {
                "ok": True,
                "result": {
                    **dict(route),
                    "is_valid": len(issues) == 0,
                    "issues": issues
                },
                "is_valid": len(issues) == 0,
                "message": "Route is valid" if len(issues) == 0 else f"Route has {len(issues)} issue(s)"
            }
    except Exception as e:
        logger.error(f"Error validating route: {e}")
        return {"ok": False, "error": str(e)}


# ============================================================================
# SYSTEM / CONVERSATIONAL TOOLS
# ============================================================================

async def tool_simulate_action(action: str, trip_id: int = None, **params) -> Dict:
    """
    Simulate an action without actually executing it.
    Shows what would happen if the action were executed.
    
    Args:
        action: Action to simulate
        trip_id: Trip ID if applicable
        **params: Additional parameters
        
    Returns:
        Dictionary with simulation results
    """
    try:
        simulation = {
            "action": action,
            "trip_id": trip_id,
            "params": params,
            "would_affect": []
        }
        
        if trip_id:
            pool = await get_conn()
            async with pool.acquire() as conn:
                # Get trip info
                trip = await conn.fetchrow("""
                    SELECT dt.*, d.vehicle_id, d.driver_id
                    FROM daily_trips dt
                    LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                    WHERE dt.trip_id = $1
                """, trip_id)
                
                if trip:
                    simulation["trip_info"] = dict(trip)
                    
                    if action in ["cancel_trip", "remove_vehicle", "remove_driver"]:
                        # Get booking count
                        booking_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM bookings WHERE trip_id = $1 AND status != 'CANCELLED'",
                            trip_id
                        )
                        simulation["would_affect"].append(f"{booking_count} active booking(s)")
                    
                    if action == "remove_vehicle" and trip['vehicle_id']:
                        simulation["would_affect"].append(f"Vehicle {trip['vehicle_id']} would be unassigned")
                    
                    if action == "remove_driver" and trip['driver_id']:
                        simulation["would_affect"].append(f"Driver {trip['driver_id']} would be unassigned")
        
        return {
            "ok": True,
            "result": simulation,
            "message": "Simulation completed - no changes made"
        }
    except Exception as e:
        logger.error(f"Error simulating action: {e}")
        return {"ok": False, "error": str(e)}


async def tool_explain_decision(action: str, context: Dict = None) -> Dict:
    """
    Explain why Movi suggested or took a particular action.
    
    Args:
        action: Action to explain
        context: Context of the decision
        
    Returns:
        Dictionary with explanation
    """
    explanations = {
        "assign_vehicle": "Vehicle assignment considers capacity requirements, availability, and proximity to minimize operational costs.",
        "assign_driver": "Driver assignment considers shift schedules, rest requirements, and driver qualifications.",
        "remove_vehicle": "Vehicle removal is suggested when the trip is cancelled or a better vehicle is available.",
        "remove_driver": "Driver removal may be needed for shift changes or to reassign to higher priority trips.",
        "cancel_trip": "Trip cancellation is recommended when demand is too low or resources are unavailable.",
        "update_trip_status": "Status updates help track trip progress and trigger notifications to passengers.",
    }
    
    return {
        "ok": True,
        "result": {
            "action": action,
            "explanation": explanations.get(action, f"Action '{action}' helps manage transport operations efficiently."),
            "context": context
        }
    }


# ============================================================================
# TRIP SCHEDULING TOOLS
# ============================================================================

async def tool_delay_trip(trip_id: int, delay_minutes: int, reason: str = None) -> Dict:
    """
    Delay a trip by a specified number of minutes.
    
    Args:
        trip_id: Trip to delay
        delay_minutes: Number of minutes to delay
        reason: Optional reason for delay
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get current trip info - shift_time is on routes table
            trip = await conn.fetchrow("""
                SELECT t.trip_id, t.display_name, t.live_status, r.shift_time
                FROM daily_trips t
                LEFT JOIN routes r ON t.route_id = r.route_id
                WHERE t.trip_id = $1
            """, trip_id)
            
            if not trip:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            if trip['live_status'] in ['COMPLETED', 'CANCELLED']:
                return {"ok": False, "error": f"Cannot delay a {trip['live_status']} trip"}
            
            # Calculate new time
            current_time = trip['shift_time']
            if current_time:
                from datetime import timedelta
                new_time = (datetime.combine(datetime.today(), current_time) + 
                           timedelta(minutes=delay_minutes)).time()
                
                # Update route's shift_time (affects all trips on this route)
                # Note: This is a simplification - a more complete solution would
                # track per-trip scheduled times separately
                await conn.execute("""
                    UPDATE routes
                    SET shift_time = $1
                    WHERE route_id = (SELECT route_id FROM daily_trips WHERE trip_id = $2)
                """, new_time, trip_id)
                
                return {
                    "ok": True,
                    "message": f"Trip {trip['display_name']} delayed by {delay_minutes} minutes. New time: {new_time.strftime('%H:%M')}",
                    "new_time": new_time.strftime('%H:%M'),
                    "action": "delay_trip"
                }
            else:
                # Try to extract time from display_name (e.g., "Path-1 - 08:00")
                import re
                time_match = re.search(r'(\d{1,2}):(\d{2})', trip['display_name'] or '')
                if time_match:
                    hour, minute = int(time_match.group(1)), int(time_match.group(2))
                    from datetime import time as time_type
                    current_time = time_type(hour, minute)
                    from datetime import timedelta
                    new_time = (datetime.combine(datetime.today(), current_time) + 
                               timedelta(minutes=delay_minutes)).time()
                    
                    # Update route's shift_time
                    await conn.execute("""
                        UPDATE routes
                        SET shift_time = $1
                        WHERE route_id = (SELECT route_id FROM daily_trips WHERE trip_id = $2)
                    """, new_time, trip_id)
                    
                    return {
                        "ok": True,
                        "message": f"Trip {trip['display_name']} delayed by {delay_minutes} minutes. New time: {new_time.strftime('%H:%M')}",
                        "new_time": new_time.strftime('%H:%M'),
                        "action": "delay_trip"
                    }
                return {"ok": False, "error": "Trip has no scheduled time to delay"}
                
    except Exception as e:
        logger.error(f"Error delaying trip: {e}")
        return {"ok": False, "error": str(e), "action": "delay_trip"}


async def tool_reschedule_trip(trip_id: int, new_time: str = None, new_date: str = None) -> Dict:
    """
    Reschedule a trip to a new time and/or date.
    
    Args:
        trip_id: Trip to reschedule
        new_time: New time in HH:MM format
        new_date: New date in YYYY-MM-DD format
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get current trip info - shift_time is on routes table
            trip = await conn.fetchrow("""
                SELECT t.trip_id, t.display_name, t.trip_date, t.live_status, t.route_id, r.shift_time
                FROM daily_trips t
                LEFT JOIN routes r ON t.route_id = r.route_id
                WHERE t.trip_id = $1
            """, trip_id)
            
            if not trip:
                return {"ok": False, "error": f"Trip {trip_id} not found"}
            
            if trip['live_status'] in ['COMPLETED', 'CANCELLED']:
                return {"ok": False, "error": f"Cannot reschedule a {trip['live_status']} trip"}
            
            msg_parts = []
            
            # Update time (on routes table)
            if new_time:
                from datetime import datetime as dt
                parsed_time = dt.strptime(new_time, '%H:%M').time()
                await conn.execute("""
                    UPDATE routes SET shift_time = $1 
                    WHERE route_id = $2
                """, parsed_time, trip['route_id'])
                msg_parts.append(f"time: {new_time}")
            
            # Update date (on daily_trips table)
            if new_date:
                from datetime import datetime as dt
                parsed_date = dt.strptime(new_date, '%Y-%m-%d').date()
                await conn.execute("""
                    UPDATE daily_trips SET trip_date = $1 
                    WHERE trip_id = $2
                """, parsed_date, trip_id)
                msg_parts.append(f"date: {new_date}")
            
            if not msg_parts:
                return {"ok": False, "error": "Either new_time or new_date must be provided"}
            
            msg_parts = []
            if new_time:
                msg_parts.append(f"time: {new_time}")
            if new_date:
                msg_parts.append(f"date: {new_date}")
            
            return {
                "ok": True,
                "message": f"Trip {trip['display_name']} rescheduled to {', '.join(msg_parts)}",
                "action": "reschedule_trip"
            }
                
    except Exception as e:
        logger.error(f"Error rescheduling trip: {e}")
        return {"ok": False, "error": str(e), "action": "reschedule_trip"}


async def tool_add_vehicle(registration_number: str, vehicle_type: str = "Bus", 
                          capacity: int = 40, status: str = "available") -> Dict:
    """
    Add a new vehicle to the fleet.
    
    Args:
        registration_number: Vehicle registration number
        vehicle_type: Type of vehicle (Bus, Cab, etc.)
        capacity: Seating capacity
        status: Initial status (available, maintenance, etc.)
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Check if vehicle already exists
            existing = await conn.fetchval(
                "SELECT vehicle_id FROM vehicles WHERE registration_number = $1",
                registration_number
            )
            
            if existing:
                return {"ok": False, "error": f"Vehicle {registration_number} already exists"}
            
            # Normalize vehicle type to match DB constraint (Bus, Cab, etc.)
            normalized_type = vehicle_type.capitalize() if vehicle_type else "Bus"
            normalized_status = status.lower() if status else "available"
            
            # Insert new vehicle
            vehicle_id = await conn.fetchval("""
                INSERT INTO vehicles (registration_number, vehicle_type, capacity, status)
                VALUES ($1, $2, $3, $4)
                RETURNING vehicle_id
            """, registration_number, normalized_type, capacity, normalized_status)
            
            return {
                "ok": True,
                "message": f"Vehicle {registration_number} added successfully with ID {vehicle_id}",
                "vehicle_id": vehicle_id,
                "action": "add_vehicle"
            }
                
    except Exception as e:
        logger.error(f"Error adding vehicle: {e}")
        return {"ok": False, "error": str(e), "action": "add_vehicle"}


async def tool_add_driver(name: str, phone: str = None, license_number: str = None,
                         status: str = "available") -> Dict:
    """
    Add a new driver.
    
    Args:
        name: Driver's name
        phone: Phone number
        license_number: Driver's license number
        status: Initial status (available, off_duty, etc.)
        
    Returns:
        Result dictionary
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Check if driver with same name exists
            existing = await conn.fetchval(
                "SELECT driver_id FROM drivers WHERE LOWER(name) = LOWER($1)",
                name
            )
            
            if existing:
                return {"ok": False, "error": f"Driver '{name}' already exists"}
            
            # Insert new driver
            driver_id = await conn.fetchval("""
                INSERT INTO drivers (name, phone, license_number, status)
                VALUES ($1, $2, $3, $4)
                RETURNING driver_id
            """, name, phone, license_number, status)
            
            return {
                "ok": True,
                "message": f"Driver {name} added successfully with ID {driver_id}",
                "driver_id": driver_id,
                "action": "add_driver"
            }
                
    except Exception as e:
        logger.error(f"Error adding driver: {e}")
        return {"ok": False, "error": str(e), "action": "add_driver"}


# Export all tools
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
    'tool_list_available_drivers',
    # New tools
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
    'tool_get_available_vehicles',
    'tool_get_available_drivers',
    'tool_get_all_paths',
    'tool_get_all_routes',
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

