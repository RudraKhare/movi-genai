# LLM Integration - Quick Start Guide

## ✅ What's Done

1. **Environment Variables** - Added to `.env`:
   - `USE_LLM_PARSE=true`
   - `OPENAI_API_KEY=<your-key>`
   - `LLM_MODEL=gpt-4o-mini`

2. **LLM Client** - Created `langgraph/tools/llm_client.py`:
   - OpenAI integration with JSON mode
   - Ollama support for local LLMs
   - Strict schema validation
   - Error handling & timeouts
   - Few-shot examples for accuracy

## 🎯 What's Next (Critical Path)

### Step 1: Create `parse_intent_llm.py` (⏱️ 20 min)

```bash
# File: backend/langgraph/nodes/parse_intent_llm.py
```

**Quick Template:**
```python
from langgraph.tools.llm_client import parse_intent_with_llm

async def parse_intent_llm(state: Dict) -> Dict:
    # 1. Skip if OCR provided trip ID
    if state.get("selectedTripId"):
        logger.info("[LLM] Skipping LLM - OCR trip ID present")
        return state  # OCR bypass
    
    # 2. Call LLM
    text = state.get("text", "")
    context = {
        "currentPage": state.get("currentPage"),
        "selectedRouteId": state.get("selectedRouteId"),
    }
    llm_result = await parse_intent_with_llm(text, context)
    
    # 3. Merge into state
    state["action"] = llm_result["action"]
    state["target_label"] = llm_result["target_label"]
    state["confidence"] = llm_result["confidence"]
    state["llm_explanation"] = llm_result["explanation"]
    state["parsed_params"] = llm_result["parameters"]
    
    # 4. Handle clarification
    if llm_result["clarify"]:
        state["needs_clarification"] = True
        state["clarify_options"] = llm_result["clarify_options"]
    
    return state
```

---

### Step 2: Modify `graph_def.py` (⏱️ 10 min)

**Add at top:**
```python
import os
from langgraph.nodes.parse_intent_llm import parse_intent_llm

USE_LLM_PARSE = os.getenv("USE_LLM_PARSE", "false").lower() == "true"
```

**Replace entry node connection:**
```python
# OLD:
# graph.add_edge("entry", "parse_intent")

# NEW:
if USE_LLM_PARSE:
    graph.add_edge("entry", "parse_intent_llm")
    graph.add_edge("parse_intent_llm", "resolve_target")
else:
    graph.add_edge("entry", "parse_intent")
    graph.add_edge("parse_intent", "resolve_target")
```

---

### Step 3: Update `resolve_target.py` (⏱️ 30 min)

**Add after OCR bypass section (after line 54):**
```python
# LLM Trip ID Verification
llm_trip_id = state.get("parsed_params", {}).get("target_trip_id")
if llm_trip_id:
    logger.info(f"[LLM_VERIFY] Checking trip_id: {llm_trip_id}")
    # Verify with DB
    from langgraph.tools import tool_get_trip_status
    trip_info = await tool_get_trip_status(llm_trip_id)
    
    if trip_info and trip_info.get("exists"):
        state["trip_id"] = llm_trip_id
        state["trip_label"] = trip_info["display_name"]
        return state
    else:
        logger.warning(f"[LLM_VERIFY] Invalid trip_id, falling back")
```

**Update label search (line 67):**
```python
# OLD:
# trip_label = text

# NEW:
trip_label = state.get("target_label") or text
```

---

## 🧪 Quick Test

### 1. With Flag OFF (Old Behavior):
```bash
USE_LLM_PARSE=false
# Restart server
# Upload image → Should work as before
```

### 2. With Flag ON (New Behavior):
```bash
USE_LLM_PARSE=true
# Restart server
# Type: "cancel the morning bulk trip"
# Expected: LLM parses → DB verifies → Shows confirmation
```

### 3. Test OCR Bypass:
```bash
USE_LLM_PARSE=true
# Upload image with trip
# Expected: Skips LLM, uses OCR trip_id directly
```

---

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not configured"
```bash
# Check .env file
cat backend/.env | grep OPENAI

# Solution: Add to .env:
OPENAI_API_KEY=sk-proj-...
```

### Error: "Module 'llm_client' not found"
```bash
# Check file exists
ls backend/langgraph/tools/llm_client.py

# Restart server
python -m uvicorn app.main:app --reload
```

### LLM Returns "unknown" action
```bash
# Check logs for LLM response
# May need to adjust confidence threshold
# Or add more few-shot examples
```

---

## 📊 What Each File Does

| File | Purpose | Status |
|------|---------|--------|
| `.env` | Config | ✅ Done |
| `llm_client.py` | LLM wrapper | ✅ Done |
| `parse_intent_llm.py` | LLM node | ❌ TODO |
| `graph_def.py` | Graph routing | ❌ TODO |
| `resolve_target.py` | DB verification | ❌ TODO |
| `report_result.py` | Output formatting | 🟡 Later |
| `agent.py` | API endpoint | 🟡 Later |

---

## 🚨 Safety Notes

- **Feature flag** allows instant rollback
- **OCR flow** bypasses LLM completely
- **DB tools** verify all LLM suggestions
- **Confirmation** still required for destructive actions
- **Old behavior** preserved when flag=false

---

## 📝 Example Interactions

### 1. Natural Language → LLM Parse
```
User: "Cancel the morning bulk trip"
LLM: {action: "cancel_trip", target_label: "Bulk", confidence: 0.75, clarify: true}
System: Shows options: ["Bulk - 00:01", "Bulk - 08:00"]
User: Clicks "Bulk - 08:00"
System: Shows confirmation with bookings count
```

### 2. Ambiguous → Clarification
```
User: "Remove vehicle from 7:30"
LLM: {action: "remove_vehicle", clarify: true, options: ["Path-3 - 07:30", "Path-3 - 19:30"]}
System: Shows both options
User: Selects "Path-3 - 07:30"
System: Verifies in DB → Shows confirmation
```

### 3. OCR → Skip LLM
```
User: Uploads image of "Path-1 - 08:00"
OCR: Returns trip_id=1
System: Skips LLM completely
System: Shows "Identified: Path-1 - 08:00" + action buttons
User: Clicks "Cancel Trip"
System: Shows confirmation
```

---

## 🎯 Success Metrics

After implementation:
- [ ] Can parse natural language commands
- [ ] LLM asks for clarification when unsure
- [ ] DB rejects hallucinated trip IDs
- [ ] OCR flow still works
- [ ] Confirmation dialog appears
- [ ] Actions execute correctly
- [ ] Old behavior works with flag=false

---

**Ready to implement! Start with `parse_intent_llm.py` 🚀**
