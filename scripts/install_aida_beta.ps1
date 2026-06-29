# AIDA Beta — Standalone Code Assistant Installer (Windows)
# Usage: .\scripts\install_aida_beta.ps1

$ErrorActionPreference = "Stop"
$AIDA_DIR = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    AIDA Beta — Code Assistant Installer  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Check Ollama
Write-Host "[1/5] Ollama tekshirilmoqda..." -ForegroundColor Yellow
$ollama = Get-Command "ollama" -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "  Ollama topilmadi. https://ollama.com dan o'rnating." -ForegroundColor Red
    Write-Host "  Yoki: winget install Ollama.Ollama" -ForegroundColor Gray
    exit 1
}
Write-Host "  Ollama: $($ollama.Source)" -ForegroundColor Green

# 2. Download base model
Write-Host "[2/5] Base model yuklanmoqda (qwen2.5-coder:3b)..." -ForegroundColor Yellow
ollama pull qwen2.5-coder:3b
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Model yuklanmadi!" -ForegroundColor Red
    exit 1
}
Write-Host "  Model yuklandi." -ForegroundColor Green

# 3. Build AIDA Beta model
Write-Host "[3/5] AIDA Beta modeli build qilinmoqda..." -ForegroundColor Yellow
$modelfile = Join-Path $AIDA_DIR "aida_beta" "Modelfile"
if (-not (Test-Path $modelfile)) {
    Write-Host "  Modelfile topilmadi: $modelfile" -ForegroundColor Red
    exit 1
}
ollama create aida-beta -f $modelfile
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Model build qilinmadi!" -ForegroundColor Red
    exit 1
}
Write-Host "  AIDA Beta modeli build qilindi." -ForegroundColor Green

# 4. Install Python package
Write-Host "[4/5] Python paket o'rnatilmoqda..." -ForegroundColor Yellow
$venv_python = Join-Path $AIDA_DIR ".venv" "Scripts" "python.exe"
if (Test-Path $venv_python) {
    & $venv_python -m pip install -e $AIDA_DIR --quiet 2>$null
} else {
    python -m pip install -e $AIDA_DIR --quiet 2>$null
}
Write-Host "  Python paket o'rnatildi." -ForegroundColor Green

# 5. Install CLI globally
Write-Host "[5/5] CLI o'rnatilmoqda..." -ForegroundColor Yellow
$cli_path = Join-Path $AIDA_DIR "aida_beta" "cli.py"
$alias_script = @"
function aida-beta {
    & python "$cli_path" @args
}
Set-Alias -Name aida -Value aida-beta -Scope Global
"@
$profilePath = $PROFILE.CurrentUserAllHosts
$profileDir = Split-Path $profilePath -Parent
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }

Add-Content -Path $profilePath -Value "`n# AIDA Beta CLI" -ErrorAction SilentlyContinue
Add-Content -Path $profilePath -Value "function aida-beta { & python `"$cli_path`" @args }" -ErrorAction SilentlyContinue
Add-Content -Path $profilePath -Value "Set-Alias -Name aida -Value aida-beta -Scope Global" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    O'RNATISH TUGALLANDI!                 ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  Buyruqlar:                              ║" -ForegroundColor Cyan
Write-Host "║    aida-beta          — Interactive REPL ║" -ForegroundColor White
Write-Host "║    aida               — qisqa alias      ║" -ForegroundColor White
Write-Host "║    aida-beta 'sozlov' — bir martalik     ║" -ForegroundColor White
Write-Host "║    aida-beta --help   — yordam           ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminalni qayta oching yoki: Import-Module $PROFILE.CurrentUserAllHosts" -ForegroundColor Gray
