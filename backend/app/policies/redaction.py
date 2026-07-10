"""Log/transcript redaction (blueprint §10: "Redact telephone numbers, email
and addresses in logs"). Applied before anything is written to
conversation_turns — raw text never reaches storage.
"""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-()]{7,}\d)")
_POSTCODE_RE = re.compile(r"\b\d{5}\b")


def redact(text: str) -> str:
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    text = _POSTCODE_RE.sub("[REDACTED_POSTCODE]", text)
    return text
