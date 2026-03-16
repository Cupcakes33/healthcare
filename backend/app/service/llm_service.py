from __future__ import annotations

import abc
import json
from typing import List, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.prompts import build_questionnaire_prompt
from app.domain.schemas.llm import LLMAnalysisResult, LLMRequest, LLMResponse
from app.domain.schemas.patient import QuestionnaireRequest



class LLMServiceError(Exception):
    pass


class LLMParsingError(LLMServiceError):
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
        for _ in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
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
        for _ in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await self._client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
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


def _validate_analysis_result(
    result: LLMAnalysisResult,
    valid_tag_codes: List[str],
    valid_package_ids: List[int],
) -> LLMAnalysisResult:
    result.extracted_tags = [
        tag for tag in result.extracted_tags if tag in valid_tag_codes
    ]
    result.recommendations = [
        rec for rec in result.recommendations
        if rec.package_id in valid_package_ids
    ]
    return result


async def analyze_questionnaire(
    questionnaire: QuestionnaireRequest,
    packages: List[dict],
    symptom_tags: List[dict],
    provider: LLMProvider,
) -> LLMAnalysisResult:
    system_prompt, user_prompt = build_questionnaire_prompt(
        questionnaire, packages, symptom_tags,
    )

    valid_tag_codes = [t["code"] for t in symptom_tags]
    valid_package_ids = [p["id"] for p in packages]

    llm_request = LLMRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    for attempt in range(settings.LLM_MAX_RETRIES + 1):
        try:
            response = await provider.generate(llm_request)
            parsed = json.loads(response.content)
            result = LLMAnalysisResult(**parsed)
            return _validate_analysis_result(
                result, valid_tag_codes, valid_package_ids,
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if attempt >= settings.LLM_MAX_RETRIES:
                raise LLMParsingError(
                    f"LLM 응답 파싱 실패: {e}"
                ) from e

    raise LLMParsingError("LLM 응답 파싱 실패: 최대 재시도 초과")
