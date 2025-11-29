# backend/app/models.py
"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ============================================================================
# Action Request/Response Models
# ============================================================================

class AssignVehicleRequest(BaseModel):
    trip_id: int = Field(..., description="ID of the trip to assign vehicle to")
    vehicle_id: int = Field(..., description="ID of the vehicle to assign")
    driver_id: int = Field(..., description="ID of the driver to assign")
    user_id: int = Field(..., description="ID of the user performing the action")


class AssignVehicleOnlyRequest(BaseModel):
    """Request to assign only a vehicle to a trip (no driver)"""
    trip_id: int = Field(..., description="ID of the trip to assign vehicle to")
    vehicle_id: int = Field(..., description="ID of the vehicle to assign")
    user_id: int = Field(..., description="ID of the user performing the action")


class AssignDriverOnlyRequest(BaseModel):
    """Request to assign only a driver to a trip (no vehicle)"""
    trip_id: int = Field(..., description="ID of the trip to assign driver to")
    driver_id: int = Field(..., description="ID of the driver to assign")
    user_id: int = Field(..., description="ID of the user performing the action")


class RemoveVehicleRequest(BaseModel):
    trip_id: int = Field(..., description="ID of the trip to remove vehicle from")
    user_id: int = Field(..., description="ID of the user performing the action")
    cancel_bookings: bool = Field(True, description="Whether to cancel existing bookings")


class CancelTripRequest(BaseModel):
    trip_id: int = Field(..., description="ID of the trip to cancel")
    user_id: int = Field(..., description="ID of the user performing the action")


class ActionResponse(BaseModel):
    ok: bool
    trip_id: int
    message: str
    details: Optional[dict] = None


# ============================================================================
# Entity Models
# ============================================================================

class Stop(BaseModel):
    stop_id: int
    name: str
    latitude: float
    longitude: float
    city: Optional[str] = None


class Path(BaseModel):
    path_id: int
    name: str
    description: Optional[str] = None


class Route(BaseModel):
    route_id: int
    path_id: int
    name: str
    shift_time: str
    direction: str
    status: str


class Vehicle(BaseModel):
    vehicle_id: int
    registration_number: str
    capacity: int
    vehicle_type: str
    status: str


class Driver(BaseModel):
    driver_id: int
    name: str
    phone: str
    license_number: str
    status: str


class TripInfo(BaseModel):
    trip_id: int
    route_id: int
    route_name: str
    live_status: str
    booked_count: int
    seats_booked: Optional[int] = 0
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    capacity: Optional[int] = None  # Vehicle capacity
    trip_date: Optional[str] = None
    shift_time: Optional[str] = None
    direction: Optional[str] = None
    registration_number: Optional[str] = None
    driver_name: Optional[str] = None
    path_name: Optional[str] = None
    start_point: Optional[str] = None
    end_point: Optional[str] = None
    display_name: Optional[str] = None
    booking_status_percentage: Optional[int] = 0


class Booking(BaseModel):
    booking_id: int
    trip_id: int
    user_id: int
    user_name: Optional[str] = None
    seats: int
    status: str
    created_at: str


class AuditLog(BaseModel):
    log_id: int
    action: str
    user_id: Optional[int] = None
    entity_type: str
    entity_id: int
    details: Optional[dict] = None
    created_at: str


# ============================================================================
# Context Models (for UI)
# ============================================================================

class DashboardContext(BaseModel):
    trips: List[TripInfo]
    summary: Optional[dict] = None


class ManageContext(BaseModel):
    stops: List[dict]
    routes: List[dict]
    paths: List[dict]
    vehicles: List[dict]
    drivers: List[dict]


class HealthStatus(BaseModel):
    status: str
    database: str
    pool_size: Optional[int] = None
    timestamp: str
