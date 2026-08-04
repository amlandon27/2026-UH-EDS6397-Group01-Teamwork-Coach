"""Advice generation agent."""

from __future__ import annotations

import json
from typing import Any

from agents.state_utils import state_get
from contract import CoachingRecommendation, RetrievedEvidence, TeamworkDiagnosis
from services.llm_service import structured_invoke

SYSTEM_PROMPT = """You are a teamwork and leadership coach for engineering students.
Create practical, proportionate coaching using ONLY the redacted reflection, diagnosis, and retrieved evidence.

Rules:
- Stay within teamwork/leadership coaching.
- Encourage action without commands (prefer "you could", "one option is").
- No unsupported diagnoses, accusations, or motive claims.
- No overconfidence words like definitely/certainly/obviously.
- No PII.
- Cite only provided source_ids and chunk_ids.
- Include concrete next steps and example phrasing.
- Note when to involve an instructor/advisor without determining fault.
"""


def advice_agent(state: Any) -> dict[str, Any]:
    diagnosis: TeamworkDiagnosis = state_get(state, "diagnosis_payload")
    evidence: list[RetrievedEvidence] = state_get(state, "retrieved_evidence", []) or []
    if not evidence:
        return {"draft_recommendation": None}
    reflection = state_get(state, "redacted_input", "") or ""
    repair_notes = state_get(state, "validation_result")

    evidence_payload = [
        {
            "chunk_id": e.chunk_id,
            "source_id": e.source_id,
            "text": e.text,
            "supported_intervention_tags": e.supported_intervention_tags,
            "limitations": e.limitations,
            "citation_text": e.citation.citation_text if e.citation else "",
        }
        for e in evidence
    ]

    repair_block = ""
    if repair_notes and getattr(repair_notes, "repairable", False):
        repair_block = (
            "\nPrevious draft failed validation for repairable reasons:\n"
            + "\n".join(f"- {r}" for r in repair_notes.reasons)
            + "\nRevise to fix those issues.\n"
        )

    user_prompt = f"""
Redacted reflection:
{reflection}

Diagnosis JSON:
{diagnosis.model_dump_json(indent=2)}

Retrieved evidence JSON:
{json.dumps(evidence_payload, indent=2)}
{repair_block}
Produce a coaching recommendation with cited_source_ids and cited_chunk_ids drawn only from the evidence list.
"""

    recommendation = structured_invoke(
        CoachingRecommendation, SYSTEM_PROMPT, user_prompt
    )
    return {"draft_recommendation": recommendation}
