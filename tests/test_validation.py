"""Tests for high-risk detection and validation guardrails."""

from agents.advice_agent import _sanitize_recommendation
from agents.finalize_node import finalize_coaching_node
from contract import (
    CitationMetadata,
    CoachingRecommendation,
    RetrievedEvidence,
    TeamworkDiagnosis,
)
from guardrails.citation_validation import validate_citations
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


def test_shoot_for_grade_is_not_high_risk():
    flagged, hits = detect_high_risk(
        "I want to shoot for an A on the milestone and clarify ownership."
    )
    assert flagged is False
    assert hits == []


def test_illegal_to_ignore_policy_is_not_high_risk():
    flagged, hits = detect_high_risk(
        "It would be illegal to ignore the syllabus late-work policy."
    )
    assert flagged is False
    assert hits == []


def test_illegal_lab_access_is_high_risk():
    flagged, hits = detect_high_risk(
        "Is there an illegal way to access the lab overnight without authorization?"
    )
    assert flagged is True
    assert "illegal" in hits


def test_shoot_threat_is_high_risk():
    flagged, hits = detect_high_risk("I want to shoot my teammate after the meeting.")
    assert flagged is True
    assert "shoot" in hits


def _sample_evidence() -> list[RetrievedEvidence]:
    return [
        RetrievedEvidence(
            chunk_id="chk_accountability_01",
            source_id="src_catme_dimensions",
            text=(
                "Accountability interventions include checkpoints, named owners, "
                "and shared task boards so deliverables are not dropped."
            ),
            score=0.8,
            citation=CitationMetadata(
                source_id="src_catme_dimensions",
                citation_key="catme",
                citation_text="CATME teamwork dimensions.",
            ),
        ),
        RetrievedEvidence(
            chunk_id="chk_psych_safety_01",
            source_id="src_google_rework",
            text=(
                "Psychological safety means teammates can speak up about mistakes "
                "without fear of embarrassment or punishment."
            ),
            score=0.7,
            citation=CitationMetadata(
                source_id="src_google_rework",
                citation_key="rework",
                citation_text="Google re:Work psychological safety.",
            ),
        ),
    ]


def _grounded_recommendation() -> CoachingRecommendation:
    return CoachingRecommendation(
        what_may_be_happening=(
            "Task ownership may be unclear, so deliverables risk being dropped."
        ),
        what_you_could_do_next=[
            "You could propose a shared task board with named owners.",
            "One option is to add midpoint checkpoints before the deadline.",
        ],
        how_you_might_say_it=["Could we assign owners for each deliverable?"],
        why_this_may_help=(
            "Clear ownership and checkpoints often reduce dropped tasks."
        ),
        what_to_watch_for=["Whether checkpoints are kept"],
        when_to_involve_someone_else="If the team cannot agree on a process after trying.",
        cited_source_ids=["src_catme_dimensions"],
        cited_chunk_ids=["chk_accountability_01"],
    )


def test_validation_passes_clean_recommendation():
    result = validate_recommendation(_grounded_recommendation(), _sample_evidence())
    assert result.safe_to_display is True
    assert result.checks.get("citations_present") is True
    assert result.checks.get("citations_lexically_grounded") is True


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
    assert result.checks.get("citations_present") is False


def test_validation_requires_chunk_cites_not_sources_alone():
    rec = CoachingRecommendation(
        what_may_be_happening=(
            "Task ownership may be unclear, so deliverables risk being dropped."
        ),
        what_you_could_do_next=[
            "You could propose a shared task board with named owners.",
        ],
        why_this_may_help="Clear ownership and checkpoints often reduce dropped tasks.",
        cited_source_ids=["src_catme_dimensions"],
        cited_chunk_ids=[],
    )
    result = validate_recommendation(rec, _sample_evidence())
    assert result.safe_to_display is False
    assert result.repairable is True
    assert result.checks.get("cited_chunks_from_retrieved") is False


def test_validation_rejects_ungrounded_cites():
    """Citing a retrieved chunk that does not support the claims should fail."""
    rec = CoachingRecommendation(
        what_may_be_happening=(
            "Task ownership may be unclear, so deliverables risk being dropped."
        ),
        what_you_could_do_next=[
            "You could propose a shared task board with named owners.",
            "One option is to add midpoint checkpoints before the deadline.",
        ],
        why_this_may_help=(
            "Clear ownership and checkpoints often reduce dropped tasks."
        ),
        cited_source_ids=["src_google_rework"],
        cited_chunk_ids=["chk_psych_safety_01"],
    )
    checks, reasons = validate_citations(rec, _sample_evidence())
    assert checks["citations_present"] is True
    assert checks["cited_chunks_from_retrieved"] is True
    assert checks["citations_lexically_grounded"] is False
    assert any("vocabulary" in r for r in reasons)

    result = validate_recommendation(rec, _sample_evidence())
    assert result.safe_to_display is False
    assert result.repairable is True


def test_advice_sanitize_does_not_invent_content_or_citations():
    thin = CoachingRecommendation(
        what_may_be_happening="",
        what_you_could_do_next=[],
        how_you_might_say_it=[],
        why_this_may_help="",
        what_to_watch_for=[],
        when_to_involve_someone_else="",
        cited_source_ids=[],
        cited_chunk_ids=[],
    )
    cleaned = _sanitize_recommendation(thin, _sample_evidence())
    assert cleaned.cited_source_ids == []
    assert cleaned.cited_chunk_ids == []
    assert cleaned.what_may_be_happening == ""
    assert cleaned.what_you_could_do_next == []
    assert cleaned.how_you_might_say_it == []
    assert cleaned.why_this_may_help == ""
    assert cleaned.when_to_involve_someone_else == ""


def test_validation_marks_incomplete_coaching_repairable():
    rec = CoachingRecommendation(
        what_may_be_happening="",
        what_you_could_do_next=["Only one step"],
        how_you_might_say_it=[],
        why_this_may_help="",
        when_to_involve_someone_else="",
        cited_source_ids=["src_catme_dimensions"],
        cited_chunk_ids=["chk_accountability_01"],
    )
    result = validate_recommendation(rec, _sample_evidence())
    assert result.safe_to_display is False
    assert result.repairable is True
    assert result.checks.get("has_observation") is False
    assert result.checks.get("has_actions") is False
    assert result.checks.get("has_phrases") is False
    assert result.checks.get("has_why") is False
    assert result.checks.get("has_escalation_guidance") is False


def test_advice_sanitize_drops_hallucinated_ids_only():
    rec = CoachingRecommendation(
        what_may_be_happening="Roles are fuzzy.",
        what_you_could_do_next=["Propose owners.", "Add a checkpoint."],
        how_you_might_say_it=["Could we name owners?"],
        why_this_may_help="Clear ownership helps.",
        when_to_involve_someone_else="If process talks stall.",
        cited_source_ids=["src_catme_dimensions", "src_fabricated"],
        cited_chunk_ids=["chk_accountability_01", "chk_fake"],
    )
    cleaned = _sanitize_recommendation(rec, _sample_evidence())
    assert cleaned.cited_chunk_ids == ["chk_accountability_01"]
    assert cleaned.cited_source_ids == ["src_catme_dimensions"]
    assert cleaned.what_you_could_do_next == ["Propose owners.", "Add a checkpoint."]


def test_finalize_only_surfaces_cited_chunks():
    state = {
        "draft_recommendation": _grounded_recommendation(),
        "diagnosis_payload": TeamworkDiagnosis(
            primary_challenge="accountability",
            confidence=0.7,
        ),
        "retrieved_evidence": _sample_evidence(),
        "redacted_input": "Roles are unclear.",
        "pii_detected": False,
    }
    out = finalize_coaching_node(state)
    final = out["final_response"]
    assert [e.chunk_id for e in final.supporting_evidence] == ["chk_accountability_01"]
    assert [c.source_id for c in final.citations] == ["src_catme_dimensions"]
    assert (
        '- "Could we assign owners for each deliverable?"' in final.body
    )


def test_finalize_does_not_dump_all_evidence_when_cites_missing():
    rec = CoachingRecommendation(
        what_may_be_happening="Coordination gaps.",
        what_you_could_do_next=["Sync once."],
        cited_source_ids=[],
        cited_chunk_ids=[],
    )
    state = {
        "draft_recommendation": rec,
        "diagnosis_payload": None,
        "retrieved_evidence": _sample_evidence(),
        "redacted_input": "x",
        "pii_detected": False,
    }
    out = finalize_coaching_node(state)
    final = out["final_response"]
    assert final.supporting_evidence == []
    assert final.citations == []
