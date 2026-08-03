"""Evidence and citation validation helpers."""

from __future__ import annotations

import re

from config.safety_policy import (
    MOTIVE_CLAIM_PATTERNS,
    OVERCONFIDENCE_PATTERNS,
    PROHIBITED_ADVICE_PATTERNS,
)
from contract import CoachingRecommendation, RetrievedEvidence, ValidationResult
from guardrails.pii_redaction import contains_pii


def validate_recommendation(
    recommendation: CoachingRecommendation,
    evidence: list[RetrievedEvidence],
    *,
    escalation_required: bool = False,
) -> ValidationResult:
    checks: dict[str, bool] = {}
    reasons: list[str] = []

    if escalation_required:
        return ValidationResult(
            safe_to_display=False,
            repairable=False,
            escalation_required=True,
            reasons=["High-risk content requires escalation, not coaching display."],
            checks={"escalation_clear": False},
        )

    retrieved_source_ids = {e.source_id for e in evidence}
    retrieved_chunk_ids = {e.chunk_id for e in evidence}

    checks["has_evidence"] = len(evidence) > 0
    if not checks["has_evidence"]:
        reasons.append("No retrieved evidence available.")

    checks["citations_from_retrieved_sources"] = all(
        sid in retrieved_source_ids for sid in recommendation.cited_source_ids
    ) and len(recommendation.cited_source_ids) > 0
    if not checks["citations_from_retrieved_sources"]:
        reasons.append("Citations missing or not limited to retrieved sources.")

    checks["cited_chunks_from_retrieved"] = all(
        cid in retrieved_chunk_ids for cid in recommendation.cited_chunk_ids
    )
    if recommendation.cited_chunk_ids and not checks["cited_chunks_from_retrieved"]:
        reasons.append("Cited chunk ids are not in retrieved evidence.")

    full_text = _flatten(recommendation)
    checks["no_pii"] = not contains_pii(full_text)
    if not checks["no_pii"]:
        reasons.append("Draft contains possible PII.")

    prohibited = _matches_any(full_text, PROHIBITED_ADVICE_PATTERNS)
    checks["no_prohibited_advice"] = not prohibited
    if prohibited:
        reasons.append("Draft contains prohibited advice patterns.")

    motive = _matches_any(full_text, MOTIVE_CLAIM_PATTERNS)
    checks["no_motive_claims"] = not motive
    if motive:
        reasons.append("Draft contains unsupported motive/character claims.")

    overconfident = _matches_any(full_text, OVERCONFIDENCE_PATTERNS)
    checks["not_overconfident"] = not overconfident
    if overconfident:
        reasons.append("Draft overstates certainty.")

    checks["has_actions"] = len(recommendation.what_you_could_do_next) > 0
    if not checks["has_actions"]:
        reasons.append("Draft lacks concrete next-step options.")

    # Hard failures vs repairable
    hard_keys = [
        "has_evidence",
        "no_prohibited_advice",
        "no_motive_claims",
    ]
    repairable_keys = [
        "citations_from_retrieved_sources",
        "cited_chunks_from_retrieved",
        "no_pii",
        "not_overconfident",
        "has_actions",
    ]

    hard_fail = any(not checks[k] for k in hard_keys if k in checks)
    repairable_fail = any(not checks[k] for k in repairable_keys if k in checks)

    if hard_fail:
        return ValidationResult(
            safe_to_display=False,
            repairable=False,
            escalation_required=False,
            reasons=reasons,
            checks=checks,
        )

    if repairable_fail:
        return ValidationResult(
            safe_to_display=False,
            repairable=True,
            escalation_required=False,
            reasons=reasons,
            checks=checks,
        )

    return ValidationResult(
        safe_to_display=True,
        repairable=False,
        escalation_required=False,
        reasons=[],
        checks=checks,
    )


def _flatten(rec: CoachingRecommendation) -> str:
    parts = [
        rec.what_may_be_happening,
        " ".join(rec.what_you_could_do_next),
        " ".join(rec.how_you_might_say_it),
        rec.why_this_may_help,
        " ".join(rec.what_to_watch_for),
        rec.when_to_involve_someone_else,
    ]
    return "\n".join(parts)


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)
