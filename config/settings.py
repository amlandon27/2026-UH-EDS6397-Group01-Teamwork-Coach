"""Application settings loaded from environment."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"

    # LLM routing: "gemini" or "ollama" — used by coach UI / CLI
    llm_provider: str = "gemini"
    # Optional secondary provider if primary fails (e.g. gemini quota → ollama)
    # Use "none" to disable fallback.
    llm_fallback_provider: str = "ollama"

    # Evaluation harness overrides (python -m evaluation). Default: Gemini.
    eval_llm_provider: str = "gemini"
    # "none" stops the eval cleanly on Gemini quota instead of falling back to Ollama.
    eval_llm_fallback_provider: str = "none"

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_dir: str = str(ROOT_DIR / ".chroma")
    chroma_collection: str = "teamwork_evidence"
    retrieval_top_k: int = 4
    retrieval_min_score: float = 0.05
    max_repair_attempts: int = 1
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "teamwork-leadership-coach"
    langsmith_endpoint: str = ""
    corpus_dir: str = str(ROOT_DIR / "corpus")


def get_settings() -> Settings:
    return Settings()
