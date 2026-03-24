from __future__ import annotations
import os
from typing import Dict, List, Any

def apply_plan(plan: Dict[str, Any], repo: str) -> Dict[str, Any]:
    edits = plan.get("edits")
    if not edits:
        return {"success": False, "reason": "no_edits", "files": []}

    changed_files: List[str] = []

    for edit in edits:
        rel_path = edit.get("file")
        search = edit.get("search")
        replace = edit.get("replace")

        if not rel_path:
            return {"success": False, "reason": "missing_file", "files": changed_files}
        if search is None or search == "":
            return {"success": False, "reason": f"empty_search:{rel_path}", "files": changed_files}
        if replace is None:
            return {"success": False, "reason": f"missing_replace:{rel_path}", "files": changed_files}

        abs_path = os.path.join(repo, rel_path)
        if not os.path.exists(abs_path):
            return {"success": False, "reason": f"file_not_found:{rel_path}", "files": changed_files}

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {"success": False, "reason": f"read_error:{rel_path}:{e}", "files": changed_files}

        if search not in content:
            return {"success": False, "reason": f"search_not_found:{rel_path}", "files": changed_files}

        new_content = content.replace(search, replace)

        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            return {"success": False, "reason": f"write_error:{rel_path}:{e}", "files": changed_files}

        if rel_path not in changed_files:
            changed_files.append(rel_path)

    return {"success": True, "reason": None, "files": changed_files}
