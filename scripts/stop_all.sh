#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PID_DIR="$ROOT/runtime/pids"

if [[ ! -d "$PID_DIR" ]]; then
  echo "No PID directory found"
  exit 0
fi

for pidfile in "$PID_DIR"/*.pid; do
  [[ -e "$pidfile" ]] || continue
  pid=$(cat "$pidfile" || true)
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "Stopped $(basename "$pidfile" .pid) ($pid)"
  fi
  rm -f "$pidfile"
done

echo "STOP_ALL_OK"
