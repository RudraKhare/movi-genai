# backend/app/core/service.py
"""
Business logic: assign_vehicle, remove_vehicle, cancel_trip.
Each operation is transactional and writes an audit log.
"""
import logging
from .db import transaction, fetchrow
from .supabase_client import get_conn
from .consequences import get_trip_consequences, check_vehicle_availability, check_driver_availability
from .audit import record_audit
from typing import Dict, Any, List

logger = logging.getLogger(__name__)
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
        # Check if COMPLETE deployment already exists (deployment_id with vehicle_id)
        # Allow completing orphaned deployments (deployment_id exists but vehicle_id is null)
        existing = await conn.fetchrow(
            """SELECT deployment_id, vehicle_id 
               FROM deployments 
               WHERE trip_id=$1""", 
            trip_id
        )
        if existing and existing['vehicle_id'] is not None:
            # Complete deployment - block
            raise ServiceError(f"Trip {trip_id} already has vehicle {existing['vehicle_id']} assigned. Remove it first if you want to assign a different vehicle.")
        elif existing and existing['vehicle_id'] is None:
            # Orphaned deployment - log that we're completing it
            logger.info(f"Completing orphaned deployment {existing['deployment_id']} for trip {trip_id}")
        # No deployment or orphaned deployment - proceed
        
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
        
        # Check driver availability using proper time overlap logic
        driver_available = await check_driver_availability(driver_id, trip_date, trip_id)
        if not driver_available:
            raise ServiceError(
                f"Driver {driver_id} is not available on {trip_date} "
                "(conflicts with another trip assignment)"
            )
        
        # Handle deployment creation/update
        if existing and existing['vehicle_id'] is None:
            # Update existing orphaned deployment
            deployment = await conn.fetchrow(
                """
                UPDATE deployments 
                SET vehicle_id = $1, driver_id = $2, deployed_at = NOW()
                WHERE trip_id = $3
                RETURNING deployment_id
                """,
                vehicle_id, driver_id, trip_id
            )
            deployment_id = deployment['deployment_id']
            deployment_action = "updated"
        else:
            # Create new deployment
            deployment = await conn.fetchrow(
                """
                INSERT INTO deployments (trip_id, vehicle_id, driver_id) 
                VALUES ($1, $2, $3)
                RETURNING deployment_id
                """,
                trip_id, vehicle_id, driver_id
            )
            deployment_id = deployment['deployment_id']
            deployment_action = "created"
        
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
            "deployment_id": deployment_id,
            "deployment_action": deployment_action
        }


async def assign_driver(
    trip_id: int, 
    driver_id: int, 
    user_id: int
) -> Dict[str, Any]:
    """
    Assign a driver to a trip (keeping existing vehicle assignment if any).
    
    This is a transactional operation that:
    1. Checks if the trip already has a deployment
    2. If yes: updates the driver, keeping the vehicle
    3. If no: creates a new deployment with just the driver
    4. Verifies driver availability on the trip date
    5. Records an audit log
    
    Args:
        trip_id: ID of the daily trip
        driver_id: ID of the driver to assign
        user_id: ID of the user performing the action (for audit)
        
    Returns:
        Dict with:
            - ok: True on success
            - trip_id: The trip ID
            - driver_id: The assigned driver ID
            - deployment_id: The deployment ID (created or updated)
            - deployment_updated: True if existing deployment was updated
            - deployment_created: True if new deployment was created
            
    Raises:
        ServiceError: If driver unavailable on trip date
        
    Example:
        result = await assign_driver(trip_id=1, driver_id=3, user_id=999)
        # Returns: {"ok": True, "trip_id": 1, "driver_id": 3, "deployment_id": 42, "deployment_updated": True}
    """
    async with transaction() as conn:
        # Get trip date for availability checks
        trip_info = await conn.fetchrow(
            "SELECT trip_date FROM daily_trips WHERE trip_id=$1", 
            trip_id
        )
        if not trip_info:
            raise ServiceError(f"Trip {trip_id} not found")
        
        trip_date = trip_info['trip_date']  # This is already a date object from asyncpg
        
        # Check driver availability using proper time overlap logic
        driver_available = await check_driver_availability(driver_id, trip_date, trip_id)
        if not driver_available:
            raise ServiceError(
                f"Driver {driver_id} is not available on {trip_date} "
                "(conflicts with another trip assignment)"
            )
        
        # Check if deployment already exists
        existing = await conn.fetchrow(
            "SELECT deployment_id, vehicle_id, driver_id FROM deployments WHERE trip_id=$1", 
            trip_id
        )
        
        if existing:
            # Update existing deployment with new driver
            await conn.execute(
                "UPDATE deployments SET driver_id=$1 WHERE trip_id=$2", 
                driver_id, trip_id
            )
            
            deployment_id = existing['deployment_id']
            
            # Record audit log
            await record_audit(
                conn, 
                action="assign_driver", 
                user_id=user_id, 
                entity_type="trip", 
                entity_id=trip_id,
                details={
                    "driver_id": driver_id, 
                    "previous_driver_id": existing["driver_id"],
                    "vehicle_id": existing["vehicle_id"],
                    "deployment_id": deployment_id,
                    "trip_date": str(trip_date)  # Convert date to string for JSON
                }
            )
            
            return {
                "ok": True, 
                "trip_id": trip_id, 
                "driver_id": driver_id,
                "deployment_id": deployment_id,
                "deployment_updated": True
            }
        else:
            # No existing deployment - create new one with just driver (no vehicle)
            deployment = await conn.fetchrow(
                """
                INSERT INTO deployments (trip_id, driver_id) 
                VALUES ($1, $2)
                RETURNING deployment_id
                """,
                trip_id, driver_id
            )
            
            deployment_id = deployment['deployment_id']
            
            # Record audit log
            await record_audit(
                conn, 
                action="assign_driver", 
                user_id=user_id, 
                entity_type="trip", 
                entity_id=trip_id,
                details={
                    "driver_id": driver_id,
                    "deployment_id": deployment_id,
                    "trip_date": str(trip_date)  # Convert date to string for JSON
                }
            )
            
            return {
                "ok": True, 
                "trip_id": trip_id, 
                "driver_id": driver_id,
                "deployment_id": deployment_id,
                "deployment_created": True
            }


async def assign_vehicle_only(
    trip_id: int, 
    vehicle_id: int, 
    user_id: int
) -> Dict[str, Any]:
    """
    Assign a vehicle to a trip (keeping existing driver assignment if any).
    
    This is a transactional operation that:
    1. Checks if the trip already has a deployment
    2. If yes: updates the vehicle, keeping the driver
    3. If no: creates a new deployment with just the vehicle
    4. Verifies vehicle availability on the trip date (with time overlap)
    5. Records an audit log
    
    Args:
        trip_id: ID of the daily trip
        vehicle_id: ID of the vehicle to assign
        user_id: ID of the user performing the action (for audit)
        
    Returns:
        Dict with:
            - ok: True on success
            - trip_id: The trip ID
            - vehicle_id: The assigned vehicle ID
            - deployment_id: The deployment ID (created or updated)
            - deployment_updated: True if existing deployment was updated
            - deployment_created: True if new deployment was created
            
    Raises:
        ServiceError: If vehicle unavailable on trip date/time
        
    Example:
        result = await assign_vehicle_only(trip_id=1, vehicle_id=5, user_id=999)
        # Returns: {"ok": True, "trip_id": 1, "vehicle_id": 5, "deployment_id": 42, "deployment_updated": True}
    """
    async with transaction() as conn:
        # Get trip date for availability checks
        trip_info = await conn.fetchrow(
            "SELECT trip_date FROM daily_trips WHERE trip_id=$1", 
            trip_id
        )
        if not trip_info:
            raise ServiceError(f"Trip {trip_id} not found")
        
        trip_date = trip_info['trip_date']
        
        # Check vehicle availability using time overlap logic
        vehicle_available = await check_vehicle_availability(vehicle_id, trip_date, trip_id)
        if not vehicle_available:
            raise ServiceError(
                f"Vehicle {vehicle_id} is not available on {trip_date} "
                "(conflicts with another trip assignment)"
            )
        
        # Check if deployment already exists
        existing = await conn.fetchrow(
            "SELECT deployment_id, vehicle_id, driver_id FROM deployments WHERE trip_id=$1", 
            trip_id
        )
        
        if existing:
            # Update existing deployment with new vehicle
            await conn.execute(
                "UPDATE deployments SET vehicle_id=$1 WHERE trip_id=$2", 
                vehicle_id, trip_id
            )
            
            deployment_id = existing['deployment_id']
            
            # Record audit log
            await record_audit(
                conn, 
                action="assign_vehicle", 
                user_id=user_id, 
                entity_type="trip", 
                entity_id=trip_id,
                details={
                    "vehicle_id": vehicle_id, 
                    "previous_vehicle_id": existing["vehicle_id"],
                    "driver_id": existing["driver_id"],
                    "deployment_id": deployment_id,
                    "trip_date": str(trip_date)
                }
            )
            
            return {
                "ok": True, 
                "trip_id": trip_id, 
                "vehicle_id": vehicle_id,
                "deployment_id": deployment_id,
                "deployment_updated": True
            }
        else:
            # No existing deployment - create new one with just vehicle (no driver)
            deployment = await conn.fetchrow(
                """
                INSERT INTO deployments (trip_id, vehicle_id) 
                VALUES ($1, $2)
                RETURNING deployment_id
                """,
                trip_id, vehicle_id
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
                    "deployment_id": deployment_id,
                    "trip_date": str(trip_date)
                }
            )
            
            return {
                "ok": True, 
                "trip_id": trip_id, 
                "vehicle_id": vehicle_id,
                "deployment_id": deployment_id,
                "deployment_created": True
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


async def get_available_vehicles_for_trip(trip_id: int) -> List[Dict[str, Any]]:
    """
    Get vehicles available for a specific trip, considering time conflicts.
    
    A vehicle is available if:
    1. It's not assigned to any active trip, OR
    2. It's not assigned to any trip with overlapping time on the same date
    
    Args:
        trip_id: The trip ID to check availability for
        
    Returns:
        List of available vehicles with their details
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        # First get the target trip details
        target_trip = await conn.fetchrow("""
            SELECT dt.trip_date, r.shift_time, r.route_name
            FROM daily_trips dt
            JOIN routes r ON dt.route_id = r.route_id
            WHERE dt.trip_id = $1
        """, trip_id)
        
        if not target_trip:
            return []
        
        target_date = target_trip['trip_date']
        target_time = target_trip['shift_time']
        
        # Get vehicles that don't have time conflicts
        # Check for any deployment on the same date (conservative approach)
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
                    -- Vehicle has no deployment
                    d.deployment_id IS NULL
                    OR
                    -- OR no active deployments on the same date
                    NOT EXISTS (
                        SELECT 1 
                        FROM deployments d2
                        JOIN daily_trips t2 ON d2.trip_id = t2.trip_id
                        WHERE d2.vehicle_id = v.vehicle_id
                            AND t2.live_status IN ('SCHEDULED', 'IN_PROGRESS')
                            AND t2.trip_date = $1
                    )
                )
            ORDER BY v.registration_number
        """, target_date)
        
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


async def create_route(route_name: str, path_id: int, user_id: int, shift_time: str = None, direction: str = "up") -> Dict[str, Any]:
    """Create a new route using an existing path and auto-create a daily trip"""
    from datetime import time as dt_time, date
    
    # Ensure direction is lowercase (database constraint)
    direction = direction.lower() if direction else "up"
    
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Verify path exists
            path_row = await conn.fetchrow("""
                SELECT path_id, path_name FROM paths WHERE path_id = $1
            """, path_id)
            
            if not path_row:
                raise ValueError(f"Path {path_id} not found")
            
            # Convert shift_time string to time object if provided
            time_obj = None
            if shift_time:
                try:
                    parts = shift_time.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    time_obj = dt_time(hour, minute)
                except (ValueError, IndexError) as e:
                    raise ValueError(f"Invalid time format: {shift_time}. Use HH:MM format.")
            
            # Create route with optional shift_time and direction
            if time_obj:
                route_row = await conn.fetchrow("""
                    INSERT INTO routes (route_name, path_id, shift_time, direction)
                    VALUES ($1, $2, $3, $4)
                    RETURNING route_id, route_name, path_id, shift_time, direction, created_at
                """, route_name, path_id, time_obj, direction)
            else:
                route_row = await conn.fetchrow("""
                    INSERT INTO routes (route_name, path_id, direction)
                    VALUES ($1, $2, $3)
                    RETURNING route_id, route_name, path_id, shift_time, direction, created_at
                """, route_name, path_id, direction)
            
            route_id = route_row['route_id']
            
            # Auto-create a daily trip for this route (for today)
            today = date.today()
            display_name = route_name
            
            trip_row = await conn.fetchrow("""
                INSERT INTO daily_trips (route_id, display_name, trip_date, live_status)
                VALUES ($1, $2, $3, 'SCHEDULED')
                RETURNING trip_id, route_id, display_name, trip_date, live_status
            """, route_id, display_name, today)
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'create_route', 'route', route_id, user_id,
                 json.dumps({"route_name": route_name, "path_id": path_id, "path_name": path_row['path_name'], "shift_time": shift_time, "direction": direction, "trip_id": trip_row['trip_id']}))
            
            return {
                **dict(route_row),
                "path_name": path_row['path_name'],
                "trip": dict(trip_row)
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


async def list_all_paths() -> List[Dict[str, Any]]:
    """List all paths in the system"""
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


async def list_all_routes() -> List[Dict[str, Any]]:
    """List all routes in the system"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                r.route_id,
                r.route_name,
                r.path_id,
                p.path_name,
                r.created_at,
                COUNT(DISTINCT t.trip_id) as trip_count
            FROM routes r
            LEFT JOIN paths p ON r.path_id = p.path_id
            LEFT JOIN daily_trips t ON r.route_id = t.route_id
            GROUP BY r.route_id, r.route_name, r.path_id, p.path_name, r.created_at
            ORDER BY r.route_name
        """)
        return [dict(r) for r in rows]


async def delete_stop(stop_id: int, force_delete: bool = False) -> Dict[str, Any]:
    """Delete a stop from the system
    
    Args:
        stop_id: The ID of the stop to delete
        force_delete: If True, remove stop from all paths and delete it anyway
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get stop name before deleting
            stop = await conn.fetchrow("""
                SELECT stop_id, name as stop_name FROM stops WHERE stop_id = $1
            """, stop_id)
            
            if not stop:
                return {"ok": False, "message": f"Stop with ID {stop_id} not found"}
            
            stop_name = stop['stop_name']
            
            # Check if stop is used in any paths - get full details
            dependent_paths = await conn.fetch("""
                SELECT DISTINCT p.path_id, p.path_name 
                FROM path_stops ps
                JOIN paths p ON ps.path_id = p.path_id
                WHERE ps.stop_id = $1
                ORDER BY p.path_name
            """, stop_id)
            
            if len(dependent_paths) > 0 and not force_delete:
                # Build detailed list of dependent paths
                path_list = [{"path_id": p['path_id'], "path_name": p['path_name']} for p in dependent_paths]
                path_names = ", ".join([p['path_name'] for p in dependent_paths])
                return {
                    "ok": False, 
                    "message": f"Cannot delete stop '{stop_name}' - it is used in {len(dependent_paths)} path(s): {path_names}",
                    "dependent_entities": path_list,
                    "entity_type": "paths",
                    "can_force_delete": True
                }
            
            if force_delete and len(dependent_paths) > 0:
                # Remove stop from all paths first
                await conn.execute("""
                    DELETE FROM path_stops WHERE stop_id = $1
                """, stop_id)
            
            # Delete the stop
            await conn.execute("""
                DELETE FROM stops WHERE stop_id = $1
            """, stop_id)
            
            # Audit log
            forced_note = " (force deleted from paths)" if force_delete and len(dependent_paths) > 0 else ""
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'delete_stop', 'stop', stop_id, 1, json.dumps({
                "stop_name": stop_name, 
                "force_deleted": force_delete,
                "removed_from_paths": [p['path_name'] for p in dependent_paths] if force_delete else []
            }))
            
            return {"ok": True, "message": f"Stop '{stop_name}' has been deleted successfully{forced_note}."}


async def delete_path(path_id: int, force_delete: bool = False) -> Dict[str, Any]:
    """Delete a path from the system
    
    Args:
        path_id: The ID of the path to delete
        force_delete: If True, delete all routes using this path first, then delete the path
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get path name before deleting
            path = await conn.fetchrow("""
                SELECT path_id, path_name FROM paths WHERE path_id = $1
            """, path_id)
            
            if not path:
                return {"ok": False, "message": f"Path with ID {path_id} not found"}
            
            path_name = path['path_name']
            
            # Check if path is used in any routes - get full details
            dependent_routes = await conn.fetch("""
                SELECT route_id, route_name 
                FROM routes 
                WHERE path_id = $1
                ORDER BY route_name
            """, path_id)
            
            if len(dependent_routes) > 0 and not force_delete:
                # Build detailed list of dependent routes
                route_list = [{"route_id": r['route_id'], "route_name": r['route_name']} for r in dependent_routes]
                route_names = ", ".join([r['route_name'] for r in dependent_routes])
                return {
                    "ok": False, 
                    "message": f"Cannot delete path '{path_name}' - it is used by {len(dependent_routes)} route(s): {route_names}",
                    "dependent_entities": route_list,
                    "entity_type": "routes",
                    "can_force_delete": True
                }
            
            deleted_routes = []
            if force_delete and len(dependent_routes) > 0:
                # Delete all trips for these routes first, then delete routes
                for route in dependent_routes:
                    # Delete trips for this route
                    await conn.execute("""
                        DELETE FROM trips WHERE route_id = $1
                    """, route['route_id'])
                    # Delete the route
                    await conn.execute("""
                        DELETE FROM routes WHERE route_id = $1
                    """, route['route_id'])
                    deleted_routes.append(route['route_name'])
            
            # Delete path_stops first (foreign key constraint)
            await conn.execute("""
                DELETE FROM path_stops WHERE path_id = $1
            """, path_id)
            
            # Delete the path
            await conn.execute("""
                DELETE FROM paths WHERE path_id = $1
            """, path_id)
            
            # Audit log
            forced_note = f" (also deleted {len(deleted_routes)} route(s): {', '.join(deleted_routes)})" if deleted_routes else ""
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'delete_path', 'path', path_id, 1, json.dumps({
                "path_name": path_name,
                "force_deleted": force_delete,
                "deleted_routes": deleted_routes
            }))
            
            return {"ok": True, "message": f"Path '{path_name}' has been deleted successfully{forced_note}."}


async def delete_route(route_id: int) -> Dict[str, Any]:
    """Delete a route from the system (also deletes associated trips)"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get route info before deleting
            route = await conn.fetchrow("""
                SELECT route_id, route_name FROM routes WHERE route_id = $1
            """, route_id)
            
            if not route:
                return {"ok": False, "message": f"Route with ID {route_id} not found"}
            
            route_name = route['route_name']
            
            # Check for trips with bookings
            trips_with_bookings = await conn.fetchval("""
                SELECT COUNT(*) FROM daily_trips t
                JOIN bookings b ON t.trip_id = b.trip_id
                WHERE t.route_id = $1
            """, route_id)
            
            if trips_with_bookings > 0:
                return {
                    "ok": False, 
                    "message": f"Cannot delete route '{route_name}' - it has trips with active bookings. Cancel those bookings first."
                }
            
            # Count trips before deleting
            trip_count = await conn.fetchval("""
                SELECT COUNT(*) FROM daily_trips WHERE route_id = $1
            """, route_id)
            
            # Delete associated trips first
            await conn.execute("""
                DELETE FROM daily_trips WHERE route_id = $1
            """, route_id)
            
            # Delete the route
            await conn.execute("""
                DELETE FROM routes WHERE route_id = $1
            """, route_id)
            
            # Audit log
            await conn.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                VALUES ($1, $2, $3, $4, $5)
            """, 'delete_route', 'route', route_id, 1, json.dumps({
                "route_name": route_name, 
                "trips_deleted": trip_count or 0
            }))
            
            trips_msg = f" ({trip_count} associated trip(s) also deleted)" if trip_count else ""
            return {"ok": True, "message": f"Route '{route_name}' has been deleted successfully{trips_msg}."}
