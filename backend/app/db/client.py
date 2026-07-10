"""Thin Supabase repository layer. All writes go through here so redaction
and idempotency are enforced in one place instead of at every call site."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY, "
            "or use the in-memory repository for local/offline demo (see app/db/memory.py)."
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


class SessionRepository:
    """CRUD for voice_sessions and related tables. Backed by Supabase in
    production; app.db.memory.InMemoryRepository implements the same
    interface for free/offline demo runs with no Supabase project."""

    def create_session(self, *, language: str, channel: str, model_provider: str) -> dict[str, Any]:
        row = {"language": language, "channel": channel, "model_provider": model_provider, "state": "DISCLOSURE"}
        res = get_supabase().table("voice_sessions").insert(row).execute()
        return res.data[0]

    def record_consent(self, session_id: str) -> None:
        get_supabase().table("voice_sessions").update({"consent_at": datetime.utcnow().isoformat()}).eq(
            "id", session_id
        ).execute()

    def append_turn(self, session_id: str, *, speaker: str, redacted_text: str, latency_ms: int | None) -> None:
        get_supabase().table("conversation_turns").insert(
            {"session_id": session_id, "speaker": speaker, "redacted_text": redacted_text, "latency_ms": latency_ms}
        ).execute()

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
        get_supabase().table("tool_executions").insert(
            {
                "session_id": session_id,
                "tool": tool,
                "validated_input": validated_input,
                "result_code": result_code,
                "retries": retries,
                "duration_ms": duration_ms,
                "idempotency_key": idempotency_key,
            }
        ).execute()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        res = get_supabase().table("voice_sessions").select("*").eq("id", session_id).is_("deleted_at", "null").execute()
        return res.data[0] if res.data else None

    def delete_session(self, session_id: str) -> None:
        """Soft-delete for the dashboard's delete action (blueprint §10)."""
        get_supabase().table("voice_sessions").update({"deleted_at": datetime.utcnow().isoformat()}).eq(
            "id", session_id
        ).execute()
