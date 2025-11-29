# MOVI Agent - Confirmed Working Actions

**Generated:** November 26, 2025  
**Status:** Production-Ready  
**Audit Method:** Full codebase scan of `llm_client.py`, `execute_action.py`, `tools.py`, `resolve_target.py`, `check_consequences.py`, `graph_def.py`

---

## Confirmed Working Actions

### 1. Trip Management (10 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 1 | `assign_vehicle` | "Assign vehicle 5 to trip 10" | Assigns a vehicle to a trip deployment |
| 2 | `assign_driver` | "Assign driver 3 to trip 10" | Assigns a driver to a trip |
| 3 | `remove_vehicle` | "Remove vehicle from trip 10" | Removes vehicle assignment from trip |
| 4 | `remove_driver` | "Remove driver from trip 10" | Removes driver assignment from trip |
| 5 | `cancel_trip` | "Cancel trip 15" | Cancels a trip and notifies passengers |
| 6 | `update_trip_time` | "Update trip 10 time to 14:30" | Changes the scheduled departure time |
| 7 | `update_trip_status` | "Mark trip 10 as completed" | Updates status (SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED) |
| 8 | `delay_trip` | "Delay trip 10 by 15 minutes" | Postpones trip by specified minutes |
| 9 | `reschedule_trip` | "Reschedule trip 10 to 16:00" | Moves trip to a new time or date |
| 10 | `get_trip_details` | "Show details for trip 10" | Returns full trip information |

---

### 2. Vehicle Management (8 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 11 | `list_all_vehicles` | "List all vehicles" | Shows all vehicles in the fleet |
| 12 | `get_unassigned_vehicles` | "Show unassigned vehicles" | Lists vehicles not assigned to any trip |
| 13 | `get_vehicle_status` | "Show status for vehicle 5" | Returns detailed status for a vehicle |
| 14 | `get_vehicle_trips_today` | "What trips does vehicle 5 have today?" | Lists today's trips for a vehicle |
| 15 | `block_vehicle` | "Block vehicle 5" | Marks vehicle as unavailable |
| 16 | `unblock_vehicle` | "Unblock vehicle 5" | Makes vehicle available again |
| 17 | `add_vehicle` | "Add vehicle KA01AB1234" | Registers a new vehicle in the fleet |
| 18 | `recommend_vehicle_for_trip` | "Recommend a vehicle for trip 10" | Suggests best available vehicle |

---

### 3. Driver Management (7 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 19 | `list_all_drivers` | "List all drivers" | Shows all drivers in the system |
| 20 | `get_available_drivers` | "Show available drivers" | Lists drivers not currently assigned |
| 21 | `get_driver_status` | "Show status for driver 3" | Returns detailed status for a driver |
| 22 | `get_driver_trips_today` | "What trips does driver 3 have today?" | Lists today's trips for a driver |
| 23 | `set_driver_availability` | "Set driver 3 as unavailable" | Updates driver availability status |
| 24 | `add_driver` | "Add driver John Smith" | Registers a new driver |
| 25 | `suggest_alternate_vehicle` | "Suggest alternate vehicle for trip 10" | Recommends replacement vehicle |

---

### 4. Booking Management (4 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 26 | `get_booking_count` | "How many bookings for trip 10?" | Returns booking count and capacity |
| 27 | `list_passengers` | "List passengers for trip 10" | Shows all booked passengers |
| 28 | `cancel_all_bookings` | "Cancel all bookings for trip 10" | Cancels all trip bookings |
| 29 | `find_employee_trips` | "Find trips for employee John" | Searches bookings by employee name |

---

### 5. Stop/Path/Route Configuration (11 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 30 | `list_all_stops` | "List all stops" | Shows all stops in the system |
| 31 | `list_all_paths` | "List all paths" | Shows all paths with stop counts |
| 32 | `list_all_routes` | "List all routes" | Shows all routes with path info |
| 33 | `list_stops_for_path` | "List stops for path 2" | Shows ordered stops in a path |
| 34 | `list_routes_using_path` | "Which routes use path 2?" | Lists routes that use a path |
| 35 | `create_stop` | "Create stop named Central Station" | Creates a new stop location |
| 36 | `create_path` | "Create path Main Route with stops A, B, C" | Creates a path with ordered stops |
| 37 | `create_route` | "Create route Express using path 2" | Creates a route using a path |
| 38 | `rename_stop` | "Rename stop Central to Downtown Central" | Renames an existing stop |
| 39 | `duplicate_route` | "Duplicate route 5" | Creates a copy of a route |
| 40 | `validate_route` | "Validate route 5" | Checks route configuration validity |

---

### 6. Dashboard Intelligence (7 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 41 | `get_trips_needing_attention` | "Which trips need attention?" | Lists trips with issues |
| 42 | `get_today_summary` | "Show today's summary" | Returns daily operational summary |
| 43 | `get_recent_changes` | "What changed in the last 10 minutes?" | Lists recent system changes |
| 44 | `get_high_demand_offices` | "Which office has most demand?" | Shows booking demand by location |
| 45 | `get_most_used_vehicles` | "Which vehicles are most used?" | Shows vehicle usage statistics |
| 46 | `detect_overbooking` | "Are any trips overbooked?" | Finds trips exceeding capacity |
| 47 | `predict_problem_trips` | "Predict problem trips" | Identifies at-risk trips |

---

### 7. Smart Automation (4 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 48 | `check_trip_readiness` | "Can trip 10 run?" | Checks if trip has all requirements |
| 49 | `simulate_action` | "Simulate cancelling trip 10" | Shows impact without executing |
| 50 | `explain_decision` | "Explain why you assigned that vehicle" | Explains agent reasoning |
| 51 | `get_trip_status` | "What is the status of trip 10?" | Returns current trip status |

---

### 8. Delete Operations (3 actions)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 52 | `delete_stop` | "Delete stop 15" | Removes a stop (with dependency check) |
| 53 | `delete_path` | "Delete path 3" | Removes a path (with dependency check) |
| 54 | `delete_route` | "Delete route 7" | Removes a route (with dependency check) |

---

### 9. Path Management (1 action)

| # | Action Name | Command | Description |
|---|-------------|---------|-------------|
| 55 | `update_path_stops` | "Update path 2 with stops 1, 5, 3, 8" | Reorders stops in a path |

---

## Total: 55 Confirmed Working Actions

---

## Alternative Command Phrasings

The Movi agent understands natural language. Here are alternative ways to trigger each action:

### Trip Actions
- `assign_vehicle`: "put vehicle on trip", "allocate vehicle", "deploy vehicle to trip"
- `assign_driver`: "put driver on trip", "allocate driver", "add driver to trip"
- `remove_vehicle`: "take vehicle off", "unassign vehicle", "detach vehicle"
- `remove_driver`: "take driver off", "unassign driver", "detach driver"
- `cancel_trip`: "abort trip", "stop trip", "delete trip"
- `delay_trip`: "postpone trip", "push trip back"
- `reschedule_trip`: "move trip to", "change trip time to"

### Vehicle Actions
- `list_all_vehicles`: "show all vehicles", "all buses"
- `get_unassigned_vehicles`: "available vehicles", "free vehicles"
- `block_vehicle`: "disable vehicle", "take vehicle offline"
- `unblock_vehicle`: "enable vehicle", "bring vehicle online"
- `add_vehicle`: "register vehicle", "create vehicle", "new bus"

### Driver Actions
- `list_all_drivers`: "show all drivers", "all drivers"
- `get_available_drivers`: "free drivers", "who is available"
- `set_driver_availability`: "driver is available", "driver not available"
- `add_driver`: "register driver", "create driver", "new driver"

### Dashboard Actions
- `get_trips_needing_attention`: "problem trips", "what needs attention"
- `get_today_summary`: "today's status", "operations summary", "daily report"
- `detect_overbooking`: "overbooked trips", "over capacity trips"
- `predict_problem_trips`: "at risk trips", "potential problems"

---

## Potentially Implemented but Needs Review

These actions exist in the registry but have limited testing or may need additional work:

| # | Action Name | Status | Notes |
|---|-------------|--------|-------|
| 1 | `get_trip_bookings` | ⚠️ Partial | Works but overlaps with `list_passengers` |
| 2 | `change_driver` | ⚠️ Partial | UI interaction needed for driver selection |
| 3 | `duplicate_trip` | ⚠️ Partial | Requires date input wizard |
| 4 | `create_followup_trip` | ⚠️ Partial | Requires wizard flow |
| 5 | `context_mismatch` | ✅ Helper | Returns when action doesn't match page context |
| 6 | `create_new_route_help` | ✅ Helper | Returns help text for route creation |

---

## NOT Implemented (Excluded from list)

These actions are in the registry but are **stubs/placeholders** and will cause errors:

| Action Name | Issue |
|-------------|-------|
| `split_trip` | Not implemented |
| `merge_trips` | Not implemented |
| `reassign_vehicle` | Not implemented |
| `reassign_driver` | Not implemented |
| `schedule_maintenance` | Not implemented |
| `check_rest_compliance` | Not implemented |
| `predict_fatigue_violations` | Not implemented |
| `predict_booking_surge` | Not implemented |
| `undo_action` | Placeholder only |

---

## Quick Reference: Most Common Commands

```
# Trip Management
"Cancel trip 5"
"Assign vehicle 3 to trip 10"
"Assign driver 2 to trip 10"
"Delay trip 5 by 20 minutes"
"Reschedule trip 10 to 15:30"

# Vehicle Management
"List all vehicles"
"Block vehicle 5"
"Add vehicle MH01XY1234"

# Driver Management
"List available drivers"
"Add driver Rahul Kumar"
"Set driver 3 as unavailable"

# Dashboard
"Show today's summary"
"Which trips need attention?"
"Detect overbooked trips"

# Configuration
"List all routes"
"Validate route 5"
"List all stops"
```

---

## Notes

1. **Rate Limiting**: Gemini API may return "unknown" action if requests are too fast. Add 1-2 second delays between consecutive calls.

2. **Confirmation Flow**: Risky actions (cancel_trip, remove_vehicle, remove_driver) require confirmation before execution.

3. **Trip Context**: When a trip is selected in the UI, actions like "assign driver" automatically use that trip without needing to specify the ID.

4. **Natural Language**: The agent understands conversational English, Hinglish, and incomplete phrases.

5. **Trip IDs Must Exist**: When using numeric trip IDs (e.g., "trip 10"), the trip must exist in the database. If the trip doesn't exist, you'll get "I couldn't find that trip". Use `get_trips_needing_attention` or check your dashboard to see which trips exist.

6. **Trip Display Names**: You can also use trip display names instead of IDs:
   - ✅ "Assign vehicle to Evening - 18:00"
   - ✅ "Cancel Morning Rush - 08:30"
   - ✅ "Remove driver from Path-1 - 09:00"

---

**End of Document**
