from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.schemas.llm import LLMRequest, LLMResponse
from app.service.llm_service import (
    AnthropicProvider,
    LLMProvider,
    LLMServiceError,
    OpenAIProvider,
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
    async def test_generate_retry_on_failure(self, provider, llm_request):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_response.model = "gpt-4o-mini"

        with patch.object(
            provider._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=[Exception("API 오류"), mock_response],
        ):
            result = await provider.generate(llm_request)

        assert result.content == '{"result": "ok"}'

    @pytest.mark.asyncio
    async def test_generate_raises_after_retry(self, provider, llm_request):
        with patch.object(
            provider._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=[Exception("1차 실패"), Exception("2차 실패")],
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
    async def test_generate_retry_on_failure(self, provider, llm_request):
        mock_content_block = MagicMock()
        mock_content_block.text = '{"result": "ok"}'
        mock_response = MagicMock()
        mock_response.content = [mock_content_block]
        mock_response.model = "claude-sonnet-4-20250514"

        with patch.object(
            provider._client.messages,
            "create",
            new_callable=AsyncMock,
            side_effect=[Exception("API 오류"), mock_response],
        ):
            result = await provider.generate(llm_request)

        assert result.content == '{"result": "ok"}'

    @pytest.mark.asyncio
    async def test_generate_raises_after_retry(self, provider, llm_request):
        with patch.object(
            provider._client.messages,
            "create",
            new_callable=AsyncMock,
            side_effect=[Exception("1차 실패"), Exception("2차 실패")],
        ):
            with pytest.raises(LLMServiceError, match="LLM API 호출 실패"):
                await provider.generate(llm_request)
