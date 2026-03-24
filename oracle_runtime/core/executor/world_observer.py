"""World state observer - captures system state before and after execution."""
from __future__ import annotations
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class FileState:
    """State of a single file."""
    path: str
    content_hash: str
    exists: bool
    size: int = 0


@dataclass
class WorldState:
    """
    Complete world state snapshot.
    
    Captures:
    - Git state (branch, status, HEAD)
    - File states (hashes for files of interest)
    - Working directory
    """
    git_branch: str
    git_status: str
    git_head: str
    working_dir: str
    file_states: List[FileState]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def get_file_hash(self, path: str) -> Optional[str]:
        """Get hash of a specific file at this state."""
        for fs in self.file_states:
            if fs.path == path:
                return fs.content_hash
        return None
    
    def has_changes(self, other: WorldState) -> bool:
        """Check if this state has changes compared to another."""
        if len(self.file_states) != len(other.file_states):
            return True
        
        self_hashes = {fs.path: fs.content_hash for fs in self.file_states}
        other_hashes = {fs.path: fs.content_hash for fs in other.file_states}
        
        return self_hashes != other_hashes


class WorldObserver:
    """
    Observes and captures world state.
    
    Used by VerifiedExecutor to:
    1. Capture pre-state before execution
    2. Capture post-state after execution
    3. Compare states to verify changes
    """
    
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
    
    def observe(self, files_of_interest: Optional[List[str]] = None) -> WorldState:
        """
        Capture current world state.
        
        Args:
            files_of_interest: Specific files to track. If None, tracks git-tracked files.
        
        Returns:
            WorldState snapshot
        """
        import datetime
        
        # Git state
        git_branch = self._run_git_command(["branch", "--show-current"]) or "unknown"
        git_status = self._run_git_command(["status", "--porcelain"]) or ""
        git_head = self._run_git_command(["rev-parse", "HEAD"]) or "unknown"
        
        # File states
        if files_of_interest:
            file_states = self._observe_files(files_of_interest)
        else:
            # Get files from git status
            files = self._get_git_files()
            file_states = self._observe_files(files)
        
        return WorldState(
            git_branch=git_branch,
            git_status=git_status,
            git_head=git_head,
            working_dir=str(self.working_dir),
            file_states=file_states,
            timestamp=datetime.datetime.now().isoformat()
        )
    
    def _run_git_command(self, args: List[str]) -> Optional[str]:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    def _get_git_files(self) -> List[str]:
        """Get list of files from git status."""
        files = []
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        # Parse git status line (XY filename)
                        filename = line[3:].strip()
                        files.append(filename)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return files
    
    def _observe_files(self, files: List[str]) -> List[FileState]:
        """Observe specific files and capture their state."""
        states = []
        
        for file_path in files:
            full_path = self.working_dir / file_path
            
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_bytes()
                    content_hash = hashlib.sha256(content).hexdigest()[:16]
                    states.append(FileState(
                        path=file_path,
                        content_hash=content_hash,
                        exists=True,
                        size=len(content)
                    ))
                except (IOError, OSError):
                    states.append(FileState(
                        path=file_path,
                        content_hash="",
                        exists=False,
                        size=0
                    ))
            else:
                states.append(FileState(
                    path=file_path,
                    content_hash="",
                    exists=False,
                    size=0
                ))
        
        return states
    
    def observe_single_file(self, file_path: str) -> FileState:
        """Observe a single file."""
        full_path = self.working_dir / file_path
        
        if full_path.exists() and full_path.is_file():
            try:
                content = full_path.read_bytes()
                content_hash = hashlib.sha256(content).hexdigest()[:16]
                return FileState(
                    path=file_path,
                    content_hash=content_hash,
                    exists=True,
                    size=len(content)
                )
            except (IOError, OSError):
                pass
        
        return FileState(
            path=file_path,
            content_hash="",
            exists=False,
            size=0
        )
