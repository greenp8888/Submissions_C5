#!/bin/bash

set -e

# -------- Paths --------
ROOT="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT/.runtime"
PID_FILE="$RUNTIME_DIR/server.pid"

# -------- Check PID file --------
if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found. Server may already be stopped."
  exit 0
fi

PID_VALUE=$(head -n 1 "$PID_FILE" | tr -d '[:space:]')

if [ -z "$PID_VALUE" ]; then
  rm -f "$PID_FILE"
  echo "PID file was empty and has been removed."
  exit 0
fi

# -------- Check process --------
if ps -p "$PID_VALUE" > /dev/null 2>&1; then
  kill -9 "$PID_VALUE"
  echo "Stopped server process $PID_VALUE."
else
  echo "Process $PID_VALUE was not running. Removing stale PID file."
fi

# -------- Cleanup --------
rm -f "$PID_FILE"