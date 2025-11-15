# 🧪 DAY 10 QUICK TEST GUIDE

## ⚡ 30-Second Test

### Prerequisites:
- Backend running: `http://localhost:8000`
- Frontend running: `http://localhost:5173`
- Browser refreshed (Ctrl + Shift + R)

### Test Steps:

1. **Open Dashboard**: `http://localhost:5173/dashboard`

2. **Take Screenshot**:
   - Screenshot any trip from the left panel (showing trip name like "Bulk - 00:01")
   - Save it as `test-trip.png`

3. **Upload Image**:
   - Click camera icon 📷 in Movi Assistant (bottom right)
   - Select `test-trip.png`
   - **WAIT** for processing (~2-5 seconds)

4. **Expected Result A** (Single Match):
   ```
   ✅ Image bubble shows: "Identified: Bulk - 00:01"
   ✅ Message appears: "I identified the trip: Bulk - 00:01 at 00:01. What would you like to do?"
   ✅ Two buttons appear:
      [Remove Vehicle]  [Cancel Trip]
   ```

5. **Click "Remove Vehicle"**

6. **Expected Result B** (Agent Response):
   ```
   ✅ Message: "Remove vehicle from Bulk - 00:01"
   ✅ Shows consequence check with booking count
   ✅ Shows [Confirm] [Cancel] buttons
   ```

7. **Click "Confirm"**

8. **Expected Result C** (Execution):
   ```
   ✅ Message: "✅ Vehicle removed from trip 12"
   ✅ Dashboard refreshes automatically
   ✅ Trip status changes in left panel
   ```

---

## 🔍 Console Logs to Verify

### Frontend Console:
```javascript
[MoviWidget] handleImageUpload called with file: File {name: "test-trip.png"}
[MoviWidget] OCR Response: {match_type: "single", trip_id: 1, display_name: "Bulk - 00:01"}
[MoviWidget] Single match detected, showing action prompt for trip_id: 1
[MoviWidget] Option clicked: {action: "remove_vehicle", trip_id: 1, name: "Remove Vehicle"}
[MoviWidget] Sending message with payload: {text: "Remove vehicle", selectedTripId: 1}
[MoviWidget] Agent reply: {action: "remove_vehicle", needs_confirmation: true, ...}
```

### Backend Terminal:
```
INFO:app.api.agent_image:Processing image: test-trip.png, size: 298284 bytes
INFO:app.api.agent_image:OCR extracted text: BULK Trip Date: 2025-11-11...
INFO:app.api.agent_image:Extracted 30 candidates: ['bulk - 00:01', 'bulk', ...]
INFO:app.core.trip_matcher:Match result: single
INFO:app.api.agent:Received agent message from user 1: Remove vehicle
INFO:app.api.agent:OCR-resolved trip_id provided: 1
INFO:langgraph.nodes.parse_intent:Parsing intent from: remove vehicle
INFO:langgraph.nodes.parse_intent:Identified action: remove_vehicle
INFO:langgraph.nodes.resolve_target:[BYPASS] Using OCR-resolved trip_id: 1
INFO:langgraph.nodes.resolve_target:[BYPASS] Resolved to: Bulk - 00:01 (ID: 1)
INFO:langgraph.nodes.check_consequences:Checking consequences for remove_vehicle on trip 1
```

---

## 🐛 Troubleshooting

### Issue: No logs appear
**Solution**: Hard refresh browser (Ctrl + Shift + R)

### Issue: "Failed to process image"
**Check**:
- Backend terminal for errors
- Network tab for 500 status code
- Database connection: `SELECT * FROM daily_trips LIMIT 1`

### Issue: "Could not identify trip"
**Check**:
- OCR text extraction (backend logs show extracted text)
- Database has matching trips
- Trip display_name format matches OCR output

### Issue: Action buttons don't appear
**Check**:
- `ocrResult.match_type === 'single'` in console log
- `ocrResult.auto_forward === true` in console log
- Frontend console for any errors

### Issue: Agent says "action: unknown"
**Check**:
- Backend logs show `selectedTripId` being passed
- Backend logs show `[BYPASS]` message in resolve_target
- Agent request payload includes `selectedTripId`

---

## ✅ Success Criteria

All these must be true:

- [x] Image uploads without errors
- [x] OCR extracts text successfully
- [x] Fuzzy matching identifies trip
- [x] Action buttons appear for single match
- [x] Clicking action button sends to agent with selectedTripId
- [x] Agent bypasses text parsing and uses provided trip_id
- [x] Consequence check works
- [x] Confirmation works
- [x] Execution works
- [x] Dashboard refreshes

---

## 🎯 Alternative Tests

### Test 2: Multiple Matches
1. Upload blurry image with partial text
2. **Expected**: Shows list of 3-5 candidate trips with confidence %
3. Click a candidate
4. **Expected**: Shows action buttons for that trip

### Test 3: No Match
1. Upload random image (not a trip screenshot)
2. **Expected**: Shows "Could not identify trip from image"

### Test 4: Cancel Trip Action
1. Upload trip image
2. Click "Cancel Trip" instead of "Remove Vehicle"
3. **Expected**: Agent asks for confirmation to cancel trip

---

## 📞 Need Help?

If tests fail after following this guide:

1. Check `DAY10_COMPLETE_FIX_SUMMARY.md` for detailed flow
2. Check backend terminal for exact error messages
3. Check frontend console for JavaScript errors
4. Verify all 6 files were modified correctly
5. Restart both backend and frontend servers

---

**Test Duration**: ~60 seconds per test
**Expected Pass Rate**: 100% for all scenarios

