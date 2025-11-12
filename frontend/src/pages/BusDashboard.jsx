import { useEffect, useState } from "react";
import Header from "../components/Header";
import TripList from "../components/TripList";
import TripDetail from "../components/TripDetail";
import MoviWidget from "../components/MoviWidget";
import { getDashboard } from "../api";

export default function BusDashboard() {
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load dashboard data from API
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getDashboard();
      
      setTrips(response.data.trips || []);
      setSummary(response.data.summary || {});
      
      // If a trip was selected, update it with fresh data
      if (selectedTrip) {
        const updatedTrip = response.data.trips.find(t => t.trip_id === selectedTrip.trip_id);
        if (updatedTrip) {
          setSelectedTrip(updatedTrip);
        }
      }
    } catch (err) {
      console.error("Error loading dashboard:", err);
      setError(err.response?.data?.error || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with navigation and summary */}
      <Header onRefresh={loadData} summary={summary} />

      {/* Main content area */}
      <div className="flex h-[calc(100vh-140px)]">
        {/* Left sidebar - Trip List */}
        <div className="w-96 bg-white border-r border-gray-200 overflow-y-auto">
          {loading && trips.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin text-4xl mb-2">⏳</div>
                <p className="text-gray-600">Loading trips...</p>
              </div>
            </div>
          ) : error ? (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 font-medium">❌ Error</p>
                <p className="text-red-600 text-sm mt-1">{error}</p>
                <button
                  onClick={loadData}
                  className="mt-3 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                >
                  Try Again
                </button>
              </div>
            </div>
          ) : (
            <TripList
              trips={trips}
              onSelect={setSelectedTrip}
              selected={selectedTrip}
            />
          )}
        </div>

        {/* Main content - Trip Detail */}
        <div className="flex-1 overflow-y-auto">
          {selectedTrip ? (
            <TripDetail trip={selectedTrip} onRefresh={loadData} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <div className="text-6xl mb-4">🚌</div>
                <p className="text-xl font-medium">Select a trip to view details</p>
                <p className="text-sm mt-2">
                  Click on any trip from the list on the left
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Floating Movi Widget */}
      <MoviWidget context={{ page: "busDashboard", selectedTrip }} />
    </div>
  );
}
