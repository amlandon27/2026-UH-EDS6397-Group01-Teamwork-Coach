from .chunker import structure_chunk_markdown
from .docling_convert import convert_to_markdown, detect_cuda, resolve_device
from .embed_cluster import assign_hierarchical_clusters
from .export import (
    export_corpus,
    hydrate_markdown_from_disk,
    load_workspace,
    save_workspace,
)
from .markdown_repair import repair_markdown
from .ollama_client import check_ollama
from .scanner import scan_inputs
from .tag_suggester import suggest_tags_batch

# Avoid torch inductor / MSVC `cl` requirement on Windows (Docling models).
import os as _os

_os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
_os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
_os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

__all__ = [
    "assign_hierarchical_clusters",
    "check_ollama",
    "convert_to_markdown",
    "export_corpus",
    "load_workspace",
    "repair_markdown",
    "save_workspace",
    "scan_inputs",
    "structure_chunk_markdown",
    "suggest_tags_batch",
]
