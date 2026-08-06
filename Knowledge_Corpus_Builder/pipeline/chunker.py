"""Structure-based markdown chunking (headings / slides / paragraphs)."""

from __future__ import annotations

import re

from Knowledge_Corpus_Builder.config.settings import BuilderSettings, get_settings

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
SLIDE_RE = re.compile(
    r"^(?:---|\*\*\*|___)\s*$|^#+\s*slide\s*\d+|^\*\*slide\s*\d+\*\*",
    re.IGNORECASE | re.MULTILINE,
)


def _split_by_headings(markdown: str) -> list[tuple[str, str]]:
    """Return list of (heading, body) sections."""
    matches = list(HEADING_RE.finditer(markdown))
    if not matches:
        return [("", markdown.strip())]

    sections: list[tuple[str, str]] = []
    # Preamble before first heading
    if matches[0].start() > 0:
        pre = markdown[: matches[0].start()].strip()
        if pre:
            sections.append(("Preamble", pre))

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        sections.append((title, body))
    return sections


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    paras = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for para in paras:
        para = para.strip()
        if not para:
            continue
        if size + len(para) + 2 > max_chars and buf:
            chunks.append("\n\n".join(buf))
            buf = [para]
            size = len(para)
        else:
            buf.append(para)
            size += len(para) + 2
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks or [text[:max_chars]]


def structure_chunk_markdown(
    markdown: str,
    *,
    settings: BuilderSettings | None = None,
) -> list[str]:
    """Chunk markdown using headings/slides, then paragraph packing."""
    settings = settings or get_settings()
    min_chars = settings.min_chunk_chars
    max_chars = settings.max_chunk_chars
    text = markdown.strip()
    if not text:
        return []

    # Slide-like separators first
    if SLIDE_RE.search(text):
        pieces = SLIDE_RE.split(text)
        sections = [("", p.strip()) for p in pieces if p and p.strip()]
    else:
        sections = _split_by_headings(text)

    raw_chunks: list[str] = []
    for title, body in sections:
        if not body.strip():
            continue
        # Skip empty/meta-only Docling preambles (repair artifacts belong in repair strip).
        if title.strip().lower() == "preamble" and len(body.strip()) < min_chars:
            continue
        content = f"## {title}\n\n{body}".strip() if title else body.strip()
        for piece in _split_long(content, max_chars):
            raw_chunks.append(piece.strip())

    # Merge tiny trailing fragments into previous
    merged: list[str] = []
    for chunk in raw_chunks:
        if merged and len(chunk) < min_chars:
            merged[-1] = (merged[-1] + "\n\n" + chunk).strip()
        elif len(chunk) < min_chars and not merged:
            merged.append(chunk)
        else:
            merged.append(chunk)

    # Final size clamp
    final: list[str] = []
    for chunk in merged:
        if len(chunk) <= max_chars * 2:
            final.append(chunk)
        else:
            final.extend(_split_long(chunk, max_chars))
    return [c for c in final if c.strip()]
