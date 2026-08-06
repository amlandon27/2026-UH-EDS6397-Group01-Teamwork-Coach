"""Strip repair artifacts, triage review status, export approved, promote + index.

This is the builder-aligned path for cleaning a pending workspace without
clicking through every chunk in the Streamlit UI:

1. Strip Ollama/Docling preamble junk from repaired.md + chunk text
2. Reject empty / refs-only / still-meta chunks; approve the rest
3. Export only approved MVP JSON
4. Copy into project corpus/ and rebuild Chroma

Usage (from project root)::

    .venv/bin/python -m Knowledge_Corpus_Builder.pipeline.clean_and_promote
"""

from __future__ import annotations

import argparse
import re
import shutil
from collections import Counter
from pathlib import Path

from Knowledge_Corpus_Builder.config.settings import PROJECT_ROOT, BuilderSettings, get_settings
from Knowledge_Corpus_Builder.pipeline.export import (
    export_corpus,
    hydrate_markdown_from_disk,
    load_workspace,
    save_markdown_artifacts,
    save_workspace,
)
from Knowledge_Corpus_Builder.pipeline.markdown_repair import strip_repair_artifacts
from Knowledge_Corpus_Builder.schemas.models import ChunkRecord, WorkspaceState

_REFS_HEADING = re.compile(
    r"(?im)^#{1,6}\s+(references|bibliography|works cited|acknowledgments?)\b"
)
_STILL_META = re.compile(
    r"(?im)here is the cleaned markdown|note:\s*i removed|i also fixed broken"
)
_TAG_FIELDS = (
    "challenge_tags",
    "conflict_types",
    "possible_conflict_sources",
    "signal_tags",
    "supported_intervention_tags",
    "mentioned_intervention_tags",
    "evidence_roles",
    "action_levels",
)


def _has_taxonomy_tags(chunk: ChunkRecord) -> bool:
    return any(getattr(chunk, field) for field in _TAG_FIELDS)


def reject_reason(chunk: ChunkRecord, *, min_chars: int) -> str | None:
    """Return why a cleaned chunk should be rejected, else None."""
    text = (chunk.text or "").strip()
    if len(text) < min_chars:
        return "too_short"
    if _STILL_META.search(text):
        return "repair_meta"
    if _REFS_HEADING.match(text) and len(text) < min_chars * 3:
        return "refs_boilerplate"
    if not _has_taxonomy_tags(chunk):
        return "untagged"
    return None


def clean_workspace(
    state: WorkspaceState,
    *,
    settings: BuilderSettings | None = None,
) -> dict[str, int]:
    """Strip artifacts and set approved/rejected on workspace chunks + repaired.md."""
    settings = settings or get_settings()
    state = hydrate_markdown_from_disk(state, settings=settings)
    min_chars = settings.min_chunk_chars
    stats: Counter[str] = Counter()

    for source_id, repaired in list(state.repaired_markdown.items()):
        cleaned = strip_repair_artifacts(repaired)
        if cleaned != repaired:
            state.repaired_markdown[source_id] = cleaned
            save_markdown_artifacts(source_id, repaired=cleaned, settings=settings)
            stats["repaired_md_cleaned"] += 1

    for chunk in state.chunks:
        before = chunk.text
        chunk.text = strip_repair_artifacts(before)
        if chunk.text != before:
            stats["chunks_text_cleaned"] += 1

        reason = reject_reason(chunk, min_chars=min_chars)
        if reason:
            chunk.review_status = "rejected"
            chunk.human_reviewed = False
            stats[f"rejected_{reason}"] += 1
            stats["rejected"] += 1
        else:
            chunk.review_status = "approved"
            chunk.human_reviewed = True
            stats["approved"] += 1

    state.last_step = "review"
    save_workspace(state, settings)
    stats["total"] = len(state.chunks)
    return dict(stats)


def promote_to_live_corpus(
    *,
    settings: BuilderSettings | None = None,
    project_root: Path | None = None,
) -> dict[str, Path]:
    """Copy approved MVP export into corpus/ for the coach runtime."""
    settings = settings or get_settings()
    root = project_root or PROJECT_ROOT
    export_paths = {
        "sources_mvp": Path(settings.corpus_output_dir) / "sources" / "sources_mvp.json",
        "chunks_mvp": Path(settings.corpus_output_dir) / "chunks" / "chunks_mvp.json",
    }
    for path in export_paths.values():
        if not path.exists():
            raise FileNotFoundError(f"Missing export artifact: {path}")

    dest_sources = root / "corpus" / "sources" / "sources.json"
    dest_chunks = root / "corpus" / "chunks" / "chunks.json"
    dest_sources.parent.mkdir(parents=True, exist_ok=True)
    dest_chunks.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(export_paths["sources_mvp"], dest_sources)
    shutil.copy2(export_paths["chunks_mvp"], dest_chunks)

    # Refuse to promote unreviewed chunks into the live coach corpus.
    import json

    live_chunks = json.loads(dest_chunks.read_text(encoding="utf-8"))
    bad = [c["chunk_id"] for c in live_chunks if not c.get("human_reviewed")]
    if bad:
        raise RuntimeError(
            f"Promote refused: {len(bad)} chunk(s) have human_reviewed=false "
            f"(e.g. {bad[:3]})"
        )
    return {"sources": dest_sources, "chunks": dest_chunks}


def run_clean_export_promote(
    *,
    rebuild_index: bool = True,
    settings: BuilderSettings | None = None,
) -> dict[str, object]:
    settings = settings or get_settings()
    state = load_workspace(settings)
    if not state.chunks:
        raise RuntimeError("Workspace has no chunks to clean.")

    stats = clean_workspace(state, settings=settings)
    # Reload after persist so export sees updated statuses
    state = load_workspace(settings)
    paths = export_corpus(
        state,
        include_builder_fields=True,
        only_approved=True,
        settings=settings,
    )
    promoted = promote_to_live_corpus(settings=settings)

    indexed = None
    if rebuild_index:
        from ingestion.build_index import build_index

        indexed = build_index(reset=True)

    return {
        "stats": stats,
        "export": {k: str(v) for k, v in paths.items()},
        "promoted": {k: str(v) for k, v in promoted.items()},
        "indexed_chunks": indexed,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip Chroma rebuild after promote",
    )
    args = parser.parse_args(argv)
    result = run_clean_export_promote(rebuild_index=not args.no_index)
    stats = result["stats"]
    print("Corpus clean + promote complete.")
    print(f"  total workspace chunks: {stats.get('total')}")
    print(f"  approved: {stats.get('approved', 0)}")
    print(f"  rejected: {stats.get('rejected', 0)}")
    for key, value in sorted(stats.items()):
        if key.startswith("rejected_"):
            print(f"    {key}: {value}")
    print(f"  chunk texts cleaned: {stats.get('chunks_text_cleaned', 0)}")
    print(f"  repaired.md cleaned: {stats.get('repaired_md_cleaned', 0)}")
    if result["indexed_chunks"] is not None:
        print(f"  indexed into Chroma: {result['indexed_chunks']}")


if __name__ == "__main__":
    main()
