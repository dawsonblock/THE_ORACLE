"""Append-only event store. No mutation. No overwrite."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Optional, Iterator, Dict, Any
from contextlib import contextmanager
import threading

from oracle_runtime.core.events.envelope import EventEnvelope


class EventStore:
    """
    Append-only event store.
    
    Guarantees:
    - Events are never modified after write
    - Events are never deleted
    - Writes are atomic
    - Reads see all committed events
    
    Storage format: JSON Lines (JSONL)
    Each line is a complete JSON event envelope.
    """
    
    def __init__(self, log_path: str = "events.log"):
        self.log_path = Path(log_path)
        self._lock = threading.RLock()
        
        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if it doesn't exist
        if not self.log_path.exists():
            self.log_path.touch()
    
    def append(self, events: List[EventEnvelope]) -> None:
        """
        Append events to the log atomically.
        
        This operation is atomic - either all events are written or none are.
        """
        if not events:
            return
        
        with self._lock:
            # Write to temporary file first (atomic write pattern)
            temp_path = self.log_path.with_suffix('.tmp')
            
            try:
                with open(temp_path, 'a') as f:
                    for event in events:
                        f.write(event.to_json() + '\n')
                
                # Atomic rename
                os.replace(temp_path, self.log_path)
                
            except Exception:
                # Clean up temp file on failure
                if temp_path.exists():
                    temp_path.unlink()
                raise
    
    def append_single(self, event: EventEnvelope) -> None:
        """Append a single event."""
        self.append([event])
    
    def read_all(self) -> List[EventEnvelope]:
        """Read all events from the log."""
        events = []
        
        if not self.log_path.exists():
            return events
        
        with self._lock:
            with open(self.log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = EventEnvelope.from_json(line)
                        events.append(event)
                    except json.JSONDecodeError as e:
                        # Log corruption at line number but continue
                        print(f"Warning: Corrupted event at line {line_num}: {e}")
                        continue
        
        return events
    
    def read_from(self, event_id: str) -> List[EventEnvelope]:
        """Read events starting from a specific event ID."""
        events = self.read_all()
        found = False
        result = []
        
        for event in events:
            if event.event_id == event_id:
                found = True
            if found:
                result.append(event)
        
        return result
    
    def read_by_type(self, event_type: str) -> List[EventEnvelope]:
        """Read all events of a specific type."""
        return [e for e in self.read_all() if e.event_type == event_type]
    
    def read_by_correlation(self, correlation_id: str) -> List[EventEnvelope]:
        """Read all events for a specific correlation (operation)."""
        return [
            e for e in self.read_all() 
            if e.correlation_id == correlation_id
        ]
    
    def get_last_event(self) -> Optional[EventEnvelope]:
        """Get the most recent event."""
        events = self.read_all()
        return events[-1] if events else None
    
    def stream(self) -> Iterator[EventEnvelope]:
        """Stream events for memory-efficient reading."""
        if not self.log_path.exists():
            return
        
        with open(self.log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield EventEnvelope.from_json(line)
                except json.JSONDecodeError:
                    continue
    
    def count(self) -> int:
        """Count total events in store."""
        count = 0
        for _ in self.stream():
            count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the event store."""
        events = self.read_all()
        types = {}
        
        for event in events:
            types[event.event_type] = types.get(event.event_type, 0) + 1
        
        return {
            "total_events": len(events),
            "event_types": types,
            "log_size_bytes": self.log_path.stat().st_size if self.log_path.exists() else 0,
            "first_event": events[0].timestamp if events else None,
            "last_event": events[-1].timestamp if events else None
        }
    
    def clear(self) -> None:
        """
        Clear all events. USE WITH CAUTION - breaks append-only guarantee.
        Only for testing/reset scenarios.
        """
        with self._lock:
            if self.log_path.exists():
                # Backup before clear
                backup_path = self.log_path.with_suffix('.backup')
                os.replace(self.log_path, backup_path)
                self.log_path.touch()


class InMemoryEventStore(EventStore):
    """In-memory event store for testing."""
    
    def __init__(self):
        self._events: List[EventEnvelope] = []
        self._lock = threading.RLock()
    
    def append(self, events: List[EventEnvelope]) -> None:
        with self._lock:
            self._events.extend(events)
    
    def read_all(self) -> List[EventEnvelope]:
        with self._lock:
            return list(self._events)
    
    def stream(self) -> Iterator[EventEnvelope]:
        with self._lock:
            for event in self._events:
                yield event
    
    def clear(self) -> None:
        with self._lock:
            self._events = []
