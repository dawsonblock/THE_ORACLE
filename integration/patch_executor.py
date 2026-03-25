"""
Patch Executor - Now routes through VerifiedExecutor.

This module is maintained for backward compatibility but now
delegates all patch execution to oracle_runtime.core.executor.
"""
from __future__ import annotations
import os
from typing import Dict, List, Any
import warnings

# Import new execution spine
from oracle_runtime import get_executor, PatchCommand


def apply_plan(plan: Dict[str, Any], repo: str) -> Dict[str, Any]:
    """
    Apply a plan to a repository.
    
    DEPRECATED: Routes through VerifiedExecutor for single authority.
    Use oracle_runtime.submit_intent() directly for new code.
    """
    warnings.warn(
        "apply_plan() is deprecated. Use oracle_runtime.submit_intent() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    edits = plan.get("edits")
    if not edits:
        return {"success": False, "reason": "no_edits", "files": []}
    
    # Convert old plan format to PatchCommand
    command = PatchCommand.from_edits(edits, repo_path=repo)
    
    # Route through VerifiedExecutor (single authority)
    executor = get_executor(repo)
    outcome = executor.execute(command)
    
    if outcome.success:
        return {
            "success": True,
            "reason": None,
            "files": command.files
        }
    else:
        return {
            "success": False,
            "reason": outcome.error_message or "execution_failed",
            "files": []
        }


# Keep old function for backward compatibility but route through new spine
def apply_edits(edits: List[Dict[str, str]], repo: str) -> Dict[str, Any]:
    """
    Apply edits to files.
    
    DEPRECATED: Routes through VerifiedExecutor.
    """
    warnings.warn(
        "apply_edits() is deprecated. Use VerifiedExecutor directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    command = PatchCommand.from_edits(edits, repo_path=repo)
    executor = get_executor(repo)
    outcome = executor.execute(command)
    
    return {
        "success": outcome.success,
        "error": outcome.error_message,
        "files": command.files
    }
