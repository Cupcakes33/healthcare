from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.domain.schemas.patient import (
    InputSummary,
    PackageRecommendation,
    QuestionnaireResponse,
    RedFlagResult,
)
from app.main import app

QUESTIONNAIRE_URL = "/api/v1/questionnaire"
RESULT_URL = "/api/v1/result"

MOCK_SESSION_KEY = "550e8400-e29b-41d4-a716-446655440000"

MOCK_RESPONSE = QuestionnaireResponse(
    session_key=MOCK_SESSION_KEY,
    summary="45세 남성 환자가 두통과 피로감을 호소합니다.",
    input_summary=InputSummary(
        age=45,
        gender="M",
        symptoms=["두통", "피로감"],
        duration="2주",
        existing_conditions=["고혈압"],
    ),
    red_flag=RedFlagResult(level="NONE", matched_rules=[], message=""),
    recommendations=[
        PackageRecommendation(
            package_id=1,
            package_name="기본 종합검진",
            match_score=0.85,
            reason="두통 관련 검진 추천",
            matched_tags=["HEADACHE"],
        ),
    ],
)


@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def override_get_db():
        yield mock_session

    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    yield mock_session
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_db):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestPostQuestionnaire:
    async def test_valid_request_returns_200(self, client, mock_db):
        # given
        payload = {
            "age": 45,
            "gender": "M",
            "symptoms": ["HEADACHE", "FATIGUE"],
            "duration": "2주",
            "existing_conditions": ["고혈압"],
        }

        with patch(
            "app.api.v1.endpoints.questionnaire.QuestionnaireService"
        ) as MockService:
            instance = MockService.return_value
            instance.analyze = AsyncMock(return_value=MOCK_RESPONSE)

            # when
            response = await client.post(QUESTIONNAIRE_URL, json=payload)

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["session_key"] == MOCK_SESSION_KEY
        assert data["summary"] is not None
        assert data["input_summary"]["age"] == 45
        assert data["red_flag"]["level"] == "NONE"
        assert len(data["recommendations"]) == 1
        QuestionnaireResponse(**data)

    async def test_missing_required_field_returns_422(self, client, mock_db):
        # given
        payload = {"age": 45, "gender": "M"}

        # when
        response = await client.post(QUESTIONNAIRE_URL, json=payload)

        # then
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_gender_returns_422(self, client, mock_db):
        # given
        payload = {
            "age": 45,
            "gender": "X",
            "symptoms": ["HEADACHE"],
            "duration": "1주",
        }

        # when
        response = await client.post(QUESTIONNAIRE_URL, json=payload)

        # then
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    async def test_negative_age_returns_422(self, client, mock_db):
        # given
        payload = {
            "age": -1,
            "gender": "M",
            "symptoms": ["HEADACHE"],
            "duration": "1주",
        }

        # when
        response = await client.post(QUESTIONNAIRE_URL, json=payload)

        # then
        assert response.status_code == 422

    async def test_age_over_150_returns_422(self, client, mock_db):
        # given
        payload = {
            "age": 200,
            "gender": "M",
            "symptoms": ["HEADACHE"],
            "duration": "1주",
        }

        # when
        response = await client.post(QUESTIONNAIRE_URL, json=payload)

        # then
        assert response.status_code == 422

    async def test_empty_symptoms_returns_422(self, client, mock_db):
        # given
        payload = {
            "age": 45,
            "gender": "M",
            "symptoms": [],
            "duration": "1주",
        }

        # when
        response = await client.post(QUESTIONNAIRE_URL, json=payload)

        # then
        assert response.status_code == 422


class TestGetResult:
    async def test_existing_session_returns_200(self, client, mock_db):
        # given
        with patch(
            "app.api.v1.endpoints.result.get_db",
        ):
            with patch(
                "app.api.v1.endpoints.result.select",
            ) as mock_select:
                from unittest.mock import MagicMock

                mock_package = MagicMock()
                mock_package.name = "기본 종합검진"

                mock_rec = MagicMock()
                mock_rec.package_id = 1
                mock_rec.match_score = 0.85
                mock_rec.reason = "두통 관련"
                mock_rec.matched_tags = ["HEADACHE"]
                mock_rec.rank = 1
                mock_rec.package = mock_package

                mock_session_obj = MagicMock()
                mock_session_obj.session_key = MOCK_SESSION_KEY
                mock_session_obj.age = 45
                mock_session_obj.gender = "M"
                mock_session_obj.duration = "2주"
                mock_session_obj.llm_summary = "요약"
                mock_session_obj.red_flag_level = "NONE"
                mock_session_obj.red_flag_details = {"matched_rules": [], "message": ""}
                mock_session_obj.input_summary = {
                    "age": 45,
                    "gender": "M",
                    "symptoms": ["두통"],
                    "duration": "2주",
                    "existing_conditions": [],
                }
                mock_session_obj.recommendations = [mock_rec]

                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_session_obj
                mock_db.execute = AsyncMock(return_value=mock_result)

                # when
                response = await client.get(f"{RESULT_URL}/{MOCK_SESSION_KEY}")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["session_key"] == MOCK_SESSION_KEY
        assert data["input_summary"]["age"] == 45
        assert data["red_flag"]["level"] == "NONE"
        QuestionnaireResponse(**data)

    async def test_nonexistent_session_returns_404(self, client, mock_db):
        # given
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # when
        response = await client.get(
            f"{RESULT_URL}/00000000-0000-0000-0000-000000000000"
        )

        # then
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    async def test_invalid_uuid_returns_404(self, client, mock_db):
        # when
        response = await client.get(f"{RESULT_URL}/not-a-uuid")

        # then
        assert response.status_code == 404
