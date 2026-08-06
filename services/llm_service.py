"""LLM service: coach uses Ollama; optional Gemini for eval judges."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Type, TypeVar

from langsmith import traceable
from pydantic import BaseModel

from config.settings import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


def get_chat_model(
    settings: Settings | None = None,
    *,
    provider: str | None = None,
):
    """Return a LangChain chat model.

    Coach default is Ollama. Pass ``provider="gemini"`` for the eval judge.
    """
    settings = settings or get_settings()
    chosen = (provider or "ollama").strip().lower()

    if chosen == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_host,
            temperature=0.2,
        )

    if chosen == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.google_api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Add it to .env for the Gemini "
                "evaluator (EVAL_LLM_PROVIDER=gemini)."
            )
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.2,
            timeout=60,
            max_retries=1,
        )

    raise RuntimeError(
        f"Unknown LLM provider={chosen!r}. Use 'ollama' or 'gemini'."
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
    settings: Settings,
    provider: str,
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
        # Fallback: ask for JSON and parse (helps some Ollama / Gemini builds)
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
            raise second_exc from first_exc


@traceable(name="structured_llm_invoke", run_type="llm")
def structured_invoke(
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
    settings: Settings | None = None,
    *,
    provider: str | None = None,
) -> T:
    """Structured LLM call. Default provider is Ollama (coach path)."""
    settings = settings or get_settings()
    chosen = (provider or "ollama").strip().lower()
    started = time.perf_counter()
    result = _invoke_structured(
        schema,
        system_prompt,
        user_prompt,
        settings=settings,
        provider=chosen,
    )
    elapsed = time.perf_counter() - started
    if elapsed > 20:
        print(f"[llm] structured_invoke ({chosen}) finished in {elapsed:.1f}s", flush=True)
    return result


def eval_judge_invoke(
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
    settings: Settings | None = None,
) -> T:
    """Structured call for the evaluation rubric judge (default: Gemini)."""
    settings = settings or get_settings()
    provider = (settings.eval_llm_provider or "gemini").strip().lower()
    return structured_invoke(
        schema,
        system_prompt,
        user_prompt,
        settings,
        provider=provider,
    )
