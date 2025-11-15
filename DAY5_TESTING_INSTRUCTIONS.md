# 🧪 Day 5 - Manual Testing Instructions

## Prerequisites

### 1. Start Backend Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
✅ Database pool initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Start Frontend Server
```bash
cd frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### 3. Open Browser
Navigate to: `http://localhost:5173`

---

## Test Sequence

### ✅ Test 1: Dashboard Load
**Action:** Load the page  
**Expected:**
- Header shows "MOVI Dashboard" with blue gradient
- Navigation shows "🚌 Dashboard" and "⚙️ Manage Routes"
- Summary stats display: Total Trips, Deployed, Pending, Total Bookings, Seats Booked
- Left sidebar shows 8 trips from database
- Each trip card shows: route name, date, time, status badge, booking counts
- Right side shows "Select a trip to view details" with 🚌 icon

**Verify:**
- [ ] No console errors
- [ ] All trip cards visible
- [ ] Status badges color-coded correctly
- [ ] Summary numbers match database

---

### ✅ Test 2: Trip Selection
**Action:** Click on first trip in list  
**Expected:**
- Trip card gets blue border and blue background
- Right panel shows trip details:
  - Trip name, ID, date, time, direction
  - Status badge (larger)
  - Deployment info card (vehicle/driver if deployed)
  - Booking info card (confirmed count, seats)
  - Three action buttons (green, yellow, red)

**Verify:**
- [ ] Selected trip highlighted
- [ ] Trip details display correctly
- [ ] Action buttons visible and enabled/disabled appropriately

---

### ✅ Test 3: Assign Vehicle
**Action:** Click "➕ Assign Vehicle" button  
**Expected:**
- Modal overlay appears with blue header
- Title: "🚌 Assign Vehicle & Driver"
- Shows trip details (route, date, time, bookings)
- Vehicle dropdown populated with available vehicles
- Driver dropdown populated with available drivers
- Both dropdowns show counts of available options
- Submit button disabled until both selected

**Action:** Select a vehicle and driver, click "✅ Assign"  
**Expected:**
- Submit button shows "Assigning..." with spinner
- Modal closes on success
- Dashboard refreshes automatically
- Selected trip now shows vehicle and driver info
- Trip card in sidebar shows vehicle number (🚌) and driver name (👨‍✈️)

**Verify:**
- [ ] Modal opens correctly
- [ ] Dropdowns populated
- [ ] Form validation works
- [ ] Assignment succeeds
- [ ] UI updates after assignment
- [ ] No console errors

---

### ✅ Test 4: Remove Vehicle
**Action:** Click "➖ Remove Vehicle" button on deployed trip  
**Expected:**
- Browser confirmation dialog: "Remove vehicle deployment from this trip? Bookings will remain."
- Click OK

**Expected:**
- Loading overlay appears with spinner
- API call completes
- Dashboard refreshes
- Trip no longer shows vehicle/driver
- Deployment card shows "⚠️ Not yet deployed"
- Booking count unchanged (bookings remain)

**Verify:**
- [ ] Confirmation dialog appears
- [ ] Removal succeeds
- [ ] Vehicle removed from trip
- [ ] Bookings not affected
- [ ] No console errors

---

### ✅ Test 5: Cancel Trip
**Action:** Click "❌ Cancel Trip" button  
**Expected:**
- Browser confirmation dialog: "Cancel this trip? All confirmed bookings will be cancelled."
- Click OK

**Expected:**
- Loading overlay appears
- API call completes
- Dashboard refreshes
- Trip status changes to "CANCELLED" (red badge)
- Action buttons disappear or disabled for cancelled trip
- Booking count may change

**Verify:**
- [ ] Confirmation dialog appears
- [ ] Cancellation succeeds
- [ ] Status changes to CANCELLED
- [ ] UI reflects cancellation state
- [ ] No console errors

---

### ✅ Test 6: Movi Widget
**Action:** Click floating 💬 button (bottom-right corner)  
**Expected:**
- Chat window slides up from bottom
- Header: "🤖 Movi Assistant - AI Transport Operations Agent"
- Welcome message displays with capabilities list
- If trip selected: Shows context bubble with trip details
- Input box disabled with placeholder text
- Buttons show: 🎤 Voice, 📸 Image (disabled)
- Text: "LangGraph integration coming in Day 7-8"

**Action:** Click X to close  
**Expected:**
- Chat window closes
- Only FAB remains visible

**Verify:**
- [ ] Widget opens/closes smoothly
- [ ] Animation works (slide-up)
- [ ] Context displays when trip selected
- [ ] Welcome message shows
- [ ] UI polished and clean

---

### ✅ Test 7: Navigation
**Action:** Click "⚙️ Manage Routes" in header  
**Expected:**
- URL changes to `/manage`
- Page shows ManageRoute placeholder:
  - Header: "⚙️ Manage Routes"
  - Large 🗺️ icon
  - "Coming in Day 6" heading
  - Description text
  - 3 feature cards: Route Management, Path Configuration, Timing Setup

**Action:** Click "🚌 Dashboard" in header  
**Expected:**
- Returns to dashboard page
- Trip list and selection state preserved (or reset, both acceptable)

**Verify:**
- [ ] Navigation works
- [ ] ManageRoute placeholder displays
- [ ] Can navigate back to dashboard
- [ ] No console errors

---

### ✅ Test 8: Error Handling
**Action:** Stop the backend server (Ctrl+C)  
**Expected:**
- Dashboard shows loading spinner initially
- After timeout: Red error box appears
- Message: "❌ Error - Failed to load dashboard data"
- "Try Again" button visible

**Action:** Restart backend, click "Try Again"  
**Expected:**
- Dashboard reloads successfully
- Trips list populates
- Error message disappears

**Verify:**
- [ ] Error state displays
- [ ] Error message user-friendly
- [ ] Retry button works
- [ ] Recovers after backend restart

---

### ✅ Test 9: Refresh Button
**Action:** Click "🔄 Refresh" in header  
**Expected:**
- Dashboard data reloads
- Trip list updates
- Selected trip updates with fresh data
- Summary stats refresh
- Quick operation (< 1 second)

**Verify:**
- [ ] Refresh works
- [ ] No page reload
- [ ] Data updates correctly
- [ ] Fast response

---

### ✅ Test 10: Responsive Design
**Action:** Resize browser window to mobile width (< 768px)  
**Expected:**
- Layout adapts (may stack vertically)
- All text readable
- Buttons remain touchable
- No horizontal scrolling
- Movi widget remains accessible

**Action:** Resize back to desktop width  
**Expected:**
- Layout returns to side-by-side
- All functionality intact

**Verify:**
- [ ] Mobile layout works
- [ ] Desktop layout works
- [ ] No UI breaking at any width
- [ ] All features accessible

---

## Browser DevTools Checks

### Console Tab
- [ ] No errors (red messages)
- [ ] No warnings about missing dependencies
- [ ] No CORS errors
- [ ] API calls succeed (200 OK)

### Network Tab
**Check these API calls succeed:**
- [ ] GET `/api/context/dashboard` → 200 OK
- [ ] GET `/api/context/manage` → 200 OK (when opening assign modal)
- [ ] POST `/api/actions/assign_vehicle` → 200 OK
- [ ] POST `/api/actions/remove_vehicle` → 200 OK
- [ ] POST `/api/actions/cancel_trip` → 200 OK

**Check headers:**
- [ ] All requests include `x-api-key` header
- [ ] CORS headers present in responses

### Performance
- [ ] Initial page load < 2 seconds
- [ ] Dashboard refresh < 1 second
- [ ] No memory leaks (check Memory tab over time)
- [ ] Smooth animations (60fps)

---

## Known Issues / Expected Behavior

### Not Implemented Yet
1. **Audit Log Viewer** - Click "View Audit" shows placeholder alert
2. **Movi Chat Input** - Input is disabled, shows "Coming Soon"
3. **Real-time Updates** - No auto-refresh, manual refresh required
4. **Search/Filter** - No search functionality yet
5. **Pagination** - All trips load at once (fine for current 8 trips)

### By Design
1. **User ID Hardcoded** - All actions use user_id=999 (admin)
2. **API Key in .env** - Development key, change for production
3. **No Authentication** - No login system yet
4. **Simple Confirmations** - Browser confirm() used (can upgrade to custom modals later)

---

## Success Criteria

✅ **All tests passing:**
- Dashboard loads and displays trips
- Trip selection and details work
- All 3 actions (assign/remove/cancel) succeed
- Movi widget opens and closes
- Navigation works
- Error handling graceful
- Responsive design functional
- No console errors

✅ **Ready for Day 6:**
- Frontend complete and stable
- API integration verified
- UI polished and user-friendly
- Documentation complete

---

## If Tests Fail

### Backend Connection Errors (403 Forbidden)
**Cause:** Middleware fix not applied or backend not restarted  
**Fix:** 
1. Verify `backend/app/middleware.py` has OPTIONS exemption
2. Restart backend server
3. Clear browser cache and reload

### API Key Errors
**Cause:** .env not configured or wrong key  
**Fix:**
1. Check `frontend/.env` has `VITE_MOVI_API_KEY=dev-key-change-in-production`
2. Restart frontend server (Vite reads .env on startup)

### CORS Errors
**Cause:** Backend CORS not allowing frontend origin  
**Fix:**
1. Check `backend/app/main.py` includes `http://localhost:5173` in `allow_origins`
2. Restart backend server

### Dropdown Empty in Assign Modal
**Cause:** No available vehicles/drivers in database  
**Fix:**
1. Check database has vehicles and drivers with status='available'
2. Run seed script if needed

### UI Not Loading
**Cause:** Frontend build error or dependency issue  
**Fix:**
1. Check terminal for Vite errors
2. Run `npm install` to ensure dependencies installed
3. Clear browser cache
4. Try incognito mode

---

## Report Issues

If any test fails or unexpected behavior occurs:

1. **Check Browser Console** - Copy any error messages
2. **Check Network Tab** - Note which API call failed
3. **Check Terminal Output** - Backend and frontend logs
4. **Document Steps** - Exact steps to reproduce
5. **Create GitHub Issue** - With all above information

---

**Testing Prepared By:** GitHub Copilot  
**Date:** November 12, 2025  
**Version:** Day 5 - BusDashboard Frontend  
**Status:** Ready for Manual Validation ✅
