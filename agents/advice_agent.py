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
- REQUIRED: what_you_could_do_next must include at least 2 concrete next steps.
- REQUIRED: how_you_might_say_it must include at least 1 example phrase.
- REQUIRED: cited_source_ids must include ONLY ids from the evidence list (copy them exactly).
- REQUIRED: cited_chunk_ids must include ONLY chunk_ids from the evidence list (copy them exactly).
- REQUIRED: cite 1-3 chunks that actually support your advice (same vocabulary/ideas as the chunk text).
- Do not cite every retrieved item by default — only chunks you used.
- Each cited_chunk_id's source_id must appear in cited_source_ids.
- Note when to involve an instructor/advisor without determining fault.
"""

_INTERVENTION_ACTIONS: dict[str, str] = {
    "clarify_roles": "Propose a short role/ownership check so each deliverable has a named owner.",
    "assign_task_ownership": "Suggest a shared task board with one owner and due date per item.",
    "establish_checkpoints": "Propose a midpoint check before the next deadline to catch gaps early.",
    "establish_team_norms": "Suggest agreeing on how updates will be shared across the whole team.",
    "clarify_shared_goal": "Facilitate a brief shared-goal recap so priorities are aligned.",
    "invite_team_input": "Invite each function to restate needs and constraints in a joint meeting.",
    "create_team_charter": "Draft a lightweight team charter covering communication channels and decision rules.",
    "use_behavior_specific_feedback": "Give behavior-specific feedback about missed cross-team updates, not character labels.",
}


def _default_actions(evidence: list[RetrievedEvidence]) -> list[str]:
    actions: list[str] = []
    for item in evidence:
        for tag in item.supported_intervention_tags:
            text = _INTERVENTION_ACTIONS.get(tag)
            if text and text not in actions:
                actions.append(text)
            if len(actions) >= 3:
                return actions
    if not actions:
        actions = [
            "You could propose a shared update channel so engineering, marketing, and operations see the same information.",
            "One option is to run a short cross-team sync that clarifies terminology, priorities, and decision owners.",
            "You could suggest a visible checklist for handoffs to reduce duplicated work.",
        ]
    return actions


def _default_phrases() -> list[str]:
    return [
        "Could we agree on one shared place for launch-critical updates so we are not optimizing different priorities in parallel?",
        "Before we decide, can each group restate their constraint in one sentence so we are using the same terms?",
    ]


def _ensure_recommendation_completeness(
    recommendation: CoachingRecommendation,
    evidence: list[RetrievedEvidence],
) -> CoachingRecommendation:
    """Drop hallucinated citation ids; fill thin non-citation fields for small models.

    Never invent citations — missing or empty cites must fail validation / repair.
    """
    data = recommendation.model_dump()
    allowed_sources = {e.source_id for e in evidence if e.source_id}
    allowed_chunks = {e.chunk_id for e in evidence if e.chunk_id}
    chunk_to_source = {e.chunk_id: e.source_id for e in evidence if e.chunk_id}

    cited_chunks = [
        cid for cid in data.get("cited_chunk_ids", []) if cid in allowed_chunks
    ]
    # Keep model-chosen sources that are retrieved; also include sources of kept chunks.
    cited_sources = [
        sid for sid in data.get("cited_source_ids", []) if sid in allowed_sources
    ]
    for cid in cited_chunks:
        sid = chunk_to_source.get(cid)
        if sid and sid not in cited_sources:
            cited_sources.append(sid)

    actions = [a.strip() for a in data.get("what_you_could_do_next", []) if str(a).strip()]
    if len(actions) < 2:
        actions = _default_actions(evidence)

    phrases = [p.strip() for p in data.get("how_you_might_say_it", []) if str(p).strip()]
    if not phrases:
        phrases = _default_phrases()

    happening = (data.get("what_may_be_happening") or "").strip()
    if not happening:
        happening = (
            "The team may be experiencing cross-functional communication gaps: "
            "different priorities and terminology, plus updates staying inside "
            "department channels, which can create misunderstandings and duplicated work."
        )

    why = (data.get("why_this_may_help") or "").strip()
    if not why:
        why = (
            "Shared visibility and clearer coordination habits often reduce "
            "process conflict without assuming bad intent."
        )

    watch = [w.strip() for w in data.get("what_to_watch_for", []) if str(w).strip()]
    if not watch:
        watch = [
            "Whether updates start appearing in a shared channel",
            "Whether disagreements shift from people-blaming to clarifying priorities",
        ]

    when = (data.get("when_to_involve_someone_else") or "").strip()
    if not when:
        when = (
            "If coordination attempts stall, or if conflict becomes personal/safety-related, "
            "involve an instructor, advisor, or appropriate university support."
        )

    return CoachingRecommendation(
        what_may_be_happening=happening,
        what_you_could_do_next=actions,
        how_you_might_say_it=phrases,
        why_this_may_help=why,
        what_to_watch_for=watch,
        when_to_involve_someone_else=when,
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
            + "\nRevise to fix those issues. You MUST include cited_source_ids, "
            "cited_chunk_ids, and at least two what_you_could_do_next items.\n"
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
Produce a coaching recommendation. Fields what_you_could_do_next, how_you_might_say_it,
cited_source_ids, and cited_chunk_ids are mandatory and must not be empty.
"""

    recommendation = structured_invoke(
        CoachingRecommendation, SYSTEM_PROMPT, user_prompt
    )
    recommendation = _ensure_recommendation_completeness(recommendation, evidence)
    return {"draft_recommendation": recommendation}
