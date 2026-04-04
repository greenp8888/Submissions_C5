param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root ".runtime"
$pidFile = Join-Path $runtimeDir "server.pid"
$outLog = Join-Path $runtimeDir "server.out.log"
$errLog = Join-Path $runtimeDir "server.err.log"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path $pidFile) {
    $existingPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if ($existingPid) {
        $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($existingProcess) {
            Write-Host "Server is already running with PID $existingPid"
            Write-Host "URL: http://$BindHost`:$Port/"
            exit 0
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

$pythonExe = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}

$arguments = @(
    "-m", "uvicorn",
    "ai_app.main:app",
    "--app-dir", "src",
    "--host", $BindHost,
    "--port", $Port
)

if ($Reload) {
    $arguments += "--reload"
}

$process = Start-Process `
    -FilePath $pythonExe `
    -ArgumentList $arguments `
    -WorkingDirectory $root `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -PassThru

Set-Content -Path $pidFile -Value $process.Id -Encoding ascii

Write-Host "Server started."
Write-Host "PID: $($process.Id)"
Write-Host "URL: http://$BindHost`:$Port/"
Write-Host "Logs: $outLog"
