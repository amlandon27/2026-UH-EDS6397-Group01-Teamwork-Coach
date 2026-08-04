"""Tests for high-risk detection and validation guardrails."""

from contract import CoachingRecommendation, RetrievedEvidence
from guardrails.evidence_validation import validate_recommendation
from guardrails.harmful_advice_validation import detect_high_risk


def test_high_risk_self_harm():
    flagged, hits = detect_high_risk("I want to kill myself after this team conflict.")
    assert flagged is True
    assert hits


def test_ordinary_teamwork_not_high_risk():
    flagged, hits = detect_high_risk(
        "We have unclear roles and missed deadlines on the lab report."
    )
    assert flagged is False
    assert hits == []


def _sample_evidence() -> list[RetrievedEvidence]:
    return [
        RetrievedEvidence(
            chunk_id="chk_accountability_01",
            source_id="src_catme_dimensions",
            text="Accountability interventions include checkpoints.",
            score=0.8,
        )
    ]


def test_validation_passes_clean_recommendation():
    rec = CoachingRecommendation(
        what_may_be_happening="Task ownership may be unclear.",
        what_you_could_do_next=["You could propose a shared task board."],
        how_you_might_say_it=["Could we assign owners for each deliverable?"],
        why_this_may_help="Clear ownership can reduce dropped tasks.",
        what_to_watch_for=["Whether checkpoints are kept"],
        when_to_involve_someone_else="If the team cannot agree on a process after trying.",
        cited_source_ids=["src_catme_dimensions"],
        cited_chunk_ids=["chk_accountability_01"],
    )
    result = validate_recommendation(rec, _sample_evidence())
    assert result.safe_to_display is True


def test_validation_blocks_motive_and_retaliation():
    rec = CoachingRecommendation(
        what_may_be_happening="They are lazy and do not care.",
        what_you_could_do_next=["Publicly shame them in the group chat."],
        cited_source_ids=["src_catme_dimensions"],
        cited_chunk_ids=["chk_accountability_01"],
    )
    result = validate_recommendation(rec, _sample_evidence())
    assert result.safe_to_display is False
    assert result.repairable is False


def test_validation_marks_missing_citations_repairable():
    rec = CoachingRecommendation(
        what_may_be_happening="Coordination may be difficult.",
        what_you_could_do_next=["You could clarify roles."],
        cited_source_ids=[],
        cited_chunk_ids=[],
    )
    result = validate_recommendation(rec, _sample_evidence())
    assert result.safe_to_display is False
    assert result.repairable is True
