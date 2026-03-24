#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# Use venv Python explicitly
VENV_PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Error: Virtual environment not found at .venv"
  echo "Run: bash scripts/bootstrap_all.sh"
  exit 1
fi

PID_DIR="$ROOT/runtime/pids"
mkdir -p "$PID_DIR"

echo "[preflight] Checking runtime..."
"$VENV_PYTHON" -c "from integration.preflight import check; check()"

start_service() {
  local name="$1"
  local cmd="$2"
  local health_url="${3:-}"

  echo "[START] $name"
  # Run service - imports work via editable install (pip install -e .)
  bash -lc "$cmd" > "$ROOT/runtime/${name}.log" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_DIR/${name}.pid"

  if [[ -n "$health_url" ]]; then
    echo "[WAIT] $name health: $health_url"
    for _ in $(seq 1 40); do
      if curl -fsS "$health_url" >/dev/null 2>&1; then
        echo "[OK] $name"
        return 0
      fi
      sleep 0.5
    done
    echo "[FAIL] $name health check failed"
    exit 1
  fi
}

is_enabled() {
  local path="$1"
  "$VENV_PYTHON" - <<EOF
import yaml
cfg = yaml.safe_load(open("configs/system.yaml"))
cur = cfg
for part in "$path".split("."):
    cur = cur[part]
print("true" if cur else "false")
EOF
}

mkdir -p integration/runtime/runs integration/runtime/receipts runtime/logs runtime/pids

if [[ "$(is_enabled run_server.enabled)" == "true" ]]; then
  # Use -c to ensure proper import path handling
  start_service "run_server" "$VENV_PYTHON -c 'from scripts.serve_coding_runs import main; main()'" "http://127.0.0.1:8000/health"
fi

if [[ "$(is_enabled retrieval.broker.enabled)" == "true" ]]; then
  start_service "retrieval_broker" "$VENV_PYTHON -c 'from integration.retrieval_broker.service import main; main()'" "http://127.0.0.1:8010/health"
fi

if [[ "$(is_enabled workers.hardened.enabled)" == "true" ]]; then
  start_service "worker_hardened" "$VENV_PYTHON -c 'from integration.worker_hardened.service import main; main()'" "http://127.0.0.1:8020/health"
fi

if [[ "$(is_enabled workers.aider.enabled)" == "true" ]]; then
  start_service "worker_aider" "$VENV_PYTHON -c 'from integration.worker_aider.service import main; main()'" "http://127.0.0.1:8030/health"
fi

echo "RUN_LOCAL_OK"
wait
