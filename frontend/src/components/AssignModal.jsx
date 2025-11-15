import { useState, useEffect } from "react";
import { assignVehicle, getManageContext } from "../api";

export default function AssignModal({ trip, onClose, onRefresh }) {
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState("");
  const [selectedDriver, setSelectedDriver] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await getManageContext();
        setVehicles(res.data.vehicles || []);
        setDrivers(res.data.drivers || []);
        setLoading(false);
      } catch (err) {
        setError("Failed to load vehicles and drivers");
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleAssign = async () => {
    if (!selectedVehicle || !selectedDriver) {
      setError("Please select both vehicle and driver");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await assignVehicle({
        trip_id: trip.trip_id,
        vehicle_id: parseInt(selectedVehicle),
        driver_id: parseInt(selectedDriver),
        user_id: 999, // Admin user ID
      });
      await onRefresh();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to assign vehicle");
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="bg-blue-600 text-white p-4 rounded-t-lg">
          <h3 className="text-xl font-semibold">🚌 Assign Vehicle & Driver</h3>
          <p className="text-sm text-blue-100 mt-1">{trip.route_name}</p>
        </div>

        {/* Body */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-4">Loading vehicles and drivers...</p>
            </div>
          ) : (
            <>
              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                  ❌ {error}
                </div>
              )}

              {/* Vehicle Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Vehicle
                </label>
                <select
                  value={selectedVehicle}
                  onChange={(e) => setSelectedVehicle(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={submitting}
                >
                  <option value="">-- Choose Vehicle --</option>
                  {vehicles
                    .filter(v => v.status === "available")
                    .map((v) => (
                      <option key={v.vehicle_id} value={v.vehicle_id}>
                        {v.license_plate} ({v.vehicle_type} - {v.capacity} seats)
                      </option>
                    ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {vehicles.filter(v => v.status === "available").length} available vehicles
                </p>
              </div>

              {/* Driver Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Driver
                </label>
                <select
                  value={selectedDriver}
                  onChange={(e) => setSelectedDriver(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={submitting}
                >
                  <option value="">-- Choose Driver --</option>
                  {drivers
                    .filter(d => d.status === "available")
                    .map((d) => (
                      <option key={d.driver_id} value={d.driver_id}>
                        {d.name} - {d.phone}
                      </option>
                    ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {drivers.filter(d => d.status === "available").length} available drivers
                </p>
              </div>

              {/* Trip Info Summary */}
              <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm">
                <p className="text-gray-600"><strong>Trip:</strong> {trip.route_name}</p>
                <p className="text-gray-600"><strong>Date:</strong> {trip.trip_date}</p>
                <p className="text-gray-600"><strong>Time:</strong> {trip.shift_time}</p>
                <p className="text-gray-600"><strong>Bookings:</strong> {trip.booked_count} confirmed</p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-4 rounded-b-lg flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-800 rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAssign}
            disabled={loading || submitting || !selectedVehicle || !selectedDriver}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Assigning...
              </>
            ) : (
              <>✅ Assign</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
