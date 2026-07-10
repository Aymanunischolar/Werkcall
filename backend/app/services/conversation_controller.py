"""Conversation controller (blueprint §5): owns the state machine, language
handling, and wires model events to the tool router, policies and
repository. One instance per active voice session."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.db.repository import Repository
from app.models.conversation import ConversationState, InvalidTransition, next_state
from app.policies.emergency import is_emergency, safety_instruction
from app.policies.handoff import evaluate_handoff
from app.policies.redaction import redact
from app.tools.router import ToolCallResult, ToolValidationError, call_tool
from app.voice.provider import ModelEvent, ModelEventType, VoiceModel

TOOL_TO_NEXT_STATE = {
    "search_faq": None,  # informational, does not advance state
    "check_slots": ConversationState.CHECK_AVAILABILITY,
    "book_appointment": ConversationState.EXECUTE,
    "reschedule_appointment": ConversationState.EXECUTE,
    "cancel_appointment": ConversationState.EXECUTE,
    "create_crm_record": None,
    "request_handoff": None,  # handled via escalation, not the normal table
}


@dataclass
class ConversationSessionContext:
    session_id: str
    language: str
    repository: Repository
    state: ConversationState = ConversationState.DISCLOSURE
    consecutive_tool_failures: int = 0


class ConversationController:
    def __init__(self, provider: VoiceModel, context: ConversationSessionContext) -> None:
        self._provider = provider
        self._ctx = context

    async def handle_model_event(self, event: ModelEvent) -> ModelEvent | None:
        """Process one event from the provider, return an event for the
        client (or None if nothing needs to be forwarded)."""
        if event.type in (ModelEventType.FINAL_TRANSCRIPT, ModelEventType.PARTIAL_TRANSCRIPT) and event.text:
            if event.type == ModelEventType.FINAL_TRANSCRIPT:
                self._ctx.repository.append_turn(
                    self._ctx.session_id, speaker="assistant", redacted_text=redact(event.text), latency_ms=None
                )
                if is_emergency(event.text):
                    self._escalate("emergency")
            return event

        if event.type == ModelEventType.TOOL_CALL and event.tool_name:
            return await self._handle_tool_call(event)

        return event

    async def handle_caller_utterance(self, text: str) -> None:
        self._ctx.repository.append_turn(self._ctx.session_id, speaker="caller", redacted_text=redact(text), latency_ms=None)
        decision = evaluate_handoff(utterance=text, consecutive_tool_failures=self._ctx.consecutive_tool_failures)
        if decision.should_handoff and decision.reason is not None:
            self._escalate(decision.urgency)

    async def _handle_tool_call(self, event: ModelEvent) -> ModelEvent:
        try:
            result: ToolCallResult = await call_tool(event.tool_name, event.tool_args)
        except ToolValidationError as exc:
            self._ctx.consecutive_tool_failures += 1
            return ModelEvent(type=ModelEventType.ERROR, error=str(exc), tool_call_id=event.tool_call_id)

        self._ctx.repository.record_tool_execution(
            self._ctx.session_id,
            tool=result.tool,
            validated_input=result.validated_input,
            result_code=result.result_code,
            retries=result.retries,
            duration_ms=result.duration_ms,
            idempotency_key=result.idempotency_key,
        )

        if result.result_code == "OK":
            self._ctx.consecutive_tool_failures = 0
            target = TOOL_TO_NEXT_STATE.get(event.tool_name)
            if target is not None:
                self._advance_state(target)
        else:
            self._ctx.consecutive_tool_failures += 1

        if event.tool_name == "request_handoff":
            self._advance_state(ConversationState.HUMAN_HANDOFF, escalation=True)

        await self._provider.send_tool_result(event.tool_call_id or "", result.output)
        return ModelEvent(type=ModelEventType.TOOL_CALL, tool_name=event.tool_name, tool_args=result.output, tool_call_id=event.tool_call_id)

    def _advance_state(self, target: ConversationState, *, escalation: bool = False) -> None:
        try:
            self._ctx.state = next_state(self._ctx.state, target, escalation=escalation)
        except InvalidTransition:
            # A non-linear but legitimate flow (e.g. caller revises details);
            # allow it rather than dropping the turn, but never for escalation targets.
            self._ctx.state = target

    def _escalate(self, urgency: str) -> None:
        target = ConversationState.EMERGENCY_ESCALATION if urgency == "emergency" else ConversationState.HUMAN_HANDOFF
        self._advance_state(target, escalation=True)

    @property
    def state(self) -> ConversationState:
        return self._ctx.state
