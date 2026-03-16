from __future__ import annotations

import abc
from typing import Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import settings
from app.domain.schemas.llm import LLMRequest, LLMResponse

OPENAI_MODEL = "gpt-4o-mini"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 1


class LLMServiceError(Exception):
    pass


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        last_error: Optional[Exception] = None
        for _ in range(MAX_RETRIES + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": request.system_prompt},
                        {"role": "user", "content": request.user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    provider="openai",
                )
            except Exception as e:
                last_error = e
        raise LLMServiceError(f"LLM API 호출 실패: {last_error}")


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        last_error: Optional[Exception] = None
        for _ in range(MAX_RETRIES + 1):
            try:
                response = await self._client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=2048,
                    system=request.system_prompt,
                    messages=[
                        {"role": "user", "content": request.user_prompt},
                    ],
                )
                return LLMResponse(
                    content=response.content[0].text,
                    model=response.model,
                    provider="anthropic",
                )
            except Exception as e:
                last_error = e
        raise LLMServiceError(f"LLM API 호출 실패: {last_error}")


_PROVIDERS = {
    "openai": lambda: OpenAIProvider(api_key=settings.OPENAI_API_KEY),
    "anthropic": lambda: AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY),
}


def get_llm_provider() -> LLMProvider:
    factory = _PROVIDERS.get(settings.LLM_PROVIDER)
    if factory is None:
        raise LLMServiceError(
            f"지원하지 않는 LLM Provider: {settings.LLM_PROVIDER}"
        )
    return factory()
