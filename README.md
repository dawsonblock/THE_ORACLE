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

---

## 🚀 Quick Start

```bash
# 1. Bootstrap
bash scripts/bootstrap_all.sh

# 2. Start services
bash scripts/run_local.sh

# 3. Verify health
curl http://localhost:8000/health

# 4. Run a task
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "fix first_token", "repo_path": "/path/to/repo"}'

# 5. Stop services
bash scripts/stop_all.sh
```

---

## ✅ What's Proven

- Python 3.11 control plane
- Local bootstrap and service management
- Planner loop with validation and retry
- Runtime artifact persistence
- Approval/promotion flow with receipts
- No-diff protection

## 🚧 What's Not Fully Proven

- Broad multi-file autonomy on large repos
- Production queueing/runtime isolation
- Swift/macOS control plane integration
- Best-of-N planning (multiple candidates)

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
├── scripts/           # Bootstrap, run, stop scripts
├── integration/       # Core pipeline modules
├── runtime/           # Artifact storage
├── tests/             # Unit, integration, E2E tests
├── configs/           # System configuration
└── docs/              # Documentation
```

---

## 📜 License

MIT License - See [LICENSE](./LICENSE) for details.
