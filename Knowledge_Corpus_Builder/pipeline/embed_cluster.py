"""Embeddings + hierarchical clustering + near-duplicate merge."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from Knowledge_Corpus_Builder.config.settings import BuilderSettings, get_settings
from Knowledge_Corpus_Builder.schemas.models import ChunkRecord


@dataclass
class ClusterResult:
    chunks: list[ChunkRecord]
    n_clusters: int
    n_merged: int


_embedding_model = None


def get_embedding_model(model_name: str):
    global _embedding_model
    if _embedding_model is None or getattr(_embedding_model, "_model_name", None) != model_name:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(model_name)
        _embedding_model._model_name = model_name  # type: ignore[attr-defined]
    return _embedding_model


def embed_texts(texts: list[str], settings: BuilderSettings | None = None) -> np.ndarray:
    settings = settings or get_settings()
    model = get_embedding_model(settings.embedding_model)
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors, dtype=np.float32)


def _merge_near_duplicates(
    chunks: list[ChunkRecord],
    embeddings: np.ndarray,
    threshold: float,
) -> tuple[list[ChunkRecord], np.ndarray, int]:
    if len(chunks) <= 1:
        return chunks, embeddings, 0

    sim = cosine_similarity(embeddings)
    n = len(chunks)
    keep = [True] * n
    merged_count = 0

    for i in range(n):
        if not keep[i]:
            continue
        for j in range(i + 1, n):
            if not keep[j]:
                continue
            # Prefer merging within same source
            same_source = chunks[i].source_id == chunks[j].source_id
            thresh = threshold if same_source else min(0.97, threshold + 0.03)
            if sim[i, j] >= thresh:
                # Keep longer text
                if len(chunks[j].text) > len(chunks[i].text):
                    chunks[i].text = chunks[j].text
                keep[j] = False
                merged_count += 1

    new_chunks = [c for c, k in zip(chunks, keep) if k]
    new_emb = embeddings[[i for i, k in enumerate(keep) if k]]
    return new_chunks, new_emb, merged_count


def assign_hierarchical_clusters(
    chunks: list[ChunkRecord],
    *,
    settings: BuilderSettings | None = None,
) -> ClusterResult:
    settings = settings or get_settings()
    if not chunks:
        return ClusterResult(chunks=[], n_clusters=0, n_merged=0)

    working = [c.model_copy(deep=True) for c in chunks]
    embeddings = embed_texts([c.text for c in working], settings)
    working, embeddings, n_merged = _merge_near_duplicates(
        working, embeddings, settings.near_duplicate_cosine
    )

    if len(working) == 1:
        working[0].cluster_id = "cluster_000"
        return ClusterResult(chunks=working, n_clusters=1, n_merged=n_merged)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=settings.cluster_distance_threshold,
        metric="cosine",
        linkage="average",
    )
    labels = clustering.fit_predict(embeddings)
    for chunk, label in zip(working, labels):
        chunk.cluster_id = f"cluster_{int(label):03d}"

    # Re-number chunk ids stably after merge
    by_source: dict[str, int] = {}
    for chunk in working:
        idx = by_source.get(chunk.source_id, 0) + 1
        by_source[chunk.source_id] = idx
        stem = chunk.source_id.replace("src_", "chk_", 1)
        chunk.chunk_id = f"{stem}_{idx:03d}"

    n_clusters = len({c.cluster_id for c in working})
    return ClusterResult(chunks=working, n_clusters=n_clusters, n_merged=n_merged)
