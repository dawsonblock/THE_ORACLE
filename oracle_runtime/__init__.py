"""
THE_ORACLE - Single Coherent System

A controlled, testable, safe coding agent.

Execution Spine:
    Intent → Planner (read-only) → Command → Verified Executor → Events → Commit → Projections

All code modifications flow through one executor.
All state changes are events.
All commits require approval.
"""

__version__ = "2.0.0"

from oracle_runtime.core.intent.intent_api import IntentAPI, IntentResult, submit_intent
from oracle_runtime.core.executor.verified_executor import VerifiedExecutor, get_executor
from oracle_runtime.core.command.patch_command import PatchCommand, ExecutionOutcome
from oracle_runtime.core.events.event_store import EventStore
from oracle_runtime.core.commit.coordinator import CommitCoordinator

__all__ = [
    "IntentAPI",
    "IntentResult", 
    "submit_intent",
    "VerifiedExecutor",
    "get_executor",
    "PatchCommand",
    "ExecutionOutcome",
    "EventStore",
    "CommitCoordinator",
]
