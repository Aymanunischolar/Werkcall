r"""Conversation state machine (blueprint §6).

DISCLOSURE -> INTENT -> SAFETY_CHECK -> COLLECT_DETAILS -> CHECK_AVAILABILITY
    -> CONFIRM -> EXECUTE -> SUMMARIZE
                \-> HUMAN_HANDOFF / EMERGENCY_ESCALATION
"""
from __future__ import annotations

from enum import StrEnum


class ConversationState(StrEnum):
    DISCLOSURE = "DISCLOSURE"
    INTENT = "INTENT"
    SAFETY_CHECK = "SAFETY_CHECK"
    COLLECT_DETAILS = "COLLECT_DETAILS"
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    CONFIRM = "CONFIRM"
    EXECUTE = "EXECUTE"
    SUMMARIZE = "SUMMARIZE"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    EMERGENCY_ESCALATION = "EMERGENCY_ESCALATION"


# States reachable from a given state under normal flow. HUMAN_HANDOFF and
# EMERGENCY_ESCALATION are reachable from every non-terminal state — that
# transition is enforced in code (policies.escalation), not in this table.
ALLOWED_TRANSITIONS: dict[ConversationState, set[ConversationState]] = {
    ConversationState.DISCLOSURE: {ConversationState.INTENT},
    ConversationState.INTENT: {ConversationState.SAFETY_CHECK},
    ConversationState.SAFETY_CHECK: {ConversationState.COLLECT_DETAILS},
    ConversationState.COLLECT_DETAILS: {
        ConversationState.CHECK_AVAILABILITY,
        ConversationState.COLLECT_DETAILS,  # caller changes the date/details mid-flow
    },
    ConversationState.CHECK_AVAILABILITY: {
        ConversationState.CONFIRM,
        ConversationState.COLLECT_DETAILS,  # no slot available, re-collect
    },
    ConversationState.CONFIRM: {
        ConversationState.EXECUTE,
        ConversationState.COLLECT_DETAILS,  # caller changes something during confirmation
    },
    ConversationState.EXECUTE: {ConversationState.SUMMARIZE},
    ConversationState.SUMMARIZE: set(),
    ConversationState.HUMAN_HANDOFF: set(),
    ConversationState.EMERGENCY_ESCALATION: set(),
}

TERMINAL_STATES = {
    ConversationState.SUMMARIZE,
    ConversationState.HUMAN_HANDOFF,
    ConversationState.EMERGENCY_ESCALATION,
}


class InvalidTransition(Exception):
    pass


def next_state(current: ConversationState, target: ConversationState, *, escalation: bool = False) -> ConversationState:
    """Validate and return the next state. Escalation transitions bypass the
    normal table because emergencies and explicit handoff requests must be
    reachable from any point in the conversation (blueprint §6, Handoff policy)."""
    if escalation and target in (ConversationState.HUMAN_HANDOFF, ConversationState.EMERGENCY_ESCALATION):
        return target
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"{current} -> {target} is not an allowed transition")
    return target
