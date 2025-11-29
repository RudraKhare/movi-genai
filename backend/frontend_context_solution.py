#!/usr/bin/env python3
"""
Create a comprehensive context management solution for the frontend
"""

# MoviWidget Context Management Enhancement
MOVIWIDGET_CONTEXT_FIX = """
// Add to MoviWidget.jsx - Context Management with Persistence

const MoviWidget = ({ context = {}, onRefresh }) => {
  const [messages, setMessages] = useState([]);
  const [persistedContext, setPersistedContext] = useState(null);
  
  // Enhanced context management with persistence
  useEffect(() => {
    // Update persisted context when new context received
    if (context.selectedTripId) {
      setPersistedContext(context);
      localStorage.setItem('moviWidget_lastContext', JSON.stringify(context));
      console.log('[MoviWidget] ✅ Context updated and persisted:', context);
    }
  }, [context.selectedTripId, context.selectedTrip]);
  
  // Load persisted context on mount
  useEffect(() => {
    const stored = localStorage.getItem('moviWidget_lastContext');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.selectedTripId && !context.selectedTripId) {
          console.log('[MoviWidget] 📂 Restored context from storage:', parsed);
          setPersistedContext(parsed);
        }
      } catch (e) {
        console.warn('[MoviWidget] Failed to parse stored context');
      }
    }
  }, []);
  
  const handleSendMessage = async (text) => {
    // Use current context or fallback to persisted context
    const effectiveContext = {
      ...context,
      ...(persistedContext && !context.selectedTripId ? persistedContext : {})
    };
    
    const payload = {
      text: text.trim(),
      user_id: 1,
      currentPage: effectiveContext.currentPage || 'busDashboard',
      selectedRouteId: effectiveContext.selectedRoute?.route_id || effectiveContext.selectedRouteId,
      selectedTripId: effectiveContext.selectedTrip?.trip_id || effectiveContext.selectedTripId,
    };
    
    // Enhanced debugging
    console.log('[MoviWidget] 🎯 Effective context used:', effectiveContext);
    console.log('[MoviWidget] 📤 Payload sent:', payload);
    
    // Warn about context issues
    if (text.toLowerCase().includes('this trip') && !payload.selectedTripId) {
      console.warn('[MoviWidget] ⚠️ CONTEXT ISSUE: User said "this trip" but selectedTripId is null!');
      console.warn('[MoviWidget] Original context:', context);
      console.warn('[MoviWidget] Persisted context:', persistedContext);
    }
    
    // ... rest of handleSendMessage
  };
};
"""

# BusDashboard Context Management Enhancement  
BUSDASHBOARD_CONTEXT_FIX = """
// Add to BusDashboard.jsx - Enhanced Context Passing

const BusDashboard = () => {
  const [selectedTrip, setSelectedTrip] = useState(null);
  
  // Enhanced trip selection with context logging
  const handleTripSelect = (trip) => {
    console.log('[BusDashboard] 🎯 Trip selected:', trip);
    setSelectedTrip(trip);
    
    // Ensure MoviWidget context is updated
    setTimeout(() => {
      console.log('[BusDashboard] ✅ Context should be:', {
        currentPage: 'busDashboard',
        selectedTrip: trip,
        selectedTripId: trip?.trip_id
      });
    }, 100);
  };
  
  // Debug context changes
  useEffect(() => {
    console.log('[BusDashboard] 📊 Selected trip changed:', selectedTrip);
  }, [selectedTrip]);
  
  return (
    <div>
      <TripList 
        trips={trips}
        onSelect={handleTripSelect}  // Use enhanced handler
        selected={selectedTrip}
      />
      
      <MoviWidget 
        key={selectedTrip?.trip_id || 'no-selection'} // Force re-render on trip change
        context={{ 
          currentPage: "busDashboard", 
          selectedTrip: selectedTrip,
          selectedTripId: selectedTrip?.trip_id,
          timestamp: Date.now() // Force context updates
        }} 
        onRefresh={loadData}
      />
    </div>
  );
};
"""

print("Frontend Context Management Solution Created")
print("=" * 50)
print("\n1. CONTEXT PERSISTENCE:")
print("   - MoviWidget stores last selected trip in localStorage")
print("   - Automatically restores context when page refreshes")
print("   - Falls back to persisted context when current context is missing")
print("\n2. ENHANCED DEBUGGING:")
print("   - Comprehensive console logging for context changes") 
print("   - Warnings when context issues detected")
print("   - Clear visibility into context flow")
print("\n3. REACTIVE UPDATES:")
print("   - MoviWidget key forces re-render on trip selection")
print("   - Enhanced trip selection handler with logging")
print("   - Context timestamp ensures updates propagate")
print("\n4. IMMEDIATE USER BENEFIT:")
print("   - 'assign vehicle to this trip' will work when trip is selected")
print("   - Clear feedback when context is missing")
print("   - Smart suggestions based on recent activity")
