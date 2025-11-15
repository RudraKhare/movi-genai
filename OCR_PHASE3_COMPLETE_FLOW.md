# Complete OCR + Phase 3 Flow Documentation

## 1. OCR Flow - How Image Processing Works (Simplified)

### Overview
OCR (Optical Character Recognition) extracts text from an uploaded image and **directly extracts the trip ID** using regex patterns. No fuzzy matching - simple and direct.

---

### Complete OCR Pipeline (Simplified)

#### Step 1: Image Upload (`agent_image.py`)
```
User uploads image (jpg/png)
    ↓
Validate file type and size
    ↓
Read image bytes
```

#### Step 2: Text Extraction (`app/core/ocr.py`)
```
Google Vision API OCR
    ↓
Extracts ALL text from image:
- Trip names ("Path-3 - 07:30")
- Trip ID ("ID Trip #5")
- Status ("SCHEDULED", "IN PROGRESS")
- Details ("Vehicle:", "Driver:", "Bookings")
    ↓
Returns: {text: "...", confidence: 0.95, success: true}
```

**Example OCR Output**:
```
"Path-3 - 07:30
ID Trip #5
2025-11-11 4
Status: SCHEDULED
Deployment
Vehicle: #123
Driver: John Doe
+ Actions
Bookings
confirmed: 5
seats booked: 10"
```

#### Step 3: Direct Trip ID Extraction (Regex)
```
Apply regex patterns to find trip ID:

Pattern 1: "ID Trip #5" or "Trip ID: 5"
    → Regex: (?:ID\s+Trip\s*#?\s*|Trip\s+ID\s*:?\s*)(\d+)
    → Match: "5"

Pattern 2: "Trip #5" or "#5"
    → Regex: (?:Trip\s*)?#(\d+)
    → Match: "5"

Pattern 3: "ID: 5"
    → Regex: ID[:\s]+(\d+)
    → Match: "5"

Result: trip_id = 5
```

**No fuzzy matching, no candidates, no scoring - just direct extraction!**

#### Step 4: Fetch Trip from Database
```
Query database for trip_id = 5
    ↓
If found:
    - Fetch full trip details
    - Analyze trip state
    - Build available actions
    ↓
If not found:
    - Return error message
```

#### Step 5: Determine Available Actions (`agent_image.py`)
```
Fetch trip details from database
    ↓
Analyze trip state:
- Has vehicle? → "Remove Vehicle" + "Change Driver"
- No vehicle? → "Assign Vehicle"
- Has bookings? → "View Bookings (N)"
- Scheduled? → "Update Time"
- Always: "Get Status", "Get Details", "Duplicate", "Cancel"
    ↓
Build 8-10 action buttons
    ↓
Return: {
        match_type: "single",
        trip_id: 5,
        display_name: "Path-3 - 07:30",
        trip_details: {...},
        available_actions: [...]
    }
```

**Example Available Actions**:
```python
available_actions = [
    {
        "action": "remove_vehicle",
        "label": "🚫 Remove Vehicle",
        "description": "Remove assigned vehicle from this trip"
    },
    {
        "action": "change_driver",
        "label": "👤 Change Driver",
        "description": "Assign a different driver to this trip"
    },
    {
        "action": "get_trip_bookings",
        "label": "👥 View Bookings (5)",
        "description": "View 5 confirmed bookings"
    },
    {
        "action": "get_trip_status",
        "label": "ℹ️ Get Status",
        "description": "View detailed trip status"
    },
    {
        "action": "get_trip_details",
        "label": "📋 Get Details",
        "description": "View comprehensive trip information"
    },
    {
        "action": "update_trip_time",
        "label": "⏰ Update Time",
        "description": "Change trip scheduled time"
    },
    {
        "action": "duplicate_trip",
        "label": "🔄 Duplicate Trip",
        "description": "Create a copy of this trip"
    },
    {
        "action": "cancel_trip",
        "label": "🗑️ Cancel Trip",
        "description": "Cancel trip (⚠️ 5 bookings)",
        "warning": true
    }
]
```

---

### OCR Response Types (Simplified)

#### Type 1: Trip Found (Success)
```json
{
    "match_type": "single",
    "trip_id": 5,
    "display_name": "Path-3 - 07:30",
    "route_name": "Path-3",
    "scheduled_time": "07:30",
    "confidence": 0.92,
    "auto_forward": true,
    "trip_details": {
        "trip_id": 5,
        "trip_name": "Path-3 - 07:30",
        "live_status": "SCHEDULED",
        "vehicle_id": 123,
        "driver_id": 45,
        "booking_count": 5
    },
    "available_actions": [
        {action: "remove_vehicle", label: "🚫 Remove Vehicle"},
        {action: "get_trip_status", label: "ℹ️ Get Status"},
        {action: "cancel_trip", label: "🗑️ Cancel Trip", warning: true}
    ],
    "ocr_text": "Path-3 - 07:30\nID Trip #5...",
    "ocr_confidence": 0.95
}
```

**Frontend displays**:
- ✅ "Found trip: Path-3 - 07:30"
- Trip details card
- 8-10 action buttons in 2-column grid

#### Type 2: Trip ID Not Found
```json
{
    "match_type": "none",
    "message": "Could not find trip ID in image. Please ensure the image shows a clear trip ID.",
    "auto_forward": false,
    "ocr_text": "Some text without trip ID...",
    "ocr_confidence": 0.88
}
```

**Frontend displays**:
- ❌ "Could not find trip ID in image"
- Preview of extracted text
- Suggestion to try image with clear trip ID

#### Type 3: Trip ID Extracted but Not in Database
```json
{
    "match_type": "none",
    "message": "Trip ID 999 was extracted but not found in database.",
    "auto_forward": false,
    "ocr_text": "ID Trip #999...",
    "ocr_confidence": 0.75,
    "extracted_trip_id": 999
}
```

**Frontend displays**:
- ❌ "Trip ID 999 not found in database"
- Suggestion to verify trip ID

---

## 2. Phase 3 Integration - How Suggestions and Wizards Work

### Phase 3 Architecture

#### Key Components
1. **decision_router** - Routes conversation based on context
2. **suggestion_provider** - Builds contextual action suggestions
3. **trip_creation_wizard** - Multi-step guided flows
4. **collect_user_input** - Handles wizard responses
5. **create_trip_suggester** - Offers creation for missing trips

---

### Complete Phase 3 Flow (After OCR)

#### Scenario A: Trip Found via OCR

**Step 1: User uploads image**
```
Frontend → /api/agent/image
    ↓
OCR processes image
    ↓
Returns: {match_type: "single", trip_id: 5, available_actions: [...]}
```

**Step 2: Frontend displays action buttons**
```
Frontend receives response:
    ↓
Renders trip details
    ↓
Renders 5-10 action buttons from available_actions
    ↓
User clicks "📋 Get Details" button
```

**Step 3: Frontend sends action to agent**
```
Frontend → /api/agent/message
Request: {
    text: "Show details for trip 5",
    selectedTripId: 5,  ← OCR-resolved trip ID
    from_image: true     ← Indicates OCR flow
}
```

**Step 4: Graph processes action**
```
agent.py receives request
    ↓
Adds from_image=true flag to state
    ↓
Calls LangGraph with state: {
    text: "Show details for trip 5",
    selectedTripId: 5,
    from_image: true,
    user_id: 1
}
```

**Step 5: parse_intent_llm (Action Detection)**
```
LLM receives: "Show details for trip 5"
    ↓
LLM parses action: "get_trip_details"
    ↓
State after: {
    action: "get_trip_details",
    selectedTripId: 5,
    from_image: true
}
    ↓
LLM OVERRIDE:
If selectedTripId exists:
    state["trip_id"] = 5  ← Use OCR trip ID, not LLM's guess
```

**Step 6: resolve_target (Trip Resolution)**
```
Sees selectedTripId=5 from OCR
    ↓
BYPASS LLM resolution (OCR more accurate)
    ↓
Query database for trip #5
    ↓
State after: {
    action: "get_trip_details",
    trip_id: 5,
    trip_label: "Path-3 - 07:30",
    from_image: true,
    resolve_result: "found"  ← Phase 3 flag
}
```

**Step 7: decision_router (Routing Logic)**
```
Check conditions:
- action: "get_trip_details"
- trip_id: 5 (exists)
- from_image: true
- resolve_result: "found"
    ↓
Route A Match: Trip found + from_image → suggestion_provider
    ↓
state["next_node"] = "suggestion_provider"
```

**Step 8: suggestion_provider (Build Suggestions)**
```
Fetch trip details for trip #5
    ↓
Analyze trip state:
- vehicle_id: 123 (has vehicle)
- booking_count: 5
- live_status: "SCHEDULED"
    ↓
Build 10-12 contextual suggestions:
[
    {action: "remove_vehicle", label: "🚫 Remove Vehicle"},
    {action: "change_driver", label: "👤 Change Driver"},
    {action: "get_trip_bookings", label: "👥 View Bookings (5)"},
    {action: "get_trip_details", label: "📋 Trip Details"},
    {action: "update_trip_time", label: "⏰ Update Time"},
    {action: "duplicate_trip", label: "🔄 Duplicate Trip"},
    {action: "create_followup_trip", label: "➕ Follow-up Trip"},
    {action: "cancel_trip", label: "🗑️ Cancel (⚠️ 5 bookings)", warning: true}
]
    ↓
State after: {
    suggestions: [...],
    message: "What would you like to do with this trip?"
}
```

**Step 9: report_result (Format Response)**
```
Format suggestions for frontend
    ↓
Return: {
    action: "show_trip_suggestions",
    status: "success",
    suggestions: [...],
    trip_id: 5,
    message: "What would you like to do?"
}
```

**Step 10: Frontend renders suggestions**
```
Frontend receives suggestions array
    ↓
Renders in 2-column grid:
┌──────────────────┬──────────────────┐
│ 🚫 Remove Vehicle│ 👤 Change Driver │
├──────────────────┼──────────────────┤
│ 👥 View Bookings │ 📋 Trip Details  │
├──────────────────┼──────────────────┤
│ ⏰ Update Time   │ 🔄 Duplicate     │
├──────────────────┼──────────────────┤
│ 🗑️ Cancel (⚠️)  │ ➕ Follow-up     │
└──────────────────┴──────────────────┘
```

---

#### Scenario B: Trip NOT Found via OCR

**Step 1: OCR returns no match**
```
OCR processes image
    ↓
No trips match extracted text
    ↓
Returns: {match_type: "none", message: "No trips found"}
```

**Step 2: User types follow-up**
```
Frontend → /api/agent/message
Request: {
    text: "Create a new trip",
    from_image: false  ← No OCR trip
}
```

**Step 3: parse_intent_llm**
```
LLM parses: "Create a new trip"
    ↓
action: "create_trip_from_scratch"
```

**Step 4: decision_router**
```
Check conditions:
- action: "create_trip_from_scratch"
- from_image: false
- resolve_result: "none"
    ↓
Route D Match: Creation action → trip_creation_wizard
    ↓
state["next_node"] = "trip_creation_wizard"
state["wizard_type"] = "create_trip_from_scratch"
```

**Step 5: trip_creation_wizard (Start Wizard)**
```
Initialize wizard:
- wizard_type: "create_trip_from_scratch"
- wizard_step: 0
- wizard_steps_total: 7
- wizard_data: {}
    ↓
Load Step 1: "What should we call this trip?"
    ↓
State after: {
    wizard_active: true,
    wizard_step: 0,
    wizard_question: "What should we call this trip?",
    wizard_data: {},
    awaiting_wizard_input: true
}
```

**Step 6: Frontend renders wizard UI**
```
Frontend receives wizard state
    ↓
Renders wizard UI:
┌─────────────────────────────────────┐
│ 🧙‍♂️ Creation Wizard   Step 1 / 7    │
│ ███░░░░░░░░░░░░░░░░░░░░ 14%        │
├─────────────────────────────────────┤
│ What should we call this trip?      │
│ 💡 e.g., "Morning Express"         │
├─────────────────────────────────────┤
│           ✗ Cancel Wizard           │
└─────────────────────────────────────┘
```

**Step 7: User provides input**
```
User types: "Morning Express"
    ↓
Frontend → /api/agent/message
Request: {
    text: "Morning Express",
    session_id: "abc-123"  ← Persists wizard state
}
```

**Step 8: agent.py loads wizard state**
```
Query agent_sessions table:
    ↓
Load wizard state: {
    wizard_active: true,
    wizard_type: "create_trip_from_scratch",
    wizard_step: 0,
    wizard_data: {}
}
    ↓
Merge into input_state
```

**Step 9: collect_user_input (Validate Input)**
```
Receive user input: "Morning Express"
    ↓
Validate: Is it valid trip name? ✅
    ↓
Store in wizard_data: {
    trip_name: "Morning Express"
}
    ↓
Advance to next step: wizard_step = 1
    ↓
state["next_node"] = "trip_creation_wizard"
```

**Step 10: trip_creation_wizard (Next Step)**
```
Load Step 2: "What date? (YYYY-MM-DD)"
    ↓
State after: {
    wizard_active: true,
    wizard_step: 1,
    wizard_question: "What date? (YYYY-MM-DD)",
    wizard_data: {trip_name: "Morning Express"},
    awaiting_wizard_input: true
}
```

**Step 11: agent.py persists wizard state**
```
Save to agent_sessions:
UPDATE agent_sessions
SET pending_action = {
    wizard_active: true,
    wizard_type: "create_trip_from_scratch",
    wizard_step: 1,
    wizard_data: {trip_name: "Morning Express"}
}
WHERE session_id = "abc-123"
```

**Step 12: Frontend updates wizard UI**
```
┌─────────────────────────────────────┐
│ 🧙‍♂️ Creation Wizard   Step 2 / 7    │
│ ██████░░░░░░░░░░░░░░░░░░ 29%       │
├─────────────────────────────────────┤
│ What date? (YYYY-MM-DD)             │
│ 💡 e.g., "2024-01-15"              │
├─────────────────────────────────────┤
│ 📝 Collected so far:                │
│   • trip_name: Morning Express      │
├─────────────────────────────────────┤
│           ✗ Cancel Wizard           │
└─────────────────────────────────────┘
```

**Steps 13-18: Continue wizard (5 more steps)**
```
Step 2: Date → "2024-01-15"
Step 3: Time → "08:30"
Step 4: Route → Select from options
Step 5: Vehicle → Select from available
Step 6: Driver → Select from available
Step 7: Confirm → "yes"
```

**Step 19: trip_creation_wizard (Execute)**
```
All 7 steps completed
    ↓
wizard_data: {
    trip_name: "Morning Express",
    trip_date: "2024-01-15",
    scheduled_time: "08:30",
    route_id: 3,
    vehicle_id: 123,
    driver_id: 45
}
    ↓
Call service layer:
await create_trip(
    route_id=3,
    trip_date="2024-01-15",
    scheduled_time="08:30",
    vehicle_id=123,
    driver_id=45
)
    ↓
Returns: {ok: true, trip_id: 99}
    ↓
State after: {
    wizard_completed: true,
    message: "✅ Trip created successfully! ID: 99"
}
```

**Step 20: agent.py clears wizard state**
```
UPDATE agent_sessions
SET status = 'DONE',
    pending_action = NULL
WHERE session_id = "abc-123"
```

---

## 3. Critical Integration Points

### Point 1: agent.py → Graph
**File**: `backend/app/api/agent.py`

```python
# Prepare input state
input_state = {
    "text": request.text,
    "user_id": request.user_id,
    "selectedTripId": request.selectedTripId,  # From OCR
    "from_image": bool(request.selectedTripId),  # ✅ Phase 3 flag
    **wizard_state  # ✅ Loaded from session
}
```

### Point 2: parse_intent_llm → LLM Override
**File**: `backend/langgraph/nodes/parse_intent_llm.py`

```python
# LLM parses action
llm_response = await parse_intent_with_llm(text, context)
state["action"] = llm_response.get("action")

# OVERRIDE: If OCR provided trip_id, use it (more accurate)
if selected_trip_id:
    state["trip_id"] = selected_trip_id  # ✅ OCR wins
```

### Point 3: resolve_target → Resolution Result
**File**: `backend/langgraph/nodes/resolve_target.py`

```python
# OCR bypass
if selected_trip_id:
    trip_row = await fetch_trip(selected_trip_id)
    if trip_row:
        state["trip_id"] = trip_row["trip_id"]
        state["resolve_result"] = "found"  # ✅ Phase 3 flag
    else:
        state["resolve_result"] = "none"   # ✅ Phase 3 flag
```

### Point 4: decision_router → Routing Logic
**File**: `backend/langgraph/nodes/decision_router.py`

```python
# Route A: Trip found + from_image → suggestions
if trip_id and from_image and resolve_result == "found":
    state["next_node"] = "suggestion_provider"  # ✅ Phase 3 route

# Route B: Trip not found + from_image → offer creation
if from_image and resolve_result == "none":
    state["next_node"] = "create_trip_suggester"  # ✅ Phase 3 route

# Route D: Creation actions → wizard
if action in creation_actions:
    state["next_node"] = "trip_creation_wizard"  # ✅ Phase 3 route
```

---

## 4. State Persistence Flow

### Wizard State Lifecycle

**1. Wizard Starts**
```python
# trip_creation_wizard.py
state = {
    "wizard_active": True,
    "wizard_type": "create_trip_from_scratch",
    "wizard_step": 0,
    "wizard_data": {}
}
```

**2. agent.py Persists State**
```python
# After graph execution
if result_state.get("wizard_active"):
    await conn.execute("""
        INSERT INTO agent_sessions (session_id, pending_action)
        VALUES ($1, $2)
        ON CONFLICT (session_id) DO UPDATE
        SET pending_action = $2
    """, session_id, json.dumps(wizard_state))
```

**3. User Refreshes Page**
```
Browser reloads → New request
```

**4. agent.py Loads State**
```python
# Before graph execution
if session_id:
    row = await conn.fetchrow("""
        SELECT pending_action FROM agent_sessions
        WHERE session_id=$1
    """, session_id)
    
    if row["pending_action"].get("wizard_active"):
        wizard_state = row["pending_action"]
        # Merge into input_state
```

**5. Wizard Continues**
```
User on Step 3/7 before refresh
    ↓
Page reloads
    ↓
Wizard state loaded
    ↓
User continues from Step 3/7 ✅
```

**6. Wizard Completes**
```python
# trip_creation_wizard.py
if wizard_step == wizard_steps_total - 1:
    # Execute creation
    result = await create_trip(wizard_data)
    state["wizard_completed"] = True
```

**7. agent.py Clears State**
```python
if result_state.get("wizard_completed"):
    await conn.execute("""
        UPDATE agent_sessions
        SET status='DONE', pending_action=NULL
        WHERE session_id=$1
    """, session_id)
```

---

## 5. Error Handling and Edge Cases

### Edge Case 1: OCR Extracts Wrong Trip
**Problem**: User uploaded image of trip #5, OCR matched trip #8

**Solution**:
```
User clicks action button → Action sent with trip_id=8
    ↓
System uses OCR trip_id (8), not text-mentioned trip_id
    ↓
Executes action on trip #8 ✅
    ↓
User sees: "Updated trip #8"
    ↓
If wrong: User can clarify with new text
```

### Edge Case 2: Wizard Cancelled Mid-Flow
**Problem**: User at Step 4/7, clicks "Cancel Wizard"

**Solution**:
```
User clicks "✗ Cancel Wizard"
    ↓
Frontend sends: text="cancel"
    ↓
collect_user_input detects "cancel"
    ↓
Sets: wizard_cancelled=True
    ↓
agent.py clears session state
    ↓
Returns: "❌ Wizard cancelled"
```

### Edge Case 3: Page Refresh During Wizard
**Problem**: User at Step 3/7, page refreshes

**Solution**:
```
Page reloads → New /api/agent/message request
    ↓
agent.py loads wizard state from DB
    ↓
Merges into input_state
    ↓
Graph continues from Step 3/7 ✅
```

### Edge Case 4: LLM Timeout
**Problem**: LLM takes too long (>30 seconds)

**Solution**:
```python
try:
    response = await asyncio.wait_for(
        llm_call(), 
        timeout=30.0
    )
except asyncio.TimeoutError:
    # Fallback to keyword matching
    action = detect_action_keywords(text)
```

---

## 6. Testing Scenarios

### Test 1: OCR → Suggestions (Route A)
```
1. Upload image of trip #5
2. OCR extracts text, matches trip #5
3. Frontend displays trip details + 5-10 action buttons
4. Click "📋 Get Details"
5. System shows trip details ✅
```

### Test 2: OCR → No Match → Create (Route B)
```
1. Upload image with unrecognized text
2. OCR returns: match_type="none"
3. User types: "Create a new trip"
4. Wizard starts with 7 steps
5. User completes all steps
6. Trip created successfully ✅
```

### Test 3: Wizard State Persistence
```
1. Start trip wizard
2. Complete Step 1: Name
3. Complete Step 2: Date
4. Refresh page (F5)
5. Wizard resumes at Step 3 ✅
6. Continue and complete wizard
```

### Test 4: Suggestion Click
```
1. Upload image → Trip found
2. See 10 suggestion buttons
3. Click "👥 View Bookings"
4. System shows bookings table ✅
```

---

## 7. Phase 3 Status Summary

### ✅ Implemented (100%)
- [x] OCR flow with trip matching
- [x] Suggestion provider (10-12 contextual actions)
- [x] Trip creation wizard (7 steps)
- [x] Route/path/stop wizards
- [x] Wizard state persistence
- [x] from_image flag propagation
- [x] resolve_result flag for routing
- [x] LLM override with OCR trip_id
- [x] decision_router with 7 routing paths
- [x] Frontend suggestion buttons
- [x] Frontend wizard UI

### 🐛 Fixed Issues
- [x] Missing from_image flag in agent.py
- [x] Missing resolve_result in resolve_target.py
- [x] LLM bypass that was blocking action detection
- [x] Tool exports in tools/__init__.py
- [x] Syntax error in llm_client.py

### ✅ All Phase 3 Components Working
1. **decision_router** ✅
2. **suggestion_provider** ✅
3. **create_trip_suggester** ✅
4. **trip_creation_wizard** ✅
5. **collect_user_input** ✅
6. **Wizard state persistence** ✅
7. **Frontend UI** ✅

---

## Conclusion

**OCR Role (Simplified)**: Extract ALL text from images and use **regex patterns to directly extract trip ID**. No fuzzy matching, no candidate generation, no scoring - just simple, direct extraction.

**How It Works**:
1. Google Vision OCR extracts all text
2. Regex patterns find trip ID (e.g., "ID Trip #5" → 5)
3. Database lookup by trip_id
4. Return trip details + 8-10 contextual actions

**Phase 3 Role**: Provide conversational intelligence on top of OCR:
- Suggestions when trip found (Route A)
- Offer creation when not found (Route B)
- Guided wizards for complex tasks (Route D)
- State persistence for multi-turn flows

**Status**: Both OCR (simplified) and Phase 3 are 100% implemented and fully integrated. Ready for production! 🚀

