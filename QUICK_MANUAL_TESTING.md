# 🧪 Quick Manual Testing - All 6 Fixes

## 🚀 **Run the Test Suite** (Easiest Way)

First, make sure backend is running:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Then run the automated manual test:
```bash
python manual_test_suite.py
```

This will test all 6 fixes automatically and show you clear PASS/FAIL results.

---

## 🌐 **Frontend Testing** (Visual Verification)

### **1. Deployment Check Test**
```
Steps:
1. Open http://localhost:3000
2. Find Trip 5 in the trips list
3. Try to assign a vehicle to Trip 5
4. Expected: Should show error "This trip already has deployment 24 assigned"

✅ PASS: Clear error message about existing deployment
❌ FAIL: Assignment goes through or generic error
```

### **2. Suggestions Test**
```
Steps:  
1. Find Trip 3 (should not have vehicle assigned)
2. Click "Assign Vehicle" 
3. Expected: Should see list of available vehicles with proper names

✅ PASS: List of vehicles with registration numbers (KA01AB5678, etc.)
❌ FAIL: Empty list or vehicles showing as "Unknown"
```

### **3. Driver Assignment Test**
```
Steps:
1. Find a trip without driver
2. Click "Assign Driver"
3. Select a driver from the list
4. Expected: Assignment should succeed without availability errors

✅ PASS: Driver assignment works smoothly
❌ FAIL: "Driver not available" errors or assignment fails
```

---

## 🔧 **API Testing** (Direct Backend)

### **Test Deployment Check**
```bash
# PowerShell/Command Prompt
python -c "
import requests
r = requests.post('http://localhost:8000/api/agent/message',
    json={'text': 'STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:8|vehicle_name:Honda|context:selection_ui', 'user_id': 1, 'session_id': 'test'},
    headers={'x-api-key': 'dev-key-change-in-production'})
print('Status:', r.json()['agent_output']['status'])
print('Error:', r.json()['agent_output']['error'])
print('Message:', r.json()['agent_output']['message'])
"
```

**Expected Output:**
```
Status: failed
Error: already_deployed
Message: This trip already has deployment 24 assigned. Remove it first...
```

### **Test Suggestions**
```bash
python -c "
import requests
r = requests.post('http://localhost:8000/api/agent/message',
    json={'text': 'assign vehicle to trip 3', 'user_id': 1, 'selectedTripId': 3, 'session_id': 'test2'},
    headers={'x-api-key': 'dev-key-change-in-production'})
print('Status:', r.json()['agent_output']['status'])
print('Options count:', len(r.json()['agent_output'].get('options', [])))
"
```

**Expected Output:**
```
Status: options_provided
Options count: 5 (or similar number > 0)
```

---

## 📊 **Log Monitoring** (Advanced)

Watch the backend terminal for these key indicators:

### **✅ Good Signs:**
```
INFO:langgraph.nodes.decision_router:Route G: Processing assign_vehicle with trip_id=5
INFO:langgraph.nodes.decision_router:Route G: assign_vehicle rejected → trip already has deployment
INFO:langgraph.nodes.parse_intent_llm:[STRUCTURED] Converted trip_id: '5' → 5 (int)
INFO:langgraph.nodes.vehicle_selection_provider:Found 7 unassigned vehicles
```

### **❌ Red Flags:**
```
ERROR:langgraph_tools_module:Error assigning vehicle: Trip 5 already has a deployment
ERROR:langgraph.tools.llm_client:[LLM] Failed to parse Gemini JSON response
asyncpg.exceptions.DataError: str cannot be interpreted as integer
INFO:langgraph.nodes.decision_router:Route J: Dynamic action 'assign_vehicle' → check_consequences
```

---

## 🎯 **Quick Pass/Fail Checklist**

Run each test and check the box:

- [ ] **Deployment Check**: Trip 5 vehicle assignment blocked with clear message  
- [ ] **Suggestions**: Vehicle list shown when assigning to Trip 3
- [ ] **Driver Assignment**: Driver assignment works without availability errors
- [ ] **No String Errors**: No "str cannot be interpreted as integer" in logs
- [ ] **Proper Names**: Vehicle names show as registration numbers, not "Unknown"
- [ ] **Fast Execution**: Structured commands execute quickly without OCR delays

**All 6 checked = All fixes working! 🎉**

---

## 🚨 **Troubleshooting**

### **Backend Not Responding**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not working, restart:
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### **Database Issues**
```bash
# Restart database
docker-compose down
docker-compose up
```

### **Frontend Issues**
```bash
# Restart frontend
cd frontend
npm start
```
