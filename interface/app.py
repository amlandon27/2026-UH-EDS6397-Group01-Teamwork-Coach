"""Lightweight Streamlit reflection interface for the MVP."""

from __future__ import annotations

import streamlit as st

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

    goal = st.text_input(
        "Optional goal",
        placeholder="e.g., Improve coordination before the next milestone",
    )
    reflection = st.text_area(
        "Describe the teamwork situation",
        height=220,
        placeholder=(
            "Focus on observable behaviors: what happened, when, and how it affected the work. "
            "Avoid names and personal identifiers."
        ),
    )

    if st.button("Get coaching", type="primary", disabled=not reflection.strip()):
        with st.spinner("Running privacy checks, diagnosis, retrieval, and validation..."):
            try:
                result = run_coach(reflection.strip(), goal.strip() or None)
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
