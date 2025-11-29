// Utility functions for MoviWidget command generation

/**
 * Action types for command generation
 */
export const ACTION_TYPES = {
  ASSIGN_DRIVER: 'assign_driver',
  ASSIGN_VEHICLE: 'assign_vehicle',
  REMOVE_VEHICLE: 'remove_vehicle',
  CANCEL_TRIP: 'cancel_trip',
};

/**
 * Generate a user command based on selection type and option data
 * @param {Object} option - The selected option (driver or vehicle)
 * @param {string} selectionType - Type of selection ('driver' or 'vehicle')
 * @param {number} tripId - The trip ID to assign to
 * @param {Object} context - Additional context for command generation
 * @returns {Object} - Object with user_message (for display) and backend_command (for API)
 */
export const makeUserCommand = (option, selectionType, tripId, context = {}) => {
  // Validate inputs
  if (!option || !selectionType) {
    console.error('makeUserCommand: Missing required parameters', { option, selectionType, tripId });
    throw new Error('Missing required parameters for command generation');
  }

  switch (selectionType) {
    case 'driver':
      if (!option.driver_id) {
        console.error('Driver option missing driver_id', option);
        throw new Error('Driver option missing driver_id');
      }
      // Enhanced structured command with context - use correct driver name field
      const driverName = option.driver_name || option.name || option.label || 'Unknown';
      return {
        user_message: `Assign driver ${driverName} to this trip`,
        backend_command: `STRUCTURED_CMD:assign_driver|trip_id:${tripId}|driver_id:${option.driver_id}|driver_name:${driverName}|context:selection_ui`
      };

    case 'vehicle':
      if (!option.vehicle_id) {
        console.error('Vehicle option missing vehicle_id', option);
        throw new Error('Vehicle option missing vehicle_id');
      }
      // Enhanced structured command with context
      const vehicleName = option.registration_number || option.name || option.license_plate || 'Unknown';
      return {
        user_message: `Assign vehicle ${vehicleName} to this trip`,
        backend_command: `STRUCTURED_CMD:assign_vehicle|trip_id:${tripId}|vehicle_id:${option.vehicle_id}|vehicle_name:${vehicleName}|context:selection_ui`
      };

    case 'ocr_action':
      // OCR action - user clicked an action button after image recognition
      if (!option.action || !option.trip_id) {
        console.error('OCR action option missing action or trip_id', option);
        throw new Error('OCR action option missing required fields');
      }
      const actionLabels = {
        'assign_vehicle': 'Assign vehicle to',
        'remove_vehicle': 'Remove vehicle from',
        'assign_driver': 'Assign driver to',
        'remove_driver': 'Remove driver from',
        'cancel_trip': 'Cancel',
        'update_trip_status': 'Update status of'
      };
      return {
        user_message: `${actionLabels[option.action] || option.action} trip ${option.trip_id}`,
        backend_command: `STRUCTURED_CMD:${option.action}|trip_id:${option.trip_id}|context:ocr_image`
      };

    case 'ocr_trip_select':
      // OCR trip selection - user picked from multiple matches
      if (!option.trip_id) {
        console.error('OCR trip select option missing trip_id', option);
        throw new Error('OCR trip select option missing trip_id');
      }
      return {
        user_message: `Selected trip: ${option.display_name || option.label}`,
        backend_command: `STRUCTURED_CMD:select_trip|trip_id:${option.trip_id}|display_name:${option.display_name || option.label}|context:ocr_selection`
      };

    default:
      console.warn('Unknown selection type:', selectionType, option);
      throw new Error(`Unknown selection type: ${selectionType}`);
  }
};

/**
 * Validate option data based on selection type
 * @param {Object} option - The option to validate
 * @param {string} selectionType - Type of selection
 * @returns {boolean} - True if valid, false otherwise
 */
export const validateOption = (option, selectionType) => {
  if (!option || !selectionType) {
    return false;
  }

  switch (selectionType) {
    case 'driver':
      return option.driver_id != null && option.driver_name;
    case 'vehicle':
      return option.vehicle_id != null;
    case 'ocr_action':
      return option.action != null && option.trip_id != null;
    case 'ocr_trip_select':
      return option.trip_id != null;
    default:
      return false;
  }
};

/**
 * Get display icon for selection type
 * @param {string} selectionType - Type of selection
 * @returns {string} - Emoji icon
 */
export const getSelectionIcon = (selectionType) => {
  switch (selectionType) {
    case 'driver':
      return '👤';
    case 'vehicle':
      return '🚗';
    case 'ocr_action':
      return '📸';
    case 'ocr_trip_select':
      return '📋';
    default:
      return '📋';
  }
};

/**
 * Get display label for selection type
 * @param {string} selectionType - Type of selection
 * @returns {string} - Human-readable label
 */
export const getSelectionLabel = (selectionType) => {
  switch (selectionType) {
    case 'driver':
      return 'Available Drivers';
    case 'vehicle':
      return 'Available Vehicles';
    case 'ocr_action':
      return 'Choose an Action';
    case 'ocr_trip_select':
      return 'Select a Trip';
    default:
      return 'Available Options';
  }
};
