# MOVI Agent - 16 Action Testing Guide

## Test Setup

1. **Start Backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Enable LLM Mode:**
   Set `USE_LLM_PARSE=true` in backend `.env` file

4. **Verify Database:**
   Ensure you have test data: trips, vehicles, stops, paths, routes

---

## Test Cases by Category

### 📊 Dynamic READ Actions (3 tests)

#### Test 1: Get Unassigned Vehicles
**Command:** "show me unassigned vehicles" OR "which vehicles are available?"
**Expected:**
- ✅ TableCard with columns: vehicle_id, registration_number, capacity, status
- ✅ Shows only vehicles not assigned to active trips
- ✅ Message: "Found X unassigned vehicles"

**Sample Output:**
```
| vehicle_id | registration_number | capacity | status    |
|------------|---------------------|----------|-----------|
| 5          | KA-01-MN-5678       | 50       | available |
| 7          | KA-01-OP-9012       | 45       | available |
```

---

#### Test 2: Get Trip Status
**Command:** "what's the status of trip 501?" OR "check trip 501"
**Expected:**
- ✅ ObjectCard with trip details
- ✅ Shows: trip_id, live_status, route_name, booking_count, etc.
- ✅ Message: "Trip 501: SCHEDULED"

**Sample Output:**
```
Trip ID: 501
Live Status: SCHEDULED
Route Name: Morning Express
Bookings: 5
Capacity: 50
Booking %: 10%
```

---

#### Test 3: Get Trip Details
**Command:** "get details for trip 501" OR "show me trip 501 details"
**Expected:**
- ✅ ObjectCard with comprehensive data
- ✅ Includes: trip info, route, path, vehicle, driver, bookings array
- ✅ Message: "Details for trip 501"

**Sample Output:**
```
Trip ID: 501
Display Name: Path-1 - 08:00
Route: Morning Express
Path: Downtown Loop
Vehicle: KA-01-AB-1234
Driver: John Doe
Bookings: [
  {booking_id: 1, passenger: "Alice", status: "confirmed"},
  {booking_id: 2, passenger: "Bob", status: "confirmed"}
]
```

---

### 📋 Static READ Actions (3 tests)

#### Test 4: List All Stops
**Command:** "list all stops" OR "show me all stops"
**Expected:**
- ✅ TableCard with columns: stop_id, stop_name, latitude, longitude
- ✅ Stops sorted alphabetically
- ✅ Message: "Found X stops"

**Sample Output:**
```
| stop_id | stop_name    | latitude | longitude |
|---------|--------------|----------|-----------|
| 1       | Airport      | 12.9716  | 77.5946   |
| 2       | City Center  | 12.9352  | 77.6245   |
| 3       | University   | 12.9698  | 77.7499   |
```

---

#### Test 5: List Stops for Path
**Command:** "show stops for path 1" OR "what stops are in path Downtown?"
**Expected:**
- ✅ TableCard with columns: stop_order, stop_name, latitude, longitude
- ✅ Stops in correct order
- ✅ Message: "Path has X stops"

**Sample Output:**
```
| stop_order | stop_name    | latitude | longitude |
|------------|--------------|----------|-----------|
| 1          | Airport      | 12.9716  | 77.5946   |
| 2          | City Center  | 12.9352  | 77.6245   |
| 3          | University   | 12.9698  | 77.7499   |
```

---

#### Test 6: List Routes Using Path
**Command:** "which routes use path 1?" OR "show routes for Downtown path"
**Expected:**
- ✅ TableCard with columns: route_id, route_name, path_name, trip_count
- ✅ Shows all routes using specified path
- ✅ Message: "Found X routes"

**Sample Output:**
```
| route_id | route_name        | path_name     | trip_count |
|----------|-------------------|---------------|------------|
| 1        | Morning Express   | Downtown Loop | 5          |
| 2        | Evening Special   | Downtown Loop | 3          |
```

---

### ✏️ Static MUTATE Actions (5 tests - No Confirmation)

#### Test 7: Create Stop
**Command:** "create stop Library at 12.34, 56.78"
**Expected:**
- ✅ Executes instantly (no confirmation)
- ✅ ObjectCard with new stop details
- ✅ Message: "✅ Created stop 'Library'"
- ✅ Audit log inserted

**Sample Output:**
```
Stop ID: 15
Stop Name: Library
Latitude: 12.34
Longitude: 56.78
Created At: 2024-11-14 10:30:00
```

---

#### Test 8: Create Path
**Command:** "create path School-Library with stops School, Library"
**Expected:**
- ✅ Executes instantly (no confirmation)
- ✅ ObjectCard with new path details
- ✅ Message: "✅ Created path 'School-Library' with 2 stops"
- ✅ Audit log inserted

**Sample Output:**
```
Path ID: 8
Path Name: School-Library
Stop Count: 2
Stops: School (1), Library (2)
Created At: 2024-11-14 10:31:00
```

---

#### Test 9: Create Route
**Command:** "create route Morning Route using School-Library"
**Expected:**
- ✅ Executes instantly (no confirmation)
- ✅ ObjectCard with new route details
- ✅ Message: "✅ Created route 'Morning Route'"
- ✅ Audit log inserted

**Sample Output:**
```
Route ID: 12
Route Name: Morning Route
Path: School-Library
Created At: 2024-11-14 10:32:00
```

---

#### Test 10: Rename Stop
**Command:** "rename stop Library to Central Library"
**Expected:**
- ✅ Executes instantly (no confirmation)
- ✅ ObjectCard with updated stop
- ✅ Message: "✅ Renamed stop to 'Central Library'"
- ✅ Audit log inserted

**Sample Output:**
```
Stop ID: 15
Old Name: Library
New Name: Central Library
Updated At: 2024-11-14 10:33:00
```

---

#### Test 11: Duplicate Route
**Command:** "duplicate route 1" OR "copy Morning Express route"
**Expected:**
- ✅ Executes instantly (no confirmation)
- ✅ ObjectCard with new route details
- ✅ Message: "✅ Duplicated route (new ID: 13)"
- ✅ New path created with same stops
- ✅ Audit log inserted

**Sample Output:**
```
Original Route ID: 1
New Route ID: 13
Route Name: Morning Express (Copy)
Path Name: Downtown Loop (Copy)
Stop Count: 5
Created At: 2024-11-14 10:34:00
```

---

### 🚌 Dynamic MUTATE Actions (4 tests - WITH Confirmation)

#### Test 12: Cancel Trip (With Bookings)
**Command:** "cancel trip 501"
**Expected:**
- ✅ Shows consequences warning
- ✅ Message: "⚠️ Cancelling will affect 5 passenger(s)"
- ✅ Confirm/Cancel buttons appear
- ✅ After confirm: "✅ Trip 501 cancelled successfully"
- ✅ Audit log inserted

**Flow:**
1. User: "cancel trip 501"
2. Agent: ⚠️ Warning + consequences
3. User: [Clicks Confirm]
4. Agent: ✅ Action completed

---

#### Test 13: Remove Vehicle (With Bookings)
**Command:** "remove vehicle from trip 501"
**Expected:**
- ✅ Shows consequences warning if bookings exist
- ✅ Message: "⚠️ This trip has 5 active booking(s) (10% capacity)"
- ✅ Confirm/Cancel buttons
- ✅ After confirm: "✅ Vehicle removed from trip 501"
- ✅ Audit log inserted

---

#### Test 14: Assign Vehicle
**Command:** "assign vehicle 5 to trip 502"
**Expected:**
- ✅ Error if vehicle already assigned: "This trip already has vehicle X assigned"
- ✅ If valid: No confirmation needed (unless edge case)
- ✅ Message: "✅ Assigned vehicle 5 to trip 502"
- ✅ Audit log inserted

---

#### Test 15: Update Trip Time (With Bookings)
**Command:** "update trip 501 time to 9:00" OR "change trip 501 to 9am"
**Expected:**
- ✅ Shows consequences if bookings exist
- ✅ Message: "⚠️ Changing time will affect 5 passenger(s)"
- ✅ Confirm/Cancel buttons
- ✅ After confirm: "✅ Trip time updated to 9:00"
- ✅ display_name updated via regex
- ✅ Audit log inserted

**Before:** `display_name = "Path-1 - 08:00"`
**After:** `display_name = "Path-1 - 09:00"`

---

#### Test 16: Update Trip Time (No Bookings)
**Command:** "update trip 503 time to 10:30"
**Expected:**
- ✅ Executes instantly (no confirmation if no bookings)
- ✅ Message: "✅ Trip time updated to 10:30"
- ✅ Audit log inserted

---

### 💡 Helper Actions (1 test)

#### Test 17: Create New Route Help
**Command:** "how do I create a new route?" OR "help with route creation"
**Expected:**
- ✅ HelpCard with step-by-step guide
- ✅ Shows 4 steps
- ✅ Blue card styling

**Sample Output:**
```
💡 How to Create a New Route

1. Go to Manage Routes page
2. Create stops first if they don't exist: 'Create stop <name> at <lat>, <lon>'
3. Create a path with ordered stops: 'Create path <name> with stops <stop1>, <stop2>, <stop3>'
4. Create a route using the path: 'Create route <name> using <path_name>'
```

---

## Edge Cases & Error Handling

### Test 18: Unknown Action
**Command:** "delete all trips" (not supported)
**Expected:**
- ✅ action = "unknown"
- ✅ Falls back to safe response
- ✅ Message: "I'm not sure what you want to do..."

---

### Test 19: Missing Parameters
**Command:** "create stop Library" (missing coordinates)
**Expected:**
- ✅ Error: "missing_parameters"
- ✅ Message: "Stop name, latitude, and longitude are required"

---

### Test 20: Trip Not Found
**Command:** "cancel trip 99999"
**Expected:**
- ✅ Error: "trip_not_found"
- ✅ Message: "Could not find trip matching '99999'"

---

### Test 21: Path Not Found
**Command:** "show stops for path NonExistent"
**Expected:**
- ✅ Error: "path_not_found"
- ✅ Message: "Path 'NonExistent' not found"

---

### Test 22: Route Not Found
**Command:** "duplicate route 99999"
**Expected:**
- ✅ Error: "route_not_found"
- ✅ Message: "Route not found"

---

## UI/UX Verification

### TableCard Tests
- ✅ Headers formatted correctly (snake_case → Title Case)
- ✅ Null values show as "-"
- ✅ Boolean values show as ✓/✗
- ✅ Hover effect on rows
- ✅ Footer shows row count

### ListCard Tests
- ✅ Items numbered 1, 2, 3...
- ✅ Blue circle with number
- ✅ Footer shows item count

### ObjectCard Tests
- ✅ Keys formatted (snake_case → Title Case)
- ✅ Type-specific rendering:
  - Numbers: blue monospace
  - Booleans: green ✓ / red ✗
  - Arrays: indented list
  - Objects: JSON preview
  - Null: gray italic
- ✅ Footer shows field count

### HelpCard Tests
- ✅ Blue theme (border, background)
- ✅ 💡 emoji in header
- ✅ Numbered steps with blue circles
- ✅ Optional notes section

---

## Performance Tests

### Test 23: Large Dataset
**Command:** "list all stops" (with 100+ stops)
**Expected:**
- ✅ TableCard renders smoothly
- ✅ Scrollable if needed
- ✅ No lag

### Test 24: Complex Object
**Command:** "get details for trip 501" (with 20+ bookings)
**Expected:**
- ✅ ObjectCard handles nested arrays
- ✅ Bookings displayed properly
- ✅ No crashes

---

## Audit Log Verification

After each MUTATE action, verify in database:

```sql
SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;
```

**Expected fields:**
- ✅ action (e.g., "cancel_trip", "create_stop")
- ✅ entity_type (e.g., "trip", "stop")
- ✅ entity_id
- ✅ user_id
- ✅ details (JSON with old/new values)
- ✅ timestamp

---

## Success Criteria

✅ **16/16 actions working**
✅ **All 4 card types render correctly**
✅ **Safe actions execute instantly**
✅ **Risky actions require confirmation**
✅ **Error handling graceful**
✅ **Audit logs complete**
✅ **UI responsive and smooth**

---

## Production Checklist

Before deployment:

- [ ] Set `USE_LLM_PARSE=true` in production .env
- [ ] Update API_KEY in frontend
- [ ] Test all 16 actions in production environment
- [ ] Verify Gemini API quota and rate limits
- [ ] Enable audit log retention policy
- [ ] Add monitoring for LLM failures
- [ ] Document new actions for users
- [ ] Train operations team on new features

---

## Known Limitations

1. **Path/Route Resolution**: Only supports exact name or numeric ID (no fuzzy matching yet)
2. **Bulk Operations**: Currently single-item only (no "cancel all trips")
3. **Undo**: No undo functionality (use audit logs to track changes)
4. **Permissions**: All actions use user_id=1 (no role-based access control yet)

---

## Next Enhancements (Future)

- [ ] Fuzzy search for paths/routes
- [ ] Bulk operations ("cancel all morning trips")
- [ ] Undo/rollback actions
- [ ] Role-based permissions
- [ ] Voice input integration
- [ ] Image-based trip selection (QR codes)
- [ ] Export data to CSV/Excel
- [ ] Advanced filtering in lists
