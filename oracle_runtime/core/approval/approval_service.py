"""Approval service - gate between execution and promotion."""
from __future__ import annotations
import json
import uuid
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from oracle_runtime.core.command.patch_command import ExecutionOutcome


@dataclass
class ApprovalRequest:
    """Request for approval."""
    approval_id: str
    run_id: str
    status: str  # "pending", "approved", "rejected"
    outcome: Optional[ExecutionOutcome]
    created_at: str
    actor: Optional[str] = None
    decided_at: Optional[str] = None
    note: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.outcome:
            data['outcome'] = self.outcome.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApprovalRequest:
        outcome_data = data.get('outcome')
        outcome = ExecutionOutcome(**outcome_data) if outcome_data else None
        return cls(
            approval_id=data["approval_id"],
            run_id=data["run_id"],
            status=data["status"],
            outcome=outcome,
            created_at=data["created_at"],
            actor=data.get("actor"),
            decided_at=data.get("decided_at"),
            note=data.get("note")
        )


class ApprovalService:
    """
    Approval boundary enforcement.
    
    Flow: Executor → Validation → Approval → Git Commit
    
    Guarantees:
    - No commit without approval
    - All approvals logged
    - Reversible decisions tracked
    """
    
    def __init__(self, storage_dir: str = "oracle_runtime/approvals"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._pending: Dict[str, ApprovalRequest] = {}
        self._load_pending()
    
    def _load_pending(self):
        """Load pending approvals from disk."""
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                if data.get("status") == "pending":
                    request = ApprovalRequest.from_dict(data)
                    self._pending[request.approval_id] = request
            except (json.JSONDecodeError, KeyError):
                continue
    
    def request_approval(self, run_id: str, outcome: ExecutionOutcome) -> str:
        """
        Request approval for an execution outcome.
        
        Returns approval_id for tracking.
        """
        approval_id = str(uuid.uuid4())
        request = ApprovalRequest(
            approval_id=approval_id,
            run_id=run_id,
            status="pending",
            outcome=outcome,
            created_at=datetime.datetime.now().isoformat()
        )
        
        # Store to disk
        self._store_request(request)
        self._pending[approval_id] = request
        
        return approval_id
    
    def approve(
        self,
        approval_id: str,
        actor: str = "operator",
        note: str = ""
    ) -> Dict[str, Any]:
        """
        Approve a pending request.
        
        Only after approval: commit to git.
        """
        request = self._get_request(approval_id)
        if not request:
            return {"error": "Approval not found"}
        
        if request.status != "pending":
            return {"error": f"Already {request.status}"}
        
        # Update request
        request.status = "approved"
        request.actor = actor
        request.decided_at = datetime.datetime.now().isoformat()
        request.note = note
        
        self._store_request(request)
        if approval_id in self._pending:
            del self._pending[approval_id]
        
        # Execute git commit
        commit_hash = self._commit_to_git(approval_id, actor, note)
        
        return {
            "status": "approved",
            "approval_id": approval_id,
            "actor": actor,
            "commit_hash": commit_hash,
            "timestamp": request.decided_at
        }
    
    def reject(
        self,
        approval_id: str,
        actor: str = "operator",
        note: str = ""
    ) -> Dict[str, Any]:
        """
        Reject a pending request.
        
        Reverts changes on rejection.
        """
        request = self._get_request(approval_id)
        if not request:
            return {"error": "Approval not found"}
        
        if request.status != "pending":
            return {"error": f"Already {request.status}"}
        
        # Update request
        request.status = "rejected"
        request.actor = actor
        request.decided_at = datetime.datetime.now().isoformat()
        request.note = note
        
        self._store_request(request)
        if approval_id in self._pending:
            del self._pending[approval_id]
        
        # Revert changes
        revert_result = self._revert_changes()
        
        return {
            "status": "rejected",
            "approval_id": approval_id,
            "actor": actor,
            "timestamp": request.decided_at,
            "reverted": revert_result
        }
    
    def get_pending(self) -> list:
        """Get all pending approvals."""
        return [
            {
                "approval_id": r.approval_id,
                "run_id": r.run_id,
                "created_at": r.created_at
            }
            for r in self._pending.values()
        ]
    
    def get_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request."""
        return self._get_request(approval_id)
    
    def _get_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Load request from memory or disk."""
        if approval_id in self._pending:
            return self._pending[approval_id]
        
        path = self.storage_dir / f"{approval_id}.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                return ApprovalRequest.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                return None
        return None
    
    def _store_request(self, request: ApprovalRequest):
        """Store request to disk."""
        path = self.storage_dir / f"{request.approval_id}.json"
        with open(path, 'w') as f:
            json.dump(request.to_dict(), f, indent=2, default=str)
    
    def _commit_to_git(self, approval_id: str, actor: str, note: str = "") -> str:
        """Commit changes to git."""
        try:
            # Stage changes
            result = subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return f"stage_error: {result.stderr}"
            
            # Build commit message
            message = f"ORACLE: {approval_id} approved by {actor}"
            if note:
                message += f"\n\nNote: {note}"
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True
                )
                return hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"
            
            # Check if nothing to commit
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return "nothing_to_commit"
            
            return f"commit_error: {result.stderr}"
        
        except Exception as e:
            return f"exception: {str(e)}"
    
    def _revert_changes(self) -> bool:
        """Revert unapproved changes."""
        try:
            result = subprocess.run(
                ["git", "checkout", "--", "."],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False


# Global service instance
_global_service: Optional[ApprovalService] = None


def get_approval_service() -> ApprovalService:
    """Get or create global approval service."""
    global _global_service
    if _global_service is None:
        _global_service = ApprovalService()
    return _global_service
