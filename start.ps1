$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating Python virtual environment..."
    py -m venv .venv
}

Write-Host "Installing backend dependencies..."
& .\.venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt

if (-not (Test-Path "frontend\dist\index.html")) {
    Write-Host "Building frontend..."
    npm install --prefix frontend
    npm run build --prefix frontend
}

if (-not (Test-Path "backend\.env")) {
    Write-Warning "backend\.env not found. Copy backend\.env.example to backend\.env and set DEEPSEEK_API_KEY for AI features."
}

Write-Host ""
Write-Host "PIANXIA: http://127.0.0.1:8000"
Write-Host ""

& .\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
