# Oracle System

Status: **Supervised coding scaffold**

A Python-based control plane for automated code modification with planner loop, validation gates, and runtime artifact persistence.

## What is Proven

- **Python control plane** - Modular integration layer with clear separation of concerns
- **Local startup path** - Single-command bootstrap and service management (`run_local.sh` / `stop_all.sh`)
- **Planner loop on bundled fixtures** - Task → Context → Plan → Apply → Validate → Retry cycle
- **Integration suite** - Unit and E2E tests covering patch execution, context building, and pipeline flow

## What is Not Fully Proven

- Broad multi-file autonomy on large repos
- Production queueing/runtime isolation
- Swift/macOS control plane as part of the trusted runtime

## Quick Start

```bash
# Bootstrap (creates .venv, installs packages, verifies imports)
bash scripts/bootstrap_all.sh

# Start services
bash scripts/run_local.sh

# Verify health
curl http://localhost:8000/health

# Stop services
bash scripts/stop_all.sh
```

## Running Tests

```bash
# Unit tests
pytest -q tests/unit/

# E2E tests
pytest -q tests/e2e/

# Integration tests
pytest -q tests/integration/
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    scripts/serve_coding_runs.py              │
│                         (FastAPI server)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                   integration/pipeline.py                    │
│              (Single patching authority)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Context │→ │  Plan    │→ │  Apply   │→ │  Validate  │  │
│  │  Builder │  │  (LLM)   │  │  Patch   │  │  (pytest)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                     ↓                        │
│                              ┌────────────┐                 │
│                              │   Retry    │                 │
│                              │  (analyze) │                 │
│                              └────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    runtime/runs/{uuid}.json                  │
│                 (Artifact persistence)                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

| Component | Purpose |
|-----------|---------|
| `integration/pipeline.py` | Single execution authority for code modification |
| `integration/patch_executor.py` | Applies multi-file edit plans safely |
| `integration/validation.py` | Syntax checking and pytest execution |
| `integration/context_builder.py` | Ranks relevant files by task tokens |
| `integration/llm_planner.py` | API + local fallback for plan generation |
| `integration/failure_analyzer.py` | Produces corrected plans from test failures |
| `scripts/serve_coding_runs.py` | HTTP server with `/health` and `/run` endpoints |

## Configuration

`configs/system.yaml` controls enabled services:

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

## Build Status

See [docs/build_status.md](docs/build_status.md) for current gate status.

## License

See LICENSE file for details.
