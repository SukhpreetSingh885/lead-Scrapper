# =====================================================================
# India Leads Platform - Windows PowerShell Quick Launch Script
# Launches Backend API (FastAPI) and Frontend Dashboard (Next.js)
# =====================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   STARTING INDIA LEADS PLATFORM (LOCAL ENVIRONMENT)     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$PythonExe = if (Test-Path "backend\.venv\Scripts\python.exe") { "backend\.venv\Scripts\python.exe" } else { "python" }
$UvicornExe = if (Test-Path "backend\.venv\Scripts\uvicorn.exe") { "backend\.venv\Scripts\uvicorn.exe" } else { "uvicorn" }

# Launch FastAPI backend
Write-Host "Starting Backend on http://localhost:8000 (Swagger docs: http://localhost:8000/docs)..." -ForegroundColor Green
$BackendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; & '$UvicornExe' app.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru

# Launch Next.js frontend
Write-Host "Starting Frontend on http://localhost:3000..." -ForegroundColor Green
$FrontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru

Write-Host "`nBoth services launched in separate windows!" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Swagger Docs: http://localhost:8000/docs" -ForegroundColor Cyan

