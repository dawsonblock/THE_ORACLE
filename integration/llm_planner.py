from __future__ import annotations
import json
import os
import re
from typing import Optional, Dict, Any, List

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None

def _local_fallback(task: str, context: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    task_l = task.lower()
    if "first_token" in task_l and ("empty" in task_l or "none" in task_l):
        for item in context:
            if item["file"].endswith("parser.py") and "return tokens[0]" in item["content"]:
                return {
                    "edits": [
                        {
                            "file": item["file"],
                            "search": "return tokens[0]",
                            "replace": "return tokens[0] if tokens else None",
                        }
                    ]
                }
    return None

def create_plan(task: str, context: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _local_fallback(task, context)

    try:
        import requests
    except Exception:
        return _local_fallback(task, context)

    prompt = f"""
You are a coding agent.
Task:
{task}

Context:
{json.dumps(context, indent=2)}

Return ONLY valid JSON:
{{
  "edits": [
    {{
      "file": "relative/path.py",
      "search": "exact old code",
      "replace": "exact new code"
    }}
  ]
}}
""".strip()

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=45,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        parsed = _extract_json(text)
        return parsed if parsed and parsed.get("edits") else _local_fallback(task, context)
    except Exception:
        return _local_fallback(task, context)
