// CONTEXT DEBUGGING TEST
// Open browser console (F12) and run this to test context flow

// Test 1: Check current selectedTrip state
console.log("🧪 TEST 1: Current selectedTrip state");
console.log("selectedTrip in BusDashboard:", window.selectedTrip);

// Test 2: Manually trigger trip selection  
console.log("\n🧪 TEST 2: Manual trip selection test");
const testTrip = {
  trip_id: 38,
  route_name: "GIV - PATH",
  live_status: "SCHEDULED"
};

// Simulate trip selection
console.log("Simulating trip selection with:", testTrip);

// Test 3: Check localStorage for persisted context
console.log("\n🧪 TEST 3: Check localStorage context");
const stored = localStorage.getItem('moviWidget_lastContext');
if (stored) {
  try {
    const parsed = JSON.parse(stored);
    console.log("Stored context:", parsed);
    console.log("Is recent?", (Date.now() - parsed.timestamp) < 3600000);
  } catch (e) {
    console.log("Failed to parse stored context:", e);
  }
} else {
  console.log("No stored context found");
}

// Test 4: Check if MoviWidget component is receiving context
console.log("\n🧪 TEST 4: MoviWidget context check");
console.log("Look for these logs when you select a trip and send a message:");
console.log("- '🔥 [MoviWidget] DEBUGGING CONTEXT ISSUE'");
console.log("- '📤 [MoviWidget] PAYLOAD BEING SENT TO BACKEND'");
console.log("- '🚀 [BusDashboard] Rendering MoviWidget with context'");

console.log("\n✅ Context debugging test completed. Now:");
console.log("1. Select a trip from the list");
console.log("2. Type 'assign vehicle to this trip' in MoviWidget");
console.log("3. Check console logs above and below this message");
console.log("4. Look for selectedTripId in the payload logs");

export {};
