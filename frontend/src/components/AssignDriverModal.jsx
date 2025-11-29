import { useState, useEffect } from "react";
import { getAvailableDriversForTrip, assignDriverOnly } from "../api";

/**
 * AssignDriverModal - Modal for assigning a driver to a trip
 * Shows only drivers available at the trip's scheduled time
 */
export default function AssignDriverModal({ trip, onClose, onRefresh }) {
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadDrivers() {
      try {
        const res = await getAvailableDriversForTrip(trip.trip_id);
        if (res.data.ok) {
          // Backend returns "result" array, not "drivers"
          setDrivers(res.data.result || res.data.drivers || []);
        } else {
          setError(res.data.message || res.data.error || "Failed to load available drivers");
        }
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load drivers");
        setLoading(false);
      }
    }
    loadDrivers();
  }, [trip.trip_id]);

  const handleAssign = async () => {
    if (!selectedDriver) {
      setError("Please select a driver");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await assignDriverOnly(trip.trip_id, parseInt(selectedDriver), 999);
      await onRefresh();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to assign driver");
      setSubmitting(false);
    }
  };

  const selectedDriverInfo = drivers.find(d => d.driver_id === parseInt(selectedDriver));

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-5">
          <div className="flex items-center gap-3">
            <span className="text-3xl">👨‍✈️</span>
            <div>
              <h3 className="text-xl font-bold">Assign Driver</h3>
              <p className="text-sm text-green-100 mt-0.5">{trip.route_name || trip.display_name}</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-14 w-14 border-4 border-green-200 border-t-green-600 mx-auto"></div>
              <p className="text-gray-600 mt-4 font-medium">Loading available drivers...</p>
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
              <div className="mb-5 bg-green-50 border border-green-100 rounded-lg p-4">
                <p className="text-sm text-green-700">
                  <strong>🕐 Trip Time:</strong> {trip.shift_time || "Not set"}
                </p>
                <p className="text-xs text-green-600 mt-1">
                  Showing drivers available at this time slot
                </p>
              </div>

              {/* Driver Selection Grid */}
              {drivers.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                  <span className="text-4xl">🚫</span>
                  <p className="text-gray-600 mt-3 font-medium">No drivers available</p>
                  <p className="text-gray-400 text-sm mt-1">All drivers are assigned to other trips at this time</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {drivers.map((driver) => (
                    <label
                      key={driver.driver_id}
                      className={`flex items-center gap-4 p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-green-300 hover:bg-green-50 ${
                        selectedDriver === String(driver.driver_id)
                          ? "border-green-500 bg-green-50 ring-2 ring-green-200"
                          : "border-gray-200 bg-white"
                      }`}
                    >
                      <input
                        type="radio"
                        name="driver"
                        value={driver.driver_id}
                        checked={selectedDriver === String(driver.driver_id)}
                        onChange={(e) => setSelectedDriver(e.target.value)}
                        className="h-5 w-5 text-green-600 focus:ring-green-500"
                        disabled={submitting}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-lg">
                            👤
                          </span>
                          <div>
                            <span className="font-bold text-gray-800">
                              {driver.driver_name || driver.name}
                            </span>
                            <p className="text-sm text-gray-500">
                              📞 {driver.phone || driver.contact || "N/A"}
                            </p>
                          </div>
                        </div>
                        {driver.reason && (
                          <div className="mt-2 text-xs text-green-600 flex items-center gap-2">
                            <span className="bg-green-50 px-2 py-0.5 rounded">
                              ✓ {driver.reason}
                            </span>
                          </div>
                        )}
                      </div>
                      {selectedDriver === String(driver.driver_id) && (
                        <span className="text-green-500 text-xl">✓</span>
                      )}
                    </label>
                  ))}
                </div>
              )}

              {/* Selected Driver Summary */}
              {selectedDriverInfo && (
                <div className="mt-5 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-800 font-medium">
                    ✅ Selected: {selectedDriverInfo.driver_name || selectedDriverInfo.name}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    📞 {selectedDriverInfo.phone || selectedDriverInfo.contact || "No phone"}
                  </p>
                </div>
              )}

              <p className="text-xs text-gray-500 mt-4 text-center">
                {drivers.length} driver(s) available for this time slot
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
            disabled={loading || submitting || !selectedDriver || drivers.length === 0}
            className="px-5 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Assigning...
              </>
            ) : (
              <>👨‍✈️ Assign Driver</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
