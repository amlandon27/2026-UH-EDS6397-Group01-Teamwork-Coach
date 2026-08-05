"""LLM service backed by Google Gemini."""

from __future__ import annotations

import time
from typing import Type, TypeVar

from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from pydantic import BaseModel

from config.settings import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


class GeminiQuotaExceeded(RuntimeError):
    """Raised when the Gemini API returns RESOURCE_EXHAUSTED / 429."""


def get_chat_model(settings: Settings | None = None) -> ChatGoogleGenerativeAI:
    settings = settings or get_settings()
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your Gemini API key."
        )
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.2,
        timeout=60,
        max_retries=1,
    )


def _raise_if_quota_error(exc: BaseException) -> None:
    message = str(exc)
    if "RESOURCE_EXHAUSTED" in message or " 429" in message or message.startswith("429"):
        settings = get_settings()
        raise GeminiQuotaExceeded(
            "Gemini API quota exceeded (free tier limit). "
            f"Model={settings.gemini_model}. "
            "Wait for the quota reset, switch GEMINI_MODEL in .env to a model "
            "with remaining quota, or reduce eval size "
            "(e.g. --suites safety or --case-ids ...). "
            f"Original error: {message}"
        ) from exc


@traceable(name="structured_llm_invoke", run_type="llm")
def structured_invoke(
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
    settings: Settings | None = None,
) -> T:
    model = get_chat_model(settings)
    structured = model.with_structured_output(schema)
    started = time.perf_counter()
    try:
        result = structured.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
    except Exception as exc:  # noqa: BLE001 - normalize quota errors for callers
        _raise_if_quota_error(exc)
        raise
    elapsed = time.perf_counter() - started
    if elapsed > 20:
        print(f"[llm] structured_invoke finished in {elapsed:.1f}s", flush=True)
    if isinstance(result, schema):
        return result
    return schema.model_validate(result)
