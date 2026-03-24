"""
API Server - Thin layer over the execution spine.

This is a minimal FastAPI server that delegates all business logic
to the oracle_runtime core.
"""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from oracle_runtime.core.intent.intent_api import (
    get_intent_api, 
    IntentResult,
    submit_intent
)
from oracle_runtime.core.events.event_store import EventStore
from oracle_runtime.core.commit.state import StateManager

app = FastAPI(
    title="THE ORACLE",
    description="Single coherent system for safe code modifications",
    version="2.0.0"
)

# CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global API instance
intent_api = get_intent_api()
event_store = EventStore()
state_manager = StateManager()


# Request/Response Models
class RunRequest(BaseModel):
    task: str
    repo_path: str
    auto_approve: bool = False
    require_tests: bool = True


class ApprovalRequest(BaseModel):
    actor: str = "operator"
    note: Optional[str] = None


class DecisionRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    actor: str = "operator"
    note: Optional[str] = None


# Health Endpoints
@app.get("/health")
def health():
    """Basic health check."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/ready")
def ready():
    """Readiness check - verifies core systems."""
    checks = {
        "event_store": event_store.log_path.exists(),
        "state_manager": True,
        "intent_api": intent_api is not None
    }
    
    all_ready = all(checks.values())
    
    if all_ready:
        return {"status": "ready", "checks": checks}
    else:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks}
        )


# Main Execution Endpoint
@app.post("/run")
def run(req: RunRequest):
    """
    Submit a code modification intent.
    
    This is the primary endpoint for all code modifications.
    All execution flows through the verified executor.
    """
    result = submit_intent(
        task=req.task,
        repo_path=req.repo_path,
        auto_approve=req.auto_approve,
        require_tests=req.require_tests
    )
    
    return result.to_dict()


# Approval Endpoints
@app.get("/approvals/pending")
def get_pending_approvals():
    """Get list of pending approvals."""
    return intent_api.get_pending_approvals()


@app.post("/approvals/{approval_id}/approve")
def approve(approval_id: str, req: ApprovalRequest):
    """Approve a pending execution."""
    result = intent_api.approve(approval_id, req.actor)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.post("/approvals/{approval_id}/reject")
def reject(approval_id: str, req: ApprovalRequest):
    """Reject a pending execution."""
    result = intent_api.reject(approval_id, req.actor)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.post("/approvals/{approval_id}/decide")
def decide(approval_id: str, req: DecisionRequest):
    """
    Unified approval/denial gate.
    
    decision: "approved" or "rejected"
    """
    if req.decision not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision: {req.decision}. Must be 'approved' or 'rejected'"
        )
    
    if req.decision == "approved":
        result = intent_api.approve(approval_id, req.actor)
    else:
        result = intent_api.reject(approval_id, req.actor)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# Event Store Endpoints
@app.get("/events")
def get_events(limit: int = 100):
    """Get recent events from the event store."""
    events = event_store.read_all()
    return {
        "total": len(events),
        "events": [e.to_dict() for e in events[-limit:]]
    }


@app.get("/events/stats")
def get_event_stats():
    """Get statistics about the event store."""
    return event_store.get_stats()


# State Endpoints
@app.get("/state")
def get_state():
    """Get current projected state."""
    return state_manager.load()


@app.get("/state/stats")
def get_state_stats():
    """Get statistics about the state."""
    return state_manager.get_stats()


# System Endpoints
@app.get("/system/status")
def get_system_status():
    """Get full system status."""
    return {
        "version": "2.0.0",
        "event_store": event_store.get_stats(),
        "state": state_manager.get_stats(),
        "pending_approvals": len(intent_api.get_pending_approvals())
    }


# Main entry point
def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
