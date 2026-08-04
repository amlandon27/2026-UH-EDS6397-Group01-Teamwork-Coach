"""LangSmith tracing setup with sanitized telemetry payloads.

One coach run is emitted as a single nested trace (graph nodes + LLM/tool spans).
Raw student reflections are never sent to LangSmith; sensitive fields are omitted
or PII-redacted before export.
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional

from langsmith import Client, traceable, tracing_context

from config.settings import Settings, get_settings
from guardrails.pii_redaction import redact_pii

# Fields that must never leave the process as raw student text.
_OMIT_KEYS = frozenset({"raw_input", "reflection"})


def sanitize_trace_payload(payload: Any) -> Any:
    """Recursively omit or redact sensitive values for LangSmith export."""
    if isinstance(payload, Mapping):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            key_str = str(key)
            if key_str in _OMIT_KEYS or key_str.lower() in _OMIT_KEYS:
                out[key_str] = "[omitted from telemetry]"
            else:
                out[key_str] = sanitize_trace_payload(value)
        return out
    if isinstance(payload, list):
        return [sanitize_trace_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return tuple(sanitize_trace_payload(item) for item in payload)
    if isinstance(payload, str):
        redacted, _ = redact_pii(payload)
        return redacted
    return payload


def configure_tracing(settings: Settings | None = None) -> bool:
    """Apply LangSmith env from settings. Returns True when tracing is active."""
    settings = settings or get_settings()

    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint

    return True


def get_tracing_client(settings: Settings | None = None) -> Client:
    """LangSmith client that sanitizes inputs/outputs before upload."""
    settings = settings or get_settings()
    kwargs: dict[str, Any] = {
        "hide_inputs": sanitize_trace_payload,
        "hide_outputs": sanitize_trace_payload,
    }
    if settings.langsmith_api_key:
        kwargs["api_key"] = settings.langsmith_api_key
    if settings.langsmith_endpoint:
        kwargs["api_url"] = settings.langsmith_endpoint
    return Client(**kwargs)


def coach_run_config(
    *,
    student_goal_set: bool,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """RunnableConfig metadata for a single end-to-end coach trace."""
    settings = settings or get_settings()
    return {
        "run_name": "teamwork_coach",
        "tags": ["teamwork-coach", "mvp", settings.langsmith_project],
        "metadata": {
            "app": "teamwork-leadership-coach",
            "student_goal_set": student_goal_set,
            "gemini_model": settings.gemini_model,
            "embedding_model": settings.embedding_model,
            "sanitized_telemetry": True,
        },
    }


def _process_graph_invoke_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Sanitize graph invoke args: omit raw reflection from the root span."""
    state = inputs.get("state")
    state_view: dict[str, Any]
    if hasattr(state, "model_dump"):
        state_view = state.model_dump()
    elif isinstance(state, Mapping):
        state_view = dict(state)
    else:
        state_view = {"state_type": type(state).__name__}
    return {
        "state": sanitize_trace_payload(state_view),
        "config": sanitize_trace_payload(inputs.get("config")),
    }


@traceable(
    name="teamwork_coach_run",
    run_type="chain",
    process_inputs=_process_graph_invoke_inputs,
)
def traced_graph_invoke(app: Any, state: Any, config: Optional[Mapping[str, Any]] = None) -> Any:
    """Invoke the compiled graph under the root coach span."""
    return app.invoke(state, config=dict(config) if config else None)


def run_with_tracing(
    *,
    reflection: str,
    student_goal: str | None,
    invoke_fn: Any,
    settings: Settings | None = None,
) -> Any:
    """Configure LangSmith (if enabled) and run invoke_fn inside one nested trace."""
    settings = settings or get_settings()
    enabled = configure_tracing(settings)
    config = coach_run_config(student_goal_set=bool(student_goal), settings=settings)

    if not enabled:
        return invoke_fn(config=config)

    client = get_tracing_client(settings)
    with tracing_context(
        client=client,
        enabled=True,
        project_name=settings.langsmith_project,
        tags=["teamwork-coach", "mvp"],
        metadata={
            "app": "teamwork-leadership-coach",
            "sanitized_telemetry": True,
        },
    ):
        return invoke_fn(config=config)
