# backend/app/api/routes.py
"""
CRUD endpoints for routes, stops, paths, vehicles, and drivers.
"""
from fastapi import APIRouter, HTTPException, status
from app.core.supabase_client import get_conn
from app.core.enum_normalizer import normalize_enum_value, normalize_data_enums
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_routes():
    """
    Get all routes with their associated path information.
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT r.*, p.name AS path_name
                FROM routes r
                LEFT JOIN paths p ON r.path_id = p.path_id
                ORDER BY r.route_id
            """)
        
        return {"routes": [dict(r) for r in rows]}
    
    except Exception as e:
        logger.error(f"Error fetching routes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch routes: {str(e)}"
        )


@router.get("/{route_id}")
async def get_route(route_id: int):
    """
    Get a single route by ID with path information.
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT r.*, p.name AS path_name
                FROM routes r
                LEFT JOIN paths p ON r.path_id = p.path_id
                WHERE r.route_id = $1
            """, route_id)
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route {route_id} not found"
            )
        
        return {"route": dict(row)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching route {route_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch route: {str(e)}"
        )


@router.get("/stops/all")
async def list_stops():
    """
    Get all stops.
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM stops
                ORDER BY stop_id
            """)
        
        return {"stops": [dict(r) for r in rows]}
    
    except Exception as e:
        logger.error(f"Error fetching stops: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stops: {str(e)}"
        )


@router.get("/paths/all")
async def list_paths():
    """
    Get all paths with their stops.
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            paths = await conn.fetch("""
                SELECT * FROM paths
                ORDER BY path_id
            """)
            
            path_stops = await conn.fetch("""
                SELECT ps.*, s.name AS stop_name
                FROM path_stops ps
                JOIN stops s ON ps.stop_id = s.stop_id
                ORDER BY ps.path_id, ps.stop_order
            """)
        
        # Group stops by path
        paths_dict = {p['path_id']: {**dict(p), 'stops': []} for p in paths}
        
        for ps in path_stops:
            path_id = ps['path_id']
            if path_id in paths_dict:
                paths_dict[path_id]['stops'].append(dict(ps))
        
        return {"paths": list(paths_dict.values())}
    
    except Exception as e:
        logger.error(f"Error fetching paths: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch paths: {str(e)}"
        )


@router.get("/vehicles/all")
async def list_vehicles():
    """
    Get all vehicles.
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM vehicles
                ORDER BY vehicle_id
            """)
        
        return {"vehicles": [dict(r) for r in rows]}
    
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vehicles: {str(e)}"
        )


@router.get("/drivers/all")
async def list_drivers():
    """
    Get all drivers.
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM drivers
                ORDER BY driver_id
            """)
        
        return {"drivers": [dict(r) for r in rows]}
    
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch drivers: {str(e)}"
        )


# POST endpoints for CRUD operations (Day 6)

@router.post("/stops/create")
async def create_stop(data: dict):
    """
    Create a new stop.
    Expected payload: { "name": "Stop Name" }
    """
    try:
        name = data.get("name", "").strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stop name is required"
            )
        
        pool = await get_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO stops (name, status)
                VALUES ($1, 'Active')
                RETURNING *
            """, name)
        
        logger.info(f"Created stop: {name} (ID: {row['stop_id']})")
        return {"success": True, "stop": dict(row)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating stop: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create stop: {str(e)}"
        )


@router.post("/paths/create")
async def create_path(data: dict):
    """
    Create a new path with ordered stops.
    Expected payload: { "path_name": "Path A", "stop_ids": [1, 2, 3] }
    """
    try:
        path_name = data.get("path_name", "").strip()
        stop_ids = data.get("stop_ids", [])
        
        if not path_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path name is required"
            )
        
        if not stop_ids or len(stop_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path must have at least 2 stops"
            )
        
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Create path
            path_row = await conn.fetchrow("""
                INSERT INTO paths (path_name)
                VALUES ($1)
                RETURNING *
            """, path_name)
            
            path_id = path_row['path_id']
            
            # Insert path_stops with ordering
            for order, stop_id in enumerate(stop_ids, start=1):
                await conn.execute("""
                    INSERT INTO path_stops (path_id, stop_id, stop_order)
                    VALUES ($1, $2, $3)
                """, path_id, stop_id, order)
        
        logger.info(f"Created path: {path_name} (ID: {path_id}) with {len(stop_ids)} stops")
        return {"success": True, "path": dict(path_row), "stop_count": len(stop_ids)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating path: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create path: {str(e)}"
        )


@router.post("/create")
async def create_route(data: dict):
    """
    Create a new route linked to a path.
    Expected payload: { "route_name": "R101", "shift_time": "08:00", "path_id": 1, "direction": "UP" }
    """
    try:
        route_name = data.get("route_name", "").strip()
        shift_time_str = data.get("shift_time", "").strip()
        path_id = data.get("path_id")
        direction = data.get("direction", "UP")
        
        # Normalize direction to match database constraint ('up' or 'down')
        direction = normalize_enum_value("routes", "direction", direction)
        
        if not route_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Route name is required"
            )
        
        if not shift_time_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shift time is required"
            )
        
        if not path_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path ID is required"
            )
        
        # Convert shift_time string to datetime.time object
        shift_time_obj = None
        try:
            shift_time_obj = datetime.strptime(shift_time_str, "%H:%M").time()
        except ValueError:
            logger.warning(f"Invalid time format: {shift_time_str}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time format: {shift_time_str}. Expected HH:MM format."
            )
        
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Verify path exists and get path details with stops
            path_data = await conn.fetchrow("""
                SELECT p.path_id, p.path_name
                FROM paths p
                WHERE p.path_id = $1
            """, path_id)
            
            if not path_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Path {path_id} not found"
                )
            
            # Get first and last stops from the path
            stops = await conn.fetch("""
                SELECT s.stop_id, s.name, ps.stop_order
                FROM path_stops ps
                JOIN stops s ON ps.stop_id = s.stop_id
                WHERE ps.path_id = $1
                ORDER BY ps.stop_order
            """, path_id)
            
            # Determine start_point and end_point
            start_point = None
            end_point = None
            if stops and len(stops) > 0:
                start_point = stops[0]['name']  # First stop
                end_point = stops[-1]['name']    # Last stop
            
            # Create route with start_point and end_point
            row = await conn.fetchrow("""
                INSERT INTO routes (route_name, shift_time, path_id, direction, start_point, end_point)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """, route_name, shift_time_obj, path_id, direction, start_point, end_point)
            
            route_id = row['route_id']
            
            # Auto-create a daily trip for this route (for today's date)
            today = datetime.now().date()
            display_name = f"{route_name}"
            
            trip_row = await conn.fetchrow("""
                INSERT INTO daily_trips (route_id, display_name, trip_date, live_status)
                VALUES ($1, $2, $3, 'SCHEDULED')
                RETURNING *
            """, route_id, display_name, today)
            
            logger.info(f"✅ Created route: {route_name} (ID: {route_id}) for path {path_id}")
            logger.info(f"✅ Auto-created daily trip: {display_name} (Trip ID: {trip_row['trip_id']}) for {today}")
        
        return {
            "success": True, 
            "route": dict(row),
            "trip": dict(trip_row),
            "message": f"Route '{route_name}' created successfully with trip scheduled for {today}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating route: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create route: {str(e)}"
        )


@router.get("/{route_id}/stops")
async def get_route_stops(route_id: int):
    """
    Get all stops for a route (via its path).
    Returns the ordered list of stops for the route's path.
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get route's path_id
            route = await conn.fetchrow("""
                SELECT path_id FROM routes WHERE route_id = $1
            """, route_id)
            
            if not route or not route['path_id']:
                return {"stops": []}
            
            # Get stops for this path
            stops = await conn.fetch("""
                SELECT 
                    s.stop_id,
                    s.name,
                    s.latitude,
                    s.longitude,
                    s.address,
                    ps.stop_order
                FROM path_stops ps
                JOIN stops s ON ps.stop_id = s.stop_id
                WHERE ps.path_id = $1
                ORDER BY ps.stop_order
            """, route['path_id'])
            
            return {
                "route_id": route_id,
                "path_id": route['path_id'],
                "stops": [dict(s) for s in stops],
                "total_stops": len(stops)
            }
    
    except Exception as e:
        logger.error(f"Error fetching route stops: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch route stops: {str(e)}"
        )
