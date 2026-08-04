"""Tests for LangSmith tracing sanitization (no network)."""

from __future__ import annotations

from services.tracing_service import sanitize_trace_payload


def test_sanitize_omits_raw_input():
    payload = {
        "raw_input": "Email jane@uh.edu about the CAD task.",
        "redacted_input": "Email [EMAIL] about the CAD task.",
        "student_goal": "Improve coordination",
    }
    cleaned = sanitize_trace_payload(payload)
    assert cleaned["raw_input"] == "[omitted from telemetry]"
    assert "jane@uh.edu" not in cleaned["redacted_input"]
    assert cleaned["student_goal"] == "Improve coordination"


def test_sanitize_nested_state():
    payload = {
        "state": {
            "raw_input": "Call 713-555-0100",
            "diagnosis_payload": {"primary_challenge": "coordination"},
        }
    }
    cleaned = sanitize_trace_payload(payload)
    assert cleaned["state"]["raw_input"] == "[omitted from telemetry]"
    assert cleaned["state"]["diagnosis_payload"]["primary_challenge"] == "coordination"
