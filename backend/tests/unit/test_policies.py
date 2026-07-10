from app.models.tools import HandoffReason
from app.policies.emergency import is_emergency
from app.policies.handoff import evaluate_handoff
from app.policies.redaction import redact


def test_gas_smell_triggers_emergency():
    assert is_emergency("Ich rieche Gas in der Küche") is True
    assert is_emergency("I smell gas in the kitchen") is True


def test_normal_request_is_not_emergency():
    assert is_emergency("Meine Heizung ist ausgefallen") is False


def test_explicit_person_request_triggers_handoff():
    decision = evaluate_handoff(utterance="Ich möchte mit einem Mitarbeiter sprechen")
    assert decision.should_handoff is True
    assert decision.reason == HandoffReason.EXPLICIT_REQUEST


def test_repeated_tool_failure_triggers_handoff():
    decision = evaluate_handoff(utterance="book it", consecutive_tool_failures=2)
    assert decision.should_handoff is True
    assert decision.reason == HandoffReason.REPEATED_TOOL_FAILURE


def test_gas_emergency_takes_priority_over_explicit_request_pattern():
    decision = evaluate_handoff(utterance="Gasgeruch, bitte Notfall!")
    assert decision.reason == HandoffReason.EMERGENCY
    assert decision.urgency == "emergency"


def test_redaction_masks_email_phone_postcode():
    text = "Call me at +49 176 1234567 or test@example.com, Hauptstr 1, 10115 Berlin"
    redacted = redact(text)
    assert "test@example.com" not in redacted
    assert "1234567" not in redacted
    assert "10115" not in redacted
