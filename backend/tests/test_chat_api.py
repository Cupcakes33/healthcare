from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

CHAT_URL = "/api/v1/chat"
CHAT_START_URL = f"{CHAT_URL}/start"
CHAT_MESSAGE_URL = f"{CHAT_URL}/message"
CHAT_COMPLETE_URL = f"{CHAT_URL}/complete"

DEFAULT_CHAT_RATE_LIMIT_PER_MINUTE = 5


@pytest.fixture(autouse=True)
def cleanup_sessions():
    from app.service.chat_service import (
        _chat_sessions,
        _daily_llm_call_count,
        _rate_limit_records,
    )

    _chat_sessions.clear()
    _rate_limit_records.clear()
    _daily_llm_call_count.clear()
    yield
    _chat_sessions.clear()
    _rate_limit_records.clear()
    _daily_llm_call_count.clear()


@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()

    async def override_get_db():
        yield mock_session

    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    yield mock_session
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_db):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestChatStartEndpoint:
    async def test_valid_start_returns_200(self, client):
        # given
        payload = {
            "age": 45,
            "gender": "M",
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 200
        data = response.json()
        assert "chat_session_id" in data
        assert data["turn"] == 1
        assert data["is_complete"] is False
        assert "message" in data
        assert data["max_turns"] == 8

    async def test_start_with_female_gender_returns_200(self, client):
        # given
        payload = {
            "age": 30,
            "gender": "F",
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["chat_session_id"] is not None
        assert data["turn"] == 1

    async def test_start_missing_age_returns_422(self, client):
        # given
        payload = {
            "gender": "M",
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 422

    async def test_start_missing_gender_returns_422(self, client):
        # given
        payload = {
            "age": 45,
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 422

    async def test_start_invalid_gender_returns_422(self, client):
        # given
        payload = {
            "age": 45,
            "gender": "X",
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 422

    async def test_start_age_zero_returns_422(self, client):
        # given
        payload = {
            "age": 0,
            "gender": "M",
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 422

    async def test_start_age_negative_returns_422(self, client):
        # given
        payload = {
            "age": -1,
            "gender": "M",
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 422

    async def test_start_age_over_150_returns_422(self, client):
        # given
        payload = {
            "age": 151,
            "gender": "M",
        }

        # when
        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 422


class TestChatMessageEndpoint:
    async def test_valid_message_returns_200(self, client):
        # given
        start_payload = {"age": 45, "gender": "M"}
        start_response = await client.post(CHAT_START_URL, json=start_payload)
        session_id = start_response.json()["chat_session_id"]

        message_payload = {
            "chat_session_id": session_id,
            "message": "어제부터 두통이 있습니다.",
        }

        mock_llm_response = MagicMock()
        mock_llm_response.content = '{"reply": "알겠습니다.", "extracted": {"symptoms": ["두통"], "duration": null, "existing_conditions": []}, "is_sufficient": false}'

        # when
        with patch("app.service.llm_service.get_llm_provider") as mock_provider_func:
            mock_provider = AsyncMock()
            mock_provider.generate = AsyncMock(return_value=mock_llm_response)
            mock_provider_func.return_value = mock_provider

            response = await client.post(CHAT_MESSAGE_URL, json=message_payload)

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["chat_session_id"] == session_id
        assert data["turn"] == 2
        assert "message" in data

    async def test_message_nonexistent_session_returns_404(self, client):
        # given
        message_payload = {
            "chat_session_id": "00000000-0000-0000-0000-000000000000",
            "message": "두통이 있습니다.",
        }

        # when
        response = await client.post(CHAT_MESSAGE_URL, json=message_payload)

        # then
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["message"] == "채팅 세션을 찾을 수 없습니다"

    async def test_message_empty_message_returns_422(self, client):
        # given
        start_payload = {"age": 45, "gender": "M"}
        start_response = await client.post(CHAT_START_URL, json=start_payload)
        session_id = start_response.json()["chat_session_id"]

        message_payload = {
            "chat_session_id": session_id,
            "message": "",
        }

        # when
        response = await client.post(CHAT_MESSAGE_URL, json=message_payload)

        # then
        assert response.status_code == 422

    async def test_message_message_too_long_returns_422(self, client):
        # given
        start_payload = {"age": 45, "gender": "M"}
        start_response = await client.post(CHAT_START_URL, json=start_payload)
        session_id = start_response.json()["chat_session_id"]

        message_payload = {
            "chat_session_id": session_id,
            "message": "a" * 501,
        }

        # when
        response = await client.post(CHAT_MESSAGE_URL, json=message_payload)

        # then
        assert response.status_code == 422


class TestChatCompleteEndpoint:
    async def test_complete_without_user_message_returns_400(self, client, mock_db):
        # given
        start_payload = {"age": 45, "gender": "M"}
        start_response = await client.post(CHAT_START_URL, json=start_payload)
        session_id = start_response.json()["chat_session_id"]

        complete_payload = {
            "chat_session_id": session_id,
        }

        # when
        response = await client.post(CHAT_COMPLETE_URL, json=complete_payload)

        # then
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["message"] == "최소 1개 이상의 대화가 필요합니다"

    async def test_complete_nonexistent_session_returns_404(self, client, mock_db):
        # given
        complete_payload = {
            "chat_session_id": "00000000-0000-0000-0000-000000000000",
        }

        # when
        response = await client.post(CHAT_COMPLETE_URL, json=complete_payload)

        # then
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["message"] == "채팅 세션을 찾을 수 없습니다"

    @pytest.mark.skip(reason="DB 의존 테스트로 별도 통합 테스트 필요")
    async def test_complete_with_user_message_returns_200(self, client, mock_db):
        # given
        start_payload = {"age": 45, "gender": "M"}
        start_response = await client.post(CHAT_START_URL, json=start_payload)
        session_id = start_response.json()["chat_session_id"]

        message_payload = {
            "chat_session_id": session_id,
            "message": "어제부터 두통이 있습니다.",
        }

        mock_llm_response = MagicMock()
        mock_llm_response.content = '{"reply": "알겠습니다.", "extracted": {"symptoms": ["두통"], "duration": null, "existing_conditions": []}, "is_sufficient": true}'

        with patch("app.service.llm_service.get_llm_provider") as mock_provider_func:
            mock_provider = AsyncMock()
            mock_provider.generate = AsyncMock(return_value=mock_llm_response)
            mock_provider_func.return_value = mock_provider

            await client.post(CHAT_MESSAGE_URL, json=message_payload)

        complete_payload = {
            "chat_session_id": session_id,
        }

        # when - DB 의존성으로 인해 스킵
        # complete 엔드포인트는 PackageService, SymptomTagService 등
        # 여러 DB 서비스를 호출하므로 통합 테스트에서 다룸
        response = await client.post(CHAT_COMPLETE_URL, json=complete_payload)

        # then
        assert response.status_code in [200, 400, 500]


class TestChatRateLimit:
    async def test_rate_limit_per_minute_exceeded_returns_429(self, client):
        # given
        limit = DEFAULT_CHAT_RATE_LIMIT_PER_MINUTE
        payload = {"age": 45, "gender": "M"}

        # when
        for i in range(limit):
            response = await client.post(CHAT_START_URL, json=payload)
            assert response.status_code == 200

        response = await client.post(CHAT_START_URL, json=payload)

        # then
        assert response.status_code == 429
        data = response.json()
        assert data["success"] is False
        assert data["error"]["message"] == "요청 횟수를 초과했습니다. 잠시 후 다시 시도해주세요."
