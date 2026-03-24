from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import re

def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.lower()))

def build_context(repo: str, task: str, max_files: int = 8, max_chars: int = 1800) -> List[Dict[str, str]]:
    repo_path = Path(repo)
    task_tokens = _tokens(task)
    candidates = []

    for path in repo_path.rglob("*.py"):
        rel = path.relative_to(repo_path).as_posix()
        score = 0

        rel_tokens = _tokens(rel)
        score += len(task_tokens & rel_tokens) * 5

        if "test" in rel.lower():
            score += 1

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        content_tokens = _tokens(content[:4000])
        score += len(task_tokens & content_tokens) * 2

        candidates.append((score, rel, content))

    candidates.sort(key=lambda x: (-x[0], x[1]))

    selected = []
    for _, rel, content in candidates[:max_files]:
        selected.append({
            "file": rel,
            "content": content[:max_chars],
        })

    return selected
