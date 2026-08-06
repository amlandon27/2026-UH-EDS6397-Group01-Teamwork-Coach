"""Build (or rebuild) the local Chroma index from hand-built corpus JSON."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from langchain_core.documents import Document

from config.settings import get_settings
from services.embedding_service import get_embedding_model
from langchain_chroma import Chroma


def load_chunks(corpus_dir: Path) -> list[dict]:
    path = corpus_dir / "chunks" / "chunks.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array of chunk objects")
    if data and "chunk_id" not in data[0]:
        keys = sorted(data[0].keys())
        raise ValueError(
            f"{path} does not look like chunks.json (missing 'chunk_id'). "
            f"First object keys={keys}. "
            "Did you copy sources_mvp.json into chunks by mistake? "
            "Use Knowledge_Corpus_Builder/Corpus_Output/chunks/chunks_mvp.json → corpus/chunks/chunks.json"
        )
    return data


def chunk_to_document(chunk: dict) -> Document:
    metadata = {
        "chunk_id": chunk["chunk_id"],
        "source_id": chunk["source_id"],
        "challenge_tags": "|".join(chunk.get("challenge_tags", [])),
        "conflict_types": "|".join(chunk.get("conflict_types", [])),
        "signal_tags": "|".join(chunk.get("signal_tags", [])),
        "supported_intervention_tags": "|".join(
            chunk.get("supported_intervention_tags", [])
        ),
        "evidence_roles": "|".join(chunk.get("evidence_roles", [])),
        "limitations": "|".join(chunk.get("limitations", [])),
        "human_reviewed": bool(chunk.get("human_reviewed", False)),
    }
    return Document(page_content=chunk["text"], metadata=metadata)


def build_index(*, reset: bool = True) -> int:
    settings = get_settings()
    corpus_dir = Path(settings.corpus_dir)
    persist_dir = Path(settings.chroma_persist_dir)

    if reset and persist_dir.exists():
        shutil.rmtree(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    chunks = load_chunks(corpus_dir)
    docs = [chunk_to_document(c) for c in chunks]
    embeddings = get_embedding_model(settings.embedding_model)

    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=settings.chroma_collection,
        persist_directory=str(persist_dir),
    )
    return len(docs)


if __name__ == "__main__":
    count = build_index(reset=True)
    print(f"Indexed {count} evidence chunks into Chroma.")
