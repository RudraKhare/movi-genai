# 🎓 MOVI Agent - Complete Technical Interview Preparation Guide

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [LangGraph - The Core Engine](#3-langgraph---the-core-engine)
4. [All Nodes Explained](#4-all-nodes-explained)
5. [Action Flows - Complete Examples](#5-action-flows---complete-examples)
6. [Database Schema](#6-database-schema)
7. [How to Create a New Node](#7-how-to-create-a-new-node)
8. [Common Interview Questions](#8-common-interview-questions)

---

## 1. Project Overview

### What is MOVI?
MOVI (Multimodal Operations Virtual Intelligence) is an **AI-powered transport operations agent** that allows fleet managers to control bus/vehicle operations using **natural language**.

### Key Capabilities:
- **Natural Language Processing**: "Assign vehicle MH-12-7777 to the 8:00 trip"
- **Context Awareness**: Understands "this trip" based on UI selection
- **OCR Support**: Extract trip info from uploaded images
- **Multi-step Wizards**: Guided flows for complex operations
- **Confirmation Flows**: Warns before risky actions

### Tech Stack:
```
Frontend:     React + Vite (port 5173)
Backend:      FastAPI + Python (port 8000)
AI Engine:    LangGraph (custom implementation)
LLM:          Google Gemini 1.5 Flash
Database:     PostgreSQL (Supabase)
```

---

## 2. Architecture Deep Dive

### Directory Structure:
```
backend/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/
│   │   ├── agent.py         # /api/agent/* endpoints
│   │   ├── routes.py        # /api/routes/* endpoints
│   │   └── resources.py     # /api/resources/* endpoints
│   ├── core/
│   │   ├── supabase_client.py  # Database connection
│   │   └── service.py          # Business logic
│   └── models.py            # Pydantic models
├── langgraph/
│   ├── graph_def.py         # Graph structure & edges
│   ├── runtime.py           # Graph execution engine
│   ├── nodes/               # All processing nodes
│   └── tools/               # Database tools & LLM client
```

### Request Flow (High-Level):
```
User Input → FastAPI → LangGraph Runtime → Nodes → Tools → Database
                ↓
           Response ← report_result ← execute_action ← ...
```

---

## 3. LangGraph - The Core Engine

### What is LangGraph?
LangGraph is a **state machine for AI agents**. It defines:
- **Nodes**: Functions that process and transform state
- **Edges**: Connections between nodes (can be conditional)
- **State**: A dictionary passed through nodes

### Our Implementation (`graph_def.py`):

```python
class Graph:
    def __init__(self, name: str):
        self.nodes: Dict[str, Callable] = {}   # Node functions
        self.edges: Dict[str, List[Dict]] = {} # Edges with conditions
    
    def add_node(self, name: str, func: Callable):
        self.nodes[name] = func
    
    def add_edge(self, from_node: str, to_node: str, condition=None):
        self.edges[from_node].append({"to": to_node, "condition": condition})
    
    def get_next_node(self, current: str, state: Dict) -> str:
        for edge in self.edges[current]:
            if edge["condition"] is None or edge["condition"](state):
                return edge["to"]
        return None
```

### The Runtime (`runtime.py`):
```python
class GraphRuntime:
    async def run(self, input_state: Dict) -> Dict:
        state = input_state.copy()
        current = "parse_intent"  # Always starts here
        
        while current:
            node_func = self.graph.nodes[current]
            state = await node_func(state)  # Execute node
            
            if current in ["report_result", "fallback"]:
                break  # Terminal nodes
            
            current = self.graph.get_next_node(current, state)
        
        return state
```

### State Object (passed through all nodes):
```python
state = {
    # Input
    "text": "Assign vehicle to trip 42",
    "user_id": 1,
    "session_id": "abc-123",
    "selectedTripId": 42,        # From frontend context
    "currentPage": "busDashboard",
    
    # After parse_intent
    "action": "assign_vehicle",
    "target_trip_id": 42,
    "confidence": 0.95,
    "parsed_params": {"vehicle_registration": "MH-12-7777"},
    
    # After resolve_target
    "trip_id": 42,
    "trip_label": "Path-1 - 08:00",
    
    # After check_consequences
    "needs_confirmation": True,
    "consequences": {"booking_count": 5},
    
    # After execute_action
    "status": "executed",
    "message": "Vehicle assigned successfully",
    
    # Final output
    "final_output": {...}
}
```

---

## 4. All Nodes Explained

### 4.1 `parse_intent_llm` (Entry Point)
**Purpose**: Convert natural language → structured intent

**Key Logic**:
1. Check if wizard is active → route to wizard
2. Check for structured commands (from UI buttons)
3. Check for context (selectedTripId) → use directly
4. Call LLM (Gemini) to parse intent

**Input**: `state["text"]`, `state["selectedTripId"]`
**Output**: `state["action"]`, `state["target_trip_id"]`, `state["confidence"]`

```python
async def parse_intent_llm(state: Dict) -> Dict:
    text = state.get("text", "")
    selected_trip_id = state.get("selectedTripId")
    
    # Shortcut: If wizard active, route there
    if state.get("wizard_active"):
        state["next_node"] = "execute_action"
        return state
    
    # Shortcut: If context exists, use it
    if selected_trip_id and "assign" in text:
        state["action"] = "assign_vehicle"
        state["target_trip_id"] = selected_trip_id
        return state
    
    # Otherwise, call LLM
    llm_response = await parse_intent_with_llm(text, context)
    state["action"] = llm_response["action"]
    state["target_trip_id"] = llm_response["target_trip_id"]
    return state
```

---

### 4.2 `resolve_target`
**Purpose**: Validate and resolve entity references (trip/path/route)

**Key Logic**:
1. Skip for actions that don't need targets (list_all_stops, etc.)
2. Check target_trip_id → verify in database
3. If label provided → fuzzy search database
4. Handle multiple matches → ask for clarification

**Input**: `state["target_trip_id"]`, `state["target_label"]`
**Output**: `state["trip_id"]` (verified), `state["trip_label"]`

```python
async def resolve_target(state: Dict) -> Dict:
    action = state["action"]
    
    # Skip for certain actions
    if action in ["list_all_stops", "get_unassigned_vehicles"]:
        return state
    
    # Priority 1: Use target_trip_id from LLM
    llm_trip_id = state.get("target_trip_id")
    if llm_trip_id:
        # Verify in database
        trip = await db.fetchrow("SELECT * FROM daily_trips WHERE trip_id=$1", llm_trip_id)
        if trip:
            state["trip_id"] = trip["trip_id"]
            state["trip_label"] = trip["display_name"]
            return state
    
    # Priority 2: Search by label
    target_label = state.get("target_label")
    if target_label:
        trips = await tool_identify_trip_from_label(target_label)
        if len(trips) == 1:
            state["trip_id"] = trips[0]["trip_id"]
        elif len(trips) > 1:
            state["needs_clarification"] = True
            state["clarify_options"] = trips
    
    return state
```

---

### 4.3 `decision_router`
**Purpose**: Route to appropriate next node based on action type and context

**Routing Logic**:
```
Route 0: Page context check (Block invalid actions)
Route A: Trip found + from_image → suggestion_provider
Route B: Trip not found + image → create_trip_suggester
Route C: Multiple matches → report_result (with clarification)
Route D: Static creation actions → trip_creation_wizard
Route D5: Compound actions → check_consequences
Route E: assign_vehicle with deployment → block with error
Route F: Regular actions → check_consequences
```

**Key Code**:
```python
async def decision_router(state: Dict) -> Dict:
    action = state["action"]
    trip_id = state.get("trip_id")
    current_page = state.get("currentPage")
    
    # Route 0: Page context validation
    if current_page == "manageRoute" and action in BUS_DASHBOARD_ACTIONS:
        state["message"] = "This action is only available on Bus Dashboard"
        state["next_node"] = "report_result"
        return state
    
    # Route D5: Compound action
    if action == "assign_vehicle_and_driver" and trip_id:
        state["next_node"] = "check_consequences"
        return state
    
    # Route F: Normal actions
    if action in ["cancel_trip", "remove_vehicle", "assign_vehicle"]:
        state["next_node"] = "check_consequences"
        return state
    
    return state
```

---

### 4.4 `check_consequences`
**Purpose**: Analyze impact of risky actions, determine if confirmation needed

**Categories**:
- **SAFE_ACTIONS**: Execute immediately (get_*, list_*, create_*, assign_driver)
- **RISKY_ACTIONS**: Need consequence check (cancel_trip, remove_vehicle, etc.)

**Key Logic**:
```python
async def check_consequences(state: Dict) -> Dict:
    action = state["action"]
    
    # Safe actions bypass
    if action in SAFE_ACTIONS:
        state["needs_confirmation"] = False
        return state
    
    # Risky actions - analyze impact
    trip_id = state["trip_id"]
    bookings = await tool_get_bookings(trip_id)
    
    state["consequences"] = {
        "booking_count": len(bookings),
        "has_passengers": len(bookings) > 0
    }
    
    # Require confirmation if passengers affected
    if len(bookings) > 0:
        state["needs_confirmation"] = True
        state["message"] = f"⚠️ This trip has {len(bookings)} bookings. Proceed?"
    
    return state
```

---

### 4.5 `get_confirmation`
**Purpose**: Prepare confirmation request for frontend

**Logic**:
```python
async def get_confirmation(state: Dict) -> Dict:
    # Save pending action to database
    await db.execute("""
        INSERT INTO agent_sessions (session_id, pending_action, status)
        VALUES ($1, $2, 'PENDING')
    """, session_id, json.dumps(pending_action))
    
    state["status"] = "awaiting_confirmation"
    state["confirmation_required"] = True
    return state
```

---

### 4.6 `execute_action`
**Purpose**: Perform the actual database operation

**Handles 40+ actions**:
```python
async def execute_action(state: Dict) -> Dict:
    action = state["action"]
    
    if action == "assign_vehicle":
        result = await tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id)
        state["message"] = "Vehicle assigned successfully"
    
    elif action == "cancel_trip":
        result = await tool_cancel_trip(trip_id)
        state["message"] = "Trip cancelled"
    
    elif action == "assign_vehicle_and_driver":
        # Compound action - both in one
        vehicle = await db.fetchrow("SELECT * FROM vehicles WHERE registration_number=$1", reg)
        driver = await db.fetchrow("SELECT * FROM drivers WHERE name ILIKE $1", name)
        result = await tool_assign_vehicle(trip_id, vehicle["vehicle_id"], driver["driver_id"], user_id)
        state["message"] = f"Assigned {reg} and {driver['name']} to trip {trip_id}"
    
    elif action == "add_vehicle":
        # Wizard flow
        if state["wizard_step"] == 0:
            state["message"] = "What type of vehicle? (bus/van/car)"
            state["wizard_step"] = 1
        elif state["wizard_step"] == 1:
            # ... continue wizard
    
    state["status"] = "executed"
    return state
```

---

### 4.7 `report_result`
**Purpose**: Format final response for frontend

**Output Structure**:
```python
final_output = {
    "action": "assign_vehicle",
    "trip_id": 42,
    "status": "executed",
    "message": "Vehicle assigned successfully",
    "success": True,
    "needs_confirmation": False,
    "suggestions": [],  # For suggestion_provider
    "options": [],      # For vehicle/driver selection
}
```

---

### 4.8 `suggestion_provider`
**Purpose**: Provide action suggestions based on trip state

```python
async def suggestion_provider(state: Dict) -> Dict:
    trip_id = state["trip_id"]
    trip = await tool_get_trip_details(trip_id)
    
    suggestions = []
    if not trip.get("vehicle_id"):
        suggestions.append({"action": "assign_vehicle", "label": "Assign a vehicle"})
    if not trip.get("driver_id"):
        suggestions.append({"action": "assign_driver", "label": "Assign a driver"})
    
    state["suggestions"] = suggestions
    return state
```

---

### 4.9 `vehicle_selection_provider` / `driver_selection_provider`
**Purpose**: Fetch available vehicles/drivers for selection

```python
async def vehicle_selection_provider(state: Dict) -> Dict:
    vehicles = await tool_get_unassigned_vehicles()
    state["options"] = vehicles
    state["selection_type"] = "vehicle"
    state["awaiting_selection"] = True
    return state
```

---

## 5. Action Flows - Complete Examples

### Flow 1: Simple Action (assign_driver)
```
User: "Assign driver John to trip 42"

1. parse_intent_llm:
   → action = "assign_driver"
   → target_trip_id = 42
   → parsed_params = {"driver_name": "John"}

2. resolve_target:
   → Verify trip 42 exists
   → trip_id = 42, trip_label = "Path-1 - 08:00"

3. decision_router:
   → assign_driver is not blocked on any page
   → next_node = "check_consequences"

4. check_consequences:
   → assign_driver is SAFE_ACTION
   → needs_confirmation = False

5. execute_action:
   → Look up driver "John" in database
   → Call tool_assign_driver(42, driver_id, user_id)
   → message = "Driver John assigned to trip 42"

6. report_result:
   → Format final_output
   → Return to frontend
```

### Flow 2: Risky Action (remove_vehicle)
```
User: "Remove vehicle from trip 42"

1. parse_intent_llm:
   → action = "remove_vehicle"
   → target_trip_id = 42

2. resolve_target:
   → trip_id = 42

3. decision_router:
   → next_node = "check_consequences"

4. check_consequences:
   → remove_vehicle is RISKY_ACTION
   → Check bookings: found 5 passengers
   → needs_confirmation = True
   → message = "⚠️ This trip has 5 passengers. Proceed?"

5. get_confirmation:
   → Save to agent_sessions
   → status = "awaiting_confirmation"
   → session_id = "abc-123"

6. report_result:
   → Return confirmation request to frontend

--- User confirms ---

7. /api/agent/confirm {session_id: "abc-123", confirmed: true}
   → Load pending_action from database
   → Execute remove_vehicle
   → Return success
```

### Flow 3: Compound Action (assign_vehicle_and_driver)
```
User: "Assign vehicle MH-12-7777 and driver John Snow to trip 42"

1. parse_intent_llm:
   → action = "assign_vehicle_and_driver"
   → target_trip_id = 42
   → parsed_params = {
       "vehicle_registration": "MH-12-7777",
       "driver_name": "John Snow"
     }

2. resolve_target:
   → trip_id = 42

3. decision_router:
   → Route D5: compound action
   → next_node = "check_consequences"

4. check_consequences:
   → assign_vehicle_and_driver is SAFE_ACTION
   → needs_confirmation = False

5. execute_action:
   → Look up vehicle by registration
   → Look up driver by name
   → Call tool_assign_vehicle(42, vehicle_id, driver_id, user_id)
   → message = "✅ Assigned MH-12-7777 and John Snow to trip 42"

6. report_result:
   → Return success
```

### Flow 4: Wizard Flow (add_vehicle)
```
User: "Add a new vehicle TN-01-AB-1234"

1. parse_intent_llm:
   → action = "add_vehicle"
   → parsed_params = {"vehicle_registration": "TN-01-AB-1234"}

2. resolve_target:
   → add_vehicle doesn't need target resolution
   → Skip

3. decision_router:
   → Fleet management action
   → next_node = "check_consequences"

4. check_consequences:
   → add_vehicle is SAFE_ACTION
   → next_node = "execute_action"

5. execute_action (Step 0):
   → wizard_step = 0
   → wizard_data = {"registration": "TN-01-AB-1234"}
   → message = "What type of vehicle? (bus/van/car)"
   → wizard_active = True, wizard_step = 1

6. report_result:
   → Return wizard prompt

--- User responds: "bus" ---

7. New request with session_id
   → parse_intent_llm detects wizard_active
   → next_node = "execute_action"

8. execute_action (Step 1):
   → wizard_data["vehicle_type"] = "bus"
   → message = "What's the seating capacity?"
   → wizard_step = 2

--- User responds: "40" ---

9. execute_action (Step 2):
   → wizard_data["capacity"] = 40
   → Create vehicle in database
   → message = "✅ Vehicle TN-01-AB-1234 (bus, 40 seats) added!"
   → wizard_active = False
```

---

## 6. Database Schema

### Key Tables:
```sql
-- Trips (daily schedule)
daily_trips (
    trip_id SERIAL PRIMARY KEY,
    route_id INT REFERENCES routes(route_id),
    display_name TEXT,
    trip_date DATE,
    live_status TEXT  -- SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
)

-- Deployments (vehicle+driver assignments)
deployments (
    deployment_id SERIAL PRIMARY KEY,
    trip_id INT REFERENCES daily_trips(trip_id),
    vehicle_id INT REFERENCES vehicles(vehicle_id),
    driver_id INT REFERENCES drivers(driver_id)
)

-- Vehicles
vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    registration_number TEXT UNIQUE,
    vehicle_type TEXT,  -- bus, van, car
    capacity INT,
    status TEXT  -- ACTIVE, BLOCKED, MAINTENANCE
)

-- Drivers
drivers (
    driver_id SERIAL PRIMARY KEY,
    name TEXT,
    phone TEXT,
    license_number TEXT,
    status TEXT  -- AVAILABLE, ON_DUTY, OFF_DUTY
)

-- Bookings (passengers)
bookings (
    booking_id SERIAL PRIMARY KEY,
    trip_id INT REFERENCES daily_trips(trip_id),
    passenger_name TEXT,
    pickup_stop_id INT,
    dropoff_stop_id INT
)

-- Agent Sessions (for confirmation flows)
agent_sessions (
    session_id TEXT PRIMARY KEY,
    pending_action JSONB,
    conversation_history JSONB,
    status TEXT,  -- PENDING, CONFIRMED, CANCELLED
    created_at TIMESTAMP
)
```

---

## 7. How to Create a New Node

### Step 1: Create the Node Function
```python
# backend/langgraph/nodes/my_new_node.py
from typing import Dict
import logging

logger = logging.getLogger(__name__)

async def my_new_node(state: Dict) -> Dict:
    """
    Description of what this node does.
    
    Args:
        state: Graph state dictionary
        
    Returns:
        Updated state dictionary
    """
    logger.info(f"[MY_NODE] Processing action: {state.get('action')}")
    
    # Your logic here
    some_value = state.get("some_input")
    
    # Do something
    result = process_something(some_value)
    
    # Update state
    state["my_output"] = result
    state["next_node"] = "next_node_name"  # If needed
    
    return state
```

### Step 2: Register in `__init__.py`
```python
# backend/langgraph/nodes/__init__.py
from .my_new_node import my_new_node
```

### Step 3: Add to Graph
```python
# backend/langgraph/graph_def.py

# Import
from langgraph.nodes.my_new_node import my_new_node

# Register node
graph.add_node("my_new_node", my_new_node)

# Add edges
graph.add_edge(
    "some_previous_node", 
    "my_new_node",
    condition=lambda s: s.get("some_condition")
)

graph.add_edge("my_new_node", "next_node")
```

### Step 4: Update Other Nodes (if needed)
If your node is reached via decision_router:
```python
# backend/langgraph/nodes/decision_router.py

if action == "my_new_action":
    state["next_node"] = "my_new_node"
    return state
```

---

## 8. Common Interview Questions

### Q1: "Explain the overall architecture"
**Answer**: MOVI uses a **state-machine architecture** powered by LangGraph. User input enters through FastAPI, flows through a series of **nodes** that transform a state dictionary, and produces a final response. The key insight is that nodes are pure functions that take state and return updated state, making the system easy to test and extend.

### Q2: "How does the LLM integration work?"
**Answer**: We use **Google Gemini 1.5 Flash** for natural language parsing. The LLM receives:
1. A detailed system prompt with action definitions
2. The user's text
3. Context (selectedTripId, currentPage)

It returns structured JSON with action type, parameters, and confidence. We also have a **fallback regex parser** for common patterns in case LLM fails.

### Q3: "How do you handle risky actions?"
**Answer**: Actions are categorized as SAFE or RISKY. RISKY actions (like remove_vehicle, cancel_trip) go through `check_consequences` which:
1. Checks for bookings/passengers
2. Sets `needs_confirmation = True`
3. Saves to `agent_sessions` table
4. Returns confirmation prompt

When user confirms, we load the pending action and execute it.

### Q4: "How would you add a new action?"
**Answer**:
1. Add action to LLM prompt in `llm_client.py`
2. Add to ACTION_REGISTRY for validation
3. Add handler in `execute_action.py`
4. Add to SAFE_ACTIONS or RISKY_ACTIONS in `check_consequences.py`
5. If needed, add routing in `decision_router.py`

### Q5: "What is the purpose of decision_router?"
**Answer**: It's the **traffic controller** of the graph. Based on:
- Action type
- Page context (tribal knowledge)
- Resolution status
- OCR flow detection

It decides which node to execute next. This keeps routing logic centralized and easy to modify.

### Q6: "How does context-awareness work?"
**Answer**: Frontend sends `selectedTripId` with each request. In `parse_intent_llm`, if user says "this trip" or "assign vehicle" while a trip is selected, we use that context directly without LLM. This provides:
1. Faster response (no LLM call)
2. Higher accuracy (no hallucination risk)
3. Better UX (natural conversation)

### Q7: "Explain the wizard flow"
**Answer**: Wizards are multi-step interactions stored in `agent_sessions.pending_action`:
```python
{
    "wizard_active": True,
    "wizard_type": "add_vehicle",
    "wizard_step": 1,
    "wizard_data": {"registration": "TN-01-AB-1234"}
}
```
Each step updates `wizard_data` and increments `wizard_step`. When complete, the final action is executed.

### Q8: "How would you debug an issue?"
**Answer**:
1. Check logs (each node logs entry/exit)
2. Trace state through nodes
3. Use the test scripts in `/backend/test_*.py`
4. Check database for saved sessions
5. Use `/api/debug/*` endpoints for internal state

### Q9: "What's the difference between tool and node?"
**Answer**:
- **Tools** (`tools.py`, `llm_client.py`): Database operations, LLM calls, pure functions
- **Nodes** (`nodes/*.py`): Graph vertices, receive/return state, orchestration logic

Nodes USE tools to do work.

### Q10: "How do you ensure reliability?"
**Answer**:
1. **Max iterations limit** in runtime (prevents infinite loops)
2. **Error handling** in each node (goes to fallback)
3. **Action validation** (reject unknown actions)
4. **Page context validation** (tribal knowledge)
5. **Session persistence** (resume interrupted flows)

---

## Quick Reference Card

### Graph Flow
```
parse_intent → resolve_target → decision_router → check_consequences → execute_action → report_result
                                       ↓
                           suggestion_provider
                           vehicle_selection_provider
                           driver_selection_provider
                           trip_creation_wizard
```

### Key State Fields
| Field | Set By | Used By |
|-------|--------|---------|
| `text` | Input | parse_intent |
| `action` | parse_intent | All nodes |
| `target_trip_id` | parse_intent | resolve_target |
| `trip_id` | resolve_target | execute_action |
| `needs_confirmation` | check_consequences | get_confirmation |
| `next_node` | decision_router | runtime |
| `final_output` | report_result | Response |

### Action Categories
- **40 BUS_DASHBOARD_ACTIONS**: Trip/Vehicle/Driver management
- **15 MANAGE_ROUTE_ACTIONS**: Stop/Path/Route configuration
- **SAFE_ACTIONS**: No confirmation needed
- **RISKY_ACTIONS**: Confirmation required

---

Good luck with your interview! 🚀
