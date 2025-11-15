# 🧪 DAY 9 MANUAL TESTING GUIDE

**MoviWidget Conversational Agent - Complete Test Suite**

---

## 🚀 Prerequisites

### 1. Start Backend Server
```powershell
cd c:\Users\rudra\Desktop\movi\backend
python -m uvicorn app.main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Start Frontend Server
```powershell
cd c:\Users\rudra\Desktop\movi\frontend
npm run dev
```

**Expected Output**:
```
VITE ready in 500ms
Local: http://localhost:5173/
```

### 3. Open Browser
Navigate to: `http://localhost:5173`

---

## 📋 Test Suite Overview

| Test # | Feature | Duration | Priority |
|--------|---------|----------|----------|
| 1 | Widget Open/Close | 2 min | HIGH |
| 2 | Basic Text Chat | 3 min | HIGH |
| 3 | Risky Action - Consequence Card | 5 min | HIGH |
| 4 | Confirm Action + Auto Refresh | 5 min | HIGH |
| 5 | Cancel Action | 3 min | HIGH |
| 6 | Ambiguous Clarification | 5 min | MEDIUM |
| 7 | Fallback Handling | 3 min | MEDIUM |
| 8 | Multi-turn Conversation | 5 min | MEDIUM |
| 9 | UI/UX Features | 5 min | HIGH |
| 10 | Error Handling | 3 min | MEDIUM |

**Total Time**: ~40 minutes

---

## TEST 1: Widget Open/Close ✅

### Objective
Verify widget toggle functionality and visual appearance

### Steps
1. Open BusDashboard page
2. Look for blue circular button at bottom-right corner
3. Click the button
4. Widget should slide open
5. Click X button in header
6. Widget should close
7. Click blue button again to reopen

### Expected Results
- ✅ Blue circular button visible (floating)
- ✅ Button has chat icon
- ✅ Widget opens smoothly
- ✅ Widget has blue gradient header
- ✅ Header shows "MOVI Assistant" with icon
- ✅ X button closes widget
- ✅ Widget reopens with same state

### Screenshots to Verify
- Closed state: Blue button visible
- Open state: Full widget with header, empty state, input

### Pass Criteria
All 7 checkboxes must be ✅

---

## TEST 2: Basic Text Chat ✅

### Objective
Test simple message sending and agent response

### Steps
1. Open widget
2. In input box, type: `Hello`
3. Press Enter
4. Wait for agent response
5. Type: `What can you help me with?`
6. Press Enter
7. Wait for response

### Expected Results
- ✅ User message appears immediately (blue bubble, right-aligned)
- ✅ Loading indicator shows ("MOVI is thinking..." with animated dots)
- ✅ Agent response appears (white bubble, left-aligned)
- ✅ Agent has MOVI avatar icon
- ✅ Timestamps visible on all messages
- ✅ Messages auto-scroll to bottom
- ✅ Chat history preserved

### Visual Checks
- User bubble: Blue background, white text, rounded-br-none
- Agent bubble: White background, gray text, MOVI icon, rounded-bl-none
- Timestamps: Small gray text below each message

### Pass Criteria
All agent responses are properly formatted and visible

---

## TEST 3: Risky Action - Consequence Card ✅

### Objective
Test consequence evaluation and risk card rendering

### Steps
1. Ensure BusDashboard has trips loaded
2. In widget, type: `Remove vehicle from Path-3 - 07:30`
3. Press Enter
4. Wait for consequence card to appear

### Expected Results

#### Consequence Card Appearance
- ✅ Card has colored left border (red/orange/yellow based on risk)
- ✅ Warning icon visible (triangle or info icon)
- ✅ Title: "⚠️ Confirmation Required"
- ✅ Message explains the action

#### Impact Analysis Section
- ✅ White card with "Impact Analysis" header
- ✅ Bullet points with icons:
  - 👥 Passenger count with active bookings
  - 📊 Booking percentage
  - 🚗 Vehicle ID (if deployed)
  - 👤 Driver ID (if assigned)
  - 📍 Live status
- ✅ Highlighted items (bold) if high impact

#### Action Details Section
- ✅ White card showing:
  - Action: `remove_vehicle`
  - Trip ID: (number)
- ✅ Monospace font for technical details

#### Warning Message
- ✅ "Please review carefully" warning
- ✅ "This action cannot be undone"
- ✅ Risk level warning if high

#### Bottom Section
- ✅ Timestamp visible
- ✅ Message: "Use the buttons below to confirm or cancel"
- ✅ Input box DISABLED
- ✅ Placeholder text changed

### Risk Level Detection
Test different scenarios:
- **High risk**: Booking count > 5, or live_status = "in_transit"
- **Medium risk**: Booking count 1-5
- **Low risk**: Booking count = 0

### Visual Verification
```
┌────────────────────────────────────┐
│ 🔺 Warning Icon                    │
│ ⚠️ Confirmation Required           │
│ This action will affect passengers │
├────────────────────────────────────┤
│ Impact Analysis                    │
│ 👥 7 passengers with bookings      │
│ 📊 35% capacity filled             │
│ 🚗 Vehicle ID: 10                  │
│ 📍 Status: SCHEDULED               │
├────────────────────────────────────┤
│ Action: remove_vehicle             │
│ Trip ID: 12                        │
├────────────────────────────────────┤
│ ⚡ Please review carefully         │
│ This action cannot be undone       │
└────────────────────────────────────┘
```

### Pass Criteria
Consequence card displays all sections correctly with proper styling

---

## TEST 4: Confirm Action + Auto Refresh ✅

### Objective
Test confirmation flow and dashboard auto-refresh

### Steps
1. Continue from Test 3 (consequence card visible)
2. Look at bottom of widget - should see Confirm/Cancel buttons
3. Note current state of trip list (vehicle ID)
4. Click **Confirm** button
5. Wait for response
6. Observe dashboard

### Expected Results

#### Confirmation Buttons
- ✅ Two buttons at bottom in gradient blue section
- ✅ Cancel button: White/gray, X icon, left side
- ✅ Confirm button: Blue, checkmark icon, right side
- ✅ Buttons are not disabled

#### After Clicking Confirm
- ✅ Loading indicator appears
- ✅ Buttons become disabled (opacity 50%)
- ✅ Green success card appears:
  - Checkmark icon
  - "Action Completed" title
  - Success message
  - Action name and Trip ID shown
- ✅ Timestamp visible

#### Auto Refresh
- ✅ Dashboard trip list refreshes automatically (500ms delay)
- ✅ Selected trip updates with new data
- ✅ Vehicle ID removed (or status changed)
- ✅ TripDetail panel reflects changes

#### Session Reset
- ✅ session_id cleared
- ✅ awaitingConfirm = false
- ✅ Input box re-enabled
- ✅ Placeholder returns to "Type a message..."
- ✅ Confirm/Cancel buttons disappear

### Database Verification (Optional)
```powershell
# Check agent_sessions table
$query = "SELECT session_id, status, pending_action FROM agent_sessions ORDER BY created_at DESC LIMIT 1;"
# Expected: status = 'DONE'
```

### Pass Criteria
- Action executed successfully
- Dashboard refreshed automatically
- Widget ready for next interaction

---

## TEST 5: Cancel Action ✅

### Objective
Test cancellation flow (no database mutation)

### Steps
1. In widget, type another risky action: `Cancel Path-2 - 09:00`
2. Wait for consequence card
3. Click **Cancel** button
4. Observe response

### Expected Results

#### After Clicking Cancel
- ✅ Loading indicator appears briefly
- ✅ Agent message appears: "Action cancelled. No changes were made."
- ✅ Message in normal agent bubble (white, left-aligned)
- ✅ No green success card (since nothing executed)
- ✅ Session reset
- ✅ Input re-enabled

#### Database State
- ✅ No trip changes in database
- ✅ agent_sessions row has status = 'CANCELLED'
- ✅ No audit logs created for the action

#### Widget State
- ✅ Confirm/Cancel buttons disappear
- ✅ Ready for next message
- ✅ Previous consequence card still visible in history

### Verification
```powershell
# Query trip before cancel
$beforeQuery = "SELECT vehicle_id FROM trips WHERE trip_id = X;"
# Cancel action
# Query trip after cancel
$afterQuery = "SELECT vehicle_id FROM trips WHERE trip_id = X;"
# Expected: vehicle_id unchanged
```

### Pass Criteria
- No database mutations occurred
- Widget handles cancellation gracefully
- User can continue chatting

---

## TEST 6: Ambiguous Clarification ✅

### Objective
Test ambiguous query handling and option selection

### Steps
1. In widget, type: `Cancel the 8am trip`
2. Wait for response
3. Observe option buttons
4. Click one of the options
5. Wait for consequence card

### Expected Results

#### Clarification Response
- ✅ Agent message: "Which trip did you mean?"
- ✅ Option buttons appear below message
- ✅ Each button shows trip name (e.g., "Jayanagar – 08:00")
- ✅ Buttons styled: white bg, blue border, hover effect
- ✅ Multiple options visible (2-3 typically)

#### Button Styling
- ✅ White background
- ✅ Blue border (border-blue-300)
- ✅ Blue text (text-blue-700)
- ✅ Hover: border-blue-500, bg-blue-50
- ✅ Left-aligned text
- ✅ Rounded corners
- ✅ Shadow

#### After Clicking Option
- ✅ User message appears with selected option text
- ✅ Widget auto-sends message to backend
- ✅ Agent processes specific trip
- ✅ Consequence card appears (if risky)
- ✅ Normal flow continues

### Alternative Test Cases
Try these ambiguous queries:
- `Remove the vehicle` (no trip specified)
- `Assign a bus to 9am route` (multiple 9am routes)
- `Cancel the morning trip` (multiple morning trips)

### Pass Criteria
- Agent requests clarification
- Options are clickable
- Selection triggers new message
- Flow continues normally

---

## TEST 7: Fallback Handling ✅

### Objective
Test how widget handles unrecognized input

### Steps
1. In widget, type: `asdfghjkl random nonsense text`
2. Press Enter
3. Observe response

### Expected Results

#### Fallback Card
- ✅ Red/orange warning card appears
- ✅ Left border: red-400 or orange-400
- ✅ Background: red-50 or orange-50
- ✅ Info icon (circle with exclamation mark)
- ✅ Title: "Need More Information"
- ✅ Message: "I couldn't understand that"
- ✅ Suggestion text: "Try being more specific..."
- ✅ Timestamp visible

#### Visual Check
```
┌────────────────────────────────────┐
│ ℹ️ Need More Information           │
│                                    │
│ I couldn't understand that.        │
│                                    │
│ Try being more specific or use a   │
│ different format.                  │
│                                    │
│ 2:45 PM                            │
└────────────────────────────────────┘
```

#### Widget State
- ✅ Input remains enabled
- ✅ User can try again immediately
- ✅ No confirmation buttons appear
- ✅ Session not created

### Test Additional Fallback Cases
- `blah blah blah`
- `????`
- `123456789`
- Empty message (should not send)

### Pass Criteria
- Fallback messages render correctly
- User can continue chatting
- No crashes or errors

---

## TEST 8: Multi-turn Conversation ✅

### Objective
Test conversation history and context preservation

### Steps
1. Open widget
2. Send 5 different messages:
   - `Hello`
   - `Show me trips`
   - `Remove vehicle from Path-3 - 07:30`
   - (Wait for consequence, then Cancel)
   - `Thank you`
3. Scroll through conversation

### Expected Results

#### Message History
- ✅ All 5+ messages visible in order
- ✅ User messages right-aligned (blue)
- ✅ Agent messages left-aligned (white)
- ✅ Consequence card preserved in history
- ✅ Cancelled action message visible
- ✅ Timestamps on all messages

#### Scroll Behavior
- ✅ Scroll bar appears when content exceeds container
- ✅ Auto-scrolls to bottom on new message
- ✅ User can manually scroll up to review history
- ✅ New message scrolls back to bottom

#### Context Preservation
- ✅ All messages remain after scroll
- ✅ Session data preserved across messages
- ✅ Widget state consistent

#### Clear Chat Function
- ✅ Click trash icon in header
- ✅ Confirmation prompt (optional)
- ✅ All messages cleared
- ✅ Empty state shows welcome message
- ✅ Widget ready for new conversation

### Pass Criteria
- Full conversation history maintained
- Scroll works correctly
- Clear chat resets properly

---

## TEST 9: UI/UX Features ✅

### Objective
Comprehensive visual and interaction testing

### Visual Elements to Check

#### Header
- ✅ Gradient background: blue-600 to blue-700
- ✅ White text
- ✅ MOVI icon in circle (bulb icon)
- ✅ Title: "MOVI Assistant"
- ✅ Subtitle: "Your AI Fleet Manager"
- ✅ Trash icon (if messages exist)
- ✅ X close button

#### Empty State
- ✅ Large chat icon (gray)
- ✅ Welcome text: "Welcome to MOVI Assistant!"
- ✅ Instructions visible
- ✅ Example prompt: "Remove vehicle from Path-3 - 07:30"

#### Loading Indicator
- ✅ Three animated dots
- ✅ Bounce animation (staggered timing)
- ✅ Blue color (blue-400)
- ✅ Text: "MOVI is thinking..."

#### Input Box
- ✅ Textarea (not input)
- ✅ Auto-expanding on type
- ✅ Max height limit
- ✅ Placeholder text clear
- ✅ Border focus state (blue ring)
- ✅ Send button (paper plane icon)
- ✅ Keyboard shortcuts hint below

#### Confirmation Buttons
- ✅ Gradient blue background
- ✅ Centered at bottom
- ✅ Equal width buttons
- ✅ Icons visible
- ✅ Hover effects work
- ✅ Disabled state visible

#### Responsive Design
Test at different widths:
- ✅ Desktop (1920px): Widget 384px (w-96)
- ✅ Tablet (768px): Widget still visible
- ✅ Mobile (375px): Widget adjusts or hides

### Interaction Features

#### Keyboard Shortcuts
- ✅ Enter to send
- ✅ Shift+Enter for new line
- ✅ Tab navigation works
- ✅ Esc closes widget (optional)

#### Mouse Interactions
- ✅ Hover states on buttons
- ✅ Click animations
- ✅ Drag scroll in message area
- ✅ Text selection works

#### Accessibility
- ✅ Color contrast sufficient
- ✅ Icons have labels
- ✅ Focus visible
- ✅ Screen reader friendly (aria labels)

### Pass Criteria
All visual elements and interactions work correctly

---

## TEST 10: Error Handling ✅

### Objective
Test widget behavior on errors

### Test Case 1: Backend Down
1. Stop backend server
2. Send a message in widget
3. Observe error handling

**Expected**:
- ✅ Error banner appears at top
- ✅ Red background with error icon
- ✅ Message: "Failed to send message"
- ✅ Error message added to chat
- ✅ Widget remains functional
- ✅ Can retry after backend restarts

### Test Case 2: Network Error
1. Disconnect internet (or block localhost)
2. Send message
3. Observe error

**Expected**:
- ✅ Similar to backend down
- ✅ Error logged to console
- ✅ User sees error message

### Test Case 3: Invalid Session ID
1. Send risky action
2. Wait for consequence card
3. Manually clear localStorage (if storing session)
4. Click Confirm

**Expected**:
- ✅ Backend returns error
- ✅ Widget shows error message
- ✅ Session resets gracefully
- ✅ User can start new conversation

### Test Case 4: Malformed Response
This requires backend modification to test, but widget should:
- ✅ Handle missing fields gracefully
- ✅ Show generic error if parsing fails
- ✅ Log error to console
- ✅ Not crash

### Pass Criteria
Widget handles all error cases without crashing

---

## 🎯 Quick Test Script (5 Minutes)

For rapid validation, run this minimal test:

### Steps
1. Open widget
2. Type: `Remove vehicle from Path-3 - 07:30`
3. Verify consequence card appears
4. Click Confirm
5. Verify green success message
6. Verify dashboard refreshes

### Pass/Fail
- **PASS**: All 6 steps work
- **FAIL**: Any step fails

---

## 📊 Test Results Template

```markdown
# Day 9 Test Results

**Date**: ___________
**Tester**: ___________
**Environment**: Local Dev

| Test # | Feature | Status | Notes |
|--------|---------|--------|-------|
| 1 | Widget Open/Close | ☐ PASS ☐ FAIL | |
| 2 | Basic Text Chat | ☐ PASS ☐ FAIL | |
| 3 | Risky Action - Consequence Card | ☐ PASS ☐ FAIL | |
| 4 | Confirm Action + Auto Refresh | ☐ PASS ☐ FAIL | |
| 5 | Cancel Action | ☐ PASS ☐ FAIL | |
| 6 | Ambiguous Clarification | ☐ PASS ☐ FAIL | |
| 7 | Fallback Handling | ☐ PASS ☐ FAIL | |
| 8 | Multi-turn Conversation | ☐ PASS ☐ FAIL | |
| 9 | UI/UX Features | ☐ PASS ☐ FAIL | |
| 10 | Error Handling | ☐ PASS ☐ FAIL | |

**Overall Status**: ☐ ALL PASS ☐ SOME FAIL

**Issues Found**: (list any)

**Screenshots**: (attach if needed)
```

---

## 🐛 Troubleshooting Guide

### Issue: Widget doesn't appear
**Solution**: 
- Check browser console for errors
- Verify MoviWidget imported in page
- Check z-index (should be 50)
- Refresh page

### Issue: Messages not sending
**Solution**:
- Check backend is running (port 8000)
- Verify API key in .env
- Check network tab for 401/403 errors
- Verify CORS settings

### Issue: Consequence card doesn't show
**Solution**:
- Check backend response format
- Verify `awaiting_confirmation` or `needs_confirmation` is true
- Check console for parsing errors
- Test with curl/Postman first

### Issue: Auto-refresh not working
**Solution**:
- Verify `onRefresh` prop passed to widget
- Check callback actually refreshes data
- Add console.log to verify callback called
- Check 500ms delay is sufficient

### Issue: Buttons not clickable
**Solution**:
- Check `disabled` state
- Verify `awaitingConfirm` is true
- Check z-index of buttons
- Look for overlaying elements

### Issue: Loading indicator stuck
**Solution**:
- Check if API response received
- Look for unhandled promise rejections
- Verify `setLoading(false)` in finally block
- Check for infinite loops

---

## ✅ Final Checklist

Before marking Day 9 complete:

- [ ] All 10 tests pass
- [ ] No console errors
- [ ] No visual glitches
- [ ] Responsive on mobile
- [ ] Backend integration works
- [ ] Auto-refresh working
- [ ] Session persistence correct
- [ ] Error handling graceful
- [ ] Code documented
- [ ] Screenshots taken

---

**Testing Complete!** 🎉

If all tests pass, Day 9 is ready for production!
