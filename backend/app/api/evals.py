"""POST /api/evals/run (blueprint §7): trigger the labelled scenario suite
over HTTP so the dashboard/CI can display measured results, not just the CLI."""
from __future__ import annotations

from fastapi import APIRouter

from evals.runner.run import main as run_all_scenarios

router = APIRouter(prefix="/api/evals", tags=["evals"])


@router.post("/run")
async def run_evals() -> dict:
    import io
    import contextlib
    import json

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        await run_all_scenarios()
    return json.loads(buffer.getvalue())
