"""Tool input/output contracts (blueprint §6 core tools table).

Every tool the model can call is defined here as a Pydantic schema pair so the
tool router can validate arguments deterministically before anything touches
Calendar, HubSpot, Gmail or Supabase. Never trust the model's raw arguments.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

GERMAN_POSTCODE_RE = re.compile(r"^\d{5}$")
E164_RE = re.compile(r"^\+?[1-9]\d{7,14}$")


class Language(StrEnum):
    DE = "de"
    EN = "en"


class ResultCode(StrEnum):
    OK = "OK"
    NOT_FOUND = "NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    CONFLICT = "CONFLICT"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"


# ---- search_faq -----------------------------------------------------------

class SearchFaqInput(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    language: Language


class SearchFaqOutput(BaseModel):
    result_code: ResultCode
    answer: str | None = None
    source_id: str | None = None


# ---- check_slots -----------------------------------------------------------

class ServiceType(StrEnum):
    HEATING_FAILURE = "heating_failure"
    MAINTENANCE = "maintenance"
    INSTALLATION_ENQUIRY = "installation_enquiry"


class CheckSlotsInput(BaseModel):
    service: ServiceType
    earliest_date: date
    latest_date: date
    postcode: str

    @field_validator("postcode")
    @classmethod
    def validate_postcode(cls, v: str) -> str:
        if not GERMAN_POSTCODE_RE.match(v):
            raise ValueError("postcode must be a 5-digit German Postleitzahl")
        return v

    @field_validator("latest_date")
    @classmethod
    def validate_range(cls, v: date, info) -> date:
        earliest = info.data.get("earliest_date")
        if earliest and v < earliest:
            raise ValueError("latest_date must not be before earliest_date")
        return v


class Slot(BaseModel):
    start_at: datetime
    end_at: datetime


class CheckSlotsOutput(BaseModel):
    result_code: ResultCode
    slots: list[Slot] = Field(default_factory=list)


# ---- book_appointment -------------------------------------------------------

class ContactDetails(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str
    email: EmailStr | None = None
    address: str = Field(min_length=1, max_length=300)
    postcode: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.replace(" ", "").replace("-", "")
        if not E164_RE.match(cleaned):
            raise ValueError("phone must be a valid E.164-ish number")
        return cleaned

    @field_validator("postcode")
    @classmethod
    def validate_postcode(cls, v: str) -> str:
        if not GERMAN_POSTCODE_RE.match(v):
            raise ValueError("postcode must be a 5-digit German Postleitzahl")
        return v


class BookAppointmentInput(BaseModel):
    service: ServiceType
    slot: Slot
    contact: ContactDetails
    urgency: Literal["standard", "urgent"] = "standard"
    idempotency_key: str = Field(min_length=8)


class BookAppointmentOutput(BaseModel):
    result_code: ResultCode
    booking_id: str | None = None
    external_calendar_id: str | None = None


# ---- reschedule_appointment --------------------------------------------------

class RescheduleAppointmentInput(BaseModel):
    booking_id: str
    new_slot: Slot
    idempotency_key: str = Field(min_length=8)


class RescheduleAppointmentOutput(BaseModel):
    result_code: ResultCode
    booking_id: str | None = None


# ---- cancel_appointment ------------------------------------------------------

class CancelAppointmentInput(BaseModel):
    booking_id: str
    reason: str = Field(min_length=1, max_length=300)
    idempotency_key: str = Field(min_length=8)


class CancelAppointmentOutput(BaseModel):
    result_code: ResultCode
    status: Literal["cancelled", "already_cancelled"] | None = None


# ---- create_crm_record -------------------------------------------------------

class CreateCrmRecordInput(BaseModel):
    contact: ContactDetails
    summary: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=8)


class CreateCrmRecordOutput(BaseModel):
    result_code: ResultCode
    hubspot_contact_id: str | None = None
    hubspot_ticket_id: str | None = None


# ---- request_handoff ----------------------------------------------------------

class HandoffReason(StrEnum):
    EXPLICIT_REQUEST = "explicit_request"
    EMERGENCY = "emergency"
    LOW_CONFIDENCE = "low_confidence"
    REPEATED_TOOL_FAILURE = "repeated_tool_failure"


class RequestHandoffInput(BaseModel):
    reason: HandoffReason
    urgency: Literal["standard", "urgent", "emergency"]
    summary: str = Field(min_length=1, max_length=1000)


class RequestHandoffOutput(BaseModel):
    result_code: ResultCode
    ticket_id: str | None = None
    caller_message: str


TOOL_SCHEMAS: dict[str, tuple[type[BaseModel], type[BaseModel]]] = {
    "search_faq": (SearchFaqInput, SearchFaqOutput),
    "check_slots": (CheckSlotsInput, CheckSlotsOutput),
    "book_appointment": (BookAppointmentInput, BookAppointmentOutput),
    "reschedule_appointment": (RescheduleAppointmentInput, RescheduleAppointmentOutput),
    "cancel_appointment": (CancelAppointmentInput, CancelAppointmentOutput),
    "create_crm_record": (CreateCrmRecordInput, CreateCrmRecordOutput),
    "request_handoff": (RequestHandoffInput, RequestHandoffOutput),
}
