"""Repair Docling markdown with local Ollama (strip ads/noise, fix structure)."""

from __future__ import annotations

import re

from Knowledge_Corpus_Builder.config.settings import BuilderSettings, get_settings
from Knowledge_Corpus_Builder.pipeline.ollama_client import ollama_chat

REPAIR_SYSTEM = """You clean document markdown for a research knowledge corpus.

Rules:
- Remove ads, cookie banners, navigation menus, social share chrome, unrelated site boilerplate.
- Remove repeated headers/footers and page-number noise when obvious.
- Keep all substantive educational/research content.
- Fix broken headings and list structure when possible.
- Preserve tables as markdown tables when feasible.
- Do NOT invent new facts, citations, or sections that were not in the source.
- Do NOT summarize away important detail; repair and clean, do not rewrite as a short abstract.
- Output ONLY the cleaned markdown. No preamble.
"""

_HERE_CLEANED = re.compile(r"(?im)^here is the cleaned markdown:?\s*$")
_NOTE_REMOVED = re.compile(r"(?im)^note:\s*i removed\b.*$")
_I_ALSO_FIXED = re.compile(r"(?im)^i also fixed\b.*$")
_SURE_PREAMBLE = re.compile(r"(?im)^sure[,!]?\s*(?:here(?:'s| is).*?)?$")
_PREAMBLE_HEADING = re.compile(r"(?im)^#{1,6}\s+preamble\s*$")
_FENCE = re.compile(r"(?im)^```(?:markdown)?\s*$")
_META_BULLET = re.compile(
    r"(?im)^(?:[-*]|\d+\.)\s+(?:"
    r"electronic supplementary|acknowledgments?|author contributions?|"
    r"funding|data availability|code availability|conflict of interest|"
    r"ethical approval|informed consent|shazib|figure\s+\d+|table\s+[ivx\d]+|"
    r"navigation menu|social share|cookie|biography"
    r").*$"
)


def strip_repair_artifacts(text: str) -> str:
    """Remove Ollama/Docling meta-preamble that leaks into repaired markdown."""
    if not text or not text.strip():
        return ""

    lines = text.replace("\r\n", "\n").splitlines()
    out: list[str] = []
    skipping_note_block = False

    for line in lines:
        stripped = line.strip()

        if _FENCE.match(stripped):
            continue
        if _HERE_CLEANED.match(stripped) or _I_ALSO_FIXED.match(stripped) or _SURE_PREAMBLE.match(stripped):
            skipping_note_block = False
            continue
        if _NOTE_REMOVED.match(stripped):
            skipping_note_block = True
            continue
        if skipping_note_block:
            if not stripped:
                continue
            if stripped.startswith(("-", "*", "•")) or re.match(r"^\d+\.", stripped):
                continue
            if _META_BULLET.match(stripped):
                continue
            # Real content resumed
            skipping_note_block = False

        if not out and _PREAMBLE_HEADING.match(stripped):
            continue
        if not out and not stripped:
            continue

        out.append(line)

    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def repair_markdown(
    raw_markdown: str,
    *,
    source_title: str = "",
    settings: BuilderSettings | None = None,
) -> str:
    settings = settings or get_settings()
    text = raw_markdown.strip()
    if not text:
        return ""

    # Process in overlapping windows for long docs
    max_chars = settings.repair_max_chars
    if len(text) <= max_chars:
        return _repair_once(text, source_title=source_title, settings=settings)

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # Prefer break at paragraph
        if end < len(text):
            br = text.rfind("\n\n", start + max_chars // 2, end)
            if br > start:
                end = br
        chunk = text[start:end]
        parts.append(_repair_once(chunk, source_title=source_title, settings=settings))
        start = end
    return "\n\n".join(p.strip() for p in parts if p.strip())


def _repair_once(
    markdown: str,
    *,
    source_title: str,
    settings: BuilderSettings,
) -> str:
    user = (
        f"Source title hint: {source_title or '(unknown)'}\n\n"
        f"Clean this markdown:\n\n{markdown}"
    )
    repaired = ollama_chat(
        [
            {"role": "system", "content": REPAIR_SYSTEM},
            {"role": "user", "content": user},
        ],
        settings=settings,
        temperature=0.1,
        format_json=False,
    ).strip()
    return strip_repair_artifacts(repaired)
