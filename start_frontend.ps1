$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath (Join-Path $ScriptDir "frontend")

Write-Host "Installing dependencies if needed..." -ForegroundColor Cyan
npm install --silent

Write-Host "Starting Vite frontend on http://localhost:3000 ..." -ForegroundColor Green
Write-Host "Make sure the backend is running on http://127.0.0.1:8001" -ForegroundColor Yellow
npm run dev:vite
