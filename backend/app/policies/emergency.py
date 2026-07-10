"""Emergency detection and the approved safety instruction (blueprint §2, §6).

Gas smell, fire, immediate danger or medical emergency must bypass normal
booking logic entirely and go straight to human transfer. This is a
deterministic keyword/regex gate, not a model judgement call — the model can
still trigger request_handoff itself, but this gate must never be skippable
by prompt content (see grounding/prompt-injection eval scenario in §9).
"""
from __future__ import annotations

import re

EMERGENCY_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bgas\w*\b.*\b(riech|smell|geruch)\w*\b",
        r"\b(riech|smell|geruch)\w*\b.*\bgas\w*\b",
        r"\bgasgeruch\b",
        r"\bsmell of gas\b",
        r"\bfeuer\b",
        r"\bfire\b",
        r"\bexplosion\b",
        r"\bnotfall\b",
        r"\bemergency\b",
        r"\blebensgefahr\b",
        r"\bmedical emergency\b",
        r"\bkohlenmonoxid\b",
        r"\bcarbon monoxide\b",
    ]
]

APPROVED_SAFETY_INSTRUCTION = {
    "de": (
        "Das ist ein Notfall. Bitte verlassen Sie sofort das Gebäude, öffnen Sie Fenster und Türen "
        "und rufen Sie die Notrufnummer 112 an. Ich verbinde Sie jetzt mit einem Mitarbeiter."
    ),
    "en": (
        "This is an emergency. Please leave the building immediately, open windows and doors, "
        "and call the emergency number. I am transferring you to a person now."
    ),
}


def is_emergency(text: str) -> bool:
    return any(pattern.search(text) for pattern in EMERGENCY_PATTERNS)


def safety_instruction(language: str) -> str:
    return APPROVED_SAFETY_INSTRUCTION.get(language, APPROVED_SAFETY_INSTRUCTION["en"])
