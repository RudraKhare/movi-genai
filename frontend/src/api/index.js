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

export default api;
