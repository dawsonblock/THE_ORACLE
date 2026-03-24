from integration.llm_planner import create_plan

def test_local_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    context = [
        {
            "file": "parser.py",
            "content": "def first_token(tokens):\n    return tokens[0]\n",
        }
    ]

    plan = create_plan("fix first_token so empty list returns None", context)
    assert plan is not None
    assert plan["edits"][0]["file"] == "parser.py"
    assert "tokens else None" in plan["edits"][0]["replace"]
