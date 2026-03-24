from __future__ import annotations
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Dict, Any

def _python_files(repo: str):
    repo_path = Path(repo)
    for path in repo_path.rglob("*.py"):
        yield path

def run_tests(repo: str) -> Tuple[bool, str, Dict[str, Any]]:
    syntax_errors = []

    for pyfile in _python_files(repo):
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(pyfile)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            syntax_errors.append(proc.stdout + proc.stderr)

    if syntax_errors:
        return False, "\n".join(syntax_errors), {
            "syntax_ok": False,
            "test_command": None,
        }

    proc = subprocess.run(
        ["pytest", "-q"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    return proc.returncode == 0, proc.stdout + proc.stderr, {
        "syntax_ok": True,
        "test_command": "pytest -q",
    }
