# 🧪 DAY 8 MANUAL TESTING SCRIPT

## Prerequisites
```powershell
# 1. Backend running
cd backend
uvicorn app.main:app --reload --port 8000

# 2. Frontend running (in another terminal)
cd frontend
npm run dev
```

---

## Test 1: Risky Action (Requires Confirmation)

### PowerShell Command
```powershell
$headers = @{
    "x-api-key" = "dev-key-change-in-production"
    "Content-Type" = "application/json"
}

$body = @{
    text = "Remove vehicle from Path-3 - 07:30"
    user_id = 1
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body

# Display results
Write-Host "`n=== RISKY ACTION TEST ===" -ForegroundColor Yellow
Write-Host "Action: $($response.agent_output.action)"
Write-Host "Trip ID: $($response.agent_output.trip_id)"
Write-Host "Needs Confirmation: $($response.agent_output.needs_confirmation)" -ForegroundColor $(if($response.agent_output.needs_confirmation){"Green"}else{"Red"})
Write-Host "Session ID: $($response.session_id)" -ForegroundColor $(if($response.session_id){"Green"}else{"Red"})
Write-Host "Booking Count: $($response.agent_output.consequences.booking_count)"
Write-Host "Message: $($response.agent_output.message)"
```

### Expected Output
```
=== RISKY ACTION TEST ===
Action: remove_vehicle
Trip ID: 5
Needs Confirmation: True          [GREEN]
Session ID: <UUID>                [GREEN]
Booking Count: 8
Message: ⚠️ This trip has 8 active booking(s) (10% capacity)

❓ Do you want to proceed?
```

### ✅ Pass Criteria
- [x] `needs_confirmation` = True
- [x] `session_id` is non-null UUID
- [x] `booking_count` > 0
- [x] Message contains warning emoji and question

---

## Test 2: Safe Action (No Confirmation)

### PowerShell Command
```powershell
# First, find a trip without bookings
$body2 = @{
    text = "Assign vehicle to Path-1 - 08:00"
    user_id = 1
} | ConvertTo-Json

$response2 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body2

Write-Host "`n=== SAFE ACTION TEST ===" -ForegroundColor Yellow
Write-Host "Action: $($response2.agent_output.action)"
Write-Host "Trip ID: $($response2.agent_output.trip_id)"
Write-Host "Needs Confirmation: $($response2.agent_output.needs_confirmation)" -ForegroundColor $(if($response2.agent_output.needs_confirmation){"Red"}else{"Green"})
Write-Host "Status: $($response2.agent_output.status)"
```

### Expected Output
```
=== SAFE ACTION TEST ===
Action: assign_vehicle
Trip ID: 1
Needs Confirmation: False         [GREEN]
Status: <error or executed>
```

### ✅ Pass Criteria
- [x] `needs_confirmation` = False (or error if already deployed)
- [x] No session_id needed
- [x] Action executes immediately (or error shown)

---

## Test 3: User Confirms Action

### PowerShell Command
```powershell
# Use session_id from Test 1
$sessionId = $response.session_id

if ($sessionId) {
    $confirmBody = @{
        session_id = $sessionId
        confirmed = $true
        user_id = 1
    } | ConvertTo-Json
    
    $confirmResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/confirm" -Method POST -Headers $headers -Body $confirmBody
    
    Write-Host "`n=== CONFIRMATION TEST ===" -ForegroundColor Yellow
    Write-Host "Status: $($confirmResponse.agent_output.status)" -ForegroundColor $(if($confirmResponse.agent_output.status -eq "executed"){"Green"}else{"Red"})
    Write-Host "Success: $($confirmResponse.agent_output.success)"
    Write-Host "Message: $($confirmResponse.agent_output.message)"
    Write-Host "Action: $($confirmResponse.agent_output.action)"
    Write-Host "Trip ID: $($confirmResponse.agent_output.trip_id)"
} else {
    Write-Host "ERROR: No session_id from Test 1!" -ForegroundColor Red
}
```

### Expected Output
```
=== CONFIRMATION TEST ===
Status: executed                  [GREEN]
Success: True
Message: ✅ Vehicle removed from trip 5
Action: remove_vehicle
Trip ID: 5
```

### ✅ Pass Criteria
- [x] `status` = "executed"
- [x] `success` = True
- [x] Message contains success emoji
- [x] Action was performed in database

---

## Test 4: User Cancels Action

### PowerShell Command
```powershell
# Send a new risky action
$body3 = @{
    text = "Cancel Path-3 - 07:30"
    user_id = 1
} | ConvertTo-Json

$response3 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body3
$sessionId3 = $response3.session_id

Write-Host "`n=== NEW ACTION ===" -ForegroundColor Yellow
Write-Host "Session ID: $sessionId3"

# Cancel it
if ($sessionId3) {
    $cancelBody = @{
        session_id = $sessionId3
        confirmed = $false
        user_id = 1
    } | ConvertTo-Json
    
    $cancelResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/confirm" -Method POST -Headers $headers -Body $cancelBody
    
    Write-Host "`n=== CANCELLATION TEST ===" -ForegroundColor Yellow
    Write-Host "Status: $($cancelResponse.agent_output.status)" -ForegroundColor $(if($cancelResponse.agent_output.status -eq "cancelled"){"Green"}else{"Red"})
    Write-Host "Success: $($cancelResponse.agent_output.success)"
    Write-Host "Message: $($cancelResponse.agent_output.message)"
}
```

### Expected Output
```
=== NEW ACTION ===
Session ID: <UUID>

=== CANCELLATION TEST ===
Status: cancelled                 [GREEN]
Success: True
Message: ❌ Action cancelled by user.
```

### ✅ Pass Criteria
- [x] `status` = "cancelled"
- [x] No DB mutation occurred
- [x] Message indicates cancellation

---

## Test 5: Check Database Sessions

### PostgreSQL Query
```sql
-- Run in your Supabase SQL editor or psql
SELECT 
    session_id,
    user_id,
    status,
    pending_action->>'action' as action,
    pending_action->>'trip_id' as trip_id,
    created_at,
    updated_at
FROM agent_sessions
ORDER BY created_at DESC
LIMIT 10;
```

### Expected Output
```
session_id                            | user_id | status    | action         | trip_id | created_at          | updated_at
--------------------------------------|---------|-----------|----------------|---------|---------------------|-------------------
1200a7bc-b956-48cf-996b-31088c9a8d1b  | 1       | DONE      | remove_vehicle | 5       | 2025-11-13 08:00:00 | 2025-11-13 08:01:00
959175ca-cc6e-4ae8-a727-b7e810b1c447  | 1       | CANCELLED | cancel_trip    | 5       | 2025-11-13 08:02:00 | 2025-11-13 08:02:30
```

### ✅ Pass Criteria
- [x] Sessions created with PENDING status
- [x] Status transitions to DONE after confirm
- [x] Status transitions to CANCELLED after cancel
- [x] pending_action stored as JSONB
- [x] Timestamps updated correctly

---

## Test 6: Consequence Accuracy

### PowerShell Command
```powershell
# Test with different trips
$trips = @(
    @{name="Path-3 - 07:30"; expected_bookings=8},
    @{name="Bulk - 00:01"; expected_bookings=5}
)

foreach ($trip in $trips) {
    $testBody = @{
        text = "Remove vehicle from $($trip.name)"
        user_id = 1
    } | ConvertTo-Json
    
    $testResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $testBody
    
    Write-Host "`n=== TRIP: $($trip.name) ===" -ForegroundColor Cyan
    Write-Host "Booking Count: $($testResponse.agent_output.consequences.booking_count) (Expected: $($trip.expected_bookings))"
    Write-Host "Booking %: $($testResponse.agent_output.consequences.booking_percentage)%"
    Write-Host "Has Deployment: $($testResponse.agent_output.consequences.has_deployment)"
    Write-Host "Live Status: $($testResponse.agent_output.consequences.live_status)"
    Write-Host "Match: $(if($testResponse.agent_output.consequences.booking_count -eq $trip.expected_bookings){"✅ PASS"}else{"❌ FAIL"})"
}
```

### Expected Output
```
=== TRIP: Path-3 - 07:30 ===
Booking Count: 8 (Expected: 8)
Booking %: 10%
Has Deployment: True
Live Status: IN_PROGRESS
Match: ✅ PASS

=== TRIP: Bulk - 00:01 ===
Booking Count: 5 (Expected: 5)
Booking %: 25%
Has Deployment: True
Live Status: COMPLETED
Match: ✅ PASS
```

### ✅ Pass Criteria
- [x] Booking counts match database
- [x] Booking percentages accurate
- [x] Deployment status correct
- [x] Live status reflects reality

---

## Test 7: Frontend UI Test

### Steps
1. Open `http://localhost:5173` in browser
2. Open browser DevTools (F12) → Console tab
3. Type: "Remove vehicle from Path-3 - 07:30"
4. Click Send

### Expected UI Behavior
```
Chat shows:
👤 You: Remove vehicle from Path-3 - 07:30

🤖 MOVI: ⚠️ This trip has 8 active booking(s) (10% capacity)

❓ Do you want to proceed?

[✓ Confirm]  [✗ Cancel]  ← These buttons should appear
```

### Click "Confirm"
```
🤖 MOVI: ✅ Vehicle removed from trip 5
```

### Click "Cancel"
```
🤖 MOVI: ❌ Action cancelled by user.
```

### Check Browser Console
```javascript
Confirming action for session: 1200a7bc-b956-48cf-996b-31088c9a8d1b
Confirmation response: {agent_output: {...}}
```

### ✅ Pass Criteria
- [x] Buttons appear when needs_confirmation=true
- [x] Confirm button calls /api/agent/confirm
- [x] Cancel button calls /api/agent/confirm with confirmed=false
- [x] Loading indicator shows during API call
- [x] Results displayed in chat
- [x] No console errors

---

## Test 8: Resolve Target Variations

### PowerShell Command
```powershell
$variations = @(
    "Cancel Path-3 - 07:30",
    "Cancel the Path-3 - 07:30 trip",
    "Remove vehicle from Bulk",
    "Remove bus from Bulk - 00:01"
)

Write-Host "`n=== RESOLVE TARGET VARIATIONS ===" -ForegroundColor Yellow

foreach ($text in $variations) {
    $varBody = @{
        text = $text
        user_id = 1
    } | ConvertTo-Json
    
    $varResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $varBody
    
    Write-Host "`nInput: $text"
    Write-Host "  Action: $($varResponse.agent_output.action)"
    Write-Host "  Trip ID: $($varResponse.agent_output.trip_id)"
    Write-Host "  Trip Label: $($varResponse.agent_output.trip_label)"
    Write-Host "  Status: $(if($varResponse.agent_output.trip_id){"✅ RESOLVED"}else{"❌ FAILED"})" -ForegroundColor $(if($varResponse.agent_output.trip_id){"Green"}else{"Red"})
}
```

### Expected Output
```
=== RESOLVE TARGET VARIATIONS ===

Input: Cancel Path-3 - 07:30
  Action: cancel_trip
  Trip ID: 5
  Trip Label: Path-3 - 07:30
  Status: ✅ RESOLVED

Input: Cancel the Path-3 - 07:30 trip
  Action: cancel_trip
  Trip ID: 5
  Trip Label: Path-3 - 07:30
  Status: ✅ RESOLVED

Input: Remove vehicle from Bulk
  Action: remove_vehicle
  Trip ID: 7
  Trip Label: Bulk - 00:01
  Status: ✅ RESOLVED

Input: Remove bus from Bulk - 00:01
  Action: remove_vehicle
  Trip ID: 7
  Trip Label: Bulk - 00:01
  Status: ✅ RESOLVED
```

### ✅ Pass Criteria
- [x] All variations resolve correctly
- [x] Regex extraction working
- [x] Action correctly parsed
- [x] Trip ID found

---

## 🟢 ALL TESTS PASSING = DAY 8 READY FOR DAY 9

### Checklist
- [ ] Test 1: Risky action needs confirmation ✅
- [ ] Test 2: Safe action executes immediately ✅
- [ ] Test 3: User can confirm action ✅
- [ ] Test 4: User can cancel action ✅
- [ ] Test 5: Database sessions created correctly ✅
- [ ] Test 6: Consequences calculated accurately ✅
- [ ] Test 7: Frontend UI buttons work ✅
- [ ] Test 8: Multiple input variations resolve ✅

### If Any Test Fails
1. Check backend logs: `backend terminal output`
2. Check database: Run Test 5 SQL query
3. Check session_id: Should be non-null UUID
4. Check API response structure
5. Refer to `DAY8_VALIDATION_REPORT.md`

---

## Quick All-in-One Test

### Run All Tests Sequentially
```powershell
# Save this as test_day8_manual.ps1

$headers = @{
    "x-api-key" = "dev-key-change-in-production"
    "Content-Type" = "application/json"
}

Write-Host "🧪 DAY 8 MANUAL TEST SUITE" -ForegroundColor Cyan
Write-Host "=" * 60

# Test 1: Risky Action
Write-Host "`n[1/4] Testing risky action..." -ForegroundColor Yellow
$body1 = @{text = "Remove vehicle from Path-3 - 07:30"; user_id = 1} | ConvertTo-Json
$r1 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body1
$t1 = $r1.agent_output.needs_confirmation -and $r1.session_id
Write-Host "Result: $(if($t1){"✅ PASS"}else{"❌ FAIL"})" -ForegroundColor $(if($t1){"Green"}else{"Red"})

# Test 2: Confirmation
Write-Host "`n[2/4] Testing confirmation..." -ForegroundColor Yellow
if ($r1.session_id) {
    $body2 = @{session_id = $r1.session_id; confirmed = $true; user_id = 1} | ConvertTo-Json
    $r2 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/confirm" -Method POST -Headers $headers -Body $body2
    $t2 = $r2.agent_output.status -eq "executed"
    Write-Host "Result: $(if($t2){"✅ PASS"}else{"❌ FAIL"})" -ForegroundColor $(if($t2){"Green"}else{"Red"})
}

# Test 3: Cancellation
Write-Host "`n[3/4] Testing cancellation..." -ForegroundColor Yellow
$body3 = @{text = "Cancel Path-3 - 07:30"; user_id = 1} | ConvertTo-Json
$r3 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body3
if ($r3.session_id) {
    $body4 = @{session_id = $r3.session_id; confirmed = $false; user_id = 1} | ConvertTo-Json
    $r4 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/confirm" -Method POST -Headers $headers -Body $body4
    $t3 = $r4.agent_output.status -eq "cancelled"
    Write-Host "Result: $(if($t3){"✅ PASS"}else{"❌ FAIL"})" -ForegroundColor $(if($t3){"Green"}else{"Red"})
}

# Test 4: Resolve Variations
Write-Host "`n[4/4] Testing resolve variations..." -ForegroundColor Yellow
$variations = @("Cancel Path-3 - 07:30", "Remove vehicle from Bulk - 00:01")
$t4 = $true
foreach ($v in $variations) {
    $body5 = @{text = $v; user_id = 1} | ConvertTo-Json
    $r5 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body5
    if (-not $r5.agent_output.trip_id) { $t4 = $false }
}
Write-Host "Result: $(if($t4){"✅ PASS"}else{"❌ FAIL"})" -ForegroundColor $(if($t4){"Green"}else{"Red"})

Write-Host "`n" + "=" * 60
Write-Host "🎉 DAY 8 MANUAL TESTS COMPLETE" -ForegroundColor Cyan
```

### Run It
```powershell
.\test_day8_manual.ps1
```

---

**Status**: Ready to test! 🚀
