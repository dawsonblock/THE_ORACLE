"""Preflight checks for all services."""

from pathlib import Path
import yaml
import os

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "system.yaml"
WORKSPACE_DIR = ROOT / "workspace"
RUNS_DIR = ROOT / "runtime" / "runs"


def load_config():
    """Load configs/system.yaml if present."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check():
    """Check all enabled services."""
    cfg = load_config()
    missing = []

    if cfg.get("workers", {}).get("aider", {}).get("enabled", False):
        try:
            import aider  # noqa: F401
        except Exception as e:
            missing.append(f"aider:{e}")

    if cfg.get("workers", {}).get("hardened", {}).get("enabled", False):
        try:
            from apps.planner_worker import PlannerWorker  # noqa: F401
        except Exception as e:
            missing.append(f"code-agent-runtime:{e}")

    if cfg.get("retrieval", {}).get("broker", {}).get("enabled", False):
        try:
            import cocoindex_code  # noqa: F401
        except Exception as e:
            missing.append(f"cocoindex-code:{e}")

    # Check workspace writability
    try:
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        test_file = WORKSPACE_DIR / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
    except Exception as e:
        missing.append(f"workspace_not_writable:{e}")

    if missing:
        raise RuntimeError("Preflight failed: " + "; ".join(missing))

    return True


def check_run_server():
    """Check run server dependencies."""
    missing = []

    # Check pipeline imports
    try:
        from integration.pipeline import run_pipeline  # noqa: F401
        from integration.patch_executor import apply_plan  # noqa: F401
        from integration.llm_planner import create_plan  # noqa: F401
        from integration.failure_analyzer import analyze_failure  # noqa: F401
    except Exception as e:
        missing.append(f"pipeline_imports:{e}")

    # Check runtime directories
    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        test_file = RUNS_DIR / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
    except Exception as e:
        missing.append(f"runs_dir_not_writable:{e}")

    if missing:
        raise RuntimeError("Run server preflight failed: " + "; ".join(missing))

    return True


def check_retrieval():
    """Check retrieval broker dependencies."""
    missing = []

    cfg = load_config()
    if not cfg.get("retrieval", {}).get("broker", {}).get("enabled", False):
        return True  # Not enabled, skip

    try:
        import cocoindex_code  # noqa: F401
    except Exception as e:
        missing.append(f"cocoindex-code:{e}")

    # Check workspace
    try:
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        test_file = WORKSPACE_DIR / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
    except Exception as e:
        missing.append(f"workspace_not_writable:{e}")

    if missing:
        raise RuntimeError("Retrieval broker preflight failed: " + "; ".join(missing))

    return True


def check_hardened_worker():
    """Check hardened worker dependencies."""
    missing = []

    cfg = load_config()
    if not cfg.get("workers", {}).get("hardened", {}).get("enabled", False):
        return True  # Not enabled, skip

    try:
        from apps.planner_worker import PlannerWorker  # noqa: F401
    except Exception as e:
        missing.append(f"code-agent-runtime:{e}")

    if missing:
        raise RuntimeError("Hardened worker preflight failed: " + "; ".join(missing))

    return True


def check_aider_worker():
    """Check aider worker dependencies."""
    missing = []

    cfg = load_config()
    if not cfg.get("workers", {}).get("aider", {}).get("enabled", False):
        return True  # Not enabled, skip

    try:
        import aider  # noqa: F401
    except Exception as e:
        missing.append(f"aider:{e}")

    if missing:
        raise RuntimeError("Aider worker preflight failed: " + "; ".join(missing))

    return True


def check_all():
    """Compatibility wrapper for legacy calls."""
    check()


if __name__ == "__main__":
    check()
