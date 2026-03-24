"""Pure reducer functions for state projection."""
from __future__ import annotations
from typing import Dict, Any, List


class StateReducer:
    """
    Pure functions that reduce events to state.
    
    Guarantees:
    - No side effects
    - Deterministic output for same inputs
    - Immutable state updates
    """
    
    @staticmethod
    def reduce(state: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply an event to state, returning new state.
        
        This is a pure function - no mutations to input state.
        """
        # Create a copy to ensure immutability
        new_state = dict(state)
        
        event_type = event.get("event_type")
        event_data = event.get("data", {})
        
        if event_type == "PreStateObserved":
            new_state = StateReducer._reduce_pre_state(new_state, event_data)
        
        elif event_type == "ActionExecuted":
            new_state = StateReducer._reduce_action_executed(new_state, event_data)
        
        elif event_type == "PostStateObserved":
            new_state = StateReducer._reduce_post_state(new_state, event_data)
        
        elif event_type == "PostconditionVerified":
            new_state = StateReducer._reduce_postcondition_verified(new_state, event_data)
        
        elif event_type == "PostconditionFailed":
            new_state = StateReducer._reduce_postcondition_failed(new_state, event_data)
        
        elif event_type == "ValidationCompleted":
            new_state = StateReducer._reduce_validation_completed(new_state, event_data)
        
        elif event_type == "ApprovalRequested":
            new_state = StateReducer._reduce_approval_requested(new_state, event_data)
        
        elif event_type == "Approved":
            new_state = StateReducer._reduce_approved(new_state, event_data)
        
        elif event_type == "Rejected":
            new_state = StateReducer._reduce_rejected(new_state, event_data)
        
        elif event_type == "Committed":
            new_state = StateReducer._reduce_committed(new_state, event_data)
        
        elif event_type == "RetryRequested":
            new_state = StateReducer._reduce_retry_requested(new_state, event_data)
        
        # Track event count
        new_state["event_count"] = new_state.get("event_count", 0) + 1
        new_state["last_event_type"] = event_type
        new_state["last_event_timestamp"] = event.get("timestamp")
        
        return new_state
    
    @staticmethod
    def _reduce_pre_state(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce PreStateObserved event."""
        if "executions" not in state:
            state["executions"] = []
        
        state["executions"].append({
            "pre_state": data.get("state"),
            "status": "started"
        })
        return state
    
    @staticmethod
    def _reduce_action_executed(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce ActionExecuted event."""
        if state["executions"]:
            state["executions"][-1]["action_result"] = data
            state["executions"][-1]["status"] = data.get("status", "executed")
        return state
    
    @staticmethod
    def _reduce_post_state(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce PostStateObserved event."""
        if state["executions"]:
            state["executions"][-1]["post_state"] = data.get("state")
        return state
    
    @staticmethod
    def _reduce_postcondition_verified(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce PostconditionVerified event."""
        state["last_verification"] = {
            "passed": True,
            "details": data
        }
        if state["executions"]:
            state["executions"][-1]["verification"] = "passed"
        return state
    
    @staticmethod
    def _reduce_postcondition_failed(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce PostconditionFailed event."""
        state["last_verification"] = {
            "passed": False,
            "details": data
        }
        state["failure_count"] = state.get("failure_count", 0) + 1
        if state["executions"]:
            state["executions"][-1]["verification"] = "failed"
        return state
    
    @staticmethod
    def _reduce_validation_completed(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce ValidationCompleted event."""
        state["last_validation"] = data
        return state
    
    @staticmethod
    def _reduce_approval_requested(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce ApprovalRequested event."""
        approval_id = data.get("approval_id")
        if "pending_approvals" not in state:
            state["pending_approvals"] = []
        state["pending_approvals"].append(approval_id)
        return state
    
    @staticmethod
    def _reduce_approved(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce Approved event."""
        approval_id = data.get("approval_id")
        if "pending_approvals" in state and approval_id in state["pending_approvals"]:
            state["pending_approvals"].remove(approval_id)
        if "approved" not in state:
            state["approved"] = []
        state["approved"].append(data)
        return state
    
    @staticmethod
    def _reduce_rejected(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce Rejected event."""
        approval_id = data.get("approval_id")
        if "pending_approvals" in state and approval_id in state["pending_approvals"]:
            state["pending_approvals"].remove(approval_id)
        if "rejected" not in state:
            state["rejected"] = []
        state["rejected"].append(data)
        return state
    
    @staticmethod
    def _reduce_committed(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce Committed event."""
        if "commits" not in state:
            state["commits"] = []
        state["commits"].append(data)
        return state
    
    @staticmethod
    def _reduce_retry_requested(state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce RetryRequested event."""
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["last_retry_reason"] = data.get("reason")
        return state
    
    @staticmethod
    def reduce_all(events: List[Dict[str, Any]], initial_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Reduce a list of events to final state.
        
        Pure function - same inputs always produce same output.
        """
        state = initial_state or {}
        for event in events:
            state = StateReducer.reduce(state, event)
        return state
    
    @staticmethod
    def get_initial_state() -> Dict[str, Any]:
        """Get the initial empty state."""
        return {
            "version": 1,
            "event_count": 0,
            "executions": [],
            "pending_approvals": [],
            "approved": [],
            "rejected": [],
            "commits": [],
            "failure_count": 0,
            "retry_count": 0
        }
