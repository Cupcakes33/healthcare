from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.prompts import SYSTEM_PROMPT, build_questionnaire_prompt
from app.domain.schemas.llm import LLMAnalysisResult, LLMResponse
from app.domain.schemas.patient import QuestionnaireRequest
from app.service.llm_service import (
    LLMParsingError,
    LLMProvider,
    analyze_questionnaire,
)

SAMPLE_PACKAGES = [
    {"id": 1, "name": "기본 종합검진", "description": "일반적인 건강 상태를 종합적으로 확인하는 기본 검진", "hospital_name": "서울병원", "target_gender": "ALL", "min_age": 20, "max_age": 80, "price_range": "30~50만원"},
    {"id": 2, "name": "심혈관 정밀검진", "description": "심장 및 혈관 질환 위험을 정밀 평가하는 검진", "hospital_name": "서울병원", "target_gender": "ALL", "min_age": 40, "max_age": 80, "price_range": "80~120만원"},
]

SAMPLE_TAGS = [
    {"code": "HEADACHE", "name": "두통", "category": "신경계"},
    {"code": "CHEST_PAIN", "name": "흉통", "category": "심혈관"},
    {"code": "FATIGUE", "name": "피로", "category": "전신"},
]


class TestBuildQuestionnairePrompt:

    @pytest.fixture
    def questionnaire(self):
        return QuestionnaireRequest(
            age=45,
            gender="M",
            symptoms=["두통", "피로"],
            duration="2주",
            existing_conditions=["고혈압"],
        )

    def test_returns_system_and_user_prompt(self, questionnaire):
        system, user = build_questionnaire_prompt(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS,
        )
        assert system == SYSTEM_PROMPT
        assert isinstance(user, str)

    def test_system_prompt_contains_no_diagnosis(self):
        assert "진단" in SYSTEM_PROMPT
        assert "처방" in SYSTEM_PROMPT

    def test_system_prompt_contains_confidence_criteria(self):
        assert "0.9 이상" in SYSTEM_PROMPT
        assert "0.7~0.9" in SYSTEM_PROMPT
        assert "0.5~0.7" in SYSTEM_PROMPT
        assert "0.5 미만" in SYSTEM_PROMPT

    def test_system_prompt_contains_few_shot_example(self):
        assert "예시:" in SYSTEM_PROMPT
        assert "CHEST_TIGHTNESS" in SYSTEM_PROMPT

    def test_user_prompt_contains_patient_info(self, questionnaire):
        _, user = build_questionnaire_prompt(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS,
        )
        assert "45세" in user
        assert "남성" in user
        assert "두통" in user
        assert "피로" in user
        assert "2주" in user
        assert "고혈압" in user

    def test_user_prompt_contains_packages(self, questionnaire):
        _, user = build_questionnaire_prompt(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS,
        )
        assert "기본 종합검진" in user
        assert "심혈관 정밀검진" in user
        assert "서울병원" in user

    def test_user_prompt_contains_tags_with_category(self, questionnaire):
        _, user = build_questionnaire_prompt(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS,
        )
        assert "HEADACHE" in user
        assert "CHEST_PAIN" in user
        assert "FATIGUE" in user
        assert "신경계" in user
        assert "심혈관" in user

    def test_user_prompt_contains_package_description(self, questionnaire):
        _, user = build_questionnaire_prompt(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS,
        )
        assert "종합적으로 확인하는 기본 검진" in user
        assert "심장 및 혈관 질환" in user

    def test_no_existing_conditions(self):
        q = QuestionnaireRequest(
            age=30, gender="F", symptoms=["두통"], duration="1주",
        )
        _, user = build_questionnaire_prompt(q, SAMPLE_PACKAGES, SAMPLE_TAGS)
        assert "없음" in user


class TestAnalyzeQuestionnaire:

    @pytest.fixture
    def questionnaire(self):
        return QuestionnaireRequest(
            age=45,
            gender="M",
            symptoms=["두통", "피로"],
            duration="2주",
            existing_conditions=["고혈압"],
        )

    def _make_llm_response(self, content):
        return LLMResponse(
            content=json.dumps(content, ensure_ascii=False),
            model="gpt-4o-mini",
            provider="openai",
        )

    @pytest.mark.asyncio
    async def test_successful_analysis(self, questionnaire):
        # given
        llm_output = {
            "summary": "45세 남성 환자가 두통과 피로를 호소합니다.",
            "extracted_tags": ["HEADACHE", "FATIGUE"],
            "recommendations": [
                {"package_id": 1, "reason": "기본 종합검진이 적합합니다.", "confidence": 0.9},
            ],
            "confidence": 0.85,
        }
        mock_provider = AsyncMock(spec=LLMProvider)
        mock_provider.generate.return_value = self._make_llm_response(llm_output)

        # when
        result = await analyze_questionnaire(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS, mock_provider,
        )

        # then
        assert isinstance(result, LLMAnalysisResult)
        assert result.summary == "45세 남성 환자가 두통과 피로를 호소합니다."
        assert result.extracted_tags == ["HEADACHE", "FATIGUE"]
        assert len(result.recommendations) == 1
        assert result.recommendations[0].package_id == 1
        assert result.confidence == 0.85

    @pytest.mark.asyncio
    async def test_filters_invalid_tags(self, questionnaire):
        # given
        llm_output = {
            "summary": "요약입니다.",
            "extracted_tags": ["HEADACHE", "INVALID_TAG"],
            "recommendations": [
                {"package_id": 1, "reason": "이유", "confidence": 0.8},
            ],
            "confidence": 0.8,
        }
        mock_provider = AsyncMock(spec=LLMProvider)
        mock_provider.generate.return_value = self._make_llm_response(llm_output)

        # when
        result = await analyze_questionnaire(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS, mock_provider,
        )

        # then
        assert "INVALID_TAG" not in result.extracted_tags
        assert "HEADACHE" in result.extracted_tags

    @pytest.mark.asyncio
    async def test_filters_invalid_package_ids(self, questionnaire):
        # given
        llm_output = {
            "summary": "요약입니다.",
            "extracted_tags": ["HEADACHE"],
            "recommendations": [
                {"package_id": 1, "reason": "이유", "confidence": 0.8},
                {"package_id": 999, "reason": "존재하지 않는 패키지", "confidence": 0.5},
            ],
            "confidence": 0.8,
        }
        mock_provider = AsyncMock(spec=LLMProvider)
        mock_provider.generate.return_value = self._make_llm_response(llm_output)

        # when
        result = await analyze_questionnaire(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS, mock_provider,
        )

        # then
        assert len(result.recommendations) == 1
        assert result.recommendations[0].package_id == 1

    @pytest.mark.asyncio
    async def test_parsing_error_raises_after_retry(self, questionnaire):
        # given
        mock_provider = AsyncMock(spec=LLMProvider)
        mock_provider.generate.return_value = LLMResponse(
            content="이것은 유효한 JSON이 아닙니다",
            model="gpt-4o-mini",
            provider="openai",
        )

        # when / then
        with pytest.raises(LLMParsingError, match="LLM 응답 파싱 실패"):
            await analyze_questionnaire(
                questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS, mock_provider,
            )

    @pytest.mark.asyncio
    async def test_retry_on_first_parse_failure(self, questionnaire):
        # given
        valid_output = {
            "summary": "요약입니다.",
            "extracted_tags": ["HEADACHE"],
            "recommendations": [
                {"package_id": 1, "reason": "이유", "confidence": 0.8},
            ],
            "confidence": 0.8,
        }
        mock_provider = AsyncMock(spec=LLMProvider)
        mock_provider.generate.side_effect = [
            LLMResponse(content="invalid json", model="gpt-4o-mini", provider="openai"),
            self._make_llm_response(valid_output),
        ]

        # when
        result = await analyze_questionnaire(
            questionnaire, SAMPLE_PACKAGES, SAMPLE_TAGS, mock_provider,
        )

        # then
        assert result.summary == "요약입니다."
        assert mock_provider.generate.call_count == 2
