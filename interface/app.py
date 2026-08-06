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


def _citation_label(citation: Any) -> str:
    """Build a non-empty display label for a supporting source."""
    text = (getattr(citation, "citation_text", None) or "").strip()
    if text:
        return text

    title = (getattr(citation, "source_title", None) or "").strip()
    authors = (getattr(citation, "authors", None) or "").strip()
    year = getattr(citation, "publication_year", None)
    publication = (getattr(citation, "publication_title", None) or "").strip()

    parts: list[str] = []
    if authors:
        parts.append(authors)
    if year:
        parts.append(f"({year})")
    if title:
        parts.append(title if not parts else f"{title}.")
    elif publication:
        parts.append(publication)

    if parts:
        # "Authors (year). Title" or just title
        if authors and year and title:
            return f"{authors} ({year}). {title}"
        if authors and title:
            return f"{authors}. {title}"
        return " ".join(parts).strip()

    key = (getattr(citation, "citation_key", None) or "").strip()
    if key:
        return key.replace("_", " ").strip()

    source_id = (getattr(citation, "source_id", None) or "").strip()
    if source_id:
        return source_id.replace("src_", "").replace("_", " ").strip() or "Source"

    return "Source"


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in "".join(
            ch.lower() if ch.isalnum() else " " for ch in (text or "")
        ).split()
        if len(token) > 2
    }


def _section_relevance(section_text: str, evidence: Any) -> float:
    """Rank evidence for a coaching section via token overlap + retrieval score."""
    section_tokens = _tokenize(section_text)
    chunk_tokens = _tokenize(getattr(evidence, "text", "") or "")
    if not section_tokens or not chunk_tokens:
        return float(getattr(evidence, "score", 0.0) or 0.0)
    overlap = len(section_tokens & chunk_tokens) / len(section_tokens)
    return overlap + 0.15 * float(getattr(evidence, "score", 0.0) or 0.0)


def _evidence_for_section(
    section_text: str,
    evidence: list[Any],
    *,
    limit: int = 2,
) -> list[Any]:
    if not evidence:
        return []
    ranked = sorted(
        evidence,
        key=lambda item: _section_relevance(section_text, item),
        reverse=True,
    )
    return ranked[: max(1, limit)]


def _render_section_evidence(evidence_items: list[Any]) -> None:
    """Show retrieved chunk text + source under a coaching paragraph."""
    if not evidence_items:
        return

    for item in evidence_items:
        chunk_text = (getattr(item, "text", None) or "").strip()
        if not chunk_text:
            continue
        # Keep UI readable for long OCR/markdown chunks
        display = chunk_text if len(chunk_text) <= 700 else chunk_text[:700].rstrip() + "…"

        st.markdown("**Chunk text**")
        st.info(display)

        citation = getattr(item, "citation", None)
        source_label = _citation_label(citation) if citation else (
            (getattr(item, "source_id", None) or "Source")
            .replace("src_", "")
            .replace("_", " ")
        )
        target = _citation_target(citation) if citation else None
        if target:
            st.markdown(f"**Source:** [{source_label}]({target})")
        else:
            st.markdown(f"**Source:** {source_label}")


def _render_coaching_sections(result: Any) -> None:
    """Render each coaching paragraph with its supporting retrieved chunks."""
    recommendation = getattr(result, "recommendation", None)
    evidence = list(getattr(result, "supporting_evidence", None) or [])

    if recommendation is None:
        body = _public_body(
            route=result.route,
            body=result.body,
            has_resources=bool(result.resources),
        )
        if body:
            st.markdown(body)
        return

    sections: list[tuple[str, str, bool]] = [
        ("What may be happening", recommendation.what_may_be_happening or "", False),
        (
            "What you could do next",
            "\n".join(recommendation.what_you_could_do_next or []),
            True,
        ),
        (
            "How you might say it",
            "\n".join(recommendation.how_you_might_say_it or []),
            True,
        ),
        ("Why this may help", recommendation.why_this_may_help or "", False),
        (
            "What to watch for",
            "\n".join(recommendation.what_to_watch_for or []),
            True,
        ),
        (
            "When to involve someone else",
            recommendation.when_to_involve_someone_else or "",
            False,
        ),
    ]

    for title, content, as_bullets in sections:
        st.markdown(f"### {title}")
        text = (content or "").strip()
        if not text:
            st.caption("No content for this section.")
        elif as_bullets:
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                st.markdown(f"- {line}")
        else:
            st.markdown(text)

        section_evidence = _evidence_for_section(text or title, evidence, limit=2)
        _render_section_evidence(section_evidence)


def _render_citations(citations: list[Any]) -> None:
    """Render supporting citations with clickable source targets."""
    if not citations:
        return

    st.markdown("### Supporting sources")
    for citation in citations:
        citation_text = _citation_label(citation)
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
        if "scope" in (result.title or "").lower():
            st.info(
                "This input is outside the teamwork coaching scope "
                "(greetings, jailbreaks, or unrelated text are not coached)."
            )
        else:
            st.warning(
                "The system abstained because it could not produce "
                "validated, evidence-grounded coaching."
            )
    else:
        st.success("Validated coaching response")

    if result.route == "coaching":
        _render_coaching_sections(result)
    else:
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
