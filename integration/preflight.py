from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "system.yaml"
WORKSPACE_DIR = ROOT / "workspace"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def check():
    cfg = load_config()
    missing = []

    if cfg["workers"]["aider"]["enabled"]:
        try:
            import aider  # noqa: F401
        except Exception as e:
            missing.append(f"aider:{e}")

    if cfg["workers"]["hardened"]["enabled"]:
        try:
            from apps.planner_worker import PlannerWorker  # noqa: F401
        except Exception as e:
            missing.append(f"code-agent-runtime:{e}")

    if cfg["retrieval"]["broker"]["enabled"]:
        try:
            import cocoindex_code  # noqa: F401
        except Exception as e:
            missing.append(f"cocoindex-code:{e}")

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
