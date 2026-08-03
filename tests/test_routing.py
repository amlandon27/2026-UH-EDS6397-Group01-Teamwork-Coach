"""Routing tests that do not require an LLM API key."""

from agents.coordinator import (
    _route_after_privacy,
    _route_after_retrieval,
    _route_after_validation,
)
from agents.escalation_node import escalation_node
from agents.fallback_node import fallback_node
from agents.privacy_risk_node import privacy_and_risk_node
from contract import AgentState, ValidationResult


def test_privacy_node_redacts_and_flags_risk():
    out = privacy_and_risk_node(
        {"raw_input": "Teammate Alex Rivera said they may be in immediate danger."}
    )
    assert out["pii_detected"] is True
    assert "Alex Rivera" not in out["redacted_input"]
    assert out["high_risk_detected"] is True
    assert out["escalation_required"] is True


def test_route_privacy_to_escalation():
    state = AgentState(raw_input="x", escalation_required=True, high_risk_detected=True)
    assert _route_after_privacy(state) == "escalation"


def test_route_insufficient_evidence_to_fallback():
    state = AgentState(raw_input="x", retrieval_sufficient=False)
    assert _route_after_retrieval(state) == "fallback"


def test_route_repair_then_fallback():
    state = AgentState(
        raw_input="x",
        regeneration_count=0,
        validation_result=ValidationResult(
            safe_to_display=False, repairable=True, reasons=["missing citation"]
        ),
    )
    assert _route_after_validation(state) == "repair"

    state.regeneration_count = 1
    assert _route_after_validation(state) == "fallback"


def test_escalation_and_fallback_nodes():
    esc = escalation_node({"redacted_input": "redacted", "pii_detected": False})
    assert esc["final_response"].route == "escalation"
    assert esc["final_response"].resources

    fb = fallback_node(
        {
            "redacted_input": "redacted",
            "retrieval_sufficient": False,
            "validation_result": None,
        }
    )
    assert fb["final_response"].route == "fallback"
