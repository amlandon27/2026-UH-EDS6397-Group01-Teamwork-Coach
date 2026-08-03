"""Basic PII detection and redaction for MVP.

Only redacted text may proceed to LLM prompts, embeddings, retrieval, and logs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PiiSpan:
    label: str
    start: int
    end: int
    text: str


# Order matters: longer/more specific patterns first where relevant.
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    (
        "phone",
        re.compile(
            r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"
        ),
    ),
    ("student_id", re.compile(r"\b(?:UH)?ID[:#\s-]?\d{6,10}\b", re.IGNORECASE)),
    ("url_account", re.compile(r"\b(?:https?://)?(?:www\.)?(?:linkedin|instagram|facebook|x)\.com/[A-Za-z0-9_./-]+\b", re.IGNORECASE)),
    (
        "person_name",
        re.compile(
            r"\b(?:Mr|Mrs|Ms|Dr|Professor|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"
        ),
    ),
    (
        "person_name",
        re.compile(
            r"\b(?:my teammate|teammate|classmate|partner|instructor|advisor)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"
        ),
    ),
    (
        "person_name",
        re.compile(
            r"\b([A-Z][a-z]{2,})(\s+[A-Z][a-z]{2,}){1,2}\b"
        ),
    ),
]


def detect_pii(text: str) -> list[PiiSpan]:
    spans: list[PiiSpan] = []
    occupied: list[tuple[int, int]] = []

    for label, pattern in _PII_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            # Skip likely sentence-start false positives for bare capitalized words
            # handled by allowing overlaps check below.
            if _overlaps(start, end, occupied):
                continue
            # Filter common non-name capitalized phrases for generic name pattern
            if label == "person_name":
                candidate = match.group(0)
                if _looks_like_non_name(candidate):
                    continue
            occupied.append((start, end))
            spans.append(PiiSpan(label=label, start=start, end=end, text=match.group(0)))

    spans.sort(key=lambda s: s.start)
    return spans


def redact_pii(text: str) -> tuple[str, list[PiiSpan]]:
    spans = detect_pii(text)
    if not spans:
        return text, []

    parts: list[str] = []
    cursor = 0
    for span in spans:
        parts.append(text[cursor:span.start])
        parts.append(f"[{span.label.upper()}]")
        cursor = span.end
    parts.append(text[cursor:])
    return "".join(parts), spans


def contains_pii(text: str) -> bool:
    return bool(detect_pii(text))


def _overlaps(start: int, end: int, occupied: list[tuple[int, int]]) -> bool:
    for o_start, o_end in occupied:
        if start < o_end and end > o_start:
            return True
    return False


_NON_NAME_BLOCKLIST = {
    "Team Charter",
    "Project Manager",
    "Monday Morning",
    "Friday Afternoon",
    "University Houston",
    "Psychological Safety",
    "Task Conflict",
    "Process Conflict",
}


def _looks_like_non_name(candidate: str) -> bool:
    if candidate in _NON_NAME_BLOCKLIST:
        return True
    # Single-token matches from titled patterns are ok; bare First Last only
    words = candidate.split()
    if len(words) == 1:
        return True
    return False
