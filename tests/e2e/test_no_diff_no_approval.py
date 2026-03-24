"""Negative control: no diff means no approval record."""

from fastapi.testclient import TestClient
from scripts.serve_coding_runs import app
from integration.patch_executor import apply_plan

client = TestClient(app)


def test_no_edits_rejected(tmp_path):
    """Empty edits should be rejected at patch executor level."""
    result = apply_plan({"edits": []}, str(tmp_path))
    assert result["success"] is False
    assert result["reason"] == "no_edits"


def test_pipeline_failure_no_approval_state(tmp_path):
    """When pipeline fails, no approval state should be created."""
    repo = tmp_path / "repo"
    repo.mkdir()
    
    # Create a file that will cause tests to fail
    (repo / "parser.py").write_text(
        "def first_token(tokens):\n    return tokens[0]\n",
        encoding="utf-8",
    )
    
    # Create a test that will fail (expects None but gets IndexError)
    (repo / "test_parser.py").write_text(
        "from parser import first_token\n"
        "def test_empty(): assert first_token([]) is None\n",
        encoding="utf-8",
    )
    
    # Run with a task that won't match the fallback
    resp = client.post("/run", json={
        "task": "some unrelated task that won't match any fix pattern",
        "repo_path": str(repo),
    })
    
    assert resp.status_code == 200
    run = resp.json()
    
    # Should be failed, not awaiting_approval
    assert run["status"] == "failed"
    
    # No receipt should exist
    resp = client.get(f"/runs/{run['run_id']}/receipt")
    assert resp.status_code == 404


def test_missing_file_in_plan_fails(tmp_path):
    """Plan referencing missing file should fail gracefully."""
    result = apply_plan({
        "edits": [{"file": "nonexistent.py", "search": "x", "replace": "y"}]
    }, str(tmp_path))
    
    assert result["success"] is False
    assert "file_not_found" in result["reason"]


def test_search_not_found_fails(tmp_path):
    """Plan with non-matching search should fail gracefully."""
    repo = tmp_path
    (repo / "test.py").write_text("x = 1\n", encoding="utf-8")
    
    result = apply_plan({
        "edits": [{"file": "test.py", "search": "y = 2", "replace": "z = 3"}]
    }, str(repo))
    
    assert result["success"] is False
    assert "search_not_found" in result["reason"]
