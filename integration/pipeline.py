from __future__ import annotations
from pathlib import Path
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from integration.context_builder import build_context
from integration.llm_planner import create_plan
from integration.failure_analyzer import analyze_failure
from integration.patch_executor import apply_plan
from integration.validation import run_tests

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runtime" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

MAX_ATTEMPTS = 3

def _write_run_artifact(payload: Dict[str, Any]) -> None:
    run_id = payload["run_id"]
    (RUNS_DIR / f"{run_id}.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

def run_pipeline(task: str, repo: str) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    context = build_context(repo, task)
    previous_plan: Optional[Dict[str, Any]] = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        plan = create_plan(task, context) if previous_plan is None else analyze_failure(task, previous_plan.get("_failure_output", ""), context, previous_plan)

        if not plan:
            previous_plan = {"_failure_output": "planner_returned_none"}
            continue

        apply_result = apply_plan(plan, repo)
        if not apply_result["success"]:
            previous_plan = {**plan, "_failure_output": apply_result["reason"]}
            continue

        ok, output, meta = run_tests(repo)
        if ok:
            result = {
                "run_id": run_id,
                "task": task,
                "repo_path": repo,
                "status": "applied",
                "attempts": attempt,
                "reason": None,
                "files_changed": apply_result["files"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            _write_run_artifact(result)
            return result

        previous_plan = {**plan, "_failure_output": output}

    result = {
        "run_id": run_id,
        "task": task,
        "repo_path": repo,
        "status": "failed",
        "attempts": MAX_ATTEMPTS,
        "reason": "tests_failed",
        "files_changed": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _write_run_artifact(result)
    return result
