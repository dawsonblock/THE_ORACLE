"""Simple approval and receipt storage."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runtime" / "runs"
RECEIPTS_DIR = ROOT / "runtime" / "receipts"

RUNS_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def get_run_path(run_id: str) -> Path:
    """Get the path to a run artifact."""
    return RUNS_DIR / f"{run_id}.json"


def get_receipt_path(run_id: str) -> Path:
    """Get the path to an approval receipt."""
    return RECEIPTS_DIR / f"{run_id}.json"


def load_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Load a run artifact by ID."""
    path = get_run_path(run_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_run(run_id: str, data: Dict[str, Any]) -> None:
    """Save a run artifact."""
    path = get_run_path(run_id)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_approval_receipt(
    run_id: str,
    decision: str,  # "approved" or "rejected"
    actor: str = "operator",
    note: str = "",
) -> Dict[str, Any]:
    """Create an approval receipt."""
    receipt = {
        "run_id": run_id,
        "decision": decision,
        "actor": actor,
        "note": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    path = get_receipt_path(run_id)
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


def get_approval_receipt(run_id: str) -> Optional[Dict[str, Any]]:
    """Get the approval receipt for a run."""
    path = get_receipt_path(run_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def approve_run(run_id: str, actor: str = "operator", note: str = "") -> Dict[str, Any]:
    """Approve a run and create receipt."""
    run = load_run(run_id)
    if run is None:
        raise RuntimeError(f"Run {run_id} not found")
    
    if run.get("status") != "awaiting_approval":
        raise RuntimeError(f"Run {run_id} is not in awaiting_approval state")
    
    # Update run status
    run["status"] = "applied"
    run["approved_at"] = datetime.now(timezone.utc).isoformat()
    run["approved_by"] = actor
    save_run(run_id, run)
    
    # Create receipt
    receipt = create_approval_receipt(run_id, "approved", actor, note)
    return {"run": run, "receipt": receipt}


def reject_run(run_id: str, actor: str = "operator", note: str = "") -> Dict[str, Any]:
    """Reject a run and create receipt."""
    run = load_run(run_id)
    if run is None:
        raise RuntimeError(f"Run {run_id} not found")
    
    if run.get("status") != "awaiting_approval":
        raise RuntimeError(f"Run {run_id} is not in awaiting_approval state")
    
    # Update run status
    run["status"] = "rejected"
    run["rejected_at"] = datetime.now(timezone.utc).isoformat()
    run["rejected_by"] = actor
    save_run(run_id, run)
    
    # Create receipt
    receipt = create_approval_receipt(run_id, "rejected", actor, note)
    return {"run": run, "receipt": receipt}
