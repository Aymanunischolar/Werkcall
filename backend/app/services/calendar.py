"""Google Calendar service (blueprint §4, §7). OAuth + exponential backoff,
never continuous polling. Falls back to an in-memory calendar when no OAuth
credentials are configured, so the demo runs without a Google Cloud project."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.config import get_settings
from app.models.tools import Slot

BUSINESS_HOURS = (8, 17)  # 08:00-17:00 local time
SLOT_DURATION_MINUTES = 90


@dataclass
class _FakeBooking:
    start_at: datetime
    end_at: datetime
    external_calendar_id: str


class InMemoryCalendar:
    """Deterministic stand-in for Google Calendar: generates open business-hour
    slots and tracks bookings so double-booking is actually prevented."""

    def __init__(self) -> None:
        self._bookings: list[_FakeBooking] = []

    def free_slots(self, earliest: datetime, latest: datetime, count: int = 3) -> list[Slot]:
        slots: list[Slot] = []
        cursor = earliest.replace(hour=BUSINESS_HOURS[0], minute=0, second=0, microsecond=0)
        if cursor < earliest:
            cursor += timedelta(days=1)
        while cursor.date() <= latest.date() and len(slots) < count:
            if cursor.hour < BUSINESS_HOURS[1] and cursor.weekday() < 5:
                candidate_end = cursor + timedelta(minutes=SLOT_DURATION_MINUTES)
                if not self._overlaps(cursor, candidate_end):
                    slots.append(Slot(start_at=cursor, end_at=candidate_end))
                cursor += timedelta(hours=2)
            else:
                cursor = (cursor + timedelta(days=1)).replace(hour=BUSINESS_HOURS[0], minute=0)
        return slots

    def _overlaps(self, start: datetime, end: datetime) -> bool:
        return any(b.start_at < end and start < b.end_at for b in self._bookings)

    def book(self, slot: Slot) -> str:
        if self._overlaps(slot.start_at, slot.end_at):
            raise ValueError("slot no longer available")
        external_id = f"cal_{random.randint(100000, 999999)}"
        self._bookings.append(_FakeBooking(slot.start_at, slot.end_at, external_id))
        return external_id

    def cancel(self, external_calendar_id: str) -> None:
        self._bookings = [b for b in self._bookings if b.external_calendar_id != external_calendar_id]


_calendar_singleton: InMemoryCalendar | None = None


def get_calendar_client() -> InMemoryCalendar:
    """Real Google Calendar integration point: swap this factory for a
    google-api-python-client-backed implementation once OAuth is wired up
    (client_id/secret already in Settings). Kept in-memory for the free demo."""
    global _calendar_singleton
    settings = get_settings()
    if settings.google_oauth_client_id and settings.google_oauth_client_secret:
        raise NotImplementedError(
            "Google OAuth credentials are configured but the live Calendar client is not yet "
            "wired in this scaffold — implement googleapiclient.discovery.build('calendar', 'v3', ...) here."
        )
    if _calendar_singleton is None:
        _calendar_singleton = InMemoryCalendar()
    return _calendar_singleton
