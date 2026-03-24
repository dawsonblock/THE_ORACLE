"""
Verified Executor - The ONLY place side effects happen.

This is the central execution authority for THE_ORACLE.
All file writes, git changes, and patches MUST flow through here.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import uuid
import subprocess
from pathlib import Path

from oracle_runtime.core.command.patch_command import PatchCommand, ExecutionOutcome
from oracle_runtime.core.executor.world_observer import WorldObserver, WorldState
from oracle_runtime.core.executor.policy import PolicyEngine, PolicyDecision
from oracle_runtime.core.executor.postconditions import PostconditionVerifier, PostconditionResult
from oracle_runtime.core.events.envelope import Event, EventEnvelope


class VerifiedExecutor:
    """
    Central execution authority.
    
    Guarantees:
    1. All side effects are authorized by policy
    2. Pre-state is captured before execution
    3. Post-state is captured after execution
    4. Postconditions are verified
    5. All actions emit events
    6. No execution happens without audit trail
    
    Usage:
        executor = VerifiedExecutor()
        outcome = executor.execute(command)
        # outcome.events contains full audit trail
    """
    
    def __init__(
        self,
        working_dir: Optional[str] = None,
        policy: Optional[PolicyEngine] = None,
        observer: Optional[WorldObserver] = None,
        verifier: Optional[PostconditionVerifier] = None
    ):
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.policy = policy or PolicyEngine()
        self.observer = observer or WorldObserver(str(self.working_dir))
        self.verifier = verifier or PostconditionVerifier()
        self.correlation_id = None
    
    def execute(self, command: PatchCommand) -> ExecutionOutcome:
        """
        Execute a command through the verified execution spine.
        
        This is the ONLY method that should cause side effects.
        
        Returns:
            ExecutionOutcome with result, events, and verification status
        """
        # Generate correlation ID for this execution
        self.correlation_id = str(uuid.uuid4())
        
        events: List[EventEnvelope] = []
        
        # 1. Capture pre-state
        pre_state = self.observer.observe(command.files)
        events.append(Event.pre_state_observed(
            pre_state.to_dict(),
            correlation_id=self.correlation_id,
            causation_id=command.command_id
        ))
        
        # 2. Check policy
        policy_decision = self.policy.check(command)
        if not policy_decision.allowed:
            events.append(Event.action_executed(
                {"status": "denied", "reason": policy_decision.reason},
                correlation_id=self.correlation_id
            ))
            return ExecutionOutcome.failed(
                command.command_id,
                f"Policy denied: {policy_decision.reason}",
                events=[e.to_dict() for e in events]
            )
        
        # 3. Execute action
        try:
            result = self._apply_patch(command)
            events.append(Event.action_executed(
                result,
                correlation_id=self.correlation_id
            ))
        except Exception as e:
            events.append(Event.action_executed(
                {"status": "error", "error": str(e)},
                correlation_id=self.correlation_id
            ))
            return ExecutionOutcome.failed(
                command.command_id,
                f"Execution failed: {str(e)}",
                events=[e.to_dict() for e in events]
            )
        
        # 4. Capture post-state
        post_state = self.observer.observe(command.files)
        events.append(Event.post_state_observed(
            post_state.to_dict(),
            correlation_id=self.correlation_id
        ))
        
        # 5. Verify postconditions
        postcondition_results = self.verifier.verify(pre_state, post_state, command)
        all_passed = self.verifier.verify_all_passed(postcondition_results)
        
        events.append(Event.postcondition_verified(
            all_passed,
            {"results": [r.__dict__ for r in postcondition_results]},
            correlation_id=self.correlation_id
        ))
        
        # 6. Return outcome
        if all_passed:
            return ExecutionOutcome.success(
                command.command_id,
                events=[e.to_dict() for e in events],
                result_data={
                    "files_modified": command.files,
                    "pre_state": pre_state.to_dict(),
                    "post_state": post_state.to_dict()
                },
                postconditions_verified=True
            )
        else:
            failed_conditions = [
                r.condition for r in postcondition_results if not r.passed
            ]
            return ExecutionOutcome.failed(
                command.command_id,
                f"Postconditions failed: {', '.join(failed_conditions)}",
                events=[e.to_dict() for e in events]
            )
    
    def _apply_patch(self, command: PatchCommand) -> Dict[str, Any]:
        """
        Apply the patch. This is the actual side effect.
        
        Uses git apply for atomic application.
        """
        # Write diff to temporary file
        temp_diff = self.working_dir / ".oracle_temp.diff"
        temp_diff.write_text(command.diff)
        
        try:
            # Apply using git apply
            result = subprocess.run(
                ["git", "apply", str(temp_diff)],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"git apply failed: {result.stderr}")
            
            return {
                "status": "applied",
                "files": command.files,
                "method": "git_apply"
            }
        
        finally:
            # Clean up temp file
            if temp_diff.exists():
                temp_diff.unlink()
    
    def dry_run(self, command: PatchCommand) -> Dict[str, Any]:
        """
        Simulate execution without applying changes.
        
        Returns what would happen without side effects.
        """
        # Check policy only
        policy_decision = self.policy.check(command)
        
        return {
            "would_execute": policy_decision.allowed,
            "policy_result": policy_decision.reason,
            "violations": policy_decision.violations,
            "files_affected": command.files,
            "postconditions": command.postconditions
        }


# Global executor instance (singleton pattern)
_global_executor: Optional[VerifiedExecutor] = None


def get_executor(working_dir: Optional[str] = None) -> VerifiedExecutor:
    """Get or create the global executor instance."""
    global _global_executor
    if _global_executor is None or (working_dir and _global_executor.working_dir != Path(working_dir)):
        _global_executor = VerifiedExecutor(working_dir=working_dir)
    return _global_executor


def reset_executor() -> None:
    """Reset the global executor (for testing)."""
    global _global_executor
    _global_executor = None
