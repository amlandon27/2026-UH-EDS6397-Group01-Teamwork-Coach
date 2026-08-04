"""Local embedding service using sentence-transformers."""

from __future__ import annotations

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from config.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str | None = None) -> HuggingFaceEmbeddings:
    settings = get_settings()
    name = model_name or settings.embedding_model
    return HuggingFaceEmbeddings(model_name=name)


def embed_query(text: str, settings: Settings | None = None) -> list[float]:
    settings = settings or get_settings()
    model = get_embedding_model(settings.embedding_model)
    return model.embed_query(text)
