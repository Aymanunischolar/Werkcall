"""Gmail booking-confirmation service (blueprint §4, §8). Actual sending is
delegated to the n8n booking-confirmation workflow — this module only builds
the payload FastAPI posts to the n8n webhook after a booking succeeds."""
from __future__ import annotations

from dataclasses import dataclass

from app.models.tools import ContactDetails, Slot


@dataclass
class BookingConfirmationPayload:
    to_name: str
    to_email: str | None
    service: str
    start_at: str
    end_at: str
    booking_id: str


def build_confirmation_payload(*, contact: ContactDetails, slot: Slot, service: str, booking_id: str) -> BookingConfirmationPayload:
    return BookingConfirmationPayload(
        to_name=contact.full_name,
        to_email=contact.email,
        service=service,
        start_at=slot.start_at.isoformat(),
        end_at=slot.end_at.isoformat(),
        booking_id=booking_id,
    )
