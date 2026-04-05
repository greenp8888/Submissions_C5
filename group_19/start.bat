@echo off
:: FinanceIQ — Windows startup script
:: Usage: Double-click start.bat or run from command prompt

setlocal
cd /d "%~dp0"

echo.
echo   FinanceIQ — AI Financial Coach
echo   ================================
echo.

:: ── 1. Python virtual environment ──────────────────────────────────────────
if not exist ".venv" (
  echo   [1/4] Creating Python virtual environment...
  python -m venv .venv
) else (
  echo   [1/4] Virtual environment found.
)

call .venv\Scripts\activate.bat

echo   [2/4] Installing Python dependencies...
pip install -r requirements.txt -q

:: ── 2. Node.js dependencies ────────────────────────────────────────────────
echo   [3/4] Installing Node dependencies...
cd server && npm install --silent && cd ..
cd client && npm install --silent && cd ..

echo   [4/4] All dependencies installed.
echo.

:: ── 3. Start servers in separate windows ───────────────────────────────────
echo   Starting servers...
start "FinanceIQ API Server" cmd /k "cd /d %~dp0server && node server.js"
start "FinanceIQ React Client" cmd /k "cd /d %~dp0client && npm run dev"

echo.
echo   Two windows opened:
echo     API Server  ^>  http://localhost:3001
echo     React App   ^>  http://localhost:5173
echo.
echo   Open http://localhost:5173 in your browser.
echo.
pause
