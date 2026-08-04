"""High-risk escalation detection (deterministic heuristics)."""

from __future__ import annotations

from config.safety_policy import HIGH_RISK_KEYWORDS


def detect_high_risk(text: str) -> tuple[bool, list[str]]:
    lowered = text.lower()
    hits = [kw for kw in HIGH_RISK_KEYWORDS if kw in lowered]
    return (len(hits) > 0, hits)
