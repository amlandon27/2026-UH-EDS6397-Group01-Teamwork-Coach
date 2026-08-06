"""Suggest taxonomy tags for chunks via local Ollama."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from Knowledge_Corpus_Builder.config.settings import BuilderSettings, get_settings
from Knowledge_Corpus_Builder.pipeline.ollama_client import extract_json_object, ollama_chat
from Knowledge_Corpus_Builder.schemas.models import ChunkRecord

TAG_FIELDS = [
    "challenge_tags",
    "conflict_types",
    "possible_conflict_sources",
    "signal_tags",
    "supported_intervention_tags",
    "mentioned_intervention_tags",
    "evidence_roles",
    "action_levels",
]


def load_taxonomy(path: str | Path | None = None) -> dict[str, list[str]]:
    settings = get_settings()
    tax_path = Path(path or settings.taxonomy_path)
    data = yaml.safe_load(tax_path.read_text(encoding="utf-8"))
    return {k: list(v) for k, v in data.items() if isinstance(v, list)}


def _filter_tags(values: Any, allowed: list[str]) -> list[str]:
    if not isinstance(values, list):
        return []
    allowed_set = set(allowed)
    out: list[str] = []
    for item in values:
        if isinstance(item, str) and item in allowed_set and item not in out:
            out.append(item)
    return out


def suggest_tags_for_chunk(
    chunk: ChunkRecord,
    taxonomy: dict[str, list[str]],
    *,
    settings: BuilderSettings | None = None,
) -> ChunkRecord:
    settings = settings or get_settings()
    tax_blob = yaml.safe_dump(taxonomy, sort_keys=False)
    system = (
        "You tag teamwork evidence chunks for an engineering education coach.\n"
        "Use ONLY values from the provided controlled vocabulary.\n"
        "Mark supported_intervention_tags only when the chunk gives evidence or "
        "implementation guidance; otherwise use mentioned_intervention_tags.\n"
        "Return JSON with keys: "
        + ", ".join(TAG_FIELDS)
        + ", applicable_contexts (string list), limitations (string list), "
        "tagging_confidence (high|medium|low).\n"
        "Do not invent vocabulary terms outside the lists."
    )
    user = (
        f"Domain: {chunk.domain or 'unknown'}\n\n"
        f"Controlled vocabulary:\n{tax_blob}\n\n"
        f"Chunk text:\n{chunk.text}"
    )
    raw = ollama_chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        settings=settings,
        temperature=0.1,
        format_json=True,
    )
    data = extract_json_object(raw)

    updated = chunk.model_copy(deep=True)
    for field in TAG_FIELDS:
        allowed = taxonomy.get(field, taxonomy.get(field.replace("mentioned_", "supported_"), []))
        if field == "mentioned_intervention_tags":
            allowed = taxonomy.get("supported_intervention_tags", [])
        updated.__setattr__(field, _filter_tags(data.get(field), allowed))

    contexts = data.get("applicable_contexts") or []
    limitations = data.get("limitations") or []
    updated.applicable_contexts = [str(x) for x in contexts if str(x).strip()][:6]
    updated.limitations = [str(x) for x in limitations if str(x).strip()][:6]
    conf = str(data.get("tagging_confidence", "medium")).lower()
    if conf not in {"high", "medium", "low"}:
        conf = "medium"
    updated.tagging_confidence = conf  # type: ignore[assignment]
    return updated


def suggest_tags_batch(
    chunks: list[ChunkRecord],
    *,
    settings: BuilderSettings | None = None,
    progress_callback=None,
) -> list[ChunkRecord]:
    settings = settings or get_settings()
    taxonomy = load_taxonomy(settings.taxonomy_path)
    out: list[ChunkRecord] = []
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        try:
            tagged = suggest_tags_for_chunk(chunk, taxonomy, settings=settings)
        except Exception as exc:  # noqa: BLE001
            tagged = chunk.model_copy(deep=True)
            tagged.limitations = list(tagged.limitations) + [f"Tag suggestion failed: {exc}"]
            tagged.tagging_confidence = "low"
        out.append(tagged)
        if progress_callback:
            progress_callback(i + 1, total)
    return out
