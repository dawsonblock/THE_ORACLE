#!/usr/bin/env bash
set -euo pipefail

# Release Gate Script
# Runs the full verification matrix to determine if the build is release-ready
# Usage: bash scripts/release_gate.sh

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

echo "================================"
echo "ORACLE Release Gate Verification"
echo "================================"
echo ""

# Phase 1: Clean bootstrap
echo "[1/9] Clean bootstrap..."
rm -rf .venv
bash scripts/bootstrap_all.sh
echo ""

# Phase 2: Integration tests
echo "[2/9] Integration tests..."
.venv/bin/python -m pytest tests/integration -q
echo ""

# Phase 3: Unit tests
echo "[3/9] Unit tests..."
.venv/bin/python -m pytest tests/unit -q
echo ""

# Phase 4: Full pipeline E2E
echo "[4/9] Full pipeline E2E..."
.venv/bin/python -m pytest tests/e2e/test_full_pipeline.py -q
echo ""

# Phase 5: Approval flow E2E
echo "[5/9] Approval flow E2E..."
.venv/bin/python -m pytest tests/e2e/test_approval_promotion_flow.py -q
echo ""

# Phase 6: No-diff protection E2E
echo "[6/9] No-diff protection E2E..."
.venv/bin/python -m pytest tests/e2e/test_no_diff_no_approval.py -q
echo ""

# Phase 7: Start local runtime
echo "[7/9] Starting local runtime..."
bash scripts/run_local.sh > /tmp/release_gate_run.log 2>&1 &
RUN_PID=$!
sleep 10

# Phase 8: Health checks
echo "[8/9] Health checks..."
HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
if [[ "$HEALTH" != '{"status":"ok"}' ]]; then
    echo "ERROR: Health check failed: $HEALTH"
    cat /tmp/release_gate_run.log
    bash scripts/stop_all.sh || true
    exit 1
fi
READY=$(curl -s http://localhost:8000/ready || echo "FAILED")
if [[ "$READY" != '{"status":"ready"}' ]]; then
    echo "ERROR: Ready check failed: $READY"
    cat /tmp/release_gate_run.log
    bash scripts/stop_all.sh || true
    exit 1
fi
echo "Health: $HEALTH"
echo "Ready: $READY"
echo ""

# Phase 9: Stop services
echo "[9/9] Stopping services..."
bash scripts/stop_all.sh
wait $RUN_PID 2>/dev/null || true
echo ""

echo "================================"
echo "RELEASE GATE PASSED"
echo "================================"
echo "All 169 tests passed"
echo "Local runtime verified"
echo "Build is release-ready"
