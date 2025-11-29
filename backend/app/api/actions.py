# backend/app/api/actions.py
"""
Trip action endpoints: assign_vehicle, remove_vehicle, cancel_trip.
These endpoints use the transactional service layer from Day 3.
"""
from fastapi import APIRouter, HTTPException, status
from app.models import (
    AssignVehicleRequest,
    AssignVehicleOnlyRequest,
    AssignDriverOnlyRequest,
    RemoveVehicleRequest,
    CancelTripRequest,
    ActionResponse
)
from app.core import service
from app.core.service import ServiceError
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/assign_vehicle", response_model=ActionResponse)
async def assign_vehicle(req: AssignVehicleRequest):
    """
    Assign a vehicle and driver to a trip.
    
    This operation:
    - Creates a deployment record
    - Checks vehicle/driver availability
    - Records an audit log
    - Is fully transactional (atomic)
    
    Returns 400 if:
    - Trip already has a deployment
    - Vehicle or driver is unavailable on that date
    - Trip doesn't exist
    """
    try:
        result = await service.assign_vehicle(
            trip_id=req.trip_id,
            vehicle_id=req.vehicle_id,
            driver_id=req.driver_id,
            user_id=req.user_id
        )
        
        logger.info(f"Vehicle {req.vehicle_id} assigned to trip {req.trip_id}")
        
        return ActionResponse(
            ok=True,
            trip_id=req.trip_id,
            message=f"Vehicle {req.vehicle_id} and driver {req.driver_id} assigned successfully",
            details=result
        )
    
    except ServiceError as e:
        logger.warning(f"Service error in assign_vehicle: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in assign_vehicle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign vehicle: {str(e)}"
        )


@router.post("/assign_vehicle_only", response_model=ActionResponse)
async def assign_vehicle_only(req: AssignVehicleOnlyRequest):
    """
    Assign only a vehicle to a trip (keeps existing driver if any).
    
    This operation:
    - Creates or updates the deployment record
    - Checks vehicle availability with time-overlap logic
    - Records an audit log
    - Is fully transactional (atomic)
    
    Returns 400 if:
    - Vehicle is unavailable at trip's scheduled time
    - Trip doesn't exist
    """
    try:
        result = await service.assign_vehicle_only(
            trip_id=req.trip_id,
            vehicle_id=req.vehicle_id,
            user_id=req.user_id
        )
        
        logger.info(f"Vehicle {req.vehicle_id} assigned to trip {req.trip_id}")
        
        return ActionResponse(
            ok=True,
            trip_id=req.trip_id,
            message=f"Vehicle {req.vehicle_id} assigned successfully",
            details=result
        )
    
    except ServiceError as e:
        logger.warning(f"Service error in assign_vehicle_only: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in assign_vehicle_only: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign vehicle: {str(e)}"
        )


@router.post("/assign_driver_only", response_model=ActionResponse)
async def assign_driver_only(req: AssignDriverOnlyRequest):
    """
    Assign only a driver to a trip (keeps existing vehicle if any).
    
    This operation:
    - Creates or updates the deployment record
    - Checks driver availability with time-overlap logic
    - Records an audit log
    - Is fully transactional (atomic)
    
    Returns 400 if:
    - Driver is unavailable at trip's scheduled time
    - Trip doesn't exist
    """
    try:
        result = await service.assign_driver(
            trip_id=req.trip_id,
            driver_id=req.driver_id,
            user_id=req.user_id
        )
        
        logger.info(f"Driver {req.driver_id} assigned to trip {req.trip_id}")
        
        return ActionResponse(
            ok=True,
            trip_id=req.trip_id,
            message=f"Driver {req.driver_id} assigned successfully",
            details=result
        )
    
    except ServiceError as e:
        logger.warning(f"Service error in assign_driver_only: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in assign_driver_only: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign driver: {str(e)}"
        )


@router.post("/remove_vehicle", response_model=ActionResponse)
async def remove_vehicle(req: RemoveVehicleRequest):
    """
    Remove vehicle deployment from a trip.
    
    This operation:
    - Deletes the deployment record
    - Optionally cancels all CONFIRMED bookings
    - Records an audit log
    - Is fully transactional (atomic)
    
    Returns 400 if:
    - Trip has no deployment
    - Trip doesn't exist
    """
    try:
        result = await service.remove_vehicle(
            trip_id=req.trip_id,
            user_id=req.user_id,
            cancel_bookings=req.cancel_bookings
        )
        
        bookings_msg = f" ({result.get('bookings_cancelled', 0)} bookings cancelled)" if req.cancel_bookings else ""
        logger.info(f"Vehicle removed from trip {req.trip_id}{bookings_msg}")
        
        return ActionResponse(
            ok=True,
            trip_id=req.trip_id,
            message=f"Vehicle removed successfully{bookings_msg}",
            details=result
        )
    
    except ServiceError as e:
        logger.warning(f"Service error in remove_vehicle: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in remove_vehicle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove vehicle: {str(e)}"
        )


@router.post("/cancel_trip", response_model=ActionResponse)
async def cancel_trip(req: CancelTripRequest):
    """
    Cancel a trip and all its confirmed bookings.
    
    This operation:
    - Updates trip status to CANCELLED
    - Cancels all CONFIRMED bookings
    - Records an audit log
    - Is fully transactional (atomic)
    
    Returns 400 if trip doesn't exist.
    """
    try:
        result = await service.cancel_trip(
            trip_id=req.trip_id,
            user_id=req.user_id
        )
        
        bookings_cancelled = result.get('bookings_cancelled', 0)
        logger.info(f"Trip {req.trip_id} cancelled ({bookings_cancelled} bookings affected)")
        
        return ActionResponse(
            ok=True,
            trip_id=req.trip_id,
            message=f"Trip cancelled successfully ({bookings_cancelled} bookings cancelled)",
            details=result
        )
    
    except ServiceError as e:
        logger.warning(f"Service error in cancel_trip: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in cancel_trip: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel trip: {str(e)}"
        )


# ============================================================================
# BOOKING MANAGEMENT ENDPOINTS
# ============================================================================

from pydantic import BaseModel

class AddBookingsRequest(BaseModel):
    trip_id: int
    count: int = 1
    user_id: int = 1

class ReduceBookingsRequest(BaseModel):
    trip_id: int
    count: int = 1
    user_id: int = 1


@router.post("/add_bookings", response_model=ActionResponse)
async def add_bookings_endpoint(req: AddBookingsRequest):
    """
    Add bookings to a trip.
    
    This operation:
    - Checks vehicle capacity
    - Creates booking records
    - Updates booking percentage
    
    Returns 400 if:
    - No vehicle assigned
    - Would exceed capacity
    """
    try:
        from langgraph.tools import tool_add_bookings
        result = await tool_add_bookings(req.trip_id, req.count, req.user_id)
        
        if not result.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to add bookings")
            )
        
        logger.info(f"Added {req.count} bookings to trip {req.trip_id}")
        
        return ActionResponse(
            ok=True,
            trip_id=req.trip_id,
            message=result.get("message", f"Added {req.count} booking(s)"),
            details=result.get("result", {})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in add_bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add bookings: {str(e)}"
        )


@router.post("/reduce_bookings", response_model=ActionResponse)
async def reduce_bookings_endpoint(req: ReduceBookingsRequest):
    """
    Reduce bookings from a trip.
    
    This operation:
    - Cancels the most recent bookings
    - Updates booking percentage
    
    Returns 400 if:
    - No bookings to reduce
    - Count exceeds current bookings
    """
    try:
        from langgraph.tools import tool_reduce_bookings
        result = await tool_reduce_bookings(req.trip_id, req.count, req.user_id)
        
        if not result.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to reduce bookings")
            )
        
        logger.info(f"Reduced {req.count} bookings from trip {req.trip_id}")
        
        return ActionResponse(
            ok=True,
            trip_id=req.trip_id,
            message=result.get("message", f"Reduced {req.count} booking(s)"),
            details=result.get("result", {})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in reduce_bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reduce bookings: {str(e)}"
        )


@router.get("/seat_availability/{trip_id}")
async def check_seat_availability_endpoint(trip_id: int):
    """
    Check seat availability for a trip.
    """
    try:
        from langgraph.tools import tool_check_seat_availability
        result = await tool_check_seat_availability(trip_id)
        
        if not result.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to check availability")
            )
        
        return result.get("result", {})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in seat_availability: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check seat availability: {str(e)}"
        )
