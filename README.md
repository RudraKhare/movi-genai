
##  LangGraph Agent Pipeline (Detailed Design)

### Overview

MOVI's core intelligence is powered by a **LangGraph state machine** with **11 interconnected nodes** that handle intent parsing, target resolution, consequence checking, confirmation loops, action execution, and result reporting. The graph is designed with **safety-first principles** — no database mutation occurs without explicit user confirmation.

---

##  Agent State Schema

The LangGraph pipeline maintains a shared state object that flows through all nodes. Each node can read and modify this state.

### Complete State Dictionary

```python
{
    #  User Input 
    "text": str,                      # Raw user message
    "session_id": str,                # UUID session identifier
    "selectedTripId": int | None,     # Trip ID from UI context
    "currentPage": str,               # "busDashboard" | "manageRoute"
    "from_image": bool,               # True if input came from OCR
    
    #  Intent Parsing 
    "action": str,                    # Parsed action (e.g., "deploy_vehicle")
    "llm_parsed": bool,               # True if LLM successfully parsed
    "confidence": float,              # LLM confidence score (0-1)
    "target_label": str | None,       # User's target description
    "targets": dict,                  # Extracted entities {trip, vehicle, driver}
    
    #  Target Resolution 
    "trip_id": int | None,            # Resolved trip ID
    "vehicle_id": int | None,         # Resolved vehicle ID
    "driver_id": int | None,          # Resolved driver ID
    "route_id": int | None,           # Resolved route ID
    "path_id": int | None,            # Resolved path ID
    "stop_id": int | None,            # Resolved stop ID
    
    #  Clarification 
    "clarify_options": list | None,   # List of ambiguous options
    "needs_clarification": bool,      # True if multiple matches found
    
    #  Consequences 
    "consequences": list,             # Preview of action impact
    "is_risky": bool,                 # True for destructive actions
    "needs_confirmation": bool,       # True if user must confirm
    
    #  Confirmation Loop 
    "confirmed": bool,                # User clicked Confirm
    "cancelled": bool,                # User clicked Cancel
    
    #  Execution 
    "result": dict | None,            # Action execution result
    "error": str | None,              # Error message if failed
    
    #  Creation Wizard State 
    "wizard_active": bool,            # True if in creation wizard
    "wizard_phase": str,              # Current wizard step
    "wizard_data": dict,              # Partial data collected
    
    #  Suggestions 
    "suggestions": list | None,       # Available options to show user
    
    #  Fallback 
    "fallback": bool,                 # True if intent not understood
    "fallback_message": str | None,   # Help message for user
    
    #  Response 
    "response": str,                  # Final message to user
    "response_type": str,             # "text" | "list" | "confirmation" | "wizard_step"
}
```


---

## ?? Node-by-Node Detailed Explanation

### 1?? `parse_intent_llm` (Entry Node)

**Purpose**: Parse user's natural language input into structured action + targets.

**Input State**:
- `text` (required)
- `currentPage` (optional, for context)
- `selectedTripId` (optional, from UI)

**Processing Logic**:
1. Check if `USE_LLM_PARSE=true` in environment
2. If LLM enabled:
   - Call LLM with JSON schema prompt
   - Parse response into `{action, targets, confidence}`
   - Set `llm_parsed = true`
3. If LLM disabled or fails:
   - Use regex fallback patterns
   - Match keywords like "deploy", "cancel", "list", etc.
   - Set `llm_parsed = false`
4. Validate action against supported actions list
5. Extract entity mentions (trip names, vehicle numbers, driver names)

**Output State Updates**:
```python
{
    "action": "deploy_vehicle",
    "llm_parsed": True,
    "confidence": 0.92,
    "targets": {
        "trip": "8 AM trip",
        "vehicle": "KA-01-AB-1234",
        "driver": "Ramesh"
    }
}
```

**Transitions**: ? `decision_router` (always)

---

### 2?? `decision_router`

**Purpose**: Route to appropriate node based on action type.

**Routing Logic**:
```python
if action == "create_trip":
    return "trip_creation_wizard"
elif action in ["deploy_vehicle", "remove_vehicle", "cancel_trip"]:
    return "resolve_target"
elif action in ["list_trips", "list_vehicles", "list_drivers"]:
    return "suggestion_provider"
elif action == "unknown":
    return "fallback"
```

**Transitions**:
- ? `trip_creation_wizard` (if create action)
- ? `suggestion_provider` (if list action)
- ? `resolve_target` (if operational action)
- ? `fallback` (if unknown)

---

### 3?? `resolve_target`

**Purpose**: Convert user's target descriptions into database IDs.

**Processing Logic**:

**For Trip Resolution**:
1. If `from_image=true` and `trip_id` already set ? Skip
2. If `selectedTripId` provided from UI ? Use directly
3. Else, query database:
   ```sql
   SELECT trip_id, display_name 
   FROM daily_trips 
   WHERE display_name ILIKE '%{user_description}%'
   ```
4. If multiple matches ? Set `needs_clarification=true`
5. If single match ? Set `trip_id`
6. If no match ? Set `fallback=true`

**For Vehicle Resolution**:
- Extract registration number pattern (e.g., "KA-01-AB-1234")
- Handle fuzzy matching (allow "KA-01" to match "KA-01-AB-1234")

**Transitions**:
- ? `check_consequences` (if all targets resolved)
- ? `collect_user_input` (if needs_clarification=true)
- ? `fallback` (if resolution failed)

---

### 4?? `check_consequences`

**Purpose**: Evaluate the impact of the action and determine if confirmation is needed.

**Processing Logic**:

**For `deploy_vehicle`**:
1. Check if trip already has deployment
2. If exists: Set `is_risky = true`, add warning
3. Get vehicle/driver details
4. Build consequence message

**For `remove_vehicle`**:
1. Check if there are bookings
2. If bookings > 0: Set `is_risky = true`

**For `cancel_trip`**:
1. Always risky
2. Check deployment + bookings
3. Build comprehensive warning

**Risk Classification**:
```python
RISKY_ACTIONS = ["deploy_vehicle", "remove_vehicle", "cancel_trip"]
if action in RISKY_ACTIONS:
    needs_confirmation = True
```

**Output State Updates**:
```python
{
    "consequences": [
        "Vehicle: KA-01-AB-1234 (30 seats)",
        "Driver: Ramesh Kumar",
        "?? Will replace existing deployment"
    ],
    "is_risky": True,
    "needs_confirmation": True
}
```

**Transitions**:
- ? `get_confirmation` (if needs_confirmation=true)
- ? `execute_action` (if safe action)

---

### 5?? `get_confirmation`

**Purpose**: Pause execution and wait for user to confirm or cancel.

**Processing Logic**:
1. Set response type to "confirmation"
2. Build confirmation message with consequences
3. Return state to frontend (graph pauses here)
4. Frontend displays `ConfirmationCard` component
5. User clicks [Confirm] or [Cancel]
6. Frontend sends `/api/agent/confirm`
7. Graph resumes with `confirmed=true` or `cancelled=true`

**Transitions**:
- ? `execute_action` (if confirmed=true)
- ? `report_result` (if cancelled=true)

---

### 6?? `execute_action`

**Purpose**: Perform the actual database mutation or data retrieval.

**For `deploy_vehicle`**:
```python
# Check if deployment exists
if existing:
    # Update existing
    await db.execute("""
        UPDATE deployments 
        SET vehicle_id = , driver_id = 
        WHERE trip_id = 
    """, vehicle_id, driver_id, trip_id)
else:
    # Insert new
    await db.execute("""
        INSERT INTO deployments (trip_id, vehicle_id, driver_id)
        VALUES (, , )
    """, trip_id, vehicle_id, driver_id)
```

**Transitions**: ? `report_result` (always)

---

### 7?? `report_result`

**Purpose**: Format the execution result into a user-friendly message.

**Processing Logic**:
1. Check if cancelled ? Return cancellation message
2. Check for errors ? Return error message
3. Format success message with details

**Output**: `"? Vehicle deployed successfully"`

**Transitions**: ? END (graph completes)

---

### 8?? `suggestion_provider`

**Purpose**: Provide lists of available options for "list" actions.

**For `list_trips`**:
```python
trips = await db.fetch("""
    SELECT t.trip_id, t.display_name, t.trip_date
    FROM daily_trips t
    WHERE t.trip_date >= CURRENT_DATE
    ORDER BY t.trip_date
""")
suggestions = [format_trip(t) for t in trips]
```

**Transitions**: ? `report_result` (always)

---

### 9?? `trip_creation_wizard`

**Purpose**: Multi-step guided conversation for creating trips.

**Wizard Phases**:
1. **Collect Trip Name**: "What should we call it?"
2. **Path Selection**: "Which path should this trip use?"
3. **Stop Collection**: "Would you like to add more stops?"
4. **Time & Direction**: "What time? Which direction?"
5. **Vehicle Suggestion**: "Here are available vehicles"
6. **Driver Suggestion**: "Select a driver"
7. **Summary & Confirmation**: "Review your trip"
8. **Creation**: Execute if confirmed

**Transitions**:
- ? `collect_user_input` (for each step)
- ? `get_confirmation` (for final confirmation)
- ? `execute_action` (when confirmed)

---

### ?? `collect_user_input`

**Purpose**: Wait for user to provide additional information.

**Use Cases**:
- Clarifying ambiguous trips
- Wizard step responses

**Transitions**:
- ? `resolve_target` (if clarification provided)
- ? `trip_creation_wizard` (if wizard active)

---

### 1??1?? `fallback`

**Purpose**: Handle unrecognized intents and provide helpful guidance.

**Processing Logic**:
```python
return """
I can help you with:
• ?? Deploy/remove vehicles
• ?? Cancel trips
• ?? List trips, routes, vehicles, drivers
• ? Create new trips (guided wizard)

Try: "Deploy vehicle KA-01 to the 8 AM trip"
"""
```

**Transitions**: ? END

---

## ?? Conditional Edges & Transitions

### Edge Logic Table

| From Node | Condition | To Node |
|-----------|-----------|---------|
| `parse_intent_llm` | always | `decision_router` |
| `decision_router` | `action == "create_trip"` | `trip_creation_wizard` |
| `decision_router` | `action in list_actions` | `suggestion_provider` |
| `decision_router` | `action in operational` | `resolve_target` |
| `decision_router` | `action == "unknown"` | `fallback` |
| `resolve_target` | `resolved` | `check_consequences` |
| `resolve_target` | `needs_clarification` | `collect_user_input` |
| `resolve_target` | `failed` | `fallback` |
| `check_consequences` | `needs_confirmation` | `get_confirmation` |
| `check_consequences` | `safe` | `execute_action` |
| `get_confirmation` | `confirmed` | `execute_action` |
| `get_confirmation` | `cancelled` | `report_result` |
| `execute_action` | always | `report_result` |
| `suggestion_provider` | always | `report_result` |
| `trip_creation_wizard` | `incomplete` | `collect_user_input` |
| `trip_creation_wizard` | `complete` | `get_confirmation` |
| `collect_user_input` | `clarified` | `resolve_target` |
| `collect_user_input` | `wizard_response` | `trip_creation_wizard` |
| `fallback` | always | END |
| `report_result` | always | END |

---

## ?? Global LangGraph Flow Diagram

```mermaid
graph TD
    START([User Input]) --> A[parse_intent_llm]
    
    A --> B{decision_router}
    
    B -->|create| W[trip_creation_wizard]
    B -->|list| S[suggestion_provider]
    B -->|operational| C[resolve_target]
    B -->|unknown| F[fallback]
    
    C -->|resolved| D[check_consequences]
    C -->|ambiguous| I[collect_user_input]
    C -->|not found| F
    
    I -->|clarified| C
    I -->|wizard response| W
    
    D -->|risky| E[get_confirmation]
    D -->|safe| G[execute_action]
    
    E -->|confirmed| G
    E -->|cancelled| H[report_result]
    
    W -->|incomplete| I
    W -->|complete| E
    
    S --> H
    G --> H
    F --> END([Response])
    H --> END
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style E fill:#FFD700
    style G fill:#FFA500
    style F fill:#FF6347
```

---


## ?? Setup Instructions

### Prerequisites

- **Python 3.11+** (required for FastAPI + LangGraph)
- **Node.js 18+** (required for React + Vite)
- **PostgreSQL 15+** (Supabase recommended)
- **Git** for version control
- **Google Cloud Account** (for Vision API OCR)
- **OpenAI API Key** or **Google Gemini API Key** (for LLM)

---

### ?? Backend Setup

#### Step 1: Clone Repository

```bash
git clone https://github.com/RudraKhare/movi-genai.git
cd movi-genai/backend
```

#### Step 2: Create Virtual Environment

**Windows (PowerShell)**:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies**:
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `asyncpg==0.29.0` - PostgreSQL driver
- `langgraph==0.0.60` - State machine
- `openai==1.3.0` - OpenAI API client
- `google-generativeai==0.3.0` - Gemini API client
- `google-cloud-vision==3.4.0` - OCR service
- `rapidfuzz==3.5.2` - Fuzzy matching
- `python-dotenv==1.0.0` - Environment management
- `pydantic==2.5.0` - Data validation

#### Step 4: Configure Environment Variables

Create `backend/.env` file:

```bash
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://user:password@db.xxx.supabase.co:5432/postgres

# Supabase (for connection pooling)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# LLM Configuration
LLM_PROVIDER=openai              # Options: openai | gemini | ollama
USE_LLM_PARSE=true               # Enable LLM intent parsing
LLM_TIMEOUT_SECONDS=10           # Timeout for LLM calls

# OpenAI (if using LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
LLM_MODEL=gpt-4o-mini            # Options: gpt-4o-mini | gpt-4o | gpt-4-turbo

# Google Gemini (if using LLM_PROVIDER=gemini)
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-1.5-flash    # Options: gemini-1.5-flash | gemini-1.5-pro

# Ollama (if using LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2              # Options: llama2 | mistral | phi

# Google Cloud Vision (OCR)
USE_OCR=true                     # Enable OCR image processing
GOOGLE_APPLICATION_CREDENTIALS=./movigenai-xxxxx.json
GOOGLE_OCR_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true                      # Auto-reload on code changes
```

#### Step 5: Setup Database (Supabase)

1. **Create Supabase Project**: Visit [supabase.com](https://supabase.com) and create new project
2. **Get Connection String**: Go to Project Settings ? Database ? Connection String
3. **Run Migrations**:

```bash
# Apply migrations in order
python -c "
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def run_migration(file):
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    with open(file) as f:
        await conn.execute(f.read())
    await conn.close()
    print(f'? {file} applied')

asyncio.run(run_migration('migrations/001_initial_schema.sql'))
asyncio.run(run_migration('migrations/002_add_bookings.sql'))
asyncio.run(run_migration('migrations/003_add_deployments.sql'))
asyncio.run(run_migration('migrations/004_agent_sessions.sql'))
"
```

Or use the provided script:
```bash
python apply_migration.py
```

#### Step 6: Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Server should start at**: `http://localhost:8000`

**Verify**:
- Visit `http://localhost:8000/docs` for interactive API documentation
- Visit `http://localhost:8000/health` for health check

---

### ?? Frontend Setup

#### Step 1: Navigate to Frontend

```bash
cd ../frontend
```

#### Step 2: Install Dependencies

```bash
npm install
```

**Key Dependencies**:
- `react@18.2.0` - UI framework
- `vite@5.4.21` - Build tool
- `axios@1.6.0` - HTTP client
- `tailwindcss@3.3.0` - CSS framework
- `lucide-react@0.263.1` - Icons

#### Step 3: Configure Environment

Create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

#### Step 4: Start Development Server

```bash
npm run dev
```

**Frontend should start at**: `http://localhost:5173`

**Pages Available**:
- `/` - Bus Dashboard (main trip management)
- `/manage` - Route Management (create routes/paths/stops)

---

### ?? OCR Setup (Google Cloud Vision)

#### Step 1: Create Google Cloud Project

1. Visit [console.cloud.google.com](https://console.cloud.google.com)
2. Create new project
3. Enable **Cloud Vision API**

#### Step 2: Create Service Account

1. Go to IAM & Admin ? Service Accounts
2. Create service account with **Cloud Vision User** role
3. Generate JSON key
4. Download and save as `backend/movigenai-xxxxx.json`

#### Step 3: Set Environment Variable

In `backend/.env`:
```bash
GOOGLE_APPLICATION_CREDENTIALS=./movigenai-xxxxx.json
USE_OCR=true
```

#### Step 4: Test OCR

```bash
python backend/tests/test_ocr.py
```

---

### ?? LLM Setup

#### Option 1: OpenAI (Recommended)

1. Get API key from [platform.openai.com](https://platform.openai.com)
2. In `backend/.env`:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
LLM_MODEL=gpt-4o-mini
USE_LLM_PARSE=true
```

#### Option 2: Google Gemini

1. Get API key from [ai.google.dev](https://ai.google.dev)
2. In `backend/.env`:
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-1.5-flash
USE_LLM_PARSE=true
```

#### Option 3: Ollama (Local, Free)

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull model:
```bash
ollama pull llama2
```
3. In `backend/.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
USE_LLM_PARSE=true
```

#### Test LLM Integration

```bash
python backend/test_llm_integration.py
```

---

###  Switching Between LLM Providers

Simply change `LLM_PROVIDER` in `.env` and restart backend:

```bash
# For OpenAI
LLM_PROVIDER=openai

# For Gemini
LLM_PROVIDER=gemini

# For Ollama (local)
LLM_PROVIDER=ollama

# Disable LLM (use regex fallback)
USE_LLM_PARSE=false
```

---

##  Feature Documentation

### 1 MoviWidget (Conversational UI)

**Location**: `frontend/src/components/MoviWidget/`

**Components**:
- `MoviWidget.jsx` - Main container
- `ChatBubble.jsx` - Message display
- `ChatInput.jsx` - User input field
- `ConfirmationCard.jsx` - Confirm/Cancel UI
- `ConsequenceCard.jsx` - Impact preview
- `ImageUploadButton.jsx` - Photo upload
- `ImagePreview.jsx` - Image display
- `MessageList.jsx` - Chat history

**Features**:
-  Real-time chat interface
-  Structured message cards (lists, objects, tables)
-  Consequence preview with warnings
-  Confirm/Cancel buttons
-  Image upload with preview
-  Session persistence (localStorage)
-  Context awareness (knows current page)
-  Auto-scroll to latest message

**Usage**:
```jsx
import MoviWidget from './components/MoviWidget/MoviWidget';

function BusDashboard() {
  return (
    <div>
      <MoviWidget 
        currentPage="busDashboard"
        selectedTripId={tripId}
      />
    </div>
  );
}
```

**Screenshot Placeholder**:
`
[MoviWidget Interface]

 MOVI - Your Transport Agent  

  What can I help with?     
                              
  Deploy KA-01 to 8AM trip  
                              
  I found:                  
    Trip: North Route 8AM     
    Vehicle: KA-01 (30 seats) 
                              
     Consequences:          
     Will replace existing   
                              
    [Confirm] [Cancel]        
                              
  [Upload Image]  [Type...

`

---

### 2 OCR Image Understanding

**Pipeline Flow**:
```
Image Upload
    
Preprocessing (contrast, denoise)
    
Google Vision API (text extraction)
    
Text Cleaning
    
Fuzzy Match (RapidFuzz)
    
Trip Resolution (trip_id)
    
Auto-forward to Agent
```

**Code Location**: `backend/app/core/ocr.py`

**Key Functions**:

**1. Preprocess Image**:
```python
def preprocess_image(image_bytes):
    # Convert to PIL Image
    image = Image.open(BytesIO(image_bytes))
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Denoise
    image_array = np.array(image)
    denoised = cv2.fastNlMeansDenoising(image_array)
    
    return Image.fromarray(denoised)
```

**2. Extract Text**:
```python
async def extract_text_from_image(image_bytes):
    client = vision.ImageAnnotatorClient()
    
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    
    texts = response.text_annotations
    if texts:
        return texts[0].description  # Full text
    return ""
```

**3. Fuzzy Match Trip**:
```python
from rapidfuzz import fuzz

def fuzzy_match_trip(extracted_text, trips):
    best_match = None
    best_score = 0
    
    for trip in trips:
        score = fuzz.partial_ratio(
            extracted_text.lower(),
            trip['display_name'].lower()
        )
        
        if score > best_score:
            best_score = score
            best_match = trip
    
    if best_score >= 70:  # Confidence threshold
        return best_match, best_score / 100
    return None, 0
```

**Example**:
```
Input Image: Photo of route board showing "North Route 8:00 AM Morning"
    
Extracted Text: "North Route 8 AM Morning"
    
Fuzzy Match Scores:
    - "North Route - Morning (8:00 AM)"  92%
    - "South Route - Morning (8:00 AM)"  58%
    - "North Route - Evening (5:00 PM)"  67%
    
Matched Trip: ID=5, Confidence=0.92
```

---

### 3 LLM Intent Parser

**Code Location**: `backend/langgraph/nodes/parse_intent_llm.py`

**JSON Schema Prompt**:
```json
{
  "role": "system",
  "content": "You are an intent parser for a transport management system. Parse user messages into JSON with this schema: {action: string, targets: {trip?: string, vehicle?: string, driver?: string, route?: string, path?: string, stop?: string}, confidence: number (0-1)}"
}
```

**Example Inputs/Outputs**:

**Example 1: Deploy Vehicle**
```
Input: "Deploy vehicle KA-01-AB-1234 to the 8 AM North Route trip with driver Ramesh Kumar"

LLM Output:
{
  "action": "deploy_vehicle",
  "targets": {
    "trip": "8 AM North Route",
    "vehicle": "KA-01-AB-1234",
    "driver": "Ramesh Kumar"
  },
  "confidence": 0.95
}
```

**Example 2: Cancel Trip**
```
Input: "Cancel the morning trip to Airport"

LLM Output:
{
  "action": "cancel_trip",
  "targets": {
    "trip": "morning trip to Airport"
  },
  "confidence": 0.88
}
```

**Example 3: List Actions**
```
Input: "Show me all available vehicles"

LLM Output:
{
  "action": "list_vehicles",
  "targets": {},
  "confidence": 0.98
}
```

**Example 4: Low Confidence**
```
Input: "Do something with the thing"

LLM Output:
{
  "action": "unknown",
  "targets": {},
  "confidence": 0.12
}
 Triggers fallback node with help message
```

**Confidence Handling**:
- ** 0.80**: High confidence, proceed
- **0.50 - 0.79**: Medium confidence, ask clarification
- **< 0.50**: Low confidence, trigger fallback

---

### 4 Conversational Creation Wizard

**Full Wizard Flow Example**:

```
User: "Create a new trip"

Agent: "Let's create a new trip! What should we call it?"

User: "Airport Express Morning"

Agent: "Great! Now, which path should this trip use? Here are available paths:
1. Whitefield  Airport (12 stops)
2. Koramangala  Airport (8 stops)
3. Indiranagar  Airport (10 stops)"

User: "Use path 1"

Agent: "Perfect! Whitefield  Airport path has 12 stops. Would you like to add more stops? (yes/no)"

User: "No"

Agent: "What time should this trip run? (Format: HH:MM, e.g., 08:00)"

User: "07:30"

Agent: "Got it: 07:30 AM. What direction is this trip? (e.g., UP, DOWN, ONWARD, RETURN)"

User: "ONWARD"

Agent: "Checking available vehicles... Here are vehicles free at 07:30:
1. KA-01-AB-1234 (30 seats, Bus)
2. KA-02-CD-5678 (45 seats, Bus)
3. KA-05-MN-3456 (20 seats, Van)

Which vehicle would you like to assign?"

User: "Vehicle 1"

Agent: "Vehicle KA-01-AB-1234 selected. Now, here are available drivers:
1. Ramesh Kumar (5 years exp)
2. Suresh Patil (3 years exp)
3. Vijay Singh (7 years exp)

Which driver?"

User: "Ramesh"

Agent: "Perfect! Here's the summary of your trip:

 Trip Summary:

Name: Airport Express Morning
Path: Whitefield  Airport (12 stops)
Time: 07:30 AM
Direction: ONWARD
Vehicle: KA-01-AB-1234 (30 seats)
Driver: Ramesh Kumar

 This will create a new trip and deploy the vehicle.

[Confirm] [Cancel]"

User: *clicks Confirm*

Agent: " Trip 'Airport Express Morning' created successfully! (ID: 42)
Vehicle KA-01-AB-1234 deployed with driver Ramesh Kumar."
```

**Wizard State Management**:
```python
wizard_data = {
    "trip_name": "Airport Express Morning",
    "selected_path_id": 1,
    "selected_stops": [/* stop IDs */],
    "shift_time": "07:30:00",
    "direction": "ONWARD",
    "suggested_vehicles": [/* vehicle objects */],
    "selected_vehicle_id": 3,
    "suggested_drivers": [/* driver objects */],
    "selected_driver_id": 2
}
```

---


##  API Documentation

### Core Agent Endpoints

#### POST `/api/agent/message`

**Purpose**: Main conversational endpoint for text-based interactions.

**Request Body**:
```json
{
  "text": "Deploy vehicle KA-01 to the 8 AM trip",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "selectedTripId": 5,
  "currentPage": "busDashboard"
}
```

**Response (Confirmation Required)**:
```json
{
  "response": "Please confirm the following action:",
  "response_type": "confirmation",
  "consequences": [
    "Vehicle: KA-01-AB-1234 (30 seats)",
    "Driver: Ramesh Kumar",
    "Trip: North Route - Morning (8:00 AM)",
    " Will replace existing deployment"
  ],
  "needs_confirmation": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (Success)**:
```json
{
  "response": " Vehicle KA-01-AB-1234 deployed successfully",
  "response_type": "text",
  "result": {
    "status": "success",
    "deployment_id": 42
  },
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

#### POST `/api/agent/confirm`

**Purpose**: Callback for user confirmation (Confirm/Cancel).

**Request Body**:
```json
{
  "action": "confirm",  // or "cancel"
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
  "response": " Vehicle deployed successfully",
  "response_type": "text",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

#### POST `/api/agent/image`

**Purpose**: OCR image upload for trip resolution.

**Request**: Multipart form-data
```
Content-Type: multipart/form-data

image: [file binary]
session_id: "550e8400-e29b-41d4-a716-446655440000"
```

**Response (Trip Found)**:
```json
{
  "success": true,
  "trip": {
    "trip_id": 5,
    "display_name": "North Route - Morning (8:00 AM)",
    "trip_date": "2025-11-15",
    "live_status": "SCHEDULED"
  },
  "confidence": 0.92,
  "extracted_text": "North Route 8 AM Morning",
  "message": "Trip identified! What would you like to do?",
  "suggestions": [
    "Deploy vehicle",
    "Cancel trip",
    "View details"
  ]
}
```

**Response (Trip Not Found)**:
```json
{
  "success": false,
  "message": "Could not identify trip from image. Please try again or describe the trip.",
  "extracted_text": "Some unclear text",
  "confidence": 0.45
}
```

---

### Dashboard & Context Endpoints

#### GET `/api/context/dashboard`

**Purpose**: Get dashboard data (trips, summary, KPIs).

**Response**:
```json
{
  "summary": {
    "total_trips": 12,
    "deployed": 8,
    "ongoing_trips": 3,
    "completed": 2
  },
  "trips": [
    {
      "trip_id": 5,
      "display_name": "North Route - Morning (8:00 AM)",
      "route_name": "North Route",
      "path_name": "Whitefield  Airport",
      "trip_date": "2025-11-15",
      "live_status": "IN_PROGRESS",
      "vehicle_id": 3,
      "registration_number": "KA-01-AB-1234",
      "capacity": 30,
      "driver_id": 2,
      "driver_name": "Ramesh Kumar",
      "total_bookings": 18,
      "booking_status_percentage": 60
    }
  ]
}
```

---

#### GET `/api/context/manage`

**Purpose**: Get route management data (routes, paths, stops).

**Response**:
```json
{
  "routes": [
    {
      "route_id": 1,
      "route_name": "North Route",
      "path_name": "Whitefield  Airport",
      "shift_time": "08:00:00",
      "direction": "ONWARD",
      "start_point": "Whitefield",
      "end_point": "Airport"
    }
  ],
  "paths": [
    {
      "path_id": 1,
      "path_name": "Whitefield  Airport",
      "description": "Main airport route",
      "stop_count": 12
    }
  ],
  "stops": [
    {
      "stop_id": 1,
      "name": "Whitefield Main",
      "latitude": 12.9698,
      "longitude": 77.7500,
      "address": "Whitefield, Bangalore"
    }
  ]
}
```

---

### Route Management Endpoints

#### POST `/api/routes/create`

**Request**:
```json
{
  "route_name": "South Route Express",
  "path_id": 2,
  "shift_time": "09:00",
  "direction": "ONWARD"
}
```

**Response**:
```json
{
  "route_id": 10,
  "route_name": "South Route Express",
  "trip": {
    "trip_id": 45,
    "display_name": "South Route Express",
    "trip_date": "2025-11-15",
    "live_status": "SCHEDULED"
  },
  "message": "Route and trip created successfully"
}
```

---

#### GET `/api/routes/{route_id}/stops`

**Purpose**: Get ordered stops for a route.

**Response**:
```json
{
  "route_id": 1,
  "stops": [
    {
      "stop_id": 1,
      "name": "Whitefield Main",
      "latitude": 12.9698,
      "longitude": 77.7500,
      "address": "Whitefield, Bangalore",
      "stop_order": 1
    },
    {
      "stop_id": 2,
      "name": "ITPL Gate",
      "stop_order": 2
    }
  ]
}
```

---

##  Testing

### Backend Tests

#### Run All Tests

```bash
cd backend
pytest tests/ -v
```

#### Test Categories

**1. LLM Integration Tests**:
```bash
pytest tests/test_llm_integration.py -v
```

Tests:
- LLM connection
- Intent parsing accuracy
- JSON schema validation
- Confidence scoring
- Fallback behavior

**2. OCR Tests**:
```bash
pytest backend/tests/test_ocr.py -v
```

Tests:
- Image preprocessing
- Text extraction
- Fuzzy matching
- Confidence thresholds

**3. Agent Confirmation Tests**:
```bash
pytest backend/tests/test_agent_confirmation.py -v
```

Tests:
- Confirmation flow
- Cancel behavior
- State persistence
- Session management

**4. Graph Execution Tests**:
```bash
pytest backend/langgraph/tests/test_graph.py -v
```

Tests:
- Node transitions
- Conditional edges
- State updates
- Error handling

---

### Manual Testing Guide

#### Scenario 1: Deploy Vehicle (Risky Action)

1. Open dashboard at `http://localhost:5173`
2. Click MoviWidget
3. Type: _"Deploy vehicle KA-01-AB-1234 to the 8 AM trip with driver Ramesh"_
4. **Expected**:
   - Agent shows consequence card
   - Vehicle and driver details displayed
   - Warning about replacement shown
   - [Confirm] [Cancel] buttons appear
5. Click **Confirm**
6. **Expected**: Success message, trip updated in dashboard

---

#### Scenario 2: List Trips (Safe Action)

1. Type: _"Show me all trips for today"_
2. **Expected**:
   - No confirmation required
   - List of trips displayed immediately
   - Each trip shows name, time, status

---

#### Scenario 3: Ambiguous Intent

1. Type: _"Deploy vehicle to 8 AM trip"_ (missing vehicle ID)
2. **Expected**:
   - Agent asks: _"Which vehicle would you like to deploy?"_
   - List of available vehicles shown
3. Select vehicle
4. **Expected**: Continue with deployment flow

---

#### Scenario 4: OCR Flow

1. Take photo of route board showing trip name
2. Click image upload button in MoviWidget
3. Upload photo
4. **Expected**:
   - Processing spinner
   - Trip identified message
   - Action suggestions shown
5. Select "Deploy vehicle"
6. **Expected**: Continue with deployment flow

---

#### Scenario 5: Trip Creation Wizard

1. Type: _"Create a new trip"_
2. **Expected**: Wizard starts, asks for trip name
3. Follow wizard prompts:
   - Enter trip name
   - Select path
   - Confirm stops
   - Set time
   - Choose direction
   - Select vehicle (from suggestions)
   - Select driver (from suggestions)
4. **Expected**: Summary shown with [Confirm]
5. Click Confirm
6. **Expected**: Trip created, visible in dashboard

---

#### Scenario 6: UI Context Switching

1. On **Dashboard** page, select a trip
2. Open MoviWidget
3. Type: _"Deploy vehicle KA-01"_
4. **Expected**: Agent uses selected trip automatically
5. Navigate to **ManageRoute** page
6. Type: _"Create a route"_
7. **Expected**: Agent knows you're on manage page

---

#### Scenario 7: LLM Fallback

1. Disable LLM: Set `USE_LLM_PARSE=false` in backend/.env
2. Restart backend
3. Type: _"Deploy KA-01 to 8 AM trip"_
4. **Expected**: Regex parser handles it correctly
5. Type: _"Do something complex with ambiguous phrasing"_
6. **Expected**: Fallback help message

---

#### Scenario 8: Confirm/Cancel Flow

1. Type: _"Cancel the 8 AM trip"_
2. **Expected**: Warning about bookings and deployments
3. Click **Cancel** button
4. **Expected**: _"Action cancelled by user"_
5. Repeat command
6. Click **Confirm**
7. **Expected**: Trip cancelled

---

##  Deployment

### Backend Deployment (Render)

#### Step 1: Prepare for Deployment

Create `render.yaml`:
```yaml
services:
  - type: web
    name: movi-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port 
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: USE_LLM_PARSE
        value: true
```

#### Step 2: Deploy to Render

1. Push code to GitHub
2. Visit [render.com](https://render.com)
3. Create new Web Service
4. Connect GitHub repo
5. Set environment variables
6. Deploy

---

### Frontend Deployment (Vercel)

#### Step 1: Configure for Production

Update `frontend/.env.production`:
```bash
VITE_API_BASE_URL=https://movi-backend.onrender.com
```

#### Step 2: Deploy to Vercel

```bash
cd frontend
npm install -g vercel
vercel --prod
```

Or use Vercel dashboard:
1. Visit [vercel.com](https://vercel.com)
2. Import GitHub repo
3. Set framework preset: Vite
4. Add environment variables
5. Deploy

---

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=
      - OPENAI_API_KEY=
    
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://backend:8000
```

Run:
```bash
docker-compose up -d
```

---

##  Troubleshooting

### Issue 1: OCR Not Working

**Symptoms**: Image upload fails, no text extracted

**Solutions**:
1. Check Google Cloud credentials:
```bash
echo 
# Should point to JSON key file
```

2. Verify Cloud Vision API is enabled
3. Check quota limits in Google Cloud Console
4. Test with simple image:
```bash
python backend/tests/test_ocr.py
```

---

### Issue 2: LLM Parsing Fails

**Symptoms**: Agent always uses regex fallback

**Solutions**:
1. Check API key is valid:
```bash
# For OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer "
```

2. Check `USE_LLM_PARSE=true` in .env
3. Verify provider matches key:
```bash
LLM_PROVIDER=openai  # Must match your API key
```

4. Check timeout settings:
```bash
LLM_TIMEOUT_SECONDS=10  # Increase if needed
```

---

### Issue 3: Graph Stuck in Fallback

**Symptoms**: Agent always responds with help message

**Solutions**:
1. Check session state:
```bash
# Query agent_sessions table
SELECT * FROM agent_sessions ORDER BY updated_at DESC LIMIT 1;
```

2. Clear localStorage in browser (DevTools  Application  Local Storage)
3. Check backend logs for parsing errors
4. Test intent parsing directly:
```bash
python backend/test_llm.py "deploy vehicle KA-01 to 8 AM trip"
```

---

### Issue 4: CORS Errors

**Symptoms**: Frontend can't reach backend API

**Solutions**:
1. Check CORS configuration in `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Verify backend is running: `curl http://localhost:8000/health`
3. Check `VITE_API_BASE_URL` in frontend/.env

---

### Issue 5: Supabase Connection Issues

**Symptoms**: Database queries fail, connection timeout

**Solutions**:
1. Verify connection string:
```bash
psql  -c "SELECT 1;"
```

2. Check SSL requirement:
```python
# In database connection code
ssl='require'  # or ssl=True
```

3. Verify IP whitelist in Supabase dashboard
4. Check connection pooling settings

---

##  Final Notes

### Architecture Insights

**Why LangGraph?**
- Explicit state management
- Visual debugging with graph inspector
- Easy to add new nodes
- Conditional routing out of the box
- Handles async operations naturally

**Why Supabase PostgreSQL?**
- Managed database (no DevOps overhead)
- Real-time subscriptions ready
- Built-in connection pooling
- RESTful API auto-generated
- Row-level security for multi-tenancy

**Why MoviWidget Pattern?**
- Reusable across multiple pages
- Maintains conversation context
- Graceful handling of async confirmations
- Easy to extend with new message types

---

### Future Roadmap

**Phase 4: Voice Integration**
- [ ] Speech-to-Text (Whisper API)
- [ ] Text-to-Speech (ElevenLabs)
- [ ] Voice commands in MoviWidget
- [ ] Hands-free operation mode

**Phase 5: Advanced Analytics**
- [ ] Trip performance dashboards
- [ ] Driver efficiency metrics
- [ ] Route optimization suggestions
- [ ] Predictive maintenance alerts

**Phase 6: Mobile App**
- [ ] React Native port
- [ ] Push notifications
- [ ] Offline mode
- [ ] GPS tracking integration

**Phase 7: Multi-tenancy**
- [ ] Organization management
- [ ] Role-based access control
- [ ] Custom branding
- [ ] API rate limiting

---

### Acknowledgements

**Technologies Used**:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - State machine orchestration
- [React](https://reactjs.org/) - UI library
- [Supabase](https://supabase.com/) - PostgreSQL hosting
- [OpenAI](https://openai.com/) - GPT-4o-mini LLM
- [Google Cloud Vision](https://cloud.google.com/vision) - OCR service
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS

**Assignment Context**:
This project was built as a capstone for the **Multimodal Transport Agent** assignment, demonstrating integration of LLMs, OCR, conversational UI, and safety-first human-in-the-loop workflows in a real-world transport management scenario.

**License**: MIT

**Author**: Rudra Khare

**Repository**: [github.com/RudraKhare/movi-genai](https://github.com/RudraKhare/movi-genai)

---

**End of README** 

