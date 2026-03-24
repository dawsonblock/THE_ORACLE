from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from integration.pipeline import run_pipeline
from pathlib import Path
import json
from datetime import datetime, timezone
import uuid

app = FastAPI()

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runtime" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

class RunRequest(BaseModel):
    task: str
    repo_path: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    from integration.preflight import check
    check()
    return {"status": "ready"}

@app.post("/run")
def run(req: RunRequest):
    result = run_pipeline(req.task, req.repo_path)

    run_id = str(uuid.uuid4())
    artifact = {
        "run_id": run_id,
        "task": req.task,
        "repo_path": req.repo_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **result,
    }
    (RUNS_DIR / f"{run_id}.json").write_text(
        json.dumps(artifact, indent=2),
        encoding="utf-8",
    )
    return artifact

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
