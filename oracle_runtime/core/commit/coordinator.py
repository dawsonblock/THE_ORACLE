"""Commit coordinator - manages event append + state reduction."""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import uuid

from oracle_runtime.core.events.event_store import EventStore, InMemoryEventStore
from oracle_runtime.core.events.envelope import EventEnvelope
from oracle_runtime.core.commit.state import StateManager, InMemoryStateManager
from oracle_runtime.core.commit.reducer import StateReducer


class CommitCoordinator:
    """
    Coordinates the commit of events to the event store
    and updates the projected state.
    
    This is the single point of coordination between:
    - Event store (append-only log)
    - State projection (reduced view)
    
    Guarantees:
    - Events are persisted before state is updated
    - State is always derived from events
    - Failed state updates don't lose events
    """
    
    def __init__(
        self,
        event_store: Optional[EventStore] = None,
        state_manager: Optional[StateManager] = None,
        reducer: Optional[StateReducer] = None
    ):
        self.event_store = event_store or EventStore()
        self.state_manager = state_manager or StateManager()
        self.reducer = reducer or StateReducer()
    
    def commit(self, events: List[EventEnvelope]) -> CommitResult:
        """
        Commit events to the event store and update state.
        
        Steps:
        1. Append events to event store (durable)
        2. Load current state
        3. Apply reducer to get new state
        4. Save new state
        
        Returns:
            CommitResult with status and details
        """
        if not events:
            return CommitResult.success([], "No events to commit")
        
        correlation_id = events[0].correlation_id or str(uuid.uuid4())
        
        try:
            # Step 1: Append events to event store
            # This is the durable write - must succeed
            self.event_store.append(events)
            
            # Step 2: Load current state
            state = self.state_manager.load()
            
            # Step 3: Apply reducer for each event
            for event in events:
                state = self.reducer.reduce(state, event.to_dict())
            
            # Step 4: Save new state
            self.state_manager.save(state)
            
            return CommitResult.success(
                [e.event_id for e in events],
                f"Committed {len(events)} events",
                correlation_id=correlation_id,
                state_snapshot=state
            )
            
        except Exception as e:
            # Event store append succeeded but state update failed
            # This is acceptable - state can be rebuilt from events
            return CommitResult.partial(
                [e.event_id for e in events],
                f"Events stored but state update failed: {str(e)}",
                correlation_id=correlation_id
            )
    
    def rebuild_state(self) -> Dict[str, Any]:
        """
        Rebuild state from all events in the event store.
        
        Use this for:
        - Recovery after state corruption
        - Migration to new state format
        - Verification that state matches events
        """
        # Read all events
        events = self.event_store.read_all()
        
        # Start from initial state
        state = StateReducer.get_initial_state()
        
        # Apply all events
        for event in events:
            state = self.reducer.reduce(state, event.to_dict())
        
        # Save rebuilt state
        self.state_manager.save(state)
        
        return state
    
    def verify_consistency(self) -> ConsistencyReport:
        """
        Verify that current state is consistent with event log.
        
        Returns report of any inconsistencies.
        """
        # Build expected state from events
        events = self.event_store.read_all()
        expected_state = StateReducer.reduce_all(
            [e.to_dict() for e in events],
            StateReducer.get_initial_state()
        )
        
        # Get actual state
        actual_state = self.state_manager.load()
        
        # Compare
        differences = self._find_differences(expected_state, actual_state)
        
        return ConsistencyReport(
            consistent=len(differences) == 0,
            event_count=len(events),
            differences=differences
        )
    
    def _find_differences(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        path: str = ""
    ) -> List[str]:
        """Find differences between expected and actual state."""
        differences = []
        
        for key in set(expected.keys()) | set(actual.keys()):
            current_path = f"{path}.{key}" if path else key
            
            if key not in expected:
                differences.append(f"{current_path}: extra in actual")
            elif key not in actual:
                differences.append(f"{current_path}: missing in actual")
            elif isinstance(expected[key], dict) and isinstance(actual[key], dict):
                differences.extend(self._find_differences(
                    expected[key], actual[key], current_path
                ))
            elif expected[key] != actual[key]:
                differences.append(f"{current_path}: {expected[key]} != {actual[key]}")
        
        return differences


class CommitResult:
    """Result of a commit operation."""
    
    def __init__(
        self,
        success: bool,
        event_ids: List[str],
        message: str,
        correlation_id: Optional[str] = None,
        state_snapshot: Optional[Dict[str, Any]] = None,
        partial: bool = False
    ):
        self.success = success
        self.event_ids = event_ids
        self.message = message
        self.correlation_id = correlation_id
        self.state_snapshot = state_snapshot
        self.partial = partial
    
    @classmethod
    def success(
        cls,
        event_ids: List[str],
        message: str,
        correlation_id: Optional[str] = None,
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> CommitResult:
        return cls(
            success=True,
            event_ids=event_ids,
            message=message,
            correlation_id=correlation_id,
            state_snapshot=state_snapshot
        )
    
    @classmethod
    def partial(
        cls,
        event_ids: List[str],
        message: str,
        correlation_id: Optional[str] = None
    ) -> CommitResult:
        return cls(
            success=True,  # Events were stored
            event_ids=event_ids,
            message=message,
            correlation_id=correlation_id,
            partial=True
        )
    
    @classmethod
    def failure(
        cls,
        message: str,
        correlation_id: Optional[str] = None
    ) -> CommitResult:
        return cls(
            success=False,
            event_ids=[],
            message=message,
            correlation_id=correlation_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "partial": self.partial,
            "event_count": len(self.event_ids),
            "message": self.message,
            "correlation_id": self.correlation_id
        }


class ConsistencyReport:
    """Report on state/event store consistency."""
    
    def __init__(
        self,
        consistent: bool,
        event_count: int,
        differences: List[str]
    ):
        self.consistent = consistent
        self.event_count = event_count
        self.differences = differences
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "consistent": self.consistent,
            "event_count": self.event_count,
            "differences": self.differences,
            "difference_count": len(self.differences)
        }


# Factory for in-memory coordinator (testing)
def create_in_memory_coordinator() -> CommitCoordinator:
    """Create a coordinator with in-memory storage for testing."""
    return CommitCoordinator(
        event_store=InMemoryEventStore(),
        state_manager=InMemoryStateManager()
    )
