#!/usr/bin/env bash
# FinanceIQ — macOS / Linux startup script
# Usage: ./start.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo ""
echo "  FinanceIQ — AI Financial Coach"
echo "  ================================"
echo ""

# ── 1. Python virtual environment ──────────────────────────────────────────────
if [ ! -d ".venv" ]; then
  echo "  [1/4] Creating Python virtual environment..."
  python3 -m venv .venv
else
  echo "  [1/4] Virtual environment found."
fi

source .venv/bin/activate

echo "  [2/4] Installing Python dependencies..."
pip install -r requirements.txt -q

# ── 2. Node.js dependencies ───────────────────────────────────────────────────
echo "  [3/4] Installing Node dependencies..."
cd "$ROOT/server" && npm install --silent
cd "$ROOT/client" && npm install --silent
cd "$ROOT"

echo "  [4/4] All dependencies installed."
echo ""

# ── 3. Start servers in separate Terminal tabs (macOS) or background ─────────
if [[ "$OSTYPE" == "darwin"* ]]; then
  # Open two new Terminal tabs on macOS
  osascript <<EOF
tell application "Terminal"
  activate
  do script "cd '$ROOT/server' && node server.js"
  tell application "System Events" to keystroke "t" using command down
  do script "cd '$ROOT/client' && npm run dev" in front window
end tell
EOF
  echo "  Started in two Terminal tabs."
else
  # Linux: launch in background, print URLs
  cd "$ROOT/server" && node server.js &
  SERVER_PID=$!
  cd "$ROOT/client" && npm run dev &
  CLIENT_PID=$!
  echo "  Server PID: $SERVER_PID  (http://localhost:3001)"
  echo "  Client PID: $CLIENT_PID  (http://localhost:5173)"
  echo ""
  echo "  Press Ctrl+C to stop both servers."
  trap "kill $SERVER_PID $CLIENT_PID 2>/dev/null" INT TERM
  wait
fi

echo ""
echo "  App running at: http://localhost:5173"
echo ""
