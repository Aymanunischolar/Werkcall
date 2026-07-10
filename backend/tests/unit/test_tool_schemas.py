import pytest
from pydantic import ValidationError

from app.models.tools import Address, BookAppointmentInput, CheckSlotsInput, ContactDetails, ServiceType, Slot
from datetime import date, datetime


def test_check_slots_rejects_bad_postcode():
    with pytest.raises(ValidationError):
        CheckSlotsInput(service=ServiceType.HEATING_REPAIR, earliest_date=date(2026, 7, 12), latest_date=date(2026, 7, 15), postcode="123")


def test_check_slots_rejects_inverted_range():
    with pytest.raises(ValidationError):
        CheckSlotsInput(service=ServiceType.HEATING_REPAIR, earliest_date=date(2026, 7, 15), latest_date=date(2026, 7, 12), postcode="10115")


def test_contact_details_normalizes_phone():
    contact = ContactDetails(
        full_name="Max Mustermann",
        phone="+49 176 123 4567",
        address=Address(street="Hauptstr 1", postcode="10115", city="Berlin"),
    )
    assert " " not in contact.phone


def test_address_rejects_bad_postcode():
    with pytest.raises(ValidationError):
        Address(street="Hauptstr 1", postcode="123", city="Berlin")


def test_book_appointment_requires_idempotency_key():
    with pytest.raises(ValidationError):
        BookAppointmentInput(
            service=ServiceType.HEATING_REPAIR,
            slot=Slot(start_at=datetime(2026, 7, 12, 9), end_at=datetime(2026, 7, 12, 10, 30)),
            contact=ContactDetails(
                full_name="Max Mustermann",
                phone="+491761234567",
                address=Address(street="Hauptstr 1", postcode="10115", city="Berlin"),
            ),
            idempotency_key="short",
        )
