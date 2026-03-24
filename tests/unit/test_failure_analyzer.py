from integration.failure_analyzer import analyze_failure

def test_failure_analyzer_returns_plan_shape(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    context = [
        {
            "file": "parser.py",
            "content": "def first_token(tokens):\n    return tokens[0]\n",
        }
    ]

    plan = analyze_failure(
        "fix first_token so empty list returns None",
        "IndexError: list index out of range",
        context,
        previous_plan=None,
    )

    assert plan is not None
    assert "edits" in plan
    assert plan["edits"][0]["file"] == "parser.py"
