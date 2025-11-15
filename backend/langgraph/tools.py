"""
LangGraph Tool Wrappers for MOVI Agent
Wraps backend service functions and Supabase connections for agent use
"""
from app.core import service
from app.core.supabase_client import get_conn
from typing import Dict, List, Optional
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
    Get all bookings for a specific trip.
    
    Args:
        trip_id: The trip ID to query
        
    Returns:
        List of booking dictionaries
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
                WHERE v.status = 'AVAILABLE'
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
                WHERE d.status = 'AVAILABLE'
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


# Export all tools
__all__ = [
    'tool_get_trip_status',
    'tool_get_bookings',
    'tool_assign_vehicle',
    'tool_remove_vehicle',
    'tool_cancel_trip',
    'tool_identify_trip_from_label',
    'tool_get_vehicles',
    'tool_get_drivers',
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
]

