# Quick Test - Day 8 Confirmation Flow

## Test the complete flow in 3 steps:

### Step 1: Test message that needs confirmation
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

# Check the response
Write-Host "Action: $($response.agent_output.action)"
Write-Host "Trip ID: $($response.agent_output.trip_id)"
Write-Host "Needs Confirmation: $($response.agent_output.needs_confirmation)"
Write-Host "Session ID: $($response.session_id)"
Write-Host "Booking Count: $($response.agent_output.consequences.booking_count)"

# Save session ID for step 2
$sessionId = $response.session_id
```

### Step 2: Confirm the action
```powershell
$confirmBody = @{
    session_id = $sessionId
    confirmed = $true
    user_id = 1
} | ConvertTo-Json

$confirmResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/confirm" -Method POST -Headers $headers -Body $confirmBody

# Check result
Write-Host "`nConfirmation Result:"
Write-Host "Status: $($confirmResponse.agent_output.status)"
Write-Host "Success: $($confirmResponse.agent_output.success)"
Write-Host "Message: $($confirmResponse.agent_output.message)"
```

### Step 3: Test cancellation
```powershell
# Send another message
$body2 = @{
    text = "Cancel Path-3 - 07:30"
    user_id = 1
} | ConvertTo-Json

$response2 = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/message" -Method POST -Headers $headers -Body $body2
$sessionId2 = $response2.session_id

# Cancel it
$cancelBody = @{
    session_id = $sessionId2
    confirmed = $false
    user_id = 1
} | ConvertTo-Json

$cancelResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/confirm" -Method POST -Headers $headers -Body $cancelBody

Write-Host "`nCancellation Result:"
Write-Host "Status: $($cancelResponse.agent_output.status)"
Write-Host "Message: $($cancelResponse.agent_output.message)"
```

## Expected Output:

### Step 1:
```
Action: remove_vehicle
Trip ID: 5
Needs Confirmation: True
Session ID: <UUID>
Booking Count: 8
```

### Step 2:
```
Confirmation Result:
Status: executed
Success: True
Message: ✅ Vehicle removed from trip 5
```

### Step 3:
```
Cancellation Result:
Status: cancelled
Message: ❌ Action cancelled by user.
```

## If session_id is NULL:
```powershell
# Check backend logs for error:
Get-Content backend/logs/app.log -Tail 50 | Select-String "confirmation|session"

# Or check if backend is running:
Invoke-RestMethod -Uri "http://localhost:8000/api/agent/health"
```
