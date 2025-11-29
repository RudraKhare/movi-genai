# 🔥 MOVI Advanced Interview Questions - Architecture & Scenarios

## Table of Contents
1. [Architecture Decisions](#1-architecture-decisions)
2. [Scenario-Based Questions](#2-scenario-based-questions)
3. [Debugging Questions](#3-debugging-questions)
4. [Extension & Modification Questions](#4-extension--modification-questions)
5. [Production Readiness](#5-production-readiness)
6. [System Design Questions](#6-system-design-questions)

---

## 1. Architecture Decisions

### Q1.1: "Why use a state machine (LangGraph) instead of simple if-else chains?"

**Answer:**

**If-else approach:**
```python
async def process_message(text, context):
    action = parse_intent(text)
    
    if action == "cancel_trip":
        trip = resolve_trip(text, context)
        if trip:
            bookings = get_bookings(trip.id)
            if bookings:
                return ask_confirmation(...)
            else:
                return cancel_trip(trip.id)
        else:
            return "Trip not found"
    
    elif action == "assign_vehicle":
        # Similar nested logic...
    
    # 40+ more actions...
```

**Problems:**
1. **Spaghetti code**: Nested conditions become unreadable
2. **No reusability**: Each action duplicates logic (resolve, confirm, execute)
3. **Hard to test**: Can't test individual steps
4. **Hard to modify**: Adding new step affects all paths

**State machine approach:**
```python
# Each concern is a separate node
graph.add_node("parse_intent", parse_intent)
graph.add_node("resolve_target", resolve_target)  # Reused by ALL actions
graph.add_node("check_consequences", check_consequences)  # Shared logic
graph.add_node("execute_action", execute_action)

# Flow is explicit and visual
parse_intent → resolve_target → decision_router → ...
```

**Benefits:**
1. **Separation of concerns**: Each node has one job
2. **Reusability**: resolve_target used by 40+ actions
3. **Testability**: Test each node independently
4. **Visibility**: Graph structure is self-documenting
5. **Extensibility**: Add new node without changing others

---

### Q1.2: "Why does decision_router exist? Couldn't each node decide its next step?"

**Answer:**

**Without decision_router:**
```python
# Each node would need routing logic
async def resolve_target(state):
    # ... resolve logic ...
    
    # Routing scattered everywhere
    if state["action"] in creation_actions:
        state["next_node"] = "trip_creation_wizard"
    elif state["from_image"]:
        state["next_node"] = "suggestion_provider"
    elif state["action"] in risky_actions:
        state["next_node"] = "check_consequences"
    # ...
    
    return state
```

**Problems:**
1. **Scattered routing**: Logic spread across multiple files
2. **Coupling**: resolve_target knows about 10+ other nodes
3. **Testing nightmare**: Must mock many nodes
4. **Changes are risky**: Modify one place, break many flows

**With decision_router:**
```python
# resolve_target is pure - just resolves targets
async def resolve_target(state):
    # ... only resolve logic ...
    return state

# ALL routing in ONE place
async def decision_router(state):
    action = state["action"]
    
    # Page context validation
    if not is_action_allowed_on_page(action, state["currentPage"]):
        return route_to_error(state)
    
    # Wizard flows
    if action in creation_actions:
        return route_to_wizard(state)
    
    # OCR flows
    if state["from_image"]:
        return route_to_suggestion(state)
    
    # Normal flows
    return route_to_consequences(state)
```

**Benefits:**
1. **Single source of truth**: All routing in one file
2. **Easy to understand**: "Where does X go? Check decision_router"
3. **Easy to modify**: Add new route in one place
4. **Easy to test**: Mock decision_router to test any path

---

### Q1.3: "Why is confirmation stored in database instead of memory/Redis?"

**Answer:**

**Memory approach:**
```python
pending_actions = {}  # In-memory dict

async def save_pending(session_id, action):
    pending_actions[session_id] = action

async def get_pending(session_id):
    return pending_actions.get(session_id)
```

**Problems:**
1. **Lost on restart**: Server restart loses all pending actions
2. **No scaling**: Memory not shared across instances
3. **No audit trail**: Can't see historical confirmations

**Database approach:**
```python
async def save_pending(session_id, action):
    await conn.execute("""
        INSERT INTO agent_sessions (session_id, pending_action, status, created_at)
        VALUES ($1, $2, 'PENDING', NOW())
    """, session_id, json.dumps(action))

async def get_pending(session_id):
    row = await conn.fetchrow(
        "SELECT pending_action FROM agent_sessions WHERE session_id=$1",
        session_id
    )
    return json.loads(row["pending_action"]) if row else None
```

**Benefits:**
1. **Persistence**: Survives restarts, deployments
2. **Scalability**: Works with multiple API instances
3. **Audit trail**: Query historical sessions
4. **Debugging**: See what users tried to do
5. **Resume**: User can confirm even after page refresh

**When to use Redis:**
> For high-volume, short-lived sessions. Current volume doesn't justify complexity.

---

### Q1.4: "Why check page context in decision_router and not in frontend?"

**Answer:**

**Frontend-only approach:**
```javascript
// Frontend hides buttons based on page
if (currentPage === "manageRoute") {
    // Don't show "Assign Vehicle" button
}
```

**Problem:**
```javascript
// But user can type in chat!
"assign vehicle to trip 42"  // This would still work!
```

**Backend validation (defense in depth):**
```python
async def decision_router(state):
    action = state["action"]
    current_page = state["currentPage"]
    
    if current_page == "manageRoute" and action in BUS_DASHBOARD_ACTIONS:
        state["message"] = "⚠️ This action is only available on Bus Dashboard"
        state["next_node"] = "report_result"
        return state
```

**Why both:**
1. **Frontend**: Better UX (hide invalid options)
2. **Backend**: Security (enforce rules regardless of client)
3. **Principle**: Never trust client input

---

## 2. Scenario-Based Questions

### Q2.1: "User says 'assign the blue bus to trip 42'. How does system handle 'blue bus'?"

**Answer:**

```python
# 1. LLM parses intent
# User: "assign the blue bus to trip 42"
llm_response = {
    "action": "assign_vehicle",
    "target_trip_id": 42,
    "parameters": {
        "vehicle_registration": None,  # LLM doesn't know reg
        "vehicle_description": "blue bus"  # Captured as description
    },
    "confidence": 0.7,  # Lower confidence
    "clarify": True,
    "clarify_options": ["Which vehicle? I found: Bus-101, Bus-102"]
}

# 2. We could enhance to search by description
async def find_vehicle_by_description(description: str):
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Search in vehicle notes/color field if exists
        rows = await conn.fetch("""
            SELECT vehicle_id, registration_number, color, notes
            FROM vehicles
            WHERE color ILIKE $1 OR notes ILIKE $1
        """, f"%{description}%")
        return [dict(r) for r in rows]

# 3. If multiple matches, ask for clarification
if len(vehicles) > 1:
    state["needs_clarification"] = True
    state["clarify_options"] = [v["registration_number"] for v in vehicles]
    state["message"] = "Found multiple blue buses. Which one?"

# 4. If single match, use it
elif len(vehicles) == 1:
    state["parsed_params"]["vehicle_id"] = vehicles[0]["vehicle_id"]
```

**Current limitation:** We don't have a color field. Would require schema change.

---

### Q2.2: "User uploads image with trip ID 50. But trip 50 was cancelled yesterday. What happens?"

**Answer:**

```python
# Flow trace:

# 1. OCR extracts trip ID from image
state["selectedTripId"] = 50
state["from_image"] = True

# 2. resolve_target verifies
async def resolve_target(state):
    trip_id = state.get("selectedTripId")
    
    pool = await get_conn()
    async with pool.acquire() as conn:
        trip = await conn.fetchrow(
            "SELECT * FROM daily_trips WHERE trip_id=$1",
            trip_id
        )
    
    if trip:
        # Check if cancelled
        if trip["live_status"] == "CANCELLED":
            state["error"] = "trip_cancelled"
            state["message"] = f"⚠️ Trip {trip_id} was cancelled. Would you like to see similar active trips?"
            state["suggestions"] = await find_similar_trips(trip)
            return state
        
        # Check if in past
        if trip["trip_date"] < date.today():
            state["error"] = "trip_past"
            state["message"] = f"⚠️ Trip {trip_id} was scheduled for {trip['trip_date']}. It's now in the past."
            return state
        
        # Valid - proceed
        state["trip_id"] = trip["trip_id"]
        state["resolve_result"] = "found"
    else:
        state["error"] = "trip_not_found"
        state["message"] = f"Trip {trip_id} not found in system"
    
    return state

# 3. decision_router sees error, routes to fallback/report
if state.get("error"):
    state["next_node"] = "report_result"
```

---

### Q2.3: "Two users try to assign different vehicles to same trip simultaneously. What happens?"

**Answer:**

```python
# Request 1: User A assigns Vehicle 5 to Trip 42
# Request 2: User B assigns Vehicle 7 to Trip 42
# Both hit execute_action at ~same time

# Without protection:
# Both would succeed, second overwrites first
# User A thinks Vehicle 5 is assigned, but it's actually Vehicle 7

# With transaction + locking:
async def tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id):
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Lock the deployment row for this trip
            existing = await conn.fetchrow("""
                SELECT * FROM deployments 
                WHERE trip_id = $1 
                FOR UPDATE  -- Exclusive lock
            """, trip_id)
            
            # Now only one request can proceed
            # Other waits for transaction to complete
            
            if existing:
                # Check if it was just modified
                last_modified = existing["updated_at"]
                if last_modified > request_start_time:
                    # Someone else just modified it!
                    return {
                        "ok": False,
                        "error": "concurrent_modification",
                        "message": f"Trip was just modified. Please refresh and try again."
                    }
                
                # Update
                await conn.execute("""
                    UPDATE deployments 
                    SET vehicle_id=$1, driver_id=$2, updated_at=NOW()
                    WHERE trip_id=$3
                """, vehicle_id, driver_id, trip_id)
            else:
                # Insert
                await conn.execute(...)
        
        # Transaction commits, lock released
```

**Additional safeguards:**
1. **Optimistic locking**: Check version/timestamp before update
2. **Frontend refresh**: Poll for changes
3. **WebSocket**: Push updates to other users

---

### Q2.4: "User says 'cancel all trips tomorrow'. How do you handle bulk operations?"

**Answer:**

```python
# 1. LLM parses
llm_response = {
    "action": "cancel_trip",  # Singular, but plural intent
    "target_date": "tomorrow",
    "is_bulk": True,  # LLM detects bulk intent
    "confidence": 0.85
}

# 2. Custom handling for bulk operations
async def handle_bulk_cancel(state):
    target_date = date.today() + timedelta(days=1)
    
    # Find all trips for tomorrow
    pool = await get_conn()
    async with pool.acquire() as conn:
        trips = await conn.fetch("""
            SELECT trip_id, display_name, 
                   (SELECT COUNT(*) FROM bookings b WHERE b.trip_id = t.trip_id) as booking_count
            FROM daily_trips t
            WHERE trip_date = $1 AND live_status = 'SCHEDULED'
        """, target_date)
    
    if not trips:
        state["message"] = f"No scheduled trips found for {target_date}"
        return state
    
    total_bookings = sum(t["booking_count"] for t in trips)
    
    # ALWAYS require confirmation for bulk
    state["needs_confirmation"] = True
    state["confirmation_required"] = True
    state["consequences"] = {
        "trip_count": len(trips),
        "total_bookings": total_bookings,
        "trips": [dict(t) for t in trips]
    }
    state["message"] = f"""
⚠️ **BULK OPERATION**

You are about to cancel **{len(trips)} trips** scheduled for tomorrow.

This will affect **{total_bookings} passengers**.

Trips to be cancelled:
{chr(10).join(f"• {t['display_name']} ({t['booking_count']} bookings)" for t in trips[:5])}
{"... and " + str(len(trips)-5) + " more" if len(trips) > 5 else ""}

❓ Are you ABSOLUTELY sure you want to proceed?
"""
    
    # Save bulk action for confirmation
    state["pending_action"] = {
        "action": "bulk_cancel_trips",
        "trip_ids": [t["trip_id"] for t in trips],
        "target_date": str(target_date)
    }
    
    return state
```

**Key considerations:**
1. **Explicit bulk flag**: LLM must recognize bulk intent
2. **Detailed preview**: Show user exactly what will happen
3. **Mandatory confirmation**: Never auto-execute bulk operations
4. **Rate limiting**: Limit bulk operations per user per day
5. **Audit logging**: Log who did bulk operation and why

---

## 3. Debugging Questions

### Q3.1: "User says 'assign vehicle' but nothing happens. How do you debug?"

**Answer:**

```python
# Step 1: Check request reached backend
# Look in FastAPI logs
logger.info(f"Received agent message: {request.text}")

# Step 2: Trace through nodes
# Each node logs entry and exit

# parse_intent_llm logs:
logger.info(f"[LLM] Processing: '{text}'")
logger.info(f"[LLM] Action: {action}, confidence: {confidence}")

# If action is "unknown":
# → LLM didn't understand. Check prompt, add patterns.

# resolve_target logs:
logger.info(f"[RESOLVE] Looking for trip: {target_label}")
logger.info(f"[RESOLVE] Found: {trip_id}" or "[RESOLVE] Not found")

# If trip not found:
# → Check target_label extraction, check DB data

# decision_router logs:
logger.info(f"[ROUTER] Action: {action}, page: {currentPage}")
logger.info(f"[ROUTER] next_node: {next_node}")

# If routed to fallback/error:
# → Check page context rules

# check_consequences logs:
logger.info(f"[CONSEQUENCES] Action {action} is SAFE/RISKY")

# execute_action logs:
logger.info(f"[EXECUTE] Running: {action}")
logger.info(f"[EXECUTE] Result: {result}")

# Step 3: Check database
# Did deployment actually change?
SELECT * FROM deployments WHERE trip_id = X;
SELECT * FROM audit_log WHERE entity_id = X ORDER BY created_at DESC;

# Step 4: Check response
# What did frontend receive?
logger.info(f"Final output: {state['final_output']}")
```

**Debugging checklist:**
1. ✅ Request received? (FastAPI log)
2. ✅ Action parsed correctly? (parse_intent log)
3. ✅ Trip resolved? (resolve_target log)
4. ✅ Routed correctly? (decision_router log)
5. ✅ Executed? (execute_action log)
6. ✅ Response sent? (report_result log)
7. ✅ Database changed? (SQL query)

---

### Q3.2: "LLM returns confidence 0.3 but user is frustrated that it didn't work. How to improve?"

**Answer:**

```python
# Current behavior: Low confidence → clarify
if confidence < 0.6:
    state["needs_clarification"] = True
    state["clarify_options"] = llm_response.get("clarify_options", [])

# Problem: Vague clarification options frustrate users

# Improvement 1: Better clarify_options from LLM
SYSTEM_PROMPT += """
When clarify=true, provide SPECIFIC actionable options:
BAD: ["Please clarify", "What do you mean?"]
GOOD: ["Did you mean trip 'Path-1 - 08:00' or 'Path-2 - 08:00'?", 
       "I found these trips: 1) ... 2) ... Which one?"]
"""

# Improvement 2: Auto-suggest based on context
if confidence < 0.6 and state.get("selectedTripId"):
    # User has a trip selected - probably means that one
    state["suggestions"] = [{
        "action": detected_action,
        "target": f"the selected trip (#{state['selectedTripId']})",
        "button": f"Yes, {detected_action} trip #{state['selectedTripId']}"
    }]

# Improvement 3: Learn from user corrections
# Store low-confidence interactions
await log_low_confidence(
    text=text,
    detected_action=action,
    confidence=confidence,
    user_correction=None  # Filled when user corrects
)

# Later, analyze patterns to improve prompts
# "Users who said X usually meant Y"
```

---

### Q3.3: "Database query in resolve_target is slow (2 seconds). How to optimize?"

**Answer:**

```python
# Current slow query:
SELECT * FROM daily_trips 
WHERE LOWER(display_name) LIKE LOWER('%' || $1 || '%')
ORDER BY trip_date DESC

# Problem: Full table scan, no index on display_name

# Optimization 1: Add indexes
CREATE INDEX idx_trips_display_name ON daily_trips(LOWER(display_name));
CREATE INDEX idx_trips_date ON daily_trips(trip_date DESC);

# Optimization 2: Limit results
SELECT * FROM daily_trips 
WHERE LOWER(display_name) LIKE LOWER($1 || '%')  -- Prefix match uses index
  AND trip_date >= CURRENT_DATE  -- Only future trips
ORDER BY trip_date 
LIMIT 10;  -- Don't need all matches

# Optimization 3: Full-text search
ALTER TABLE daily_trips ADD COLUMN search_vector tsvector;
CREATE INDEX idx_trips_search ON daily_trips USING gin(search_vector);

UPDATE daily_trips SET search_vector = to_tsvector(display_name);

SELECT * FROM daily_trips 
WHERE search_vector @@ plainto_tsquery($1)
ORDER BY trip_date 
LIMIT 10;

# Optimization 4: Caching
from functools import lru_cache

@lru_cache(maxsize=1000, ttl=300)  # 5 minute cache
async def search_trips_cached(label: str) -> List[Dict]:
    return await search_trips_db(label)

# Optimization 5: Pre-compute popular searches
# Materialized view of common trip patterns
CREATE MATERIALIZED VIEW trip_search_mv AS
SELECT trip_id, display_name, trip_date, route_id,
       LOWER(display_name) as search_key
FROM daily_trips
WHERE trip_date >= CURRENT_DATE;

REFRESH MATERIALIZED VIEW trip_search_mv;  -- Daily job
```

---

## 4. Extension & Modification Questions

### Q4.1: "Add support for voice input. What changes are needed?"

**Answer:**

```python
# 1. New endpoint for audio
@router.post("/voice")
async def agent_voice(audio: UploadFile = File(...)):
    # Transcribe using Whisper or Google Speech-to-Text
    text = await transcribe_audio(audio)
    
    # Then process as normal text
    return await agent_message(AgentMessageRequest(text=text))

# 2. Transcription service
async def transcribe_audio(audio: UploadFile) -> str:
    import openai
    
    # Read audio file
    audio_bytes = await audio.read()
    
    # Call Whisper API
    client = openai.AsyncOpenAI()
    response = await client.audio.transcriptions.create(
        model="whisper-1",
        file=("audio.wav", audio_bytes, "audio/wav"),
        response_format="text"
    )
    
    return response.text

# 3. Handle voice-specific patterns in LLM
SYSTEM_PROMPT += """
Voice input may contain:
- Filler words: "um", "uh", "like"
- Corrections: "no wait, I meant..."
- Incomplete sentences

Clean and interpret the intent, ignoring filler.
"""

# 4. Frontend changes
// Add microphone button
const [isRecording, setIsRecording] = useState(false);

const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    // ...record and send to /voice endpoint
};
```

---

### Q4.2: "Add multi-language support (Hindi, Spanish). What changes?"

**Answer:**

```python
# 1. Detect language in parse_intent
from langdetect import detect

async def parse_intent_llm(state: Dict) -> Dict:
    text = state.get("text", "")
    
    # Detect language
    try:
        language = detect(text)
    except:
        language = "en"
    
    state["detected_language"] = language
    
    # If not English, translate first
    if language != "en":
        text = await translate_to_english(text)
        state["original_text"] = state["text"]
        state["translated_text"] = text

# 2. Update LLM prompt
SYSTEM_PROMPT += """
MULTI-LANGUAGE SUPPORT:
You may receive input in Hindi or mixed Hindi-English (Hinglish).

Hindi patterns:
- "गाड़ी लगाओ" (assign vehicle)
- "ट्रिप रद्द करो" (cancel trip)
- "ड्राइवर बदलो" (change driver)

Spanish patterns:
- "asignar vehículo" (assign vehicle)
- "cancelar viaje" (cancel trip)

Always return JSON in English, but include:
"detected_language": "hi" | "es" | "en"
"""

# 3. Translate responses back
async def report_result(state: Dict) -> Dict:
    # ... existing logic ...
    
    # Translate message if needed
    language = state.get("detected_language", "en")
    if language != "en":
        state["message_english"] = state["message"]
        state["message"] = await translate_from_english(
            state["message"], 
            target_language=language
        )
    
    return state

# 4. Translation service
async def translate_to_english(text: str) -> str:
    # Use Google Translate API or Gemini
    response = await genai.generate_content(
        f"Translate to English, preserving intent: {text}"
    )
    return response.text
```

---

### Q4.3: "Add notification when trip is about to depart (30 min warning). What changes?"

**Answer:**

```python
# 1. Background task (status_updater.py already exists)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def check_departing_trips():
    """Check for trips departing in next 30 minutes"""
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Find trips departing soon without vehicle/driver
        trips = await conn.fetch("""
            SELECT t.trip_id, t.display_name, t.trip_date,
                   d.vehicle_id, d.driver_id
            FROM daily_trips t
            LEFT JOIN deployments d ON t.trip_id = d.trip_id
            WHERE t.trip_date = CURRENT_DATE
              AND t.departure_time BETWEEN NOW() AND NOW() + INTERVAL '30 minutes'
              AND t.live_status = 'SCHEDULED'
              AND (d.vehicle_id IS NULL OR d.driver_id IS NULL)
        """)
    
    for trip in trips:
        await send_notification(
            type="departure_warning",
            trip_id=trip["trip_id"],
            message=f"⚠️ Trip {trip['display_name']} departs in 30 min but is missing {'vehicle' if not trip['vehicle_id'] else 'driver'}!"
        )

# 2. Register with scheduler
scheduler.add_job(check_departing_trips, 'interval', minutes=5)
scheduler.start()

# 3. Notification service
async def send_notification(type: str, trip_id: int, message: str):
    # Option A: Store in database for polling
    await conn.execute("""
        INSERT INTO notifications (type, trip_id, message, created_at)
        VALUES ($1, $2, $3, NOW())
    """, type, trip_id, message)
    
    # Option B: WebSocket push
    await websocket_manager.broadcast({
        "type": "notification",
        "data": {"type": type, "trip_id": trip_id, "message": message}
    })
    
    # Option C: External service (email, SMS, Slack)
    await slack_client.post_message(channel="#ops", text=message)

# 4. Frontend: Subscribe to notifications
const ws = new WebSocket("ws://localhost:8000/ws/notifications");
ws.onmessage = (event) => {
    const notification = JSON.parse(event.data);
    toast.warning(notification.message);
};
```

---

## 5. Production Readiness

### Q5.1: "What would you add before deploying to production?"

**Answer:**

```python
# 1. AUTHENTICATION & AUTHORIZATION
from fastapi import Depends, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload["user_id"]

@router.post("/message")
async def agent_message(request, user_id: int = Depends(verify_token)):
    # Now user_id comes from verified token
    ...

# 2. RATE LIMITING
from slowapi import Limiter
limiter = Limiter(key_func=get_user_id)

@router.post("/message")
@limiter.limit("20/minute")  # 20 requests per minute per user
async def agent_message(...):
    ...

# 3. REQUEST VALIDATION
from pydantic import validator

class AgentMessageRequest(BaseModel):
    text: str
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 1000:
            raise ValueError("Message too long (max 1000 chars)")
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()

# 4. LOGGING & MONITORING
import structlog
from opentelemetry import trace

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

@router.post("/message")
async def agent_message(request):
    with tracer.start_as_current_span("agent_message") as span:
        span.set_attribute("user_id", request.user_id)
        span.set_attribute("text_length", len(request.text))
        
        logger.info("Processing message", 
                    user_id=request.user_id,
                    text_preview=request.text[:50])
        
        try:
            result = await runtime.run(...)
            span.set_attribute("action", result.get("action"))
            return result
        except Exception as e:
            logger.error("Processing failed", error=str(e))
            span.set_status(trace.StatusCode.ERROR)
            raise

# 5. HEALTH CHECKS
@router.get("/health/ready")
async def readiness():
    """Check if service is ready to handle requests"""
    try:
        await get_conn()  # DB available?
        await test_llm_connection()  # LLM available?
        return {"status": "ready"}
    except:
        raise HTTPException(503, "Service not ready")

@router.get("/health/live")
async def liveness():
    """Check if service is alive"""
    return {"status": "alive"}

# 6. GRACEFUL SHUTDOWN
@asynccontextmanager
async def lifespan(app):
    # Startup
    await init_db_pool()
    await scheduler.start()
    yield
    # Shutdown
    await scheduler.shutdown(wait=True)  # Wait for running jobs
    await close_pool()

# 7. ERROR HANDLING
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", 
                 path=request.url.path, 
                 error=str(exc))
    
    # Don't expose internal errors
    return JSONResponse(
        status_code=500,
        content={"error": "An internal error occurred"}
    )
```

---

### Q5.2: "How would you implement audit logging for compliance?"

**Answer:**

```python
# 1. Audit log table
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id INT NOT NULL,
    session_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,  -- trip, vehicle, driver
    entity_id INT,
    before_state JSONB,
    after_state JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN
);

# 2. Audit decorator
from functools import wraps

def audit_action(entity_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(state: Dict, *args, **kwargs):
            # Capture before state
            entity_id = state.get("trip_id") or state.get("vehicle_id")
            before_state = await get_current_state(entity_type, entity_id)
            
            # Execute action
            result = await func(state, *args, **kwargs)
            
            # Capture after state
            after_state = await get_current_state(entity_type, entity_id)
            
            # Log
            await log_audit(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                action=state.get("action"),
                entity_type=entity_type,
                entity_id=entity_id,
                before_state=before_state,
                after_state=after_state,
                success=result.get("ok", True)
            )
            
            return result
        return wrapper
    return decorator

# 3. Apply to tools
@audit_action("trip")
async def tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id):
    # ... existing logic ...

# 4. Query audit trail
@router.get("/audit/{entity_type}/{entity_id}")
async def get_audit_trail(entity_type: str, entity_id: int):
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM audit_log
            WHERE entity_type = $1 AND entity_id = $2
            ORDER BY timestamp DESC
            LIMIT 100
        """, entity_type, entity_id)
    return [dict(r) for r in rows]
```

---

## 6. System Design Questions

### Q6.1: "Design the system for a company with 10,000 vehicles and 1,000,000 daily trips"

**Answer:**

```
Current: Single instance handles everything

Scaled Architecture:

┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│                   (React SPA, CDN-hosted)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                 │
│  - Rate limiting (per user, per endpoint)                       │
│  - Authentication (JWT validation)                              │
│  - Request routing                                               │
│  - SSL termination                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐       ┌─────────┐       ┌─────────┐
    │ Agent   │       │ Agent   │       │ Agent   │
    │ Service │       │ Service │       │ Service │
    │ (K8s)   │       │ (K8s)   │       │ (K8s)   │
    └────┬────┘       └────┬────┘       └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│    Redis     │   │   Gemini     │   │  PostgreSQL  │
│   (Cache)    │   │    API       │   │   (Primary)  │
└──────────────┘   └──────────────┘   └──────┬───────┘
                                             │
                                    ┌────────┴────────┐
                                    ▼                 ▼
                              ┌──────────┐      ┌──────────┐
                              │ Read     │      │ Read     │
                              │ Replica  │      │ Replica  │
                              └──────────┘      └──────────┘

Key Changes:
1. Kubernetes deployment (3+ pods)
2. Redis for session state (not DB)
3. Read replicas for queries
4. Connection pooling via PgBouncer
5. Async message queue for bulk operations

Scale Numbers:
- 1M trips/day = ~12 trips/second
- With 3 pods = 4 trips/pod/second
- Each pod handles 10 concurrent = 40 req/sec capacity
- 4x headroom for peaks
```

---

### Q6.2: "How would you add real-time collaboration (multiple users editing same trip)?"

**Answer:**

```python
# 1. WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        # trip_id → set of websocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = defaultdict(set)
    
    async def connect(self, websocket: WebSocket, trip_id: int, user_id: int):
        await websocket.accept()
        self.active_connections[trip_id].add(websocket)
        
        # Notify others
        await self.broadcast(trip_id, {
            "type": "user_joined",
            "user_id": user_id
        }, exclude=websocket)
    
    async def disconnect(self, websocket: WebSocket, trip_id: int, user_id: int):
        self.active_connections[trip_id].discard(websocket)
        await self.broadcast(trip_id, {
            "type": "user_left",
            "user_id": user_id
        })
    
    async def broadcast(self, trip_id: int, message: dict, exclude=None):
        for connection in self.active_connections[trip_id]:
            if connection != exclude:
                await connection.send_json(message)

manager = ConnectionManager()

# 2. WebSocket endpoint
@router.websocket("/ws/trip/{trip_id}")
async def trip_websocket(websocket: WebSocket, trip_id: int, user_id: int):
    await manager.connect(websocket, trip_id, user_id)
    try:
        while True:
            # Listen for messages (cursor position, typing indicator, etc.)
            data = await websocket.receive_json()
            await manager.broadcast(trip_id, data, exclude=websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, trip_id, user_id)

# 3. Broadcast changes from execute_action
async def execute_action(state: Dict) -> Dict:
    # ... execute action ...
    
    # Notify all viewers of this trip
    trip_id = state.get("trip_id")
    if trip_id:
        await manager.broadcast(trip_id, {
            "type": "trip_updated",
            "action": state["action"],
            "changes": state.get("execution_result"),
            "by_user": state["user_id"]
        })
    
    return state

# 4. Frontend: Display collaboration
// Show who's viewing
useEffect(() => {
    const ws = new WebSocket(`ws://api/ws/trip/${tripId}?user_id=${userId}`);
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        
        if (msg.type === "user_joined") {
            setViewers(prev => [...prev, msg.user_id]);
        }
        
        if (msg.type === "trip_updated") {
            // Refresh trip data
            refetchTrip();
            toast.info(`${msg.by_user} ${msg.action}ed the trip`);
        }
    };
}, [tripId]);
```

---

## Quick Reference: Key Files to Know

| File | Purpose | Key Functions |
|------|---------|---------------|
| `graph_def.py` | Graph structure | `Graph`, `add_node`, `add_edge` |
| `runtime.py` | Execution engine | `GraphRuntime.run()` |
| `parse_intent_llm.py` | NLP entry point | `parse_intent_llm()` |
| `llm_client.py` | LLM integration | `parse_intent_with_llm()`, `SYSTEM_PROMPT` |
| `resolve_target.py` | Entity verification | `resolve_target()` |
| `decision_router.py` | Flow routing | `decision_router()`, `BUS_DASHBOARD_ACTIONS` |
| `check_consequences.py` | Risk analysis | `check_consequences()`, `SAFE_ACTIONS` |
| `execute_action.py` | Action handlers | 40+ action handlers |
| `report_result.py` | Response formatting | `report_result()` |
| `tools.py` | Database operations | `tool_*` functions |
| `agent.py` | HTTP endpoints | `/message`, `/confirm` |

---

Good luck with your deep technical interview! 🎯
