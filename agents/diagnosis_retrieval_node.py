"""Combined diagnosis + retrieval node (MVP)."""

from __future__ import annotations

from typing import Any

from agents.state_utils import state_get
from contract import TeamworkDiagnosis
from services.llm_service import structured_invoke
from services.retrieval_service import retrieve_evidence

SYSTEM_PROMPT = """You are a teamwork diagnosis assistant for engineering student teams.
Return structured diagnosis only.

Rules:
- Separate observable behavior from interpretation.
- Treat possible causes as hypotheses, not facts.
- Do not infer motives, character, or laziness.
- Do not assume silence means agreement.
- Use controlled challenge tags when possible:
  accountability, communication_breakdown, coordination, decision_making,
  inclusion, psychological_safety, role_ambiguity, uneven_work_distribution
- Conflict types: task_conflict, process_conflict, interpersonal_conflict, certainty_conflict
- Be cautious; note uncertainty.
"""


def diagnosis_retrieval_node(state: Any) -> dict[str, Any]:
    reflection = state_get(state, "redacted_input", "") or ""
    student_goal = state_get(state, "student_goal")

    user_prompt = (
        f"Student goal (optional): {student_goal or 'not provided'}\n\n"
        f"Redacted reflection:\n{reflection}\n\n"
        "Produce a cautious teamwork diagnosis."
    )

    diagnosis = structured_invoke(TeamworkDiagnosis, SYSTEM_PROMPT, user_prompt)
    if student_goal and not diagnosis.student_goal:
        diagnosis.student_goal = student_goal

    evidence, sufficient = retrieve_evidence(reflection, diagnosis)
    return {
        "diagnosis_payload": diagnosis,
        "retrieved_evidence": evidence,
        "retrieval_sufficient": sufficient,
    }
