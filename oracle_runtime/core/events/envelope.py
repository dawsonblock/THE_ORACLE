"""Event envelope for structured event storage."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid


@dataclass(frozen=True)
class EventEnvelope:
    """
    Immutable envelope wrapping an event with metadata.
    
    Provides:
    - Unique event ID
    - Timestamp
    - Event type
    - Causation tracking (what caused this event)
    - Correlation tracking (what operation this belongs to)
    """
    event_id: str
    event_type: str
    timestamp: str
    data: Dict[str, Any]
    causation_id: Optional[str] = None
    correlation_id: Optional[str] = None
    version: int = 1
    
    @classmethod
    def create(
        cls,
        event_type: str,
        data: Dict[str, Any],
        causation_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> EventEnvelope:
        """Create a new event envelope."""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data,
            causation_id=causation_id,
            correlation_id=correlation_id,
            version=1
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EventEnvelope:
        """Create from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> EventEnvelope:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


class Event:
    """Simple event factory for common event types."""
    
    @staticmethod
    def pre_state_observed(state: Dict[str, Any], **kwargs) -> EventEnvelope:
        return EventEnvelope.create("PreStateObserved", {"state": state}, **kwargs)
    
    @staticmethod
    def action_executed(result: Dict[str, Any], **kwargs) -> EventEnvelope:
        return EventEnvelope.create("ActionExecuted", {"result": result}, **kwargs)
    
    @staticmethod
    def post_state_observed(state: Dict[str, Any], **kwargs) -> EventEnvelope:
        return EventEnvelope.create("PostStateObserved", {"state": state}, **kwargs)
    
    @staticmethod
    def postcondition_verified(passed: bool, details: Dict[str, Any], **kwargs) -> EventEnvelope:
        return EventEnvelope.create(
            "PostconditionVerified" if passed else "PostconditionFailed",
            {"passed": passed, "details": details},
            **kwargs
        )
    
    @staticmethod
    def validation_completed(result: Dict[str, Any], **kwargs) -> EventEnvelope:
        return EventEnvelope.create("ValidationCompleted", result, **kwargs)
    
    @staticmethod
    def approval_requested(approval_id: str, **kwargs) -> EventEnvelope:
        return EventEnvelope.create("ApprovalRequested", {"approval_id": approval_id}, **kwargs)
    
    @staticmethod
    def approved(approval_id: str, actor: str, **kwargs) -> EventEnvelope:
        return EventEnvelope.create("Approved", {"approval_id": approval_id, "actor": actor}, **kwargs)
    
    @staticmethod
    def rejected(approval_id: str, actor: str, **kwargs) -> EventEnvelope:
        return EventEnvelope.create("Rejected", {"approval_id": approval_id, "actor": actor}, **kwargs)
    
    @staticmethod
    def committed(commit_hash: str, **kwargs) -> EventEnvelope:
        return EventEnvelope.create("Committed", {"commit_hash": commit_hash}, **kwargs)
    
    @staticmethod
    def retry_requested(attempt: int, reason: str, **kwargs) -> EventEnvelope:
        return EventEnvelope.create("RetryRequested", {"attempt": attempt, "reason": reason}, **kwargs)
