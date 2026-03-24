# 🔮 THE ORACLE

> **AI-Powered Code Modification with Validation & Retry Loop**

[![Status](https://img.shields.io/badge/status-supervised%20scaffold-blue)](./docs/build_status.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-unit%20%7C%20e2e%20%7C%20integration-green)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

A supervised coding scaffold that plans, executes, and validates code modifications through an iterative feedback loop.

---

## ✨ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🧠 **Planner Loop** | ✅ Ready | Task → Context → Plan → Apply → Validate → Retry |
| 🔧 **Patch Executor** | ✅ Ready | Multi-file string replacement with safety guards |
| ✅ **Validation Gate** | ✅ Ready | Syntax check + pytest execution |
| 🔄 **Failure Analysis** | ✅ Ready | Automatic retry with corrected plans |
| 📊 **Runtime Artifacts** | ✅ Ready | JSON persistence for every run |
| 🚀 **Local Server** | ✅ Ready | FastAPI with health checks |
| 🧪 **Test Suite** | ✅ Ready | Unit, E2E, and integration tests |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Git

### 1. Bootstrap

```bash
git clone https://github.com/dawsonblock/THE_ORACLE.git
cd THE_ORACLE
bash scripts/bootstrap_all.sh
```

Output:
```
[1/5] Create virtual environment
[2/5] Upgrade pip
[3/5] Install packages
[4/5] Verify runtime imports
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
[START] run_server
[WAIT] run_server health: http://127.0.0.1:8000/health
[OK] run_server
RUN_LOCAL_OK
```

### 3. Verify Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok"}
```

### 4. Run a Task

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "fix first_token so empty list returns None",
    "repo_path": "/path/to/repo"
  }'
```

Response:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "task": "fix first_token so empty list returns None",
  "repo_path": "/path/to/repo",
  "status": "applied",
  "attempts": 1,
  "reason": null,
  "files_changed": ["parser.py"],
  "timestamp": "2026-03-24T00:00:00+00:00"
}
```

### 5. Stop Services

```bash
bash scripts/stop_all.sh
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HTTP Interface                               │
│              scripts/serve_coding_runs.py:8000                       │
│                      ┌──────────────┐                                │
│                      │  /health     │                                │
│                      │  /ready      │                                │
│                      │  /run   ─────┼────┐                           │
│                      └──────────────┘    │                           │
└──────────────────────────────────────────┼───────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Single Patching Authority                         │
│                   integration/pipeline.py                            │
│                                                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│   │   Context   │───▶│    Plan     │───▶│    Apply    │             │
│   │   Builder   │    │   (LLM)     │    │   Patch     │             │
│   └─────────────┘    └─────────────┘    └──────┬──────┘             │
│                                                  │                   │
│   ┌─────────────┐    ┌─────────────┐            │                   │
│   │   Failure   │◀───│   Validate  │◀───────────┘                   │
│   │   Analyzer  │    │   (pytest)  │                                │
│   └──────┬──────┘    └─────────────┘                                │
│          │                                                          │
│          └──────────────────────────────────┐ (retry on failure)    │
│                                             │                       │
│   MAX_ATTEMPTS = 3                          │                       │
│                                             ▼                       │
│                                    ┌─────────────┐                  │
│                                    │   SUCCESS   │                  │
│                                    └──────┬──────┘                  │
│                                           │                         │
└───────────────────────────────────────────┼─────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Runtime Artifacts                               │
│                    runtime/runs/{uuid}.json                          │
│                                                                      │
│   {                                                                  │
│     "run_id": "uuid",                                               │
│     "task": "...",                                                  │
│     "status": "applied",   // or "failed"                           │
│     "attempts": 2,                                                  │
│     "files_changed": ["parser.py"]                                  │
│   }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### Core Pipeline

| Component | File | Purpose |
|-----------|------|---------|
| **Pipeline** | `integration/pipeline.py` | Orchestrates the full modification loop |
| **Context Builder** | `integration/context_builder.py` | Ranks files by task relevance |
| **LLM Planner** | `integration/llm_planner.py` | Generates edit plans (API + fallback) |
| **Patch Executor** | `integration/patch_executor.py` | Applies multi-file edits safely |
| **Validation** | `integration/validation.py` | Syntax + pytest validation |
| **Failure Analyzer** | `integration/failure_analyzer.py` | Corrects plans from test output |

### Services

| Service | Port | Endpoint | Purpose |
|---------|------|----------|---------|
| Run Server | 8000 | `/health`, `/run` | Main HTTP interface |
| Aider Worker | 8030 | `/health` | Aider integration (optional) |
| Hardened Worker | 8020 | `/health` | Hardened runtime (optional) |
| Retrieval Broker | 8010 | `/health` | Code retrieval (optional) |

---

## 🧪 Testing

### Run All Tests

```bash
# Unit tests
pytest -q tests/unit/

# E2E tests
pytest -q tests/e2e/

# Integration tests
pytest -q tests/integration/

# All tests
pytest -q
```

### Test Coverage

**Unit Tests** (`tests/unit/`):
- `test_patch_executor.py` - 5 test cases (single/multi-file, missing file, missing search, empty edits)
- `test_context_builder.py` - 2 test cases (parser preference, deterministic order)
- `test_planner_fallbacks.py` - Local fallback without API key
- `test_failure_analyzer.py` - Plan-shaped return verification
- `test_validation.py` - Return structure verification

**E2E Tests** (`tests/e2e/`):
- `test_full_pipeline.py` - End-to-end pipeline execution
- `test_approval_promotion_flow.py` - Server endpoint test
- `test_no_diff_no_approval.py` - Negative control

---

## ⚙️ Configuration

### System Config (`configs/system.yaml`)

```yaml
workers:
  aider:
    enabled: true
  hardened:
    enabled: true

retrieval:
  broker:
    enabled: true

run_server:
  enabled: true
```

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | Optional | Enables API-backed planner (fallback works without it) |

---

## 📁 Project Structure

```
THE_ORACLE/
├── 📁 scripts/
│   ├── bootstrap_all.sh       # One-command setup
│   ├── run_local.sh           # Start all services
│   ├── stop_all.sh            # Stop all services
│   └── serve_coding_runs.py   # FastAPI server
│
├── 📁 integration/
│   ├── pipeline.py            # Main orchestration
│   ├── patch_executor.py      # Safe file editing
│   ├── validation.py          # Syntax + pytest
│   ├── context_builder.py     # File ranking
│   ├── llm_planner.py         # Plan generation
│   ├── failure_analyzer.py    # Error recovery
│   └── preflight.py           # Dependency checks
│
├── 📁 tests/
│   ├── unit/                  # Unit tests
│   ├── e2e/                   # End-to-end tests
│   └── integration/           # Integration tests
│
├── 📁 runtime/
│   ├── runs/                  # Run artifacts (JSON)
│   ├── receipts/              # Approval receipts
│   ├── pids/                  # Process IDs
│   └── logs/                  # Service logs
│
├── 📁 configs/
│   └── system.yaml            # Service configuration
│
├── 📁 third_party/
│   ├── aider/                 # Aider integration
│   ├── code-agent-runtime/    # Hardened worker
│   └── cocoindex-code/        # Retrieval broker
│
└── 📁 archive/legacy_runtime/ # Old scripts (reference)
```

---

## ✅ What's Proven

- ✅ **Python control plane** - Clean modular architecture
- ✅ **Local startup path** - Bootstrap → Run → Stop in 3 commands
- ✅ **Planner loop** - Context → Plan → Apply → Validate → Retry
- ✅ **Test suite** - Unit, E2E, and integration coverage
- ✅ **Runtime artifacts** - Every run persisted to JSON
- ✅ **Service management** - PID-based process control

## 🚧 What's Not Fully Proven

- 🚧 Broad multi-file autonomy on large repos
- 🚧 Production queueing/runtime isolation
- 🚧 Swift/macOS control plane integration

See [docs/build_status.md](./docs/build_status.md) for detailed gate status.

---

## 🛠️ Development

### Adding a New Test

```python
# tests/unit/test_my_feature.py
def test_my_feature(tmp_path):
    repo = tmp_path
    (repo / "file.py").write_text("content")
    
    result = my_function(str(repo))
    
    assert result["success"] is True
```

### Running Preflight Checks

```python
python -c "from integration.preflight import check; check()"
```

### Debugging a Run

Check runtime artifacts:

```bash
ls -la runtime/runs/
cat runtime/runs/{run_id}.json
```

---

## 📜 License

MIT License - See [LICENSE](./LICENSE) for details.

---

## 🤝 Contributing

This is a **supervised coding scaffold** under active development. Contributions should focus on:

1. **Stability** - Pass all gates in `docs/build_status.md`
2. **Testability** - Every feature needs tests
3. **Clarity** - Single patching authority principle

---

<div align="center">

**[⬆ Back to Top](#-the-oracle)**

Built with 🔮 by Dawson Block

</div>
