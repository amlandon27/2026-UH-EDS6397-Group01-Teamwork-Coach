"""LLM service backed by Google Gemini."""

from __future__ import annotations

from typing import Type, TypeVar

from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from pydantic import BaseModel

from config.settings import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


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
    )


@traceable(name="structured_llm_invoke", run_type="llm")
def structured_invoke(
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
    settings: Settings | None = None,
) -> T:
    model = get_chat_model(settings)
    structured = model.with_structured_output(schema)
    result = structured.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    if isinstance(result, schema):
        return result
    return schema.model_validate(result)
