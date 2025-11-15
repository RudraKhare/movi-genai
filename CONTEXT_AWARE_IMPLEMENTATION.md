# Context-Aware Intent Parsing Implementation

## Overview
MOVI now enforces **page context awareness** - the LLM produces different actions based on `currentPage`, ensuring users can only perform actions appropriate to their current UI context.

---

## Implementation Details

### 1. Updated LLM Schema
**File**: `langgraph/tools/llm_client.py`

**Added**:
- New action: `context_mismatch`
- Context-aware rules in SYSTEM_PROMPT
- 4 few-shot examples showing context mismatches
- Enhanced context display in prompts

**Dashboard-Only Actions**:
- `cancel_trip`, `remove_vehicle`, `assign_vehicle`, `update_trip_time`
- `get_trip_status`, `get_trip_details`, `get_unassigned_vehicles`

**ManageRoute-Only Actions**:
- `create_stop`, `create_path`, `create_route`, `rename_stop`, `duplicate_route`
- `list_all_stops`, `list_stops_for_path`, `list_routes_using_path`
- `create_new_route_help`

---

### 2. Added `context_mismatch` Handler
**Files Updated**:
- `check_consequences.py`: Added to SAFE_ACTIONS
- `resolve_target.py`: Added to no_target_actions
- `execute_action.py`: Added handler that returns clear error message

---

## Test Cases

### TEST 1A: Route Creation on Wrong Page
**Request**:
```json
POST /api/agent/message
{
  "text": "Help me create a new route",
  "currentPage": "busDashboard",
  "user_id": 1
}
```

**Expected LLM Response**:
```json
{
  "action": "context_mismatch",
  "confidence": 0.95,
  "explanation": "Route creation is only available on Manage Route page. Please switch to Manage Route."
}
```

**Expected Agent Response**:
```json
{
  "action": "context_mismatch",
  "status": "context_mismatch",
  "message": "Route creation is only available on Manage Route page. Please switch to Manage Route.",
  "success": false
}
```

---

### TEST 1B: Route Creation on Correct Page
**Request**:
```json
{
  "text": "Help me create a new route",
  "currentPage": "manageRoute",
  "user_id": 1
}
```

**Expected LLM Response**:
```json
{
  "action": "create_new_route_help",
  "confidence": 0.98,
  "explanation": "User needs guidance for route creation"
}
```

**Expected Agent Response**:
```json
{
  "action": "create_new_route_help",
  "status": "completed",
  "message": "Here's how to create a new route",
  "final_output": {
    "type": "help",
    "data": {
      "title": "How to Create a New Route",
      "steps": [...]
    }
  }
}
```

---

### TEST 2A: Trip Cancellation on Wrong Page
**Request**:
```json
{
  "text": "Cancel the Bulk - 00:01 trip",
  "currentPage": "manageRoute",
  "user_id": 1
}
```

**Expected**:
- action: `context_mismatch`
- message: "Trip cancellations are only available on Dashboard. Please switch to Dashboard."
- No DB operations attempted

---

### TEST 2B: Trip Cancellation on Correct Page
**Request**:
```json
{
  "text": "Cancel the Bulk - 00:01 trip",
  "currentPage": "busDashboard",
  "user_id": 1
}
```

**Expected**:
- action: `cancel_trip`
- target_label: "Bulk - 00:01"
- resolve_target: Finds trip
- check_consequences: Checks bookings
- needs_confirmation: true (if bookings exist)

---

### TEST 3A: List Stops on Wrong Page
**Request**:
```json
{
  "text": "Show me all stops for Path-2",
  "currentPage": "busDashboard",
  "user_id": 1
}
```

**Expected**:
- action: `context_mismatch`
- message: "Listing stops is a Manage Route action. Switch to Manage Route page."

---

### TEST 3B: List Stops on Correct Page
**Request**:
```json
{
  "text": "Show me all stops for Path-2",
  "currentPage": "manageRoute",
  "user_id": 1
}
```

**Expected**:
- action: `list_stops_for_path`
- target_label: "Path-2"
- Returns: Table of stops

---

### TEST 4A: Remove Vehicle with Context
**Request**:
```json
{
  "text": "Remove vehicle from this trip",
  "currentPage": "busDashboard",
  "selectedTripId": 12,
  "user_id": 1
}
```

**Expected**:
- action: `remove_vehicle`
- trip_id: 12 (from selectedTripId)
- Proceeds with confirmation flow

---

### TEST 4B: Remove Vehicle on Wrong Page
**Request**:
```json
{
  "text": "Remove vehicle from this trip",
  "currentPage": "manageRoute",
  "selectedRouteId": 34,
  "user_id": 1
}
```

**Expected**:
- action: `context_mismatch`
- message: "Vehicle management is only available on Dashboard. Please switch to Dashboard."

---

### TEST 5A: Create Stop on Wrong Page
**Request**:
```json
{
  "text": "Create a new stop called Odeon Circle",
  "currentPage": "busDashboard",
  "user_id": 1
}
```

**Expected**:
- action: `context_mismatch`
- message: "Stop creation is only available on Manage Route page. Please switch to Manage Route."

---

### TEST 5B: Create Stop on Correct Page
**Request**:
```json
{
  "text": "Create a new stop called Odeon Circle",
  "currentPage": "manageRoute",
  "user_id": 1
}
```

**Expected**:
- action: `create_stop`
- parameters: { "stop_name": "Odeon Circle" }
- Executes immediately (SAFE action)
- Returns: ObjectCard with stop details

---

### TEST 6A: Assign Vehicle on Wrong Page
**Request**:
```json
{
  "text": "Assign bus 10 and driver 4 to the 8 AM trip",
  "currentPage": "manageRoute",
  "user_id": 1
}
```

**Expected**:
- action: `context_mismatch`
- message: "Assigning vehicles is only available on Dashboard. Please switch to Dashboard."

---

### TEST 6B: Assign Vehicle on Correct Page
**Request**:
```json
{
  "text": "Assign bus 10 and driver 4 to the 8 AM trip",
  "currentPage": "busDashboard",
  "user_id": 1
}
```

**Expected**:
- action: `assign_vehicle`
- target_time: "08:00"
- parameters: { vehicle_id: 10, driver_id: 4 }
- resolve_target: Maps "8 AM" to trip
- Proceeds with assignment

---

## How It Works

### 1. **LLM Receives Context**
```
=== CURRENT CONTEXT ===
Page: busDashboard
Selected Trip: 5

REMEMBER: Enforce page context rules! Return action='context_mismatch' if user requests wrong-page action.

User: Help me create a new route
```

### 2. **LLM Checks Context Rules**
- Checks if "create route" is allowed on `busDashboard`
- Dashboard-only actions: ❌ No route creation
- Returns: `action="context_mismatch"`

### 3. **Backend Handles Gracefully**
- `resolve_target`: Skips (no_target_actions)
- `check_consequences`: Skips (SAFE_ACTIONS)
- `execute_action`: Returns error message
- `report_result`: Sends to frontend

### 4. **Frontend Displays**
```
❌ Route creation is only available on Manage Route page. Please switch to Manage Route.
```

---

## Benefits

✅ **Better UX**: Clear guidance when user is on wrong page
✅ **Data Integrity**: Prevents accidental cross-context operations
✅ **Assignment Compliance**: Meets "UI Context Awareness" requirement
✅ **Explicit Errors**: No confusing "not found" errors when context is wrong

---

## Status
🟢 **FULLY IMPLEMENTED** - Context-aware intent parsing is now active!

Server will auto-reload. Test with any of the above test cases.
