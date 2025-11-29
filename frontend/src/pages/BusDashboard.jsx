import { useEffect, useState } from "react";
import Header from "../components/Header";
import TripList from "../components/TripList";
import TripDetail from "../components/TripDetail";
import MoviWidget from "../components/MoviWidget";
import { getDashboard } from "../api";

export default function BusDashboard() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);

  // Enhanced trip selection with context logging
  const handleTripSelect = (trip) => {
    console.log("🔥 [BusDashboard] DEBUGGING TRIP SELECTION:");
    console.log("   Selected trip:", trip);
    console.log("   Trip ID:", trip?.trip_id);
    console.log("   Trip route name:", trip?.route_name);
    
    setSelectedTrip(trip);
    
    // Immediate context verification
    setTimeout(() => {
      console.log("🎯 [BusDashboard] Context being passed to MoviWidget:", {
        currentPage: 'busDashboard',
        selectedTrip: trip,
        selectedTripId: trip?.trip_id
      });
    }, 100);
  };
  
  // Debug context changes
  useEffect(() => {
    console.log('🔍 [BusDashboard] 📊 Selected trip state changed:', {
      trip: selectedTrip,
      tripId: selectedTrip?.trip_id,
      routeName: selectedTrip?.route_name,
      hasSelectedTrip: !!selectedTrip,
      timestamp: new Date().toISOString()
    });
  }, [selectedTrip]);

  // Debug every render to see if context is maintained
  console.log('🔍 [BusDashboard] RENDER - Current state:', {
    selectedTrip: selectedTrip,
    selectedTripId: selectedTrip?.trip_id,
    tripsCount: trips.length,
    loading: loading
  });
  
  const [summary, setSummary] = useState({});

  // Load dashboard data from API
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getDashboard();
      
      console.log("📊 Dashboard API Response:", response.data);
      console.log("🚌 Sample trip data:", response.data.trips?.[0]);
      
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
        {/* Test Button for Debugging Trip Selection */}
        <div className="absolute top-20 left-4 z-50">
          <button 
            onClick={() => {
              const testTrip = trips[0]; // First trip from the list
              console.log("🧪 [TEST] Simulating trip selection with:", testTrip);
              handleTripSelect(testTrip);
            }}
            className="bg-red-500 text-white px-3 py-1 rounded text-sm"
            disabled={trips.length === 0}
          >
            🧪 Test Select Trip {trips.length > 0 ? trips[0]?.trip_id : ''}
          </button>
        </div>

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
              onSelect={handleTripSelect}
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
      <MoviWidget 
        context={(() => {
          const contextObj = {
            currentPage: "busDashboard", 
            selectedTrip: selectedTrip,
            selectedTripId: selectedTrip?.trip_id
          };
          console.log("🚀 [BusDashboard] Rendering MoviWidget with context:", contextObj);
          return contextObj;
        })()} 
        onRefresh={loadData}
      />
    </div>
  );
}
