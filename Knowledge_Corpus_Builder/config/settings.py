"""Settings for the Knowledge Corpus Builder."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BUILDER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BUILDER_ROOT.parent


class BuilderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    corpus_inputs_dir: str = str(BUILDER_ROOT / "Corpus_Inputs")
    corpus_output_dir: str = str(BUILDER_ROOT / "Corpus_Output")
    taxonomy_path: str = str(PROJECT_ROOT / "config" / "teamwork_taxonomy.yaml")

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Docling accelerator: "cpu" | "cuda" | "auto"
    docling_device: str = "cpu"
    docling_num_threads: int = 4

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Cosine distance in [0, 2]; lower => more/finer clusters
    cluster_distance_threshold: float = 0.55
    near_duplicate_cosine: float = 0.92
    min_chunk_chars: int = 120
    max_chunk_chars: int = 1800
    repair_max_chars: int = 12000


def get_settings() -> BuilderSettings:
    return BuilderSettings()
