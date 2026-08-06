"""Shared state contract for the Teamwork & Leadership Coach MVP.

Contract changes require team review and updated tests.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ReflectionInput(BaseModel):
    """Student-submitted reflection."""

    text: str = Field(..., min_length=1)
    student_goal: Optional[str] = None


class CitationMetadata(BaseModel):
    source_id: str
    citation_key: str
    citation_text: str
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    source_title: Optional[str] = None
    publication_title: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    access_status: Optional[str] = None
    license: Optional[str] = None
    publicly_verifiable: bool = True


class TeamworkDiagnosis(BaseModel):
    primary_challenge: str
    secondary_challenges: list[str] = Field(default_factory=list)
    conflict_type: Optional[str] = None
    observed_signals: list[str] = Field(default_factory=list)
    possible_conflict_sources: list[str] = Field(default_factory=list)
    student_goal: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    uncertainty_notes: list[str] = Field(default_factory=list)
    observation_summary: str = ""
    interpretation_notes: list[str] = Field(default_factory=list)


class RetrievedEvidence(BaseModel):
    chunk_id: str
    source_id: str
    text: str
    score: float = 0.0
    challenge_tags: list[str] = Field(default_factory=list)
    conflict_types: list[str] = Field(default_factory=list)
    signal_tags: list[str] = Field(default_factory=list)
    supported_intervention_tags: list[str] = Field(default_factory=list)
    evidence_roles: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    citation: Optional[CitationMetadata] = None


class CoachingRecommendation(BaseModel):
    what_may_be_happening: str
    what_you_could_do_next: list[str] = Field(default_factory=list)
    how_you_might_say_it: list[str] = Field(default_factory=list)
    why_this_may_help: str = ""
    what_to_watch_for: list[str] = Field(default_factory=list)
    when_to_involve_someone_else: str = ""
    cited_source_ids: list[str] = Field(default_factory=list)
    cited_chunk_ids: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    safe_to_display: bool = False
    repairable: bool = False
    escalation_required: bool = False
    reasons: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)


ResponseRoute = Literal[
    "coaching",
    "fallback",
    "escalation",
]


class FinalResponse(BaseModel):
    route: ResponseRoute
    title: str
    body: str
    recommendation: Optional[CoachingRecommendation] = None
    citations: list[CitationMetadata] = Field(default_factory=list)
    supporting_evidence: list[RetrievedEvidence] = Field(default_factory=list)
    diagnosis: Optional[TeamworkDiagnosis] = None
    resources: list[dict[str, str]] = Field(default_factory=list)
    redacted_input: Optional[str] = None
    pii_detected: bool = False


class AgentState(BaseModel):
    """Root LangGraph state. Only redacted text may flow downstream."""

    raw_input: str = ""
    redacted_input: str = ""
    student_goal: Optional[str] = None
    round_number: int = 1
    regeneration_count: int = 0
    pii_detected: bool = False
    pii_spans: list[dict[str, Any]] = Field(default_factory=list)
    high_risk_detected: bool = False
    out_of_scope: bool = False
    diagnosis_payload: Optional[TeamworkDiagnosis] = None
    retrieved_evidence: list[RetrievedEvidence] = Field(default_factory=list)
    retrieval_sufficient: bool = False
    draft_recommendation: Optional[CoachingRecommendation] = None
    validation_result: Optional[ValidationResult] = None
    escalation_required: bool = False
    safe_to_display: bool = False
    final_response: Optional[FinalResponse] = None
    error_message: Optional[str] = None

    model_config = {"extra": "forbid"}
