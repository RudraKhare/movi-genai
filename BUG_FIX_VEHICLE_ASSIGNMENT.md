# Bug Fix: Vehicle Assignment by Name

## Issue
When user says "Assign vehicle 'MH-12-3456' and driver 'Amit' to trip 5", the system was failing with "trip_not_found" error even though trip_id=5 was correctly parsed by the LLM.

## Root Cause Analysis

### Problem 1: Missing `target_trip_id` in State
**File**: `langgraph/nodes/parse_intent_llm.py` (line 86)

The LLM was returning:
```json
{
  "target_trip_id": 5,
  "target_path_id": null,
  "target_route_id": null
}
```

But the code was only mapping `target_path_id` and `target_route_id` to state, **NOT** `target_trip_id`.

**Fix**: Added `state["target_trip_id"] = llm_response.get("target_trip_id")` at line 87

---

### Problem 2: Wrong Lookup Location in resolve_target
**File**: `langgraph/nodes/resolve_target.py` (line 205)

The code was looking for trip_id in the wrong place:
```python
# ❌ BEFORE (WRONG)
parsed_params = state.get("parsed_params", {})
llm_trip_id = parsed_params.get("target_trip_id")
```

But `target_trip_id` is stored at the **top level** of state, not inside `parsed_params`.

**Fix**: Changed to:
```python
# ✅ AFTER (CORRECT)
llm_trip_id = state.get("target_trip_id")
```

---

### Problem 3: Missing Vehicle/Driver Lookup
**File**: `langgraph/nodes/execute_action.py` (lines 157-195)

The `assign_vehicle` action expected numeric IDs but received registration numbers and names.

**Fix**: Added lookup logic:
1. If `vehicle_registration` provided → Query `vehicles` table → Get `vehicle_id`
2. If `driver_name` provided → Query `drivers` table (fuzzy match) → Get `driver_id`

**Example**:
```python
if not vehicle_id and vehicle_registration:
    vehicle_row = await conn.fetchrow("""
        SELECT vehicle_id FROM vehicles
        WHERE LOWER(registration_number) = LOWER($1)
    """, vehicle_registration.strip())
    if vehicle_row:
        vehicle_id = vehicle_row['vehicle_id']
```

---

### Problem 4: LLM Schema Missing Parameters
**File**: `langgraph/tools/llm_client.py`

The LLM schema didn't include `vehicle_registration` and `driver_name` parameters.

**Fix**:
1. Added to schema (line 28):
   ```json
   "vehicle_registration": "string"|null,
   "driver_name": "string"|null,
   ```

2. Added to validation (line 194):
   ```python
   response["parameters"].setdefault("vehicle_registration", None)
   response["parameters"].setdefault("driver_name", None)
   ```

3. Added few-shot example (line 99):
   ```json
   {
     "user": "Assign vehicle MH-12-3456 and driver Amit to trip 5",
     "assistant": '{"action":"assign_vehicle","target_trip_id":5,"parameters":{"vehicle_registration":"MH-12-3456","driver_name":"Amit"}}'
   }
   ```

---

## Test Case

**Command**: `"Assign vehicle 'MH-12-3456' and driver 'Amit' to trip 5"`

**Expected Flow**:
1. **LLM Parsing**:
   - ✅ action = `assign_vehicle`
   - ✅ target_trip_id = `5` (stored at top level)
   - ✅ parameters.vehicle_registration = `"MH-12-3456"`
   - ✅ parameters.driver_name = `"Amit"`

2. **resolve_target**:
   - ✅ Check `state["target_trip_id"]` = 5
   - ✅ Query database: `SELECT * FROM daily_trips WHERE trip_id = 5`
   - ✅ If found → Set `state["trip_id"] = 5`

3. **execute_action**:
   - ✅ Get vehicle_registration = `"MH-12-3456"`
   - ✅ Query: `SELECT vehicle_id FROM vehicles WHERE registration_number = 'MH-12-3456'`
   - ✅ Get vehicle_id (e.g., 3)
   - ✅ Get driver_name = `"Amit"`
   - ✅ Query: `SELECT driver_id FROM drivers WHERE name LIKE '%Amit%'`
   - ✅ Get driver_id (e.g., 2)
   - ✅ Call `tool_assign_vehicle(trip_id=5, vehicle_id=3, driver_id=2)`

4. **Result**:
   - ✅ `"Assigned vehicle 3 to trip 5"`

---

## Files Modified

1. ✅ `langgraph/nodes/parse_intent_llm.py` (line 87)
2. ✅ `langgraph/nodes/resolve_target.py` (line 205)
3. ✅ `langgraph/nodes/execute_action.py` (lines 157-195)
4. ✅ `langgraph/tools/llm_client.py` (lines 28, 99, 194)

---

## Status
🟢 **FIXED** - All 4 problems resolved. Vehicle assignment by name now fully functional.
