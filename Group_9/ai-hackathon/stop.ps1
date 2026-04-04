$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root ".runtime"
$pidFile = Join-Path $runtimeDir "server.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "No PID file found. Server may already be stopped."
    exit 0
}

$pidValue = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
if (-not $pidValue) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "PID file was empty and has been removed."
    exit 0
}

$process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $pidValue -Force
    Write-Host "Stopped server process $pidValue."
} else {
    Write-Host "Process $pidValue was not running. Removing stale PID file."
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue

