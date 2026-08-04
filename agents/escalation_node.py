"""Escalation response node."""

from __future__ import annotations

from typing import Any

from agents.state_utils import state_get
from config.escalation_resources import ESCALATION_INTRO, ESCALATION_RESOURCES
from contract import FinalResponse


def escalation_node(state: Any) -> dict[str, Any]:
    lines = [ESCALATION_INTRO, "", "University of Houston and related resources:"]
    for res in ESCALATION_RESOURCES:
        phone = f" | Phone: {res['phone']}" if res.get("phone") else ""
        lines.append(f"- {res['name']}: {res['detail']} ({res['url']}){phone}")

    final = FinalResponse(
        route="escalation",
        title="Human support recommended",
        body="\n".join(lines),
        resources=ESCALATION_RESOURCES,
        redacted_input=state_get(state, "redacted_input"),
        pii_detected=bool(state_get(state, "pii_detected")),
        diagnosis=state_get(state, "diagnosis_payload"),
    )
    return {
        "final_response": final,
        "safe_to_display": True,
        "escalation_required": True,
    }
