# =====================================================================
# India Leads Platform - Windows PowerShell Automated Setup Script
# Run this script in PowerShell from the project root:
#   .\scripts\setup.ps1
# =====================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   INDIA LEADS PLATFORM - SETUP & INITIALIZATION         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ProjectRoot = Resolve-Path .
Write-Host "[1/4] Project Directory: $ProjectRoot" -ForegroundColor Yellow

# 1. Environment file check
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Green
    Copy-Item ".env.example" ".env"
} else {
    Write-Host ".env configuration file already exists." -ForegroundColor Green
}

# 2. Python Virtual Environment & Dependencies
Write-Host "`n[2/4] Setting up Python Backend Virtual Environment..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.venv")) {
    Write-Host "Creating Python virtual environment in backend\.venv..." -ForegroundColor Gray
    python -m venv backend\.venv
}

$PipExe = "backend\.venv\Scripts\pip.exe"
$PythonExe = "backend\.venv\Scripts\python.exe"

Write-Host "Installing Python dependencies from backend\requirements.txt..." -ForegroundColor Gray
& $PipExe install --upgrade pip
& $PipExe install -r backend\requirements.txt

# 3. Seed Database & India Locations
Write-Host "`n[3/4] Initializing Database & Seeding Indian Reference Data..." -ForegroundColor Yellow
& $PythonExe scripts\seed_demo.py

# 4. Frontend Node Dependencies
Write-Host "`n[4/4] Installing Frontend NPM Dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   SETUP COMPLETE! ALL DEPENDENCIES READY.                " -ForegroundColor Green
Write-Host "   To start the platform, run:                            " -ForegroundColor White
Write-Host "       .\scripts\start-all.ps1                             " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Green

