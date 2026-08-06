"""Repair Docling markdown with local Ollama (strip ads/noise, fix structure)."""

from __future__ import annotations

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
    return ollama_chat(
        [
            {"role": "system", "content": REPAIR_SYSTEM},
            {"role": "user", "content": user},
        ],
        settings=settings,
        temperature=0.1,
        format_json=False,
    ).strip()
