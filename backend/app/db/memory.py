"""In-memory repository with the same interface as SessionRepository.

Lets the whole demo run with zero external accounts: no Supabase project,
no network. Used automatically when SUPABASE_URL is unset (see
app/db/repository.py). Data does not survive a process restart.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4


class InMemoryRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._turns: dict[str, list[dict[str, Any]]] = {}
        self._tool_executions: dict[str, list[dict[str, Any]]] = {}
        self._handoffs: dict[str, dict[str, Any]] = {}

    def create_session(self, *, language: str, channel: str, model_provider: str) -> dict[str, Any]:
        session_id = str(uuid4())
        row = {
            "id": session_id,
            "started_at": datetime.utcnow().isoformat(),
            "ended_at": None,
            "language": language,
            "channel": channel,
            "consent_at": None,
            "outcome": "in_progress",
            "state": "DISCLOSURE",
            "duration_ms": None,
            "model_provider": model_provider,
            "deleted_at": None,
        }
        self._sessions[session_id] = row
        self._turns[session_id] = []
        self._tool_executions[session_id] = []
        return row

    def record_consent(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["consent_at"] = datetime.utcnow().isoformat()

    def update_state(self, session_id: str, state: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["state"] = state

    def update_outcome(self, session_id: str, outcome: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["outcome"] = outcome

    def append_turn(self, session_id: str, *, speaker: str, redacted_text: str, latency_ms: int | None) -> None:
        self._turns.setdefault(session_id, []).append(
            {
                "speaker": speaker,
                "redacted_text": redacted_text,
                "timestamp": datetime.utcnow().isoformat(),
                "latency_ms": latency_ms,
            }
        )

    def record_tool_execution(
        self,
        session_id: str,
        *,
        tool: str,
        validated_input: dict[str, Any],
        result_code: str,
        retries: int,
        duration_ms: int,
        idempotency_key: str | None,
    ) -> None:
        executions = self._tool_executions.setdefault(session_id, [])
        if idempotency_key and any(
            e["tool"] == tool and e["idempotency_key"] == idempotency_key for e in executions
        ):
            return  # duplicate write guard (blueprint §9 "Duplicate writes: 0")
        executions.append(
            {
                "tool": tool,
                "validated_input": validated_input,
                "result_code": result_code,
                "retries": retries,
                "duration_ms": duration_ms,
                "idempotency_key": idempotency_key,
            }
        )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        row = self._sessions.get(session_id)
        if not row or row.get("deleted_at"):
            return None
        return {
            **row,
            "turns": self._turns.get(session_id, []),
            "tool_executions": self._tool_executions.get(session_id, []),
        }

    def delete_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["deleted_at"] = datetime.utcnow().isoformat()

    def list_sessions(self) -> list[dict[str, Any]]:
        return [row for row in self._sessions.values() if not row.get("deleted_at")]

    def create_handoff(self, session_id: str, *, reason: str, urgency: str, ticket_id: str | None) -> dict[str, Any]:
        handoff_id = str(uuid4())
        row = {
            "id": handoff_id,
            "session_id": session_id,
            "reason": reason,
            "urgency": urgency,
            "ticket_id": ticket_id,
            "resolution_status": "open",
            "created_at": datetime.utcnow().isoformat(),
        }
        self._handoffs[handoff_id] = row
        return row

    def get_handoff(self, handoff_id: str) -> dict[str, Any] | None:
        return self._handoffs.get(handoff_id)

    def list_handoffs(self, *, unresolved_only: bool = False) -> list[dict[str, Any]]:
        rows = list(self._handoffs.values())
        if unresolved_only:
            rows = [r for r in rows if r["resolution_status"] in ("open", "in_progress")]
        return rows
