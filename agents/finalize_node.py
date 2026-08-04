"""Assemble a displayable coaching response after validation passes."""

from __future__ import annotations

from typing import Any

from agents.state_utils import state_get
from contract import FinalResponse, RetrievedEvidence


def finalize_coaching_node(state: Any) -> dict[str, Any]:
    recommendation = state_get(state, "draft_recommendation")
    diagnosis = state_get(state, "diagnosis_payload")
    evidence: list[RetrievedEvidence] = state_get(state, "retrieved_evidence", []) or []

    citations = []
    seen = set()
    for e in evidence:
        if e.source_id in recommendation.cited_source_ids and e.citation:
            if e.source_id not in seen:
                citations.append(e.citation)
                seen.add(e.source_id)

    body_parts = [
        "## What may be happening",
        recommendation.what_may_be_happening,
        "",
        "## What you could do next",
        *[f"- {item}" for item in recommendation.what_you_could_do_next],
        "",
        "## How you might say it",
        *[f"- {item}" for item in recommendation.how_you_might_say_it],
        "",
        "## Why this may help",
        recommendation.why_this_may_help,
        "",
        "## What to watch for",
        *[f"- {item}" for item in recommendation.what_to_watch_for],
        "",
        "## When to involve someone else",
        recommendation.when_to_involve_someone_else,
    ]

    final = FinalResponse(
        route="coaching",
        title="Evidence-grounded coaching",
        body="\n".join(body_parts),
        recommendation=recommendation,
        citations=citations,
        diagnosis=diagnosis,
        redacted_input=state_get(state, "redacted_input"),
        pii_detected=bool(state_get(state, "pii_detected")),
    )
    return {"final_response": final, "safe_to_display": True}
