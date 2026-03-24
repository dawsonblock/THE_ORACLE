from integration.patch_executor import apply_plan

def test_single_file_edit(tmp_path):
    repo = tmp_path
    f = repo / "parser.py"
    f.write_text("def x():\n    return 1\n", encoding="utf-8")

    result = apply_plan(
        {"edits": [{"file": "parser.py", "search": "return 1", "replace": "return 2"}]},
        str(repo),
    )

    assert result["success"] is True
    assert "parser.py" in result["files"]
    assert "return 2" in f.read_text(encoding="utf-8")

def test_multi_file_edit(tmp_path):
    repo = tmp_path
    a = repo / "a.py"
    b = repo / "b.py"
    a.write_text("x=1\n", encoding="utf-8")
    b.write_text("y=1\n", encoding="utf-8")

    result = apply_plan(
        {
            "edits": [
                {"file": "a.py", "search": "x=1", "replace": "x=2"},
                {"file": "b.py", "search": "y=1", "replace": "y=2"},
            ]
        },
        str(repo),
    )

    assert result["success"] is True
    assert set(result["files"]) == {"a.py", "b.py"}

def test_missing_file(tmp_path):
    result = apply_plan(
        {"edits": [{"file": "missing.py", "search": "x", "replace": "y"}]},
        str(tmp_path),
    )
    assert result["success"] is False
    assert result["reason"].startswith("file_not_found:")

def test_missing_search_text(tmp_path):
    repo = tmp_path
    f = repo / "a.py"
    f.write_text("x=1\n", encoding="utf-8")

    result = apply_plan(
        {"edits": [{"file": "a.py", "search": "z=1", "replace": "z=2"}]},
        str(repo),
    )
    assert result["success"] is False
    assert result["reason"].startswith("search_not_found:")

def test_empty_edits_rejected(tmp_path):
    result = apply_plan({"edits": []}, str(tmp_path))
    assert result["success"] is False
    assert result["reason"] == "no_edits"
