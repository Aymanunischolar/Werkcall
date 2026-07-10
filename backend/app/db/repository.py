"""Repository factory: Supabase when configured, in-memory otherwise.

This is what makes the free browser-first demo runnable with zero external
accounts (blueprint build principle) while still using the same interface
Supabase-backed production would use.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Protocol, Any

from app.config import get_settings
from app.db.memory import InMemoryRepository


class Repository(Protocol):
    def create_session(self, *, language: str, channel: str, model_provider: str) -> dict[str, Any]: ...
    def record_consent(self, session_id: str) -> None: ...
    def append_turn(self, session_id: str, *, speaker: str, redacted_text: str, latency_ms: int | None) -> None: ...
    def record_tool_execution(self, session_id: str, **kwargs: Any) -> None: ...
    def get_session(self, session_id: str) -> dict[str, Any] | None: ...
    def delete_session(self, session_id: str) -> None: ...


@lru_cache
def get_repository() -> Repository:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_role_key:
        from app.db.client import SessionRepository

        return SessionRepository()
    return InMemoryRepository()
