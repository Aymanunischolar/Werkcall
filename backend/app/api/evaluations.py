"""POST /api/evaluations/run, GET /api/evaluations/{run_id} (detailed spec §6).

Runs the labelled scenario suite and stores the result so it can be fetched
again by run_id — the dashboard/CI display measured results, not just a
one-shot CLI printout.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from evals.runner.run import main as run_all_scenarios

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])

# In-memory run store. Good enough for a demo; a real deployment would
# persist evaluation_runs rows the same way tool_executions are persisted.
_runs: dict[str, dict[str, Any]] = {}


@router.post("/run")
async def run_evaluations() -> dict:
    import contextlib
    import io
    import json

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        await run_all_scenarios()
    summary = json.loads(buffer.getvalue())

    run_id = str(uuid4())
    summary["run_id"] = run_id
    _runs[run_id] = summary
    return summary


@router.get("/{run_id}")
async def get_evaluation_run(run_id: str) -> dict:
    run = _runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="evaluation run not found")
    return run
