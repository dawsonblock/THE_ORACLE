from fastapi.testclient import TestClient
from scripts.serve_coding_runs import app

def test_run_endpoint_writes_artifact(tmp_path):
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

    client = TestClient(app)
    resp = client.post("/run", json={
        "task": "fix first_token so empty list returns None",
        "repo_path": str(repo),
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "applied"
