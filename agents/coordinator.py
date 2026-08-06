"""LangGraph coordinator / graph wiring."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, StateGraph

from agents.advice_agent import advice_agent
from agents.diagnosis_retrieval_node import diagnosis_retrieval_node
from agents.escalation_node import escalation_node
from agents.fallback_node import fallback_node
from agents.finalize_node import finalize_coaching_node
from agents.privacy_risk_node import privacy_and_risk_node
from agents.validation_agent import validation_agent
from config.settings import get_settings
from contract import AgentState


def _privacy_boundary(state: Any) -> dict[str, Any]:
    """Remove raw identifiers before workflow state reaches downstream nodes."""
    update = dict(privacy_and_risk_node(state))

    sanitized_spans = [
        {
            key: value
            for key, value in span.items()
            if key != "text"
        }
        for span in update.get("pii_spans", [])
        if isinstance(span, dict)
    ]

    update["raw_input"] = ""
    update["pii_spans"] = sanitized_spans
    return update


def _route_after_privacy(
    state: AgentState,
) -> Literal["escalation", "fallback", "diagnosis_retrieval"]:
    if state.escalation_required or state.high_risk_detected:
        return "escalation"
    if state.out_of_scope:
        return "fallback"
    return "diagnosis_retrieval"


def _route_after_retrieval(state: AgentState) -> Literal["advice", "fallback"]:
    if not state.retrieval_sufficient:
        return "fallback"
    return "advice"


def _route_after_validation(
    state: AgentState,
) -> Literal["finalize", "repair", "fallback", "escalation"]:
    result = state.validation_result
    if result is None:
        return "fallback"
    if result.escalation_required:
        return "escalation"
    if result.safe_to_display:
        return "finalize"
    settings = get_settings()
    if result.repairable and state.regeneration_count < settings.max_repair_attempts:
        return "repair"
    return "fallback"


def _increment_repair(state: Any) -> dict[str, Any]:
    from agents.state_utils import state_get

    return {"regeneration_count": int(state_get(state, "regeneration_count", 0) or 0) + 1}


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("privacy_risk", _privacy_boundary)
    graph.add_node("diagnosis_retrieval", diagnosis_retrieval_node)
    graph.add_node("advice", advice_agent)
    graph.add_node("validation", validation_agent)
    graph.add_node("repair_increment", _increment_repair)
    graph.add_node("finalize", finalize_coaching_node)
    graph.add_node("fallback", fallback_node)
    graph.add_node("escalation", escalation_node)

    graph.set_entry_point("privacy_risk")
    graph.add_conditional_edges(
        "privacy_risk",
        _route_after_privacy,
        {
            "escalation": "escalation",
            "fallback": "fallback",
            "diagnosis_retrieval": "diagnosis_retrieval",
        },
    )
    graph.add_conditional_edges(
        "diagnosis_retrieval",
        _route_after_retrieval,
        {
            "advice": "advice",
            "fallback": "fallback",
        },
    )
    graph.add_edge("advice", "validation")
    graph.add_conditional_edges(
        "validation",
        _route_after_validation,
        {
            "finalize": "finalize",
            "repair": "repair_increment",
            "fallback": "fallback",
            "escalation": "escalation",
        },
    )
    graph.add_edge("repair_increment", "advice")
    graph.add_edge("finalize", END)
    graph.add_edge("fallback", END)
    graph.add_edge("escalation", END)

    return graph.compile()
