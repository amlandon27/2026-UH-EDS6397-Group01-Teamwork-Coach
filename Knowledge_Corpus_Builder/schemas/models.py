"""Pydantic models matching MVP corpus schema + builder fields."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ReviewStatus = Literal["pending", "approved", "rejected", "needs_rewrite"]
TaggingConfidence = Literal["high", "medium", "low"]


class SourceRecord(BaseModel):
    source_id: str
    citation_key: str = ""
    citation_text: str = ""
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
    # Builder-only (safe to strip when copying to MVP)
    domain: Optional[str] = None
    source_path: Optional[str] = None
    folder_name: Optional[str] = None


class ChunkRecord(BaseModel):
    chunk_id: str
    source_id: str
    text: str
    challenge_tags: list[str] = Field(default_factory=list)
    conflict_types: list[str] = Field(default_factory=list)
    possible_conflict_sources: list[str] = Field(default_factory=list)
    signal_tags: list[str] = Field(default_factory=list)
    supported_intervention_tags: list[str] = Field(default_factory=list)
    mentioned_intervention_tags: list[str] = Field(default_factory=list)
    evidence_roles: list[str] = Field(default_factory=list)
    action_levels: list[str] = Field(default_factory=list)
    applicable_contexts: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    human_reviewed: bool = False
    tagging_confidence: TaggingConfidence = "medium"
    # Builder-only
    domain: Optional[str] = None
    cluster_id: Optional[str] = None
    review_status: ReviewStatus = "pending"
    source_path: Optional[str] = None


class InputFileInfo(BaseModel):
    path: str
    relative_path: str
    folder_name: str
    domain: str
    extension: str
    size_bytes: int
    source_id: str


class WorkspaceState(BaseModel):
    """Persisted builder workspace."""

    selected_paths: list[str] = Field(default_factory=list)
    sources: dict[str, SourceRecord] = Field(default_factory=dict)
    raw_markdown: dict[str, str] = Field(default_factory=dict)
    repaired_markdown: dict[str, str] = Field(default_factory=dict)
    chunks: list[ChunkRecord] = Field(default_factory=list)
    last_step: str = "inputs"
    preferred_device: str = "cpu"
    # Per-source convert/repair checkpoint bookkeeping
    convert_errors: dict[str, str] = Field(default_factory=dict)
    convert_done: list[str] = Field(default_factory=list)
    repair_done: list[str] = Field(default_factory=list)
