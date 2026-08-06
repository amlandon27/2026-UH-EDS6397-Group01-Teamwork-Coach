"""Reject jailbreaks, empty chat, and off-topic inputs before coaching."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Short greetings / spam should not trigger coaching
MIN_REFLECTION_CHARS = 40
MIN_REFLECTION_WORDS = 8

JAILBREAK_PATTERNS: list[str] = [
    r"\bsystem\s*prompt",
    r"\bhidden\s+prompt",
    r"\binternal\s+(prompt|instructions?|rules?)\b",
    r"\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?",
    r"\bdisregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"\breveal\s+your\s+(system|hidden|internal|developer)",
    r"\bshow\s+(me\s+)?your\s+(system|hidden|developer)?\s*prompts?",
    r"\bprint\s+your\s+(system|hidden)?\s*prompts?",
    r"\bwhat\s+are\s+your\s+(system\s+)?instructions\b",
    r"\bdeveloper\s+mode\b",
    r"\bjailbreak\b",
    r"\bDAN\b",
    r"\bdo\s+anything\s+now\b",
    r"\boverride\s+(your\s+)?(safety|rules|guardrails)",
    r"\bpretend\s+you\s+have\s+no\s+(rules|restrictions|guidelines)",
    r"\bact\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"\bbypass\s+(your\s+)?(filters?|safety|guardrails)",
]

# At least one signal that this is about teamwork / student collaboration
TEAMWORK_SIGNAL_PATTERNS: list[str] = [
    r"\bteams?\b",
    r"\bteammates?\b",
    r"\bgroup\s*mates?\b",
    r"\bgroup\s*work\b",
    r"\bproject\b",
    r"\bcapstone\b",
    r"\blab\b",
    r"\bmeeting\b",
    r"\bdeadline\b",
    r"\bmilestones?\b",
    r"\broles?\b",
    r"\bresponsibility\b",
    r"\bresponsibilities\b",
    r"\bcoordination\b",
    r"\bcommunicat",
    r"\bconflict\b",
    r"\bdisagreement\b",
    r"\bworkload\b",
    r"\bcontribution\b",
    r"\bcollaborat",
    r"\bpeer\b",
    r"\binstructor\b",
    r"\badvisor\b",
    r"\baccountability\b",
    r"\bpsychological\s+safety\b",
    r"\binclusion\b",
    r"\bfeedback\b",
    r"\bstandup\b",
    r"\bsprint\b",
    r"\bdeliverable\b",
    r"\bmissed\b",
    r"\buneven\b",
    r"\bshared\s+(goal|doc|file|drive)\b",
]


@dataclass(frozen=True)
class ScopeAssessment:
    in_scope: bool
    reasons: list[str]


def assess_reflection_scope(text: str) -> ScopeAssessment:
    """Deterministic gate: teamwork reflections only; no jailbreaks / empty chat."""
    cleaned = (text or "").strip()
    reasons: list[str] = []

    if not cleaned:
        return ScopeAssessment(False, ["Empty input."])

    lowered = cleaned.lower()
    words = re.findall(r"[a-zA-Z0-9']+", cleaned)

    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            reasons.append(
                "Request looks like a prompt-injection / jailbreak attempt, "
                "not a teamwork reflection."
            )
            return ScopeAssessment(False, reasons)

    if len(cleaned) < MIN_REFLECTION_CHARS or len(words) < MIN_REFLECTION_WORDS:
        reasons.append(
            "Message is too short to be a teamwork reflection. "
            "Describe what happened on the team with observable details."
        )
        return ScopeAssessment(False, reasons)

    has_team_signal = any(
        re.search(pattern, lowered, flags=re.IGNORECASE)
        for pattern in TEAMWORK_SIGNAL_PATTERNS
    )
    if not has_team_signal:
        reasons.append(
            "Message does not appear to describe a teamwork or leadership "
            "situation (no team/project/meeting/conflict signals)."
        )
        return ScopeAssessment(False, reasons)

    # Low-information spam: mostly repeated characters / nonsense tokens
    unique_words = {w.lower() for w in words}
    if len(unique_words) <= 3 and len(words) >= MIN_REFLECTION_WORDS:
        reasons.append("Message looks like repeated/random text, not a reflection.")
        return ScopeAssessment(False, reasons)

    return ScopeAssessment(True, [])
