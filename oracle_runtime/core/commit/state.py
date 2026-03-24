"""State management for projections."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import fcntl


class StateManager:
    """
    Manages the projected state.
    
    Guarantees:
    - Atomic reads and writes
    - Concurrent access safety
    - Persistent storage
    """
    
    def __init__(self, state_path: str = "state.json"):
        self.state_path = Path(state_path)
        self._lock = threading.RLock()
        
        # Ensure directory exists
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """Load state from disk."""
        with self._lock:
            if not self.state_path.exists():
                return self._empty_state()
            
            try:
                with open(self.state_path, 'r') as f:
                    # File locking for concurrent access
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        content = f.read()
                        if not content:
                            return self._empty_state()
                        return json.loads(content)
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (json.JSONDecodeError, IOError):
                return self._empty_state()
    
    def save(self, state: Dict[str, Any]) -> None:
        """Save state to disk atomically."""
        with self._lock:
            # Write to temp file first
            temp_path = self.state_path.with_suffix('.tmp')
            
            try:
                with open(temp_path, 'w') as f:
                    # Exclusive lock during write
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        json.dump(state, f, indent=2, default=str)
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
                # Atomic rename
                os.replace(temp_path, self.state_path)
                
            except Exception:
                # Clean up temp file on failure
                if temp_path.exists():
                    temp_path.unlink()
                raise
    
    def _empty_state(self) -> Dict[str, Any]:
        """Return empty state structure."""
        from oracle_runtime.core.commit.reducer import StateReducer
        return StateReducer.get_initial_state()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the state."""
        state = self.load()
        return {
            "state_version": state.get("version", 0),
            "event_count": state.get("event_count", 0),
            "execution_count": len(state.get("executions", [])),
            "pending_approvals": len(state.get("pending_approvals", [])),
            "total_approved": len(state.get("approved", [])),
            "total_rejected": len(state.get("rejected", [])),
            "total_commits": len(state.get("commits", [])),
            "failure_count": state.get("failure_count", 0),
            "retry_count": state.get("retry_count", 0),
            "file_size_bytes": self.state_path.stat().st_size if self.state_path.exists() else 0
        }
    
    def clear(self) -> None:
        """Clear state (use with caution)."""
        with self._lock:
            if self.state_path.exists():
                backup_path = self.state_path.with_suffix('.backup')
                os.replace(self.state_path, backup_path)
            self.save(self._empty_state())


class InMemoryStateManager(StateManager):
    """In-memory state manager for testing."""
    
    def __init__(self, state_path: str = None):
        self._state: Dict[str, Any] = self._empty_state()
        self._lock = threading.RLock()
    
    def load(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)
    
    def save(self, state: Dict[str, Any]) -> None:
        with self._lock:
            self._state = dict(state)
    
    def clear(self) -> None:
        with self._lock:
            self._state = self._empty_state()
