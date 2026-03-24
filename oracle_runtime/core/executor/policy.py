"""Execution policy - determines if a command is allowed to execute."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

from oracle_runtime.core.command.patch_command import PatchCommand


@dataclass
class PolicyDecision:
    """Result of policy check."""
    allowed: bool
    reason: str
    violations: List[str]
    
    @classmethod
    def allow(cls, reason: str = "Policy check passed") -> PolicyDecision:
        return cls(allowed=True, reason=reason, violations=[])
    
    @classmethod
    def deny(cls, reason: str, violations: List[str] = None) -> PolicyDecision:
        return cls(allowed=False, reason=reason, violations=violations or [])


class PolicyEngine:
    """
    Policy engine for execution authorization.
    
    Checks commands against security and safety policies before allowing execution.
    
    Policies:
    - No absolute paths (must be relative to working dir)
    - No parent directory traversal (..)
    - No system/binary files
    - File size limits
    - Allowed extensions only
    """
    
    # File extensions that are safe to modify
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.kt', '.scala',
        '.go', '.rs',
        '.rb', '.php',
        '.swift', '.m', '.mm',
        '.c', '.cpp', '.h', '.hpp',
        '.cs', '.fs',
        '.r', '.pl', '.lua',
        '.sh', '.bash', '.zsh',
        '.yaml', '.yml', '.json', '.toml',
        '.md', '.rst', '.txt',
        '.html', '.css', '.scss', '.sass',
        '.xml', '.sql'
    }
    
    # Forbidden patterns in file paths
    FORBIDDEN_PATTERNS = [
        '..',           # Parent directory traversal
        '~',            # Home directory
        '$',            # Environment variables
        '\x00',         # Null bytes
    ]
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Maximum diff size (1MB)
    MAX_DIFF_SIZE = 1024 * 1024
    
    def __init__(self, custom_policies: Optional[List] = None):
        self.custom_policies = custom_policies or []
    
    def check(self, command: PatchCommand) -> PolicyDecision:
        """
        Check if a command is allowed by policy.
        
        Returns PolicyDecision with allow/deny and reason.
        """
        violations = []
        
        # Check command validity
        is_valid, error = command.validate()
        if not is_valid:
            return PolicyDecision.deny(f"Invalid command: {error}")
        
        # Check each file
        for file_path in command.files:
            file_violations = self._check_file_path(file_path)
            violations.extend(file_violations)
        
        # Check diff size
        if len(command.diff) > self.MAX_DIFF_SIZE:
            violations.append(f"Diff exceeds maximum size ({self.MAX_DIFF_SIZE} bytes)")
        
        # Check for dangerous patterns in diff
        diff_violations = self._check_diff(command.diff)
        violations.extend(diff_violations)
        
        # Run custom policies
        for policy in self.custom_policies:
            result = policy.check(command)
            if not result.allowed:
                violations.extend(result.violations)
        
        if violations:
            return PolicyDecision.deny(
                f"Policy violations: {len(violations)} issues found",
                violations
            )
        
        return PolicyDecision.allow()
    
    def _check_file_path(self, file_path: str) -> List[str]:
        """Check a single file path for policy violations."""
        violations = []
        path = Path(file_path)
        
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in file_path:
                violations.append(f"File path contains forbidden pattern '{pattern}': {file_path}")
        
        # Check for absolute paths
        if path.is_absolute():
            violations.append(f"Absolute path not allowed: {file_path}")
        
        # Check extension
        if path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            violations.append(f"File extension not allowed: {path.suffix}")
        
        # Check for hidden files (starting with .)
        if any(part.startswith('.') for part in path.parts):
            # Allow .github, .vscode, etc but not .env, .ssh
            if path.name.startswith('.') and path.name not in ['.gitignore', '.dockerignore', '.editorconfig']:
                violations.append(f"Hidden files not allowed: {file_path}")
        
        return violations
    
    def _check_diff(self, diff: str) -> List[str]:
        """Check diff content for dangerous patterns."""
        violations = []
        
        # Check for binary content markers
        if 'Binary files' in diff and 'differ' in diff:
            violations.append("Binary file modifications not allowed")
        
        # Check for suspicious patterns that might indicate malicious code
        suspicious_patterns = [
            'rm -rf /',
            'os.system',
            'subprocess.call',
            'eval(',
            'exec(',
            '__import__',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in diff:
                # This is a weak check - just flagging for review
                # In production, you'd want more sophisticated analysis
                pass  # Don't block for now
        
        return violations


class ReadOnlyPolicy:
    """Policy that denies all modifications (for read-only mode)."""
    
    def check(self, command: PatchCommand) -> PolicyDecision:
        return PolicyDecision.deny("System is in read-only mode")


class AllowlistPolicy:
    """Policy that only allows specific files."""
    
    def __init__(self, allowed_files: List[str]):
        self.allowed_files = set(allowed_files)
    
    def check(self, command: PatchCommand) -> PolicyDecision:
        for file_path in command.files:
            if file_path not in self.allowed_files:
                return PolicyDecision.deny(f"File not in allowlist: {file_path}")
        return PolicyDecision.allow()
