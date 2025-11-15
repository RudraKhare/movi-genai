import { Link, useLocation } from "react-router-dom";

export default function Header({ onRefresh, summary }) {
  const location = useLocation();
  
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center gap-4">
            <div className="text-3xl">🚌</div>
            <div>
              <h1 className="text-2xl font-bold">MOVI Dashboard</h1>
              <p className="text-sm text-blue-100">Multimodal Transport Operations</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-6">
            <Link
              to="/dashboard"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                location.pathname === "/dashboard"
                  ? "bg-blue-800 text-white"
                  : "hover:bg-blue-700 text-blue-100"
              }`}
            >
              🚌 Dashboard
            </Link>
            {/* Bug Fix: Changed route from /manage to /manage-route to match route definition in main.jsx */}
            <Link
              to="/manage-route"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                location.pathname === "/manage-route"
                  ? "bg-blue-800 text-white"
                  : "hover:bg-blue-700 text-blue-100"
              }`}
            >
              ⚙️ Manage Routes
            </Link>
          </nav>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            className="bg-blue-800 hover:bg-blue-900 px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <span className="text-lg">🔄</span>
            Refresh
          </button>
        </div>

        {/* Enhanced Summary Stats with Missing Features */}
        {summary && Object.keys(summary).length > 0 && (
          <div className="mt-4 grid grid-cols-5 gap-4">
            {/* Total Trips */}
            <div className="bg-white bg-opacity-20 backdrop-blur-sm px-4 py-3 rounded-xl border border-white border-opacity-30 hover:bg-opacity-25 transition-all">
              <p className="text-blue-100 text-xs font-medium mb-1">Total Trips</p>
              <p className="text-2xl font-bold">{summary.total_trips || 0}</p>
            </div>

            {/* Deployed vs Pending */}
            <div className="bg-white bg-opacity-20 backdrop-blur-sm px-4 py-3 rounded-xl border border-white border-opacity-30 hover:bg-opacity-25 transition-all">
              <p className="text-blue-100 text-xs font-medium mb-1">Deployed</p>
              <p className="text-2xl font-bold text-green-300">{summary.deployed || 0}</p>
              <p className="text-xs text-blue-200 mt-1">
                {summary.pending_deployment || 0} pending
              </p>
            </div>

            {/* Vehicles Not Assigned (Missing Feature A) */}
            <div className="bg-white bg-opacity-20 backdrop-blur-sm px-4 py-3 rounded-xl border border-white border-opacity-30 hover:bg-opacity-25 transition-all">
              <p className="text-blue-100 text-xs font-medium mb-1">Vehicles Not Assigned</p>
              <p className="text-2xl font-bold text-orange-300">
                {summary.pending_deployment || 0}
              </p>
              <p className="text-xs text-blue-200 mt-1">trips need vehicles</p>
            </div>

            {/* Bookings */}
            <div className="bg-white bg-opacity-20 backdrop-blur-sm px-4 py-3 rounded-xl border border-white border-opacity-30 hover:bg-opacity-25 transition-all">
              <p className="text-blue-100 text-xs font-medium mb-1">Total Bookings</p>
              <p className="text-2xl font-bold">{summary.total_bookings || 0}</p>
              <p className="text-xs text-blue-200 mt-1">
                {summary.total_seats_booked || 0} seats
              </p>
            </div>

            {/* Ongoing Trips (Missing Feature A) */}
            <div className="bg-white bg-opacity-20 backdrop-blur-sm px-4 py-3 rounded-xl border border-white border-opacity-30 hover:bg-opacity-25 transition-all">
              <p className="text-blue-100 text-xs font-medium mb-1">Ongoing Trips</p>
              <p className="text-2xl font-bold text-yellow-300">
                {summary.ongoing_trips || 0}
              </p>
              <p className="text-xs text-blue-200 mt-1">currently running</p>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
