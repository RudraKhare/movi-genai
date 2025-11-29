# 🧪 MOVI Natural Language & Driver Assignment Manual Testing Guide

## 📋 Overview

This guide will help you manually test that both major issues have been resolved:

1. **Issue 1**: MOVI not understanding natural language (was regex-only)
2. **Issue 2**: "Assign Driver" operation not working at all

---

## 🚀 Pre-Testing Setup

### Step 1: Start the Backend
```bash
cd C:\Users\rudra\Desktop\movi
docker-compose up
```

Wait for these log messages:
- ✅ "FastAPI server started on port 8000"
- ✅ "Database connection established"
- ✅ "LangGraph agent initialized"

### Step 2: Open the Frontend
1. Open your browser
2. Navigate to the MOVI frontend URL (usually `http://localhost:3000`)
3. Log in if required

### Step 3: Prepare Test Data
Make sure you have:
- At least 2-3 trips created in the system
- At least 2-3 drivers in the database
- Note down actual driver names from your database

---

## 🔍 Test Categories

## A. **Natural Language Understanding Tests**

### A1. Basic Driver Assignment Phrases

**Before Fix**: All these would return "❌ I'm not sure what you want to do"  
**After Fix**: Should recognize as driver assignment actions

| Test Case | Input | Expected Result |
|-----------|--------|----------------|
| A1.1 | "assign John to this trip" | ✅ Recognizes as assign_driver |
| A1.2 | "allocate a driver" | ✅ Asks which driver to assign |
| A1.3 | "can you assign someone to drive" | ✅ Asks which driver to assign |
| A1.4 | "set driver to Sarah" | ✅ Recognizes driver assignment |
| A1.5 | "please assign a driver" | ✅ Asks which driver to assign |
| A1.6 | "get a driver for this trip" | ✅ Asks which driver to assign |
| A1.7 | "add Mike as driver" | ✅ Recognizes driver assignment |

**How to Test**:
1. Select a trip from the trip list
2. Type each phrase in the chat
3. Check that MOVI doesn't respond with "I'm not sure what you want to do"

---

## B. **Driver Assignment Workflow Tests**

### B1. Complete Success Scenarios

| Test Case | Steps | Expected Result |
|-----------|--------|----------------|
| B1.1 | 1. Select trip<br>2. Type "assign John to this trip" | ✅ "John has been assigned to this trip" |
| B1.2 | 1. Select trip<br>2. Type "allocate Sarah as driver" | ✅ "Sarah has been assigned to this trip" |
| B1.3 | 1. Select trip<br>2. Type "set driver to Mike" | ✅ "Mike has been assigned to this trip" |

### B2. Missing Information Scenarios

| Test Case | Steps | Expected Result |
|-----------|--------|----------------|
| B2.1 | 1. Don't select trip<br>2. Type "assign John as driver" | ⚠️ "Which trip would you like to assign a driver to?" |
| B2.2 | 1. Select trip<br>2. Type "assign a driver" | ⚠️ "Which driver would you like to assign?" |
| B2.3 | 1. Select trip<br>2. Type "allocate someone" | ⚠️ "Which driver would you like to assign?" |

### B3. Error Scenarios

| Test Case | Steps | Expected Result |
|-----------|--------|----------------|
| B3.1 | 1. Select trip<br>2. Type "assign NonExistentDriver" | ❌ "I couldn't find a driver named 'NonExistentDriver'" |
| B3.2 | 1. Select invalid trip<br>2. Type "assign John" | ❌ Trip-related error message |

---

## C. **Backwards Compatibility Tests**

Ensure existing functionality still works:

| Test Case | Input | Expected Result |
|-----------|--------|----------------|
| C1.1 | "cancel trip Morning Route" | ✅ Should work as before |
| C1.2 | "list all trips" | ✅ Should work as before |
| C1.3 | "assign_vehicle:123" | ✅ Regex patterns should still work |
| C1.4 | "what trips do I have" | ✅ Should work as before |

---

## D. **Edge Cases & Error Handling**

### D1. Ambiguous Input
| Test Case | Input | Expected Behavior |
|-----------|--------|------------------|
| D1.1 | "assign" | ⚠️ Asks for clarification |
| D1.2 | "driver John" | ⚠️ Asks what to do with driver |
| D1.3 | "John trip" | ⚠️ Asks for clarification |

### D2. Special Characters & Names
| Test Case | Input | Expected Behavior |
|-----------|--------|------------------|
| D2.1 | "assign O'Brien to trip" | ✅ Should handle apostrophes |
| D2.2 | "assign Van Der Berg" | ✅ Should handle multi-part names |
| D2.3 | "assign driver with space names" | ✅ Should handle spaces |

---

## 🔧 **Debugging & Monitoring**

### Where to Look for Issues

1. **Browser Console** (F12)
   - Check for JavaScript errors
   - Look for failed API calls
   
2. **Backend Logs**
   - Look for these log patterns:
     ```
     [LLM] 🤖 Processing natural language input: 'assign John to this trip'
     [DRIVER] Looking up driver by name: 'John'
     [ASSIGN_DRIVER] ✅ Success: John has been assigned to trip 123
     ```

3. **Network Tab** (F12 → Network)
   - Check `/agent/chat` API calls
   - Verify request/response structure

### Common Error Patterns & Solutions

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| "I'm not sure what you want to do" | LLM parsing disabled or failing | Check graph_def.py USE_LLM_PARSE=True |
| "Driver not found" | Driver name doesn't exist in DB | Check driver table, try exact names |
| No response at all | Backend connection issue | Check docker-compose logs |
| "Missing trip_id" | Trip not selected properly | Select trip from list first |

---

## 📊 **Validation Checklist**

Use this checklist to confirm everything works:

### ✅ Natural Language Understanding Fixed
- [ ] "assign John to this trip" → recognizes as assign_driver (not "not sure")
- [ ] "allocate a driver" → asks for driver name (not "not sure") 
- [ ] "set driver to Sarah" → recognizes as assign_driver (not "not sure")
- [ ] Multiple natural language variations work

### ✅ Driver Assignment Functionality Fixed  
- [ ] Complete workflow: select trip → type "assign John" → gets success message
- [ ] Driver lookup by name works
- [ ] Database assignment actually happens (check trip details)
- [ ] Error handling for non-existent drivers

### ✅ Error Handling & Edge Cases
- [ ] Missing trip → asks for trip selection
- [ ] Missing driver → asks for driver name  
- [ ] Invalid driver name → proper error message
- [ ] Ambiguous input → asks for clarification

### ✅ Backwards Compatibility
- [ ] Existing trip actions still work
- [ ] Regex patterns still work as fallback
- [ ] Other agent functionality unaffected

---

## 🎯 **Step-by-Step Testing Procedure**

### Test 1: Basic Natural Language Recognition
```
1. Open MOVI frontend
2. Select any trip from the list
3. Type: "assign John to this trip"
4. Expected: Should NOT say "I'm not sure what you want to do"
5. Expected: Should either assign John OR ask "I couldn't find driver John"
```

### Test 2: Complete Driver Assignment
```
1. Check your database for actual driver names
2. Select a trip
3. Type: "assign [ACTUAL_DRIVER_NAME] to this trip"
4. Expected: "[DRIVER_NAME] has been assigned to this trip"
5. Verify: Check trip details to confirm assignment
```

### Test 3: Missing Information Handling
```
1. Don't select any trip
2. Type: "assign John as driver"  
3. Expected: "Which trip would you like to assign a driver to?"
4. Select a trip
5. Type: "assign a driver"
6. Expected: "Which driver would you like to assign?"
```

### Test 4: Error Scenarios
```
1. Select a trip
2. Type: "assign NonExistentDriverName123"
3. Expected: "I couldn't find a driver named 'NonExistentDriverName123'"
```

---

## 🚨 **What to Do If Tests Fail**

### If Natural Language Still Not Working:
1. Check backend logs for `[LLM]` entries
2. Verify graph_def.py has `USE_LLM_PARSE = True`
3. Check if LLM service is connected (OpenAI/Gemini)

### If Driver Assignment Not Working:
1. Check backend logs for `[ASSIGN_DRIVER]` entries  
2. Verify database has driver records
3. Check if tool_assign_driver function exists in tools.py

### If Getting "Not Sure" Responses:
1. LLM parsing might be falling back to regex
2. Check confidence scores in logs
3. Verify system prompt has driver assignment examples

---

## 📈 **Success Criteria**

**✅ COMPLETE SUCCESS** when:
1. Natural language phrases like "assign John to this trip" work (no more "not sure")
2. Complete driver assignment workflow functions end-to-end  
3. Error handling provides helpful guidance
4. Existing functionality remains intact

**🎉 Both original issues will be RESOLVED!**
