# MOVI Agent Expansion - Implementation Status

## ✅ COMPLETED PHASES

### Phase A: LLM Schema Update ✅
- ✅ Updated SYSTEM_PROMPT with all 16 actions
- ✅ Added 16 few-shot examples covering all action types
- ✅ Updated _validate_llm_response() to accept all actions
- ✅ Extended parse_intent_llm.py to pass target_path_id, target_route_id

### Phase C: Tools Layer ✅  
- ✅ Added tool_get_unassigned_vehicles()
- ✅ Added tool_get_trip_details()
- ✅ Added tool_list_all_stops()
- ✅ Added tool_list_stops_for_path()
- ✅ Added tool_list_routes_using_path()
- ✅ Added tool_create_stop()
- ✅ Added tool_create_path()
- ✅ Added tool_create_route()
- ✅ Added tool_update_trip_time()
- ✅ Added tool_rename_stop()
- ✅ Added tool_duplicate_route()
- ✅ Added tool_get_path_by_label()
- ✅ Added tool_get_route_by_label()
- ✅ Updated tools/__init__.py exports

## 🔄 REMAINING PHASES

### Phase B: Update resolve_target ⏳
**Status:** Ready to implement

**Changes Needed:**
1. Add path resolution logic after trip resolution
2. Add route resolution logic
3. Handle actions that don't need target resolution (list_all_stops, get_unassigned_vehicles, create_new_route_help)

**Implementation:**
```python
# In resolve_target.py, after existing trip resolution:

# === PATH RESOLUTION (for path-related actions) ===
path_actions = ["list_stops_for_path", "list_routes_using_path", "create_path"]
if state.get("action") in path_actions:
    # Try numeric path_id first
    if state.get("target_path_id"):
        # Verify with DB
        ...
    # Try label-based search
    elif state.get("target_label"):
        path = await tool_get_path_by_label(state["target_label"])
        if path:
            state["path_id"] = path["path_id"]
            return state
    
# === ROUTE RESOLUTION ===
route_actions = ["duplicate_route", "create_route"]
if state.get("action") in route_actions:
    if state.get("target_route_id"):
        # Verify with DB
        ...
    elif state.get("target_label"):
        route = await tool_get_route_by_label(state["target_label"])
        ...

# === ACTIONS THAT DON'T NEED RESOLUTION ===
no_target_actions = ["list_all_stops", "get_unassigned_vehicles", "create_new_route_help"]
if state.get("action") in no_target_actions:
    return state  # Skip resolution
```

### Phase D: Service Layer ⏳
**Status:** Need to implement in `app/core/service.py`

**Functions to Add:**
- get_unassigned_vehicles()
- get_trip_details()
- list_all_stops()
- list_stops_for_path()
- list_routes_using_path()
- create_stop()
- create_path()
- create_route()
- update_trip_time()
- rename_stop()
- duplicate_route()

### Phase E: Update execute_action ⏳
**Status:** Need to map all 16 actions to tools

**Actions to Map:**
```python
# READ actions (instant execution, type="table" or "list")
if action == "get_unassigned_vehicles":
    result = await tool_get_unassigned_vehicles()
    state["final_output"] = {"type": "table", "data": result}

# MUTATE actions (check if risky)
elif action == "update_trip_time":
    # Requires confirmation
    ...
elif action == "create_stop":
    # Safe, execute instantly
    result = await tool_create_stop(...)
    state["final_output"] = {"type": "object", "data": result}
```

### Phase F: Consequence Logic ⏳
**Update check_consequences.py:**
```python
RISKY_ACTIONS = [
    "remove_vehicle",
    "cancel_trip", 
    "update_trip_time",
    "delete_path"
]

SAFE_ACTIONS = [
    # All READ actions
    "get_unassigned_vehicles", "get_trip_status", "get_trip_details",
    "list_all_stops", "list_stops_for_path", "list_routes_using_path",
    # Safe CREATE actions
    "create_stop", "create_path", "create_route", "rename_stop", "duplicate_route"
]
```

### Phase G: Frontend Widget ⏳
**Components Needed:**
- TableCard.tsx (for tabular data)
- ListCard.tsx (for lists)
- ObjectCard.tsx (for key-value)
- Update MoviWidget to render based on response.type

## 📊 Implementation Progress

| Phase | Status | Progress |
|-------|--------|----------|
| Phase A (LLM) | ✅ Complete | 100% |
| Phase B (resolve_target) | ⏳ Ready | 0% |
| Phase C (Tools) | ✅ Complete | 100% |
| Phase D (Service) | ⏳ Pending | 0% |
| Phase E (execute_action) | ⏳ Pending | 0% |
| Phase F (Consequences) | ⏳ Pending | 0% |
| Phase G (Frontend) | ⏳ Pending | 0% |

**Overall:** 2/7 phases complete (29%)

## 🎯 Next Steps

1. ✅ Update resolve_target.py for path/route resolution
2. ✅ Implement all service.py functions
3. ✅ Update execute_action.py to map all 16 actions
4. ✅ Update check_consequences.py risky actions list
5. ✅ Frontend: Add TableCard, ListCard, ObjectCard components

## 📝 Notes

- All tool wrappers call service functions
- Service functions handle DB transactions + audit logs
- execute_action determines output format (table/list/object)
- Risky actions require confirmation, safe actions execute instantly
- currentPage context guides LLM action selection

---
**Status:** Backend 29% complete, ready to continue Phase B
