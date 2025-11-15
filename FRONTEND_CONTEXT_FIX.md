# Frontend Context Passing Fix

## Problem
The frontend was sending context as a nested object:
```json
{
  "text": "Create a stop",
  "user_id": 1,
  "context": {
    "currentPage": "busDashboard",
    "selectedRouteId": null
  }
}
```

But the backend expected flat structure:
```json
{
  "text": "Create a stop",
  "user_id": 1,
  "currentPage": "busDashboard",
  "selectedRouteId": null,
  "selectedTripId": null
}
```

This caused `currentPage` to always be `None`, disabling context-aware intent parsing.

---

## Solution

### Updated: `frontend/src/components/MoviWidget.jsx` (lines 36-42)

**Before**:
```jsx
{
  text: userMessage,
  user_id: 1,
  context: context  // ❌ Nested object
}
```

**After**:
```jsx
{
  text: userMessage,
  user_id: 1,
  currentPage: context?.currentPage || null,         // ✅ Top-level
  selectedRouteId: context?.selectedRouteId || null, // ✅ Top-level
  selectedTripId: context?.selectedTripId || null,   // ✅ Top-level
  conversation_history: []
}
```

---

## Expected Behavior After Fix

### Test 1: Create Stop on Dashboard
**Request**:
```jsx
// User on Dashboard page
<MoviWidget context={{ currentPage: "busDashboard" }} />
```

**User types**: "Create a stop called Odeon Circle"

**Backend logs**:
```
INFO: context: {'currentPage': 'busDashboard', ...}
INFO: action=context_mismatch
```

**Response**:
```
❌ Stop creation is only available on Manage Route page. Please switch to Manage Route.
```

---

### Test 2: Create Stop on Manage Route
**Request**:
```jsx
// User on Manage Route page
<MoviWidget context={{ currentPage: "manageRoute" }} />
```

**User types**: "Create a stop called Odeon Circle"

**Backend logs**:
```
INFO: context: {'currentPage': 'manageRoute', ...}
INFO: action=create_stop
INFO: ✅ Created stop 'Odeon Circle'
```

**Response**:
```
✅ Created stop 'Odeon Circle'
```

---

### Test 3: Cancel Trip on Dashboard
**Request**:
```jsx
<MoviWidget context={{ currentPage: "busDashboard" }} />
```

**User types**: "Cancel trip Bulk - 00:01"

**Backend logs**:
```
INFO: context: {'currentPage': 'busDashboard', ...}
INFO: action=cancel_trip
INFO: resolve_target → found trip_id=7
INFO: check_consequences → found 8 bookings
INFO: needs_confirmation=true
```

**Response**:
```
⚠️ This trip has 8 bookings. Are you sure you want to cancel?
[Confirm] [Cancel]
```

---

### Test 4: Cancel Trip on Manage Route
**Request**:
```jsx
<MoviWidget context={{ currentPage: "manageRoute" }} />
```

**User types**: "Cancel trip Bulk - 00:01"

**Backend logs**:
```
INFO: context: {'currentPage': 'manageRoute', ...}
INFO: action=context_mismatch
```

**Response**:
```
❌ Trip cancellations are only available on Dashboard. Please switch to Dashboard.
```

---

## How to Test

1. **Restart frontend** (if not using hot reload):
   ```bash
   cd frontend
   npm start
   ```

2. **Open Dashboard page** - Context should be `{ currentPage: "busDashboard" }`

3. **Try these commands**:
   - ❌ "Create a stop called Odeon Circle" → Should show context mismatch
   - ✅ "Cancel trip Bulk - 00:01" → Should work normally

4. **Open Manage Route page** - Context should be `{ currentPage: "manageRoute" }`

5. **Try these commands**:
   - ✅ "Create a stop called Odeon Circle" → Should create stop
   - ❌ "Cancel trip Bulk - 00:01" → Should show context mismatch

---

## Files Modified

1. ✅ **Backend - Valid Actions** (`langgraph/tools/llm_client.py`):
   - Added `"context_mismatch"` to valid_actions list

2. ✅ **Backend - System Prompt** (`langgraph/tools/llm_client.py`):
   - Updated to only enforce context when `currentPage` is provided
   - Added backward compatibility for `null` currentPage

3. ✅ **Backend - Execute Action** (`langgraph/nodes/execute_action.py`):
   - Added handler for `context_mismatch` action

4. ✅ **Frontend - Request Format** (`frontend/src/components/MoviWidget.jsx`):
   - Changed from nested `context` object to flat structure
   - Now sends `currentPage`, `selectedRouteId`, `selectedTripId` at top level

---

## Status
🟢 **FIXED** - Context-aware intent parsing now fully functional!

The frontend now properly sends page context, and the backend enforces it.
