"""Retrieval over the local Chroma evidence corpus."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_chroma import Chroma
from langsmith import traceable

from config.settings import Settings, get_settings
from contract import CitationMetadata, RetrievedEvidence, TeamworkDiagnosis
from services.embedding_service import get_embedding_model


def _synthesize_citation_text(item: dict) -> str:
    """Prefer stored citation_text; otherwise build from title/authors/year."""
    text = (item.get("citation_text") or "").strip()
    if text:
        return text

    title = (item.get("source_title") or "").strip()
    authors = (item.get("authors") or "").strip() or None
    year = item.get("publication_year")
    publication = (item.get("publication_title") or "").strip()

    if authors and year and title:
        return f"{authors} ({year}). {title}."
    if authors and title:
        return f"{authors}. {title}."
    if title and year:
        return f"{title} ({year})."
    if title:
        return title
    if publication:
        return publication
    key = (item.get("citation_key") or item.get("source_id") or "Source").strip()
    return key.replace("_", " ")


def _load_sources(corpus_dir: Path) -> dict[str, CitationMetadata]:
    path = corpus_dir / "sources" / "sources.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["source_id"]: CitationMetadata(
            source_id=item["source_id"],
            citation_key=item.get("citation_key") or item["source_id"],
            citation_text=_synthesize_citation_text(item),
            authors=item.get("authors"),
            publication_year=item.get("publication_year"),
            source_title=item.get("source_title"),
            publication_title=item.get("publication_title"),
            doi=item.get("doi"),
            url=item.get("url"),
            source_type=item.get("source_type"),
            access_status=item.get("access_status"),
            license=item.get("license"),
            publicly_verifiable=bool(item.get("publicly_verifiable", True)),
        )
        for item in raw
    }


def get_vectorstore(settings: Settings | None = None) -> Chroma:
    settings = settings or get_settings()
    embeddings = get_embedding_model(settings.embedding_model)
    return Chroma(
        collection_name=settings.chroma_collection,
        persist_directory=settings.chroma_persist_dir,
        embedding_function=embeddings,
    )


@traceable(name="retrieve_evidence", run_type="retriever")
def retrieve_evidence(
    reflection: str,
    diagnosis: TeamworkDiagnosis | None = None,
    settings: Settings | None = None,
) -> tuple[list[RetrievedEvidence], bool]:
    settings = settings or get_settings()
    corpus_dir = Path(settings.corpus_dir)
    sources = _load_sources(corpus_dir)
    store = get_vectorstore(settings)

    query = reflection
    if diagnosis:
        boost_terms = [
            diagnosis.primary_challenge,
            *diagnosis.secondary_challenges[:2],
            *diagnosis.observed_signals[:3],
            diagnosis.conflict_type or "",
            *diagnosis.possible_conflict_sources[:2],
        ]
        query = reflection + "\n" + " ".join(t for t in boost_terms if t)

    # similarity_search_with_relevance_scores returns higher = more similar for Chroma cosine
    pairs = store.similarity_search_with_relevance_scores(
        query, k=settings.retrieval_top_k
    )

    results: list[RetrievedEvidence] = []
    for doc, score in pairs:
        meta = doc.metadata or {}
        source_id = meta.get("source_id", "")
        if score < settings.retrieval_min_score:
            continue
        results.append(
            RetrievedEvidence(
                chunk_id=meta.get("chunk_id", ""),
                source_id=source_id,
                text=doc.page_content,
                score=float(score),
                challenge_tags=_split_tags(meta.get("challenge_tags", "")),
                conflict_types=_split_tags(meta.get("conflict_types", "")),
                signal_tags=_split_tags(meta.get("signal_tags", "")),
                supported_intervention_tags=_split_tags(
                    meta.get("supported_intervention_tags", "")
                ),
                evidence_roles=_split_tags(meta.get("evidence_roles", "")),
                limitations=_split_tags(meta.get("limitations", "")),
                citation=sources.get(source_id),
            )
        )

    # Lightweight tag boost: prefer chunks sharing primary challenge
    if diagnosis and results:
        primary = diagnosis.primary_challenge
        results.sort(
            key=lambda r: (
                primary in r.challenge_tags,
                r.score,
            ),
            reverse=True,
        )

    sufficient = len(results) >= 1
    return results, sufficient


def _split_tags(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if not value:
        return []
    return [part for part in str(value).split("|") if part]
