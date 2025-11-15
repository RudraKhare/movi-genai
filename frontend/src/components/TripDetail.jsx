import { useState, useEffect } from "react";
import AssignModal from "./AssignModal";
import { removeVehicle, cancelTrip, getRouteStops } from "../api";

export default function TripDetail({ trip, onRefresh }) {
  const [showAssign, setShowAssign] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stops, setStops] = useState([]);
  const [loadingStops, setLoadingStops] = useState(false);

  // Fetch stops when trip changes
  useEffect(() => {
    const fetchStops = async () => {
      if (!trip?.route_id) return;
      
      setLoadingStops(true);
      try {
        const response = await getRouteStops(trip.route_id);
        setStops(response.data.stops || []);
      } catch (err) {
        console.error("Failed to fetch stops:", err);
        setStops([]);
      } finally {
        setLoadingStops(false);
      }
    };

    fetchStops();
  }, [trip?.route_id]);

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

        {/* Info Cards Grid - Enhanced with Missing Features */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Deployment Info */}
          <div className="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span className="text-xl">🚌</span>
              <span>Deployment</span>
            </h3>
            {trip.vehicle_id ? (
              <div className="space-y-2 text-sm">
                <p className="flex justify-between">
                  <span className="text-gray-600">Vehicle:</span>
                  <span className="font-medium">{trip.registration_number || `#${trip.vehicle_id}`}</span>
                </p>
                <p className="flex justify-between">
                  <span className="text-gray-600">Driver:</span>
                  <span className="font-medium">{trip.driver_name || `#${trip.driver_id || 'N/A'}`}</span>
                </p>
                {trip.capacity && (
                  <p className="flex justify-between">
                    <span className="text-gray-600">Vehicle Capacity:</span>
                    <span className="font-medium">{trip.capacity} seats</span>
                  </p>
                )}
                <div className="mt-3 pt-3 border-t">
                  <p className="text-green-600 text-xs font-medium flex items-center gap-1">
                    <span>✅</span>
                    <span>Deployed</span>
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-orange-600 text-sm font-medium flex items-center gap-1">
                <span>⚠️</span>
                <span>Not yet deployed</span>
              </p>
            )}
          </div>

          {/* Booking Info with Progress Bar (Missing Feature G) */}
          <div className="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span className="text-xl">👥</span>
              <span>Bookings</span>
            </h3>
            <div className="space-y-2 text-sm">
              <p className="flex justify-between">
                <span className="text-gray-600">Confirmed:</span>
                <span className="font-medium text-blue-600">{trip.booked_count || 0}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-gray-600">Seats Booked:</span>
                <span className="font-medium">{trip.seats_booked || 0}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-gray-600">Vehicle Capacity:</span>
                <span className="font-medium">
                  {trip.capacity ? `${trip.capacity} seats` : 
                   trip.vehicle_id ? 'Unknown' : 'Not deployed'}
                </span>
              </p>
              
              {/* Booking Progress Bar - Only show if capacity is available */}
              {trip.capacity && trip.capacity > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span className="font-medium">Booking Progress</span>
                    <span className="font-bold text-blue-600">
                      {Math.round((trip.seats_booked || 0) / trip.capacity * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        ((trip.seats_booked || 0) / trip.capacity * 100 >= 80) ? 'bg-green-500' :
                        ((trip.seats_booked || 0) / trip.capacity * 100 >= 50) ? 'bg-yellow-500' :
                        (trip.seats_booked || 0) > 0 ? 'bg-blue-500' :
                        'bg-gray-300'
                      }`}
                      style={{ width: `${Math.min((trip.seats_booked || 0) / trip.capacity * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
              
              {/* Status message */}
              {trip.booked_count > 0 ? (
                <p className="text-green-600 text-xs mt-2 flex items-center gap-1">
                  <span>✅</span>
                  <span>{trip.booked_count} confirmed booking{trip.booked_count !== 1 ? 's' : ''}</span>
                </p>
              ) : trip.vehicle_id ? (
                <p className="text-gray-500 text-xs mt-2 flex items-center gap-1">
                  <span>ℹ️</span>
                  <span>No confirmed bookings yet</span>
                </p>
              ) : (
                <p className="text-orange-600 text-xs mt-2 flex items-center gap-1">
                  <span>⚠️</span>
                  <span>Deploy vehicle first</span>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Route-level Summary (Missing Feature F) */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6 shadow-sm">
          <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span className="text-xl">🛣️</span>
            <span>Route Information</span>
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-600 text-xs mb-1">Route Name</p>
              <p className="font-medium text-gray-900">{trip.route_name || 'N/A'}</p>
            </div>
            <div>
              <p className="text-gray-600 text-xs mb-1">Path</p>
              <p className="font-medium text-gray-900">{trip.path_name || 'N/A'}</p>
            </div>
            <div>
              <p className="text-gray-600 text-xs mb-1">Direction</p>
              <p className="font-medium text-gray-900 capitalize">{trip.direction || 'N/A'}</p>
            </div>
          </div>
          
          {/* Start and End Points */}
          {(trip.start_point || trip.end_point) && (
            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-blue-200">
              <div>
                <p className="text-gray-600 text-xs mb-1">📍 Start Point</p>
                <p className="font-medium text-gray-900">{trip.start_point || 'Not specified'}</p>
              </div>
              <div>
                <p className="text-gray-600 text-xs mb-1">🏁 End Point</p>
                <p className="font-medium text-gray-900">{trip.end_point || 'Not specified'}</p>
              </div>
            </div>
          )}
        </div>

        {/* Stops Information */}
        {stops.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span className="text-xl">🚏</span>
              <span>Stops Along Route</span>
              <span className="text-xs text-gray-500 ml-2">({stops.length} stops)</span>
            </h3>
            
            {loadingStops ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-sm text-gray-600">Loading stops...</span>
              </div>
            ) : (
              <div className="space-y-2">
                {stops.map((stop, index) => (
                  <div 
                    key={stop.stop_id}
                    className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 transition-colors"
                  >
                    {/* Stop Number Badge */}
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                      index === 0 ? 'bg-green-100 text-green-700' :
                      index === stops.length - 1 ? 'bg-red-100 text-red-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {index + 1}
                    </div>
                    
                    {/* Stop Details */}
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 text-sm">{stop.name}</p>
                      {stop.address && (
                        <p className="text-xs text-gray-500">{stop.address}</p>
                      )}
                    </div>
                    
                    {/* Special Badges */}
                    {index === 0 && (
                      <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded font-medium">
                        Start
                      </span>
                    )}
                    {index === stops.length - 1 && (
                      <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded font-medium">
                        End
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

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
