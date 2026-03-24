#!/usr/bin/env bash
set -e

echo "═══════════════════════════════════════════════════════════════════"
echo "RELEASE GATE - Full Verification Suite"
echo "═══════════════════════════════════════════════════════════════════"

# Step 0: Clean state
echo "Step 0: Clean state..."
rm -rf .venv .pytest_cache runtime/pids runtime/runs runtime/receipts
mkdir -p runtime/pids runtime/runs runtime/receipts

# Step 1: Bootstrap
echo "Step 1: Bootstrap..."
bash scripts/bootstrap_all.sh

# Step 2: Import check (via unit tests that verify imports)
echo "Step 2: Import surface..."
source .venv/bin/activate
python -c "
import aider
from apps.planner_worker import PlannerWorker
import integration.pipeline
import integration.patch_executor
import integration.llm_planner
import integration.failure_analyzer
import integration.runtime.approval_store
from scripts.serve_coding_runs import main
print('IMPORTS_OK')
"

# Step 3: Unit tests
echo "Step 3: Unit tests..."
pytest -q tests/unit/test_patch_executor.py -W error
pytest -q tests/unit/test_context_builder.py -W error
pytest -q tests/unit/test_planner_fallbacks.py -W error
pytest -q tests/unit/test_failure_analyzer.py -W error

# Step 4: Integration suite
echo "Step 4: Integration suite (150 tests)..."
pytest -q tests/integration -W error

# Step 5: Planner loop E2E
echo "Step 5: Planner loop E2E..."
pytest -q tests/e2e/test_real_bug_fix.py -W error
pytest -q tests/e2e/test_full_pipeline.py -W error

# Step 6: Approval/control-plane
echo "Step 6: Approval/control-plane..."
pytest -q tests/e2e/test_approval_promotion_flow.py -W error
pytest -q tests/e2e/test_no_diff_no_approval.py -W error
pytest -q tests/e2e/test_unified_approval_gate.py -W error

# Step 7: Server lifecycle
echo "Step 7: Server lifecycle..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1
source .venv/bin/activate
python -c "from scripts.serve_coding_runs import main; main()" > runtime/run_server.log 2>&1 &
sleep 4
curl -fsS http://localhost:8000/health > /dev/null
curl -fsS http://localhost:8000/ready > /dev/null
bash scripts/stop_all.sh

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "RELEASE GATE PASSED - ALL CHECKS SUCCEEDED"
echo "══════════════════════════════════════════════════════════════════="
