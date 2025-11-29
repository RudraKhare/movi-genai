# 🧠 MOVI AI Agent Architecture - Complete Guide

## Table of Contents
1. [What is an AI Agent?](#1-what-is-an-ai-agent)
2. [LangGraph Framework](#2-langgraph-framework)
3. [The Graph Structure](#3-the-graph-structure)
4. [State Management](#4-state-management)
5. [Node Deep Dives](#5-node-deep-dives)
6. [LLM Integration](#6-llm-integration)
7. [Tools Layer](#7-tools-layer)
8. [Conversation Flow Examples](#8-conversation-flow-examples)
9. [Interview Q&A](#9-interview-qa)

---

## 1. What is an AI Agent?

### Traditional Chatbot vs AI Agent

```
TRADITIONAL CHATBOT:
User → "Cancel trip 42" → IF-ELSE Logic → Response
       (Hardcoded patterns, no reasoning)

AI AGENT:
User → "Cancel this trip" → [Parse Intent] → [Resolve Target] → [Check Consequences] 
                                ↓                   ↓                    ↓
                            Uses LLM          Queries DB           Analyzes Impact
                                ↓                   ↓                    ↓
                         [Get Confirmation] → [Execute Action] → [Report Result]
                               ↓                    ↓                   ↓
                          Asks User            Updates DB         Returns Summary
```

### Key Differences:
| Aspect | Chatbot | AI Agent |
|--------|---------|----------|
| Understanding | Pattern matching | LLM reasoning |
| Context | Stateless | Maintains state |
| Actions | Fixed responses | Executes real operations |
| Reasoning | None | Multi-step reasoning |
| Error Handling | Generic | Context-aware |

---

## 2. LangGraph Framework

LangGraph is a framework for building **stateful, multi-step AI applications**. Think of it as:

```
LangGraph = State Machine + LLM + Tools
```

### Core Components:

```python
# 1. GRAPH - The workflow definition
class Graph:
    def __init__(self, name):
        self.nodes = {}     # Functions to execute
        self.edges = {}     # Transitions between nodes
    
    def add_node(name, function):
        """Register a processing step"""
        
    def add_edge(from_node, to_node, condition):
        """Define when to transition"""

# 2. STATE - The data flowing through
state = {
    "text": "Cancel trip 42",        # User input
    "action": "cancel_trip",          # Parsed intent
    "trip_id": 42,                    # Resolved target
    "consequences": {...},            # Impact analysis
    "confirmed": True,                # User decision
    "result": {...},                  # Execution result
}

# 3. NODES - Individual processing steps
async def parse_intent(state):
    """Extract what user wants"""
    # Uses LLM to understand natural language
    return updated_state

# 4. RUNTIME - Executes the graph
async def run(input_state):
    current = "start_node"
    while current:
        state = await execute_node(current, state)
        current = get_next_node(current, state)
    return state
```

---

## 3. The Graph Structure

### Your MOVI Agent Graph (Visual):

```
                                    ┌──────────────────┐
                                    │   User Input     │
                                    └────────┬─────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PARSE_INTENT (LLM)                                │
│  • Understands natural language ("cancel this trip")                        │
│  • Extracts action type, target, parameters                                 │
│  • Handles context (selectedTripId from UI)                                 │
│  • Supports wizards (multi-step flows)                                      │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESOLVE_TARGET (DB)                               │
│  • Converts "Bulk - 00:01" → trip_id=42                                    │
│  • Queries database to find actual entities                                 │
│  • Handles multiple matches (asks for clarification)                        │
│  • Validates that target exists                                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DECISION_ROUTER (Logic)                              │
│  • Routes to different paths based on:                                      │
│    - Page context (Bus Dashboard vs Manage Route)                          │
│    - OCR flow vs text command                                               │
│    - Action type (safe vs risky)                                           │
│    - Need for user selection                                                │
└───────┬─────────┬─────────┬─────────┬─────────┬─────────┬──────────────────┘
        │         │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼         ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │SUGGEST │ │VEHICLE │ │DRIVER  │ │CREATE  │ │CHECK   │ │TRIP    │
   │PROVIDER│ │SELECT  │ │SELECT  │ │TRIP    │ │CONSEQ  │ │WIZARD  │
   └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
        │         │         │         │         │         │
        └─────────┴─────────┴─────────┴────┬────┴─────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CHECK_CONSEQUENCES (Analysis)                          │
│  • Analyzes impact of action:                                               │
│    - How many bookings affected?                                            │
│    - Is trip in progress?                                                   │
│    - Are there conflicts?                                                   │
│  • Categorizes: SAFE (skip confirm) vs RISKY (need confirm)                │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │ RISKY?                  │ SAFE?
                        ▼                         ▼
┌─────────────────────────────┐      ┌─────────────────────────────┐
│    GET_CONFIRMATION         │      │     (Skip to Execute)       │
│  • Shows warning to user    │      └──────────────┬──────────────┘
│  • "This will affect 5      │                     │
│     bookings. Proceed?"     │                     │
│  • Waits for Yes/No         │                     │
└──────────────┬──────────────┘                     │
               │ (If confirmed)                     │
               └────────────────────┬───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXECUTE_ACTION (Tools)                               │
│  • Calls actual database operations                                         │
│  • Updates trips, vehicles, drivers, bookings                              │
│  • Returns success/failure result                                           │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REPORT_RESULT (Response)                             │
│  • Formats response for user                                                │
│  • Includes action summary, affected entities                              │
│  • Returns to frontend                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Code Location:
```
backend/langgraph/
├── graph_def.py      # Graph definition, nodes & edges
├── runtime.py        # Execution engine
├── nodes/            # Individual processing steps
│   ├── parse_intent.py
│   ├── parse_intent_llm.py
│   ├── resolve_target.py
│   ├── decision_router.py
│   ├── check_consequences.py
│   ├── execute_action.py
│   ├── report_result.py
│   └── ... (more specialized nodes)
└── tools/            # Database operations
    ├── llm_client.py
    └── ... 
```

---

## 4. State Management

The **state** is a Python dictionary that flows through all nodes. Each node reads and writes to it.

### State Schema:

```python
state = {
    # === INPUT (from frontend) ===
    "text": str,                    # User's message
    "selectedTripId": int | None,   # Trip selected in UI (for context)
    "currentPage": str,             # "busDashboard" or "manageRoute"
    "from_image": bool,             # True if came from OCR scan
    "session_id": str,              # For conversation continuity
    
    # === PARSE_INTENT OUTPUT ===
    "action": str,                  # "cancel_trip", "assign_vehicle", etc.
    "target_label": str | None,     # "Bulk - 00:01" (text from user)
    "target_time": str | None,      # "08:30" (extracted time)
    "confidence": float,            # 0.0 - 1.0 (LLM confidence)
    "needs_clarification": bool,    # True if LLM unsure
    "clarify_options": List[str],   # Suggestions if clarification needed
    "parsed_params": Dict,          # Extracted parameters
    
    # === RESOLVE_TARGET OUTPUT ===
    "trip_id": int | None,          # Resolved database ID
    "route_id": int | None,
    "path_id": int | None,
    "resolve_result": str,          # "found", "multiple", "none"
    
    # === DECISION_ROUTER OUTPUT ===
    "next_node": str,               # Where to go next
    
    # === CHECK_CONSEQUENCES OUTPUT ===
    "consequences": Dict,           # Impact analysis
    "needs_confirmation": bool,     # True for risky actions
    "warning_messages": List[str],  # Warnings to show user
    
    # === EXECUTE_ACTION OUTPUT ===
    "result": Dict,                 # Operation result
    "success": bool,
    
    # === REPORT_RESULT OUTPUT ===
    "message": str,                 # Final response text
    "final_output": Dict,           # Structured response
    "status": str,                  # "completed", "failed", "needs_confirmation"
    
    # === WIZARD STATE (for multi-step flows) ===
    "wizard_active": bool,
    "wizard_type": str,             # "add_vehicle", "create_trip", etc.
    "wizard_step": int,
    "wizard_data": Dict,            # Accumulated data
}
```

### State Flow Example:

```python
# User types: "Cancel trip Bulk - 08:30"

# After PARSE_INTENT:
state = {
    "text": "Cancel trip Bulk - 08:30",
    "action": "cancel_trip",
    "target_label": "Bulk - 08:30",
    "target_time": "08:30",
    "confidence": 0.95,
}

# After RESOLVE_TARGET:
state = {
    ...
    "trip_id": 42,
    "resolve_result": "found",
}

# After CHECK_CONSEQUENCES:
state = {
    ...
    "consequences": {
        "booking_count": 5,
        "has_deployment": True,
        "live_status": "SCHEDULED"
    },
    "needs_confirmation": True,
    "warning_messages": ["This trip has 5 active bookings"]
}

# After user confirms and EXECUTE_ACTION:
state = {
    ...
    "result": {"ok": True, "cancelled_trip_id": 42},
    "success": True,
}

# After REPORT_RESULT:
state = {
    ...
    "message": "✅ Trip 'Bulk - 08:30' cancelled successfully. 5 bookings were also cancelled.",
    "status": "completed"
}
```

---

## 5. Node Deep Dives

### 5.1 PARSE_INTENT_LLM

**Purpose**: Understand what the user wants using LLM.

```python
# Location: backend/langgraph/nodes/parse_intent_llm.py

async def parse_intent_llm(state: Dict) -> Dict:
    """
    Uses LLM (Gemini/OpenAI) to parse natural language input.
    
    Flow:
    1. Check if wizard is active → route to wizard
    2. Check if context reference ("this trip") + selectedTripId → use context
    3. Check for structured commands (from UI buttons)
    4. Call LLM with text + context
    5. Extract action, target, parameters
    """
    
    text = state.get("text", "").lower()
    selected_trip_id = state.get("selectedTripId")
    
    # CONTEXT AWARENESS: If user says "this trip" and we have selectedTripId
    if selected_trip_id and any(ref in text for ref in ["this trip", "this", "here"]):
        # Skip LLM, use context directly
        state["action"] = detect_action(text)  # "assign_vehicle", etc.
        state["target_trip_id"] = selected_trip_id
        state["confidence"] = 0.95
        return state
    
    # Call LLM for complex parsing
    llm_response = await parse_intent_with_llm(text, context)
    
    # Merge LLM output
    state["action"] = llm_response["action"]
    state["target_label"] = llm_response["target_label"]
    state["confidence"] = llm_response["confidence"]
    state["needs_clarification"] = llm_response.get("clarify", False)
    
    return state
```

**Key Concept - LLM System Prompt**:

The LLM is given a detailed system prompt that teaches it:
- All possible actions (40+ actions!)
- How to extract parameters
- Natural language patterns ("cancel this" → cancel_trip)
- Context awareness rules
- When to ask for clarification

### 5.2 RESOLVE_TARGET

**Purpose**: Convert human-readable labels to database IDs.

```python
# Location: backend/langgraph/nodes/resolve_target.py

async def resolve_target(state: Dict) -> Dict:
    """
    Resolves "Bulk - 08:30" → trip_id=42
    
    Priority Order:
    1. selectedTripId (from UI/OCR) - highest priority
    2. target_trip_id (from LLM)
    3. target_time (time-based search)
    4. target_label (text search)
    """
    
    action = state.get("action")
    
    # Skip for actions that don't need resolution
    if action in ["list_all_stops", "get_unassigned_vehicles", ...]:
        return state
    
    # Priority 1: Use UI context
    if state.get("target_trip_id"):
        trip_id = state["target_trip_id"]
        # Verify it exists in DB
        trip = await verify_trip_exists(trip_id)
        if trip:
            state["trip_id"] = trip_id
            state["resolve_result"] = "found"
            return state
    
    # Priority 2: Search by label
    target_label = state.get("target_label")
    if target_label:
        trips = await tool_identify_trip_from_label(target_label)
        
        if len(trips) == 1:
            state["trip_id"] = trips[0]["trip_id"]
            state["resolve_result"] = "found"
        elif len(trips) > 1:
            state["resolve_result"] = "multiple"
            state["matches"] = trips  # Let user choose
        else:
            state["resolve_result"] = "none"
            state["error"] = "trip_not_found"
    
    return state
```

### 5.3 DECISION_ROUTER

**Purpose**: Route to the correct next step based on context.

```python
# Location: backend/langgraph/nodes/decision_router.py

# Page-Context Mapping (Tribal Knowledge)
BUS_DASHBOARD_ACTIONS = {
    "assign_vehicle", "assign_driver", "cancel_trip", 
    "get_trip_status", "add_bookings", ...  # 40 actions
}

MANAGE_ROUTE_ACTIONS = {
    "create_stop", "create_path", "create_route",
    "delete_stop", ...  # 15 actions
}

async def decision_router(state: Dict) -> Dict:
    """
    Routes based on:
    1. Page context (prevent wrong actions on wrong page)
    2. OCR flow (show suggestions after scan)
    3. Action type (safe vs risky)
    4. Resolution status (found vs not found)
    """
    
    action = state["action"]
    current_page = state.get("currentPage")
    
    # ROUTE 0: Page Context Validation
    if current_page == "manageRoute" and action in BUS_DASHBOARD_ACTIONS:
        state["next_node"] = "report_result"
        state["message"] = "⚠️ This action is only available on Bus Dashboard"
        return state
    
    # ROUTE 1: OCR Image Flow
    if state.get("from_image") and state.get("trip_id"):
        state["next_node"] = "suggestion_provider"  # Show action buttons
        return state
    
    # ROUTE 2: Vehicle Selection Flow
    if action == "assign_vehicle" and not state.get("vehicle_id"):
        state["next_node"] = "vehicle_selection_provider"
        return state
    
    # ROUTE 3: Normal Flow
    state["next_node"] = "check_consequences"
    return state
```

### 5.4 CHECK_CONSEQUENCES

**Purpose**: Analyze impact before executing risky actions.

```python
# Location: backend/langgraph/nodes/check_consequences.py

SAFE_ACTIONS = ["get_trip_status", "list_all_stops", ...]  # Read-only
RISKY_ACTIONS = ["cancel_trip", "remove_vehicle", ...]     # Affect data

async def check_consequences(state: Dict) -> Dict:
    """
    For RISKY actions:
    1. Get current trip status
    2. Count affected bookings
    3. Check if trip is in progress
    4. Build warning messages
    """
    
    action = state["action"]
    
    if action in SAFE_ACTIONS:
        state["needs_confirmation"] = False
        return state
    
    trip_id = state["trip_id"]
    
    # Get impact data
    trip_status = await tool_get_trip_status(trip_id)
    bookings = await tool_get_bookings(trip_id)
    
    consequences = {
        "booking_count": len(bookings),
        "live_status": trip_status.get("live_status"),
        "has_vehicle": bool(trip_status.get("vehicle_id")),
    }
    
    state["consequences"] = consequences
    
    # Build warnings
    warnings = []
    if action == "cancel_trip":
        warnings.append(f"⚠️ Cancelling will affect {len(bookings)} bookings")
        if trip_status["live_status"] == "IN_PROGRESS":
            warnings.append("⚠️ Trip is currently IN PROGRESS!")
    
    state["warning_messages"] = warnings
    state["needs_confirmation"] = len(warnings) > 0
    
    return state
```

### 5.5 EXECUTE_ACTION

**Purpose**: Actually perform the operation.

```python
# Location: backend/langgraph/nodes/execute_action.py

async def execute_action(state: Dict) -> Dict:
    """
    Executes the action using tool functions.
    Handles 40+ different actions.
    """
    
    action = state["action"]
    
    if action == "cancel_trip":
        result = await tool_cancel_trip(
            trip_id=state["trip_id"],
            user_id=state.get("user_id", 1)
        )
        state["result"] = result
        state["success"] = result.get("ok", False)
        
    elif action == "assign_vehicle":
        result = await tool_assign_vehicle(
            trip_id=state["trip_id"],
            vehicle_id=state.get("vehicle_id"),
            user_id=state.get("user_id", 1)
        )
        state["result"] = result
        state["success"] = result.get("ok", False)
    
    # ... 38 more actions ...
    
    return state
```

---

## 6. LLM Integration

### LLM Client Architecture:

```python
# Location: backend/langgraph/tools/llm_client.py

# Supports multiple providers
PROVIDERS = ["gemini", "openai", "ollama"]

async def parse_intent_with_llm(text: str, context: Dict) -> Dict:
    """
    Calls LLM to parse natural language into structured action.
    """
    
    # Build prompt with context
    prompt = f"""
    User message: {text}
    Context: {json.dumps(context)}
    
    Parse this into a structured action.
    """
    
    # Try providers in order
    for provider in PROVIDERS:
        try:
            if provider == "gemini":
                response = await call_gemini(prompt)
            elif provider == "openai":
                response = await call_openai(prompt)
            else:
                response = await call_ollama(prompt)
            
            return parse_json_response(response)
        except Exception as e:
            logger.warning(f"{provider} failed: {e}")
            continue
    
    # Fallback if all fail
    return {"action": "unknown", "clarify": True}
```

### System Prompt (The Magic):

The system prompt is ~200 lines that teaches the LLM:

```python
SYSTEM_PROMPT = """
You are MoviAgent's intelligent intent parser.

ACTIONS:
- cancel_trip: "cancel", "abort", "stop trip"
- assign_vehicle: "assign vehicle", "put bus on", "deploy"
- assign_driver: "assign driver", "add driver"
...

CONTEXT RULES:
- If selectedTripId exists, use it as target
- If user says "this trip", map to selectedTripId
...

PARAMETER EXTRACTION:
- Extract vehicle_registration from "Bus 123"
- Extract driver_name from "driver John"
...

OUTPUT FORMAT:
{
    "action": "cancel_trip",
    "target_trip_id": 42,
    "confidence": 0.95,
    "explanation": "User wants to cancel trip 42"
}
"""
```

---

## 7. Tools Layer

Tools are the bridge between the agent and the database.

### Tool Pattern:

```python
# Location: backend/langgraph/tools.py

async def tool_cancel_trip(trip_id: int, user_id: int) -> Dict:
    """
    Cancel a trip and all its bookings.
    
    Args:
        trip_id: Trip to cancel
        user_id: Who is performing the action (audit)
    
    Returns:
        {"ok": True, "message": "..."} or {"ok": False, "error": "..."}
    """
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Update trip status
                await conn.execute("""
                    UPDATE daily_trips 
                    SET live_status = 'CANCELLED'
                    WHERE trip_id = $1
                """, trip_id)
                
                # Cancel all bookings
                await conn.execute("""
                    UPDATE bookings 
                    SET status = 'CANCELLED'
                    WHERE trip_id = $1
                """, trip_id)
                
                # Log audit trail
                await conn.execute("""
                    INSERT INTO audit_log (action, trip_id, user_id)
                    VALUES ('CANCEL_TRIP', $1, $2)
                """, trip_id, user_id)
        
        return {"ok": True, "message": f"Trip {trip_id} cancelled"}
        
    except Exception as e:
        logger.error(f"Cancel trip failed: {e}")
        return {"ok": False, "error": str(e)}
```

### Tool Categories:

| Category | Examples |
|----------|----------|
| READ | `tool_get_trip_status`, `tool_get_bookings` |
| MUTATE | `tool_cancel_trip`, `tool_assign_vehicle` |
| SEARCH | `tool_identify_trip_from_label`, `tool_search_driver` |
| CREATE | `tool_create_stop`, `tool_create_path` |

---

## 8. Conversation Flow Examples

### Example 1: Simple Cancel Trip

```
User: "Cancel trip Bulk - 08:30"

┌─────────────────────────────────────────────────────────────────┐
│ PARSE_INTENT_LLM                                                │
│ Input: "Cancel trip Bulk - 08:30"                              │
│ Output: action=cancel_trip, target_label="Bulk - 08:30"        │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESOLVE_TARGET                                                  │
│ Search: "Bulk - 08:30" → Found trip_id=42                      │
│ Output: trip_id=42, resolve_result="found"                     │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ DECISION_ROUTER                                                 │
│ Action: cancel_trip (risky) → route to check_consequences      │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHECK_CONSEQUENCES                                              │
│ Trip 42: 5 bookings, SCHEDULED status                          │
│ Warning: "This will cancel 5 bookings"                         │
│ needs_confirmation = True                                       │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ REPORT_RESULT (asks for confirmation)                          │
│ Response: "⚠️ Cancel trip 'Bulk - 08:30'?                      │
│           This will affect 5 bookings. Proceed?"               │
│           [Yes] [No]                                            │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
                    User clicks [Yes]
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ EXECUTE_ACTION                                                  │
│ Calls: tool_cancel_trip(42, user_id=1)                         │
│ Result: {"ok": True}                                            │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ REPORT_RESULT                                                   │
│ Response: "✅ Trip 'Bulk - 08:30' cancelled successfully.      │
│           5 bookings were also cancelled."                      │
└─────────────────────────────────────────────────────────────────┘
```

### Example 2: OCR Image Flow

```
User: [Uploads image of trip]

┌─────────────────────────────────────────────────────────────────┐
│ OCR (in backend)                                                │
│ Extracts: route="Bulk", time="08:30"                           │
│ Searches DB → Found single match: trip_id=42                   │
│ Sets: from_image=True, selectedTripId=42                       │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ DECISION_ROUTER                                                 │
│ from_image=True, trip_id=42                                    │
│ Route to: suggestion_provider                                   │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ SUGGESTION_PROVIDER                                             │
│ Output: "Found trip 'Bulk - 08:30'. What would you like to do?" │
│         [Assign Vehicle] [Assign Driver] [Cancel Trip]         │
│         [Check Status] [View Bookings] [Get Summary]           │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
              User clicks [Assign Vehicle]
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ VEHICLE_SELECTION_PROVIDER                                      │
│ Gets available vehicles for trip 42's time slot                │
│ Output: "Select a vehicle:"                                    │
│         [🚌 MH-12-1234 (30 seats)]                             │
│         [🚌 MH-12-5678 (45 seats)]                             │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
           User clicks [MH-12-1234]
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ EXECUTE_ACTION                                                  │
│ Calls: tool_assign_vehicle(trip_id=42, vehicle_id=5)          │
│ Result: {"ok": True, "vehicle": "MH-12-1234"}                  │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ REPORT_RESULT                                                   │
│ Response: "✅ Vehicle MH-12-1234 assigned to trip 'Bulk-08:30'" │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Interview Q&A

### Q1: "Explain your AI agent architecture"

**Answer:**
"Our MOVI agent uses a **LangGraph-based state machine architecture** with 6 core nodes:

1. **Parse Intent (LLM)** - Uses Gemini/OpenAI to understand natural language. It handles context-awareness, extracting actions like 'cancel trip' from vague inputs like 'cancel this'.

2. **Resolve Target (DB)** - Converts human labels to database IDs. 'Bulk - 08:30' becomes trip_id=42.

3. **Decision Router** - Routes to different flows based on context: OCR flow, selection UI, or direct execution.

4. **Check Consequences** - For risky actions, analyzes impact. 'Cancel this trip' with 5 bookings triggers a confirmation.

5. **Execute Action** - Performs the actual DB operation using tool functions.

6. **Report Result** - Formats and returns the response.

State flows through all nodes, accumulating information until we can execute or need clarification."

### Q2: "How does LLM integrate with the agent?"

**Answer:**
"The LLM is the 'brain' in the parse_intent node. We:

1. Send user text + context (selected trip, current page) to the LLM
2. Use a detailed system prompt (200+ lines) teaching it our 40 actions
3. Get structured JSON back: action, target, confidence, parameters
4. Fall back to regex parsing if LLM fails

We support multiple providers (Gemini primary, OpenAI fallback) for reliability. The LLM handles:
- Natural language understanding
- Context awareness ('this trip' → selectedTripId)
- Parameter extraction
- Confidence scoring"

### Q3: "What's the difference between your agent and a chatbot?"

**Answer:**
"Three key differences:

1. **Stateful**: We maintain state across the conversation. Each node adds to a shared state dict.

2. **Reasoned Actions**: We don't just respond - we analyze consequences. Before canceling a trip, we check bookings, status, and warn the user.

3. **Real Operations**: We execute actual database operations through tool functions, not just chat responses.

A chatbot might say 'Trip cancelled'. Our agent actually cancels the trip, updates bookings, logs audit trails, and reports what changed."

### Q4: "How do you handle errors and edge cases?"

**Answer:**
"Multiple layers:

1. **Confidence scoring**: LLM returns confidence. Below 0.6, we ask for clarification.

2. **Resolution fallback**: If 'Bulk - 08:30' matches multiple trips, we show options.

3. **Page context validation**: Can't run trip actions on Manage Route page - we block it.

4. **Consequence checks**: Risky actions require confirmation.

5. **Wizard flows**: Complex operations (create trip) become multi-step wizards.

6. **Fallback node**: Any unhandled error goes to fallback with helpful message."

### Q5: "How would you add a new action?"

**Answer:**
"Four steps:

1. **Add tool function** in `tools.py`:
```python
async def tool_my_action(trip_id: int) -> Dict:
    # Database operation
```

2. **Update LLM prompt** in `llm_client.py`:
```python
# Add to SYSTEM_PROMPT:
# "my action", "do my thing" → action="my_action"
```

3. **Add handler** in `execute_action.py`:
```python
elif action == "my_action":
    result = await tool_my_action(state["trip_id"])
```

4. **Add routing** if needed in `decision_router.py`:
```python
if action == "my_action":
    state["next_node"] = "check_consequences"
```

We did this for `get_trip_summary` as a tutorial example."

---

## Summary: The Big Picture

```
┌────────────────────────────────────────────────────────────────────┐
│                         MOVI AI AGENT                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│  │   LLM    │    │  STATE   │    │  GRAPH   │    │  TOOLS   │    │
│  │ (Brain)  │◄──►│ (Memory) │◄──►│ (Flow)   │◄──►│  (Hands) │    │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    │
│       │                │                │               │          │
│       ▼                ▼                ▼               ▼          │
│  Understands     Tracks context    Routes logic    Executes       │
│  natural         across nodes      to right        database       │
│  language        and turns         handlers        operations     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

This is what makes it an **AI Agent** and not just a chatbot - it's a reasoning system that understands, plans, confirms, executes, and reports.
