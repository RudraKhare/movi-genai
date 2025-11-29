"""
Resources API - Drivers and Vehicles with Dynamic Availability
Provides endpoints for listing and getting details of drivers and vehicles
with real-time availability computed from trip assignments.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, date, time, timedelta
from app.core.supabase_client import get_conn
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resources", tags=["resources"])

# ===================== DRIVER ENDPOINTS =====================

@router.get("/drivers/all")
async def get_all_drivers() -> List[Dict[str, Any]]:
    """
    Get all drivers with their current availability status.
    
    Returns list of drivers with:
    - Basic info (id, name, phone, license)
    - Current availability status (Available, Unavailable, Available with upcoming trip)
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get all drivers
            drivers = await conn.fetch("""
                SELECT 
                    driver_id,
                    name,
                    phone,
                    license_number,
                    status,
                    created_at
                FROM drivers
                ORDER BY name
            """)
            
            result = []
            now = datetime.now()
            today = date.today()
            
            for driver in drivers:
                driver_dict = dict(driver)
                
                # Compute dynamic availability
                availability = await _compute_driver_availability(conn, driver['driver_id'], today, now)
                driver_dict['availability'] = availability
                
                result.append(driver_dict)
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drivers/{driver_id}")
async def get_driver_details(driver_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific driver including:
    - All driver fields
    - Current dynamic availability
    - Today's assigned trips
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get driver info
            driver = await conn.fetchrow("""
                SELECT 
                    driver_id,
                    name,
                    phone,
                    license_number,
                    status,
                    created_at
                FROM drivers
                WHERE driver_id = $1
            """, driver_id)
            
            if not driver:
                raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")
            
            driver_dict = dict(driver)
            now = datetime.now()
            today = date.today()
            
            # Compute dynamic availability
            availability = await _compute_driver_availability(conn, driver_id, today, now)
            driver_dict['availability'] = availability
            
            # Get today's trips for this driver
            today_trips = await conn.fetch("""
                SELECT 
                    t.trip_id,
                    t.display_name,
                    t.live_status,
                    r.shift_time,
                    v.registration_number as vehicle_registration,
                    t.booking_status_percentage
                FROM daily_trips t
                JOIN deployments d ON t.trip_id = d.trip_id
                LEFT JOIN routes r ON t.route_id = r.route_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                WHERE d.driver_id = $1 AND t.trip_date = $2
                ORDER BY r.shift_time
            """, driver_id, today)
            
            driver_dict['todays_trips'] = [dict(trip) for trip in today_trips]
            
            return driver_dict
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching driver {driver_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _compute_driver_availability(conn, driver_id: int, today: date, now: datetime) -> Dict[str, Any]:
    """
    Compute dynamic availability for a driver based on current trips.
    
    Returns:
        {
            "status": "available" | "unavailable" | "available_upcoming",
            "message": "Available" | "Unavailable (Busy until HH:MM)" | "Available now, next trip at HH:MM",
            "current_trip": {...} | None,
            "next_trip": {...} | None,
            "busy_until": "HH:MM" | None
        }
    """
    current_time = now.time()
    
    # Get all trips for this driver today
    trips = await conn.fetch("""
        SELECT 
            t.trip_id,
            t.display_name,
            t.live_status,
            r.shift_time,
            r.route_name
        FROM daily_trips t
        JOIN deployments d ON t.trip_id = d.trip_id
        LEFT JOIN routes r ON t.route_id = r.route_id
        WHERE d.driver_id = $1 AND t.trip_date = $2
        ORDER BY r.shift_time
    """, driver_id, today)
    
    if not trips:
        return {
            "status": "available",
            "message": "Available (No trips today)",
            "current_trip": None,
            "next_trip": None,
            "busy_until": None
        }
    
    # Assume each trip takes 60 minutes
    TRIP_DURATION_MINUTES = 60
    
    current_trip = None
    next_trip = None
    
    for trip in trips:
        shift_time = trip['shift_time']
        if not shift_time:
            # Try to extract time from display_name (e.g., "Path-1 - 08:00")
            display_name = trip['display_name'] or ''
            if ' - ' in display_name:
                time_part = display_name.split(' - ')[-1]
                try:
                    shift_time = datetime.strptime(time_part, "%H:%M").time()
                except ValueError:
                    continue
            else:
                continue
        
        trip_start = shift_time
        trip_end_dt = datetime.combine(today, trip_start) + timedelta(minutes=TRIP_DURATION_MINUTES)
        trip_end = trip_end_dt.time()
        
        # Check if this trip is currently active
        if trip_start <= current_time <= trip_end:
            # Currently on this trip
            current_trip = {
                "trip_id": trip['trip_id'],
                "display_name": trip['display_name'],
                "shift_time": str(shift_time)[:5] if shift_time else None,
                "busy_until": str(trip_end)[:5]
            }
        elif trip_start > current_time and next_trip is None:
            # This is the next upcoming trip
            next_trip = {
                "trip_id": trip['trip_id'],
                "display_name": trip['display_name'],
                "shift_time": str(shift_time)[:5] if shift_time else None
            }
    
    if current_trip:
        return {
            "status": "unavailable",
            "message": f"Unavailable (Busy until {current_trip['busy_until']})",
            "current_trip": current_trip,
            "next_trip": next_trip,
            "busy_until": current_trip['busy_until']
        }
    elif next_trip:
        return {
            "status": "available_upcoming",
            "message": f"Available now, next trip at {next_trip['shift_time']}",
            "current_trip": None,
            "next_trip": next_trip,
            "busy_until": None
        }
    else:
        # All trips are in the past
        return {
            "status": "available",
            "message": "Available (All trips completed)",
            "current_trip": None,
            "next_trip": None,
            "busy_until": None
        }


# ===================== VEHICLE ENDPOINTS =====================

@router.get("/vehicles/all")
async def get_all_vehicles() -> List[Dict[str, Any]]:
    """
    Get all vehicles with their current availability status.
    
    Returns list of vehicles with:
    - Basic info (id, registration_number, type, capacity, status)
    - Current availability status (Available, Unavailable, Available with upcoming trip)
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get all vehicles
            vehicles = await conn.fetch("""
                SELECT 
                    vehicle_id,
                    registration_number,
                    vehicle_type,
                    capacity,
                    status,
                    created_at
                FROM vehicles
                ORDER BY registration_number
            """)
            
            result = []
            now = datetime.now()
            today = date.today()
            
            for vehicle in vehicles:
                vehicle_dict = dict(vehicle)
                
                # Compute dynamic availability
                availability = await _compute_vehicle_availability(conn, vehicle['vehicle_id'], today, now)
                vehicle_dict['availability'] = availability
                
                result.append(vehicle_dict)
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vehicles/available")
async def get_available_vehicles() -> List[Dict[str, Any]]:
    """
    Get only currently available vehicles (not on a trip right now).
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            vehicles = await conn.fetch("""
                SELECT 
                    vehicle_id,
                    registration_number,
                    vehicle_type,
                    capacity,
                    status,
                    created_at
                FROM vehicles
                WHERE status != 'maintenance'
                ORDER BY registration_number
            """)
            
            result = []
            now = datetime.now()
            today = date.today()
            
            for vehicle in vehicles:
                availability = await _compute_vehicle_availability(conn, vehicle['vehicle_id'], today, now)
                
                # Only include vehicles that are currently available
                if availability['status'] != 'unavailable':
                    vehicle_dict = dict(vehicle)
                    vehicle_dict['availability'] = availability
                    result.append(vehicle_dict)
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching available vehicles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vehicles/available-for-trip/{trip_id}")
async def get_available_vehicles_for_trip_endpoint(trip_id: int) -> Dict[str, Any]:
    """
    Get vehicles available at the specific trip's scheduled time.
    Uses time-overlap logic to exclude vehicles already assigned to overlapping trips.
    """
    try:
        from app.core.service import get_available_vehicles_for_trip
        result = await get_available_vehicles_for_trip(trip_id)
        return {"ok": True, "vehicles": result}
    except Exception as e:
        logger.error(f"Error fetching available vehicles for trip {trip_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drivers/available-for-trip/{trip_id}")
async def get_available_drivers_for_trip_endpoint(trip_id: int) -> Dict[str, Any]:
    """
    Get drivers available at the specific trip's scheduled time.
    Uses time-overlap logic to exclude drivers already assigned to overlapping trips.
    """
    try:
        from langgraph.tools import tool_list_available_drivers
        result = await tool_list_available_drivers(trip_id)
        return result
    except Exception as e:
        logger.error(f"Error fetching available drivers for trip {trip_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vehicles/{vehicle_id}")
async def get_vehicle_details(vehicle_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific vehicle including:
    - All vehicle fields
    - Current dynamic availability
    - Currently assigned driver (if any)
    - Today's assigned trips
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get vehicle info
            vehicle = await conn.fetchrow("""
                SELECT 
                    vehicle_id,
                    registration_number,
                    vehicle_type,
                    capacity,
                    status,
                    created_at
                FROM vehicles
                WHERE vehicle_id = $1
            """, vehicle_id)
            
            if not vehicle:
                raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
            
            vehicle_dict = dict(vehicle)
            now = datetime.now()
            today = date.today()
            
            # Compute dynamic availability
            availability = await _compute_vehicle_availability(conn, vehicle_id, today, now)
            vehicle_dict['availability'] = availability
            
            # Get current/assigned driver for today's trips
            current_driver = await conn.fetchrow("""
                SELECT DISTINCT 
                    dr.driver_id,
                    dr.name as driver_name,
                    dr.phone as driver_phone
                FROM deployments d
                JOIN daily_trips t ON d.trip_id = t.trip_id
                JOIN drivers dr ON d.driver_id = dr.driver_id
                WHERE d.vehicle_id = $1 AND t.trip_date = $2
                LIMIT 1
            """, vehicle_id, today)
            
            vehicle_dict['assigned_driver'] = dict(current_driver) if current_driver else None
            
            # Get today's trips for this vehicle
            today_trips = await conn.fetch("""
                SELECT 
                    t.trip_id,
                    t.display_name,
                    t.live_status,
                    r.shift_time,
                    dr.name as driver_name,
                    t.booking_status_percentage
                FROM daily_trips t
                JOIN deployments d ON t.trip_id = d.trip_id
                LEFT JOIN routes r ON t.route_id = r.route_id
                LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
                WHERE d.vehicle_id = $1 AND t.trip_date = $2
                ORDER BY r.shift_time
            """, vehicle_id, today)
            
            vehicle_dict['todays_trips'] = [dict(trip) for trip in today_trips]
            
            return vehicle_dict
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching vehicle {vehicle_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _compute_vehicle_availability(conn, vehicle_id: int, today: date, now: datetime) -> Dict[str, Any]:
    """
    Compute dynamic availability for a vehicle based on current trips.
    
    Returns:
        {
            "status": "available" | "unavailable" | "available_upcoming" | "maintenance",
            "message": "Available" | "On trip until HH:MM" | "Available now, next trip at HH:MM" | "Under Maintenance",
            "current_trip": {...} | None,
            "next_trip": {...} | None,
            "busy_until": "HH:MM" | None
        }
    """
    # First check if vehicle is under maintenance
    vehicle_status = await conn.fetchval("""
        SELECT status FROM vehicles WHERE vehicle_id = $1
    """, vehicle_id)
    
    if vehicle_status == 'maintenance':
        return {
            "status": "maintenance",
            "message": "Under Maintenance",
            "current_trip": None,
            "next_trip": None,
            "busy_until": None
        }
    
    current_time = now.time()
    
    # Get all trips for this vehicle today
    trips = await conn.fetch("""
        SELECT 
            t.trip_id,
            t.display_name,
            t.live_status,
            r.shift_time,
            r.route_name
        FROM daily_trips t
        JOIN deployments d ON t.trip_id = d.trip_id
        LEFT JOIN routes r ON t.route_id = r.route_id
        WHERE d.vehicle_id = $1 AND t.trip_date = $2
        ORDER BY r.shift_time
    """, vehicle_id, today)
    
    if not trips:
        return {
            "status": "available",
            "message": "Available (No trips today)",
            "current_trip": None,
            "next_trip": None,
            "busy_until": None
        }
    
    # Assume each trip takes 60 minutes
    TRIP_DURATION_MINUTES = 60
    
    current_trip = None
    next_trip = None
    
    for trip in trips:
        shift_time = trip['shift_time']
        if not shift_time:
            # Try to extract time from display_name
            display_name = trip['display_name'] or ''
            if ' - ' in display_name:
                time_part = display_name.split(' - ')[-1]
                try:
                    shift_time = datetime.strptime(time_part, "%H:%M").time()
                except ValueError:
                    continue
            else:
                continue
        
        trip_start = shift_time
        trip_end_dt = datetime.combine(today, trip_start) + timedelta(minutes=TRIP_DURATION_MINUTES)
        trip_end = trip_end_dt.time()
        
        # Check if this trip is currently active
        if trip_start <= current_time <= trip_end:
            current_trip = {
                "trip_id": trip['trip_id'],
                "display_name": trip['display_name'],
                "shift_time": str(shift_time)[:5] if shift_time else None,
                "busy_until": str(trip_end)[:5]
            }
        elif trip_start > current_time and next_trip is None:
            next_trip = {
                "trip_id": trip['trip_id'],
                "display_name": trip['display_name'],
                "shift_time": str(shift_time)[:5] if shift_time else None
            }
    
    if current_trip:
        return {
            "status": "unavailable",
            "message": f"On trip until {current_trip['busy_until']}",
            "current_trip": current_trip,
            "next_trip": next_trip,
            "busy_until": current_trip['busy_until']
        }
    elif next_trip:
        return {
            "status": "available_upcoming",
            "message": f"Available now, next trip at {next_trip['shift_time']}",
            "current_trip": None,
            "next_trip": next_trip,
            "busy_until": None
        }
    else:
        return {
            "status": "available",
            "message": "Available (All trips completed)",
            "current_trip": None,
            "next_trip": None,
            "busy_until": None
        }
