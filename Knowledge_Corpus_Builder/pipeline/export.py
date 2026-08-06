"""Persist workspace and export MVP-compatible corpus JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Knowledge_Corpus_Builder.config.settings import BuilderSettings, get_settings
from Knowledge_Corpus_Builder.schemas.models import (
    ChunkRecord,
    SourceRecord,
    WorkspaceState,
)

MVP_SOURCE_FIELDS = [
    "source_id",
    "citation_key",
    "citation_text",
    "authors",
    "publication_year",
    "source_title",
    "publication_title",
    "doi",
    "url",
    "source_type",
    "access_status",
    "license",
    "publicly_verifiable",
]

MVP_CHUNK_FIELDS = [
    "chunk_id",
    "source_id",
    "text",
    "challenge_tags",
    "conflict_types",
    "possible_conflict_sources",
    "signal_tags",
    "supported_intervention_tags",
    "mentioned_intervention_tags",
    "evidence_roles",
    "action_levels",
    "applicable_contexts",
    "limitations",
    "human_reviewed",
    "tagging_confidence",
]


def output_dirs(settings: BuilderSettings | None = None) -> dict[str, Path]:
    settings = settings or get_settings()
    root = Path(settings.corpus_output_dir)
    dirs = {
        "root": root,
        "markdown": root / "markdown",
        "sources": root / "sources",
        "chunks": root / "chunks",
        "review": root / "review",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def workspace_path(settings: BuilderSettings | None = None) -> Path:
    return output_dirs(settings)["review"] / "workspace.json"


def save_workspace(state: WorkspaceState, settings: BuilderSettings | None = None) -> Path:
    path = workspace_path(settings)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_workspace(settings: BuilderSettings | None = None) -> WorkspaceState:
    path = workspace_path(settings)
    if not path.exists():
        return WorkspaceState()
    data = json.loads(path.read_text(encoding="utf-8"))
    return WorkspaceState.model_validate(data)


def save_markdown_artifacts(
    source_id: str,
    *,
    raw: str | None = None,
    repaired: str | None = None,
    settings: BuilderSettings | None = None,
) -> Path:
    base = output_dirs(settings)["markdown"] / source_id
    base.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        (base / "raw.md").write_text(raw, encoding="utf-8")
    if repaired is not None:
        (base / "repaired.md").write_text(repaired, encoding="utf-8")
    return base


def load_markdown_artifact(
    source_id: str,
    kind: str,
    *,
    settings: BuilderSettings | None = None,
) -> str | None:
    """Load raw.md or repaired.md from disk if present."""
    path = output_dirs(settings)["markdown"] / source_id / f"{kind}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    return text if text.strip() else None


def hydrate_markdown_from_disk(
    state: WorkspaceState,
    *,
    settings: BuilderSettings | None = None,
) -> WorkspaceState:
    """Fill workspace markdown maps from Corpus_Output/markdown checkpoints."""
    for source_id in list(state.sources.keys()) or []:
        if source_id not in state.raw_markdown:
            raw = load_markdown_artifact(source_id, "raw", settings=settings)
            if raw:
                state.raw_markdown[source_id] = raw
                if source_id not in state.convert_done:
                    state.convert_done.append(source_id)
        if source_id not in state.repaired_markdown:
            repaired = load_markdown_artifact(source_id, "repaired", settings=settings)
            if repaired:
                state.repaired_markdown[source_id] = repaired
                if source_id not in state.repair_done:
                    state.repair_done.append(source_id)
    # Also hydrate any markdown folders even if source metadata missing
    md_root = output_dirs(settings)["markdown"]
    if md_root.exists():
        for folder in md_root.iterdir():
            if not folder.is_dir():
                continue
            sid = folder.name
            if sid not in state.raw_markdown:
                raw = load_markdown_artifact(sid, "raw", settings=settings)
                if raw:
                    state.raw_markdown[sid] = raw
                    if sid not in state.convert_done:
                        state.convert_done.append(sid)
            if sid not in state.repaired_markdown:
                repaired = load_markdown_artifact(sid, "repaired", settings=settings)
                if repaired:
                    state.repaired_markdown[sid] = repaired
                    if sid not in state.repair_done:
                        state.repair_done.append(sid)
    return state


def _source_for_export(src: SourceRecord, *, include_builder_fields: bool) -> dict[str, Any]:
    data = src.model_dump()
    # Auto-fill empty citation_text so the coach UI never shows blank bullets
    if not (data.get("citation_text") or "").strip():
        title = (data.get("source_title") or "").strip()
        authors = (data.get("authors") or "").strip()
        year = data.get("publication_year")
        if authors and year and title:
            data["citation_text"] = f"{authors} ({year}). {title}."
        elif authors and title:
            data["citation_text"] = f"{authors}. {title}."
        elif title:
            data["citation_text"] = title
        else:
            data["citation_text"] = (data.get("citation_key") or data.get("source_id") or "Source").replace(
                "_", " "
            )
    if include_builder_fields:
        return data
    return {k: data.get(k) for k in MVP_SOURCE_FIELDS}


def _chunk_for_export(chunk: ChunkRecord, *, include_builder_fields: bool) -> dict[str, Any]:
    data = chunk.model_dump()
    # Mirror review into human_reviewed for MVP compatibility
    if chunk.review_status == "approved":
        data["human_reviewed"] = True
    if include_builder_fields:
        return data
    return {k: data.get(k) for k in MVP_CHUNK_FIELDS}


def export_corpus(
    state: WorkspaceState,
    *,
    include_builder_fields: bool = True,
    only_approved: bool = False,
    settings: BuilderSettings | None = None,
) -> dict[str, Path]:
    dirs = output_dirs(settings)
    chunks = state.chunks
    if only_approved:
        chunks = [c for c in chunks if c.review_status == "approved"]

    if only_approved:
        used_source_ids = {c.source_id for c in chunks}
        sources = [s for s in state.sources.values() if s.source_id in used_source_ids]
    else:
        sources = list(state.sources.values())

    source_payload = [
        _source_for_export(s, include_builder_fields=include_builder_fields) for s in sources
    ]
    chunk_payload = [
        _chunk_for_export(c, include_builder_fields=include_builder_fields) for c in chunks
    ]

    sources_path = dirs["sources"] / "sources.json"
    chunks_path = dirs["chunks"] / "chunks.json"
    sources_path.write_text(json.dumps(source_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    chunks_path.write_text(json.dumps(chunk_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Also write MVP-stripped copies for easy handoff
    mvp_sources = dirs["sources"] / "sources_mvp.json"
    mvp_chunks = dirs["chunks"] / "chunks_mvp.json"
    mvp_sources.write_text(
        json.dumps(
            [_source_for_export(s, include_builder_fields=False) for s in sources],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    mvp_chunks.write_text(
        json.dumps(
            [_chunk_for_export(c, include_builder_fields=False) for c in chunks],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    save_workspace(state, settings)
    return {
        "sources": sources_path,
        "chunks": chunks_path,
        "sources_mvp": mvp_sources,
        "chunks_mvp": mvp_chunks,
    }
