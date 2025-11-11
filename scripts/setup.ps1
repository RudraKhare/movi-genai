# Setup script for Windows (PowerShell)
# This script sets up the development environment for the Movi project

Write-Host "Setting up Movi development environment..." -ForegroundColor Green

# Check Python installation
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "Python not found. Please install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

# Check Node.js installation
Write-Host "`nChecking Node.js installation..." -ForegroundColor Yellow
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "Found Node: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "Node.js not found. Please install Node.js 18+ from nodejs.org" -ForegroundColor Red
    exit 1
}

# Setup Backend
Write-Host "`n=== Setting up Backend ===" -ForegroundColor Cyan
Set-Location backend

Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv .venv

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Backend setup complete!" -ForegroundColor Green
Set-Location ..

# Setup Frontend
Write-Host "`n=== Setting up Frontend ===" -ForegroundColor Cyan
Set-Location frontend

Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Write-Host "Frontend setup complete!" -ForegroundColor Green
Set-Location ..

# Create .env.local from .env.example if not exists
Write-Host "`n=== Environment Configuration ===" -ForegroundColor Cyan
if (!(Test-Path .env.local)) {
    Write-Host "Creating .env.local from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env.local
    Write-Host ".env.local created. Please edit it with your credentials." -ForegroundColor Yellow
} else {
    Write-Host ".env.local already exists." -ForegroundColor Green
}

Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env.local with your Supabase credentials (or use Docker Postgres)" -ForegroundColor White
Write-Host "2. Start backend:  cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "3. Start frontend: cd frontend; npm run dev" -ForegroundColor White
Write-Host "4. Visit http://localhost:5173 to see the app" -ForegroundColor White
