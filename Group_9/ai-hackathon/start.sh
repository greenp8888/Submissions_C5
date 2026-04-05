#!/bin/bash

set -e

# -------- Parameters (with defaults) --------
BIND_HOST="127.0.0.1"
PORT=8000
RELOAD=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --host=*)
      BIND_HOST="${arg#*=}"
      ;;
    --port=*)
      PORT="${arg#*=}"
      ;;
    --reload)
      RELOAD=true
      ;;
  esac
done

# -------- Paths --------
ROOT="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT/.runtime"
PID_FILE="$RUNTIME_DIR/server.pid"
OUT_LOG="$RUNTIME_DIR/server.out.log"
ERR_LOG="$RUNTIME_DIR/server.err.log"

mkdir -p "$RUNTIME_DIR"

# -------- Check existing process --------
if [ -f "$PID_FILE" ]; then
  EXISTING_PID=$(head -n 1 "$PID_FILE" | tr -d '[:space:]')

  if [ -n "$EXISTING_PID" ] && ps -p "$EXISTING_PID" > /dev/null 2>&1; then
    echo "Server is already running with PID $EXISTING_PID"
    echo "URL: http://$BIND_HOST:$PORT/"
    exit 0
  fi

  rm -f "$PID_FILE"
fi

# -------- Function: Check Python module --------
test_python_module() {
  local python_path="$1"
  local module_name="$2"

  if [ ! -f "$python_path" ]; then
    return 1
  fi

  "$python_path" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$module_name') else 1)" >/dev/null 2>&1
  return $?
}

# -------- Python Detection --------
VENV_PYTHON="$ROOT/.venv/bin/python"
SYSTEM_PYTHON="$(which python3 || which python)"

if test_python_module "$VENV_PYTHON" "uvicorn"; then
  PYTHON_EXE="$VENV_PYTHON"
elif test_python_module "$SYSTEM_PYTHON" "uvicorn"; then
  PYTHON_EXE="$SYSTEM_PYTHON"
  echo "Virtual environment Python missing 'uvicorn'. Using system Python: $PYTHON_EXE"
else
  echo "ERROR: Could not find Python with 'uvicorn'. Run 'pip install -e .' first."
  exit 1
fi

# -------- Build arguments --------
ARGS=(
  -m uvicorn
  ai_app.main:app
  --app-dir src
  --host "$BIND_HOST"
  --port "$PORT"
)

if [ "$RELOAD" = true ]; then
  ARGS+=(--reload)
fi

# -------- Start server --------
cd "$ROOT"

"$PYTHON_EXE" "${ARGS[@]}" >"$OUT_LOG" 2>"$ERR_LOG" &
PROCESS_ID=$!

echo "$PROCESS_ID" > "$PID_FILE"

# -------- Wait for startup --------
sleep 2

if ! ps -p "$PROCESS_ID" > /dev/null 2>&1; then
  ERROR_OUTPUT=""
  if [ -f "$ERR_LOG" ]; then
    ERROR_OUTPUT=$(cat "$ERR_LOG")
  fi

  rm -f "$PID_FILE"
  echo -e "Server process exited during startup.\n$ERROR_OUTPUT"
  exit 1
fi

# -------- Health check --------
HEALTH_READY=false

for i in {1..10}; do
  sleep 1

  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$BIND_HOST:$PORT/health" || true)

  if [ "$STATUS" = "200" ]; then
    HEALTH_READY=true
    break
  fi
done

# -------- Output --------
echo "Server started."
echo "PID: $PROCESS_ID"
echo "URL: http://$BIND_HOST:$PORT/"
echo "Logs: $OUT_LOG"

if [ "$HEALTH_READY" = true ]; then
  echo "Health check passed. UI is ready."
else
  echo "Server running, but health endpoint not ready yet."
fi