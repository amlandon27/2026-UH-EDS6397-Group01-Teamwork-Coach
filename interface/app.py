"""Lightweight Streamlit reflection interface for the MVP."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit sets the script dir as cwd/path; add project root for imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main_system import run_coach

PRIVACY_NOTICE = """
**Privacy notice:** Do not include names, emails, phone numbers, student IDs, or other identifiers.
If any are detected, they are automatically redacted before coaching. This tool is advisory only and
does not replace instructors, advisors, counselors, or emergency services. Session data is not stored
as a long-term profile.
"""


def main() -> None:
    st.set_page_config(page_title="Teamwork & Leadership Coach", layout="centered")
    st.title("Teamwork & Leadership Coach")
    st.caption("AI-assisted reflection for engineering student teams (MVP)")
    st.info(PRIVACY_NOTICE)

    reflection = st.text_area(
        "Describe the teamwork situation (required)",
        height=220,
        placeholder=(
            "Focus on observable behaviors: what happened, when, and how it affected the work. "
            "Avoid names and personal identifiers."
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
        st.caption("Enter a situation description to continue. A goal is optional.")

    if st.button("Get coaching", type="primary", disabled=not can_submit):
        with st.spinner("Running privacy checks, diagnosis, retrieval, and validation..."):
            try:
                goal_arg = goal.strip() if include_goal and goal.strip() else None
                result = run_coach(reflection.strip(), goal_arg)
            except Exception as exc:  # noqa: BLE001 - show friendly UI error
                st.error(f"Something went wrong: {exc}")
                return

        st.subheader(result.title)
        if result.pii_detected:
            st.warning("Possible PII was detected and redacted before processing.")
            with st.expander("Redacted reflection"):
                st.write(result.redacted_input)

        if result.route == "escalation":
            st.error("This reflection was routed to human-support resources.")
        elif result.route == "fallback":
            st.warning("The system abstained from ordinary coaching.")
        else:
            st.success("Validated coaching response")

        st.markdown(result.body)

        if result.diagnosis:
            with st.expander("Diagnosis (structured)"):
                st.json(result.diagnosis.model_dump())

        if result.citations:
            st.markdown("### Citations")
            for cite in result.citations:
                st.markdown(f"- {cite.citation_text}")
                if cite.doi or cite.url:
                    st.caption(cite.doi or cite.url)

        if result.resources:
            st.markdown("### Resources")
            for res in result.resources:
                phone = f" — {res['phone']}" if res.get("phone") else ""
                st.markdown(f"- [{res['name']}]({res['url']}): {res['detail']}{phone}")


if __name__ == "__main__":
    main()
