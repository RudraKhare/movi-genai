# MOVI Agent - Complete Actions Audit (83 Actions)

## Summary

| Category | Total | ✅ Implemented | ⚠️ Partial | ❌ Missing |
|----------|-------|----------------|------------|------------|
| 1. Trip Management | 16 | 10 | 2 | 4 |
| 2. Vehicle Management | 10 | 8 | 0 | 2 |
| 3. Driver Management | 8 | 5 | 0 | 3 |
| 4. Booking Management | 6 | 5 | 0 | 1 |
| 5. Route/Path/Stop | 14 | 13 | 0 | 1 |
| 6. Dashboard Intelligence | 5 | 5 | 0 | 0 |
| 7. Multimodal Actions | 5 | 3 | 2 | 0 |
| 8. Smart Automation | 9 | 3 | 0 | 6 |
| 9. Query Capabilities | 7 | 2 | 0 | 5 |
| 10. System/Meta Actions | 5 | 3 | 1 | 1 |
| **TOTAL** | **83** | **57** | **5** | **23** |

---

## 1️⃣ TRIP MANAGEMENT (16 actions)

### Core (6 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Assign a vehicle to a trip | ✅ | `tool_assign_vehicle` | ✅ | RISKY | Full flow |
| Assign a driver to a trip | ✅ | `tool_assign_driver` | ✅ | SAFE | Full flow |
| Remove a vehicle from a trip | ✅ | `tool_remove_vehicle` | ✅ | RISKY | Full flow |
| Remove a driver from a trip | ✅ | `tool_remove_driver` | ✅ | RISKY | Full flow |
| Reassign vehicle between trips | ⚠️ | N/A | N/A | - | Use remove + assign |
| Reassign driver between trips | ⚠️ | N/A | N/A | - | Use remove + assign |

### Advanced (6 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Delay a trip | ❌ | `tool_delay_trip` exists | ❌ No handler | - | Tool exists but no handler |
| Cancel a trip | ✅ | `tool_cancel_trip` | ✅ | RISKY | Full flow |
| Reschedule a trip | ❌ | `tool_reschedule_trip` exists | ❌ No handler | - | Tool exists but no handler |
| Mark trip as started/completed | ✅ | `tool_update_trip_status` | ✅ | RISKY | Full flow |
| Split a trip | ❌ | `tool_split_trip` exists | ❌ No handler | - | Tool exists but no handler |
| Merge trips | ❌ | `tool_merge_trips` exists | ❌ No handler | - | Tool exists but no handler |

### Safety/Tribal Knowledge (4 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Check if trip can run | ✅ | `tool_check_trip_readiness` | ✅ | SAFE | Full flow |
| Check if trip is overbooked | ✅ | `tool_detect_overbooking` | ✅ | SAFE | Full flow |
| Predict trips that may fail | ✅ | `tool_predict_problem_trips` | ✅ | SAFE | Full flow |
| Suggest alternate vehicle | ✅ | `tool_suggest_alternate_vehicle` | ✅ | SAFE | Full flow |

---

## 2️⃣ VEHICLE MANAGEMENT (10 actions)

### Core (5 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| List all unassigned vehicles | ✅ | `tool_get_unassigned_vehicles` | ✅ | SAFE | Full flow |
| Show vehicle status | ✅ | `tool_get_vehicle_status` | ✅ | SAFE | Full flow |
| Add a new vehicle | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Remove a vehicle from fleet | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Check vehicle capacity | ✅ | Part of `get_vehicle_status` | ✅ | SAFE | Included in status |

### Advanced (5 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Schedule vehicle maintenance | ✅ | `tool_block_vehicle` | ✅ | RISKY | Uses block with reason |
| Block a vehicle temporarily | ✅ | `tool_block_vehicle` | ✅ | RISKY | Full flow |
| Show vehicle trips today | ✅ | `tool_get_vehicle_trips_today` | ✅ | SAFE | Full flow |
| Recommend best vehicle | ✅ | `tool_recommend_vehicle_for_trip` | ✅ | SAFE | Full flow |
| Unblock a vehicle | ✅ | `tool_unblock_vehicle` | ✅ | RISKY | Full flow |

---

## 3️⃣ DRIVER MANAGEMENT (8 actions)

### Core (5 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| List available drivers | ✅ | `tool_get_available_drivers` | ✅ | SAFE | Full flow |
| Add a new driver | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Remove/deactivate a driver | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Assign driver shift | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Show driver duty roster | ✅ | `tool_get_driver_trips_today` | ✅ | SAFE | Shows today's assignments |

### Advanced (3 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Check driver eligibility | ✅ | `tool_get_driver_status` | ✅ | SAFE | Full flow |
| Predict driver fatigue | ⚠️ | Part of `get_driver_status` | ✅ | SAFE | Basic implementation |
| Show driver past history | ✅ | `tool_get_driver_trips_today` | ✅ | SAFE | Today only, not full history |

---

## 4️⃣ BOOKING MANAGEMENT (6 actions)

### Core (4 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Check booking count | ✅ | `tool_get_booking_count` | ✅ | SAFE | Full flow |
| List all passengers | ✅ | `tool_list_passengers` | ✅ | SAFE | Full flow |
| Cancel all bookings | ✅ | `tool_cancel_all_bookings` | ✅ | RISKY | Full flow |
| Find trips by employee | ✅ | `tool_find_employee_trips` | ✅ | SAFE | Full flow |

### Advanced (2 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Predict booking surge | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Identify high-risk trips | ✅ | `tool_predict_problem_trips` | ✅ | SAFE | Covers this use case |

---

## 5️⃣ ROUTE / PATH / STOP CONFIGURATION (14 actions)

### Stops (4 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Create a new stop | ✅ | `tool_create_stop` | ✅ | SAFE | Full flow |
| Delete a stop | ✅ | `tool_delete_stop` | ✅ | RISKY | Full flow |
| Rename a stop | ✅ | `tool_rename_stop` | ✅ | SAFE | Full flow |
| List all stops | ✅ | `tool_list_all_stops` | ✅ | SAFE | Full flow |

### Paths (5 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Create a path | ✅ | `tool_create_path` | ✅ | SAFE | Full flow |
| Update stops in a path | ✅ | `tool_update_path_stops` | ✅ | RISKY | Full flow |
| Delete a path | ✅ | `tool_delete_path` | ✅ | RISKY | Full flow |
| List all paths | ✅ | `tool_get_all_paths` | ⚠️ | SAFE | Tool exists, no direct handler |
| List trips using a path | ✅ | `tool_list_routes_using_path` | ✅ | SAFE | Full flow |

### Routes (5 actions)
| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Create a new route | ✅ | `tool_create_route` | ✅ | SAFE | Full flow |
| Update a route | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Delete a route | ✅ | `tool_delete_route` | ✅ | RISKY | Full flow |
| List all routes | ✅ | `tool_get_all_routes` | ⚠️ | SAFE | Tool exists, no direct handler |
| Check if route is broken | ✅ | `tool_validate_route` | ✅ | SAFE | Full flow |

---

## 6️⃣ DASHBOARD INTELLIGENCE (5 actions)

| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Trips needing attention | ✅ | `tool_get_trips_needing_attention` | ✅ | SAFE | Full flow |
| Trips that will fail today | ✅ | `tool_predict_problem_trips` | ✅ | SAFE | Full flow |
| What changed in last 10 min | ✅ | `tool_get_recent_changes` | ✅ | SAFE | Full flow |
| Office with most demand | ✅ | `tool_get_high_demand_offices` | ✅ | SAFE | Full flow |
| Most used vehicle this week | ✅ | `tool_get_most_used_vehicles` | ✅ | SAFE | Full flow |

---

## 7️⃣ MULTIMODAL ACTIONS (5 actions)

| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Infer trip from screenshot | ✅ | OCR in `llm_client.py` | ✅ | N/A | Uses Gemini Vision |
| Interpret arrows/highlights | ⚠️ | Partial in OCR | ⚠️ | N/A | Basic support |
| Extract trip from blurred UI | ⚠️ | Partial in OCR | ⚠️ | N/A | Basic support |
| Understand voice commands | ✅ | Frontend Web Speech API | ✅ | N/A | Works well |
| Follow-up questions | ✅ | LLM clarification flow | ✅ | N/A | Uses clarify_options |

---

## 8️⃣ SMART AUTOMATION (9 actions)

| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Auto-create missing trip sheets | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Auto-assign vehicles | ❌ | `tool_auto_assign_vehicle` exists | ❌ | - | Tool exists, no handler |
| Auto-assign drivers | ❌ | `tool_auto_assign_driver` exists | ❌ | - | Tool exists, no handler |
| Optimize fleet usage | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Suggest combining trips | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Validate data model | ✅ | `tool_validate_route` | ✅ | SAFE | Partial coverage |
| Find orphaned trips/stops | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Detect config problems | ✅ | `tool_validate_route` | ✅ | SAFE | Partial coverage |
| Simulate action | ✅ | `tool_simulate_action` | ✅ | SAFE | Full flow |

---

## 9️⃣ QUERY CAPABILITIES (7 actions)

| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| How many trips running now? | ✅ | `tool_get_today_summary` | ✅ | SAFE | Full flow |
| How many trips failed today? | ✅ | `tool_get_today_summary` | ✅ | SAFE | Full flow |
| Which driver had most delays? | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| How many used shuttle today? | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| Trip with highest risk if remove vehicle | ❌ | N/A | N/A | - | NOT IMPLEMENTED |
| What breaks if delete stop? | ❌ | N/A | N/A | - | Partial in validate_route |
| Why can't this trip start? | ❌ | N/A | N/A | - | Partial in check_trip_readiness |

---

## 🔟 SYSTEM / META ACTIONS (5 actions)

| Action | Status | Tool Function | Execute Handler | Consequences | Notes |
|--------|--------|---------------|-----------------|--------------|-------|
| Undo last action | ❌ | `tool_undo_action` exists | ❌ | - | Tool exists, no handler |
| Confirm an action | ✅ | Confirmation flow | ✅ | N/A | Works via frontend |
| Reject an action | ✅ | Confirmation flow | ✅ | N/A | Works via frontend |
| Explain decision | ✅ | `tool_explain_decision` | ✅ | SAFE | Full flow |
| Simulate scenario | ⚠️ | `tool_simulate_action` | ✅ | SAFE | Basic implementation |

---

## FRONTEND INTEGRATION STATUS

| Component | Status | Notes |
|-----------|--------|-------|
| MoviWidget | ✅ | Main chat interface |
| Voice Input | ✅ | Web Speech API |
| Voice Output | ✅ | Speech synthesis |
| Image Upload | ✅ | Camera + file upload |
| Confirmation Flow | ✅ | For risky actions |
| Action Buttons | ✅ | Quick action options |
| Table Display | ✅ | For list results |

---

## DATABASE SCHEMA ALIGNMENT

| Table | Status | Notes |
|-------|--------|-------|
| daily_trips | ✅ | Uses `booking_status_percentage` not `booked_count` |
| vehicles | ✅ | Uses `status` not `is_active` |
| drivers | ✅ | Uses `status` not `is_available` |
| deployments | ✅ | Join table for trips/vehicles/drivers |
| bookings | ✅ | Passenger bookings |
| stops | ✅ | Stop locations |
| paths | ✅ | Path definitions |
| routes | ✅ | Route definitions |

---

## ACTIONS NEEDING IMPLEMENTATION

### High Priority (Commonly needed)
1. `delay_trip` - Add execute handler
2. `reschedule_trip` - Add execute handler  
3. `add_vehicle` - New tool + handler
4. `add_driver` - New tool + handler
5. `undo_action` - Add execute handler
6. `auto_assign_vehicle` - Add execute handler
7. `auto_assign_driver` - Add execute handler

### Medium Priority (Nice to have)
8. `split_trip` - Add execute handler
9. `merge_trips` - Add execute handler
10. `assign_driver_shift` - New tool + handler
11. `predict_booking_surge` - New tool + handler
12. `update_route` - New tool + handler
13. `list_all_paths` - Add execute handler
14. `list_all_routes` - Add execute handler

### Low Priority (Advanced features)
15. `remove_vehicle_from_fleet` - New tool + handler
16. `remove_driver` - New tool + handler
17. `find_orphaned_items` - New tool + handler
18. `optimize_fleet` - New tool + handler
19. `which_driver_most_delays` - New tool + handler

---

## CONSEQUENCE CHECKING STATUS

### SAFE_ACTIONS (36 actions)
All read-only actions execute immediately without confirmation.

### RISKY_ACTIONS (14 actions)
These require user confirmation:
- `remove_vehicle`, `remove_driver`, `cancel_trip`
- `update_trip_time`, `update_trip_status`, `assign_vehicle`
- `cancel_all_bookings`, `block_vehicle`, `unblock_vehicle`
- `set_driver_availability`, `delete_stop`, `delete_path`
- `delete_route`, `update_path_stops`

---

## TESTED & VERIFIED ACTIONS

The following actions have been tested and work correctly:
- ✅ `get_today_summary`
- ✅ `get_available_drivers`
- ✅ `get_driver_status`
- ✅ `get_recent_changes`
- ✅ `detect_overbooking`
- ✅ `predict_problem_trips`
- ✅ `get_trips_needing_attention`
- ✅ `list_all_stops`
- ✅ `get_unassigned_vehicles`
- ✅ `list_passengers` (needs trip_id)
- ✅ `find_employee_trips` (needs name)
