param(
    [string]$TaskName = "AI Daily Brief",
    [string]$Time = "08:00"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Runner = Join-Path $ProjectRoot "scripts\run_daily_brief.ps1"
$Action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$Runner`""
schtasks.exe /Create /TN $TaskName /SC DAILY /ST $Time /TR $Action /F
Write-Host "Registered '$TaskName' at $Time"
