import { useState } from "react";
import { createPath } from "../api";

export default function PathCreator({ stops, paths, onRefresh }) {
  const [pathName, setPathName] = useState("");
  const [selectedStops, setSelectedStops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedPath, setExpandedPath] = useState(null);

  const addStop = (stopId) => {
    if (!stopId || stopId === "placeholder") return;
    if (!selectedStops.includes(parseInt(stopId))) {
      setSelectedStops([...selectedStops, parseInt(stopId)]);
    }
  };

  const removeStop = (stopId) => {
    setSelectedStops(selectedStops.filter((id) => id !== stopId));
  };
  
  const moveUp = (index) => {
    if (index === 0) return;
    const reordered = [...selectedStops];
    [reordered[index - 1], reordered[index]] = [reordered[index], reordered[index - 1]];
    setSelectedStops(reordered);
  };

  const moveDown = (index) => {
    if (index === selectedStops.length - 1) return;
    const reordered = [...selectedStops];
    [reordered[index], reordered[index + 1]] = [reordered[index + 1], reordered[index]];
    setSelectedStops(reordered);
  };

  const handleCreate = async () => {
    if (!pathName.trim()) {
      setError("Path name is required");
      return;
    }
    if (selectedStops.length < 2) {
      setError("Path must have at least 2 stops");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createPath({
        path_name: pathName.trim(),
        stop_ids: selectedStops,
      });
      setPathName("");
      setSelectedStops([]);
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to create path");
    } finally {
      setLoading(false);
    }
  };

  const getStopName = (stopId) => {
    return stops.find((s) => s.stop_id === stopId)?.name || `Stop #${stopId}`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-[600px]">
      {/* Header - Orange/Amber */}
      <div className="bg-amber-500 text-white px-5 py-4 rounded-t-xl">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🛣️</span>
          <div>
            <h2 className="font-bold text-xl">Paths</h2>
            <p className="text-sm text-amber-100">{paths.length} sequences</p>
          </div>
        </div>
      </div>

      {/* Existing Paths List - Scrollable */}
      <div className="flex-1 overflow-y-auto px-4 py-3 border-b border-gray-100">
        {paths.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <span className="text-4xl block mb-3">🛣️</span>
            <p className="text-sm">No paths yet</p>
            <p className="text-xs mt-1">Create your first path below</p>
          </div>
        ) : (
          <div className="space-y-2">
            {paths.map((path) => {
              const pathStops = path.stops || [];
              const startPoint = pathStops[0]?.stop_name || "N/A";
              const endPoint = pathStops[pathStops.length - 1]?.stop_name || "N/A";
              const isExpanded = expandedPath === path.path_id;
              
              return (
                <div
                  key={path.path_id}
                  className={`border rounded-lg overflow-hidden transition-all ${
                    isExpanded ? 'border-amber-300 bg-amber-50' : 'border-gray-200 bg-white'
                  }`}
                >
                  {/* Clickable Header */}
                  <div 
                    className="flex items-center justify-between p-3 cursor-pointer hover:bg-amber-50 transition-colors"
                    onClick={() => setExpandedPath(isExpanded ? null : path.path_id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-amber-500 text-white rounded-lg flex items-center justify-center text-sm font-bold">
                        P{path.path_id}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-800">{path.path_name}</p>
                        <p className="text-xs text-gray-500">
                          {startPoint} → {endPoint} • {pathStops.length} stops
                        </p>
                      </div>
                    </div>
                    <span className={`text-amber-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </div>
                  
                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="border-t border-amber-200 bg-white p-3">
                      {/* Path Info Grid */}
                      <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                        <div className="bg-gray-50 p-2 rounded">
                          <span className="text-gray-500">Path ID:</span>
                          <span className="ml-1 font-medium text-gray-700">#{path.path_id}</span>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <span className="text-gray-500">Total Stops:</span>
                          <span className="ml-1 font-medium text-gray-700">{pathStops.length}</span>
                        </div>
                      </div>
                      
                      {/* Start Point */}
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs">🚀</span>
                        <div>
                          <p className="text-[10px] text-gray-400 uppercase">Starting Point</p>
                          <p className="text-sm font-medium text-green-700">{startPoint}</p>
                        </div>
                      </div>
                      
                      {/* Stops Flow */}
                      {pathStops.length > 2 && (
                        <div className="ml-3 pl-3 border-l-2 border-dashed border-gray-300 my-2">
                          <p className="text-[10px] text-gray-400 uppercase mb-1">Stops in Sequence</p>
                          <div className="space-y-1">
                            {pathStops.slice(1, -1).map((stop, idx) => (
                              <div key={idx} className="flex items-center gap-2 text-xs text-gray-600">
                                <span className="w-5 h-5 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center text-[10px] font-medium">
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
                          <p className="text-[10px] text-gray-400 uppercase">Ending Point</p>
                          <p className="text-sm font-medium text-red-700">{endPoint}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create New Path Form - Fixed at bottom */}
      <div className="p-5 bg-gray-50 rounded-b-xl">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Create New Path</h3>

        {/* Error Message */}
        {error && (
          <div className="mb-3 p-2.5 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            ❌ {error}
          </div>
        )}

        {/* Path Name Input */}
        <input
          type="text"
          value={pathName}
          onChange={(e) => setPathName(e.target.value)}
          disabled={loading}
          className="border border-gray-300 w-full p-2.5 mb-3 text-sm rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:bg-gray-100"
          placeholder="Path name (e.g., Morning Route A)"
        />

        {/* Stop Selector */}
        <select
          onChange={(e) => addStop(e.target.value)}
          disabled={loading || stops.length === 0}
          className="border border-gray-300 w-full p-2.5 text-sm mb-3 rounded-lg focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
          value="placeholder"
        >
          <option value="placeholder">
            {stops.length === 0 ? "No stops available" : "➕ Add Stop to Path"}
          </option>
          {stops.map((stop) => (
            <option
              key={stop.stop_id}
              value={stop.stop_id}
              disabled={selectedStops.includes(stop.stop_id)}
            >
              {stop.name} {selectedStops.includes(stop.stop_id) && "✓"}
            </option>
          ))}
        </select>

        {/* Selected Stops Preview */}
        {selectedStops.length > 0 ? (
          <div className="mb-3 p-3 bg-white border border-gray-200 rounded-lg max-h-32 overflow-y-auto">
            <div className="space-y-1.5">
              {selectedStops.map((stopId, index) => (
                <div
                  key={stopId}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-xs font-medium">
                      {index + 1}
                    </span>
                    <span className="text-gray-700">{getStopName(stopId)}</span>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => moveUp(index)}
                      disabled={index === 0}
                      className="w-6 h-6 text-xs bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-30"
                    >↑</button>
                    <button
                      onClick={() => moveDown(index)}
                      disabled={index === selectedStops.length - 1}
                      className="w-6 h-6 text-xs bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-30"
                    >↓</button>
                    <button
                      onClick={() => removeStop(stopId)}
                      className="w-6 h-6 text-xs bg-red-100 text-red-600 hover:bg-red-200 rounded"
                    >✕</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="mb-3 p-3 bg-white border border-dashed border-gray-300 rounded-lg text-center">
            <p className="text-xs text-gray-400">Select stops to build path sequence</p>
          </div>
        )}

        {/* Create Button */}
        <button
          onClick={handleCreate}
          disabled={loading || !pathName.trim() || selectedStops.length < 2}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white w-full py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              Creating...
            </>
          ) : (
            <>✅ Create Path</>
          )}
        </button>
      </div>
    </div>
  );
}
