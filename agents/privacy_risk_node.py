"""LangGraph node helpers for privacy / high-risk gating."""

from __future__ import annotations

from typing import Any

from agents.state_utils import state_get
from guardrails.harmful_advice_validation import detect_high_risk
from guardrails.pii_redaction import redact_pii


def privacy_and_risk_node(state: Any) -> dict[str, Any]:
    raw = state_get(state, "raw_input", "") or ""
    redacted, spans = redact_pii(raw)
    high_risk, hits = detect_high_risk(redacted)

    return {
        "redacted_input": redacted,
        "pii_detected": len(spans) > 0,
        "pii_spans": [
            {"label": s.label, "start": s.start, "end": s.end, "text": s.text}
            for s in spans
        ],
        "high_risk_detected": high_risk,
        "escalation_required": high_risk,
        "error_message": (
            f"High-risk keywords detected: {', '.join(hits[:5])}" if high_risk else None
        ),
    }
