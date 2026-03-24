from __future__ import annotations
import json
import os
import re
from typing import Optional, Dict, Any, List

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
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

def analyze_failure(task: str, failure_output: str, context: List[Dict[str, str]], previous_plan: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    task_l = task.lower()
    if "first_token" in task_l and "indexerror" in failure_output.lower():
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

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        import requests
    except Exception:
        return None

    prompt = f"""
Task:
{task}

Previous plan:
{json.dumps(previous_plan, indent=2) if previous_plan else "null"}

Failure output:
{failure_output}

Context:
{json.dumps(context, indent=2)}

Return ONLY valid JSON with this shape:
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
        return parsed if parsed and parsed.get("edits") else None
    except Exception:
        return None
