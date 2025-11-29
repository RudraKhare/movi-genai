# 📋 MOVI Interview - Quick Revision Notes (10-Minute Read)

## 🎯 Project One-Liner
> "MOVI is an AI-powered fleet management system where an LLM-based conversational agent manages buses, drivers, trips, and routes through natural language commands using a LangGraph state machine."

---

## 🏗️ Architecture in 30 Seconds

```
User Chat → FastAPI → LangGraph Runtime → 6 Nodes → Database → Response
                         │
                         └── Gemini LLM (for intent parsing)
```

**Key Insight**: Graph architecture, not if-else chains. Each node has one job.

---

## 📦 Tech Stack (Memorize This!)

| Layer | Technology |
|-------|------------|
| Frontend | React + TypeScript + Zustand + TanStack Query |
| Backend | FastAPI + Python 3.11 |
| LLM | Gemini 1.5 Flash via `google.generativeai` |
| Database | PostgreSQL via asyncpg (Supabase hosted) |
| Graph Engine | Custom LangGraph implementation |

---

## 🔄 Core Flow (Most Important!)

```
1. parse_intent_llm  → LLM converts text to action+params
2. resolve_target    → Verifies trip/route/vehicle exists
3. decision_router   → Decides which path based on page context
4. check_consequences→ SAFE or RISKY action?
5. execute_action    → Actually runs the action
6. report_result     → Formats and returns response
```

**Alternative paths:**
- Wizards: trip_creation_wizard, route_wizard
- Fallback: When action unknown
- Selection providers: vehicle_selection, driver_selection

---

## 🎯 Key Concepts to Explain

### 1. State Machine Pattern
```python
class Graph:
    def __init__(self):
        self.nodes = {}      # name → function
        self.edges = {}      # name → [{condition, target}]
    
    def add_node(self, name, func): ...
    def add_edge(self, source, target, condition=None): ...
```
**Why**: Separation of concerns, reusability, testability

### 2. Conditional Routing
```python
# From decision_router
if action in ["create_route", "route_creation_wizard"]:
    state["next_node"] = "route_wizard"
elif state.get("from_image"):
    state["next_node"] = "suggestion_provider"
elif action in SAFE_ACTIONS:
    state["next_node"] = "execute_action"
```

### 3. Safe vs Risky Actions
```python
SAFE_ACTIONS = ["show_trip_details", "assign_vehicle", ...]  # No confirmation
RISKY_ACTIONS = ["cancel_trip", "delete_route", ...]  # Needs confirmation
```

### 4. LLM JSON Output
```python
# LLM returns structured JSON
{
    "action": "assign_vehicle",
    "confidence": 0.95,
    "target_trip_id": 42,
    "parameters": {"vehicle_id": 5}
}
```

### 5. Async/Await Pattern
```python
async def tool_get_trip(trip_id: int) -> Optional[Dict]:
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM daily_trips WHERE trip_id = $1",
            trip_id
        )
        return dict(row) if row else None
```

---

## 📁 Key Files (Know Their Purpose!)

| File | One-Line Purpose |
|------|-----------------|
| `graph_def.py` | Defines graph nodes and edges |
| `runtime.py` | Executes graph from start to finish |
| `parse_intent_llm.py` | Converts natural language → action |
| `llm_client.py` | Gemini integration + system prompt |
| `resolve_target.py` | Validates trip/route/vehicle exists |
| `decision_router.py` | Routes based on page context |
| `check_consequences.py` | Decides if confirmation needed |
| `execute_action.py` | 40+ action handlers |
| `tools.py` | Database wrapper functions |

---

## 💡 Common Interview Answers

### "Why LangGraph instead of simple if-else?"
> "State machine provides separation of concerns. Each node has one job - parse, resolve, route, check, execute. This makes code testable, reusable, and easy to extend. Adding new action? Just add handler in execute_action. New flow? Add node and edges."

### "How does LLM parse intent?"
> "We send user text + context (current page, selected trip) to Gemini with detailed system prompt. LLM returns structured JSON with action, parameters, and confidence. We validate against ACTION_REGISTRY. If confidence low, we ask for clarification."

### "How do you handle confirmation for dangerous actions?"
> "Actions are classified as SAFE (show info, assign vehicle) or RISKY (cancel trip, delete route). Risky actions stop at check_consequences node, save pending action to database, return confirmation request. When user confirms, we reload pending action and execute."

### "How do you handle image upload/OCR?"
> "Image sent to Gemini Vision API which extracts trip details. We set `from_image=True` in state. Decision router routes to suggestion_provider which shows extracted data as clickable suggestions. User confirms, then normal flow continues."

### "How would you add a new action?"
> "Three steps: (1) Add to ACTION_REGISTRY in llm_client.py, (2) Add handler in execute_action.py, (3) If risky, add to RISKY_ACTIONS. That's it - graph handles everything else."

### "What happens if LLM fails?"
> "Fallback regex patterns in parse_intent. If regex fails, route to fallback node with helpful suggestions. Never let system crash."

---

## 🔢 Numbers to Know

| Metric | Value |
|--------|-------|
| Total Actions | 40+ |
| Nodes in Graph | 15+ |
| Max Iterations | 20 |
| LLM Model | Gemini 1.5 Flash |
| DB Pool | min=1, max=10 |
| Action Categories | 6 (query, mutate, wizard, display, info, compound) |

---

## ⚡ Quick Code Patterns

### Pattern 1: Node Function
```python
async def my_node(state: Dict) -> Dict:
    # Read from state
    action = state.get("action")
    
    # Do work
    result = await some_async_operation()
    
    # Update state
    state["my_result"] = result
    state["next_node"] = "next_step"
    
    return state
```

### Pattern 2: Database Query
```python
pool = await get_conn()
async with pool.acquire() as conn:
    rows = await conn.fetch("SELECT * FROM table WHERE id = $1", id)
    return [dict(r) for r in rows]
```

### Pattern 3: LLM Call
```python
import google.generativeai as genai
model = genai.GenerativeModel("gemini-1.5-flash")
response = await asyncio.to_thread(
    model.generate_content,
    prompt
)
return json.loads(response.text)
```

### Pattern 4: Action Handler
```python
elif action == "my_action":
    param = state.get("parsed_params", {}).get("my_param")
    result = await tool_my_action(param, user_id)
    state["execution_result"] = result
```

---

## 🚨 Common Mistakes to Avoid

1. ❌ Don't say "if-else chains" - Say "state machine with conditional edges"
2. ❌ Don't say "simple API" - Say "LangGraph-powered conversational agent"
3. ❌ Don't forget async/await - Everything is async for non-blocking I/O
4. ❌ Don't confuse nodes and edges - Nodes are functions, edges are transitions
5. ❌ Don't forget page context - decision_router validates page before action

---

## 🎤 When They Ask "Any Questions?"

1. "How does the current system handle concurrent updates?"
2. "What's the plan for scaling as fleet grows?"
3. "How do you measure LLM accuracy in production?"
4. "What observability tools do you use?"

---

## ✅ Final Checklist Before Interview

- [ ] Can explain full request flow (6 nodes)
- [ ] Know difference between SAFE and RISKY actions
- [ ] Understand why LangGraph over if-else
- [ ] Can write a new node function
- [ ] Can write a new action handler
- [ ] Know key files and their purpose
- [ ] Can explain LLM integration
- [ ] Understand async/await patterns
- [ ] Know database connection patterns
- [ ] Can explain page context validation

---

**You've got this! 💪**

The project shows:
- ✅ LLM/AI integration skills
- ✅ State machine design patterns
- ✅ Async Python expertise
- ✅ Clean architecture principles
- ✅ Production-ready thinking
