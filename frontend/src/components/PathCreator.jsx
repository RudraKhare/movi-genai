import { useState } from "react";
import { createPath } from "../api";

export default function PathCreator({ stops, paths, onRefresh }) {
  const [pathName, setPathName] = useState("");
  const [selectedStops, setSelectedStops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 pb-3 border-b">
        <span className="text-2xl">🛣️</span>
        <div>
          <h2 className="font-semibold text-lg text-gray-800">Paths</h2>
          <p className="text-xs text-gray-500">{paths.length} sequences</p>
        </div>
      </div>

      {/* Existing Paths List */}
      <div className="mb-3 max-h-32 overflow-y-auto">
        {paths.length === 0 ? (
          <div className="text-center py-4 text-gray-400">
            <p className="text-xs">No paths yet</p>
          </div>
        ) : (
          <div className="space-y-1">
            {paths.map((path) => (
              <div
                key={path.path_id}
                className="border-b border-gray-100 py-2 hover:bg-gray-50"
              >
                <p className="text-sm font-medium text-gray-800">{path.path_name}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {path.stop_count || 0} stops
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create New Path Form */}
      <div className="flex-1 flex flex-col">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Create New Path</h3>

        {/* Error Message */}
        {error && (
          <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
            ❌ {error}
          </div>
        )}

        {/* Path Name Input */}
        <input
          type="text"
          value={pathName}
          onChange={(e) => setPathName(e.target.value)}
          disabled={loading}
          className="border border-gray-300 w-full p-2 mb-2 text-sm rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:bg-gray-100"
          placeholder="Path name (e.g., Morning Route A)"
        />

        {/* Stop Selector */}
        <select
          onChange={(e) => addStop(e.target.value)}
          disabled={loading || stops.length === 0}
          className="border border-gray-300 w-full p-2 text-sm mb-2 rounded-lg focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
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

        {/* Selected Stops - Ordered List */}
        <div className="flex-1 overflow-y-auto mb-2">
          {selectedStops.length === 0 ? (
            <div className="text-center py-4 text-gray-400 bg-gray-50 rounded-lg">
              <p className="text-xs">Select stops to build path sequence</p>
            </div>
          ) : (
            <ul className="space-y-1">
              {selectedStops.map((stopId, index) => (
                <li
                  key={stopId}
                  className="flex items-center justify-between bg-green-50 border border-green-200 rounded px-2 py-2"
                >
                  <div className="flex items-center gap-2 flex-1">
                    <span className="text-xs font-mono text-green-700 w-6">
                      {index + 1}.
                    </span>
                    <span className="text-sm text-gray-800 flex-1">
                      {getStopName(stopId)}
                    </span>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => moveUp(index)}
                      disabled={index === 0}
                      className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      title="Move up"
                    >
                      ↑
                    </button>
                    <button
                      onClick={() => moveDown(index)}
                      disabled={index === selectedStops.length - 1}
                      className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      title="Move down"
                    >
                      ↓
                    </button>
                    <button
                      onClick={() => removeStop(stopId)}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 border border-red-300 rounded hover:bg-red-200 transition-colors"
                      title="Remove"
                    >
                      ✕
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Create Button */}
        <button
          onClick={handleCreate}
          disabled={loading || !pathName.trim() || selectedStops.length < 2}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white w-full py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Creating...
            </>
          ) : (
            <>✅ Create Path ({selectedStops.length} stops)</>
          )}
        </button>
      </div>
    </div>
  );
}
