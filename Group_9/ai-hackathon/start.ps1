param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload,
    [switch]$BuildFrontend
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root ".runtime"
$pidFile = Join-Path $runtimeDir "server.pid"
$outLog = Join-Path $runtimeDir "server.out.log"
$errLog = Join-Path $runtimeDir "server.err.log"
$frontendDir = Join-Path $root "frontend"
$frontendDist = Join-Path $frontendDir "dist\index.html"

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

function Test-PythonModule {
    param(
        [string]$PythonPath,
        [string]$ModuleName
    )

    if (-not (Test-Path $PythonPath)) {
        return $false
    }

    & $PythonPath -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)" *> $null
    return $LASTEXITCODE -eq 0
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$systemPython = (Get-Command python -ErrorAction Stop).Source

if (Test-PythonModule -PythonPath $venvPython -ModuleName "uvicorn") {
    $pythonExe = $venvPython
} elseif (Test-PythonModule -PythonPath $systemPython -ModuleName "uvicorn") {
    $pythonExe = $systemPython
    Write-Host "Virtual environment Python is missing 'uvicorn'. Falling back to system Python: $pythonExe"
} else {
    throw "Could not find a Python interpreter with 'uvicorn' installed. Run 'pip install -e .' in the app root first."
}

if ((Test-Path $frontendDir) -and ($BuildFrontend -or -not (Test-Path $frontendDist))) {
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCommand) {
        throw "Node.js/npm is required to build the React frontend. Install Node.js or build the frontend manually in '$frontendDir'."
    }

    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Host "Installing frontend dependencies..."
        Push-Location $frontendDir
        try {
            & $npmCommand.Source install
            if ($LASTEXITCODE -ne 0) {
                throw "npm install failed for the frontend."
            }
        } finally {
            Pop-Location
        }
    }

    Write-Host "Building React frontend..."
    Push-Location $frontendDir
    try {
        & $npmCommand.Source run build
        if ($LASTEXITCODE -ne 0) {
            throw "npm run build failed for the frontend."
        }
    } finally {
        Pop-Location
    }
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

Start-Sleep -Seconds 2
$startedProcess = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
if (-not $startedProcess) {
    $errorOutput = ""
    if (Test-Path $errLog) {
        $errorOutput = Get-Content -Raw $errLog
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    throw "Server process exited during startup.`n$errorOutput"
}

$healthReady = $false
for ($attempt = 0; $attempt -lt 10; $attempt++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://$BindHost`:$Port/health" -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            $healthReady = $true
            break
        }
    } catch {
    }
}

Write-Host "Server started."
Write-Host "PID: $($process.Id)"
Write-Host "URL: http://$BindHost`:$Port/"
Write-Host "Logs: $outLog"
if ($healthReady) {
    Write-Host "Health check passed. UI is ready."
} else {
    Write-Host "Server process is running, but the health endpoint is not ready yet. Wait a few more seconds and refresh."
}
