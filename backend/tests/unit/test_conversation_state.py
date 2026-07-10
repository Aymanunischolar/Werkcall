import pytest

from app.models.conversation import ConversationState, InvalidTransition, next_state


def test_happy_path_transitions():
    state = ConversationState.DISCLOSURE
    for target in [
        ConversationState.INTENT,
        ConversationState.SAFETY_CHECK,
        ConversationState.COLLECT_DETAILS,
        ConversationState.CHECK_AVAILABILITY,
        ConversationState.CONFIRM,
        ConversationState.EXECUTE,
        ConversationState.SUMMARIZE,
    ]:
        state = next_state(state, target)
    assert state == ConversationState.SUMMARIZE


def test_caller_changes_date_mid_confirmation():
    state = next_state(ConversationState.CONFIRM, ConversationState.COLLECT_DETAILS)
    assert state == ConversationState.COLLECT_DETAILS


def test_invalid_transition_rejected():
    with pytest.raises(InvalidTransition):
        next_state(ConversationState.DISCLOSURE, ConversationState.EXECUTE)


def test_escalation_bypasses_table_from_any_state():
    state = next_state(ConversationState.COLLECT_DETAILS, ConversationState.EMERGENCY_ESCALATION, escalation=True)
    assert state == ConversationState.EMERGENCY_ESCALATION
