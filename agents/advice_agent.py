"""Advice generation agent."""

from __future__ import annotations

import json
from typing import Any

from agents.state_utils import state_get
from contract import CoachingRecommendation, RetrievedEvidence, TeamworkDiagnosis
from services.llm_service import structured_invoke

# Safe, blame-free default — only used when the model omits the field.
DEFAULT_WHEN_TO_INVOLVE = (
    "If the issue continues after you try a clear team process, ask your "
    "instructor or advisor to help facilitate a check-in without assigning blame."
)

SYSTEM_PROMPT = """You are a teamwork and leadership coach for engineering students.
Create practical, proportionate coaching using ONLY the redacted reflection, diagnosis, and retrieved evidence.

Rules:
- Stay within teamwork/leadership coaching.
- Encourage action without commands (prefer "you could", "one option is").
- No unsupported diagnoses, accusations, or motive claims.
- No overconfidence words like definitely/certainly/obviously.
- No PII (no names, emails, phones, student IDs, URLs that identify a person).
- REQUIRED: what_may_be_happening must be a non-empty observational summary.
- REQUIRED: what_you_could_do_next must include at least 2 concrete next steps.
- REQUIRED: how_you_might_say_it must include at least 1 example phrase in quotes-ready form.
- REQUIRED: why_this_may_help must be non-empty.
- REQUIRED: when_to_involve_someone_else must be non-empty.
- REQUIRED: cited_source_ids must include ONLY ids from the evidence list (copy them exactly).
- REQUIRED: cited_chunk_ids must include ONLY chunk_ids from the evidence list (copy them exactly).
- REQUIRED: cite 1-3 chunks that actually support your advice (same vocabulary/ideas as the chunk text).
- Do not cite every retrieved item by default — only chunks you used.
- Each cited_chunk_id's source_id must appear in cited_source_ids.
- Note when to involve an instructor/advisor without determining fault.
- Never invent scenario details that are not grounded in the reflection or evidence.

Return every required field populated. Incomplete drafts are rejected.
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


def structural_gaps(recommendation: CoachingRecommendation) -> list[str]:
    """Return human-readable gaps that make a draft fail completeness checks."""
    gaps: list[str] = []
    if not (recommendation.what_may_be_happening or "").strip():
        gaps.append("what_may_be_happening is empty")
    if len([a for a in recommendation.what_you_could_do_next if str(a).strip()]) < 2:
        gaps.append("what_you_could_do_next needs at least 2 items")
    if len([p for p in recommendation.how_you_might_say_it if str(p).strip()]) < 1:
        gaps.append("how_you_might_say_it needs at least 1 phrase")
    if not (recommendation.why_this_may_help or "").strip():
        gaps.append("why_this_may_help is empty")
    if not (recommendation.when_to_involve_someone_else or "").strip():
        gaps.append("when_to_involve_someone_else is empty")
    if not recommendation.cited_chunk_ids:
        gaps.append("cited_chunk_ids is empty")
    if not recommendation.cited_source_ids:
        gaps.append("cited_source_ids is empty")
    return gaps


def apply_safe_defaults(recommendation: CoachingRecommendation) -> CoachingRecommendation:
    """Fill only the safe escalation-guidance default when omitted.

    Does not invent actions, phrases, observations, or citations.
    """
    data = recommendation.model_dump()
    when = (data.get("when_to_involve_someone_else") or "").strip()
    if not when:
        data["when_to_involve_someone_else"] = DEFAULT_WHEN_TO_INVOLVE
    return CoachingRecommendation.model_validate(data)


def _build_user_prompt(
    *,
    reflection: str,
    diagnosis: TeamworkDiagnosis,
    evidence_payload: list[dict[str, Any]],
    allowed_source_ids: list[str],
    allowed_chunk_ids: list[str],
    repair_block: str = "",
) -> str:
    return f"""
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
scenarios. You MUST populate ALL of these fields before responding:
- what_may_be_happening (non-empty)
- what_you_could_do_next (array with >= 2 concrete steps)
- how_you_might_say_it (array with >= 1 example phrase)
- why_this_may_help (non-empty)
- when_to_involve_someone_else (non-empty)
- cited_source_ids and cited_chunk_ids (from ALLOWED lists only)
"""


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
            "phrase, cited_source_ids, and cited_chunk_ids grounded in the evidence. "
            "Remove any PII (names, emails, phones, IDs).\n"
        )

    user_prompt = _build_user_prompt(
        reflection=reflection,
        diagnosis=diagnosis,
        evidence_payload=evidence_payload,
        allowed_source_ids=allowed_source_ids,
        allowed_chunk_ids=allowed_chunk_ids,
        repair_block=repair_block,
    )

    recommendation = structured_invoke(
        CoachingRecommendation, SYSTEM_PROMPT, user_prompt
    )
    recommendation = apply_safe_defaults(
        _sanitize_recommendation(recommendation, evidence)
    )

    # One inline completeness retry before validation — Ollama often omits fields.
    gaps = structural_gaps(recommendation)
    if gaps:
        retry_block = (
            "\nYour previous draft was incomplete:\n"
            + "\n".join(f"- {g}" for g in gaps)
            + "\nReturn a COMPLETE recommendation with every required field filled.\n"
        )
        retry_prompt = _build_user_prompt(
            reflection=reflection,
            diagnosis=diagnosis,
            evidence_payload=evidence_payload,
            allowed_source_ids=allowed_source_ids,
            allowed_chunk_ids=allowed_chunk_ids,
            repair_block=repair_block + retry_block,
        )
        recommendation = structured_invoke(
            CoachingRecommendation, SYSTEM_PROMPT, retry_prompt
        )
        recommendation = apply_safe_defaults(
            _sanitize_recommendation(recommendation, evidence)
        )

    return {"draft_recommendation": recommendation}
