from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.schemas.llm import LLMAnalysisResult, LLMRequest, LLMResponse
from app.service.llm_service import (
    AnthropicProvider,
    LLMParsingError,
    LLMProvider,
    LLMServiceError,
    OpenAIProvider,
    _validate_analysis_result,
    analyze_questionnaire,
    get_llm_provider,
)


class TestLLMProviderInterface:

    def test_llm_provider_is_abstract(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_openai_provider_is_llm_provider(self):
        provider = OpenAIProvider(api_key="test-key")
        assert isinstance(provider, LLMProvider)

    def test_anthropic_provider_is_llm_provider(self):
        provider = AnthropicProvider(api_key="test-key")
        assert isinstance(provider, LLMProvider)


class TestGetLLMProvider:

    def test_get_openai_provider(self):
        with patch("app.service.llm_service.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "openai"
            mock_settings.OPENAI_API_KEY = "sk-test"
            provider = get_llm_provider()
            assert isinstance(provider, OpenAIProvider)

    def test_get_anthropic_provider(self):
        with patch("app.service.llm_service.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "anthropic"
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            provider = get_llm_provider()
            assert isinstance(provider, AnthropicProvider)

    def test_invalid_provider_raises_error(self):
        with patch("app.service.llm_service.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "invalid"
            with pytest.raises(LLMServiceError, match="지원하지 않는 LLM Provider"):
                get_llm_provider()


class TestOpenAIProvider:

    @pytest.fixture
    def provider(self):
        return OpenAIProvider(api_key="sk-test")

    @pytest.fixture
    def llm_request(self):
        return LLMRequest(
            system_prompt="테스트 시스템 프롬프트",
            user_prompt="테스트 사용자 프롬프트",
        )

    @pytest.mark.asyncio
    async def test_generate_success(self, provider, llm_request):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "테스트"}'
        mock_response.model = "gpt-4o-mini"

        with patch.object(
            provider._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.generate(llm_request)

        assert isinstance(result, LLMResponse)
        assert result.content == '{"result": "테스트"}'
        assert result.model == "gpt-4o-mini"
        assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_generate_raises_on_failure(self, provider, llm_request):
        with patch.object(
            provider._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=Exception("API 오류"),
        ):
            with pytest.raises(LLMServiceError, match="LLM API 호출 실패"):
                await provider.generate(llm_request)


class TestAnthropicProvider:

    @pytest.fixture
    def provider(self):
        return AnthropicProvider(api_key="sk-ant-test")

    @pytest.fixture
    def llm_request(self):
        return LLMRequest(
            system_prompt="테스트 시스템 프롬프트",
            user_prompt="테스트 사용자 프롬프트",
        )

    @pytest.mark.asyncio
    async def test_generate_success(self, provider, llm_request):
        mock_content_block = MagicMock()
        mock_content_block.text = '{"result": "테스트"}'
        mock_response = MagicMock()
        mock_response.content = [mock_content_block]
        mock_response.model = "claude-sonnet-4-20250514"

        with patch.object(
            provider._client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.generate(llm_request)

        assert isinstance(result, LLMResponse)
        assert result.content == '{"result": "테스트"}'
        assert result.model == "claude-sonnet-4-20250514"
        assert result.provider == "anthropic"

    @pytest.mark.asyncio
    async def test_generate_raises_on_failure(self, provider, llm_request):
        with patch.object(
            provider._client.messages,
            "create",
            new_callable=AsyncMock,
            side_effect=Exception("API 오류"),
        ):
            with pytest.raises(LLMServiceError, match="LLM API 호출 실패"):
                await provider.generate(llm_request)


class TestValidateAnalysisResult:

    def test_filters_invalid_tags(self):
        # given
        result = LLMAnalysisResult(
            summary="요약",
            extracted_tags=["HEADACHE", "INVALID_TAG", "FATIGUE"],
            recommendations=[],
            confidence=0.8,
        )
        valid_tags = ["HEADACHE", "FATIGUE", "DIZZINESS"]
        valid_ids = []

        # when
        validated = _validate_analysis_result(result, valid_tags, valid_ids)

        # then
        assert validated.extracted_tags == ["HEADACHE", "FATIGUE"]

    def test_filters_invalid_package_ids(self):
        # given
        result = LLMAnalysisResult(
            summary="요약",
            extracted_tags=[],
            recommendations=[
                {"package_id": 1, "reason": "이유1", "confidence": 0.9},
                {"package_id": 999, "reason": "이유2", "confidence": 0.7},
            ],
            confidence=0.8,
        )
        valid_tags = []
        valid_ids = [1, 2, 3]

        # when
        validated = _validate_analysis_result(result, valid_tags, valid_ids)

        # then
        assert len(validated.recommendations) == 1
        assert validated.recommendations[0].package_id == 1


class TestAnalyzeQuestionnaire:

    @pytest.fixture
    def valid_llm_response_content(self):
        return json.dumps({
            "summary": "45세 남성 환자가 두통과 피로감을 호소합니다.",
            "extracted_tags": ["HEADACHE", "FATIGUE"],
            "recommendations": [
                {"package_id": 1, "reason": "기본 검진 추천", "confidence": 0.85},
            ],
            "confidence": 0.8,
        })

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock(spec=LLMProvider)

    @pytest.mark.asyncio
    async def test_normal_response_parsing(
        self, sample_questionnaire, sample_packages, sample_symptom_tags,
        mock_provider, valid_llm_response_content,
    ):
        # given
        mock_provider.generate.return_value = LLMResponse(
            content=valid_llm_response_content,
            model="gpt-4o-mini",
            provider="openai",
        )

        # when
        result = await analyze_questionnaire(
            sample_questionnaire, sample_packages, sample_symptom_tags, mock_provider,
        )

        # then
        assert isinstance(result, LLMAnalysisResult)
        assert result.summary == "45세 남성 환자가 두통과 피로감을 호소합니다."
        assert "HEADACHE" in result.extracted_tags
        assert "FATIGUE" in result.extracted_tags
        assert len(result.recommendations) == 1
        mock_provider.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_json_parse_failure(
        self, sample_questionnaire, sample_packages, sample_symptom_tags,
        mock_provider, valid_llm_response_content,
    ):
        # given
        mock_provider.generate.side_effect = [
            LLMResponse(content="잘못된 JSON {{{", model="gpt-4o-mini", provider="openai"),
            LLMResponse(content=valid_llm_response_content, model="gpt-4o-mini", provider="openai"),
        ]

        # when
        result = await analyze_questionnaire(
            sample_questionnaire, sample_packages, sample_symptom_tags, mock_provider,
        )

        # then
        assert isinstance(result, LLMAnalysisResult)
        assert mock_provider.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries_exhausted(
        self, sample_questionnaire, sample_packages, sample_symptom_tags,
        mock_provider,
    ):
        # given
        mock_provider.generate.return_value = LLMResponse(
            content="잘못된 JSON", model="gpt-4o-mini", provider="openai",
        )

        # when / then
        with pytest.raises(LLMParsingError, match="LLM 응답 파싱 실패"):
            await analyze_questionnaire(
                sample_questionnaire, sample_packages, sample_symptom_tags, mock_provider,
            )

    @pytest.mark.asyncio
    async def test_filters_hallucinated_tags_and_packages(
        self, sample_questionnaire, sample_packages, sample_symptom_tags,
        mock_provider,
    ):
        # given
        hallucinated_response = json.dumps({
            "summary": "요약",
            "extracted_tags": ["HEADACHE", "NONEXISTENT_TAG"],
            "recommendations": [
                {"package_id": 1, "reason": "이유", "confidence": 0.9},
                {"package_id": 999, "reason": "환각 패키지", "confidence": 0.7},
            ],
            "confidence": 0.8,
        })
        mock_provider.generate.return_value = LLMResponse(
            content=hallucinated_response, model="gpt-4o-mini", provider="openai",
        )

        # when
        result = await analyze_questionnaire(
            sample_questionnaire, sample_packages, sample_symptom_tags, mock_provider,
        )

        # then
        assert "NONEXISTENT_TAG" not in result.extracted_tags
        assert all(r.package_id in [1, 2, 3] for r in result.recommendations)
