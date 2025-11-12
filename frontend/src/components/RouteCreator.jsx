import { useState } from "react";
import { createRoute } from "../api";

export default function RouteCreator({ paths, routes, onRefresh }) {
  const [routeName, setRouteName] = useState("");
  const [shiftTime, setShiftTime] = useState("");
  const [pathId, setPathId] = useState("");
  const [direction, setDirection] = useState("UP");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCreate = async () => {
    if (!routeName.trim()) {
      setError("Route name is required");
      return;
    }
    if (!shiftTime) {
      setError("Shift time is required");
      return;
    }
    if (!pathId || pathId === "placeholder") {
      setError("Please select a path");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createRoute({
        route_name: routeName.trim(),
        shift_time: shiftTime,
        path_id: parseInt(pathId),
        direction,
      });
      setRouteName("");
      setShiftTime("");
      setPathId("");
      setDirection("UP");
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to create route");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 pb-3 border-b">
        <span className="text-2xl">🚌</span>
        <div>
          <h2 className="font-semibold text-lg text-gray-800">Routes</h2>
          <p className="text-xs text-gray-500">{routes.length} scheduled</p>
        </div>
      </div>

      {/* Existing Routes List */}
      <div className="mb-3 max-h-32 overflow-y-auto">
        {routes.length === 0 ? (
          <div className="text-center py-4 text-gray-400">
            <p className="text-xs">No routes yet</p>
          </div>
        ) : (
          <div className="space-y-1">
            {routes.map((route) => (
              <div
                key={route.route_id}
                className="border-b border-gray-100 py-2 hover:bg-gray-50"
              >
                <p className="text-sm font-medium text-gray-800">{route.route_name}</p>
                <div className="flex gap-2 mt-1">
                  <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                    {route.shift_time || "N/A"}
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                    {route.direction || "UP"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create New Route Form */}
      <div className="flex-1 flex flex-col">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Create New Route</h3>

        {/* Error Message */}
        {error && (
          <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
            ❌ {error}
          </div>
        )}

        {/* Route Name Input */}
        <input
          type="text"
          value={routeName}
          onChange={(e) => setRouteName(e.target.value)}
          disabled={loading}
          className="border border-gray-300 w-full p-2 mb-2 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
          placeholder="Route name (e.g., R101 Morning Shift)"
        />

        {/* Shift Time Input */}
        <input
          type="time"
          value={shiftTime}
          onChange={(e) => setShiftTime(e.target.value)}
          disabled={loading}
          className="border border-gray-300 w-full p-2 mb-2 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
        />

        {/* Path Selector */}
        <select
          value={pathId}
          onChange={(e) => setPathId(e.target.value)}
          disabled={loading || paths.length === 0}
          className="border border-gray-300 w-full p-2 mb-2 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
        >
          <option value="placeholder">
            {paths.length === 0 ? "No paths available" : "Select Path"}
          </option>
          {paths.map((path) => (
            <option key={path.path_id} value={path.path_id}>
              {path.path_name} ({path.stop_count || 0} stops)
            </option>
          ))}
        </select>

        {/* Direction Selector */}
        <select
          value={direction}
          onChange={(e) => setDirection(e.target.value)}
          disabled={loading}
          className="border border-gray-300 w-full p-2 mb-4 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
        >
          <option value="UP">⬆️ UP</option>
          <option value="DOWN">⬇️ DOWN</option>
        </select>

        {/* Create Button */}
        <button
          onClick={handleCreate}
          disabled={
            loading ||
            !routeName.trim() ||
            !shiftTime ||
            !pathId ||
            pathId === "placeholder"
          }
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white w-full py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 mt-auto"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Creating...
            </>
          ) : (
            <>✅ Create Route</>
          )}
        </button>
      </div>
    </div>
  );
}
