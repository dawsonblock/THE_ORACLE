#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

echo "[1/5] Create virtual environment"
python3 -m venv .venv
source .venv/bin/activate

echo "[2/5] Upgrade pip"
python -m pip install --upgrade pip

echo "[3/5] Install packages"
pip install -r requirements.txt
pip install -e third_party/aider
pip install -e third_party/code-agent-runtime
pip install -e third_party/cocoindex-code

echo "[4/5] Verify runtime imports"
python - <<'PY'
from integration.pipeline import run_pipeline
from integration.patch_executor import apply_plan
from integration.llm_planner import create_plan
from integration.failure_analyzer import analyze_failure
from scripts.serve_coding_runs import main
import redis
import rq
print("Import checks passed")
print("PIPELINE IMPORT OK")
PY

echo "[5/5] Bootstrap complete"
echo "BOOTSTRAP OK"
