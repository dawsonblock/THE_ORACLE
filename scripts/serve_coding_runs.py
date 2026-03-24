"""FastAPI server for coding runs with approval flow."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from integration.pipeline import run_pipeline
from runtime.approval_store import (
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

ROOT = Path(__file__).resolve().parents[1]


class RunRequest(BaseModel):
    task: str
    repo_path: str


class ApprovalRequest(BaseModel):
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


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
