param(
    [int]$Port = 8080,
    [switch]$Background,
    [switch]$InstallService,
    [switch]$RemoveService,
    [switch]$Status,
    [switch]$Stop,
    [switch]$Scheduled
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StdOutLog = Join-Path $ProjectRoot "server_out.log"
$StdErrLog = Join-Path $ProjectRoot "server_err.log"
$PidFile = Join-Path $ProjectRoot "aida.pid"

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = (Get-Command python).Source
}

$ManagePy = Join-Path $ProjectRoot "manage.py"

function Start-Server {
    param([bool]$Bg = $false)
    if ($Bg) {
        $job = Start-Job -Name "AIDA-Server" -ScriptBlock {
            param($Py, $Mng, $P)
            $env:PYTHONUNBUFFERED = "1"
            & $Py $Mng runserver "0.0.0.0:$P" --noreload
        } -ArgumentList $Python, $ManagePy, $Port
        $job.Id | Out-File -FilePath $PidFile -Force
        Write-Host "AIDA server ishga tushdi (Job ID: $($job.Id), port: $Port)" -ForegroundColor Green
        Write-Host "Log: $StdOutLog" -ForegroundColor Gray
        Write-Host "To'xtatish: Stop-Job -Id $($job.Id)" -ForegroundColor Yellow
    } else {
        $env:PYTHONUNBUFFERED = "1"
        Write-Host "AIDA server ishga tushmoqda (port: $Port)..." -ForegroundColor Cyan
        & $Python $ManagePy runserver "0.0.0.0:$Port" --noreload
    }
}

function Stop-Server {
    if (Test-Path $PidFile) {
        $pid = (Get-Content $PidFile -Raw).Trim()
        $job = Get-Job -Id $pid -ErrorAction SilentlyContinue
        if ($job) { Stop-Job -Id $pid; Remove-Job -Id $pid }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
    Get-Job -Name "AIDA-Server" -ErrorAction SilentlyContinue | Stop-Job | Remove-Job
    Write-Host "AIDA server to'xtatildi" -ForegroundColor Yellow
}

function Install-Service {
    $TaskName = "AIDA-Server"
    $TaskPath = "\AIDA\"
    $ScriptPath = Join-Path $ProjectRoot "start_aida.ps1"
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$ScriptPath`" -Scheduled -Background"
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    try {
        $existing = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
        if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false }
    } catch {}
    Register-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
    Start-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName
    Write-Host "AIDA Service o'rnatildi! Har safar Windows ochilganda avtomatik ishga tushadi" -ForegroundColor Green
}

function Remove-Service {
    try {
        Unregister-ScheduledTask -TaskName "AIDA-Server" -TaskPath "\AIDA\" -Confirm:$false
        Write-Host "AIDA Service o'chirildi" -ForegroundColor Yellow
    } catch { Write-Host "Task topilmadi" -ForegroundColor Red }
    Stop-Server
}

function Show-Status {
    $job = Get-Job -Name "AIDA-Server" -ErrorAction SilentlyContinue
    if ($job -and $job.State -eq "Running") {
        Write-Host "AIDA server: ISHLAMOQDA (Job ID: $($job.Id))" -ForegroundColor Green
    } else {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:$Port/api/status/" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) { Write-Host "AIDA server: ISHLAMOQDA (port: $Port)" -ForegroundColor Green }
            else { Write-Host "AIDA server: XATOLIK (status: $($resp.StatusCode))" -ForegroundColor Red }
        } catch { Write-Host "AIDA server: TO'XTATILGAN" -ForegroundColor Red }
    }
    try {
        $task = Get-ScheduledTask -TaskName "AIDA-Server" -TaskPath "\AIDA\" -ErrorAction SilentlyContinue
        if ($task) { Write-Host "Service: O'RNATILGAN ($($task.State))" -ForegroundColor Cyan }
        else { Write-Host "Service: O'RNATILMAGAN" -ForegroundColor Gray }
    } catch { Write-Host "Service: O'RNATILMAGAN" -ForegroundColor Gray }
}

if ($InstallService) { Install-Service; exit }
if ($RemoveService) { Remove-Service; exit }
if ($Status) { Show-Status; exit }
if ($Stop) { Stop-Server; exit }
if ($Scheduled) {
    $env:PYTHONUNBUFFERED = "1"
    & $Python $ManagePy runserver "0.0.0.0:$Port" --noreload
    exit
}

Write-Host ""
Write-Host "===== AIDA Server boshqaruvi =====" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ishga tushirish:" -ForegroundColor White
Write-Host "  .\start_aida.ps1                  # olding planda" -ForegroundColor Gray
Write-Host "  .\start_aida.ps1 -Background      # background job" -ForegroundColor Gray
Write-Host "  .\start_aida.ps1 -Port 8081       # boshqa port" -ForegroundColor Gray
Write-Host ""
Write-Host "Xizmat (service):" -ForegroundColor White
Write-Host "  .\start_aida.ps1 -InstallService  # auto-start o'rnatish" -ForegroundColor Gray
Write-Host "  .\start_aida.ps1 -RemoveService   # auto-start o'chirish" -ForegroundColor Gray
Write-Host "  .\start_aida.ps1 -Status          # holatni ko'rish" -ForegroundColor Gray
Write-Host "  .\start_aida.ps1 -Stop            # to'xtatish" -ForegroundColor Gray
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Start-Server -Bg:$Background
