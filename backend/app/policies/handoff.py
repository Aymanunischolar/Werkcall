"""Handoff triggers (blueprint §6 Handoff policy): explicit request, emergency
intent, low confidence, or repeated tool failure escalate to a human."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.tools import HandoffReason
from app.policies.emergency import is_emergency

EXPLICIT_HANDOFF_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [r"\bmitarbeiter\b", r"\bmensch\w*\b", r"\bperson\b", r"\bhuman\b", r"\brepresentative\b", r"\bagent\b sprechen"]
]

MAX_CONSECUTIVE_TOOL_FAILURES = 2
LOW_CONFIDENCE_THRESHOLD = 0.55


@dataclass
class HandoffDecision:
    should_handoff: bool
    reason: HandoffReason | None = None
    urgency: str = "standard"


def evaluate_handoff(
    *, utterance: str, consecutive_tool_failures: int = 0, intent_confidence: float | None = None
) -> HandoffDecision:
    if is_emergency(utterance):
        return HandoffDecision(True, HandoffReason.EMERGENCY, "emergency")
    if any(p.search(utterance) for p in EXPLICIT_HANDOFF_PATTERNS):
        return HandoffDecision(True, HandoffReason.EXPLICIT_REQUEST, "standard")
    if consecutive_tool_failures >= MAX_CONSECUTIVE_TOOL_FAILURES:
        return HandoffDecision(True, HandoffReason.REPEATED_TOOL_FAILURE, "standard")
    if intent_confidence is not None and intent_confidence < LOW_CONFIDENCE_THRESHOLD:
        return HandoffDecision(True, HandoffReason.LOW_CONFIDENCE, "standard")
    return HandoffDecision(False)
