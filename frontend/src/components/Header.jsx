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
              to="/"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                location.pathname === "/"
                  ? "bg-blue-800 text-white"
                  : "hover:bg-blue-700 text-blue-100"
              }`}
            >
              🚌 Dashboard
            </Link>
            <Link
              to="/manage"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                location.pathname === "/manage"
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

        {/* Summary Stats */}
        {summary && Object.keys(summary).length > 0 && (
          <div className="mt-4 flex gap-6 text-sm">
            <div className="bg-blue-800 bg-opacity-50 px-4 py-2 rounded-lg">
              <span className="text-blue-200">Total Trips:</span>
              <span className="ml-2 font-bold">{summary.total_trips || 0}</span>
            </div>
            <div className="bg-blue-800 bg-opacity-50 px-4 py-2 rounded-lg">
              <span className="text-blue-200">Deployed:</span>
              <span className="ml-2 font-bold text-green-300">{summary.deployed || 0}</span>
            </div>
            <div className="bg-blue-800 bg-opacity-50 px-4 py-2 rounded-lg">
              <span className="text-blue-200">Pending:</span>
              <span className="ml-2 font-bold text-yellow-300">{summary.pending_deployment || 0}</span>
            </div>
            <div className="bg-blue-800 bg-opacity-50 px-4 py-2 rounded-lg">
              <span className="text-blue-200">Total Bookings:</span>
              <span className="ml-2 font-bold">{summary.total_bookings || 0}</span>
            </div>
            <div className="bg-blue-800 bg-opacity-50 px-4 py-2 rounded-lg">
              <span className="text-blue-200">Seats Booked:</span>
              <span className="ml-2 font-bold">{summary.total_seats_booked || 0}</span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
