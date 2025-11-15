# backend/app/api/context.py
"""
Context endpoints for UI components (dashboard, manage routes).
These provide aggregated data tailored for specific UI views.
"""
from fastapi import APIRouter, HTTPException, status
from app.models import DashboardContext, ManageContext
from app.core.supabase_client import get_conn
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=DashboardContext)
async def dashboard_context():
    """
    Get aggregated context for the bus dashboard UI.
    
    Returns:
    - List of all trips with deployment and booking statistics
    - Summary statistics (total trips, deployed, bookings)
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get all trips with deployment and booking info
            trips = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.route_id,
                    dt.trip_date,
                    dt.display_name,
                    dt.booking_status_percentage,
                    r.route_name,
                    r.shift_time,
                    r.direction,
                    r.start_point,
                    r.end_point,
                    dt.live_status,
                    d.vehicle_id,
                    d.driver_id,
                    v.registration_number,
                    v.capacity,
                    dr.name AS driver_name,
                    p.path_name,
                    COUNT(b.booking_id) FILTER (WHERE b.status='CONFIRMED') AS booked_count,
                    COALESCE(SUM(b.seats) FILTER (WHERE b.status='CONFIRMED'), 0) AS seats_booked
                FROM daily_trips dt
                JOIN routes r ON dt.route_id = r.route_id
                LEFT JOIN paths p ON r.path_id = p.path_id
                LEFT JOIN deployments d ON d.trip_id = dt.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
                LEFT JOIN bookings b ON b.trip_id = dt.trip_id
                GROUP BY 
                    dt.trip_id, dt.route_id, dt.trip_date, dt.display_name, dt.booking_status_percentage,
                    r.route_name, r.shift_time, r.direction, r.start_point, r.end_point,
                    dt.live_status, d.vehicle_id, d.driver_id, v.registration_number, v.capacity, dr.name,
                    p.path_name
                ORDER BY dt.trip_date DESC, r.shift_time
                LIMIT 100
            """)
            
            # Calculate summary statistics
            total_trips = len(trips)
            deployed_count = sum(1 for t in trips if t['vehicle_id'] is not None)
            total_bookings = sum(int(t['booked_count']) for t in trips)
            total_seats_booked = sum(int(t['seats_booked']) for t in trips)
            ongoing_trips = sum(1 for t in trips if t['live_status'] == 'IN_PROGRESS')
        
        # Convert asyncpg.Record to dict and format data
        trips_list = []
        for t in trips:
            trip_dict = dict(t)
            # Convert date to string for JSON serialization
            if trip_dict.get('trip_date'):
                trip_dict['trip_date'] = str(trip_dict['trip_date'])
            # Convert time to string
            if trip_dict.get('shift_time'):
                trip_dict['shift_time'] = str(trip_dict['shift_time'])
            trips_list.append(trip_dict)
        
        return DashboardContext(
            trips=trips_list,
            summary={
                "total_trips": total_trips,
                "deployed": deployed_count,
                "pending_deployment": total_trips - deployed_count,
                "total_bookings": total_bookings,
                "total_seats_booked": total_seats_booked,
                "ongoing_trips": ongoing_trips
            }
        )
    
    except Exception as e:
        logger.error(f"Error fetching dashboard context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard context: {str(e)}"
        )


@router.get("/manage", response_model=ManageContext)
async def manage_context():
    """
    Get aggregated context for the manage routes UI.
    
    Returns:
    - All stops
    - All routes
    - All paths with their stops
    - All vehicles
    - All drivers
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Fetch all entity types in parallel
            stops = await conn.fetch("SELECT * FROM stops ORDER BY stop_id")
            
            routes = await conn.fetch("""
                SELECT r.*, p.path_name
                FROM routes r
                LEFT JOIN paths p ON r.path_id = p.path_id
                ORDER BY r.route_id
            """)
            
            paths = await conn.fetch("SELECT * FROM paths ORDER BY path_id")
            
            path_stops = await conn.fetch("""
                SELECT ps.*, s.name AS stop_name, s.latitude, s.longitude
                FROM path_stops ps
                JOIN stops s ON ps.stop_id = s.stop_id
                ORDER BY ps.path_id, ps.stop_order
            """)
            
            vehicles = await conn.fetch("SELECT * FROM vehicles ORDER BY vehicle_id")
            
            drivers = await conn.fetch("SELECT * FROM drivers ORDER BY driver_id")
        
        # Group stops by path
        paths_dict = {p['path_id']: {**dict(p), 'stops': [], 'stop_count': 0} for p in paths}
        for ps in path_stops:
            path_id = ps['path_id']
            if path_id in paths_dict:
                paths_dict[path_id]['stops'].append(dict(ps))
                paths_dict[path_id]['stop_count'] = len(paths_dict[path_id]['stops'])
        
        # Convert asyncpg.Record to dict and handle date/time serialization
        def serialize_row(row):
            d = dict(row)
            for key, value in d.items():
                if hasattr(value, 'isoformat'):  # datetime, date, or time object
                    d[key] = str(value)
            return d
        
        return ManageContext(
            stops=[serialize_row(s) for s in stops],
            routes=[serialize_row(r) for r in routes],
            paths=list(paths_dict.values()),
            vehicles=[serialize_row(v) for v in vehicles],
            drivers=[serialize_row(d) for d in drivers]
        )
    
    except Exception as e:
        logger.error(f"Error fetching manage context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch manage context: {str(e)}"
        )
