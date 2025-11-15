# backend/app/api/actions.py
"""
Trip action endpoints: assign_vehicle, remove_vehicle, cancel_trip.
These endpoints use the transactional service layer from Day 3.
"""
from fastapi import APIRouter, HTTPException, status
from app.models import (
    AssignVehicleRequest,
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
