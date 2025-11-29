# MOVI Agent Actions Reference

## Overview

MOVI now supports **50+ actions** across 10 major capability categories. This document provides a complete reference for all implemented actions.

---

## 1️⃣ Trip Management (Dynamic)

| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `assign_vehicle` | Assign a vehicle to a trip | trip_id, vehicle_id | ✅ Yes |
| `assign_driver` | Assign a driver to a trip | trip_id, driver_id | ❌ No |
| `remove_vehicle` | Remove vehicle from a trip | trip_id | ✅ Yes |
| `remove_driver` | Remove driver from a trip | trip_id | ✅ Yes |
| `cancel_trip` | Cancel a trip | trip_id | ✅ Yes |
| `update_trip_time` | Update trip departure time | trip_id, new_time | ✅ Yes |
| `update_trip_status` | Manually update trip status | trip_id, new_status | ✅ Yes |
| `get_trip_status` | Get current status of a trip | trip_id | ❌ No |
| `get_trip_details` | Get full trip details | trip_id | ❌ No |
| `get_trip_bookings` | Get bookings for a trip | trip_id | ❌ No |
| `check_trip_readiness` | Check if trip is ready to run | trip_id | ❌ No |

### Example Commands
```
"Assign vehicle ABC123 to the 8:00 AM trip"
"Remove the driver from trip 41"
"Cancel trip Bulk - 00:01"
"Mark trip as in progress"
"Is trip 5 ready to run?"
```

---

## 2️⃣ Vehicle Management

| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `get_unassigned_vehicles` | List vehicles without assignments | - | ❌ No |
| `get_vehicle_status` | Get detailed vehicle status | vehicle_id | ❌ No |
| `get_vehicle_trips_today` | Get today's trips for a vehicle | vehicle_id | ❌ No |
| `block_vehicle` | Block vehicle from assignments | vehicle_id, reason | ✅ Yes |
| `unblock_vehicle` | Unblock a vehicle | vehicle_id | ✅ Yes |
| `recommend_vehicle_for_trip` | Suggest best vehicle for trip | trip_id | ❌ No |
| `suggest_alternate_vehicle` | Suggest alternate vehicle | trip_id | ❌ No |

### Example Commands
```
"List all unassigned vehicles"
"Show status of vehicle 5"
"Block vehicle ABC123 for maintenance"
"Recommend a vehicle for trip 10"
"What trips does vehicle 3 have today?"
```

---

## 3️⃣ Driver Management

| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `tool_list_available_drivers` | List available drivers | trip_id | ❌ No |
| `get_driver_status` | Get detailed driver status | driver_id | ❌ No |
| `get_driver_trips_today` | Get today's trips for a driver | driver_id | ❌ No |
| `set_driver_availability` | Set driver availability | driver_id, is_available | ✅ Yes |
| `find_driver_by_name` | Find driver by name | driver_name | ❌ No |

### Example Commands
```
"List available drivers"
"Show status of driver John"
"Set driver 5 as unavailable"
"What trips does Raj have today?"
```

---

## 4️⃣ Booking Management

| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `get_booking_count` | Get booking count for trip | trip_id | ❌ No |
| `list_passengers` | List all passengers on trip | trip_id | ❌ No |
| `cancel_all_bookings` | Cancel all bookings for trip | trip_id, reason | ✅ Yes |
| `find_employee_trips` | Find trips booked by employee | employee_name | ❌ No |

### Example Commands
```
"How many bookings does trip 5 have?"
"List passengers on the 8:00 trip"
"Cancel all bookings for trip 10"
"Find trips for employee John Smith"
```

---

## 5️⃣ Stops / Paths / Routes

### Stops
| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `list_all_stops` | List all stops | - | ❌ No |
| `create_stop` | Create a new stop | stop_name, lat, lng | ❌ No |
| `rename_stop` | Rename an existing stop | stop_id, new_name | ❌ No |
| `delete_stop` | Delete a stop (with checks) | stop_id | ✅ Yes |

### Paths
| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `list_stops_for_path` | List stops in a path | path_id | ❌ No |
| `create_path` | Create a new path | path_name, stop_names | ❌ No |
| `update_path_stops` | Update stops in a path | path_id, stop_ids | ✅ Yes |
| `delete_path` | Delete a path (with checks) | path_id | ✅ Yes |

### Routes
| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `list_routes_using_path` | List routes using a path | path_id | ❌ No |
| `create_route` | Create a new route | route_name, path_id | ❌ No |
| `duplicate_route` | Duplicate an existing route | route_id | ❌ No |
| `delete_route` | Delete a route (with checks) | route_id | ✅ Yes |
| `validate_route` | Validate route configuration | route_id | ❌ No |

### Example Commands
```
"List all stops"
"Create a new stop called 'Tech Park Gate 2'"
"Delete path 3"
"Validate route 5"
"What stops are on path 2?"
```

---

## 6️⃣ Dashboard Intelligence

| Action | Description | Parameters | Risky? |
|--------|-------------|------------|--------|
| `get_trips_needing_attention` | Trips with issues | - | ❌ No |
| `get_today_summary` | Today's operations summary | - | ❌ No |
| `get_recent_changes` | Recent system changes | minutes (default 10) | ❌ No |
| `get_high_demand_offices` | Offices with most demand | - | ❌ No |
| `get_most_used_vehicles` | Most used vehicles | days (default 7) | ❌ No |
| `detect_overbooking` | Find overbooked trips | - | ❌ No |
| `predict_problem_trips` | Predict at-risk trips | - | ❌ No |

### Example Commands
```
"What trips need attention?"
"Give me today's summary"
"What changed in the last 10 minutes?"
"Which office has the most bookings?"
"Which vehicle is most used this week?"
"Are there any overbooked trips?"
"Predict which trips might fail"
```

---

## 7️⃣ Smart Automation

| Action | Description | Parameters |
|--------|-------------|------------|
| `check_trip_readiness` | Check if trip can run | trip_id |
| `detect_overbooking` | Find overbooked trips | - |
| `predict_problem_trips` | Predict failing trips | - |
| `recommend_vehicle_for_trip` | Suggest best vehicle | trip_id |

### Example Commands
```
"Can trip 5 run?"
"Are there any overbooked trips?"
"Which trips might fail today?"
"Suggest a vehicle for trip 10"
```

---

## 8️⃣ System Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `simulate_action` | Simulate without executing | action, trip_id |
| `explain_decision` | Explain agent reasoning | action |

### Example Commands
```
"What would happen if I cancelled trip 5?"
"Explain why you suggested that vehicle"
```

---

## 9️⃣ Confirmation Flow

All **risky actions** require user confirmation before execution:

1. User requests action
2. Agent shows consequences: "⚠️ This trip has 5 bookings. Proceed?"
3. User confirms: "Yes" or "Confirm"
4. Agent executes action

### Risky Actions List
- `cancel_trip`
- `remove_vehicle`
- `remove_driver`
- `update_trip_time`
- `update_trip_status`
- `assign_vehicle`
- `cancel_all_bookings`
- `block_vehicle` / `unblock_vehicle`
- `set_driver_availability`
- `delete_stop` / `delete_path` / `delete_route`
- `update_path_stops`

---

## 🔟 Conversational Features

### Wizards
- **Trip Creation Wizard**: Step-by-step trip creation
- **Route Creation Help**: Guided route setup

### Context Awareness
- Uses `selectedTripId` from UI context
- Understands vague references: "this", "that", "it"
- Page-aware: Different actions on Dashboard vs Manage Routes

### Voice/Natural Language Support
- Understands various phrasings
- Handles Hinglish: "driver dal do", "yaha driver add karo"
- Tolerates incomplete phrases

---

## Action Categories Summary

| Category | Count | Examples |
|----------|-------|----------|
| Trip Management | 11 | assign, remove, cancel, status |
| Vehicle Management | 7 | list, status, block, recommend |
| Driver Management | 5 | list, status, availability |
| Booking Management | 4 | count, list, cancel, find |
| Stops/Paths/Routes | 13 | create, delete, validate |
| Dashboard Intelligence | 7 | summary, attention, predict |
| Smart Automation | 4 | readiness, overbooking |
| System | 2 | simulate, explain |
| Conversational | 9 | wizards, suggestions |

**Total: 50+ Actions**

---

## Architecture Flow

```
User Input
    ↓
parse_intent (LLM/Regex)
    ↓
resolve_target (Find trip/vehicle/driver)
    ↓
decision_router
    ↓
    ├── READ actions → execute_action → report_result
    │
    └── MUTATE actions → check_consequences
                              ↓
                         needs_confirmation?
                              ├── Yes → get_confirmation → execute_action
                              └── No → execute_action
                                            ↓
                                      report_result
```

---

## Files Modified

- `backend/langgraph/tools.py` - All tool implementations
- `backend/langgraph/tools/__init__.py` - Tool exports
- `backend/langgraph/tools/llm_client.py` - LLM prompt & action registry
- `backend/langgraph/nodes/execute_action.py` - Action handlers
- `backend/langgraph/nodes/check_consequences.py` - Risk categorization

---

*Last Updated: November 26, 2025*
