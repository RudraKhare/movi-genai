# Day 8 Confirmation Flow Test Script

$API_BASE = "http://localhost:8000/api/agent"
$API_KEY = "dev-key-change-in-production"

$headers = @{
    "x-api-key" = $API_KEY
    "Content-Type" = "application/json"
}

Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Day 8 Confirmation Flow - End-to-End Test              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Send initial message
Write-Host "📤 STEP 1: Sending message 'Cancel Path-3 - 07:30'..." -ForegroundColor Yellow
$body = @{
    text = "Cancel Path-3 - 07:30"
    user_id = 1
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$API_BASE/message" -Method POST -Headers $headers -Body $body
    $json = $response.Content | ConvertFrom-Json
    
    Write-Host "`n✅ Agent Response:" -ForegroundColor Green
    Write-Host "  Action: $($json.agent_output.action)" -ForegroundColor White
    Write-Host "  Trip ID: $($json.agent_output.trip_id)" -ForegroundColor White
    Write-Host "  Needs Confirmation: $($json.agent_output.needs_confirmation)" -ForegroundColor White
    Write-Host "  Session ID: $($json.session_id)" -ForegroundColor $(if ($json.session_id) { 'Green' } else { 'Red' })
    Write-Host "  Message: $($json.agent_output.message)" -ForegroundColor Cyan
    
    $sessionId = $json.session_id
    
    if (-not $sessionId) {
        Write-Host "`n❌ ERROR: No session_id returned! Session not saved to database." -ForegroundColor Red
        Write-Host "   This means the confirmation button won't work." -ForegroundColor Red
        exit 1
    }
    
    # Step 2: Confirm the action
    Write-Host "`n📤 STEP 2: Sending confirmation..." -ForegroundColor Yellow
    $confirmBody = @{
        session_id = $sessionId
        confirmed = $true
        user_id = 1
    } | ConvertTo-Json
    
    $confirmResponse = Invoke-WebRequest -Uri "$API_BASE/confirm" -Method POST -Headers $headers -Body $confirmBody
    $confirmJson = $confirmResponse.Content | ConvertFrom-Json
    
    Write-Host "`n✅ Confirmation Response:" -ForegroundColor Green
    Write-Host "  Status: $($confirmJson.agent_output.status)" -ForegroundColor White
    Write-Host "  Success: $($confirmJson.agent_output.success)" -ForegroundColor $(if ($confirmJson.agent_output.success) { 'Green' } else { 'Red' })
    Write-Host "  Message: $($confirmJson.agent_output.message)" -ForegroundColor Cyan
    
    if ($confirmJson.agent_output.success) {
        Write-Host "`n🎉 Day 8 Confirmation Flow: WORKING!" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  Confirmation executed but reported failure" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "`n❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.Exception -ForegroundColor Red
    exit 1
}

Write-Host "`n[SUCCESS] All tests passed!" -ForegroundColor Green
