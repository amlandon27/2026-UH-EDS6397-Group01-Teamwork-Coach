"""Advice generation agent."""

from __future__ import annotations

import json
from typing import Any

from agents.state_utils import state_get
from contract import CoachingRecommendation, RetrievedEvidence, TeamworkDiagnosis
from services.llm_service import structured_invoke

SYSTEM_PROMPT = """You are a teamwork and leadership coach for engineering students.
Create practical, proportionate coaching using ONLY the redacted reflection, diagnosis, and retrieved evidence.

Rules:
- Stay within teamwork/leadership coaching.
- Encourage action without commands (prefer "you could", "one option is").
- No unsupported diagnoses, accusations, or motive claims.
- No overconfidence words like definitely/certainly/obviously.
- No PII.
- REQUIRED: what_may_be_happening must be a non-empty observational summary.
- REQUIRED: what_you_could_do_next must include at least 2 concrete next steps.
- REQUIRED: how_you_might_say_it must include at least 1 example phrase.
- REQUIRED: why_this_may_help must be non-empty.
- REQUIRED: when_to_involve_someone_else must be non-empty.
- REQUIRED: cited_source_ids must include ONLY ids from the evidence list (copy them exactly).
- REQUIRED: cited_chunk_ids must include ONLY chunk_ids from the evidence list (copy them exactly).
- REQUIRED: cite 1-3 chunks that actually support your advice (same vocabulary/ideas as the chunk text).
- Do not cite every retrieved item by default — only chunks you used.
- Each cited_chunk_id's source_id must appear in cited_source_ids.
- Note when to involve an instructor/advisor without determining fault.
- Never invent scenario details that are not grounded in the reflection or evidence.
"""


def _sanitize_recommendation(
    recommendation: CoachingRecommendation,
    evidence: list[RetrievedEvidence],
) -> CoachingRecommendation:
    """Drop hallucinated citation ids and trim whitespace.

    Never invent coaching content — thin drafts must fail validation / repair / fallback.
    """
    data = recommendation.model_dump()
    allowed_sources = {e.source_id for e in evidence if e.source_id}
    allowed_chunks = {e.chunk_id for e in evidence if e.chunk_id}
    chunk_to_source = {e.chunk_id: e.source_id for e in evidence if e.chunk_id}

    cited_chunks = [
        cid for cid in data.get("cited_chunk_ids", []) if cid in allowed_chunks
    ]
    cited_sources = [
        sid for sid in data.get("cited_source_ids", []) if sid in allowed_sources
    ]
    for cid in cited_chunks:
        sid = chunk_to_source.get(cid)
        if sid and sid not in cited_sources:
            cited_sources.append(sid)

    actions = [a.strip() for a in data.get("what_you_could_do_next", []) if str(a).strip()]
    phrases = [p.strip() for p in data.get("how_you_might_say_it", []) if str(p).strip()]
    watch = [w.strip() for w in data.get("what_to_watch_for", []) if str(w).strip()]

    return CoachingRecommendation(
        what_may_be_happening=(data.get("what_may_be_happening") or "").strip(),
        what_you_could_do_next=actions,
        how_you_might_say_it=phrases,
        why_this_may_help=(data.get("why_this_may_help") or "").strip(),
        what_to_watch_for=watch,
        when_to_involve_someone_else=(
            data.get("when_to_involve_someone_else") or ""
        ).strip(),
        cited_source_ids=cited_sources,
        cited_chunk_ids=cited_chunks,
    )


def advice_agent(state: Any) -> dict[str, Any]:
    diagnosis: TeamworkDiagnosis = state_get(state, "diagnosis_payload")
    evidence: list[RetrievedEvidence] = state_get(state, "retrieved_evidence", []) or []
    reflection = state_get(state, "redacted_input", "") or ""
    repair_notes = state_get(state, "validation_result")

    evidence_payload = [
        {
            "chunk_id": e.chunk_id,
            "source_id": e.source_id,
            "text": e.text[:1200],
            "supported_intervention_tags": e.supported_intervention_tags,
            "limitations": e.limitations,
            "citation_text": e.citation.citation_text if e.citation else "",
        }
        for e in evidence
    ]
    allowed_source_ids = [e.source_id for e in evidence if e.source_id]
    allowed_chunk_ids = [e.chunk_id for e in evidence if e.chunk_id]

    repair_block = ""
    if repair_notes and getattr(repair_notes, "repairable", False):
        repair_block = (
            "\nPrevious draft failed validation for repairable reasons:\n"
            + "\n".join(f"- {r}" for r in repair_notes.reasons)
            + "\nRevise to fix those issues. You MUST include non-empty "
            "what_may_be_happening, why_this_may_help, when_to_involve_someone_else, "
            "at least two what_you_could_do_next items, at least one how_you_might_say_it "
            "phrase, cited_source_ids, and cited_chunk_ids grounded in the evidence.\n"
        )

    user_prompt = f"""
Redacted reflection:
{reflection}

Diagnosis JSON:
{diagnosis.model_dump_json(indent=2)}

Retrieved evidence JSON:
{json.dumps(evidence_payload, indent=2)}

ALLOWED cited_source_ids (copy exactly, include at least one):
{json.dumps(allowed_source_ids)}

ALLOWED cited_chunk_ids (copy exactly, include at least one):
{json.dumps(allowed_chunk_ids)}
{repair_block}
Produce a coaching recommendation tailored to THIS reflection. Do not invent unrelated
scenarios. Fields what_may_be_happening, what_you_could_do_next (2+), how_you_might_say_it
(1+), why_this_may_help, when_to_involve_someone_else, cited_source_ids, and cited_chunk_ids
are mandatory and must not be empty.
"""

    recommendation = structured_invoke(
        CoachingRecommendation, SYSTEM_PROMPT, user_prompt
    )
    recommendation = _sanitize_recommendation(recommendation, evidence)
    return {"draft_recommendation": recommendation}
