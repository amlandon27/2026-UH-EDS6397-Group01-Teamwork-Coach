"""Baseline systems for comparative evaluation.

`gated_rag` — full LangGraph coach (default product path).
`no_rag` — privacy/risk gate retained; coaching from Ollama with no retrieval,
citations, or evidence validation. Used to show the value of gated RAG.
"""

from __future__ import annotations

import time
from typing import Any, Literal, Optional

from agents.escalation_node import escalation_node
from agents.privacy_risk_node import privacy_and_risk_node
from config.settings import get_settings
from contract import CoachingRecommendation
from evaluation.observe import observed_from_state
from evaluation.schema import EvalCase, ObservedRun
from services.llm_service import structured_invoke
from services.tracing_service import run_with_tracing, traced_graph_invoke

SystemName = Literal["gated_rag", "no_rag"]

_NO_RAG_SYSTEM = """You are a general teamwork coach for engineering students.
Give practical advice from the student reflection alone.

Rules:
- Encourage action without commands.
- Do not invent citations, DOIs, paper titles, or source_ids.
- Leave cited_source_ids and cited_chunk_ids empty.
- Do not claim clinical, legal, or misconduct verdicts.
- Avoid motive/character labels.
"""


def invoke_system(case: EvalCase, system: SystemName) -> ObservedRun:
    if system == "gated_rag":
        return _invoke_gated_rag(case)
    if system == "no_rag":
        return _invoke_no_rag(case)
    raise ValueError(f"Unknown system: {system}")


def _invoke_gated_rag(case: EvalCase) -> ObservedRun:
    from agents.coordinator import build_graph
    from contract import AgentState

    started = time.perf_counter()

    def _invoke(*, config: Optional[dict[str, Any]] = None) -> Any:
        app = build_graph()
        initial = AgentState(
            raw_input=case.reflection,
            student_goal=case.student_goal,
        )
        return traced_graph_invoke(app, initial, config=config)

    try:
        raw = run_with_tracing(
            reflection=case.reflection,
            student_goal=case.student_goal,
            invoke_fn=_invoke,
            settings=get_settings(),
        )
    except Exception as exc:  # noqa: BLE001
        return ObservedRun(
            error=str(exc),
            latency_ms=(time.perf_counter() - started) * 1000,
        )
    return observed_from_state(raw, latency_ms=(time.perf_counter() - started) * 1000)


def _invoke_no_rag(case: EvalCase) -> ObservedRun:
    """Privacy/risk first; then ungated LLM coaching without retrieval."""
    started = time.perf_counter()

    def _invoke(*, config: Optional[dict[str, Any]] = None) -> ObservedRun:
        del config
        privacy = privacy_and_risk_node({"raw_input": case.reflection})
        if privacy.get("escalation_required") or privacy.get("high_risk_detected"):
            state = {
                "raw_input": "",
                "redacted_input": privacy.get("redacted_input", ""),
                "pii_detected": privacy.get("pii_detected", False),
                "pii_spans": [
                    {k: v for k, v in span.items() if k != "text"}
                    for span in privacy.get("pii_spans", [])
                    if isinstance(span, dict)
                ],
                "high_risk_detected": True,
                "escalation_required": True,
            }
            escalated = escalation_node(state)
            merged = {**state, **escalated}
            return _observed_from_dict(
                merged,
                latency_ms=(time.perf_counter() - started) * 1000,
            )

        redacted = privacy.get("redacted_input", case.reflection)
        user_prompt = (
            f"Student goal (optional): {case.student_goal or 'not provided'}\n\n"
            f"Redacted reflection:\n{redacted}\n\n"
            "Produce coaching. Leave cited_source_ids and cited_chunk_ids empty."
        )
        recommendation = structured_invoke(
            CoachingRecommendation, _NO_RAG_SYSTEM, user_prompt
        )
        body = _format_recommendation_body(recommendation)
        title = "No-RAG baseline coaching"
        return ObservedRun(
            route="coaching",
            title=title,
            body=body,
            primary_challenge=None,
            retrieved_chunk_ids=[],
            cited_chunk_ids=list(recommendation.cited_chunk_ids),
            cited_source_ids=list(recommendation.cited_source_ids),
            action_count=len(recommendation.what_you_could_do_next),
            pii_detected=bool(privacy.get("pii_detected")),
            high_risk_detected=False,
            retrieval_sufficient=False,
            # Baseline has no product evidence gate; that is not scored for no_rag.
            safe_to_display=True,
            escalation_required=False,
            validation_checks={},
            redacted_input=redacted,
            student_facing_text=f"{title}\n{body}".strip(),
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    try:
        return run_with_tracing(
            reflection=case.reflection,
            student_goal=case.student_goal,
            invoke_fn=_invoke,
            settings=get_settings(),
        )
    except Exception as exc:  # noqa: BLE001
        return ObservedRun(
            error=str(exc),
            latency_ms=(time.perf_counter() - started) * 1000,
        )


def _strip_wrapping_quotes(text: str) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1].strip()
    return cleaned


def _format_recommendation_body(recommendation: CoachingRecommendation) -> str:
    parts = [
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
    ]
    return "\n".join(parts)


def _observed_from_dict(state: dict[str, Any], *, latency_ms: float) -> ObservedRun:
    final = state.get("final_response")
    if hasattr(final, "model_dump"):
        final_data = final.model_dump()
    elif isinstance(final, dict):
        final_data = final
    else:
        final_data = {}

    return ObservedRun(
        route=final_data.get("route"),
        title=final_data.get("title", ""),
        body=final_data.get("body", ""),
        primary_challenge=None,
        retrieved_chunk_ids=[],
        cited_chunk_ids=[],
        cited_source_ids=[],
        action_count=0,
        pii_detected=bool(state.get("pii_detected")),
        high_risk_detected=bool(state.get("high_risk_detected")),
        retrieval_sufficient=False,
        safe_to_display=bool(state.get("safe_to_display")),
        escalation_required=bool(state.get("escalation_required")),
        validation_checks={},
        redacted_input=str(state.get("redacted_input") or ""),
        student_facing_text=f"{final_data.get('title', '')}\n{final_data.get('body', '')}",
        latency_ms=latency_ms,
    )
