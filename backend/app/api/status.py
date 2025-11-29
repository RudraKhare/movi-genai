"""
Trip Status Management API Routes

Provides endpoints for:
- Manual status updates (for dispatchers)
- Status updater control (start/stop/force update)
- Status monitoring and logs
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.core.status_updater import (
    force_update_trip_statuses,
    manually_update_trip_status
)

logger = logging.getLogger(__name__)
router = APIRouter()

class ManualStatusUpdate(BaseModel):
    trip_id: int
    new_status: str
    user_id: Optional[int] = 1  # Default to user 1 for testing

class StatusUpdateResponse(BaseModel):
    success: bool
    message: str
    trip_id: Optional[int] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None

@router.post("/manual_update", response_model=StatusUpdateResponse)
async def manual_status_update(data: ManualStatusUpdate):
    """
    Manually update a trip's status (for dispatcher override)
    
    Valid statuses: SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    """
    try:
        result = await manually_update_trip_status(
            trip_id=data.trip_id,
            new_status=data.new_status,
            user_id=data.user_id
        )
        
        return StatusUpdateResponse(
            success=True,
            message=f"Trip {data.trip_id} status updated to {data.new_status}",
            trip_id=result["trip_id"],
            old_status=result["old_status"],
            new_status=result["new_status"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error manually updating status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/force_update", response_model=StatusUpdateResponse)
async def force_status_update():
    """
    Force an immediate update of all trip statuses
    (normally runs automatically every minute)
    """
    try:
        await force_update_trip_statuses()
        
        return StatusUpdateResponse(
            success=True,
            message="Forced status update completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error forcing status update: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/status_info")
async def get_status_info():
    """
    Get information about the current status updater configuration
    """
    try:
        from app.core.status_updater import _status_updater
        
        if _status_updater:
            return {
                "status_updater_running": _status_updater.is_running,
                "update_interval_seconds": _status_updater.update_interval,
                "trip_duration_hours": _status_updater.trip_duration_hours,
                "valid_statuses": ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
                "automatic_transitions": {
                    "SCHEDULED_to_IN_PROGRESS": "When current_time >= trip_start_time",
                    "IN_PROGRESS_to_COMPLETED": "When current_time >= trip_end_time"
                }
            }
        else:
            return {
                "status_updater_running": False,
                "message": "Status updater not initialized"
            }
            
    except Exception as e:
        logger.error(f"Error getting status info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
