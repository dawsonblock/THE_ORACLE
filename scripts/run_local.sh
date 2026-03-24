#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

PID_DIR="$ROOT/runtime/pids"
mkdir -p "$PID_DIR"

source "$ROOT/.venv/bin/activate"

python -c "from integration.preflight import check; check()"

start_service() {
  local name="$1"
  local cmd="$2"
  local health_url="${3:-}"

  echo "[START] $name"
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
  python - <<EOF
import yaml
cfg = yaml.safe_load(open("configs/system.yaml"))
cur = cfg
for part in "$path".split("."):
    cur = cur[part]
print("true" if cur else "false")
EOF
}

mkdir -p runtime/runs runtime/receipts runtime/logs

if [[ "$(is_enabled run_server.enabled)" == "true" ]]; then
  start_service "run_server" "oracle-run-server" "http://127.0.0.1:8000/health"
fi

if [[ "$(is_enabled retrieval.broker.enabled)" == "true" ]]; then
  start_service "retrieval_broker" "python -m integration.retrieval_broker.service" "http://127.0.0.1:8010/health"
fi

if [[ "$(is_enabled workers.hardened.enabled)" == "true" ]]; then
  start_service "worker_hardened" "python -m integration.worker_hardened.service" "http://127.0.0.1:8020/health"
fi

if [[ "$(is_enabled workers.aider.enabled)" == "true" ]]; then
  start_service "worker_aider" "python -m integration.worker_aider.service" "http://127.0.0.1:8030/health"
fi

echo "RUN_LOCAL_OK"
wait
