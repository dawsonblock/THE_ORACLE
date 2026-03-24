from integration.pipeline import run_pipeline

def test_full_pipeline(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "parser.py").write_text(
        "def first_token(tokens):\n    return tokens[0]\n",
        encoding="utf-8",
    )

    (repo / "test_parser.py").write_text(
        "from parser import first_token\n"
        "def test_empty(): assert first_token([]) is None\n",
        encoding="utf-8",
    )

    result = run_pipeline(
        "fix first_token so empty list returns None",
        str(repo),
    )

    assert result["status"] == "applied"
    assert result["attempts"] >= 1
    assert "parser.py" in result["files_changed"]

    content = (repo / "parser.py").read_text(encoding="utf-8")
    assert "if tokens else None" in content
