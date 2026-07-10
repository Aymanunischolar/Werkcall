"""Gemini Live adapter — the free-first default (blueprint §4).

Uses the google-genai SDK's Live API (bidirectional websocket): send raw PCM
in, receive transcript/audio/tool-call events out. Requires GEMINI_API_KEY.
Free-tier content may be used by Google to improve their products — the
system prompt and demo data must stay synthetic (see SECURITY.md).
"""
from __future__ import annotations

from typing import Any, AsyncIterator
from uuid import uuid4

from google import genai
from google.genai import types

from app.config import get_settings
from app.voice.provider import ModelEvent, ModelEventType, VoiceSession


class GeminiLiveProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for VOICE_PROVIDER=gemini_live")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_live_model
        self._session_cm = None
        self._live_session = None
        self._session: VoiceSession | None = None

    async def connect(self, session: VoiceSession) -> None:
        self._session = session
        function_declarations = [
            types.FunctionDeclaration(name=spec["name"], description=spec.get("description", ""), parameters=spec.get("parameters", {}))
            for spec in session.tool_specs
        ]
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=types.Content(parts=[types.Part(text=session.system_prompt)]),
            tools=[types.Tool(function_declarations=function_declarations)] if function_declarations else None,
        )
        self._session_cm = self._client.aio.live.connect(model=self._model, config=config)
        self._live_session = await self._session_cm.__aenter__()

    async def send_audio(self, pcm: bytes) -> None:
        if not self._live_session:
            raise RuntimeError("call connect() before send_audio()")
        await self._live_session.send_realtime_input(audio=types.Blob(data=pcm, mime_type="audio/pcm;rate=16000"))

    async def send_tool_result(self, tool_call_id: str, result: dict[str, Any]) -> None:
        if not self._live_session:
            raise RuntimeError("call connect() before send_tool_result()")
        await self._live_session.send_tool_response(
            function_responses=[types.FunctionResponse(id=tool_call_id, name="tool_result", response=result)]
        )

    async def receive_events(self) -> AsyncIterator[ModelEvent]:
        if not self._live_session:
            raise RuntimeError("call connect() before receive_events()")
        async for message in self._live_session.receive():
            server_content = getattr(message, "server_content", None)
            if server_content and server_content.model_turn:
                for part in server_content.model_turn.parts:
                    if part.text:
                        yield ModelEvent(type=ModelEventType.FINAL_TRANSCRIPT, text=part.text)
                    if part.inline_data and part.inline_data.data:
                        yield ModelEvent(type=ModelEventType.AUDIO_CHUNK, audio=part.inline_data.data)
            if server_content and server_content.turn_complete:
                yield ModelEvent(type=ModelEventType.TURN_COMPLETE)
            tool_call = getattr(message, "tool_call", None)
            if tool_call:
                for fc in tool_call.function_calls:
                    yield ModelEvent(
                        type=ModelEventType.TOOL_CALL,
                        tool_name=fc.name,
                        tool_args=dict(fc.args or {}),
                        tool_call_id=fc.id or str(uuid4()),
                    )

    async def close(self) -> None:
        if self._session_cm is not None:
            await self._session_cm.__aexit__(None, None, None)
