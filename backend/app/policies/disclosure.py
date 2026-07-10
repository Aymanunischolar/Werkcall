"""Non-negotiable disclosure text (blueprint §6 / §10).

The caller must be told they are speaking with an AI in the first spoken
turn, in every supported language, before any other conversation content.
"""
DISCLOSURE_TEXT = {
    "de": (
        "Sie sprechen mit dem KI-Assistenten von NordWerk Haustechnik. "
        "Sie können jederzeit einen Mitarbeiter verlangen."
    ),
    "en": (
        "You are speaking with NordWerk Haustechnik's AI assistant. "
        "You can ask to speak with a person at any time."
    ),
}


def disclosure_text(language: str) -> str:
    return DISCLOSURE_TEXT.get(language, DISCLOSURE_TEXT["en"])
