"""Command definitions for the execution spine."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import hashlib
import json


@dataclass(frozen=True)
class PatchCommand:
    """
    Immutable command for patch execution.
    
    This is the ONLY way to request code modifications.
    All fields are frozen to ensure immutability.
    """
    files: List[str]
    diff: str
    postconditions: List[str] = field(default_factory=lambda: [
        "files_modified",
        "syntax_valid"
    ])
    metadata: Dict[str, Any] = field(default_factory=dict)
    command_id: str = field(default="")
    
    def __post_init__(self):
        # Generate command ID from content if not provided
        if not self.command_id:
            content = json.dumps({
                "files": sorted(self.files),
                "diff": self.diff,
                "postconditions": sorted(self.postconditions)
            }, sort_keys=True)
            object.__setattr__(
                self, 
                'command_id', 
                hashlib.sha256(content.encode()).hexdigest()[:16]
            )
    
    @classmethod
    def from_edits(cls, edits: List[Dict[str, str]], **metadata) -> PatchCommand:
        """
        Create a PatchCommand from a list of edits.
        
        edits: List of {"file": str, "search": str, "replace": str}
        """
        files = list(set(e["file"] for e in edits))
        
        # Generate unified diff format
        diff_lines = []
        for edit in edits:
            diff_lines.append(f"--- a/{edit['file']}")
            diff_lines.append(f"+++ b/{edit['file']}")
            diff_lines.append("@@ -1 +1 @@")
            diff_lines.append(f"-{edit['search']}")
            diff_lines.append(f"+{edit['replace']}")
        
        return cls(
            files=files,
            diff="\n".join(diff_lines),
            metadata={"edits": edits, **metadata}
        )
    
    @classmethod
    def from_plan(cls, plan: Dict[str, Any]) -> PatchCommand:
        """Create a PatchCommand from a planner output."""
        edits = plan.get("edits", [])
        return cls.from_edits(
            edits,
            plan_id=plan.get("plan_id"),
            confidence=plan.get("confidence", 0.0),
            task=plan.get("task", "")
        )
    
    def with_postconditions(self, postconditions: List[str]) -> PatchCommand:
        """Return new command with different postconditions."""
        return PatchCommand(
            files=self.files,
            diff=self.diff,
            postconditions=postconditions,
            metadata=self.metadata,
            command_id=self.command_id
        )
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the command.
        
        Returns (is_valid, error_message)
        """
        if not self.files:
            return False, "No files specified"
        
        if not self.diff:
            return False, "No diff content"
        
        for f in self.files:
            if not f or f.startswith('/') or '..' in f:
                return False, f"Invalid file path: {f}"
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "command_id": self.command_id,
            "files": self.files,
            "diff": self.diff,
            "postconditions": self.postconditions,
            "metadata": self.metadata
        }


@dataclass(frozen=True)
class ExecutionOutcome:
    """
    Result of command execution.
    
    Contains:
    - Result data
    - Events emitted during execution
    - Whether postconditions were verified
    - Error information if failed
    """
    command_id: str
    success: bool
    events: List[Any] = field(default_factory=list)
    postconditions_verified: bool = False
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    @classmethod
    def success(
        cls,
        command_id: str,
        events: List[Any],
        result_data: Dict[str, Any],
        postconditions_verified: bool = True
    ) -> ExecutionOutcome:
        return cls(
            command_id=command_id,
            success=True,
            events=events,
            postconditions_verified=postconditions_verified,
            result_data=result_data
        )
    
    @classmethod
    def failed(
        cls,
        command_id: str,
        error_message: str,
        events: List[Any] = None
    ) -> ExecutionOutcome:
        return cls(
            command_id=command_id,
            success=False,
            events=events or [],
            error_message=error_message
        )
    
    @classmethod
    def policy_denied(cls, command_id: str, reason: str) -> ExecutionOutcome:
        return cls.failed(command_id, f"Policy denied: {reason}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "command_id": self.command_id,
            "success": self.success,
            "postconditions_verified": self.postconditions_verified,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "event_count": len(self.events)
        }
