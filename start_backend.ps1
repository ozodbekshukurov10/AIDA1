$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ScriptDir

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
. .\.venv\Scripts\Activate.ps1

Write-Host "Starting Django backend on http://127.0.0.1:8001 ..." -ForegroundColor Green
python manage.py runserver 127.0.0.1:8001
