from integration.context_builder import build_context

def test_prefers_parser_and_test(tmp_path):
    repo = tmp_path
    (repo / "parser.py").write_text("def first_token(tokens):\n    return tokens[0]\n", encoding="utf-8")
    (repo / "test_parser.py").write_text("from parser import first_token\n", encoding="utf-8")
    (repo / "other.py").write_text("def unrelated():\n    pass\n", encoding="utf-8")

    ctx = build_context(str(repo), "fix first_token empty list", max_files=3)
    files = [c["file"] for c in ctx]

    assert "parser.py" in files
    assert "test_parser.py" in files
    assert all(not f.startswith("/") for f in files)

def test_deterministic_order(tmp_path):
    repo = tmp_path
    (repo / "a.py").write_text("def a(): pass\n", encoding="utf-8")
    (repo / "b.py").write_text("def b(): pass\n", encoding="utf-8")

    c1 = build_context(str(repo), "fix a", max_files=2)
    c2 = build_context(str(repo), "fix a", max_files=2)
    assert c1 == c2
