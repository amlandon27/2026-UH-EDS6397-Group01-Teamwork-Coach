"""Scan Corpus_Inputs for supported source files."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from Knowledge_Corpus_Builder.config.domain_map import domain_from_folder
from Knowledge_Corpus_Builder.schemas.models import InputFileInfo

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".ppt",
    ".docx",
    ".doc",
    ".txt",
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".tif",
    ".tiff",
}


def _slugify(text: str, max_len: int = 48) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return (text[:max_len] or "source").rstrip("_")


def make_source_id(path: Path, inputs_root: Path) -> str:
    try:
        rel = path.relative_to(inputs_root)
    except ValueError:
        rel = path.name
    stem = _slugify(path.stem)
    digest = hashlib.sha1(str(rel).encode("utf-8")).hexdigest()[:8]
    return f"src_{stem}_{digest}"


def scan_inputs(inputs_dir: str | Path) -> list[InputFileInfo]:
    root = Path(inputs_dir)
    if not root.exists():
        return []

    results: list[InputFileInfo] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        folder_name = rel.parts[0] if len(rel.parts) > 1 else "root"
        results.append(
            InputFileInfo(
                path=str(path.resolve()),
                relative_path=str(rel).replace("\\", "/"),
                folder_name=folder_name,
                domain=domain_from_folder(folder_name),
                extension=ext,
                size_bytes=path.stat().st_size,
                source_id=make_source_id(path, root),
            )
        )
    return results
