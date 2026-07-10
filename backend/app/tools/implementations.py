"""Tool business logic. Each function takes a validated Pydantic input model
and returns the matching output model — the router (app/tools/router.py)
handles validation, retries, timeouts and idempotency around these calls."""
from __future__ import annotations

from app.models.tools import (
    BookAppointmentInput,
    BookAppointmentOutput,
    CancelAppointmentInput,
    CancelAppointmentOutput,
    CheckSlotsInput,
    CheckSlotsOutput,
    CreateCrmRecordInput,
    CreateCrmRecordOutput,
    RequestHandoffInput,
    RequestHandoffOutput,
    RescheduleAppointmentInput,
    RescheduleAppointmentOutput,
    ResultCode,
    SearchFaqInput,
    SearchFaqOutput,
)
from app.services.calendar import get_calendar_client
from app.services.crm import get_crm_client
from app.services.knowledge_base import get_knowledge_base


async def search_faq(payload: SearchFaqInput) -> SearchFaqOutput:
    entry = get_knowledge_base().search(payload.query, payload.language.value)
    if entry is None:
        return SearchFaqOutput(result_code=ResultCode.NOT_FOUND)
    return SearchFaqOutput(result_code=ResultCode.OK, answer=entry.answer, source_id=entry.source_id)


async def check_slots(payload: CheckSlotsInput) -> CheckSlotsOutput:
    from datetime import datetime

    calendar = get_calendar_client()
    earliest = datetime.combine(payload.earliest_date, datetime.min.time())
    latest = datetime.combine(payload.latest_date, datetime.min.time())
    slots = calendar.free_slots(earliest, latest)
    if not slots:
        return CheckSlotsOutput(result_code=ResultCode.NOT_FOUND, slots=[])
    return CheckSlotsOutput(result_code=ResultCode.OK, slots=slots)


async def book_appointment(payload: BookAppointmentInput) -> BookAppointmentOutput:
    calendar = get_calendar_client()
    try:
        external_id = calendar.book(payload.slot)
    except ValueError:
        return BookAppointmentOutput(result_code=ResultCode.CONFLICT)
    from uuid import uuid4

    booking_id = str(uuid4())
    return BookAppointmentOutput(result_code=ResultCode.OK, booking_id=booking_id, external_calendar_id=external_id)


async def reschedule_appointment(payload: RescheduleAppointmentInput) -> RescheduleAppointmentOutput:
    calendar = get_calendar_client()
    try:
        calendar.book(payload.new_slot)
    except ValueError:
        return RescheduleAppointmentOutput(result_code=ResultCode.CONFLICT)
    return RescheduleAppointmentOutput(result_code=ResultCode.OK, booking_id=payload.booking_id)


async def cancel_appointment(payload: CancelAppointmentInput) -> CancelAppointmentOutput:
    return CancelAppointmentOutput(result_code=ResultCode.OK, status="cancelled")


async def create_crm_record(payload: CreateCrmRecordInput) -> CreateCrmRecordOutput:
    crm = get_crm_client()
    contact_id = crm.upsert_contact(payload.contact)
    ticket_id = crm.create_ticket(payload.contact, payload.summary)
    return CreateCrmRecordOutput(result_code=ResultCode.OK, hubspot_contact_id=contact_id, hubspot_ticket_id=ticket_id)


async def request_handoff(payload: RequestHandoffInput) -> RequestHandoffOutput:
    from uuid import uuid4

    ticket_id = str(uuid4())
    caller_message = (
        "I understand. I'm connecting you with a member of our team now."
        if payload.urgency != "emergency"
        else "This is an emergency — I'm transferring you to a person immediately."
    )
    return RequestHandoffOutput(result_code=ResultCode.OK, ticket_id=ticket_id, caller_message=caller_message)


TOOL_IMPLEMENTATIONS = {
    "search_faq": search_faq,
    "check_slots": check_slots,
    "book_appointment": book_appointment,
    "reschedule_appointment": reschedule_appointment,
    "cancel_appointment": cancel_appointment,
    "create_crm_record": create_crm_record,
    "request_handoff": request_handoff,
}
