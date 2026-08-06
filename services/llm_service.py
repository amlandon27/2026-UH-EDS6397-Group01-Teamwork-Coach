"""LLM service: Gemini and/or local Ollama (llama3.1)."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Type, TypeVar

from langsmith import traceable
from pydantic import BaseModel

from config.settings import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


class GeminiQuotaExceeded(RuntimeError):
    """Raised when the Gemini API returns RESOURCE_EXHAUSTED / 429.

    Evaluation runner stops cleanly on this error. Coach UI may still
    fall back to Ollama when LLM_FALLBACK_PROVIDER=ollama.
    """


def _is_quota_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "resource_exhausted",
            "429",
            "quota exceeded",
            "rate-limits",
            "rate limit",
        )
    )


def _raise_if_quota_error(exc: BaseException) -> None:
    if not _is_quota_error(exc):
        return
    settings = get_settings()
    raise GeminiQuotaExceeded(
        "Gemini API quota exceeded (free tier limit). "
        f"Model={settings.gemini_model}. "
        "Wait for the quota reset, set LLM_PROVIDER=ollama, switch GEMINI_MODEL, "
        "or reduce eval size (e.g. --suites safety or --case-ids ...). "
        f"Original error: {exc}"
    ) from exc


def get_chat_model(settings: Settings | None = None, *, provider: str | None = None):
    """Return a LangChain chat model for the selected provider."""
    settings = settings or get_settings()
    chosen = (provider or settings.llm_provider or "ollama").strip().lower()

    if chosen == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.google_api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your "
                "Gemini API key, or set LLM_PROVIDER=ollama."
            )
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.2,
            timeout=60,
            max_retries=1,
        )

    if chosen == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_host,
            temperature=0.2,
        )

    raise RuntimeError(
        f"Unknown LLM_PROVIDER={chosen!r}. Use 'ollama' or 'gemini'."
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("Model did not return a JSON object")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def _invoke_structured(
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
    *,
    provider: str,
    settings: Settings,
) -> T:
    model = get_chat_model(settings, provider=provider)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        structured = model.with_structured_output(schema)
        result = structured.invoke(messages)
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)
    except Exception as first_exc:
        # Gemini quota should surface as GeminiQuotaExceeded (not swallowed by JSON retry)
        if provider == "gemini" and _is_quota_error(first_exc):
            _raise_if_quota_error(first_exc)

        # Fallback: ask for JSON and parse (helps some Ollama builds)
        try:
            json_system = (
                system_prompt
                + "\n\nRespond with ONLY a JSON object matching this schema:\n"
                + json.dumps(schema.model_json_schema(), indent=2)
            )
            raw = model.invoke(
                [
                    {"role": "system", "content": json_system},
                    {"role": "user", "content": user_prompt},
                ]
            )
            content = getattr(raw, "content", raw)
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            return schema.model_validate(_extract_json_object(str(content)))
        except Exception as second_exc:
            if provider == "gemini" and _is_quota_error(second_exc):
                _raise_if_quota_error(second_exc)
            raise second_exc from first_exc


@traceable(name="structured_llm_invoke", run_type="llm")
def structured_invoke(
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
    settings: Settings | None = None,
) -> T:
    settings = settings or get_settings()
    primary = (settings.llm_provider or "ollama").strip().lower()
    fallback = (settings.llm_fallback_provider or "").strip().lower() or None

    started = time.perf_counter()
    try:
        result = _invoke_structured(
            schema, system_prompt, user_prompt, provider=primary, settings=settings
        )
    except GeminiQuotaExceeded:
        # Prefer Ollama fallback for interactive coaching; re-raise for eval if no fallback
        if primary == "gemini":
            fallback = fallback or "ollama"
        if not fallback or fallback == primary:
            raise
        result = _invoke_structured(
            schema, system_prompt, user_prompt, provider=fallback, settings=settings
        )
    except Exception as exc:
        if primary == "gemini" and _is_quota_error(exc):
            fallback = fallback or "ollama"
            if fallback and fallback != primary:
                result = _invoke_structured(
                    schema,
                    system_prompt,
                    user_prompt,
                    provider=fallback,
                    settings=settings,
                )
            else:
                _raise_if_quota_error(exc)
                raise
        else:
            raise

    elapsed = time.perf_counter() - started
    if elapsed > 20:
        print(f"[llm] structured_invoke finished in {elapsed:.1f}s", flush=True)
    return result
