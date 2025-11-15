# PowerShell script to test API endpoints
# Usage: .\test_api.ps1

$API_KEY = "dev-key-change-in-production"
$BASE_URL = "http://localhost:8000"

Write-Host "`n=== Testing MOVI REST API ===" -ForegroundColor Cyan

# Test 1: Root endpoint (no auth required)
Write-Host "`n1. Testing root endpoint..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$BASE_URL/" -Method Get
$response | ConvertTo-Json -Depth 3

# Test 2: Health status (with auth)
Write-Host "`n2. Testing health status..." -ForegroundColor Yellow
$headers = @{ "x-api-key" = $API_KEY }
$response = Invoke-RestMethod -Uri "$BASE_URL/api/health/status" -Method Get -Headers $headers
$response | ConvertTo-Json -Depth 3

# Test 3: Health ping
Write-Host "`n3. Testing health ping..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$BASE_URL/api/health/ping" -Method Get -Headers $headers
$response | ConvertTo-Json -Depth 3

# Test 4: List routes (should fail without auth)
Write-Host "`n4. Testing routes without auth (should fail)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/routes/" -Method Get
    Write-Host "UNEXPECTED: Request succeeded without auth!" -ForegroundColor Red
} catch {
    Write-Host "EXPECTED: Auth required - $($_.Exception.Message)" -ForegroundColor Green
}

# Test 5: List routes (with auth)
Write-Host "`n5. Testing list routes..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/routes/" -Method Get -Headers $headers
    Write-Host "Found $($response.routes.Count) routes" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: List stops
Write-Host "`n6. Testing list stops..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/routes/stops/all" -Method Get -Headers $headers
    Write-Host "Found $($response.stops.Count) stops" -ForegroundColor Green
    $response.stops | Select-Object -First 3 | ConvertTo-Json -Depth 2
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: List vehicles
Write-Host "`n7. Testing list vehicles..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/routes/vehicles/all" -Method Get -Headers $headers
    Write-Host "Found $($response.vehicles.Count) vehicles" -ForegroundColor Green
    $response.vehicles | Select-Object -First 3 | ConvertTo-Json -Depth 2
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 8: Dashboard context
Write-Host "`n8. Testing dashboard context..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/context/dashboard" -Method Get -Headers $headers
    Write-Host "Dashboard Summary:" -ForegroundColor Green
    $response.summary | ConvertTo-Json -Depth 2
    Write-Host "`nFirst 2 trips:" -ForegroundColor Green
    $response.trips | Select-Object -First 2 | ConvertTo-Json -Depth 2
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 9: Manage context
Write-Host "`n9. Testing manage context..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/context/manage" -Method Get -Headers $headers
    Write-Host "Manage context loaded:" -ForegroundColor Green
    Write-Host "  - Stops: $($response.stops.Count)"
    Write-Host "  - Routes: $($response.routes.Count)"
    Write-Host "  - Paths: $($response.paths.Count)"
    Write-Host "  - Vehicles: $($response.vehicles.Count)"
    Write-Host "  - Drivers: $($response.drivers.Count)"
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 10: Recent audit logs
Write-Host "`n10. Testing recent audit logs..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/audit/logs/recent?limit=5" -Method Get -Headers $headers
    Write-Host "Found $($response.logs.Count) recent audit logs" -ForegroundColor Green
    $response.logs | Select-Object -First 3 | ConvertTo-Json -Depth 2
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 11: Database health
Write-Host "`n11. Testing database health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/health/database" -Method Get -Headers $headers
    Write-Host "Database info:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== All tests completed ===" -ForegroundColor Cyan
Write-Host "`nAPI Documentation: $BASE_URL/docs" -ForegroundColor Green
