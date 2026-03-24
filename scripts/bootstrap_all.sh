#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# Portable Python interpreter resolution
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: Python not found: $PYTHON_BIN"
  echo "Set PYTHON_BIN to specify the Python interpreter path"
  exit 1
fi

# Validate Python version (3.11+)
"$PYTHON_BIN" - <<'EOF'
import sys
if sys.version_info < (3, 11):
    print(f"Error: Python 3.11+ required, found {sys.version}")
    sys.exit(1)
print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} OK")
EOF

echo "[1/5] Create virtual environment"
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate

echo "[2/5] Upgrade pip"
python -m pip install --upgrade pip

echo "[3/5] Install packages"
pip install -r requirements.txt

echo "[4/5] Verify runtime imports"
python - <<'PY'
from integration.pipeline import run_pipeline
from integration.patch_executor import apply_plan
from integration.llm_planner import create_plan
from integration.failure_analyzer import analyze_failure
from scripts.serve_coding_runs import main
from integration.runtime.approval_store import load_run, save_run
import redis
import rq
print("Import checks passed")
print("PIPELINE IMPORT OK")
PY

echo "[5/5] Bootstrap complete"
echo "BOOTSTRAP OK"
