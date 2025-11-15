# LangGraph Agent Quick Start Guide

## 🚀 Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
🚀 Starting Movi backend API...
✅ Database pool initialized
```

---

## 📡 Test the Agent Endpoint

### Using cURL

```bash
# Test 1: Remove vehicle (should need confirmation if trip has bookings)
curl -X POST "http://localhost:8000/api/agent/message" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key-change-in-production" \
  -d '{
    "text": "Remove vehicle from Bulk - 00:01",
    "user_id": 1
  }'

# Test 2: Cancel trip
curl -X POST "http://localhost:8000/api/agent/message" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key-change-in-production" \
  -d '{
    "text": "Cancel trip Bulk - 00:01",
    "user_id": 1
  }'

# Test 3: Unknown action
curl -X POST "http://localhost:8000/api/agent/message" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key-change-in-production" \
  -d '{
    "text": "Do something random",
    "user_id": 1
  }'

# Test 4: Agent health check
curl "http://localhost:8000/api/agent/health"
```

### Using Python Requests

```python
import requests
import json

url = "http://localhost:8000/api/agent/message"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "dev-key-change-in-production"
}

data = {
    "text": "Remove vehicle from Bulk - 00:01",
    "user_id": 1
}

response = requests.post(url, headers=headers, json=data)
print(json.dumps(response.json(), indent=2))
```

### Using FastAPI Swagger UI

1. Open: http://localhost:8000/docs
2. Find section: **AI Agent**
3. Click on **POST /api/agent/message**
4. Click **"Try it out"**
5. Enter request body:
```json
{
  "text": "Remove vehicle from Bulk - 00:01",
  "user_id": 1
}
```
6. Click **Execute**

---

## 🧪 Run Unit Tests

### Using pytest
```bash
cd backend
pytest langgraph/tests/test_graph.py -v
```

Expected output:
```
==================== test session starts ====================
collected 25 items

langgraph/tests/test_graph.py::test_parse_intent_remove_vehicle PASSED
langgraph/tests/test_graph.py::test_parse_intent_cancel_trip PASSED
langgraph/tests/test_graph.py::test_parse_intent_assign_vehicle PASSED
...
==================== 25 passed in 2.34s ====================
```

### Using the test runner
```bash
cd backend
python -m langgraph.tests.run_tests
```

Expected output:
```
======================================================================
MOVI LangGraph Agent Test Suite
======================================================================

======================================================================
Test 1: Remove vehicle (with bookings - should need confirmation)
======================================================================
Input: Remove vehicle from Bulk - 00:01

Status: awaiting_confirmation
Action: remove_vehicle
Trip ID: 12
Trip Label: Bulk - 00:01
Needs Confirmation: True
Success: True

Message:
⚠️ This trip has 5 active booking(s) (25% capacity)

❓ Do you want to proceed?

Consequences:
  - Booking Count: 5
  - Booking %: 25
  - Has Deployment: True
```

---

## 🗄️ Apply Database Migration

```bash
cd backend
# Option 1: Using psql
psql $DATABASE_URL -f migrations/004_agent_sessions.sql

# Option 2: Using the migration script
python scripts/apply_migration.py migrations/004_agent_sessions.sql
```

Expected output:
```
✅ Migration 004_agent_sessions completed successfully
   Created table: agent_sessions
   Created indexes: idx_agent_sessions_user_id, idx_agent_sessions_status, idx_agent_sessions_expires_at
   Created trigger: trigger_update_agent_sessions_updated_at
```

---

## 📊 Verify Everything Works

### Check 1: API Root
```bash
curl http://localhost:8000/
```

Should return:
```json
{
  "message": "MOVI Backend API is running successfully",
  "version": "1.0.0",
  "api_docs": "/docs",
  "endpoints": {
    "routes": "/api/routes",
    "actions": "/api/actions",
    "context": "/api/context",
    "audit": "/api/audit",
    "health": "/api/health",
    "agent": "/api/agent",
    "debug": "/api/debug"
  }
}
```

### Check 2: Agent Health
```bash
curl http://localhost:8000/api/agent/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "movi_agent",
  "graph_nodes": 7
}
```

### Check 3: Database Table
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM agent_sessions;"
```

Should return:
```
 count 
-------
     0
(1 row)
```

---

## 🎯 Supported Commands

### Remove Vehicle Commands
- "Remove vehicle from Bulk - 00:01"
- "Unassign vehicle from trip"
- "Clear deployment"

### Cancel Trip Commands
- "Cancel trip Bulk - 00:01"
- "Abort trip"
- "Stop trip"

### Assign Vehicle Commands
- "Assign vehicle to Bulk - 00:01"
- "Deploy vehicle to trip"
- "Add vehicle"

---

## 🐛 Troubleshooting

### Issue: Import errors
**Solution:**
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# On Windows: $env:PYTHONPATH="$PWD"
```

### Issue: Database connection error
**Solution:**
1. Verify `.env` has `DATABASE_URL`
2. Check Supabase connection: `psql $DATABASE_URL -c "SELECT 1;"`
3. Ensure `app/core/supabase_client.py` is configured

### Issue: Agent returns "trip_not_found"
**Solution:**
1. Check if trips exist: `psql $DATABASE_URL -c "SELECT trip_id, display_name FROM daily_trips LIMIT 5;"`
2. Use exact trip display name in command
3. Verify `tool_identify_trip_from_label` logic

### Issue: Tests fail with asyncio errors
**Solution:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Run with explicit event loop
pytest langgraph/tests/test_graph.py -v --asyncio-mode=auto
```

---

## 📝 Example Session

```bash
# 1. Start server
uvicorn app.main:app --reload

# 2. Test agent (in another terminal)
curl -X POST "http://localhost:8000/api/agent/message" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key-change-in-production" \
  -d '{"text": "Remove vehicle from Bulk - 00:01", "user_id": 1}'

# 3. Check response
# Should show confirmation needed if trip has bookings

# 4. Run tests
pytest langgraph/tests/test_graph.py -v

# 5. Check logs
# Server logs show: [Iteration 1] Executing node: parse_intent
#                  [Iteration 2] Executing node: resolve_target
#                  etc.
```

---

## ✅ Success Indicators

- ✅ Server starts without errors
- ✅ `/api/agent/health` returns `"status": "healthy"`
- ✅ `/api/agent/message` returns structured JSON
- ✅ Tests pass: 25/25
- ✅ Database migration applied
- ✅ API docs accessible at `/docs`

---

## 🎯 Next: Integrate with Frontend

See `DAY7_LANGGRAPH_AGENT_CORE.md` for Day 8 roadmap:
- Connect MoviWidget to agent API
- Implement confirmation dialogs
- Add conversation history

---

**Quick Start Complete! Agent is ready to process commands. 🚀**
