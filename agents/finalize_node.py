"""Assemble a displayable coaching response after validation passes."""

from __future__ import annotations

from typing import Any

from agents.state_utils import state_get
from contract import FinalResponse, RetrievedEvidence


def _strip_wrapping_quotes(text: str) -> str:
    """Normalize so UI can always wrap example phrases in quotation marks."""
    cleaned = (text or "").strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1].strip()
    return cleaned


def finalize_coaching_node(state: Any) -> dict[str, Any]:
    recommendation = state_get(state, "draft_recommendation")
    diagnosis = state_get(state, "diagnosis_payload")
    evidence: list[RetrievedEvidence] = state_get(state, "retrieved_evidence", []) or []

    cited_chunk_ids = set(recommendation.cited_chunk_ids or [])
    cited_source_ids = set(recommendation.cited_source_ids or [])

    citations = []
    seen_sources: set[str] = set()
    supporting: list[RetrievedEvidence] = []
    seen_chunks: set[str] = set()

    for item in evidence:
        # Only surface chunks the model explicitly cited — never invent grounding.
        if not (item.chunk_id and item.chunk_id in cited_chunk_ids):
            continue
        if item.chunk_id not in seen_chunks:
            supporting.append(item)
            seen_chunks.add(item.chunk_id)
        if item.citation and item.source_id not in seen_sources:
            citations.append(item.citation)
            seen_sources.add(item.source_id)

    # If chunk cites are missing but source cites remain (should not pass validation),
    # still attach citation metadata without dumping uncited chunk text.
    if not supporting and cited_source_ids:
        for item in evidence:
            if item.source_id not in cited_source_ids:
                continue
            if item.citation and item.source_id not in seen_sources:
                citations.append(item.citation)
                seen_sources.add(item.source_id)

    body_parts = [
        "## What may be happening",
        recommendation.what_may_be_happening,
        "",
        "## What you could do next",
        *[f"- {item}" for item in recommendation.what_you_could_do_next],
        "",
        "## How you might say it",
        *[
            f'- "{_strip_wrapping_quotes(item)}"'
            for item in recommendation.how_you_might_say_it
        ],
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
        supporting_evidence=supporting,
        diagnosis=diagnosis,
        redacted_input=state_get(state, "redacted_input"),
        pii_detected=bool(state_get(state, "pii_detected")),
    )
    return {"final_response": final, "safe_to_display": True}
