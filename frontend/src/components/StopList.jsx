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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-[600px]">
      {/* Header - Blue */}
      <div className="bg-blue-500 text-white px-5 py-4 rounded-t-xl">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📍</span>
          <div>
            <h2 className="font-bold text-xl">Stops</h2>
            <p className="text-sm text-blue-100">{stops.length} locations</p>
          </div>
        </div>
      </div>

      {/* Stop List - Scrollable */}
      <div className="flex-1 overflow-y-auto px-5 py-3">
        {stops.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <span className="text-4xl block mb-3">📍</span>
            <p className="text-sm">No stops yet</p>
            <p className="text-xs mt-1">Add your first pickup/drop point</p>
          </div>
        ) : (
          <div className="space-y-0">
            {stops.map((stop, index) => (
              <div
                key={stop.stop_id}
                className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors -mx-2 px-2 rounded"
              >
                <div className="flex items-center gap-3 flex-1">
                  <span className="text-sm text-gray-400 font-medium w-6">
                    {index + 1}
                  </span>
                  <span className="text-sm font-medium text-gray-800">{stop.name}</span>
                </div>
                <span className="text-xs font-medium text-green-600 bg-green-50 px-2.5 py-1 rounded-full">
                  Active
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Stop Form - Fixed at bottom */}
      <div className="p-5 border-t border-gray-100 bg-gray-50 rounded-b-xl">
        {/* Error Message */}
        {error && (
          <div className="mb-3 p-2.5 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            ❌ {error}
          </div>
        )}
        
        <div className="flex gap-2">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            className="flex-1 border border-gray-300 p-2.5 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            placeholder="Enter new stop name..."
          />
          <button
            onClick={handleAdd}
            disabled={loading || !name.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 whitespace-nowrap"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            ) : (
              <>➕ Add</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
