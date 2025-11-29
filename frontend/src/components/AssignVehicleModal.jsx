import { useState, useEffect } from "react";
import { getAvailableVehiclesForTrip, assignVehicleOnly } from "../api";

/**
 * AssignVehicleModal - Modal for assigning a vehicle to a trip
 * Shows only vehicles available at the trip's scheduled time
 */
export default function AssignVehicleModal({ trip, onClose, onRefresh }) {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadVehicles() {
      try {
        const res = await getAvailableVehiclesForTrip(trip.trip_id);
        if (res.data.ok) {
          setVehicles(res.data.vehicles || []);
        } else {
          setError("Failed to load available vehicles");
        }
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load vehicles");
        setLoading(false);
      }
    }
    loadVehicles();
  }, [trip.trip_id]);

  const handleAssign = async () => {
    if (!selectedVehicle) {
      setError("Please select a vehicle");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await assignVehicleOnly(trip.trip_id, parseInt(selectedVehicle), 999);
      await onRefresh();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to assign vehicle");
      setSubmitting(false);
    }
  };

  const selectedVehicleInfo = vehicles.find(v => v.vehicle_id === parseInt(selectedVehicle));

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-5">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🚌</span>
            <div>
              <h3 className="text-xl font-bold">Assign Vehicle</h3>
              <p className="text-sm text-blue-100 mt-0.5">{trip.route_name || trip.display_name}</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-14 w-14 border-4 border-blue-200 border-t-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-4 font-medium">Loading available vehicles...</p>
              <p className="text-gray-400 text-sm mt-1">Checking time-based availability</p>
            </div>
          ) : (
            <>
              {/* Error Message */}
              {error && (
                <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                  <span className="text-red-500 text-lg">⚠️</span>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              {/* Trip Time Context */}
              <div className="mb-5 bg-blue-50 border border-blue-100 rounded-lg p-4">
                <p className="text-sm text-blue-700">
                  <strong>🕐 Trip Time:</strong> {trip.shift_time || "Not set"}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Showing vehicles available at this time slot
                </p>
              </div>

              {/* Vehicle Selection Grid */}
              {vehicles.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                  <span className="text-4xl">🚫</span>
                  <p className="text-gray-600 mt-3 font-medium">No vehicles available</p>
                  <p className="text-gray-400 text-sm mt-1">All vehicles are assigned to other trips at this time</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {vehicles.map((vehicle) => (
                    <label
                      key={vehicle.vehicle_id}
                      className={`flex items-center gap-4 p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-blue-300 hover:bg-blue-50 ${
                        selectedVehicle === String(vehicle.vehicle_id)
                          ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                          : "border-gray-200 bg-white"
                      }`}
                    >
                      <input
                        type="radio"
                        name="vehicle"
                        value={vehicle.vehicle_id}
                        checked={selectedVehicle === String(vehicle.vehicle_id)}
                        onChange={(e) => setSelectedVehicle(e.target.value)}
                        className="h-5 w-5 text-blue-600 focus:ring-blue-500"
                        disabled={submitting}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">
                            {vehicle.vehicle_type?.toLowerCase().includes("mini") ? "🚐" : "🚌"}
                          </span>
                          <span className="font-bold text-gray-800">
                            {vehicle.registration_number || vehicle.license_plate}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                          <span className="bg-gray-100 px-2 py-0.5 rounded">
                            {vehicle.vehicle_type || "Bus"}
                          </span>
                          <span>
                            👥 {vehicle.capacity || "?"} seats
                          </span>
                        </div>
                      </div>
                      {selectedVehicle === String(vehicle.vehicle_id) && (
                        <span className="text-green-500 text-xl">✓</span>
                      )}
                    </label>
                  ))}
                </div>
              )}

              {/* Selected Vehicle Summary */}
              {selectedVehicleInfo && (
                <div className="mt-5 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-800 font-medium">
                    ✅ Selected: {selectedVehicleInfo.registration_number || selectedVehicleInfo.license_plate}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {selectedVehicleInfo.vehicle_type} • {selectedVehicleInfo.capacity} seats capacity
                  </p>
                </div>
              )}

              <p className="text-xs text-gray-500 mt-4 text-center">
                {vehicles.length} vehicle(s) available for this time slot
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3 border-t">
          <button
            onClick={onClose}
            disabled={submitting}
            className="px-5 py-2.5 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAssign}
            disabled={loading || submitting || !selectedVehicle || vehicles.length === 0}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Assigning...
              </>
            ) : (
              <>🚌 Assign Vehicle</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
