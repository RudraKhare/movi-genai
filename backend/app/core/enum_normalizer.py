# backend/app/core/enum_normalizer.py
"""
Utility for normalizing enum values to match database check constraints.
Ensures backend input values align with database-defined enum constraints.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Define database constraint mappings
# Format: "table.column": {"backend_value": "db_value", ...}
ENUM_MAPPINGS: Dict[str, Dict[str, str]] = {
    # Routes table
    "routes.direction": {
        "UP": "up",
        "DOWN": "down",
        "Up": "up",
        "Down": "down",
        "up": "up",
        "down": "down",
    },
    "routes.status": {
        "ACTIVE": "active",
        "DEACTIVATED": "deactivated",
        "active": "active",
        "deactivated": "deactivated",
        "Active": "active",
        "Deactivated": "deactivated",
    },
    # Vehicles table
    "vehicles.status": {
        "AVAILABLE": "available",
        "DEPLOYED": "deployed",
        "MAINTENANCE": "maintenance",
        "available": "available",
        "deployed": "deployed",
        "maintenance": "maintenance",
        "Available": "available",
        "Deployed": "deployed",
        "Maintenance": "maintenance",
    },
    "vehicles.vehicle_type": {
        "BUS": "Bus",
        "CAB": "Cab",
        "bus": "Bus",
        "cab": "Cab",
        "Bus": "Bus",
        "Cab": "Cab",
    },
    # Drivers table
    "drivers.status": {
        "AVAILABLE": "available",
        "ON_TRIP": "on_trip",
        "OFF_DUTY": "off_duty",
        "available": "available",
        "on_trip": "on_trip",
        "off_duty": "off_duty",
        "Available": "available",
        "OnTrip": "on_trip",
        "OffDuty": "off_duty",
    },
    # Bookings table
    "bookings.status": {
        "CONFIRMED": "CONFIRMED",
        "CANCELLED": "CANCELLED",
        "confirmed": "CONFIRMED",
        "cancelled": "CANCELLED",
        "Confirmed": "CONFIRMED",
        "Cancelled": "CANCELLED",
    },
    # Daily trips table
    "daily_trips.live_status": {
        "SCHEDULED": "SCHEDULED",
        "IN_PROGRESS": "IN_PROGRESS",
        "COMPLETED": "COMPLETED",
        "CANCELLED": "CANCELLED",
        "scheduled": "SCHEDULED",
        "in_progress": "IN_PROGRESS",
        "completed": "COMPLETED",
        "cancelled": "CANCELLED",
    },
}


def normalize_enum_value(
    table: str, 
    column: str, 
    value: Any, 
    strict: bool = True
) -> Optional[str]:
    """
    Normalize an enum value to match database check constraints.
    
    Args:
        table: Table name (e.g., "routes")
        column: Column name (e.g., "direction")
        value: The value to normalize
        strict: If True, log warnings for unmapped values
    
    Returns:
        Normalized value that matches database constraint, or None if value is None/empty
    
    Example:
        >>> normalize_enum_value("routes", "direction", "UP")
        'up'
        >>> normalize_enum_value("vehicles", "vehicle_type", "bus")
        'Bus'
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    
    key = f"{table}.{column}"
    
    # If no mapping exists, return original value
    if key not in ENUM_MAPPINGS:
        return value
    
    mapping = ENUM_MAPPINGS[key]
    
    # Try to find mapping
    if value in mapping:
        normalized = mapping[value]
        if normalized != value:
            logger.debug(
                f"Normalized {table}.{column}: '{value}' → '{normalized}'"
            )
        return normalized
    
    # Value not in mapping
    if strict:
        logger.warning(
            f"Unmapped enum value for {table}.{column}: '{value}'. "
            f"Expected one of: {list(set(mapping.values()))}"
        )
    
    return value


def normalize_data_enums(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all enum fields in a data dictionary for a specific table.
    
    Args:
        table: Table name
        data: Dictionary of column: value pairs
    
    Returns:
        Dictionary with normalized enum values
    
    Example:
        >>> normalize_data_enums("routes", {"direction": "UP", "status": "ACTIVE"})
        {'direction': 'up', 'status': 'active'}
    """
    normalized = data.copy()
    
    for column, value in data.items():
        key = f"{table}.{column}"
        if key in ENUM_MAPPINGS and value is not None:
            normalized[column] = normalize_enum_value(table, column, value)
    
    return normalized


def get_allowed_values(table: str, column: str) -> Optional[list]:
    """
    Get the list of database-allowed values for a table.column.
    
    Args:
        table: Table name
        column: Column name
    
    Returns:
        List of allowed values, or None if no constraint exists
    
    Example:
        >>> get_allowed_values("routes", "direction")
        ['up', 'down']
    """
    key = f"{table}.{column}"
    if key not in ENUM_MAPPINGS:
        return None
    
    # Return unique database values
    return list(set(ENUM_MAPPINGS[key].values()))
