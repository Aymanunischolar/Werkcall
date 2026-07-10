"""HubSpot CRM service (blueprint §4, §6): upsert by email/phone hash so
repeated calls from the same contact never create duplicate records."""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from app.config import get_settings
from app.models.tools import ContactDetails


def contact_hash_key(contact: ContactDetails) -> str:
    basis = (contact.email or contact.phone).lower()
    return hashlib.sha256(basis.encode()).hexdigest()


@dataclass
class _FakeContact:
    contact_id: str
    hash_key: str
    ticket_ids: list[str] = field(default_factory=list)


class InMemoryCrm:
    """Stand-in for HubSpot's private-app API. Real implementation point:
    HubSpot CRM v3 contacts/tickets API using hubspot_private_app_token."""

    def __init__(self) -> None:
        self._contacts: dict[str, _FakeContact] = {}

    def upsert_contact(self, contact: ContactDetails) -> str:
        key = contact_hash_key(contact)
        if key in self._contacts:
            return self._contacts[key].contact_id
        contact_id = f"hs_contact_{random.randint(100000, 999999)}"
        self._contacts[key] = _FakeContact(contact_id=contact_id, hash_key=key)
        return contact_id

    def create_ticket(self, contact: ContactDetails, summary: str) -> str:
        key = contact_hash_key(contact)
        if key not in self._contacts:
            self.upsert_contact(contact)
        ticket_id = f"hs_ticket_{random.randint(100000, 999999)}"
        self._contacts[key].ticket_ids.append(ticket_id)
        return ticket_id


_crm_singleton: InMemoryCrm | None = None


def get_crm_client() -> InMemoryCrm:
    global _crm_singleton
    settings = get_settings()
    if settings.hubspot_private_app_token:
        raise NotImplementedError(
            "HUBSPOT_PRIVATE_APP_TOKEN is set but the live HubSpot client is not yet wired in this "
            "scaffold — implement the CRM v3 contacts/tickets API here (upsert by email/phone hash)."
        )
    if _crm_singleton is None:
        _crm_singleton = InMemoryCrm()
    return _crm_singleton
