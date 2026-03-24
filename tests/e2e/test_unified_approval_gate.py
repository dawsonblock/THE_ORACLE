"""Unified approval/denial gate E2E tests.

This test suite verifies that the /decide endpoint provides a single,
unified path for both approval and rejection, with shared validation logic.
"""

from fastapi.testclient import TestClient
from scripts.serve_coding_runs import app
import json

client = TestClient(app)


def test_unified_gate_approve_success(tmp_path):
    """Test unified gate approves successfully through single path."""
    repo = tmp_path / "repo"
    repo.mkdir()
    
    # Create buggy file
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
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    
    # Use unified gate to approve
    resp = client.post(f"/runs/{run_id}/decide", json={
        "decision": "approved",
        "actor": "test_operator",
        "note": "LGTM",
    })
    assert resp.status_code == 200
    
    result = resp.json()
    
    # Verify unified response structure
    assert result["run"]["status"] == "applied"
    assert result["run"]["approved_by"] == "test_operator"
    assert "approved_at" in result["run"]
    assert result["receipt"]["decision"] == "approved"
    assert result["receipt"]["actor"] == "test_operator"
    assert result["receipt"]["note"] == "LGTM"
    
    # Verify receipt accessible
    resp = client.get(f"/runs/{run_id}/receipt")
    assert resp.status_code == 200
    assert resp.json()["decision"] == "approved"


def test_unified_gate_reject_success(tmp_path):
    """Test unified gate rejects successfully through single path."""
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
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    
    # Use unified gate to reject
    resp = client.post(f"/runs/{run_id}/decide", json={
        "decision": "rejected",
        "actor": "test_reviewer",
        "note": "Doesn't look right",
    })
    assert resp.status_code == 200
    
    result = resp.json()
    
    # Verify unified response structure
    assert result["run"]["status"] == "rejected"
    assert result["run"]["rejected_by"] == "test_reviewer"
    assert "rejected_at" in result["run"]
    assert result["receipt"]["decision"] == "rejected"
    assert result["receipt"]["actor"] == "test_reviewer"
    assert result["receipt"]["note"] == "Doesn't look right"
    
    # Verify receipt accessible
    resp = client.get(f"/runs/{run_id}/receipt")
    assert resp.status_code == 200
    assert resp.json()["decision"] == "rejected"


def test_unified_gate_validates_invalid_decision(tmp_path):
    """Test unified gate rejects invalid decision values."""
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
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    
    # Try invalid decision
    resp = client.post(f"/runs/{run_id}/decide", json={
        "decision": "maybe",
        "actor": "test_operator",
        "note": "",
    })
    assert resp.status_code == 400
    assert "Invalid decision" in resp.json()["detail"]
    
    # Verify run still in awaiting_approval (gate blocked)
    resp = client.get(f"/runs/{run_id}")
    assert resp.json()["status"] == "awaiting_approval"


def test_unified_gate_validates_nonexistent_run():
    """Test unified gate validates run exists for both paths."""
    # Try approve on nonexistent
    resp = client.post("/runs/nonexistent/decide", json={
        "decision": "approved",
        "actor": "test_operator",
        "note": "",
    })
    assert resp.status_code == 404
    
    # Try reject on nonexistent (same validation)
    resp = client.post("/runs/nonexistent/decide", json={
        "decision": "rejected",
        "actor": "test_operator",
        "note": "",
    })
    assert resp.status_code == 404


def test_unified_gate_validates_wrong_state(tmp_path):
    """Test unified gate validates state for both approve and reject."""
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
    
    client.post(f"/runs/{run_id}/decide", json={
        "decision": "approved",
        "actor": "test_operator",
        "note": "",
    })
    
    # Try to decide again (should fail for both approve and reject)
    resp = client.post(f"/runs/{run_id}/decide", json={
        "decision": "approved",
        "actor": "test_operator",
        "note": "",
    })
    assert resp.status_code == 400
    assert "not in awaiting_approval" in resp.json()["detail"]
    
    resp = client.post(f"/runs/{run_id}/decide", json={
        "decision": "rejected",
        "actor": "test_operator",
        "note": "",
    })
    assert resp.status_code == 400
    assert "not in awaiting_approval" in resp.json()["detail"]


def test_unified_gate_idempotent_receipt(tmp_path):
    """Test that receipt is created consistently for both decisions."""
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
    
    # Run pipeline twice
    resp1 = client.post("/run", json={
        "task": "fix first_token so empty list returns None",
        "repo_path": str(repo),
    })
    run_id_1 = resp1.json()["run_id"]
    
    resp2 = client.post("/run", json={
        "task": "fix first_token so empty list returns None",
        "repo_path": str(repo),
    })
    run_id_2 = resp2.json()["run_id"]
    
    # Approve one, reject other
    client.post(f"/runs/{run_id_1}/decide", json={
        "decision": "approved",
        "actor": "operator1",
        "note": "Good",
    })
    client.post(f"/runs/{run_id_2}/decide", json={
        "decision": "rejected",
        "actor": "operator2",
        "note": "Bad",
    })
    
    # Both should have receipts with same structure
    receipt1 = client.get(f"/runs/{run_id_1}/receipt").json()
    receipt2 = client.get(f"/runs/{run_id_2}/receipt").json()
    
    assert receipt1["decision"] == "approved"
    assert receipt2["decision"] == "rejected"
    assert "timestamp" in receipt1
    assert "timestamp" in receipt2
    assert "actor" in receipt1
    assert "actor" in receipt2
    assert "note" in receipt1
    assert "note" in receipt2


def test_legacy_endpoints_still_work(tmp_path):
    """Test that legacy /approve and /reject endpoints still function."""
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
    
    # Use legacy approve endpoint
    resp = client.post(f"/runs/{run_id}/approve", json={
        "actor": "legacy_operator",
        "note": "Via legacy",
    })
    assert resp.status_code == 200
    assert resp.json()["run"]["status"] == "applied"
