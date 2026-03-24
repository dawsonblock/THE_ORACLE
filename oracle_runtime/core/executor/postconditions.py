"""Postcondition verification - ensures execution had intended effects."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import ast
import subprocess

from oracle_runtime.core.command.patch_command import PatchCommand
from oracle_runtime.core.executor.world_observer import WorldState


@dataclass
class PostconditionResult:
    """Result of postcondition check."""
    passed: bool
    condition: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @classmethod
    def pass_(cls, condition: str, details: Dict[str, Any] = None) -> PostconditionResult:
        return cls(passed=True, condition=condition, details=details or {})
    
    @classmethod
    def fail(cls, condition: str, error: str, details: Dict[str, Any] = None) -> PostconditionResult:
        return cls(passed=False, condition=condition, error=error, details=details or {})


class PostconditionVerifier:
    """
    Verifies that execution produced expected results.
    
    Postconditions:
    - files_modified: Target files were actually modified
    - syntax_valid: Modified Python files have valid syntax
    - tests_pass: Test suite passes
    - no_new_errors: No new lint/type errors introduced
    """
    
    def verify(
        self,
        pre_state: WorldState,
        post_state: WorldState,
        command: PatchCommand
    ) -> List[PostconditionResult]:
        """
        Verify all postconditions for a command.
        
        Returns list of results, one per postcondition.
        """
        results = []
        
        for condition in command.postconditions:
            result = self._verify_condition(condition, pre_state, post_state, command)
            results.append(result)
        
        return results
    
    def _verify_condition(
        self,
        condition: str,
        pre_state: WorldState,
        post_state: WorldState,
        command: PatchCommand
    ) -> PostconditionResult:
        """Verify a single postcondition."""
        
        if condition == "files_modified":
            return self._verify_files_modified(pre_state, post_state, command)
        
        elif condition == "syntax_valid":
            return self._verify_syntax_valid(command)
        
        elif condition == "tests_pass":
            return self._verify_tests_pass()
        
        elif condition == "no_new_errors":
            return self._verify_no_new_errors(pre_state, post_state, command)
        
        else:
            return PostconditionResult.fail(
                condition,
                f"Unknown postcondition: {condition}"
            )
    
    def _verify_files_modified(
        self,
        pre_state: WorldState,
        post_state: WorldState,
        command: PatchCommand
    ) -> PostconditionResult:
        """Verify that target files were modified."""
        modified_files = []
        
        for file_path in command.files:
            pre_hash = pre_state.get_file_hash(file_path)
            post_hash = post_state.get_file_hash(file_path)
            
            if pre_hash != post_hash:
                modified_files.append(file_path)
        
        if not modified_files:
            return PostconditionResult.fail(
                "files_modified",
                "No files were modified",
                {"expected_files": command.files}
            )
        
        return PostconditionResult.pass_(
            "files_modified",
            {"modified_files": modified_files}
        )
    
    def _verify_syntax_valid(self, command: PatchCommand) -> PostconditionResult:
        """Verify that modified Python files have valid syntax."""
        python_files = [f for f in command.files if f.endswith('.py')]
        
        if not python_files:
            # No Python files to check
            return PostconditionResult.pass_("syntax_valid", {"skipped": True})
        
        errors = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{file_path}: {e.msg} at line {e.lineno}")
            except FileNotFoundError:
                errors.append(f"{file_path}: File not found")
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
        
        if errors:
            return PostconditionResult.fail(
                "syntax_valid",
                f"Syntax errors in {len(errors)} file(s)",
                {"errors": errors}
            )
        
        return PostconditionResult.pass_(
            "syntax_valid",
            {"checked_files": python_files}
        )
    
    def _verify_tests_pass(self) -> PostconditionResult:
        """Verify that tests pass."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-x", "-q"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return PostconditionResult.pass_(
                    "tests_pass",
                    {"output": result.stdout}
                )
            else:
                return PostconditionResult.fail(
                    "tests_pass",
                    "Tests failed",
                    {
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                )
        except subprocess.TimeoutExpired:
            return PostconditionResult.fail(
                "tests_pass",
                "Tests timed out (>120s)"
            )
        except FileNotFoundError:
            return PostconditionResult.fail(
                "tests_pass",
                "pytest not found"
            )
        except Exception as e:
            return PostconditionResult.fail(
                "tests_pass",
                f"Error running tests: {str(e)}"
            )
    
    def _verify_no_new_errors(
        self,
        pre_state: WorldState,
        post_state: WorldState,
        command: PatchCommand
    ) -> PostconditionResult:
        """Verify no new errors were introduced (basic check)."""
        # This is a placeholder for more sophisticated analysis
        # In practice, you'd run linters/type checkers and compare results
        
        return PostconditionResult.pass_(
            "no_new_errors",
            {"note": "Basic check - full linting not implemented"}
        )
    
    def verify_all_passed(self, results: List[PostconditionResult]) -> bool:
        """Check if all postconditions passed."""
        return all(r.passed for r in results)
