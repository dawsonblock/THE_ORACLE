"""FastAPI server for coding runs with approval flow."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from integration.pipeline import run_pipeline
from integration.runtime.approval_store import (
    load_run,
    save_run,
    approve_run,
    reject_run,
    get_approval_receipt,
    RUNS_DIR,
)
from pathlib import Path
import json
from datetime import datetime, timezone
import uuid

app = FastAPI()

# Enable CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parents[1]


class RunRequest(BaseModel):
    task: str
    repo_path: str


class ApprovalRequest(BaseModel):
    actor: str = "operator"
    note: str = ""


class DecisionRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    actor: str = "operator"
    note: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    from integration.preflight import check_run_server
    check_run_server()
    return {"status": "ready"}


@app.post("/run")
def run(req: RunRequest):
    """Execute a run through the pipeline."""
    result = run_pipeline(req.task, req.repo_path)
    
    # Use the pipeline's run_id
    run_id = result["run_id"]
    
    # Build artifact, ensuring we control the fields
    artifact = {
        "run_id": run_id,
        "task": req.task,
        "repo_path": req.repo_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": result["status"],
        "attempts": result["attempts"],
        "reason": result["reason"],
        "files_changed": result["files_changed"],
    }
    
    # If pipeline succeeded, set to awaiting_approval
    if artifact["status"] == "applied":
        artifact["status"] = "awaiting_approval"
    
    save_run(run_id, artifact)
    return artifact


@app.get("/runs")
def list_runs():
    """List all runs."""
    runs = []
    for run_file in RUNS_DIR.glob("*.json"):
        try:
            with open(run_file) as f:
                run = json.load(f)
                runs.append(run)
        except Exception:
            continue
    # Sort by timestamp descending
    runs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return runs


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    """Get a run by ID."""
    run = load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.post("/runs/{run_id}/approve")
def approve(run_id: str, req: ApprovalRequest):
    """Approve a run."""
    try:
        result = approve_run(run_id, req.actor, req.note)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/runs/{run_id}/reject")
def reject(run_id: str, req: ApprovalRequest):
    """Reject a run."""
    try:
        result = reject_run(run_id, req.actor, req.note)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/runs/{run_id}/receipt")
def get_receipt(run_id: str):
    """Get the approval receipt for a run."""
    receipt = get_approval_receipt(run_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@app.post("/runs/{run_id}/decide")
def decide(run_id: str, req: DecisionRequest):
    """Unified approval/denial gate.
    
    This is the single entry point for both approve and reject decisions.
    Both paths share the same validation logic:
    1. Run must exist
    2. Run must be in 'awaiting_approval' state
    3. Decision must be 'approved' or 'rejected'
    """
    # Validate decision value (unified validation)
    if req.decision not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid decision: {req.decision}. Must be 'approved' or 'rejected'"
        )
    
    # Run validation (shared by both paths)
    run = load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    if run.get("status") != "awaiting_approval":
        raise HTTPException(
            status_code=400, 
            detail=f"Run {run_id} is not in awaiting_approval state (current: {run.get('status')})"
        )
    
    # Execute decision through unified gate
    try:
        if req.decision == "approved":
            result = approve_run(run_id, req.actor, req.note)
        else:  # rejected
            result = reject_run(run_id, req.actor, req.note)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
