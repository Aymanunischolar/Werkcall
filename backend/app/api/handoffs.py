"""Handoff endpoints (detailed spec §10: custom node "Handoff" resource —
create, get status, list unresolved). Backs the request_handoff tool result
with a queryable record, since a human operator needs to see and update
handoff status after the call ends."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.repository import get_repository
from app.models.tools import HandoffReason

router = APIRouter(prefix="/api/handoffs", tags=["handoffs"])


class CreateHandoffRequest(BaseModel):
    session_id: str
    reason: HandoffReason
    urgency: Literal["standard", "urgent", "emergency"]
    ticket_id: str | None = None


@router.post("")
async def create_handoff(payload: CreateHandoffRequest) -> dict:
    row = get_repository().create_handoff(
        payload.session_id, reason=payload.reason.value, urgency=payload.urgency, ticket_id=payload.ticket_id
    )
    return row


@router.get("")
async def list_handoffs(unresolved: bool = False) -> list[dict]:
    return get_repository().list_handoffs(unresolved_only=unresolved)


@router.get("/{handoff_id}")
async def get_handoff(handoff_id: str) -> dict:
    row = get_repository().get_handoff(handoff_id)
    if row is None:
        raise HTTPException(status_code=404, detail="handoff not found")
    return row
