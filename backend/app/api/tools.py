"""Direct HTTP tool endpoints (blueprint §7) — used by n8n workflows, the
dashboard, and evals to call tools outside of a live voice session, through
the same validated tool router."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.tools.router import ToolValidationError, call_tool

router = APIRouter(prefix="/api/tools", tags=["tools"])

_ENDPOINT_TO_TOOL = {
    "check-slots": "check_slots",
    "book": "book_appointment",
    "reschedule": "reschedule_appointment",
    "cancel": "cancel_appointment",
    "handoff": "request_handoff",
}


async def _invoke(endpoint: str, args: dict) -> dict:
    tool_name = _ENDPOINT_TO_TOOL[endpoint]
    try:
        result = await call_tool(tool_name, args)
    except ToolValidationError as exc:
        raise HTTPException(status_code=422, detail={"tool": exc.tool, "errors": exc.errors}) from exc
    return {"result_code": result.result_code, "output": result.output, "retries": result.retries, "duration_ms": result.duration_ms}


@router.post("/check-slots")
async def check_slots(payload: dict) -> dict:
    return await _invoke("check-slots", payload)


@router.post("/book")
async def book(payload: dict) -> dict:
    return await _invoke("book", payload)


@router.post("/reschedule")
async def reschedule(payload: dict) -> dict:
    return await _invoke("reschedule", payload)


@router.post("/cancel")
async def cancel(payload: dict) -> dict:
    return await _invoke("cancel", payload)


@router.post("/handoff")
async def handoff(payload: dict) -> dict:
    return await _invoke("handoff", payload)
