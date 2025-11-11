# Reset MOVI database - drops all tables, recreates schema, and seeds data
# PowerShell version for Windows

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔄 MOVI Database Reset Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Load environment variables
if (Test-Path ".env.local") {
    Get-Content ".env.local" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
        }
    }
} else {
    Write-Host "❌ Error: .env.local file not found" -ForegroundColor Red
    exit 1
}

$DATABASE_URL = $env:DATABASE_URL
$SUPABASE_URL = $env:SUPABASE_URL

if (-not $DATABASE_URL -and -not $SUPABASE_URL) {
    Write-Host "❌ Error: No database connection configured" -ForegroundColor Red
    Write-Host "Please set DATABASE_URL or SUPABASE_URL in .env.local"
    exit 1
}

Write-Host ""
Write-Host "⚠️  WARNING: This will delete ALL data in the database!" -ForegroundColor Yellow
$confirm = Read-Host "Are you sure you want to continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "❌ Aborted" -ForegroundColor Red
    exit 0
}

Write-Host ""

# If using Supabase, guide user to run SQL manually
if ($SUPABASE_URL) {
    Write-Host "📝 Using Supabase - Please follow these steps:" -ForegroundColor Yellow
    Write-Host "1. Go to your Supabase project dashboard"
    Write-Host "2. Navigate to SQL Editor"
    Write-Host "3. Copy and paste the contents of: migrations\001_init.sql"
    Write-Host "4. Click 'Run'"
    Write-Host ""
    $sqlRun = Read-Host "Have you run the SQL migration? (yes/no)"
    
    if ($sqlRun -ne "yes") {
        Write-Host "❌ Please run the SQL migration first" -ForegroundColor Red
        exit 1
    }
} else {
    # Using local PostgreSQL
    Write-Host "🗑️  Dropping and recreating schema..." -ForegroundColor Yellow
    
    if (Get-Command psql -ErrorAction SilentlyContinue) {
        psql $DATABASE_URL -f migrations\001_init.sql
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Migration failed!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ psql command not found. Please install PostgreSQL client tools." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🌱 Seeding database..." -ForegroundColor Yellow

# Activate virtual environment if it exists
if (Test-Path "backend\.venv\Scripts\Activate.ps1") {
    & backend\.venv\Scripts\Activate.ps1
    python scripts\seed_db.py
    deactivate
} else {
    python scripts\seed_db.py
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Seeding failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Database reset complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  • View data in Supabase dashboard or pgAdmin"
Write-Host "  • Test queries: SELECT * FROM daily_trips;"
Write-Host "  • Start backend: cd backend && uvicorn app.main:app --reload"
