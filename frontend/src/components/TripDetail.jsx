import { useState, useEffect } from "react";
import AssignVehicleModal from "./AssignVehicleModal";
import AssignDriverModal from "./AssignDriverModal";
import ConfirmationModal from "./ConfirmationModal";
import TripStatusBadge from "./TripStatusBadge";
import { removeVehicle, cancelTrip, getRouteStops, addBookings, reduceBookings } from "../api";

export default function TripDetail({ trip, onRefresh }) {
  const [showAssignVehicle, setShowAssignVehicle] = useState(false);
  const [showAssignDriver, setShowAssignDriver] = useState(false);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bookingError, setBookingError] = useState(null);
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [stops, setStops] = useState([]);
  const [loadingStops, setLoadingStops] = useState(false);
  const [bookingCount, setBookingCount] = useState(1);

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

  // Clear messages when trip changes
  useEffect(() => {
    setBookingError(null);
    setBookingSuccess(null);
    setBookingCount(1);
  }, [trip?.trip_id]);

  // Calculate booking stats for confirmation dialogs
  const bookedCount = trip?.booked_count || 0;
  const capacity = trip?.capacity || 40;
  const bookingPercentage = Math.round((bookedCount / capacity) * 100);

  const handleRemove = async () => {
    setLoading(true);
    setError(null);
    try {
      await removeVehicle({ 
        trip_id: trip.trip_id, 
        user_id: 999,
        cancel_bookings: false
      });
      setShowRemoveConfirm(false);
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to remove vehicle");
      setShowRemoveConfirm(false);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    setLoading(true);
    setError(null);
    try {
      await cancelTrip({ 
        trip_id: trip.trip_id, 
        user_id: 999
      });
      setShowCancelConfirm(false);
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to cancel trip");
      setShowCancelConfirm(false);
    } finally {
      setLoading(false);
    }
  };

  const handleAddBookings = async () => {
    if (!trip.vehicle_id) {
      setBookingError("Cannot add bookings - no vehicle assigned");
      return;
    }
    
    setBookingLoading(true);
    setBookingError(null);
    setBookingSuccess(null);
    
    try {
      const response = await addBookings(trip.trip_id, bookingCount);
      setBookingSuccess(response.data.message || `Added ${bookingCount} booking(s)`);
      setBookingCount(1);
      await onRefresh();
    } catch (err) {
      setBookingError(err.response?.data?.error || err.response?.data?.message || "Failed to add bookings");
    } finally {
      setBookingLoading(false);
    }
  };

  const handleReduceBookings = async () => {
    if ((trip.booked_count || 0) === 0) {
      setBookingError("No bookings to reduce");
      return;
    }
    
    if (bookingCount > (trip.booked_count || 0)) {
      setBookingError(`Cannot reduce by ${bookingCount}. Only ${trip.booked_count} booking(s) exist.`);
      return;
    }
    
    if (!confirm(`Reduce ${bookingCount} booking(s) from this trip?`)) return;
    
    setBookingLoading(true);
    setBookingError(null);
    setBookingSuccess(null);
    
    try {
      const response = await reduceBookings(trip.trip_id, bookingCount);
      setBookingSuccess(response.data.message || `Reduced ${bookingCount} booking(s)`);
      setBookingCount(1);
      await onRefresh();
    } catch (err) {
      setBookingError(err.response?.data?.error || err.response?.data?.message || "Failed to reduce bookings");
    } finally {
      setBookingLoading(false);
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

        {/* Status Badge with Live Updates */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-gray-700 font-medium">Current Status:</span>
            <TripStatusBadge 
              trip={trip} 
              onStatusChange={(tripId, newStatus) => {
                console.log(`🔄 Trip ${tripId} status changed to ${newStatus}`);
                // Trigger refresh of trip data
                if (onRefresh) {
                  onRefresh();
                }
              }}
            />
          </div>
          
          {/* Status explanation */}
          <div className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
            {trip.live_status === "SCHEDULED" && "📅 Waiting for departure time"}
            {trip.live_status === "IN_PROGRESS" && "🚛 Currently running"}
            {trip.live_status === "COMPLETED" && "✅ Trip finished"}
            {trip.live_status === "CANCELLED" && "❌ Trip cancelled"}
          </div>
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

              {/* Booking Management Controls */}
              {trip.vehicle_id && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-600 font-medium mb-2">Manage Bookings</p>
                  
                  {/* Error/Success Messages */}
                  {bookingError && (
                    <p className="text-red-600 text-xs mb-2 flex items-center gap-1">
                      <span>❌</span>
                      <span>{bookingError}</span>
                    </p>
                  )}
                  {bookingSuccess && (
                    <p className="text-green-600 text-xs mb-2 flex items-center gap-1">
                      <span>✅</span>
                      <span>{bookingSuccess}</span>
                    </p>
                  )}
                  
                  <div className="flex items-center gap-2">
                    {/* Count Input */}
                    <div className="flex items-center border rounded-md bg-gray-50">
                      <button
                        onClick={() => setBookingCount(Math.max(1, bookingCount - 1))}
                        className="px-2 py-1 text-gray-600 hover:bg-gray-200 transition-colors rounded-l-md"
                        disabled={bookingLoading}
                      >
                        −
                      </button>
                      <input
                        type="number"
                        min="1"
                        max={trip.capacity || 50}
                        value={bookingCount}
                        onChange={(e) => setBookingCount(Math.max(1, parseInt(e.target.value) || 1))}
                        className="w-12 text-center text-sm bg-transparent border-x py-1 focus:outline-none"
                        disabled={bookingLoading}
                      />
                      <button
                        onClick={() => setBookingCount(Math.min((trip.capacity || 50), bookingCount + 1))}
                        className="px-2 py-1 text-gray-600 hover:bg-gray-200 transition-colors rounded-r-md"
                        disabled={bookingLoading}
                      >
                        +
                      </button>
                    </div>
                    
                    {/* Add Button */}
                    <button
                      onClick={handleAddBookings}
                      disabled={bookingLoading || !trip.vehicle_id || (trip.seats_booked >= trip.capacity)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors flex items-center gap-1 ${
                        bookingLoading || !trip.vehicle_id || (trip.seats_booked >= trip.capacity)
                          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                          : 'bg-green-500 text-white hover:bg-green-600'
                      }`}
                    >
                      {bookingLoading ? '...' : '➕ Add'}
                    </button>
                    
                    {/* Reduce Button */}
                    <button
                      onClick={handleReduceBookings}
                      disabled={bookingLoading || (trip.booked_count || 0) === 0}
                      className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors flex items-center gap-1 ${
                        bookingLoading || (trip.booked_count || 0) === 0
                          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                          : 'bg-red-500 text-white hover:bg-red-600'
                      }`}
                    >
                      {bookingLoading ? '...' : '➖ Reduce'}
                    </button>
                  </div>
                  
                  {/* Available seats hint */}
                  {trip.capacity && (
                    <p className="text-xs text-gray-500 mt-2">
                      {trip.capacity - (trip.seats_booked || 0)} seats available
                    </p>
                  )}
                </div>
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
              onClick={() => setShowAssignVehicle(true)}
              disabled={loading || trip.live_status === "CANCELLED"}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              🚌 Assign Vehicle
            </button>
            
            <button
              onClick={() => setShowAssignDriver(true)}
              disabled={loading || trip.live_status === "CANCELLED"}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              👨‍✈️ Assign Driver
            </button>
            
            <button
              onClick={() => setShowRemoveConfirm(true)}
              disabled={loading || !trip.vehicle_id || trip.live_status === "CANCELLED"}
              className="bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              ➖ Remove Vehicle
            </button>
            
            <button
              onClick={() => setShowCancelConfirm(true)}
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

      {/* Assign Vehicle Modal */}
      {showAssignVehicle && (
        <AssignVehicleModal
          trip={trip}
          onClose={() => setShowAssignVehicle(false)}
          onRefresh={onRefresh}
        />
      )}

      {/* Assign Driver Modal */}
      {showAssignDriver && (
        <AssignDriverModal
          trip={trip}
          onClose={() => setShowAssignDriver(false)}
          onRefresh={onRefresh}
        />
      )}

      {/* Remove Vehicle Confirmation Modal */}
      <ConfirmationModal
        isOpen={showRemoveConfirm}
        onClose={() => setShowRemoveConfirm(false)}
        onConfirm={handleRemove}
        title="Remove Vehicle Assignment"
        icon="🚌"
        type="warning"
        tripName={trip.route_name || trip.display_name}
        bookingsAffected={bookedCount}
        bookingPercentage={bookingPercentage}
        consequences={[
          "The vehicle will be unassigned from this trip",
          "The driver assignment will also be removed",
          bookedCount > 0 
            ? `${bookedCount} confirmed booking(s) will remain but trip cannot operate without a vehicle`
            : "No bookings will be affected",
          "A trip-sheet will fail to generate until a new vehicle is assigned",
        ]}
        confirmText="Remove Vehicle"
        cancelText="Keep Assignment"
        loading={loading}
      />

      {/* Cancel Trip Confirmation Modal */}
      <ConfirmationModal
        isOpen={showCancelConfirm}
        onClose={() => setShowCancelConfirm(false)}
        onConfirm={handleCancel}
        title="Cancel Trip"
        icon="❌"
        type="danger"
        tripName={trip.route_name || trip.display_name}
        bookingsAffected={bookedCount}
        bookingPercentage={bookingPercentage}
        consequences={[
          "This trip will be permanently cancelled",
          bookedCount > 0 
            ? `All ${bookedCount} confirmed booking(s) will be cancelled automatically`
            : "No bookings to cancel",
          "Affected employees will need to be notified",
          "This action cannot be undone",
        ]}
        confirmText="Cancel Trip"
        cancelText="Keep Trip Active"
        loading={loading}
      />
    </div>
  );
}
