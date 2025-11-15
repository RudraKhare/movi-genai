# backend/app/core/service.py
"""
Business logic: assign_vehicle, remove_vehicle, cancel_trip.
Each operation is transactional and writes an audit log.
"""
from .db import transaction, fetchrow
from .supabase_client import get_conn
from .consequences import get_trip_consequences, check_vehicle_availability, check_driver_availability
from .audit import record_audit
from typing import Dict, Any, List
import json


class ServiceError(Exception):
    """
    Exception raised for business logic violations.
    
    This should be caught by the FastAPI route layer and converted to
    HTTPException with status_code=400.
    """
    pass


async def assign_vehicle(
    trip_id: int, 
    vehicle_id: int, 
    driver_id: int, 
    user_id: int
) -> Dict[str, Any]:
    """
    Assign a vehicle and driver to a trip.
    
    This is a transactional operation that:
    1. Checks if the trip already has a deployment
    2. Verifies vehicle and driver availability on the trip date
    3. Creates a new deployment record
    4. Records an audit log
    
    Args:
        trip_id: ID of the daily trip
        vehicle_id: ID of the vehicle to assign
        driver_id: ID of the driver to assign
        user_id: ID of the user performing the action (for audit)
        
    Returns:
        Dict with:
            - ok: True on success
            - trip_id: The trip ID
            - vehicle_id: The assigned vehicle ID
            - driver_id: The assigned driver ID
            - deployment_id: The created deployment ID
            
    Raises:
        ServiceError: If trip already has deployment, or vehicle/driver unavailable
        
    Example:
        result = await assign_vehicle(
            trip_id=1, 
            vehicle_id=5, 
            driver_id=3, 
            user_id=999
        )
        # Returns: {"ok": True, "trip_id": 1, "vehicle_id": 5, "driver_id": 3, "deployment_id": 42}
    """
    async with transaction() as conn:
        # Check if deployment already exists
        existing = await conn.fetchrow(
            "SELECT deployment_id FROM deployments WHERE trip_id=$1", 
            trip_id
        )
        if existing:
            raise ServiceError(f"Trip {trip_id} already has a deployment (ID: {existing['deployment_id']})")
        
        # Get trip date for availability checks
        trip_info = await conn.fetchrow(
            "SELECT trip_date FROM daily_trips WHERE trip_id=$1", 
            trip_id
        )
        if not trip_info:
            raise ServiceError(f"Trip {trip_id} not found")
        
        trip_date = trip_info['trip_date']  # This is already a date object from asyncpg
        
        # Check vehicle availability
        vehicle_available = await check_vehicle_availability(vehicle_id, trip_date)
        if not vehicle_available:
            raise ServiceError(
                f"Vehicle {vehicle_id} is not available on {trip_date} "
                "(already deployed to another trip)"
            )
        
        # Check driver availability
        driver_available = await check_driver_availability(driver_id, trip_date)
        if not driver_available:
            raise ServiceError(
                f"Driver {driver_id} is not available on {trip_date} "
                "(already assigned to another trip)"
            )
        
        # Create deployment
        deployment = await conn.fetchrow(
            """
            INSERT INTO deployments (trip_id, vehicle_id, driver_id) 
            VALUES ($1, $2, $3)
            RETURNING deployment_id
            """,
            trip_id, vehicle_id, driver_id
        )
        
        deployment_id = deployment['deployment_id']
        
        # Record audit log
        await record_audit(
            conn, 
            action="assign_vehicle", 
            user_id=user_id, 
            entity_type="trip", 
            entity_id=trip_id,
            details={
                "vehicle_id": vehicle_id, 
                "driver_id": driver_id,
                "deployment_id": deployment_id,
                "trip_date": str(trip_date)  # Convert date to string for JSON
            }
        )
        
        return {
            "ok": True, 
            "trip_id": trip_id, 
            "vehicle_id": vehicle_id, 
            "driver_id": driver_id,
            "deployment_id": deployment_id
        }


async def remove_vehicle(
    trip_id: int, 
    user_id: int, 
    cancel_bookings: bool = True
) -> Dict[str, Any]:
    """
    Remove vehicle deployment from a trip.
    
    This is a transactional operation that:
    1. Verifies a deployment exists
    2. Optionally cancels all CONFIRMED bookings
    3. Deletes the deployment record
    4. Records an audit log
    
    Args:
        trip_id: ID of the daily trip
        user_id: ID of the user performing the action (for audit)
        cancel_bookings: If True, cancel all CONFIRMED bookings (default: True)
        
    Returns:
        Dict with:
            - ok: True on success
            - trip_id: The trip ID
            - vehicle_id: The removed vehicle ID
            - driver_id: The removed driver ID
            - bookings_cancelled: Number of bookings cancelled (if cancel_bookings=True)
            
    Raises:
        ServiceError: If no deployment exists for the trip
        
    Example:
        result = await remove_vehicle(trip_id=1, user_id=999, cancel_bookings=True)
        # Returns: {"ok": True, "trip_id": 1, "vehicle_id": 5, "driver_id": 3, "bookings_cancelled": 12}
    """
    async with transaction() as conn:
        # Get existing deployment
        dep = await conn.fetchrow(
            "SELECT deployment_id, vehicle_id, driver_id FROM deployments WHERE trip_id=$1", 
            trip_id
        )
        if not dep:
            raise ServiceError(f"No deployment found for trip {trip_id}")
        
        vehicle_id = dep['vehicle_id']
        driver_id = dep['driver_id']
        deployment_id = dep['deployment_id']
        bookings_cancelled = 0
        
        # Cancel bookings if requested
        if cancel_bookings:
            result = await conn.execute(
                """
                UPDATE bookings 
                SET status='CANCELLED' 
                WHERE trip_id=$1 AND status='CONFIRMED'
                """, 
                trip_id
            )
            # Parse result string like "UPDATE 12" to get count
            bookings_cancelled = int(result.split()[-1]) if result else 0
        
        # Delete deployment
        await conn.execute("DELETE FROM deployments WHERE trip_id=$1", trip_id)
        
        # Record audit log
        await record_audit(
            conn, 
            action="remove_vehicle", 
            user_id=user_id, 
            entity_type="trip", 
            entity_id=trip_id, 
            details={
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "deployment_id": deployment_id,
                "bookings_cancelled": bookings_cancelled
            }
        )
        
        return {
            "ok": True, 
            "trip_id": trip_id, 
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "bookings_cancelled": bookings_cancelled
        }


async def cancel_trip(trip_id: int, user_id: int) -> Dict[str, Any]:
    """
    Cancel a trip and all its confirmed bookings.
    
    This is a transactional operation that:
    1. Updates trip status to CANCELLED
    2. Cancels all CONFIRMED bookings
    3. Records an audit log
    
    Args:
        trip_id: ID of the daily trip to cancel
        user_id: ID of the user performing the action (for audit)
        
    Returns:
        Dict with:
            - ok: True on success
            - trip_id: The cancelled trip ID
            - bookings_cancelled: Number of bookings cancelled
            
    Example:
        result = await cancel_trip(trip_id=1, user_id=999)
        # Returns: {"ok": True, "trip_id": 1, "bookings_cancelled": 15}
    """
    async with transaction() as conn:
        # Verify trip exists
        trip = await conn.fetchrow(
            "SELECT live_status FROM daily_trips WHERE trip_id=$1", 
            trip_id
        )
        if not trip:
            raise ServiceError(f"Trip {trip_id} not found")
        
        # Update trip status
        await conn.execute(
            "UPDATE daily_trips SET live_status='CANCELLED' WHERE trip_id=$1", 
            trip_id
        )
        
        # Cancel all confirmed bookings
        result = await conn.execute(
            """
            UPDATE bookings 
            SET status='CANCELLED' 
            WHERE trip_id=$1 AND status='CONFIRMED'
            """, 
            trip_id
        )
        
        # Parse result string like "UPDATE 15" to get count
        bookings_cancelled = int(result.split()[-1]) if result else 0
        
        # Record audit log
        await record_audit(
            conn, 
            action="cancel_trip", 
            user_id=user_id, 
            entity_type="trip", 
            entity_id=trip_id, 
            details={
                "previous_status": trip['live_status'],
                "bookings_cancelled": bookings_cancelled
            }
        )
        
        return {
            "ok": True, 
            "trip_id": trip_id,
            "bookings_cancelled": bookings_cancelled
        }


async def get_trip_info(trip_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a trip including deployment and booking stats.
    
    This is a convenience function that combines trip data with deployment
    and booking information. Useful for the LangGraph agent to get context.
    
    Args:
        trip_id: ID of the daily trip
        
    Returns:
        Dict with trip details, or empty dict if not found
    """
    return await get_trip_consequences(trip_id)


# ============ NEW SERVICE FUNCTIONS FOR 16 ACTIONS ============

async def get_unassigned_vehicles() -> List[Dict[str, Any]]:
    """
    Get all vehicles not currently assigned to any active trip.
    
    A vehicle is considered "unassigned" if:
    - It has no deployment at all, OR
    - Its only deployments are for trips that are COMPLETED, CANCELLED, or past trips
    
    Returns vehicles with their current driver assignment (if any)
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT
                v.vehicle_id,
                v.registration_number,
                v.capacity,
                v.status,
                d.driver_id,
                dr.name as driver_name
            FROM vehicles v
            LEFT JOIN deployments d ON v.vehicle_id = d.vehicle_id
            LEFT JOIN daily_trips t ON d.trip_id = t.trip_id
            LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
            WHERE v.status = 'available'
                AND (
                    -- Vehicle has no active deployment
                    d.deployment_id IS NULL
                    OR
                    -- OR all its deployments are for inactive trips
                    NOT EXISTS (
                        SELECT 1 
                        FROM deployments d2
                        JOIN daily_trips t2 ON d2.trip_id = t2.trip_id
                        WHERE d2.vehicle_id = v.vehicle_id
                            AND t2.live_status IN ('SCHEDULED', 'IN_PROGRESS')
                    )
                )
            ORDER BY v.registration_number
        """)
        return [dict(r) for r in rows]


async def get_trip_details(trip_id: int) -> Dict[str, Any]:
    """Get comprehensive trip details including all related data"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Get trip info
        trip_row = await conn.fetchrow("""
            SELECT 
                t.trip_id,
                t.display_name,
                t.trip_date,
                t.live_status,
                t.booking_status_percentage,
                r.route_name,
                p.path_name,
                d.vehicle_id,
                d.driver_id,
                v.registration_number,
                dr.name as driver_name
            FROM daily_trips t
            LEFT JOIN routes r ON t.route_id = r.route_id
            LEFT JOIN paths p ON r.path_id = p.path_id
            LEFT JOIN deployments d ON t.trip_id = d.trip_id
            LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
            LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
            WHERE t.trip_id = $1
        """, trip_id)
        
        if not trip_row:
            return {}
        
        # Get bookings (no users table - user_name is in bookings)
        bookings = await conn.fetch("""
            SELECT 
                b.booking_id,
                b.user_id,
                b.user_name,
                b.seats,
                b.status,
                b.created_at
            FROM bookings b
            WHERE b.trip_id = $1
        """, trip_id)
        
        return {
            **dict(trip_row),
            "bookings": [dict(b) for b in bookings],
            "booking_count": len(bookings)
        }


async def list_all_stops() -> List[Dict[str, Any]]:
    """List all stops in the system"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                stop_id,
                name as stop_name,
                latitude,
                longitude,
                created_at
            FROM stops
            ORDER BY name
        """)
        return [dict(r) for r in rows]


async def list_stops_for_path(path_id: int) -> List[Dict[str, Any]]:
    """List all stops for a specific path in order"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
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
        """, path_id)
        return [dict(r) for r in rows]


async def list_routes_using_path(path_id: int) -> List[Dict[str, Any]]:
    """List all routes that use a specific path"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                r.route_id,
                r.route_name,
                r.path_id,
                p.path_name,
                COUNT(DISTINCT t.trip_id) as trip_count
            FROM routes r
            JOIN paths p ON r.path_id = p.path_id
            LEFT JOIN daily_trips t ON r.route_id = t.route_id
            WHERE r.path_id = $1
            GROUP BY r.route_id, r.route_name, r.path_id, p.path_name
            ORDER BY r.route_name
        """, path_id)
        return [dict(r) for r in rows]


async def create_stop(stop_name: str, latitude: float = None, longitude: float = None, user_id: int = 1) -> Dict[str, Any]:
    """Create a new stop with optional coordinates"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Insert stop with optional coordinates (default to NULL)
            stop_row = await conn.fetchrow("""
                INSERT INTO stops (name, latitude, longitude)
                VALUES ($1, $2, $3)
                RETURNING stop_id, name as stop_name, latitude, longitude, created_at
            """, stop_name, latitude, longitude)
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'create_stop', 'stop', stop_row['stop_id'], user_id, 
                 json.dumps({"stop_name": stop_name, "latitude": latitude, "longitude": longitude}))
            
            return dict(stop_row)


async def create_path(path_name: str, stop_names: List[str], user_id: int) -> Dict[str, Any]:
    """Create a new path with ordered stops"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Create path
            path_row = await conn.fetchrow("""
                INSERT INTO paths (path_name)
                VALUES ($1)
                RETURNING path_id, path_name, created_at
            """, path_name)
            
            path_id = path_row['path_id']
            
            # Find stops by name and add to path
            stop_order = 1
            added_stops = []
            for stop_name in stop_names:
                stop_row = await conn.fetchrow("""
                    SELECT stop_id, name as stop_name
                    FROM stops
                    WHERE LOWER(name) = LOWER($1)
                    LIMIT 1
                """, stop_name.strip())
                
                if stop_row:
                    await conn.execute("""
                        INSERT INTO path_stops (path_id, stop_id, stop_order)
                        VALUES ($1, $2, $3)
                    """, path_id, stop_row['stop_id'], stop_order)
                    added_stops.append(dict(stop_row))
                    stop_order += 1
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'create_path', 'path', path_id, user_id,
                 json.dumps({"path_name": path_name, "stops": stop_names, "added_count": len(added_stops)}))
            
            return {
                **dict(path_row),
                "stops": added_stops,
                "stop_count": len(added_stops)
            }


async def create_route(route_name: str, path_id: int, user_id: int) -> Dict[str, Any]:
    """Create a new route using an existing path"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Verify path exists
            path_row = await conn.fetchrow("""
                SELECT path_id, path_name FROM paths WHERE path_id = $1
            """, path_id)
            
            if not path_row:
                raise ValueError(f"Path {path_id} not found")
            
            # Create route
            route_row = await conn.fetchrow("""
                INSERT INTO routes (route_name, path_id)
                VALUES ($1, $2)
                RETURNING route_id, route_name, path_id, created_at
            """, route_name, path_id)
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'create_route', 'route', route_row['route_id'], user_id,
                 json.dumps({"route_name": route_name, "path_id": path_id, "path_name": path_row['path_name']}))
            
            return {
                **dict(route_row),
                "path_name": path_row['path_name']
            }


async def update_trip_time(trip_id: int, new_time: str, user_id: int) -> Dict[str, Any]:
    """Update trip departure time"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get old trip info
            old_trip = await conn.fetchrow("""
                SELECT display_name, trip_date FROM daily_trips WHERE trip_id = $1
            """, trip_id)
            
            if not old_trip:
                raise ValueError(f"Trip {trip_id} not found")
            
            # Parse display_name to replace time
            # Format: "Path-1 - 08:00" -> "Path-1 - 09:00"
            old_display = old_trip['display_name']
            import re
            new_display = re.sub(r'\d{2}:\d{2}', new_time, old_display)
            
            # Update trip
            updated_row = await conn.fetchrow("""
                UPDATE daily_trips
                SET display_name = $1
                WHERE trip_id = $2
                RETURNING trip_id, display_name, trip_date
            """, new_display, trip_id)
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'update_trip_time', 'trip', trip_id, user_id,
                 json.dumps({"old_display": old_display, "new_display": new_display, "new_time": new_time}))
            
            return dict(updated_row)


async def rename_stop(stop_id: int, new_name: str, user_id: int) -> Dict[str, Any]:
    """Rename an existing stop"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get old name
            old_stop = await conn.fetchrow("""
                SELECT name as stop_name FROM stops WHERE stop_id = $1
            """, stop_id)
            
            if not old_stop:
                raise ValueError(f"Stop {stop_id} not found")
            
            # Update name
            updated_row = await conn.fetchrow("""
                UPDATE stops
                SET name = $1
                WHERE stop_id = $2
                RETURNING stop_id, name as stop_name, latitude, longitude
            """, new_name, stop_id)
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'rename_stop', 'stop', stop_id, user_id,
                 json.dumps({"old_name": old_stop['stop_name'], "new_name": new_name}))
            
            return dict(updated_row)


async def duplicate_route(route_id: int, user_id: int) -> Dict[str, Any]:
    """Duplicate an existing route with its path and stops"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get original route
            orig_route = await conn.fetchrow("""
                SELECT r.route_name, r.path_id, p.path_name
                FROM routes r
                JOIN paths p ON r.path_id = p.path_id
                WHERE r.route_id = $1
            """, route_id)
            
            if not orig_route:
                raise ValueError(f"Route {route_id} not found")
            
            # Duplicate path
            new_path_name = f"{orig_route['path_name']} (Copy)"
            new_path = await conn.fetchrow("""
                INSERT INTO paths (path_name)
                VALUES ($1)
                RETURNING path_id, path_name
            """, new_path_name)
            
            # Copy path_stops
            await conn.execute("""
                INSERT INTO path_stops (path_id, stop_id, stop_order)
                SELECT $1, stop_id, stop_order
                FROM path_stops
                WHERE path_id = $2
            """, new_path['path_id'], orig_route['path_id'])
            
            # Create new route
            new_route_name = f"{orig_route['route_name']} (Copy)"
            new_route = await conn.fetchrow("""
                INSERT INTO routes (route_name, path_id)
                VALUES ($1, $2)
                RETURNING route_id, route_name, path_id, created_at
            """, new_route_name, new_path['path_id'])
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'duplicate_route', 'route', new_route['route_id'], user_id,
                 json.dumps({"original_route_id": route_id, "new_route_name": new_route_name}))
            
            return {
                **dict(new_route),
                "path_name": new_path['path_name'],
                "original_route_id": route_id
            }
