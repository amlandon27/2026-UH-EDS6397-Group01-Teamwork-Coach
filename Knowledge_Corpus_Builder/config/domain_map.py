"""Map Corpus_Inputs folder names to domain tags."""

from __future__ import annotations

FOLDER_TO_DOMAIN: dict[str, str] = {
    "diagnostic and behavioral frameworks": "diagnostic_behavioral",
    "psychological safety and team climate": "psychological_safety",
    "conflict, coordination, and decision making": "conflict_coordination",
    "team interventions": "interventions",
    "teamwork interventions and practical tools": "interventions",
    "inclusion and equitable participation": "inclusion",
    "inclusion": "inclusion",
}


def domain_from_folder(folder_name: str) -> str:
    key = folder_name.strip().lower()
    if key in FOLDER_TO_DOMAIN:
        return FOLDER_TO_DOMAIN[key]
    slug = (
        key.replace("&", "and")
        .replace(",", "")
        .replace("/", "_")
        .replace(" ", "_")
    )
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "unknown"
