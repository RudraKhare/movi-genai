# backend/app/core/service.py
"""
Business logic: assign_vehicle, remove_vehicle, cancel_trip.
Each operation is transactional and writes an audit log.
"""
from .db import transaction, fetchrow
from .consequences import get_trip_consequences, check_vehicle_availability, check_driver_availability
from .audit import record_audit
from typing import Dict, Any


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
