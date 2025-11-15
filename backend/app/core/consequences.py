# backend/app/core/consequences.py
"""
Compute consequences for a trip (bookings, deployment, seats).
This is the data Movi will use in check_consequences node.
"""
from .db import fetchrow
from typing import Dict, Any, Optional


async def get_trip_consequences(trip_id: int) -> Dict[str, Any]:
    """
    Calculate the consequences of modifying a trip.
    
    This function is used by the LangGraph agent's "check_consequences" node
    to determine if an action (assign/remove vehicle, cancel trip) will affect
    existing bookings.
    
    Args:
        trip_id: The ID of the daily trip to analyze
        
    Returns:
        Dictionary containing:
            - trip_id: The trip ID
            - display_name: Human-readable trip name (e.g., "Morning Shift - Gavipuram to Electronic City")
            - live_status: Current status (SCHEDULED, RUNNING, COMPLETED, CANCELLED)
            - vehicle_id: Currently assigned vehicle ID (or None)
            - driver_id: Currently assigned driver ID (or None)
            - booked_count: Number of CONFIRMED bookings
            - seats_booked: Total seats reserved in CONFIRMED bookings
            - has_deployment: Whether a vehicle is currently assigned
            - has_bookings: Whether there are any confirmed bookings
            
        Empty dict if trip not found.
        
    Example:
        {
            "trip_id": 1,
            "display_name": "Morning Shift - Gavipuram to Electronic City",
            "live_status": "SCHEDULED",
            "vehicle_id": 5,
            "driver_id": 3,
            "booked_count": 12,
            "seats_booked": 15,
            "has_deployment": True,
            "has_bookings": True
        }
    """
    query = """
    SELECT 
        dt.trip_id, 
        dt.display_name, 
        dt.live_status,
        d.deployment_id,
        d.vehicle_id,
        d.driver_id,
        COUNT(b.booking_id) FILTER (WHERE b.status='CONFIRMED') AS booked_count,
        COALESCE(SUM(b.seats) FILTER (WHERE b.status='CONFIRMED'), 0) AS seats_booked
    FROM daily_trips dt
    LEFT JOIN deployments d ON d.trip_id = dt.trip_id
    LEFT JOIN bookings b ON b.trip_id = dt.trip_id
    WHERE dt.trip_id = $1
    GROUP BY dt.trip_id, d.deployment_id, d.vehicle_id, d.driver_id, dt.display_name, dt.live_status
    """
    
    row = await fetchrow(query, trip_id)
    
    if not row:
        return {}
    
    # Normalize keys to friendly types for LangGraph
    booked_count = int(row.get("booked_count") or 0)
    seats_booked = int(row.get("seats_booked") or 0)
    
    return {
        "trip_id": row.get("trip_id"),
        "display_name": row.get("display_name"),
        "live_status": row.get("live_status"),
        "vehicle_id": row.get("vehicle_id"),
        "driver_id": row.get("driver_id"),
        "booked_count": booked_count,
        "seats_booked": seats_booked,
        "has_deployment": row.get("deployment_id") is not None,
        "has_bookings": booked_count > 0,
    }


async def get_vehicle_capacity(vehicle_id: int) -> Optional[int]:
    """
    Get the seating capacity of a vehicle.
    
    Args:
        vehicle_id: The vehicle ID
        
    Returns:
        Seating capacity, or None if vehicle not found
    """
    from .db import fetchval
    
    query = "SELECT capacity FROM vehicles WHERE vehicle_id = $1"
    return await fetchval(query, vehicle_id)


async def check_vehicle_availability(vehicle_id: int, trip_date) -> bool:
    """
    Check if a vehicle is available on a given date.
    
    A vehicle is unavailable if it's already deployed to another trip on the same date.
    
    Args:
        vehicle_id: The vehicle ID to check
        trip_date: Date as string 'YYYY-MM-DD', datetime.date object, or datetime.datetime object
        
    Returns:
        True if available, False if already deployed
    """
    from .db import fetchval
    from datetime import date, datetime
    
    # Convert string to date object if needed (asyncpg requires date objects)
    if isinstance(trip_date, str):
        trip_date = datetime.strptime(trip_date, '%Y-%m-%d').date()
    elif isinstance(trip_date, datetime):
        trip_date = trip_date.date()
    
    query = """
    SELECT EXISTS(
        SELECT 1 
        FROM deployments d
        JOIN daily_trips dt ON d.trip_id = dt.trip_id
        WHERE d.vehicle_id = $1 
        AND dt.trip_date = $2
    )
    """
    
    exists = await fetchval(query, vehicle_id, trip_date)
    return not exists  # Return True if NOT exists (i.e., available)


async def check_driver_availability(driver_id: int, trip_date) -> bool:
    """
    Check if a driver is available on a given date.
    
    A driver is unavailable if they're already assigned to another trip on the same date.
    
    Args:
        driver_id: The driver ID to check
        trip_date: Date as string 'YYYY-MM-DD', datetime.date object, or datetime.datetime object
        
    Returns:
        True if available, False if already assigned
    """
    from .db import fetchval
    from datetime import date, datetime
    
    # Convert string to date object if needed (asyncpg requires date objects)
    if isinstance(trip_date, str):
        trip_date = datetime.strptime(trip_date, '%Y-%m-%d').date()
    elif isinstance(trip_date, datetime):
        trip_date = trip_date.date()
    
    query = """
    SELECT EXISTS(
        SELECT 1 
        FROM deployments d
        JOIN daily_trips dt ON d.trip_id = dt.trip_id
        WHERE d.driver_id = $1 
        AND dt.trip_date = $2
    )
    """
    
    exists = await fetchval(query, driver_id, trip_date)
    return not exists  # Return True if NOT exists (i.e., available)
