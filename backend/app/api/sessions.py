"""Session + WebSocket audio endpoints (blueprint §7)."""
from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.db.repository import get_repository
from app.models.session import (
    Channel,
    ConversationTurn,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionDetail,
    SessionOutcome,
)
from app.models.tools import Language
from app.policies.disclosure import disclosure_text
from app.policies.prompts import build_system_prompt
from app.services.conversation_controller import ConversationController, ConversationSessionContext
from app.tools.router import TOOL_SCHEMAS
from app.voice.provider import ModelEventType, VoiceSession, get_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _tool_specs() -> list[dict]:
    specs = []
    for name, (input_model, _output) in TOOL_SCHEMAS.items():
        specs.append({"name": name, "description": input_model.__doc__ or name, "parameters": input_model.model_json_schema()})
    return specs


@router.post("", response_model=CreateSessionResponse)
async def create_session(payload: CreateSessionRequest) -> CreateSessionResponse:
    if not payload.consent_given:
        raise HTTPException(status_code=400, detail="Microphone/AI-disclosure consent is required before a session can start.")
    settings = get_settings()
    repo = get_repository()
    row = repo.create_session(language=payload.language.value, channel=payload.channel.value, model_provider=settings.voice_provider)
    repo.record_consent(row["id"])
    return CreateSessionResponse(
        session_id=row["id"],
        websocket_url=f"/api/sessions/{row['id']}/audio",
        disclosure_text=disclosure_text(payload.language.value),
    )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str) -> SessionDetail:
    repo = get_repository()
    row = repo.get_session(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")
    return SessionDetail(
        session_id=row["id"],
        started_at=row["started_at"],
        language=row["language"],
        channel=row["channel"],
        consent_at=row.get("consent_at"),
        outcome=row.get("outcome", SessionOutcome.IN_PROGRESS),
        state=row.get("state", "DISCLOSURE"),
        duration_ms=row.get("duration_ms"),
        model_provider=row["model_provider"],
        turns=[ConversationTurn(**t) for t in row.get("turns", [])],
        tool_executions=row.get("tool_executions", []),
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    """Dashboard delete action (blueprint §10)."""
    get_repository().delete_session(session_id)
    return {"status": "deleted"}


@router.websocket("/{session_id}/audio")
async def session_audio(websocket: WebSocket, session_id: str) -> None:
    settings = get_settings()
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.allowed_origins_list:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    repo = get_repository()
    row = repo.get_session(session_id)
    if row is None:
        await websocket.send_json({"type": "error", "payload": {"message": "unknown session"}})
        await websocket.close()
        return

    language = row["language"]
    provider = get_provider(settings.voice_provider)
    context = ConversationSessionContext(session_id=session_id, language=language, repository=repo)
    controller = ConversationController(provider, context)

    await provider.connect(
        VoiceSession(
            session_id=session_id,
            language=language,
            system_prompt=build_system_prompt(language),
            tool_specs=_tool_specs(),
        )
    )

    import asyncio

    async def pump_client_to_provider() -> None:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                return
            if "bytes" in message and message["bytes"] is not None:
                await provider.send_audio(message["bytes"])
            elif "text" in message and message["text"] is not None:
                data = json.loads(message["text"])
                if data.get("type") == "text_turn":
                    text = data.get("payload", {}).get("text", "")
                    await controller.handle_caller_utterance(text)
                    send_text_turn = getattr(provider, "send_text_turn", None)
                    if send_text_turn is not None:
                        await send_text_turn(text)
                elif data.get("type") == "client_disconnect":
                    return

    async def pump_provider_to_client() -> None:
        async for event in provider.receive_events():
            outgoing = await controller.handle_model_event(event)
            if outgoing is not None:
                await websocket.send_json(
                    {
                        "type": outgoing.type.value,
                        "payload": {
                            "text": outgoing.text,
                            "tool_name": outgoing.tool_name,
                            "tool_args": outgoing.tool_args,
                            "error": outgoing.error,
                        },
                        "state": controller.state.value,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

    try:
        tasks = [asyncio.create_task(pump_client_to_provider()), asyncio.create_task(pump_provider_to_client())]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        logger.info("client disconnected session=%s", session_id)
    finally:
        await provider.close()
