"""High-risk escalation detection (deterministic heuristics)."""

from __future__ import annotations

import re

from config.safety_policy import HIGH_RISK_KEYWORDS, HIGH_RISK_PATTERNS


def detect_high_risk(text: str) -> tuple[bool, list[str]]:
    lowered = text.lower()
    hits: list[str] = []

    for kw in HIGH_RISK_KEYWORDS:
        if kw in lowered:
            hits.append(kw)

    for pattern, label in HIGH_RISK_PATTERNS:
        if re.search(pattern, lowered) and label not in hits:
            hits.append(label)

    return (len(hits) > 0, hits)
