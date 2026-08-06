"""Ollama client helpers for markdown repair and tagging."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from Knowledge_Corpus_Builder.config.settings import BuilderSettings, get_settings


class OllamaError(RuntimeError):
    pass


def check_ollama(settings: BuilderSettings | None = None) -> tuple[bool, str]:
    settings = settings or get_settings()
    try:
        with httpx.Client(base_url=settings.ollama_host, timeout=5.0) as client:
            r = client.get("/api/tags")
            r.raise_for_status()
            models = [m.get("name", "") for m in r.json().get("models", [])]
            wanted = settings.ollama_model
            if any(wanted in m or m.startswith(wanted.split(":")[0]) for m in models):
                return True, f"Ollama OK — model available ({wanted})"
            return False, (
                f"Ollama reachable but model '{wanted}' not found. "
                f"Installed: {models or 'none'}. Run: ollama pull {wanted}"
            )
    except Exception as exc:  # noqa: BLE001
        return False, f"Ollama not reachable at {settings.ollama_host}: {exc}"


def ollama_chat(
    messages: list[dict[str, str]],
    *,
    settings: BuilderSettings | None = None,
    temperature: float = 0.2,
    format_json: bool = False,
    timeout: float = 300.0,
) -> str:
    settings = settings or get_settings()
    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if format_json:
        payload["format"] = "json"

    try:
        with httpx.Client(base_url=settings.ollama_host, timeout=timeout) as client:
            r = client.post("/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
            content = data.get("message", {}).get("content", "")
            if not content:
                raise OllamaError("Empty response from Ollama")
            return content
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama chat failed: {exc}") from exc


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise OllamaError("Could not parse JSON from model response")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise OllamaError("JSON root must be an object")
    return data
