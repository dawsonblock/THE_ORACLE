# 🔮 THE ORACLE

> **AI-Powered Code Modification with Validation & Retry Loop**

[![Status](https://img.shields.io/badge/status-operational%20scaffold-brightgreen)](./docs/build_status.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

A supervised coding scaffold that plans, executes, and validates code modifications through an iterative feedback loop.

**Status**: Operational supervised coding scaffold (169 tests passing)

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
| 🧪 **Test Suite** | ✅ 169 Passed | Unit, E2E, and integration tests |
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

### 6. Stop Services

```bash
bash scripts/stop_all.sh
```

---

## ✅ What's Proven

- ✅ **Python 3.11+ control plane** - Works with any Python 3.11+ installation
- ✅ **Portable startup** - `PYTHON_BIN` environment variable support
- ✅ **Local bootstrap and service management** - One-command setup
- ✅ **Planner loop with validation and retry** - End-to-end pipeline
- ✅ **Runtime artifact persistence** - Every run saved to `runtime/runs/`
- ✅ **Approval/promotion flow with receipts** - Full control plane
- ✅ **No-diff protection** - No approval without changes

## 🚧 What's Not Fully Proven

- 🚧 Broad multi-file autonomy on large repos
- 🚧 Production queueing/runtime isolation
- 🚧 Swift/macOS control plane integration
- 🚧 Best-of-N planning (multiple candidates)

---

## 📊 Test Results

| Suite | Count | Status |
|-------|-------|--------|
| Unit | 10 | ✅ Pass |
| Integration | 150 | ✅ Pass |
| E2E | 9 | ✅ Pass |
| **Total** | **169** | **✅ Pass** |

See [docs/build_status.md](./docs/build_status.md) for full details.

---

## 📁 Project Structure

```
THE_ORACLE/
├── scripts/           # Bootstrap, run, stop scripts (portable)
├── integration/       # Core pipeline modules
├── runtime/           # Artifact storage
├── tests/             # Unit, integration, E2E tests
├── configs/           # System configuration
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
