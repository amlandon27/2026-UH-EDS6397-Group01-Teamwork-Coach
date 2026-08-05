"""Helpers to normalize LangGraph / baseline outputs into ObservedRun."""

from __future__ import annotations

from typing import Any

from contract import AgentState, CoachingRecommendation, FinalResponse
from evaluation.schema import ObservedRun


def observed_from_state(raw: Any, *, latency_ms: float) -> ObservedRun:
    if isinstance(raw, AgentState):
        state = raw
    else:
        state = AgentState.model_validate(raw)

    final = state.final_response
    recommendation = None
    if final and final.recommendation:
        recommendation = final.recommendation
    elif state.draft_recommendation:
        recommendation = state.draft_recommendation

    diagnosis = None
    if final and final.diagnosis:
        diagnosis = final.diagnosis
    elif state.diagnosis_payload:
        diagnosis = state.diagnosis_payload

    retrieved_ids = [e.chunk_id for e in state.retrieved_evidence]
    cited_chunks, cited_sources, action_count = recommendation_bits(recommendation)

    title = final.title if final else ""
    body = final.body if final else ""
    student_facing = student_facing_text(final, recommendation)

    validation = state.validation_result
    return ObservedRun(
        route=final.route if final else None,
        title=title,
        body=body,
        primary_challenge=diagnosis.primary_challenge if diagnosis else None,
        secondary_challenges=list(diagnosis.secondary_challenges) if diagnosis else [],
        retrieved_chunk_ids=retrieved_ids,
        cited_chunk_ids=cited_chunks,
        cited_source_ids=cited_sources,
        action_count=action_count,
        pii_detected=bool(state.pii_detected or (final.pii_detected if final else False)),
        high_risk_detected=bool(state.high_risk_detected),
        retrieval_sufficient=bool(state.retrieval_sufficient),
        safe_to_display=bool(
            state.safe_to_display
            or (validation.safe_to_display if validation else False)
        ),
        escalation_required=bool(
            state.escalation_required
            or (validation.escalation_required if validation else False)
        ),
        validation_checks=dict(validation.checks) if validation else {},
        redacted_input=state.redacted_input or (final.redacted_input if final else "") or "",
        student_facing_text=student_facing,
        latency_ms=latency_ms,
    )


def recommendation_bits(
    recommendation: CoachingRecommendation | None,
) -> tuple[list[str], list[str], int]:
    if recommendation is None:
        return [], [], 0
    return (
        list(recommendation.cited_chunk_ids),
        list(recommendation.cited_source_ids),
        len(recommendation.what_you_could_do_next),
    )


def student_facing_text(
    final: FinalResponse | None,
    recommendation: CoachingRecommendation | None,
) -> str:
    parts: list[str] = []
    if final:
        parts.extend([final.title, final.body])
    if recommendation:
        parts.append(recommendation.what_may_be_happening)
        parts.extend(recommendation.what_you_could_do_next)
        parts.extend(recommendation.how_you_might_say_it)
        parts.append(recommendation.why_this_may_help)
        parts.extend(recommendation.what_to_watch_for)
        parts.append(recommendation.when_to_involve_someone_else)
    return "\n".join(p for p in parts if p)
