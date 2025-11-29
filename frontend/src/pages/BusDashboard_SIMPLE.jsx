import React, { useState, useEffect } from "react";
import TripList from "../components/TripList";
import TripDetail from "../components/TripDetail";
import VehicleSummary from "../components/VehicleSummary";
import MoviWidget from "../components/MoviWidget";
import { getDashboard } from "../api";

export default function BusDashboard() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [summary, setSummary] = useState({});

  // Load dashboard data from API
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getDashboard();
      
      console.log("📊 Dashboard API Response:", response.data);
      
      const { trips: tripData, summary: summaryData } = response.data;
      setTrips(tripData || []);
      setSummary(summaryData || {});
      
      // Preserve selected trip if it still exists
      if (selectedTrip) {
        const updatedTrip = tripData?.find(t => t.trip_id === selectedTrip.trip_id);
        if (updatedTrip) {
          setSelectedTrip(updatedTrip);
        }
      }
    } catch (err) {
      console.error("❌ Failed to load dashboard data:", err);
      setError(err.message || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">Bus Dashboard</h1>
            <button
              onClick={loadData}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              {loading ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Summary Cards */}
        <VehicleSummary 
          summary={summary} 
          onRefresh={loadData}
        />
        
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h2 className="text-xl font-semibold mb-4">Trips</h2>
            {error ? (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Error loading trips
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                    <button
                      onClick={loadData}
                      className="mt-2 bg-red-100 hover:bg-red-200 text-red-800 font-semibold py-1 px-3 rounded text-sm"
                    >
                      Try Again
                    </button>
                  </div>
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

          <div>
            <h2 className="text-xl font-semibold mb-4">Details</h2>
            {selectedTrip ? (
              <TripDetail trip={selectedTrip} onRefresh={loadData} />
            ) : (
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500">Select a trip to view details</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Simplified MoviWidget without complex context */}
      <MoviWidget 
        context={{ 
          currentPage: "busDashboard", 
          selectedTrip: selectedTrip,
          selectedTripId: selectedTrip?.trip_id
        }} 
        onRefresh={loadData}
      />
    </div>
  );
}
