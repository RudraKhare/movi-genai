import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || "http://localhost:8000/api",
  headers: { 
    "x-api-key": import.meta.env.VITE_MOVI_API_KEY || "dev-key-change-in-production" 
  },
});

// Dashboard and context endpoints
export const getDashboard = () => api.get("/context/dashboard");
export const getManageContext = () => api.get("/context/manage");

// Trip action endpoints
export const assignVehicle = (data) => api.post("/actions/assign_vehicle", data);
export const removeVehicle = (data) => api.post("/actions/remove_vehicle", data);
export const cancelTrip = (data) => api.post("/actions/cancel_trip", data);

// Audit log endpoints
export const getAuditLogs = (entityType, entityId, limit = 10) =>
  api.get(`/audit/logs/${entityType}/${entityId}?limit=${limit}`);
export const getRecentAuditLogs = (limit = 20) =>
  api.get(`/audit/logs/recent?limit=${limit}`);

// Health check
export const getHealthStatus = () => api.get("/health/status");

// Route Management endpoints (Day 6)
export const createStop = (data) => api.post("/routes/stops/create", data);
export const createPath = (data) => api.post("/routes/paths/create", data);
export const createRoute = (data) => api.post("/routes/create", data);
export const getRouteStops = (routeId) => api.get(`/routes/${routeId}/stops`);

// Agent endpoints (Day 9)
export const sendAgentMessage = (payload) => {
  console.log("🌐 [API] sendAgentMessage called with payload:", JSON.stringify(payload, null, 2));
  return api.post("/agent/message", payload);
};
export const confirmAgentAction = (payload) => api.post("/agent/confirm", payload);

// Agent image endpoint (Day 10)
export const uploadAgentImage = (formData) => 
  api.post("/agent/image", formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

// Status management endpoints (Trip Status Updater)
export const forceStatusUpdate = () => api.post("/status/force_update");
export const getStatusInfo = () => api.get("/status/status_info");
export const manualStatusUpdate = (tripId, newStatus, userId = 1) => 
  api.post("/status/manual_update", { trip_id: tripId, new_status: newStatus, user_id: userId });

// Resources endpoints - Drivers & Vehicles with dynamic availability
export const getAllDrivers = () => api.get("/resources/drivers/all");
export const getDriverDetails = (driverId) => api.get(`/resources/drivers/${driverId}`);
export const getAllVehicles = () => api.get("/resources/vehicles/all");
export const getAvailableVehicles = () => api.get("/resources/vehicles/available");
export const getVehicleDetails = (vehicleId) => api.get(`/resources/vehicles/${vehicleId}`);

// Time-aware availability for a specific trip
export const getAvailableVehiclesForTrip = (tripId) => api.get(`/resources/vehicles/available-for-trip/${tripId}`);
export const getAvailableDriversForTrip = (tripId) => api.get(`/resources/drivers/available-for-trip/${tripId}`);

// Assignment endpoints (single entity)
export const assignVehicleOnly = (tripId, vehicleId, userId = 1) => 
  api.post("/actions/assign_vehicle_only", { trip_id: tripId, vehicle_id: vehicleId, user_id: userId });
export const assignDriverOnly = (tripId, driverId, userId = 1) => 
  api.post("/actions/assign_driver_only", { trip_id: tripId, driver_id: driverId, user_id: userId });

// Booking management endpoints
export const addBookings = (tripId, count, userId = 1) => 
  api.post("/actions/add_bookings", { trip_id: tripId, count, user_id: userId });
export const reduceBookings = (tripId, count, userId = 1) => 
  api.post("/actions/reduce_bookings", { trip_id: tripId, count, user_id: userId });
export const checkSeatAvailability = (tripId) => 
  api.get(`/actions/seat_availability/${tripId}`);

export default api;
