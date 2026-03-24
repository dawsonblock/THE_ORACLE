"""
Intent API - Single entry point for all code modification operations.

This is the ONLY way to submit code modification intents.
All operations flow through here to ensure:
- Consistent execution spine
- Full audit trail
- Approval boundary enforcement
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import uuid

from oracle_runtime.core.command.patch_command import PatchCommand, ExecutionOutcome
from oracle_runtime.core.executor.verified_executor import VerifiedExecutor, get_executor
from oracle_runtime.core.executor.world_observer import WorldObserver
from oracle_runtime.core.commit.coordinator import CommitCoordinator, create_in_memory_coordinator
from oracle_runtime.core.events.envelope import Event
from oracle_runtime.core.events.event_store import EventStore


@dataclass
class IntentResult:
    """Result of submitting an intent."""
    intent_id: str
    status: str  # "awaiting_approval", "failed", "completed"
    run_id: str
    execution_outcome: Optional[ExecutionOutcome] = None
    approval_id: Optional[str] = None
    error_message: Optional[str] = None
    events_committed: int = 0
    
    @classmethod
    def awaiting_approval(
        cls,
        intent_id: str,
        run_id: str,
        outcome: ExecutionOutcome,
        approval_id: str
    ) -> IntentResult:
        return cls(
            intent_id=intent_id,
            status="awaiting_approval",
            run_id=run_id,
            execution_outcome=outcome,
            approval_id=approval_id,
            events_committed=len(outcome.events) if outcome else 0
        )
    
    @classmethod
    def failed(
        cls,
        intent_id: str,
        run_id: str,
        error_message: str,
        outcome: Optional[ExecutionOutcome] = None
    ) -> IntentResult:
        return cls(
            intent_id=intent_id,
            status="failed",
            run_id=run_id,
            error_message=error_message,
            execution_outcome=outcome,
            events_committed=len(outcome.events) if outcome else 0
        )
    
    @classmethod
    def completed(
        cls,
        intent_id: str,
        run_id: str,
        outcome: ExecutionOutcome
    ) -> IntentResult:
        return cls(
            intent_id=intent_id,
            status="completed",
            run_id=run_id,
            execution_outcome=outcome,
            events_committed=len(outcome.events) if outcome else 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "status": self.status,
            "run_id": self.run_id,
            "approval_id": self.approval_id,
            "error_message": self.error_message,
            "events_committed": self.events_committed,
            "execution": self.execution_outcome.to_dict() if self.execution_outcome else None
        }


class IntentAPI:
    """
    Single entry point for all code modification intents.
    
    Flow:
    1. Receive intent (task + repo_path)
    2. Build context (read-only)
    3. Generate plan (read-only)
    4. Create PatchCommand
    5. Execute via VerifiedExecutor (ONLY side effects)
    6. Commit events
    7. Validate
    8. Request approval
    9. Return result
    """
    
    def __init__(
        self,
        executor: Optional[VerifiedExecutor] = None,
        coordinator: Optional[CommitCoordinator] = None,
        planner = None,  # Will be injected
        validator = None  # Will be injected
    ):
        self.executor = executor
        self.coordinator = coordinator or CommitCoordinator()
        self.planner = planner
        self.validator = validator
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
    
    def submit_intent(
        self,
        task: str,
        repo_path: str,
        auto_approve: bool = False,
        require_tests: bool = True
    ) -> IntentResult:
        """
        Submit a code modification intent.
        
        This is the SINGLE ENTRY POINT for all code modifications.
        
        Args:
            task: Description of the code modification
            repo_path: Path to the repository
            auto_approve: If True, skip approval (use with caution)
            require_tests: If True, require tests to pass
        
        Returns:
            IntentResult with status and execution details
        """
        intent_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        
        try:
            # 1. Build context (read-only)
            context = self._build_context(task, repo_path)
            
            # 2. Generate plan (read-only)
            plan = self._generate_plan(task, context)
            
            if not plan or not plan.get("edits"):
                return IntentResult.failed(
                    intent_id, run_id,
                    "No plan generated - task may be unclear or already satisfied"
                )
            
            # 3. Create command
            command = PatchCommand.from_plan({
                **plan,
                "task": task,
                "run_id": run_id
            })
            
            # Add postconditions based on options
            postconditions = ["files_modified", "syntax_valid"]
            if require_tests:
                postconditions.append("tests_pass")
            command = command.with_postconditions(postconditions)
            
            # 4. Execute (ONLY side effects happen here)
            executor = self.executor or get_executor(repo_path)
            outcome = executor.execute(command)
            
            # 5. Commit events
            events = [EventEnvelope.from_dict(e) for e in outcome.events]
            commit_result = self.coordinator.commit(events)
            
            if not outcome.success:
                return IntentResult.failed(
                    intent_id, run_id,
                    outcome.error_message or "Execution failed",
                    outcome
                )
            
            # 6. Run additional validation
            if self.validator:
                validation_result = self.validator.run()
                validation_event = Event.validation_completed(
                    validation_result.__dict__ if hasattr(validation_result, '__dict__') else validation_result,
                    correlation_id=executor.correlation_id
                )
                self.coordinator.commit([validation_event])
                
                if not validation_result.get("passed", True):
                    return IntentResult.failed(
                        intent_id, run_id,
                        "Validation failed",
                        outcome
                    )
            
            # 7. Approval
            if auto_approve:
                # Auto-approve and commit
                self._auto_commit(run_id, outcome)
                return IntentResult.completed(intent_id, run_id, outcome)
            else:
                # Request approval
                approval_id = self._request_approval(run_id, outcome)
                return IntentResult.awaiting_approval(
                    intent_id, run_id, outcome, approval_id
                )
        
        except Exception as e:
            return IntentResult.failed(
                intent_id, run_id,
                f"Unexpected error: {str(e)}"
            )
    
    def _build_context(self, task: str, repo_path: str) -> List[Dict[str, Any]]:
        """Build context for planning (read-only)."""
        # Import here to avoid circular dependency
        try:
            from integration.context_builder import build_context
            return build_context(task, repo_path)
        except ImportError:
            # Fallback: minimal context
            return [{"file": "", "content": ""}]
    
    def _generate_plan(self, task: str, context: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate plan (read-only)."""
        # Use injected planner or fallback
        if self.planner:
            return self.planner.plan(task, context)
        
        # Fallback to existing planner
        try:
            from integration.llm_planner import create_plan
            return create_plan(task, context)
        except ImportError:
            return None
    
    def _request_approval(self, run_id: str, outcome: ExecutionOutcome) -> str:
        """Request approval for the outcome."""
        approval_id = str(uuid.uuid4())
        
        self.pending_approvals[approval_id] = {
            "run_id": run_id,
            "outcome": outcome,
            "status": "pending"
        }
        
        # Emit approval requested event
        approval_event = Event.approval_requested(
            approval_id,
            correlation_id=outcome.events[0].get("correlation_id") if outcome.events else None
        )
        self.coordinator.commit([approval_event])
        
        return approval_id
    
    def approve(self, approval_id: str, actor: str = "operator") -> Dict[str, Any]:
        """Approve a pending execution."""
        if approval_id not in self.pending_approvals:
            return {"error": "Approval not found"}
        
        pending = self.pending_approvals[approval_id]
        outcome = pending["outcome"]
        
        # Emit approved event
        approved_event = Event.approved(
            approval_id,
            actor,
            correlation_id=outcome.events[0].get("correlation_id") if outcome.events else None
        )
        self.coordinator.commit([approved_event])
        
        # Commit to git
        commit_hash = self._commit_to_git(approval_id, actor)
        
        # Emit committed event
        committed_event = Event.committed(
            commit_hash,
            correlation_id=outcome.events[0].get("correlation_id") if outcome.events else None
        )
        self.coordinator.commit([committed_event])
        
        # Update pending
        pending["status"] = "approved"
        pending["committed_by"] = actor
        pending["commit_hash"] = commit_hash
        
        return {
            "status": "approved",
            "approval_id": approval_id,
            "commit_hash": commit_hash
        }
    
    def reject(self, approval_id: str, actor: str = "operator") -> Dict[str, Any]:
        """Reject a pending execution."""
        if approval_id not in self.pending_approvals:
            return {"error": "Approval not found"}
        
        pending = self.pending_approvals[approval_id]
        outcome = pending["outcome"]
        
        # Emit rejected event
        rejected_event = Event.rejected(
            approval_id,
            actor,
            correlation_id=outcome.events[0].get("correlation_id") if outcome.events else None
        )
        self.coordinator.commit([rejected_event])
        
        # Update pending
        pending["status"] = "rejected"
        pending["rejected_by"] = actor
        
        return {
            "status": "rejected",
            "approval_id": approval_id
        }
    
    def _auto_commit(self, run_id: str, outcome: ExecutionOutcome) -> str:
        """Auto-commit (use with caution)."""
        return self._commit_to_git(run_id, "auto")
    
    def _commit_to_git(self, identifier: str, actor: str) -> str:
        """Commit changes to git."""
        import subprocess
        
        try:
            # Stage changes
            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                check=True
            )
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", f"ORACLE: {identifier} approved by {actor}"],
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
            
            return "nothing_to_commit"
        
        except Exception as e:
            return f"error: {str(e)}"
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get list of pending approvals."""
        return [
            {
                "approval_id": aid,
                "run_id": data["run_id"],
                "status": data["status"]
            }
            for aid, data in self.pending_approvals.items()
            if data["status"] == "pending"
        ]


# Global API instance
_global_api: Optional[IntentAPI] = None


def get_intent_api() -> IntentAPI:
    """Get or create global IntentAPI instance."""
    global _global_api
    if _global_api is None:
        _global_api = IntentAPI()
    return _global_api


def submit_intent(task: str, repo_path: str, **kwargs) -> IntentResult:
    """
    Convenience function to submit an intent.
    
    This is the PRIMARY ENTRY POINT for code modifications.
    """
    api = get_intent_api()
    return api.submit_intent(task, repo_path, **kwargs)
