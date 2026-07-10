import pytest
from pydantic import ValidationError

from app.models.tools import BookAppointmentInput, CheckSlotsInput, ContactDetails, ServiceType, Slot
from datetime import date, datetime


def test_check_slots_rejects_bad_postcode():
    with pytest.raises(ValidationError):
        CheckSlotsInput(service=ServiceType.HEATING_FAILURE, earliest_date=date(2026, 7, 12), latest_date=date(2026, 7, 15), postcode="123")


def test_check_slots_rejects_inverted_range():
    with pytest.raises(ValidationError):
        CheckSlotsInput(service=ServiceType.HEATING_FAILURE, earliest_date=date(2026, 7, 15), latest_date=date(2026, 7, 12), postcode="10115")


def test_contact_details_normalizes_phone():
    contact = ContactDetails(full_name="Max Mustermann", phone="+49 176 123 4567", address="Hauptstr 1", postcode="10115")
    assert " " not in contact.phone


def test_book_appointment_requires_idempotency_key():
    with pytest.raises(ValidationError):
        BookAppointmentInput(
            service=ServiceType.HEATING_FAILURE,
            slot=Slot(start_at=datetime(2026, 7, 12, 9), end_at=datetime(2026, 7, 12, 10, 30)),
            contact=ContactDetails(full_name="Max Mustermann", phone="+491761234567", address="Hauptstr 1", postcode="10115"),
            idempotency_key="short",
        )
