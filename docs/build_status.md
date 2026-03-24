# Build Status

## Current State

**Status**: Operational supervised coding scaffold with portable startup

All acceptance gates now pass on any system with Python 3.11+.

## Acceptance Gates

### Gate 1 — Bootstrap Truth ✅

```bash
rm -rf .venv
bash scripts/bootstrap_all.sh
```

**Result**: Bootstrap completes successfully with portable Python detection.

**Portable**: Works with `python3`, `python3.11`, or `PYTHON_BIN=/custom/path`.

### Gate 2 — Packaging Truth ✅

```bash
pytest -q tests/integration
```

**Result**: 150 passed

### Gate 3 — Planner Truth ✅

```bash
pytest -q tests/e2e/test_full_pipeline.py
```

**Result**: 1 passed - Pipeline executes planner loop correctly

### Gate 4 — Control-Plane Truth ✅

```bash
pytest -q tests/e2e/test_approval_promotion_flow.py
pytest -q tests/e2e/test_no_diff_no_approval.py
```

**Result**: 8 passed - Approval/promotion flow proven

### Gate 5 — Local Runtime Truth ✅

```bash
bash scripts/run_local.sh
curl http://localhost:8000/health
curl http://localhost:8000/ready
bash scripts/stop_all.sh
```

**Result**: All endpoints respond correctly

## Test Summary

| Test Suite | Count | Status |
|------------|-------|--------|
| Unit Tests | 10 | ✅ All pass |
| Integration Tests | 150 | ✅ All pass |
| E2E Tests | 9 | ✅ All pass |
| **Total** | **169** | **✅ All pass** |

## What's Proven

- ✅ **Portable Python 3.11+ startup** - Works with any Python installation via `PYTHON_BIN`
- ✅ **Local bootstrap and service management** - One-command setup
- ✅ **Planner loop**: task → context → plan → apply → validate → retry
- ✅ **Runtime artifact persistence** (runtime/runs/)
- ✅ **Approval/promotion flow with receipts**
- ✅ **No-diff protection** (no approval without changes)
- ✅ **Multi-service architecture** (run server, optional workers)

## What's Not Fully Proven

- 🚧 Broad multi-file autonomy on large repos
- 🚧 Production queueing/runtime isolation
- 🚧 Swift/macOS control plane integration
- 🚧 Best-of-N planning (generate multiple candidates)

## Known Limitations

1. **Planner Quality**: Local fallback handles bundled fixtures. API mode requires `OPENAI_API_KEY`.
2. **Worker Services**: Aider and hardened workers install but may have additional dependencies.
3. **Benchmarks**: No formal benchmark suite yet.

## Recent Changes

### Latest: All P0 Operational Gaps Closed

**1. Import Consistency (Fixed)**
- `runtime.approval_store` now imports correctly under pytest
- Requires editable install: `pip install -e .` (handled by bootstrap)
- All 169 tests pass with `-W error` (zero warnings)

**2. Control Plane Proof (Verified)**
- Approval e2e tests assert real state transitions: `awaiting_approval` → `applied`
- Receipt artifacts verified with correct fields
- No-diff blocking verified
- Tests: `test_approval_promotion_flow.py` (4 tests), `test_no_diff_no_approval.py` (4 tests)

**3. Local Runtime Hardening (Fixed)**
- `run_local.sh` now uses `-c` import pattern for reliable startup
- Works twice in a row without manual cleanup
- Health and ready checks pass consistently

### Previous: Portable Startup (Phase 1 Complete)
- Replaced hardcoded `python3.11` with `PYTHON_BIN` environment variable
- Added Python 3.11+ version validation
- Bootstrap and run scripts now work on any system with Python 3.11+

### Previous: Full Operational State
- Fixed preflight service-specific checks
- Aligned packaging (requirements.txt, pyproject.toml, bootstrap)
- Achieved 150/150 integration tests
- Added real approval/promotion E2E tests
- Updated documentation to match proof

## Next Steps (Future Phases)

See full upgrade plan for:
- Best-of-2/3 planning
- Attempt history preservation
- Benchmark fixture set
- Docker packaging
- Queue/parallel execution
