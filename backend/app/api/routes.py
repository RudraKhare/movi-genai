# backend/app/api/routes.py
"""
CRUD endpoints for routes, stops, paths, vehicles, and drivers.
"""
from fastapi import APIRouter, HTTPException, status
from app.core.supabase_client import get_conn
from typing import List
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
