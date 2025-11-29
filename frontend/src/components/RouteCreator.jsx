import { useState } from "react";
import { createRoute } from "../api";

export default function RouteCreator({ paths, routes, onRefresh }) {
  const [routeName, setRouteName] = useState("");
  const [shiftTime, setShiftTime] = useState("");
  const [pathId, setPathId] = useState("");
  const [direction, setDirection] = useState("UP");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedRoute, setExpandedRoute] = useState(null);

  // Helper to get path details by path_id
  const getPathDetails = (pathId) => {
    return paths.find(p => p.path_id === pathId) || null;
  };

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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-[600px]">
      {/* Header - Teal/Cyan */}
      <div className="bg-teal-500 text-white px-5 py-4 rounded-t-xl">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🚌</span>
          <div>
            <h2 className="font-bold text-xl">Routes</h2>
            <p className="text-sm text-teal-100">{routes.length} scheduled routes</p>
          </div>
        </div>
      </div>

      {/* Existing Routes List - Scrollable */}
      <div className="flex-1 overflow-y-auto px-4 py-3 min-h-0">
        {routes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <span className="text-4xl mb-2">🚌</span>
            <p className="text-sm">No routes yet</p>
            <p className="text-xs">Create your first route below</p>
          </div>
        ) : (
          <div className="space-y-2">
            {routes.map((route) => {
              const isExpanded = expandedRoute === route.route_id;
              const pathDetails = getPathDetails(route.path_id);
              const pathStops = pathDetails?.stops || [];
              const startPoint = pathStops[0]?.stop_name || "N/A";
              const endPoint = pathStops[pathStops.length - 1]?.stop_name || "N/A";
              
              return (
                <div
                  key={route.route_id}
                  className={`border rounded-lg overflow-hidden transition-all ${
                    isExpanded ? 'border-teal-300 bg-teal-50' : 'border-gray-200 bg-white'
                  }`}
                >
                  {/* Clickable Header */}
                  <div 
                    className="flex items-center justify-between p-3 cursor-pointer hover:bg-teal-50 transition-colors"
                    onClick={() => setExpandedRoute(isExpanded ? null : route.route_id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-teal-500 text-white rounded-lg flex items-center justify-center text-sm font-bold">
                        R{route.route_id}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-800">{route.route_name}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs px-1.5 py-0.5 bg-teal-100 text-teal-700 rounded">
                            {route.shift_time?.substring(0, 5) || "N/A"}
                          </span>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            route.direction === 'UP' 
                              ? 'bg-blue-100 text-blue-600' 
                              : 'bg-orange-100 text-orange-600'
                          }`}>
                            {route.direction === 'UP' ? '⬆️' : '⬇️'} {route.direction}
                          </span>
                        </div>
                      </div>
                    </div>
                    <span className={`text-teal-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </div>
                  
                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="border-t border-teal-200 bg-white p-3">
                      {/* Route Info Grid */}
                      <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                        <div className="bg-gray-50 p-2 rounded">
                          <span className="text-gray-500">Route ID:</span>
                          <span className="ml-1 font-medium text-gray-700">#{route.route_id}</span>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <span className="text-gray-500">Path:</span>
                          <span className="ml-1 font-medium text-gray-700">{route.path_name || `Path #${route.path_id}`}</span>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <span className="text-gray-500">Shift Time:</span>
                          <span className="ml-1 font-medium text-teal-700">{route.shift_time || "N/A"}</span>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <span className="text-gray-500">Direction:</span>
                          <span className={`ml-1 font-medium ${route.direction === 'UP' ? 'text-blue-600' : 'text-orange-600'}`}>
                            {route.direction === 'UP' ? '⬆️ UP' : '⬇️ DOWN'}
                          </span>
                        </div>
                      </div>
                      
                      {/* Start Point */}
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs">🚀</span>
                        <div>
                          <p className="text-[10px] text-gray-400 uppercase">Start Point</p>
                          <p className="text-sm font-medium text-green-700">{startPoint}</p>
                        </div>
                      </div>
                      
                      {/* Stops Flow */}
                      {pathStops.length > 2 && (
                        <div className="ml-3 pl-3 border-l-2 border-dashed border-gray-300 my-2">
                          <p className="text-[10px] text-gray-400 uppercase mb-1">Stops in Between</p>
                          <div className="space-y-1">
                            {pathStops.slice(1, -1).map((stop, idx) => (
                              <div key={idx} className="flex items-center gap-2 text-xs text-gray-600">
                                <span className="w-5 h-5 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center text-[10px] font-medium">
                                  {idx + 2}
                                </span>
                                {stop.stop_name}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* End Point */}
                      <div className="flex items-center gap-2 mt-2">
                        <span className="w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs">🏁</span>
                        <div>
                          <p className="text-[10px] text-gray-400 uppercase">End Point</p>
                          <p className="text-sm font-medium text-red-700">{endPoint}</p>
                        </div>
                      </div>
                      
                      {/* Total Stops Badge */}
                      <div className="mt-3 pt-2 border-t border-gray-100">
                        <span className="text-xs bg-teal-100 text-teal-700 px-2 py-1 rounded-full">
                          📍 {pathStops.length} stops total
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create New Route Form - Fixed at Bottom */}
      <div className="border-t border-gray-200 p-4 bg-gray-50 rounded-b-xl">
        <h3 className="text-sm font-medium text-gray-700 mb-3">➕ Create New Route</h3>

        {/* Error Message */}
        {error && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            ❌ {error}
          </div>
        )}

        {/* Route Name Input */}
        <input
          type="text"
          value={routeName}
          onChange={(e) => setRouteName(e.target.value)}
          disabled={loading}
          className="border border-gray-300 w-full p-2.5 mb-2 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
          placeholder="Route name (e.g., R101 Morning)"
        />

        {/* Shift Time Input */}
        <input
          type="time"
          value={shiftTime}
          onChange={(e) => setShiftTime(e.target.value)}
          disabled={loading}
          className="border border-gray-300 w-full p-2.5 mb-2 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
        />

        {/* Path Selector */}
        <select
          value={pathId}
          onChange={(e) => setPathId(e.target.value)}
          disabled={loading || paths.length === 0}
          className="border border-gray-300 w-full p-2.5 mb-2 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
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
          className="border border-gray-300 w-full p-2.5 mb-3 text-sm rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
        >
          <option value="UP">⬆️ UP (Morning)</option>
          <option value="DOWN">⬇️ DOWN (Evening)</option>
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
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white w-full py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
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
