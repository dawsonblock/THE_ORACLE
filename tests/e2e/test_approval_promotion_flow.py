"""Real approval/promotion flow E2E tests."""

from fastapi.testclient import TestClient
from scripts.serve_coding_runs import app
import json

client = TestClient(app)


def test_full_approval_promotion_flow(tmp_path):
    """Test the full approval flow:
    1. Create a repo with a bug
    2. Run the pipeline
    3. Verify status is awaiting_approval
    4. Approve the run
    5. Verify receipt exists
    6. Verify final state is applied
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    
    # Create buggy file
    (repo / "parser.py").write_text(
        "def first_token(tokens):\n    return tokens[0]\n",
        encoding="utf-8",
    )
    
    # Create test
    (repo / "test_parser.py").write_text(
        "from parser import first_token\n"
        "def test_empty(): assert first_token([]) is None\n",
        encoding="utf-8",
    )
    
    # Step 1: Run the pipeline
    resp = client.post("/run", json={
        "task": "fix first_token so empty list returns None",
        "repo_path": str(repo),
    })
    assert resp.status_code == 200
    
    run = resp.json()
    run_id = run["run_id"]
    
    # Step 2: Verify status is awaiting_approval
    assert run["status"] == "awaiting_approval"
    
    # Step 3: Get run details
    resp = client.get(f"/runs/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "awaiting_approval"
    
    # Step 4: Approve the run
    resp = client.post(f"/runs/{run_id}/approve", json={
        "actor": "test_operator",
        "note": "LGTM",
    })
    assert resp.status_code == 200
    
    result = resp.json()
    
    # Step 5: Verify run is now applied
    assert result["run"]["status"] == "applied"
    assert result["run"]["approved_by"] == "test_operator"
    assert "approved_at" in result["run"]
    
    # Step 6: Verify receipt exists
    assert result["receipt"]["decision"] == "approved"
    assert result["receipt"]["actor"] == "test_operator"
    assert result["receipt"]["note"] == "LGTM"
    assert "timestamp" in result["receipt"]
    
    # Step 7: Get receipt via endpoint
    resp = client.get(f"/runs/{run_id}/receipt")
    assert resp.status_code == 200
    receipt = resp.json()
    assert receipt["decision"] == "approved"
    
    # Step 8: Verify file was actually changed
    content = (repo / "parser.py").read_text(encoding="utf-8")
    assert "if tokens else None" in content


def test_reject_flow(tmp_path):
    """Test the reject flow."""
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
    
    # Run pipeline
    resp = client.post("/run", json={
        "task": "fix first_token so empty list returns None",
        "repo_path": str(repo),
    })
    run_id = resp.json()["run_id"]
    
    # Reject the run
    resp = client.post(f"/runs/{run_id}/reject", json={
        "actor": "test_operator",
        "note": "Doesn't look right",
    })
    assert resp.status_code == 200
    
    result = resp.json()
    assert result["run"]["status"] == "rejected"
    assert result["receipt"]["decision"] == "rejected"


def test_approve_already_applied_fails(tmp_path):
    """Test that approving an already applied run fails."""
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
    
    # Run and approve
    resp = client.post("/run", json={
        "task": "fix first_token so empty list returns None",
        "repo_path": str(repo),
    })
    run_id = resp.json()["run_id"]
    
    client.post(f"/runs/{run_id}/approve", json={})
    
    # Try to approve again
    resp = client.post(f"/runs/{run_id}/approve", json={})
    assert resp.status_code == 400
    assert "not in awaiting_approval state" in resp.json()["detail"]


def test_approve_nonexistent_run_fails():
    """Test that approving a nonexistent run fails."""
    resp = client.post("/runs/nonexistent/approve", json={})
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]
