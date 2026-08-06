"""Optional LLM-as-judge rubric for coaching quality.

Kept separate from deterministic metrics so offline CI can skip it.
Calibrate against human ratings before trusting absolute scores.
"""

from __future__ import annotations

import json
import re
from typing import Any

from evaluation.schema import CaseResult, EvalCase, MetricScore, ObservedRun
from services.llm_service import get_chat_model

RUBRIC_DIMENSIONS = (
    "observation_vs_interpretation",
    "actionability",
    "proportionality",
    "evidence_alignment",
    "scope_fidelity",
    "tone_non_accusatory",
)

_RUBRIC_PROMPT = """You are evaluating an AI teamwork coach for engineering students.

Score the coach response on each dimension from 1 (poor) to 5 (excellent).
Return ONLY valid JSON with integer scores and a short overall_notes string.

Dimensions:
- observation_vs_interpretation: separates observable behavior from motive/character claims
- actionability: concrete, feasible next steps
- proportionality: advice scaled to severity; not overdramatic
- evidence_alignment: advice appears consistent with evidence-based practices for improving teamwork
- scope_fidelity: stays in teamwork/leadership coaching; no legal/clinical/disciplinary verdicts
- tone_non_accusatory: respectful, non-shaming

Student reflection:
{reflection}

Student goal:
{goal}

Coach route: {route}
Coach response:
{response}
"""


def judge_coaching_quality(case: EvalCase, observed: ObservedRun) -> dict[str, Any]:
    """Return rubric scores for coaching-route cases; empty dict otherwise."""
    if observed.route != "coaching" or observed.error:
        return {}

    model = get_chat_model()
    prompt = _RUBRIC_PROMPT.format(
        reflection=case.reflection,
        goal=case.student_goal or "(none)",
        route=observed.route,
        response=observed.student_facing_text or observed.body,
    )
    raw = model.invoke(prompt)
    content = getattr(raw, "content", raw)
    if isinstance(content, list):
        content = " ".join(str(part) for part in content)
    return _parse_rubric_json(str(content))


def attach_rubric_scores(case: EvalCase, result: CaseResult) -> CaseResult:
    """Judge ``result.observed`` and attach ``rubric_*`` metrics (replaces prior rubric)."""
    result.metrics = [m for m in result.metrics if not m.name.startswith("rubric_")]
    try:
        result.rubric = judge_coaching_quality(case, result.observed)
        for dim in RUBRIC_DIMENSIONS:
            value = result.rubric.get(dim)
            if isinstance(value, (int, float)):
                score = float(value) / 5.0
                result.metrics.append(
                    MetricScore(
                        name=f"rubric_{dim}",
                        value=score,
                        passed=float(value) >= 4.0,
                        detail=f"rubric={value}/5",
                    )
                )
    except Exception as exc:  # noqa: BLE001
        result.rubric = {"error": str(exc)}
    return result


def _parse_rubric_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {"parse_error": True, "raw": text[:500]}
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"parse_error": True, "raw": text[:500]}

    scores: dict[str, Any] = {}
    for dim in RUBRIC_DIMENSIONS:
        value = data.get(dim)
        if isinstance(value, (int, float)):
            scores[dim] = int(max(1, min(5, round(value))))
    scores["overall_notes"] = str(data.get("overall_notes", ""))[:500]
    return scores
