export default function TripList({ trips, onSelect, selected }) {
  if (!trips || trips.length === 0) {
    return (
      <aside className="w-1/3 border-r overflow-y-auto bg-white p-4">
        <p className="text-gray-500 text-center">No trips available</p>
      </aside>
    );
  }

  return (
    <aside className="w-1/3 border-r overflow-y-auto bg-white">
      <div className="p-4 border-b bg-gray-50">
        <h2 className="font-semibold text-lg">Daily Trips ({trips.length})</h2>
      </div>
      {trips.map((trip) => (
        <div
          key={trip.trip_id}
          onClick={() => onSelect(trip)}
          className={`p-4 cursor-pointer border-b hover:bg-blue-50 transition-colors ${
            selected?.trip_id === trip.trip_id ? "bg-blue-100 border-l-4 border-l-blue-600" : ""
          }`}
        >
          <div className="flex justify-between items-start mb-2">
            <p className="font-semibold text-gray-900">{trip.route_name}</p>
            <span className={`text-xs px-2 py-1 rounded ${
              trip.live_status === "COMPLETED" ? "bg-green-100 text-green-800" :
              trip.live_status === "IN_PROGRESS" ? "bg-blue-100 text-blue-800" :
              trip.live_status === "SCHEDULED" ? "bg-yellow-100 text-yellow-800" :
              "bg-gray-100 text-gray-800"
            }`}>
              {trip.live_status}
            </span>
          </div>
          
          <div className="text-sm text-gray-600 space-y-1">
            <p className="flex justify-between">
              <span>📅 {trip.trip_date}</span>
              <span>🕐 {trip.shift_time}</span>
            </p>
            <p className="flex justify-between">
              <span>👥 Booked: {trip.booked_count}</span>
              <span>💺 Seats: {trip.seats_booked || 0}</span>
            </p>
            {trip.vehicle_id && (
              <p className="text-xs text-green-600">
                🚌 {trip.vehicle_number || `Vehicle #${trip.vehicle_id}`}
              </p>
            )}
            {trip.driver_id && (
              <p className="text-xs text-blue-600">
                👨‍✈️ {trip.driver_name || `Driver #${trip.driver_id}`}
              </p>
            )}
          </div>
        </div>
      ))}
    </aside>
  );
}
