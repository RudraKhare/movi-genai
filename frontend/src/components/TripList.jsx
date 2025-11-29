import TripStatusBadge from './TripStatusBadge';

export default function TripList({ trips, onSelect, selected }) {
  if (!trips || trips.length === 0) {
    return (
      <aside className="border-r overflow-y-auto bg-white p-6">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-3">📋</div>
          <p className="font-medium">No trips available</p>
          <p className="text-sm mt-1">Trips will appear here</p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="border-r overflow-y-auto bg-white shadow-sm">
      {/* Header with improved visibility */}
      <div className="sticky top-0 z-10 px-5 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md">
        <h2 className="font-bold text-xl flex items-center gap-2">
          <span className="text-2xl">📋</span>
          <span>Daily Trips</span>
        </h2>
        <p className="text-blue-100 text-sm mt-1">{trips.length} trip{trips.length !== 1 ? 's' : ''} today</p>
      </div>

      {/* Trip Cards */}
      <div className="divide-y divide-gray-200">
        {trips.map((trip) => {
          const bookingPercentage = trip.capacity ? Math.round((trip.seats_booked || 0) / trip.capacity * 100) : 0;
          const isSelected = selected?.trip_id === trip.trip_id;
          
          return (
            <div
              key={trip.trip_id}
              onClick={() => {
                console.log("🚀 [TripList] Trip clicked:", trip.trip_id, trip.route_name);
                console.log("🚀 [TripList] Calling onSelect with trip:", trip);
                onSelect(trip);
              }}
              className={`p-4 cursor-pointer transition-all duration-200 ${
                isSelected 
                  ? "bg-blue-50 border-l-4 border-l-blue-600 shadow-sm" 
                  : "hover:bg-gray-50 hover:shadow-sm"
              }`}
            >
              {/* Trip Header */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <p className="font-bold text-gray-900 text-base leading-tight">
                    {trip.route_name}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    ID Trip #{trip.trip_id}
                  </p>
                </div>
                <TripStatusBadge 
                  trip={trip} 
                  onStatusChange={(tripId, newStatus) => {
                    console.log(`🔄 Status changed: Trip ${tripId} → ${newStatus}`);
                    // Trigger refresh if needed
                  }}
                />
              </div>
              
              {/* Trip Details */}
              <div className="space-y-2 text-sm">
                {/* Date and Time */}
                <div className="flex items-center justify-between text-gray-700">
                  <span className="flex items-center gap-1.5">
                    <span className="text-base">📅</span>
                    <span>{trip.trip_date || '2025-11-11'}</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="text-base">🕐</span>
                    <span className="font-medium">{trip.shift_time || 'N/A'}</span>
                  </span>
                </div>

                {/* Booking Progress Bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span className="font-medium">Bookings: {trip.booked_count || 0}</span>
                    <span className="font-medium">Seats: {trip.seats_booked || 0}/{trip.capacity || '?'}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-300 ${
                        bookingPercentage >= 80 ? 'bg-green-500' :
                        bookingPercentage >= 50 ? 'bg-yellow-500' :
                        bookingPercentage > 0 ? 'bg-blue-500' :
                        'bg-gray-300'
                      }`}
                      style={{ width: `${Math.min(bookingPercentage, 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 text-right">{bookingPercentage}% booked</p>
                </div>

                {/* Deployment Status */}
                <div className="pt-1 space-y-1">
                  {trip.vehicle_id ? (
                    <div className="flex items-center gap-1.5 text-green-700 bg-green-50 px-2 py-1 rounded">
                      <span className="text-sm">🚌</span>
                      <span className="text-xs font-medium">{trip.registration_number || `Vehicle #${trip.vehicle_id}`}</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-orange-600 bg-orange-50 px-2 py-1 rounded">
                      <span className="text-sm">⚠️</span>
                      <span className="text-xs font-medium">No vehicle assigned</span>
                    </div>
                  )}
                  
                  {trip.driver_id ? (
                    <div className="flex items-center gap-1.5 text-blue-700 bg-blue-50 px-2 py-1 rounded">
                      <span className="text-sm">👨‍✈️</span>
                      <span className="text-xs font-medium">{trip.driver_name || `Driver #${trip.driver_id}`}</span>
                    </div>
                  ) : trip.vehicle_id && (
                    <div className="flex items-center gap-1.5 text-orange-600 bg-orange-50 px-2 py-1 rounded">
                      <span className="text-sm">⚠️</span>
                      <span className="text-xs font-medium">No driver assigned</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
