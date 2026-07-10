"""Deterministic offline provider: no network, no API key.

Lets the whole demo (and the eval runner) execute without any billed or
rate-limited service. Recognizes a tiny set of scripted phrases so the
required demo scenarios (blueprint §9) are reproducible in CI.
"""
from __future__ import annotations

import asyncio
import re
from datetime import date, timedelta
from typing import Any, AsyncIterator
from uuid import uuid4

from app.policies.emergency import is_emergency
from app.policies.handoff import EXPLICIT_HANDOFF_PATTERNS
from app.voice.provider import ModelEvent, ModelEventType, VoiceSession

FAQ_KEYWORDS = {"preis", "price", "kosten", "cost", "öffnungszeit", "opening hour", "kostet"}
IMPOSSIBLE_DAY_RE = re.compile(r"\b(3[2-9]|[4-9]\d)\.\s*\w+\b", re.IGNORECASE)


class MockVoiceProvider:
    def __init__(self) -> None:
        self._session: VoiceSession | None = None
        self._queue: asyncio.Queue[ModelEvent] = asyncio.Queue()
        self._closed = False

    async def connect(self, session: VoiceSession) -> None:
        self._session = session
        await self._queue.put(
            ModelEvent(
                type=ModelEventType.FINAL_TRANSCRIPT,
                text=(
                    "Sie sprechen mit dem KI-Assistenten von NordWerk Haustechnik. "
                    "Sie können jederzeit einen Mitarbeiter verlangen. Wie kann ich helfen?"
                    if session.language == "de"
                    else "You are speaking with NordWerk Haustechnik's AI assistant. "
                    "You can ask for a human at any time. How can I help?"
                ),
            )
        )

    async def send_audio(self, pcm: bytes) -> None:
        # The mock provider has no ASR; the browser client/eval runner sends
        # plain text turns through the same channel for deterministic testing.
        return None

    async def send_text_turn(self, text: str) -> None:
        """Test/demo hook: feed a caller utterance directly as text.

        This is a small rule-based classifier standing in for the real
        model's tool-calling decisions, ordered by policy precedence
        (blueprint §6): emergency first, then deterministic validation,
        then explicit human request, then grounding, then normal booking flow.
        """
        lowered = text.lower()

        if is_emergency(text):
            await self._emit_tool_call("request_handoff", {"reason": "emergency", "urgency": "emergency", "summary": text})
            return

        if IMPOSSIBLE_DAY_RE.search(text):
            # Deterministic validation rejects the impossible date before any
            # tool call is made — never pass it to Calendar (blueprint §6 Validation).
            await self._queue.put(
                ModelEvent(type=ModelEventType.FINAL_TRANSCRIPT, text="That date does not exist — could you repeat it?")
            )
            return

        if any(p.search(text) for p in EXPLICIT_HANDOFF_PATTERNS):
            await self._emit_tool_call("request_handoff", {"reason": "explicit_request", "urgency": "standard", "summary": text})
            return

        if any(kw in lowered for kw in FAQ_KEYWORDS):
            await self._emit_tool_call("search_faq", {"query": text, "language": "de" if any(c in text for c in "äöüß") else "en"})
            return

        if "termin" in lowered or "appointment" in lowered or "heizung" in lowered or "heating" in lowered:
            # A real model fills these from the conversation (address/postcode
            # collected in COLLECT_DETAILS); the mock provider uses synthetic
            # demo values so the golden-path flow is drivable end to end.
            tomorrow = date.today() + timedelta(days=1)
            await self._emit_tool_call(
                "check_slots",
                {
                    "service": "heating_repair",
                    "earliest_date": tomorrow.isoformat(),
                    "latest_date": (tomorrow + timedelta(days=3)).isoformat(),
                    "postcode": "10115",
                },
            )
            return

        await self._queue.put(ModelEvent(type=ModelEventType.FINAL_TRANSCRIPT, text=f"echo: {text}"))

    async def _emit_tool_call(self, tool_name: str, tool_args: dict[str, Any]) -> None:
        await self._queue.put(ModelEvent(type=ModelEventType.TOOL_CALL, tool_name=tool_name, tool_args=tool_args, tool_call_id=str(uuid4())))

    async def send_tool_result(self, tool_call_id: str, result: dict[str, Any]) -> None:
        await self._queue.put(ModelEvent(type=ModelEventType.TURN_COMPLETE))

    async def receive_events(self) -> AsyncIterator[ModelEvent]:
        while not self._closed:
            event = await self._queue.get()
            yield event

    async def close(self) -> None:
        self._closed = True
