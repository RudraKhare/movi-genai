# 🧪 Day 6 Manual Testing Guide

## Quick Start

### 1. Start Servers
```powershell
# Terminal 1 - Backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Access Application
- Frontend: http://localhost:5173/manage-route
- Backend API: http://localhost:8000/docs

---

## Test Scenarios

### ✅ Scenario 1: Create Your First Stop
**Steps**:
1. Open http://localhost:5173/manage-route
2. In left column (Stops), type "Main Gate" in input
3. Click "Add Stop" button
4. **Expected**: Loading spinner → Stop appears in list with #1 and green "Active" badge

**Validation**:
- [ ] Stop appears immediately after creation
- [ ] Loading spinner shown during API call
- [ ] Stop has sequential numbering
- [ ] Status badge displays as green "Active"

---

### ✅ Scenario 2: Test Stop Validation
**Steps**:
1. Leave stop name input empty
2. Click "Add Stop"
3. **Expected**: Red error message "Stop name is required"

**Validation**:
- [ ] Error message displays in red alert box
- [ ] No API call made (check Network tab)
- [ ] Button remains enabled for retry

---

### ✅ Scenario 3: Create Multiple Stops
**Steps**:
1. Create 4 stops in sequence:
   - "Main Gate"
   - "College Building"
   - "Library"
   - "Sports Complex"
2. **Expected**: All 4 stops appear numbered 1-4

**Validation**:
- [ ] Each stop created successfully
- [ ] Numbering is sequential
- [ ] List scrolls if needed
- [ ] All stops have "Active" status

---

### ✅ Scenario 4: Create a Path with Ordered Stops
**Steps**:
1. In middle column (Paths), enter "Morning Route A" as path name
2. From dropdown, select "Main Gate" → Click to add
3. Select "College Building" → Click to add
4. Select "Library" → Click to add
5. **Expected**: Ordered list shows:
   - 1. Main Gate
   - 2. College Building
   - 3. Library

**Validation**:
- [ ] Stops appear in selected order
- [ ] Each stop has move up/down/remove buttons
- [ ] Dropdown shows selected stops with ✓ mark
- [ ] Can't add same stop twice

---

### ✅ Scenario 5: Test Stop Ordering in Path
**Steps**:
1. Create path with 3 stops as above
2. Click ↑ button on "Library" (3rd stop)
3. **Expected**: "Library" moves to position 2
4. Click ↓ button on "Main Gate"
5. **Expected**: "Main Gate" moves to position 2

**Validation**:
- [ ] Move up button works correctly
- [ ] Move down button works correctly
- [ ] First item's ↑ button is disabled
- [ ] Last item's ↓ button is disabled
- [ ] Numbering updates automatically

---

### ✅ Scenario 6: Remove Stop from Path
**Steps**:
1. Create path with 3 stops
2. Click ✕ button on middle stop
3. **Expected**: Stop removed, list renumbered 1→2

**Validation**:
- [ ] Stop removed from path
- [ ] Remaining stops renumber automatically
- [ ] Stop becomes available in dropdown again

---

### ✅ Scenario 7: Test Path Validation
**Steps**:
1. Enter path name "Test Path"
2. Add only 1 stop
3. Click "Create Path"
4. **Expected**: Red error "Path must have at least 2 stops"

**Validation**:
- [ ] Error displays before API call
- [ ] No network request made
- [ ] Can add more stops and retry

---

### ✅ Scenario 8: Successfully Create Path
**Steps**:
1. Enter "Morning Route A" as path name
2. Add at least 2 stops in desired order
3. Click "Create Path (3 stops)" button
4. **Expected**: 
   - Loading spinner shows
   - Path appears in path list above
   - Shows stop count
   - Form resets

**Validation**:
- [ ] Path created successfully
- [ ] Appears in path list with stop count
- [ ] Form clears after creation
- [ ] Selected stops reset

---

### ✅ Scenario 9: Create a Route
**Steps**:
1. In right column (Routes), enter "R101 Morning"
2. Select shift time "08:00"
3. Select path from dropdown (e.g., "Morning Route A")
4. Select direction "UP"
5. Click "Create Route"
6. **Expected**: Route appears with purple time badge and blue direction badge

**Validation**:
- [ ] Route created successfully
- [ ] Shift time displays in purple badge
- [ ] Direction displays in blue badge
- [ ] Form resets after creation

---

### ✅ Scenario 10: Test Route Validation
**Steps**:
1. Try creating route with empty name → Error
2. Try creating route without shift time → Error
3. Try creating route without selecting path → Error

**Validation**:
- [ ] All fields validated before submission
- [ ] Clear error messages displayed
- [ ] No partial routes created

---

### ✅ Scenario 11: Test Page Refresh
**Steps**:
1. Create 2 stops, 1 path, 1 route
2. Click refresh button in header
3. **Expected**: Loading spinner → All data reloads

**Validation**:
- [ ] Loading overlay displays
- [ ] All created entities persist
- [ ] Counts in header update
- [ ] No console errors

---

### ✅ Scenario 12: Test Error Handling (Network Failure)
**Steps**:
1. Stop backend server (Ctrl+C in terminal)
2. Try creating a stop
3. **Expected**: Red error message "Failed to create stop"
4. Restart backend
5. Retry → Should succeed

**Validation**:
- [ ] Error message displays for network failure
- [ ] User can retry after error
- [ ] No app crash
- [ ] Success after backend restart

---

### ✅ Scenario 13: Test Responsive Layout
**Steps**:
1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test these screen sizes:
   - Mobile (375px): Single column stacked
   - Tablet (768px): 3 columns appear
   - Desktop (1920px): 3 columns with proper spacing

**Validation**:
- [ ] Mobile shows single column
- [ ] Tablet/Desktop shows 3 columns
- [ ] No horizontal scrolling
- [ ] All buttons accessible

---

### ✅ Scenario 14: Test Keyboard Navigation
**Steps**:
1. Tab through all form fields
2. Press Enter in stop name input
3. **Expected**: Stop created (same as clicking button)

**Validation**:
- [ ] Can tab through all inputs
- [ ] Enter key works in stop input
- [ ] Focus indicators visible
- [ ] Dropdowns accessible via keyboard

---

### ✅ Scenario 15: Test Empty States
**Steps**:
1. Load page with no data
2. **Expected**: Each column shows "No X yet" message

**Validation**:
- [ ] Stops: "No stops yet"
- [ ] Paths: "No paths yet"
- [ ] Routes: "No routes yet"
- [ ] Messages are centered and gray

---

### ✅ Scenario 16: Full Workflow Test
**Steps**:
1. Create 5 stops
2. Create 2 paths using different stops
3. Create 3 routes using different paths and times
4. Refresh page
5. **Expected**: All data persists and displays correctly

**Validation**:
- [ ] All 5 stops visible and numbered
- [ ] All 2 paths visible with stop counts
- [ ] All 3 routes visible with time/direction
- [ ] Header stats correct (5 stops, 2 paths, 3 routes)

---

## Network Debugging

### Check API Calls (DevTools Network Tab)
1. Open DevTools → Network tab
2. Filter: "Fetch/XHR"
3. Create a stop
4. **Expected Request**:
   ```
   POST http://localhost:8000/api/routes/stops/create
   Headers: x-api-key: dev-key-change-in-production
   Payload: { "name": "Main Gate" }
   ```
5. **Expected Response**:
   ```json
   {
     "success": true,
     "stop": {
       "stop_id": 1,
       "name": "Main Gate",
       "status": "Active"
     }
   }
   ```

### Verify CORS
- OPTIONS request should return 200
- Access-Control-Allow-Origin header present
- No CORS errors in console

---

## Browser Console Checks

### Should NOT See:
- ❌ CORS errors
- ❌ 404 Not Found errors
- ❌ Undefined variable errors
- ❌ React key warnings
- ❌ Network failures

### Should See:
- ✅ Successful API responses (200)
- ✅ "Context loaded" logs (if any)
- ✅ Clean console on page load

---

## Database Verification (Optional)

If you have Supabase access:

### Check Stops Table
```sql
SELECT * FROM stops ORDER BY stop_id;
```
**Expected**: All created stops with "Active" status

### Check Paths Table
```sql
SELECT p.*, COUNT(ps.stop_id) as stop_count
FROM paths p
LEFT JOIN path_stops ps ON p.path_id = ps.path_id
GROUP BY p.path_id;
```
**Expected**: Paths with correct stop counts

### Check Path Stops Table
```sql
SELECT ps.*, s.name
FROM path_stops ps
JOIN stops s ON ps.stop_id = s.stop_id
ORDER BY ps.path_id, ps.stop_order;
```
**Expected**: Ordered stops for each path

### Check Routes Table
```sql
SELECT r.*, p.path_name
FROM routes r
JOIN paths p ON r.path_id = p.path_id;
```
**Expected**: Routes linked to correct paths

---

## Performance Testing

### Page Load Speed
- Initial load: < 2 seconds
- Subsequent refreshes: < 1 second

### API Response Times
- Create stop: < 300ms
- Create path: < 500ms
- Create route: < 400ms
- Load context: < 600ms

---

## Edge Cases to Test

### Large Data Sets
1. Create 50 stops
2. **Expected**: List scrolls, no performance issues

### Special Characters
1. Try stop name with emoji: "Main Gate 🚪"
2. **Expected**: Saves and displays correctly

### Rapid Clicks
1. Double-click "Add Stop" quickly
2. **Expected**: Only one stop created (loading state prevents duplicates)

### Long Names
1. Try very long stop name (100+ characters)
2. **Expected**: Saves correctly, UI handles gracefully

---

## ✅ Test Results Template

Copy this to track your testing:

```
[ ] Scenario 1: Create First Stop
[ ] Scenario 2: Stop Validation
[ ] Scenario 3: Multiple Stops
[ ] Scenario 4: Create Path
[ ] Scenario 5: Stop Ordering
[ ] Scenario 6: Remove Stop
[ ] Scenario 7: Path Validation
[ ] Scenario 8: Create Path Success
[ ] Scenario 9: Create Route
[ ] Scenario 10: Route Validation
[ ] Scenario 11: Page Refresh
[ ] Scenario 12: Network Failure
[ ] Scenario 13: Responsive Layout
[ ] Scenario 14: Keyboard Navigation
[ ] Scenario 15: Empty States
[ ] Scenario 16: Full Workflow

Browser Console: [ ] Clean
Network Tab: [ ] All 200s
Database: [ ] Data Persists
Performance: [ ] < 2s load

VERDICT: [ ] PASS / [ ] FAIL
```

---

**Testing Time**: ~15-20 minutes for full suite  
**Critical Scenarios**: 1, 4, 8, 9, 11, 16  
**Status**: Ready for testing
