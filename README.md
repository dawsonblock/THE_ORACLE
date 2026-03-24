# 🔮 THE ORACLE

> **AI-Powered Code Modification with Validation & Retry Loop**

[![Status](https://img.shields.io/badge/status-operational%20scaffold-brightgreen)](./docs/build_status.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

A supervised coding scaffold that plans, executes, and validates code modifications through an iterative feedback loop.

**Status**: Operational supervised coding scaffold (169 tests passing, zero warnings) - VERIFIED

---

## ✨ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🧠 **Planner Loop** | ✅ Operational | Task → Context → Plan → Apply → Validate → Retry |
| 🔧 **Patch Executor** | ✅ Operational | Multi-file string replacement with safety guards |
| ✅ **Validation Gate** | ✅ Operational | Syntax check + pytest execution |
| 🔄 **Failure Analysis** | ✅ Operational | Automatic retry with corrected plans |
| 📊 **Runtime Artifacts** | ✅ Operational | JSON persistence for every run |
| 🚀 **Local Server** | ✅ Operational | FastAPI with health checks |
| 🧪 **Test Suite** | ✅ 169 Passed | Unit, E2E, and integration tests (zero warnings) |
| 🔐 **Approval Flow** | ✅ Operational | Approve/reject with receipts |
| 🌐 **Portable Startup** | ✅ Works on any system with Python 3.11+ |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (any installation: `python3`, `python3.11`, or custom path)
- Git

### 1. Bootstrap

```bash
git clone https://github.com/dawsonblock/THE_ORACLE.git
cd THE_ORACLE
bash scripts/bootstrap_all.sh
```

The bootstrap installs the package in editable mode (`pip install -e .`) to ensure imports work correctly.

**Using a specific Python interpreter:**
```bash
PYTHON_BIN=/usr/local/bin/python3.11 bash scripts/bootstrap_all.sh
```

Output:
```
Python 3.11.x OK
[1/5] Create virtual environment
[2/5] Upgrade pip
[3/5] Install packages
[4/5] Verify runtime imports
Import checks passed
PIPELINE IMPORT OK
[5/5] Bootstrap complete
BOOTSTRAP OK
```

### 2. Start Services

```bash
bash scripts/run_local.sh
```

Output:
```
[preflight] Checking runtime...
[START] run_server
[WAIT] run_server health: http://127.0.0.1:8000/health
[OK] run_server
RUN_LOCAL_OK
```

### 3. Verify Health

```bash
curl http://localhost:8000/health
# {"status": "ok"}

curl http://localhost:8000/ready
# {"status": "ready"}
```

### 4. Run a Task

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "fix first_token", "repo_path": "/path/to/repo"}'
```

Response:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "task": "fix first_token",
  "repo_path": "/path/to/repo",
  "status": "awaiting_approval",
  "attempts": 1,
  "files_changed": ["parser.py"],
  "timestamp": "2026-03-24T00:00:00+00:00"
}
```

### 5. Approve the Run

```bash
curl -X POST http://localhost:8000/runs/{run_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"actor": "operator", "note": "LGTM"}'
```

Response:
```json
{
  "run": {
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "applied",
    "approved_by": "operator",
    "approved_at": "2026-03-24T00:00:01+00:00"
  },
  "receipt": {
    "decision": "approved",
    "actor": "operator",
    "note": "LGTM",
    "timestamp": "2026-03-24T00:00:01+00:00"
  }
}
```

### 6. Stop Services

```bash
bash scripts/stop_all.sh
```

---

## ✅ What's Proven

### Core Pipeline
- ✅ **Python 3.11+ control plane** - Works with any Python 3.11+ installation
- ✅ **Portable startup** - `PYTHON_BIN` environment variable support
- ✅ **Local bootstrap and service management** - One-command setup
- ✅ **Planner loop with validation and retry** - End-to-end pipeline

### Control Plane
- ✅ **Runtime artifact persistence** - Every run saved to `runtime/runs/`
- ✅ **Approval/promotion flow with receipts** - Full state machine (`awaiting_approval` → `applied`/`rejected`)
- ✅ **No-diff protection** - No approval without actual file changes
- ✅ **Receipt artifacts** - Written to `runtime/receipts/` with full audit trail

### Test Coverage
- ✅ **169 tests passing** with `-W error` (zero warnings)
- ✅ **150 integration tests** - Core pipeline, adapters, validation
- ✅ **10 unit tests** - Context building, patch execution, planning
- ✅ **9 E2E tests** - Full pipeline, approval flow, no-diff protection

---

## 🚧 What's Not Fully Proven

- 🚧 Broad multi-file autonomy on large repos
- 🚧 Production queueing/runtime isolation
- 🚧 Swift/macOS control plane integration
- 🚧 Best-of-N planning (multiple candidates)
- 🚧 Worker services (retrieval broker, hardened worker, aider) - disabled by default

---

## 📊 Test Results

Run the full test suite:

```bash
# All 169 tests with warnings as errors
python -W error -m pytest tests/integration tests/unit \
  tests/e2e/test_full_pipeline.py \
  tests/e2e/test_approval_promotion_flow.py \
  tests/e2e/test_no_diff_no_approval.py -q
```

| Suite | Count | Status |
|-------|-------|--------|
| Unit | 10 | ✅ Pass |
| Integration | 150 | ✅ Pass |
| E2E | 9 | ✅ Pass |
| **Total** | **169** | **✅ Pass** |

See [docs/build_status.md](./docs/build_status.md) for full details.

---

## 🔒 Release Gate

Verify the build is release-ready:

```bash
bash scripts/release_gate.sh
```

This runs the full verification matrix:
1. Clean bootstrap
2. 169 tests (integration, unit, E2E)
3. Local runtime health checks
4. Clean shutdown

---

## 📁 Project Structure

```
THE_ORACLE/
├── scripts/           # Bootstrap, run, stop scripts (portable)
│   ├── bootstrap_all.sh
│   ├── run_local.sh
│   ├── stop_all.sh
│   └── release_gate.sh
├── integration/       # Core pipeline modules
│   ├── pipeline.py           # Main orchestration
│   ├── patch_executor.py     # Safe file patching
│   ├── llm_planner.py        # Plan generation
│   ├── failure_analyzer.py   # Retry logic
│   └── preflight.py          # Health checks
├── runtime/           # Artifact storage
│   ├── runs/          # Run artifacts (JSON)
│   └── receipts/      # Approval receipts (JSON)
├── tests/             # Unit, integration, E2E tests
├── configs/           # System configuration
│   └── system.yaml    # Service enable/disable flags
└── docs/              # Documentation
```

---

## 🔧 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PYTHON_BIN` | `python3` | Python interpreter to use |
| `OPENAI_API_KEY` | - | Enable API-backed planner (optional) |

---

## 📜 License

MIT License - See [LICENSE](./LICENSE) for details.
