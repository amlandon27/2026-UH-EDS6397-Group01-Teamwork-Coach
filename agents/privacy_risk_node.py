"""LangGraph node helpers for privacy / high-risk / scope gating."""

from __future__ import annotations

from typing import Any

from agents.state_utils import state_get
from guardrails.harmful_advice_validation import detect_high_risk
from guardrails.pii_redaction import redact_pii
from guardrails.scope_validation import assess_reflection_scope


def privacy_and_risk_node(state: Any) -> dict[str, Any]:
    raw = state_get(state, "raw_input", "") or ""
    goal_raw = state_get(state, "student_goal")

    redacted, spans = redact_pii(raw)
    if goal_raw:
        redacted_goal, goal_spans = redact_pii(goal_raw)
    else:
        redacted_goal = goal_raw
        goal_spans = []

    risk_text = redacted
    if redacted_goal:
        risk_text = f"{redacted}\n{redacted_goal}"

    high_risk, hits = detect_high_risk(risk_text)
    scope = assess_reflection_scope(redacted)
    all_spans = list(spans) + list(goal_spans)

    error_message = None
    if high_risk:
        error_message = f"High-risk keywords detected: {', '.join(hits[:5])}"
    elif not scope.in_scope:
        error_message = "; ".join(scope.reasons) if scope.reasons else "Out of scope."

    return {
        "redacted_input": redacted,
        "student_goal": redacted_goal,
        "pii_detected": len(all_spans) > 0,
        "pii_spans": [
            {"label": s.label, "start": s.start, "end": s.end, "text": s.text}
            for s in all_spans
        ],
        "high_risk_detected": high_risk,
        "escalation_required": high_risk,
        "out_of_scope": (not high_risk) and (not scope.in_scope),
        "error_message": error_message,
    }
