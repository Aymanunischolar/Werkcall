"""Provider-adapter interface (blueprint §4 / §5).

Every voice backend — Gemini Live (free-first default), OpenAI Realtime
(optional paid), or the offline mock — implements this same Protocol so the
conversation controller never branches on which provider is active.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, AsyncIterator, Protocol


class ModelEventType(StrEnum):
    PARTIAL_TRANSCRIPT = "partial_transcript"
    FINAL_TRANSCRIPT = "final_transcript"
    AUDIO_CHUNK = "audio_chunk"
    TOOL_CALL = "tool_call"
    TURN_COMPLETE = "turn_complete"
    ERROR = "error"


@dataclass
class ModelEvent:
    type: ModelEventType
    text: str | None = None
    audio: bytes | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    tool_call_id: str | None = None
    error: str | None = None


@dataclass
class VoiceSession:
    session_id: str
    language: str
    system_prompt: str
    tool_specs: list[dict[str, Any]]


class VoiceModel(Protocol):
    """Matches the interface from blueprint §4 exactly:

        class VoiceModel(Protocol):
            async def connect(self, session: VoiceSession) -> None: ...
            async def send_audio(self, pcm: bytes) -> None: ...
            async def receive_events(self) -> AsyncIterator[ModelEvent]: ...
            async def close(self) -> None: ...
    """

    async def connect(self, session: VoiceSession) -> None: ...

    async def send_audio(self, pcm: bytes) -> None: ...

    async def send_tool_result(self, tool_call_id: str, result: dict[str, Any]) -> None: ...

    def receive_events(self) -> AsyncIterator[ModelEvent]: ...

    async def close(self) -> None: ...


def get_provider(name: str) -> VoiceModel:
    """Factory used by the session API so VOICE_PROVIDER is the only switch
    needed to move between free and paid adapters."""
    if name == "gemini_live":
        from app.voice.gemini_live import GeminiLiveProvider

        return GeminiLiveProvider()
    if name == "openai_realtime":
        from app.voice.openai_realtime import OpenAIRealtimeProvider

        return OpenAIRealtimeProvider()
    if name == "mock":
        from app.voice.mock_provider import MockVoiceProvider

        return MockVoiceProvider()
    raise ValueError(f"Unknown VOICE_PROVIDER: {name}")
