r"""Conversation state machine (detailed spec §7).

DISCLOSURE -> INTENT -> SAFETY_CHECK -> COLLECT_DETAILS -> CHECK_AVAILABILITY
    -> CONFIRM -> EXECUTE -> SUMMARIZE

Alternative exits, reachable from any non-terminal state via escalation:
    HUMAN_HANDOFF / EMERGENCY_ESCALATION / FAILED_INTERACTION / CALLER_CANCELLED
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
    FAILED_INTERACTION = "FAILED_INTERACTION"
    CALLER_CANCELLED = "CALLER_CANCELLED"


ESCALATION_STATES = {
    ConversationState.HUMAN_HANDOFF,
    ConversationState.EMERGENCY_ESCALATION,
    ConversationState.FAILED_INTERACTION,
    ConversationState.CALLER_CANCELLED,
}

# States reachable from a given state under normal flow. The escalation
# states are reachable from every non-terminal state — that transition is
# enforced in code (the `escalation` flag below), not in this table, because
# an emergency, an explicit handoff, a caller hang-up, or repeated tool
# failure can happen at any point in the conversation.
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
    ConversationState.FAILED_INTERACTION: set(),
    ConversationState.CALLER_CANCELLED: set(),
}

TERMINAL_STATES = {
    ConversationState.SUMMARIZE,
    *ESCALATION_STATES,
}


class InvalidTransition(Exception):
    pass


def next_state(current: ConversationState, target: ConversationState, *, escalation: bool = False) -> ConversationState:
    """Validate and return the next state. Escalation transitions bypass the
    normal table because emergencies, explicit handoff requests, caller
    cancellation, and repeated failure must be reachable from any point in
    the conversation (detailed spec §7)."""
    if escalation and target in ESCALATION_STATES:
        return target
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"{current} -> {target} is not an allowed transition")
    return target
