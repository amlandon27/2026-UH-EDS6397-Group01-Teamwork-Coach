"""Student-facing Streamlit reflection interface for the MVP."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import streamlit as st

# Streamlit sets the script directory as its path; add the project root
# so application modules can be imported consistently.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main_system import run_coach

LOGGER = logging.getLogger(__name__)

PRIVACY_NOTICE = """
**Privacy notice:** Do not include names, emails, phone numbers, student IDs, or other identifiers.
If any are detected, they are automatically redacted before coaching. This tool is advisory only and
does not replace instructors, advisors, counselors, or emergency services. Session data is not stored
as a long-term profile.
"""

_INTERNAL_NOTE_MARKER = "\n\nInternal routing note (not model advice):"
_ESCALATION_RESOURCE_MARKER = "\n\nUniversity of Houston and related resources:"


def _public_body(route: str, body: str, has_resources: bool) -> str:
    """Return only content intended for the student-facing interface."""
    public_body = body or ""

    if route == "fallback":
        public_body = public_body.split(_INTERNAL_NOTE_MARKER, maxsplit=1)[0]

    if route == "escalation" and has_resources:
        public_body = public_body.split(
            _ESCALATION_RESOURCE_MARKER,
            maxsplit=1,
        )[0]

    return public_body.strip()


def _format_tag(value: str | None) -> str:
    """Convert an internal controlled tag into readable interface text."""
    if not value:
        return ""
    return value.replace("_", " ").strip().title()


def _citation_target(citation: Any) -> str | None:
    """Return a usable citation URL, preferring the stored source URL."""
    url = getattr(citation, "url", None)
    if url:
        return str(url)

    doi = getattr(citation, "doi", None)
    if not doi:
        return None

    doi_text = str(doi).strip()
    if doi_text.startswith(("http://", "https://")):
        return doi_text
    return f"https://doi.org/{doi_text}"


def _render_diagnosis(diagnosis: Any) -> None:
    """Show a limited, student-friendly explanation instead of raw JSON."""
    with st.expander("How the system interpreted the situation"):
        st.caption(
            "This is a cautious hypothesis based on the reflection, "
            "not a judgment about any teammate."
        )

        summary = getattr(diagnosis, "observation_summary", None)
        if summary:
            st.markdown(f"**Observed pattern:** {summary}")

        primary = _format_tag(getattr(diagnosis, "primary_challenge", None))
        if primary:
            st.markdown(f"**Primary teamwork challenge:** {primary}")

        secondary = [
            _format_tag(item)
            for item in getattr(diagnosis, "secondary_challenges", [])
            if item
        ]
        if secondary:
            st.markdown(
                "**Related challenges:** "
                + ", ".join(secondary)
            )

        uncertainty_notes = getattr(diagnosis, "uncertainty_notes", [])
        if uncertainty_notes:
            st.markdown("**What remains uncertain:**")
            for note in uncertainty_notes:
                st.markdown(f"- {note}")


def _render_citations(citations: list[Any]) -> None:
    """Render supporting citations with clickable source targets."""
    if not citations:
        return

    st.markdown("### Supporting sources")
    for citation in citations:
        citation_text = getattr(citation, "citation_text", "Source")
        target = _citation_target(citation)

        if target:
            st.markdown(f"- [{citation_text}]({target})")
        else:
            st.markdown(f"- {citation_text}")


def _render_resources(resources: list[dict[str, Any]]) -> None:
    """Render escalation resources once in a consistent format."""
    if not resources:
        return

    st.markdown("### Support resources")
    for resource in resources:
        phone = (
            f" | Phone: {resource['phone']}"
            if resource.get("phone")
            else ""
        )
        st.markdown(
            f"- [{resource['name']}]({resource['url']}): "
            f"{resource['detail']}{phone}"
        )


def _render_result(result: Any) -> None:
    """Render one completed workflow response."""
    st.subheader(result.title)

    if result.pii_detected:
        st.warning("Possible PII was detected and redacted before processing.")
        with st.expander("View the redacted reflection"):
            st.write(result.redacted_input)

    if result.route == "escalation":
        st.error("This reflection was routed to human-support resources.")
    elif result.route == "fallback":
        st.warning(
            "The system abstained because it could not produce "
            "validated, evidence-grounded coaching."
        )
    else:
        st.success("Validated coaching response")

    body = _public_body(
        route=result.route,
        body=result.body,
        has_resources=bool(result.resources),
    )
    if body:
        st.markdown(body)

    if result.route == "coaching" and result.diagnosis:
        _render_diagnosis(result.diagnosis)

    _render_citations(result.citations)
    _render_resources(result.resources)


def main() -> None:
    st.set_page_config(
        page_title="Teamwork & Leadership Coach",
        layout="centered",
    )

    st.title("Teamwork & Leadership Coach")
    st.caption("AI-assisted reflection for engineering student teams (MVP)")
    st.info(PRIVACY_NOTICE)

    reflection = st.text_area(
        "Describe the teamwork situation (required)",
        height=220,
        placeholder=(
            "Focus on observable behaviors: what happened, when, and how it "
            "affected the work. Avoid names and personal identifiers."
        ),
    )

    include_goal = st.checkbox("Add a goal (optional)", value=False)
    goal = ""
    if include_goal:
        goal = st.text_input(
            "What would you like help with?",
            placeholder="e.g., Improve coordination before the next milestone",
        )

    can_submit = bool(reflection.strip())
    if not can_submit:
        st.caption(
            "Enter a situation description to continue. A goal is optional."
        )

    if st.button(
        "Get coaching",
        type="primary",
        disabled=not can_submit,
    ):
        with st.spinner(
            "Running privacy checks, diagnosis, retrieval, and validation..."
        ):
            try:
                goal_arg = (
                    goal.strip()
                    if include_goal and goal.strip()
                    else None
                )
                result = run_coach(reflection.strip(), goal_arg)
            except Exception:  # noqa: BLE001
                LOGGER.exception("Coaching workflow failed")
                st.error(
                    "We could not complete this reflection right now. "
                    "Please try again. No unvalidated coaching was displayed."
                )
                return

        _render_result(result)


if __name__ == "__main__":
    main()
