"""Unit tests for diagnosis challenge-tag normalization."""

from __future__ import annotations

from contract import TeamworkDiagnosis
from agents.diagnosis_retrieval_node import (
    CONFLICT_TO_CHALLENGE,
    normalize_diagnosis,
)


def test_moves_interpersonal_conflict_out_of_primary():
    diag = TeamworkDiagnosis(
        primary_challenge="interpersonal_conflict",
        confidence=0.6,
    )
    out = normalize_diagnosis(diag)
    assert out.primary_challenge == "psychological_safety"
    assert out.conflict_type == "interpersonal_conflict"


def test_prefers_secondary_challenge_over_default_map():
    diag = TeamworkDiagnosis(
        primary_challenge="process_conflict",
        secondary_challenges=["communication_breakdown", "coordination"],
        confidence=0.7,
    )
    out = normalize_diagnosis(diag)
    assert out.primary_challenge == "communication_breakdown"
    assert out.conflict_type == "process_conflict"
    assert "communication_breakdown" not in out.secondary_challenges
    assert "coordination" in out.secondary_challenges


def test_keeps_valid_challenge_primary():
    diag = TeamworkDiagnosis(
        primary_challenge="accountability",
        conflict_type="process_conflict",
        secondary_challenges=["uneven_work_distribution", "task_conflict"],
        confidence=0.8,
    )
    out = normalize_diagnosis(diag)
    assert out.primary_challenge == "accountability"
    assert out.conflict_type == "process_conflict"
    assert out.secondary_challenges == ["uneven_work_distribution"]


def test_default_maps_cover_all_conflict_types():
    for conflict, expected in CONFLICT_TO_CHALLENGE.items():
        out = normalize_diagnosis(
            TeamworkDiagnosis(primary_challenge=conflict, confidence=0.5)
        )
        assert out.primary_challenge == expected
        assert out.conflict_type == conflict


def test_empty_primary_stays_empty_when_low_signal():
    out = normalize_diagnosis(
        TeamworkDiagnosis(
            primary_challenge="",
            confidence=0.02,
            observation_summary="out of scope greeting",
        )
    )
    assert out.primary_challenge == ""
