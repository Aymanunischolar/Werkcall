"""Approved FAQ grounding source (blueprint §3, §6). search_faq must only
answer from these approved files and return NOT_FOUND otherwise — never
fall back to the model's general knowledge for company facts."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[3] / "knowledge-base"


@dataclass
class FaqEntry:
    source_id: str
    language: str
    question: str
    answer: str


def _parse_faq_file(path: Path, language: str) -> list[FaqEntry]:
    entries: list[FaqEntry] = []
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=## )", text)
    for block in blocks:
        block = block.strip()
        if not block.startswith("## "):
            continue
        lines = block.splitlines()
        question = lines[0][3:].strip()
        answer = "\n".join(lines[1:]).strip()
        source_id = f"{path.stem}:{len(entries)}"
        entries.append(FaqEntry(source_id=source_id, language=language, question=question, answer=answer))
    return entries


class KnowledgeBase:
    def __init__(self, directory: Path = KNOWLEDGE_BASE_DIR) -> None:
        self._entries: list[FaqEntry] = []
        for path in directory.glob("faq_*.md"):
            language = "de" if path.stem.endswith("_de") else "en"
            self._entries.extend(_parse_faq_file(path, language))

    def search(self, query: str, language: str) -> FaqEntry | None:
        query_terms = set(re.findall(r"\w+", query.lower()))
        best: tuple[int, FaqEntry] | None = None
        for entry in self._entries:
            if entry.language != language:
                continue
            entry_terms = set(re.findall(r"\w+", entry.question.lower()))
            overlap = len(query_terms & entry_terms)
            if overlap == 0:
                continue
            if best is None or overlap > best[0]:
                best = (overlap, entry)
        return best[1] if best else None


_kb: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb
