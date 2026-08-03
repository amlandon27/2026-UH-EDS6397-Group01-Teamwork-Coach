"""Safe fallback response node."""

from __future__ import annotations

from typing import Any

from agents.state_utils import state_get
from config.escalation_resources import SAFE_FALLBACK_MESSAGE
from contract import FinalResponse


def fallback_node(state: Any) -> dict[str, Any]:
    reasons = []
    validation = state_get(state, "validation_result")
    if validation and getattr(validation, "reasons", None):
        reasons = validation.reasons
    elif not state_get(state, "retrieval_sufficient", False):
        reasons = ["Insufficient or irrelevant retrieved evidence."]

    body = SAFE_FALLBACK_MESSAGE
    if reasons:
        body += "\n\nInternal routing note (not model advice):\n" + "\n".join(
            f"- {r}" for r in reasons
        )

    final = FinalResponse(
        route="fallback",
        title="Unable to provide validated coaching",
        body=body,
        redacted_input=state_get(state, "redacted_input"),
        pii_detected=bool(state_get(state, "pii_detected")),
        diagnosis=state_get(state, "diagnosis_payload"),
        citations=[],
    )
    return {
        "final_response": final,
        "safe_to_display": True,
    }
