import { useState } from "react";
import AssignModal from "./AssignModal";
import { removeVehicle, cancelTrip } from "../api";

export default function TripDetail({ trip, onRefresh }) {
  const [showAssign, setShowAssign] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRemove = async () => {
    if (!confirm("Remove vehicle deployment from this trip? Bookings will remain.")) return;
    
    setLoading(true);
    setError(null);
    try {
      await removeVehicle({ 
        trip_id: trip.trip_id, 
        user_id: 999,
        cancel_bookings: false
      });
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to remove vehicle");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Cancel this trip? All confirmed bookings will be cancelled.")) return;
    
    setLoading(true);
    setError(null);
    try {
      await cancelTrip({ 
        trip_id: trip.trip_id, 
        user_id: 999
      });
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to cancel trip");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-4xl">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {trip.route_name}
          </h2>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>🆔 Trip #{trip.trip_id}</span>
            <span>📅 {trip.trip_date}</span>
            <span>🕐 {trip.shift_time}</span>
            <span>📍 {trip.direction}</span>
          </div>
        </div>

        {/* Status Badge */}
        <div className="mb-6">
          <span className={`inline-block px-4 py-2 rounded-lg font-semibold ${
            trip.live_status === "COMPLETED" ? "bg-green-100 text-green-800" :
            trip.live_status === "IN_PROGRESS" ? "bg-blue-100 text-blue-800" :
            trip.live_status === "SCHEDULED" ? "bg-yellow-100 text-yellow-800" :
            trip.live_status === "CANCELLED" ? "bg-red-100 text-red-800" :
            "bg-gray-100 text-gray-800"
          }`}>
            Status: {trip.live_status}
          </span>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            ❌ {error}
          </div>
        )}

        {/* Info Cards */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Deployment Info */}
          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">🚌 Deployment</h3>
            {trip.vehicle_id ? (
              <div className="space-y-2 text-sm">
                <p className="flex justify-between">
                  <span className="text-gray-600">Vehicle:</span>
                  <span className="font-medium">{trip.vehicle_number || `#${trip.vehicle_id}`}</span>
                </p>
                <p className="flex justify-between">
                  <span className="text-gray-600">Driver:</span>
                  <span className="font-medium">{trip.driver_name || `#${trip.driver_id}`}</span>
                </p>
                <p className="text-green-600 text-xs mt-2">✅ Deployed</p>
              </div>
            ) : (
              <p className="text-orange-600 text-sm">⚠️ Not yet deployed</p>
            )}
          </div>

          {/* Booking Info */}
          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">👥 Bookings</h3>
            <div className="space-y-2 text-sm">
              <p className="flex justify-between">
                <span className="text-gray-600">Confirmed:</span>
                <span className="font-medium text-blue-600">{trip.booked_count}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-gray-600">Seats Booked:</span>
                <span className="font-medium">{trip.seats_booked || 0}</span>
              </p>
              {trip.booked_count > 0 ? (
                <p className="text-green-600 text-xs mt-2">✅ Has bookings</p>
              ) : (
                <p className="text-gray-500 text-xs mt-2">No bookings yet</p>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="bg-gray-50 border rounded-lg p-4">
          <h3 className="font-semibold text-gray-700 mb-4">⚡ Actions</h3>
          <div className="flex gap-3 flex-wrap">
            <button
              onClick={() => setShowAssign(true)}
              disabled={loading || trip.live_status === "CANCELLED"}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              ➕ Assign Vehicle
            </button>
            
            <button
              onClick={handleRemove}
              disabled={loading || !trip.vehicle_id || trip.live_status === "CANCELLED"}
              className="bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              ➖ Remove Vehicle
            </button>
            
            <button
              onClick={handleCancel}
              disabled={loading || trip.live_status === "CANCELLED" || trip.live_status === "COMPLETED"}
              className="bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              ❌ Cancel Trip
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            💡 Tip: Assign a vehicle and driver to deploy this trip. Cancel will affect all confirmed bookings.
          </p>
        </div>

        {/* Loading Overlay */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-40">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-center mt-4 text-gray-700">Processing...</p>
            </div>
          </div>
        )}
      </div>

      {/* Assign Modal */}
      {showAssign && (
        <AssignModal
          trip={trip}
          onClose={() => setShowAssign(false)}
          onRefresh={onRefresh}
        />
      )}
    </div>
  );
}
