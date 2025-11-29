# 🎯 MOVI Deep Technical Interview Questions & Answers

## Table of Contents
1. [LangGraph Core Architecture](#1-langgraph-core-architecture)
2. [Node Deep Dive Questions](#2-node-deep-dive-questions)
3. [LLM Integration Questions](#3-llm-integration-questions)
4. [State Management Questions](#4-state-management-questions)
5. [Database & Tools Questions](#5-database--tools-questions)
6. [Error Handling & Edge Cases](#6-error-handling--edge-cases)
7. [Performance & Scalability](#7-performance--scalability)
8. [Code Walkthrough Questions](#8-code-walkthrough-questions)
9. [Design Decision Questions](#9-design-decision-questions)
10. [Hands-On Coding Questions](#10-hands-on-coding-questions)

---

## 1. LangGraph Core Architecture

### Q1.1: "Explain the Graph class implementation. Why did you create a custom implementation instead of using a library?"

**Answer:**
```python
class Graph:
    def __init__(self, name: str):
        self.nodes: Dict[str, Callable] = {}   # Node name → function mapping
        self.edges: Dict[str, List[Dict]] = {} # From-node → list of edges
    
    def add_edge(self, from_node, to_node, condition=None):
        self.edges[from_node].append({"to": to_node, "condition": condition})
    
    def get_next_node(self, current: str, state: Dict) -> Optional[str]:
        for edge in self.edges[current]:
            if edge["condition"] is None or edge["condition"](state):
                return edge["to"]
        return None
```

**Key points to explain:**
1. **Simplicity**: Custom implementation gives full control, easy to debug
2. **Conditional routing**: Edges have lambda conditions evaluated at runtime
3. **First-match wins**: `get_next_node` returns first matching edge
4. **Async support**: All node functions are async, runtime awaits them

**Follow-up**: "What if two conditions both return True?"
> First one wins. Edge order matters. We add more specific conditions first.

---

### Q1.2: "Walk me through runtime.py. What happens if a node throws an exception?"

**Answer:**
```python
class GraphRuntime:
    async def run(self, input_state: Dict) -> Dict:
        state = input_state.copy()
        current = "parse_intent"
        iteration = 0
        
        while current and iteration < self.max_iterations:
            iteration += 1
            node_func = self.graph.nodes.get(current)
            
            try:
                state = await node_func(state)
                
                if current in ["report_result", "fallback"]:
                    break  # Terminal nodes
                
                current = self.graph.get_next_node(current, state)
                
            except Exception as e:
                state["error"] = "node_execution_error"
                state["message"] = f"Internal error: {str(e)}"
                state = await self.graph.nodes["fallback"](state)
                break
        
        return state
```

**Key points:**
1. **Exception handling**: Catches any exception, routes to `fallback` node
2. **Max iterations**: Prevents infinite loops (set to 20)
3. **Terminal nodes**: `report_result` and `fallback` end execution
4. **State immutability**: `input_state.copy()` prevents mutation of original

**Follow-up**: "Why 20 iterations? What if legitimate flow needs more?"
> 20 is generous for our graph (typically 5-7 nodes). If exceeded, it's likely infinite loop. Can increase but with logging alerts.

---

### Q1.3: "Explain the edge conditions in graph_def.py. How does conditional routing work?"

**Answer:**
```python
# Example edge definitions
graph.add_edge(
    "parse_intent", 
    "resolve_target", 
    condition=lambda s: s.get("next_node") != "execute_action"
)

graph.add_edge(
    "parse_intent", 
    "execute_action", 
    condition=lambda s: s.get("next_node") == "execute_action"
)

graph.add_edge(
    "check_consequences",
    "get_confirmation",
    condition=lambda s: s.get("needs_confirmation") and not s.get("error")
)

graph.add_edge(
    "check_consequences",
    "execute_action",
    condition=lambda s: not s.get("needs_confirmation") and not s.get("error")
)
```

**Key points:**
1. **Lambda conditions**: Evaluated with current state at runtime
2. **State-driven routing**: Nodes set flags like `next_node`, `needs_confirmation`
3. **Multiple edges from same node**: First matching condition wins
4. **Fallback edge**: Usually last, with no condition (always matches)

---

## 2. Node Deep Dive Questions

### Q2.1: "Explain parse_intent_llm.py in detail. What are all the code paths?"

**Answer:**

```python
async def parse_intent_llm(state: Dict) -> Dict:
    text = state.get("text", "").lower().strip()
    selected_trip_id = state.get("selectedTripId")
    
    # PATH 1: Wizard continuation
    if state.get("wizard_active"):
        state["next_node"] = "execute_action"  # Skip all other nodes
        return state
    
    # PATH 2: Structured commands (from UI buttons)
    if text.startswith("structured_cmd:"):
        return await parse_structured_command(state, text)
    
    # PATH 3: Context-aware shortcut
    if selected_trip_id and has_context_reference(text):
        state["action"] = detect_action(text)
        state["target_trip_id"] = selected_trip_id
        state["confidence"] = 0.95
        return state  # Skip LLM call!
    
    # PATH 4: Full LLM parsing
    llm_response = await parse_intent_with_llm(text, context)
    state.update({
        "action": llm_response["action"],
        "target_trip_id": llm_response["target_trip_id"],
        "parsed_params": llm_response["parameters"],
        "confidence": llm_response["confidence"]
    })
    
    return state
```

**The 4 paths:**
1. **Wizard path**: Already in multi-step flow, skip directly to execute_action
2. **Structured path**: Frontend button clicks (e.g., `structured_cmd:assign_vehicle:42:5`)
3. **Context shortcut**: User said "assign vehicle" while trip selected → no LLM needed
4. **Full LLM**: Natural language parsing via Gemini

**Follow-up**: "Why skip LLM for context-aware commands?"
> Performance (100ms vs 500ms) and accuracy (context is 100% reliable, LLM can hallucinate).

---

### Q2.2: "Explain resolve_target.py. What's the priority order for trip resolution?"

**Answer:**

```python
async def resolve_target(state: Dict) -> Dict:
    action = state.get("action")
    
    # SKIP for certain actions
    if action in ["list_all_stops", "add_vehicle", "get_unassigned_vehicles"]:
        return state  # No target needed
    
    # PRIORITY 1: OCR selectedTripId (from image upload)
    if state.get("selectedTripId") and state.get("from_image"):
        trip = await verify_trip_exists(state["selectedTripId"])
        if trip:
            state["trip_id"] = trip["trip_id"]
            state["resolve_result"] = "found"
            return state
    
    # PRIORITY 2: LLM target_trip_id (numeric)
    llm_trip_id = state.get("target_trip_id")
    if llm_trip_id:
        trip = await verify_trip_exists(llm_trip_id)
        if trip:
            state["trip_id"] = trip["trip_id"]
            return state
        # If not found, fall through (LLM hallucinated)
    
    # PRIORITY 3: Time-based search
    target_time = state.get("target_time")
    if target_time:
        trips = await search_trips_by_time(target_time)
        if len(trips) == 1:
            state["trip_id"] = trips[0]["trip_id"]
        elif len(trips) > 1:
            state["needs_clarification"] = True
            state["clarify_options"] = trips
        return state
    
    # PRIORITY 4: Label-based search (fuzzy)
    target_label = state.get("target_label")
    if target_label:
        trips = await tool_identify_trip_from_label(target_label)
        # Similar logic...
    
    return state
```

**Priority order:**
1. **OCR selectedTripId** (100% reliable if from image)
2. **LLM target_trip_id** (numeric, verify exists)
3. **target_time** (search by time like "08:00")
4. **target_label** (fuzzy match on display_name)

---

### Q2.3: "Explain decision_router.py. What is 'tribal knowledge'?"

**Answer:**

"Tribal knowledge" = **Page context rules** that determine which actions are valid on which page.

```python
# Actions ONLY allowed on Bus Dashboard
BUS_DASHBOARD_ACTIONS = {
    "assign_vehicle", "assign_driver", "remove_vehicle", "cancel_trip",
    "get_trip_details", "list_all_vehicles", "add_driver", ...
}

# Actions ONLY allowed on Manage Route page
MANAGE_ROUTE_ACTIONS = {
    "list_all_stops", "create_stop", "create_path", "delete_route", ...
}

def _check_page_context(action: str, current_page: str) -> tuple:
    if current_page == "busDashboard" and action in MANAGE_ROUTE_ACTIONS:
        return False, "This action is only available on Manage Route page"
    if current_page == "manageRoute" and action in BUS_DASHBOARD_ACTIONS:
        return False, "This action is only available on Bus Dashboard"
    return True, None
```

**Why important:**
- Prevents confusion (can't assign vehicle while on route config page)
- Better UX (tells user where to go)
- Security (actions only valid in proper context)

---

### Q2.4: "Walk through check_consequences.py. How do you determine if confirmation is needed?"

**Answer:**

```python
SAFE_ACTIONS = [
    "get_*", "list_*",           # All read operations
    "create_stop", "create_path", # Non-destructive creates
    "assign_driver",              # Driver assignment is safe
    "add_vehicle", "add_driver",  # Fleet additions
]

RISKY_ACTIONS = [
    "remove_vehicle",             # Affects passengers
    "cancel_trip",                # Affects bookings
    "delete_stop", "delete_path", # Cascading deletes
    "assign_vehicle",             # Could override existing
]

async def check_consequences(state: Dict) -> Dict:
    action = state["action"]
    
    # Safe actions: skip check
    if action in SAFE_ACTIONS:
        state["needs_confirmation"] = False
        return state
    
    # Risky actions: analyze impact
    trip_id = state["trip_id"]
    
    # Get current data
    trip_status = await tool_get_trip_status(trip_id)
    bookings = await tool_get_bookings(trip_id)
    
    state["consequences"] = {
        "trip_status": trip_status.get("live_status"),
        "booking_count": len(bookings),
        "has_vehicle": trip_status.get("vehicle_id") is not None,
        "has_driver": trip_status.get("driver_id") is not None,
    }
    
    # Determine if confirmation needed
    if action == "cancel_trip":
        state["needs_confirmation"] = True
        state["message"] = f"⚠️ This will cancel trip with {len(bookings)} passengers"
    
    elif action == "remove_vehicle" and len(bookings) > 0:
        state["needs_confirmation"] = True
        state["message"] = f"⚠️ {len(bookings)} passengers will be affected"
    
    elif action == "assign_vehicle" and trip_status.get("vehicle_id"):
        state["needs_confirmation"] = True
        state["message"] = "⚠️ This will replace the current vehicle"
    
    return state
```

---

### Q2.5: "Explain execute_action.py structure. How is it organized?"

**Answer:**

```python
async def execute_action(state: Dict) -> Dict:
    action = state.get("action")
    
    # ========== SECTION 1: READ ACTIONS ==========
    if action == "get_unassigned_vehicles":
        result = await tool_get_unassigned_vehicles()
        state["final_output"] = {"type": "table", "data": result}
    
    elif action == "get_trip_details":
        result = await tool_get_trip_details(state["trip_id"])
        state["final_output"] = {"type": "object", "data": result}
    
    # ========== SECTION 2: SAFE MUTATE ACTIONS ==========
    elif action == "create_stop":
        params = state["parsed_params"]
        result = await tool_create_stop(
            params["stop_name"], 
            params.get("latitude"), 
            params.get("longitude")
        )
    
    elif action == "assign_driver":
        result = await tool_assign_driver(
            state["trip_id"],
            state["parsed_params"]["driver_id"],
            state["user_id"]
        )
    
    # ========== SECTION 3: RISKY MUTATE ACTIONS ==========
    elif action == "remove_vehicle":
        result = await tool_remove_vehicle(state["trip_id"], state["user_id"])
    
    elif action == "cancel_trip":
        result = await tool_cancel_trip(state["trip_id"])
    
    # ========== SECTION 4: COMPOUND ACTIONS ==========
    elif action == "assign_vehicle_and_driver":
        # Look up vehicle and driver
        vehicle = await find_vehicle(state["parsed_params"]["vehicle_registration"])
        driver = await find_driver(state["parsed_params"]["driver_name"])
        result = await tool_assign_vehicle(trip_id, vehicle["id"], driver["id"], user_id)
    
    # ========== SECTION 5: WIZARD ACTIONS ==========
    elif action == "add_vehicle":
        wizard_step = state.get("wizard_step", 0)
        
        if wizard_step == 0:
            state["message"] = "What type of vehicle? (bus/van/car)"
            state["wizard_step"] = 1
            state["wizard_active"] = True
        elif wizard_step == 1:
            state["wizard_data"]["vehicle_type"] = state["user_message"]
            state["message"] = "What's the seating capacity?"
            state["wizard_step"] = 2
        elif wizard_step == 2:
            # Create vehicle with all collected data
            await create_vehicle(state["wizard_data"])
            state["wizard_active"] = False
    
    state["status"] = "executed"
    return state
```

**Organization:**
1. **READ actions**: Just fetch and format data
2. **SAFE MUTATE**: Create operations, low risk
3. **RISKY MUTATE**: Already confirmed by this point
4. **COMPOUND**: Multiple operations in one
5. **WIZARD**: Multi-step with state persistence

---

## 3. LLM Integration Questions

### Q3.1: "Explain the LLM prompt structure in llm_client.py"

**Answer:**

```python
SYSTEM_PROMPT = """
You are MoviAgent's intelligent intent parser.

Return ONLY valid JSON:
{
    "action": "cancel_trip|assign_vehicle|...",
    "target_label": "string|null",
    "target_trip_id": int|null,
    "parameters": {...},
    "confidence": 0.0-1.0,
    "clarify": boolean,
    "explanation": "short"
}

**NATURAL LANGUAGE RULES:**

VEHICLE ASSIGNMENT patterns:
- "assign vehicle", "put a bus on", "deploy vehicle"...

DRIVER ASSIGNMENT patterns:
- "assign driver", "add driver to", "put someone on"...

**CONTEXT RULES:**
- If selectedTripId in context → use as target_trip_id
- If user says "this trip" → use selectedTripId
- If no context → set clarify=true

**CONFIDENCE GUIDELINES:**
- 0.9+: Clear action + target
- 0.7-0.9: Clear action, partial target
- <0.6: Need clarification
"""
```

**Key sections:**
1. **JSON schema**: Strict output format
2. **Action patterns**: Synonyms for each action
3. **Context rules**: How to use selectedTripId
4. **Confidence guidelines**: When to ask for clarification

---

### Q3.2: "How do you handle LLM failures and fallbacks?"

**Answer:**

```python
async def parse_intent_with_llm(text: str, context: Dict) -> Dict:
    try:
        # Try Gemini first
        response = await call_gemini(text, context)
        return parse_json_response(response)
    
    except GeminiTimeoutError:
        logger.warning("Gemini timeout, using fallback")
        return fallback_regex_parse(text, context)
    
    except JSONDecodeError:
        logger.warning("Invalid JSON from Gemini, attempting fix")
        fixed = attempt_json_fix(response)
        if fixed:
            return fixed
        return fallback_regex_parse(text, context)
    
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {"action": "unknown", "confidence": 0.0}


def fallback_regex_parse(text: str, context: Dict) -> Dict:
    """Regex-based fallback when LLM fails"""
    
    patterns = {
        "assign_vehicle": ["assign vehicle", "put bus on", "deploy vehicle"],
        "cancel_trip": ["cancel trip", "cancel this", "abort"],
        "remove_vehicle": ["remove vehicle", "unassign vehicle"],
        # ...
    }
    
    text_lower = text.lower()
    for action, keywords in patterns.items():
        for keyword in keywords:
            if keyword in text_lower:
                result = {"action": action, "confidence": 0.8}
                
                # Extract trip ID if present
                trip_match = re.search(r"trip\s+(\d+)", text)
                if trip_match:
                    result["target_trip_id"] = int(trip_match.group(1))
                
                return result
    
    return {"action": "unknown", "confidence": 0.0}
```

**Fallback layers:**
1. **Primary**: Gemini LLM
2. **JSON fix**: Attempt to repair malformed JSON
3. **Regex fallback**: Pattern matching for common phrases
4. **Ultimate fallback**: Return "unknown" action

---

### Q3.3: "How is ACTION_REGISTRY used for validation?"

**Answer:**

```python
ACTION_REGISTRY = {
    "read_dynamic": [
        "get_trip_status", "get_trip_details", "get_unassigned_vehicles", ...
    ],
    "mutate_dynamic": [
        "cancel_trip", "remove_vehicle", "assign_vehicle", "assign_driver",
        "assign_vehicle_and_driver", ...  # Our compound action
    ],
    "read_static": [
        "list_all_stops", "list_all_paths", "list_all_routes", ...
    ],
    "mutate_static": [
        "create_stop", "create_path", "create_route", "delete_stop", ...
    ],
    "special": [
        "context_mismatch", "unknown"
    ]
}

# Flatten for validation
valid_actions = []
for category, actions in ACTION_REGISTRY.items():
    valid_actions.extend(actions)

def validate_llm_response(response):
    action = response.get("action")
    
    if action not in valid_actions:
        # Try fuzzy matching
        fuzzy_matches = {
            "assign_drivers": "assign_driver",  # Plural → singular
            "cancel_trips": "cancel_trip",
        }
        if action in fuzzy_matches:
            response["action"] = fuzzy_matches[action]
        else:
            response["action"] = "unknown"
    
    return response
```

**Purpose:**
1. **Validation**: Reject hallucinated actions
2. **Normalization**: Fix common LLM mistakes (plurals, typos)
3. **Categorization**: Helps determine SAFE vs RISKY

---

## 4. State Management Questions

### Q4.1: "How is session state persisted for multi-turn conversations?"

**Answer:**

```python
# In agent.py - saving wizard state
async def agent_message(request):
    # Load existing session
    row = await conn.fetchrow("""
        SELECT pending_action, conversation_history 
        FROM agent_sessions 
        WHERE session_id=$1 AND status='PENDING'
    """, request.session_id)
    
    if row and row["pending_action"]:
        pending = json.loads(row["pending_action"])
        if pending.get("wizard_active"):
            wizard_state = {
                "wizard_active": True,
                "wizard_type": pending["wizard_type"],
                "wizard_step": pending["wizard_step"],
                "wizard_data": pending["wizard_data"]
            }
            input_state.update(wizard_state)
    
    # Run graph
    result = await runtime.run(input_state)
    
    # Save updated wizard state
    if result.get("wizard_active"):
        await conn.execute("""
            INSERT INTO agent_sessions (session_id, pending_action, status)
            VALUES ($1, $2, 'PENDING')
            ON CONFLICT (session_id) 
            DO UPDATE SET pending_action=$2, updated_at=NOW()
        """, session_id, json.dumps({
            "wizard_active": True,
            "wizard_type": result["wizard_type"],
            "wizard_step": result["wizard_step"],
            "wizard_data": result["wizard_data"]
        }))
```

**Key points:**
1. **agent_sessions table**: Stores pending_action as JSONB
2. **Wizard state**: Persisted between requests
3. **Conversation history**: Also stored for LLM context
4. **Status tracking**: PENDING, CONFIRMED, CANCELLED

---

### Q4.2: "What happens to state between nodes? Is it mutable?"

**Answer:**

```python
# In runtime.py
async def run(self, input_state: Dict) -> Dict:
    state = input_state.copy()  # Shallow copy!
    
    while current:
        state = await node_func(state)  # Node modifies and returns
        current = self.graph.get_next_node(current, state)
    
    return state
```

**Important details:**
1. **Shallow copy**: Initial state is copied, original preserved
2. **Direct mutation**: Nodes mutate the state dict directly
3. **Return required**: Nodes must return state (for chaining)
4. **No deep copy**: Nested objects are shared (be careful!)

**Follow-up**: "Is there a risk of unintended state mutation?"

> Yes. If a node modifies a nested object, it affects the original. We mitigate by:
> 1. Using immutable patterns where possible
> 2. Creating new dicts for nested updates
> 3. Logging state at each step for debugging

---

### Q4.3: "How do you handle concurrent requests with shared state?"

**Answer:**

```python
# Each request gets its own state copy
async def run(self, input_state: Dict) -> Dict:
    state = input_state.copy()  # Isolated per request
    ...

# Database connections from pool
pool = await get_conn()  # Connection pool (asyncpg)
async with pool.acquire() as conn:
    # Each request gets its own connection
    ...
```

**Isolation mechanisms:**
1. **State isolation**: Each request has own state dict
2. **Connection pool**: asyncpg pool manages connections
3. **No shared mutable state**: Graph and nodes are stateless
4. **Session isolation**: session_id uniquely identifies conversations

---

## 5. Database & Tools Questions

### Q5.1: "Explain the tools.py structure. What's the naming convention?"

**Answer:**

```python
# Pattern: tool_<action>_<entity>

# GET operations
async def tool_get_trip_status(trip_id: int) -> Dict:
    """Read trip status from database"""
    
async def tool_get_bookings(trip_id: int) -> List[Dict]:
    """Read all bookings for a trip"""

# MUTATE operations
async def tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id) -> Dict:
    """Assign vehicle + driver to trip"""
    
async def tool_remove_vehicle(trip_id, user_id) -> Dict:
    """Remove vehicle assignment"""

# CREATE operations
async def tool_create_stop(name, lat=None, lon=None) -> Dict:
    """Create new stop"""
    
async def tool_add_vehicle(reg, vtype, capacity) -> Dict:
    """Add new vehicle to fleet"""

# SEARCH operations
async def tool_identify_trip_from_label(label: str) -> List[Dict]:
    """Fuzzy search trips by label"""
```

**Naming convention:**
- `tool_` prefix for all functions
- Verb describes operation (get, assign, remove, create)
- Returns Dict with `ok` field for success/failure

---

### Q5.2: "Explain the database connection management"

**Answer:**

```python
# supabase_client.py
from asyncpg import create_pool

_pool = None

async def init_db_pool(min_size=2, max_size=10):
    global _pool
    _pool = await create_pool(
        DATABASE_URL,
        min_size=min_size,
        max_size=max_size,
        ssl='require'  # Supabase requires SSL
    )
    logger.info(f"✅ Database pool initialized (min={min_size}, max={max_size})")

async def get_conn():
    """Get connection pool (lazy init if needed)"""
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool

async def close_pool():
    """Close pool on shutdown"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

# Usage in tools
async def tool_get_trip_status(trip_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:  # Get connection from pool
        result = await conn.fetchrow("SELECT * FROM daily_trips WHERE trip_id=$1", trip_id)
    # Connection automatically returned to pool
    return dict(result) if result else {}
```

**Key points:**
1. **Connection pooling**: asyncpg pool reuses connections
2. **Lazy initialization**: Pool created on first use
3. **Context manager**: `async with` ensures connection return
4. **Lifecycle**: Init on startup, close on shutdown (lifespan)

---

### Q5.3: "How do you handle database transactions?"

**Answer:**

```python
async def tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id):
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Transaction for atomic updates
        async with conn.transaction():
            # Check if deployment exists
            existing = await conn.fetchrow(
                "SELECT deployment_id FROM deployments WHERE trip_id=$1",
                trip_id
            )
            
            if existing:
                # Update existing deployment
                await conn.execute("""
                    UPDATE deployments 
                    SET vehicle_id=$1, driver_id=$2, updated_at=NOW()
                    WHERE trip_id=$3
                """, vehicle_id, driver_id, trip_id)
            else:
                # Create new deployment
                await conn.execute("""
                    INSERT INTO deployments (trip_id, vehicle_id, driver_id)
                    VALUES ($1, $2, $3)
                """, trip_id, vehicle_id, driver_id)
            
            # Log to audit table
            await conn.execute("""
                INSERT INTO audit_log (user_id, action, entity_id, details)
                VALUES ($1, 'assign_vehicle', $2, $3)
            """, user_id, trip_id, json.dumps({
                "vehicle_id": vehicle_id,
                "driver_id": driver_id
            }))
        
        # Transaction commits here (or rolls back on exception)
    
    return {"ok": True, "message": "Vehicle assigned"}
```

---

## 6. Error Handling & Edge Cases

### Q6.1: "How do you handle malformed LLM responses?"

**Answer:**

```python
def parse_llm_response(response_text: str) -> Dict:
    """Parse and validate LLM response"""
    
    try:
        # Try direct JSON parse
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # Attempt fixes
        
        # Fix 1: Extract JSON from markdown code blocks
        match = re.search(r'```json?\s*([\s\S]*?)\s*```', response_text)
        if match:
            try:
                data = json.loads(match.group(1))
            except:
                pass
        
        # Fix 2: Fix trailing commas
        cleaned = re.sub(r',\s*}', '}', response_text)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        try:
            data = json.loads(cleaned)
        except:
            pass
        
        # Fix 3: Handle unquoted strings
        # ...more fixes...
        
        # Ultimate fallback
        return {
            "action": "unknown",
            "confidence": 0.0,
            "explanation": "Failed to parse LLM response"
        }
    
    # Validate required fields
    if "action" not in data:
        data["action"] = "unknown"
    
    if data.get("action") not in valid_actions:
        data["action"] = "unknown"
    
    # Normalize confidence
    data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
    
    return data
```

---

### Q6.2: "What happens if a trip doesn't exist but LLM returns a trip_id?"

**Answer:**

```python
# In resolve_target.py
async def resolve_target(state: Dict) -> Dict:
    llm_trip_id = state.get("target_trip_id")
    
    if llm_trip_id:
        # Verify with database
        pool = await get_conn()
        async with pool.acquire() as conn:
            trip = await conn.fetchrow(
                "SELECT * FROM daily_trips WHERE trip_id=$1",
                llm_trip_id
            )
        
        if trip:
            # Valid - use it
            state["trip_id"] = trip["trip_id"]
            state["trip_label"] = trip["display_name"]
            logger.info(f"✅ Trip {llm_trip_id} verified")
        else:
            # LLM hallucinated! Fall through to other methods
            logger.warning(f"❌ Trip {llm_trip_id} doesn't exist - LLM hallucinated")
            # Don't set error - try label-based search next
    
    # Continue with label-based search...
```

**Key insight**: Never trust LLM-provided IDs without verification.

---

### Q6.3: "How do you handle race conditions in vehicle assignment?"

**Answer:**

```python
async def check_vehicle_availability(trip_id: int, vehicle_id: int) -> bool:
    """Check if vehicle is available for this trip's time slot"""
    
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Get the trip's time slot
        trip = await conn.fetchrow(
            "SELECT trip_date, start_time, end_time FROM daily_trips WHERE trip_id=$1",
            trip_id
        )
        
        # Check for conflicting assignments
        conflict = await conn.fetchrow("""
            SELECT d.deployment_id 
            FROM deployments d
            JOIN daily_trips t ON d.trip_id = t.trip_id
            WHERE d.vehicle_id = $1
              AND t.trip_date = $2
              AND t.trip_id != $3
              AND (
                  (t.start_time, t.end_time) OVERLAPS ($4, $5)
              )
        """, vehicle_id, trip["trip_date"], trip_id, 
             trip["start_time"], trip["end_time"])
        
        return conflict is None

async def tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id):
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Lock the vehicle row for update
            await conn.execute(
                "SELECT * FROM vehicles WHERE vehicle_id=$1 FOR UPDATE",
                vehicle_id
            )
            
            # Check availability inside transaction
            available = await check_vehicle_availability(trip_id, vehicle_id)
            if not available:
                return {"ok": False, "error": "Vehicle has conflicting assignment"}
            
            # Proceed with assignment
            await conn.execute(...)
```

**Race condition handling:**
1. **SELECT FOR UPDATE**: Locks vehicle row
2. **Transaction**: Ensures atomic check-and-assign
3. **Time overlap check**: Prevents double-booking

---

## 7. Performance & Scalability Questions

### Q7.1: "What's the latency breakdown for a typical request?"

**Answer:**

```
Typical request: "Assign vehicle to trip 42"

1. FastAPI routing:           ~5ms
2. Session loading:           ~20ms (DB query)
3. parse_intent_llm:
   - Context check:           ~2ms
   - LLM call (Gemini):       ~300-500ms  ← Bottleneck
   - OR context shortcut:     ~5ms
4. resolve_target:            ~30ms (DB verify)
5. decision_router:           ~1ms
6. check_consequences:        ~40ms (DB: trip + bookings)
7. execute_action:            ~50ms (DB update + audit)
8. report_result:             ~1ms
9. Session save:              ~20ms

Total (with LLM):    ~500-700ms
Total (with shortcut): ~150-200ms
```

**Optimization strategies:**
1. **Context shortcuts**: Skip LLM when context is clear
2. **Connection pooling**: Reuse DB connections
3. **Parallel queries**: Fetch trip + bookings concurrently
4. **LLM caching**: Cache common responses (future)

---

### Q7.2: "How would you scale this for 1000 concurrent users?"

**Answer:**

```
Current: Single instance, in-memory graph

Scaling approach:

1. HORIZONTAL SCALING
   - Multiple FastAPI instances behind load balancer
   - Graph is stateless - scales horizontally
   - Session state in shared database (already done)

2. DATABASE SCALING
   - Read replicas for GET operations
   - Connection pool per instance (currently max=10)
   - PgBouncer for connection multiplexing

3. LLM SCALING
   - Gemini has high rate limits
   - Add request queuing for burst handling
   - Consider local model (Ollama) for common patterns

4. CACHING
   - Redis for session state (faster than DB)
   - Cache trip lookups (short TTL)
   - Cache LLM responses for identical queries

Architecture:
┌─────────────┐
│ Load        │
│ Balancer    │
└──────┬──────┘
       │
  ┌────┴────┬────────┐
  ▼         ▼        ▼
┌────┐   ┌────┐   ┌────┐
│API1│   │API2│   │API3│
└──┬─┘   └──┬─┘   └──┬─┘
   │        │        │
   └────────┼────────┘
            ▼
      ┌──────────┐     ┌──────────┐
      │ Redis    │     │ Gemini   │
      │ (cache)  │     │ API      │
      └──────────┘     └──────────┘
            │
            ▼
      ┌──────────┐
      │PostgreSQL│
      │(Primary) │
      └────┬─────┘
           │
     ┌─────┴─────┐
     ▼           ▼
  ┌──────┐   ┌──────┐
  │Replica│   │Replica│
  └──────┘   └──────┘
```

---

## 8. Code Walkthrough Questions

### Q8.1: "Show me the complete flow for 'cancel trip 42'"

**Answer:**

```python
# 1. Frontend sends request
POST /api/agent/message
{
    "text": "cancel trip 42",
    "user_id": 1,
    "selectedTripId": null,
    "currentPage": "busDashboard"
}

# 2. agent.py creates input state
input_state = {
    "text": "cancel trip 42",
    "user_id": 1,
    "session_id": "abc-123",
    "currentPage": "busDashboard",
    "ui_context": {"selectedTripId": None}
}

# 3. runtime.run(input_state)
# Node 1: parse_intent_llm
state = {
    ...input_state,
    "action": "cancel_trip",
    "target_trip_id": 42,
    "confidence": 0.95,
    "parsed_params": {}
}

# Node 2: resolve_target
# Verify trip 42 exists in DB
state["trip_id"] = 42
state["trip_label"] = "Path-1 - 08:00"
state["resolve_result"] = "found"

# Node 3: decision_router
# cancel_trip on busDashboard → allowed
# cancel_trip is risky → check_consequences
state["next_node"] = "check_consequences"

# Node 4: check_consequences
# cancel_trip is RISKY_ACTION
# Check bookings: found 5 passengers
state["consequences"] = {"booking_count": 5}
state["needs_confirmation"] = True
state["message"] = "⚠️ This will cancel trip with 5 passengers. Proceed?"

# Node 5: get_confirmation
# Save pending action to database
await conn.execute("""
    INSERT INTO agent_sessions (session_id, pending_action, status)
    VALUES ('abc-123', '{"action":"cancel_trip","trip_id":42}', 'PENDING')
""")
state["status"] = "awaiting_confirmation"
state["confirmation_required"] = True

# Node 6: report_result
state["final_output"] = {
    "action": "cancel_trip",
    "trip_id": 42,
    "status": "awaiting_confirmation",
    "needs_confirmation": True,
    "message": "⚠️ This will cancel trip with 5 passengers. Proceed?",
    "session_id": "abc-123",
    "success": True
}

# 4. Response to frontend
{
    "agent_output": {
        "action": "cancel_trip",
        "status": "awaiting_confirmation",
        "needs_confirmation": true,
        "session_id": "abc-123",
        "message": "⚠️ This will cancel trip with 5 passengers. Proceed?"
    }
}

# 5. User confirms
POST /api/agent/confirm
{"session_id": "abc-123", "confirmed": true}

# 6. Load and execute pending action
pending = await load_pending_action("abc-123")
result = await tool_cancel_trip(pending["trip_id"])
await update_session_status("abc-123", "CONFIRMED")

# 7. Final response
{"status": "executed", "message": "Trip 42 cancelled successfully"}
```

---

## 9. Design Decision Questions

### Q9.1: "Why separate parse_intent and resolve_target into two nodes?"

**Answer:**

**Separation of concerns:**

```
parse_intent: Natural language → Intent (no DB access)
resolve_target: Intent → Verified entities (DB access)
```

**Benefits:**
1. **Testability**: Can test NLP without DB mocks
2. **Caching**: LLM responses cacheable (no state dependency)
3. **Fallback handling**: LLM can suggest invalid IDs, resolve_target catches
4. **Clear responsibility**: Each node does one thing

**Alternative considered:**
> Merging them would reduce node count but:
> - Mix concerns (NLP + DB)
> - Harder to test
> - LLM would need real-time DB access

---

### Q9.2: "Why is assign_driver SAFE but assign_vehicle RISKY?"

**Answer:**

```python
SAFE_ACTIONS = ["assign_driver", ...]
RISKY_ACTIONS = ["assign_vehicle", ...]
```

**Reasoning:**

**assign_driver:**
- Driver is just a person, can be changed freely
- No cascading effects on other systems
- Doesn't affect vehicle availability
- Users frequently change drivers

**assign_vehicle:**
- Vehicle might already be assigned elsewhere
- Could cause time conflicts (double booking)
- Affects maintenance schedules
- Replacement vehicle impacts passengers

**In check_consequences:**
```python
if action == "assign_vehicle":
    if trip_status.get("vehicle_id"):
        state["needs_confirmation"] = True
        state["message"] = "⚠️ This will replace the current vehicle"
```

---

### Q9.3: "Why did you implement wizards instead of single-request operations?"

**Answer:**

**For add_vehicle:**

Single request would require:
```json
{
    "text": "Add vehicle TN-01-AB-1234, type bus, capacity 40"
}
```

Problems:
1. **User burden**: Must remember all required fields
2. **Error prone**: Typos, missing data
3. **Poor UX**: "Required field missing" errors
4. **No guidance**: User doesn't know valid options

**Wizard approach:**
```
Step 0: "Add vehicle TN-01-AB-1234"
Response: "What type of vehicle? (bus/van/car)"

Step 1: "bus"
Response: "What's the seating capacity?"

Step 2: "40"
Response: "✅ Vehicle TN-01-AB-1234 (bus, 40 seats) added!"
```

**Benefits:**
1. **Guided experience**: User only answers one question at a time
2. **Validation per step**: Catch errors early
3. **Discoverable options**: Shows valid choices
4. **Conversational feel**: More natural interaction

---

## 10. Hands-On Coding Questions

### Q10.1: "Add a new action: get_trip_stops that returns all stops for a trip"

**Answer:**

```python
# Step 1: llm_client.py - Add to ACTION_REGISTRY
ACTION_REGISTRY = {
    "read_dynamic": [
        ...,
        "get_trip_stops",  # NEW
    ],
    ...
}

# Step 2: llm_client.py - Add pattern to SYSTEM_PROMPT
"""
GET_TRIP_STOPS - Recognize these patterns:
- "what stops", "show stops", "list stops for trip"
- "stops in trip X", "stops on this route"
→ action="get_trip_stops"
"""

# Step 3: tools.py - Add tool function
async def tool_get_trip_stops(trip_id: int) -> List[Dict]:
    """Get all stops for a trip's route"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.stop_id, s.stop_name, s.latitude, s.longitude, ps.stop_order
            FROM daily_trips t
            JOIN routes r ON t.route_id = r.route_id
            JOIN path_stops ps ON r.path_id = ps.path_id
            JOIN stops s ON ps.stop_id = s.stop_id
            WHERE t.trip_id = $1
            ORDER BY ps.stop_order
        """, trip_id)
        return [dict(r) for r in rows]

# Step 4: check_consequences.py - Mark as SAFE
SAFE_ACTIONS = [
    ...,
    "get_trip_stops",  # Read-only, no confirmation needed
]

# Step 5: execute_action.py - Add handler
elif action == "get_trip_stops":
    trip_id = state.get("trip_id")
    if not trip_id:
        state["error"] = "missing_trip_id"
        state["message"] = "Please specify which trip"
        return state
    
    stops = await tool_get_trip_stops(trip_id)
    state["final_output"] = {
        "type": "table",
        "data": stops,
        "columns": ["stop_name", "stop_order", "latitude", "longitude"]
    }
    state["message"] = f"Found {len(stops)} stops for trip {trip_id}"
    state["status"] = "executed"

# Step 6: No routing changes needed (default flow works)
```

---

### Q10.2: "Add rate limiting to prevent LLM abuse"

**Answer:**

```python
# New file: backend/app/core/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)  # user_id → [timestamps]
        self._lock = asyncio.Lock()
    
    async def check(self, user_id: int) -> tuple[bool, str]:
        """Returns (allowed, message)"""
        async with self._lock:
            now = datetime.now()
            window_start = now - self.window
            
            # Clean old requests
            self.requests[user_id] = [
                ts for ts in self.requests[user_id]
                if ts > window_start
            ]
            
            if len(self.requests[user_id]) >= self.max_requests:
                return False, f"Rate limit exceeded. Max {self.max_requests} requests per minute."
            
            self.requests[user_id].append(now)
            return True, ""

rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

# In agent.py
from app.core.rate_limiter import rate_limiter

@router.post("/message")
async def agent_message(request: AgentMessageRequest):
    # Rate limiting check
    allowed, message = await rate_limiter.check(request.user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    # Continue with normal flow...
```

---

### Q10.3: "Implement a health check that verifies all components"

**Answer:**

```python
# backend/app/api/health.py

@router.get("/status")
async def health_status():
    """Comprehensive health check"""
    results = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check 1: Database
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        results["components"]["database"] = {
            "status": "healthy",
            "pool_size": pool.get_size(),
            "pool_free": pool.get_idle_size()
        }
    except Exception as e:
        results["status"] = "degraded"
        results["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check 2: LLM (Gemini)
    try:
        from langgraph.tools.llm_client import test_llm_connection
        llm_ok = await test_llm_connection()
        results["components"]["llm"] = {
            "status": "healthy" if llm_ok else "unhealthy",
            "provider": "gemini"
        }
    except Exception as e:
        results["components"]["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check 3: Graph integrity
    from langgraph.graph_def import graph
    results["components"]["graph"] = {
        "status": "healthy",
        "nodes": len(graph.nodes),
        "edges": sum(len(e) for e in graph.edges.values())
    }
    
    # Overall status
    unhealthy = [k for k, v in results["components"].items() 
                 if v["status"] == "unhealthy"]
    if unhealthy:
        results["status"] = "unhealthy"
        results["unhealthy_components"] = unhealthy
    
    return results
```

---

## Final Tips for Deep Technical Interview

1. **Know the file locations**: Be ready to say "that's handled in `decision_router.py` lines 50-80"

2. **Understand state flow**: Every question can be answered by tracing state through nodes

3. **Know the constants**: SAFE_ACTIONS, RISKY_ACTIONS, BUS_DASHBOARD_ACTIONS, ACTION_REGISTRY

4. **Database queries**: Know the key tables and relationships

5. **Error handling**: Be ready to explain fallback paths

6. **Trade-offs**: Every design decision has pros/cons - explain both

7. **Draw diagrams**: When explaining flows, sketch the graph

8. **Be honest**: If unsure, say "I'd need to check the code, but I believe..."

Good luck! 🚀
