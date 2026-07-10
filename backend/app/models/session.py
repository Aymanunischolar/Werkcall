"""API-facing session/event models (blueprint §7)."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.conversation import ConversationState
from app.models.tools import Language


class Channel(StrEnum):
    BROWSER = "browser"
    TELEPHONE = "telephone"


class SessionOutcome(StrEnum):
    IN_PROGRESS = "in_progress"
    BOOKED = "booked"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    HANDED_OFF = "handed_off"
    EMERGENCY = "emergency"
    ABANDONED = "abandoned"
    FAILED_INTERACTION = "failed_interaction"
    CALLER_CANCELLED = "caller_cancelled"


class CreateSessionRequest(BaseModel):
    language: Language = Language.DE
    channel: Channel = Channel.BROWSER
    consent_given: bool = Field(description="Caller accepted the microphone/AI-disclosure consent UI")


class CreateSessionResponse(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    websocket_url: str
    disclosure_text: str


class ConversationTurn(BaseModel):
    speaker: Literal["caller", "assistant"]
    redacted_text: str
    timestamp: datetime
    latency_ms: int | None = None


class ToolExecutionRecord(BaseModel):
    tool: str
    validated_input: dict[str, Any]
    result_code: str
    retries: int = 0
    duration_ms: int
    idempotency_key: str | None = None


class SessionDetail(BaseModel):
    session_id: str
    started_at: datetime
    language: Language
    channel: Channel
    consent_at: datetime | None
    outcome: SessionOutcome
    state: ConversationState
    duration_ms: int | None
    model_provider: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    tool_executions: list[ToolExecutionRecord] = Field(default_factory=list)


# --- WebSocket event envelope -------------------------------------------------

class ClientEventType(StrEnum):
    AUDIO_CHUNK = "audio_chunk"
    END_OF_TURN = "end_of_turn"
    CLIENT_DISCONNECT = "client_disconnect"


class ServerEventType(StrEnum):
    AUDIO_CHUNK = "audio_chunk"
    PARTIAL_TRANSCRIPT = "partial_transcript"
    FINAL_TRANSCRIPT = "final_transcript"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATE_CHANGE = "state_change"
    ERROR = "error"
    SESSION_ENDED = "session_ended"


class WsEvent(BaseModel):
    type: ClientEventType | ServerEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
