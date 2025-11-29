# Context Debugging Checklist

## Step-by-Step Debugging Guide

### 1. Test Trip Selection
- Open browser console (F12)
- Go to http://localhost:5173
- Click on ANY trip in the trip list
- Look for these logs:
  ```
  [BusDashboard] 🎯 Trip selected: {trip_id: XX, route_name: "..."}
  [BusDashboard] 📊 Selected trip state changed: {...}
  [BusDashboard] ✅ Context should be updated to: {...}
  ```

### 2. Test MoviWidget Context Reception
- After selecting a trip, look for:
  ```
  [MoviWidget] ✅ Context updated and persisted: {selectedTripId: XX}
  ```

### 3. Test Message Sending
- Type "assign vehicle to this trip" in MoviWidget
- Look for these logs:
  ```
  [MoviWidget] 🎯 Effective context used: {...}
  [MoviWidget] ✅ Context reference detected and resolved: XX
  [MoviWidget] 📤 Final payload: {selectedTripId: XX, ...}
  ```

### 4. Check Backend Reception
- Backend should log:
  ```
  Received request data: AgentMessageRequest(selectedTripId=XX, currentPage='busDashboard', ...)
  [CONTEXT] Complete context received: selectedTripId=XX, ui_context={...}
  [CONTEXT] Found context reference with selectedTripId=XX
  ```

## Possible Issues & Solutions:

### Issue 1: No trip selection logs
**Problem**: User didn't actually select a trip
**Solution**: Click on a trip in the list first

### Issue 2: Context not persisted
**Problem**: MoviWidget not receiving context
**Solution**: Check BusDashboard → MoviWidget prop passing

### Issue 3: Payload missing data
**Problem**: API request doesn't include selectedTripId
**Solution**: Check MoviWidget handleSendMessage function

### Issue 4: Backend not parsing
**Problem**: Backend receives data but can't parse it
**Solution**: Check AgentMessageRequest model structure

## Expected Successful Flow:
1. User selects Trip 38 → `[BusDashboard] Trip selected: {trip_id: 38}`
2. Context updates → `[MoviWidget] Context updated: {selectedTripId: 38}`
3. User types "assign vehicle to this trip" → `[MoviWidget] Context detected: 38`
4. Backend receives → `selectedTripId=38, action=assign_vehicle, confidence=0.95`
5. System responds → "Available vehicles for trip 38: [...]"

## Quick Fix Test:
If context isn't working, try explicit command:
- Type: "assign vehicle to trip 38"
- This should work regardless of context issues
- If this fails, the problem is elsewhere
