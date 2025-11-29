# It contains 3 small helper functions:
# get_trip_consequences() → Trip summary (bookings, deployments, etc.)
# check_vehicle_availability() → Is vehicle free on this date?
# check_driver_availability() → Is driver free on this date?
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


async def check_vehicle_availability(vehicle_id: int, trip_date, exclude_trip_id: int = None) -> bool:
    """
    Check if a vehicle is available on a given date.
    
    A vehicle is unavailable if it's already deployed to another trip on the same date.
    
    Args:
        vehicle_id: The vehicle ID to check
        trip_date: Date as string 'YYYY-MM-DD', datetime.date object, or datetime.datetime object
        exclude_trip_id: Optional trip ID to exclude from the check (for updates to existing deployments)
        
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
    
    if exclude_trip_id:
        # Exclude the specified trip from the check
        query = """
        SELECT EXISTS(
            SELECT 1 
            FROM deployments d
            JOIN daily_trips dt ON d.trip_id = dt.trip_id
            WHERE d.vehicle_id = $1 
            AND dt.trip_date = $2
            AND d.trip_id != $3
        )
        """
        exists = await fetchval(query, vehicle_id, trip_date, exclude_trip_id)
    else:
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

async def check_driver_availability(driver_id: int, trip_date, target_trip_id: int = None) -> bool:
    """
    Check if a driver is available for assignment based on time overlap logic.
    
    A driver is unavailable if they're assigned to another trip that has overlapping time.
    Uses the same logic as tool_list_available_drivers for consistency.
    
    Args:
        driver_id: The driver ID to check
        trip_date: Date as string 'YYYY-MM-DD', datetime.date object, or datetime.datetime object
        target_trip_id: The trip ID we want to assign the driver to (to get its time)
        
    Returns:
        True if available, False if has time conflicts
    """
    from .db import fetchval, fetchrow, fetch
    from datetime import date, datetime, time as dt_time, timedelta
    
    # Convert string to date object if needed (asyncpg requires date objects)
    if isinstance(trip_date, str):
        trip_date = datetime.strptime(trip_date, '%Y-%m-%d').date()
    elif isinstance(trip_date, datetime):
        trip_date = trip_date.date()
    
    # If no target_trip_id provided, fall back to old date-only logic
    if not target_trip_id:
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
    
    # ✅ NEW: Use time overlap logic like tool_list_available_drivers
    
    # Get target trip time details
    trip_row = await fetchrow("""
        SELECT t.trip_date, r.shift_time, t.display_name
        FROM daily_trips t
        LEFT JOIN routes r ON t.route_id = r.route_id  
        WHERE t.trip_id = $1
    """, target_trip_id)
    
    if not trip_row:
        # Target trip not found - cannot determine availability
        return False
    
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
            hour, minute = map(int, time_str.split(':'))
            target_time = dt_time(hour, minute)
    
    if not target_time:
        # Cannot determine target trip time - fall back to date-only check
        query = """
        SELECT EXISTS(
            SELECT 1 
            FROM deployments d
            JOIN daily_trips dt ON d.trip_id = dt.trip_id
            WHERE d.driver_id = $1 
            AND dt.trip_date = $2
            AND dt.trip_id != $3
        )
        """
        exists = await fetchval(query, driver_id, trip_date, target_trip_id)
        return not exists
    
    # Get conflicting trips for this driver on same date
    conflicting_trips = await fetch("""
        SELECT t.trip_id, t.display_name, r.shift_time
        FROM deployments d
        JOIN daily_trips t ON t.trip_id = d.trip_id
        LEFT JOIN routes r ON t.route_id = r.route_id
        WHERE d.driver_id = $1 
          AND t.trip_date = $2
          AND t.trip_id != $3
    """, driver_id, trip_date, target_trip_id)
    
    if not conflicting_trips:
        # No other trips on this date - driver is available
        return True
    
    # Check for time conflicts using proper overlap logic
    trip_duration_minutes = 60  # Assume 60-minute trip duration
    
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
            
            # Check for overlap: trip1_end > trip2_start AND trip1_start < trip2_end
            overlaps = (target_end > conflict_start and target_start < conflict_end)
            
            if overlaps:
                # Time conflict found - driver not available
                return False
    
    # No time conflicts - driver is available
    return True
