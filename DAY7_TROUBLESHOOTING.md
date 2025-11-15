# Day 7 LangGraph Agent - Troubleshooting Guide

## Issue: API Still Returns "trip_not_found" After Schema Fixes

### Root Cause
✅ **Schema fixes applied correctly**  
❌ **Backend server not restarted** - still running old code

### Solution

**1. Restart Backend Server**

```powershell
# In backend terminal, press Ctrl+C to stop server

# Then restart
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**2. Verify Schema Fixes Loaded**

Check backend console output - should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**3. Retest API**

```powershell
$headers = @{
    "Content-Type" = "application/json"
    "x-api-key" = "dev-secret-key-12345"
}
$body = @{
    text = "Remove vehicle from Bulk - 00:01"
    user_id = 1
    context = @{
        page = "busDashboard"
        selectedTrip = $null
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body | ConvertTo-Json -Depth 10
```

**Expected Result:**
```json
{
  "agent_output": {
    "action": "remove_vehicle",
    "trip_id": 7,
    "trip_label": "Bulk - 00:01",
    "status": "needs_confirmation",
    "needs_confirmation": true,
    "consequences": {
      "booking_percentage": 75,
      "bookings_count": 15,
      "message": "This trip has 15 bookings (75% capacity)..."
    }
  }
}
```

---

## Common Issues After Schema Fixes

### Issue 1: Server Not Picking Up Changes

**Symptom:** API still returns old errors after fixing code

**Cause:** FastAPI running with `--reload` doesn't always catch tool changes

**Fix:**
1. Stop server (Ctrl+C)
2. Restart: `uvicorn app.main:app --reload --port 8000`

---

### Issue 2: Import Errors After Restart

**Symptom:** Server crashes with `ModuleNotFoundError`

**Cause:** Virtual environment not activated

**Fix:**
```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

### Issue 3: Database Connection Errors

**Symptom:** `asyncpg.exceptions.InvalidCatalogNameError`

**Cause:** Database URL incorrect or database not running

**Fix:**
```powershell
# Check .env file
cat backend\.env

# Should have:
DATABASE_URL=postgresql://user:pass@host:5432/movi_db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

---

### Issue 4: Frontend Not Showing Results

**Symptom:** Messages sent but no agent response in UI

**Cause:** CORS or API key issues

**Fix:**

**Check browser console:**
```javascript
// Should see:
Sending message: Remove vehicle from Bulk - 00:01...
Agent response: {agent_output: {...}}

// Should NOT see:
CORS error
403 Forbidden
Network error
```

**If CORS error:**
```python
# In backend/app/main.py, verify:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing Checklist After Server Restart

- [ ] Backend terminal shows "Application startup complete"
- [ ] No import errors or warnings
- [ ] Test trip lookup: `tool_identify_trip_from_label('Bulk')`
- [ ] Test API endpoint with PowerShell
- [ ] Check frontend - send message and see response
- [ ] Check browser DevTools Network tab - API call should be 200 OK

---

## Quick Validation Script

Run this in backend directory to verify everything works:

```powershell
# 1. Activate environment
.venv\Scripts\Activate.ps1

# 2. Run tool integrity test
python test_tools_integrity.py

# Expected output:
# ✅ Found trip: Bulk - 00:01 (ID: 7)
# ✅ Got trip status: 8 fields
# ✅ Got bookings: 5 bookings
# ✅ Got vehicles: 9 vehicles
# ✅ Got drivers: 6 drivers

# 3. Run unit tests
pytest langgraph/tests/test_graph.py -v

# Expected: 22 passed in ~1s

# 4. Start server
uvicorn app.main:app --reload --port 8000
```

---

## Still Having Issues?

### Debug resolve_target Node

Add logging to see what's happening:

```python
# In backend/langgraph/nodes/resolve_target.py

async def resolve_target(state: Dict) -> Dict:
    text = state.get("text", "")
    action = state.get("action")
    
    # ADD THIS:
    logger.info(f"[resolve_target] Input text: '{text}'")
    logger.info(f"[resolve_target] Action: '{action}'")
    
    trip = await tool_identify_trip_from_label(text)
    
    # ADD THIS:
    logger.info(f"[resolve_target] Tool returned: {trip}")
    
    # ...rest of function
```

Then check backend logs when you send a message.

---

## Expected Flow (After Restart)

```
User: "Remove vehicle from Bulk - 00:01"
  ↓
parse_intent → action="remove_vehicle" ✅
  ↓
resolve_target → tool finds trip ID 7 ✅
  ↓
check_consequences → finds 15 bookings ✅
  ↓
get_confirmation → needs_confirmation=true ✅
  ↓
report_result → Returns JSON with consequences ✅
  ↓
Frontend displays yellow warning box with booking count ✅
```

---

## Success Indicators

✅ Backend logs show: "Database pool created"  
✅ Tool test returns: "Found trip: Bulk - 00:01 (ID: 7)"  
✅ API returns: `"trip_id": 7` (not null)  
✅ Frontend shows: Agent response with consequences  
✅ No errors in browser console  

---

**Next Steps:**

1. **Restart backend server** ← DO THIS FIRST
2. Retest API with PowerShell
3. Test frontend interaction
4. If still issues, add logging to resolve_target
5. Check backend terminal logs during API call

---

**Status:** Schema fixes complete, just need server restart to load new code!
