"""OpenAI Realtime adapter — optional paid commercial adapter (blueprint §4).

Implemented behind the same VoiceModel interface as Gemini Live so switching
providers is a single VOICE_PROVIDER env var change. Not part of the free
demo path: document any use of this adapter as a paid, optional integration.
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator
from uuid import uuid4

import websockets

from app.config import get_settings
from app.voice.provider import ModelEvent, ModelEventType, VoiceSession

REALTIME_URL = "wss://api.openai.com/v1/realtime"


class OpenAIRealtimeProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for VOICE_PROVIDER=openai_realtime")
        self._api_key = settings.openai_api_key
        self._model = settings.openai_realtime_model
        self._ws: websockets.WebSocketClientProtocol | None = None

    async def connect(self, session: VoiceSession) -> None:
        self._ws = await websockets.connect(
            f"{REALTIME_URL}?model={self._model}",
            additional_headers={"Authorization": f"Bearer {self._api_key}", "OpenAI-Beta": "realtime=v1"},
        )
        tools = [
            {"type": "function", "name": spec["name"], "description": spec.get("description", ""), "parameters": spec.get("parameters", {})}
            for spec in session.tool_specs
        ]
        await self._ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {
                        "modalities": ["audio", "text"],
                        "instructions": session.system_prompt,
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "tools": tools,
                    },
                }
            )
        )

    async def send_audio(self, pcm: bytes) -> None:
        if not self._ws:
            raise RuntimeError("call connect() before send_audio()")
        import base64

        await self._ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": base64.b64encode(pcm).decode()}))

    async def send_tool_result(self, tool_call_id: str, result: dict[str, Any]) -> None:
        if not self._ws:
            raise RuntimeError("call connect() before send_tool_result()")
        await self._ws.send(
            json.dumps(
                {
                    "type": "conversation.item.create",
                    "item": {"type": "function_call_output", "call_id": tool_call_id, "output": json.dumps(result)},
                }
            )
        )
        await self._ws.send(json.dumps({"type": "response.create"}))

    async def receive_events(self) -> AsyncIterator[ModelEvent]:
        if not self._ws:
            raise RuntimeError("call connect() before receive_events()")
        async for raw in self._ws:
            event = json.loads(raw)
            etype = event.get("type")
            if etype == "response.audio_transcript.delta":
                yield ModelEvent(type=ModelEventType.PARTIAL_TRANSCRIPT, text=event.get("delta"))
            elif etype == "response.audio_transcript.done":
                yield ModelEvent(type=ModelEventType.FINAL_TRANSCRIPT, text=event.get("transcript"))
            elif etype == "response.audio.delta":
                import base64

                yield ModelEvent(type=ModelEventType.AUDIO_CHUNK, audio=base64.b64decode(event.get("delta", "")))
            elif etype == "response.function_call_arguments.done":
                yield ModelEvent(
                    type=ModelEventType.TOOL_CALL,
                    tool_name=event.get("name"),
                    tool_args=json.loads(event.get("arguments", "{}")),
                    tool_call_id=event.get("call_id", str(uuid4())),
                )
            elif etype == "response.done":
                yield ModelEvent(type=ModelEventType.TURN_COMPLETE)
            elif etype == "error":
                yield ModelEvent(type=ModelEventType.ERROR, error=str(event.get("error")))

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
