import { useState } from "react";
import { createStop } from "../api";

export default function StopList({ stops, onRefresh }) {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAdd = async () => {
    if (!name.trim()) {
      setError("Stop name is required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createStop({ name: name.trim() });
      setName("");
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to create stop");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !loading) {
      handleAdd();
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 pb-3 border-b">
        <span className="text-2xl">📍</span>
        <div>
          <h2 className="font-semibold text-lg text-gray-800">Stops</h2>
          <p className="text-xs text-gray-500">{stops.length} locations</p>
        </div>
      </div>

      {/* Stop List */}
      <div className="flex-1 mb-3 overflow-y-auto">
        {stops.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p className="text-sm">No stops yet</p>
            <p className="text-xs mt-1">Add your first pickup/drop point</p>
          </div>
        ) : (
          <ul className="space-y-1">
            {stops.map((stop, index) => (
              <li
                key={stop.stop_id}
                className="flex items-center justify-between border-b border-gray-100 py-2 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-xs text-gray-400 font-mono w-6">
                    {index + 1}
                  </span>
                  <span className="text-sm text-gray-800">{stop.name}</span>
                </div>
                <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                  Active
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
          ❌ {error}
        </div>
      )}

      {/* Add Stop Form */}
      <div className="space-y-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          className="border border-gray-300 w-full p-2 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
          placeholder="Enter stop name (e.g., Gavipuram Gate)"
        />
        <button
          onClick={handleAdd}
          disabled={loading || !name.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white w-full py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Adding...
            </>
          ) : (
            <>➕ Add Stop</>
          )}
        </button>
      </div>
    </div>
  );
}
