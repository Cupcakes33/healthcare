from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.schemas.llm import LLMAnalysisResult, LLMPackageRecommendation
from app.domain.schemas.matcher import MatchResult
from app.domain.schemas.patient import (
    QuestionnaireRequest,
    QuestionnaireResponse,
    RedFlagResult,
)
from app.service.llm_service import LLMServiceError
from app.service.questionnaire_service import QuestionnaireService


@pytest.fixture
def questionnaire():
    return QuestionnaireRequest(
        age=45, gender="M", symptoms=["HEADACHE", "FATIGUE"],
        duration="2주", existing_conditions=["고혈압"],
    )


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_red_flag():
    return RedFlagResult(level="NONE", matched_rules=[], message="특이 소견이 없습니다.")


@pytest.fixture
def mock_llm_result():
    return LLMAnalysisResult(
        summary="45세 남성 환자가 두통과 피로를 호소합니다.",
        extracted_tags=["HEADACHE", "FATIGUE"],
        recommendations=[
            LLMPackageRecommendation(package_id=1, reason="기본 검진이 적합합니다.", confidence=0.9),
            LLMPackageRecommendation(package_id=2, reason="뇌신경 검진 권장.", confidence=0.85),
            LLMPackageRecommendation(package_id=3, reason="호흡기 검진 권장.", confidence=0.7),
        ],
        confidence=0.88,
    )


def _make_package(pkg_id, name, description):
    pkg = MagicMock()
    pkg.id = pkg_id
    pkg.name = name
    pkg.description = description
    pkg.hospital_name = "서울병원"
    pkg.target_gender = "ALL"
    pkg.min_age = 20
    pkg.max_age = 80
    pkg.price_range = "30만원"
    pkg.is_active = True
    pkg.package_tags = []
    return pkg


@pytest.fixture
def mock_packages():
    return [
        _make_package(1, "기본 종합검진", "기본"),
        _make_package(2, "뇌신경 검진", "뇌"),
        _make_package(3, "호흡기 검진", "호흡기"),
    ]


def _make_tag(id, code, tag_name, category):
    tag = MagicMock(id=id, code=code, category=category)
    tag.name = tag_name
    return tag


@pytest.fixture
def mock_tags():
    return [
        _make_tag(1, "HEADACHE", "두통", "신경계"),
        _make_tag(2, "FATIGUE", "피로감", "전신"),
    ]


class TestQuestionnaireServiceNormalFlow:

    @pytest.mark.asyncio
    async def test_full_pipeline(
        self, questionnaire, mock_session, mock_red_flag, mock_llm_result,
        mock_packages, mock_tags,
    ):
        # given
        service = QuestionnaireService(mock_session)

        with patch.object(service, "_check_red_flags", return_value=mock_red_flag), \
             patch.object(service, "_load_packages", return_value=mock_packages), \
             patch.object(service, "_load_symptom_tags", return_value=mock_tags), \
             patch.object(service, "_run_llm_analysis", return_value=mock_llm_result), \
             patch.object(service, "_save_session", return_value="test-uuid"):

            # when
            result = await service.analyze(questionnaire)

        # then
        assert isinstance(result, QuestionnaireResponse)
        assert result.session_key == "test-uuid"
        assert result.summary == "45세 남성 환자가 두통과 피로를 호소합니다."
        assert result.red_flag.level == "NONE"
        assert len(result.recommendations) <= 3
        assert not hasattr(result, "disclaimer") or "disclaimer" not in result.model_fields

    @pytest.mark.asyncio
    async def test_input_summary_included(
        self, questionnaire, mock_session, mock_red_flag, mock_llm_result,
        mock_packages, mock_tags,
    ):
        # given
        service = QuestionnaireService(mock_session)

        with patch.object(service, "_check_red_flags", return_value=mock_red_flag), \
             patch.object(service, "_load_packages", return_value=mock_packages), \
             patch.object(service, "_load_symptom_tags", return_value=mock_tags), \
             patch.object(service, "_run_llm_analysis", return_value=mock_llm_result), \
             patch.object(service, "_save_session", return_value="test-uuid"):

            # when
            result = await service.analyze(questionnaire)

        # then
        assert result.input_summary.age == 45
        assert result.input_summary.gender == "M"
        assert "두통" in result.input_summary.symptoms


class TestQuestionnaireServiceGracefulDegradation:

    @pytest.mark.asyncio
    async def test_llm_failure_summary_is_none(
        self, questionnaire, mock_session, mock_red_flag,
        mock_packages, mock_tags,
    ):
        # given
        service = QuestionnaireService(mock_session)
        tag_results = [
            MatchResult(package_id=1, package_name="기본 종합검진", match_score=0.7, matched_tags=["HEADACHE"]),
        ]

        with patch.object(service, "_check_red_flags", return_value=mock_red_flag), \
             patch.object(service, "_load_packages", return_value=mock_packages), \
             patch.object(service, "_load_symptom_tags", return_value=mock_tags), \
             patch.object(service, "_run_llm_analysis", side_effect=LLMServiceError("LLM 실패")), \
             patch.object(service, "_run_tag_matcher", return_value=tag_results), \
             patch.object(service, "_save_session", return_value="fallback-uuid"):

            # when
            result = await service.analyze(questionnaire)

        # then
        assert result.summary is None
        assert result.session_key == "fallback-uuid"
        assert len(result.recommendations) >= 1

    @pytest.mark.asyncio
    async def test_no_disclaimer_in_response(
        self, questionnaire, mock_session, mock_red_flag, mock_llm_result,
        mock_packages, mock_tags,
    ):
        # given
        service = QuestionnaireService(mock_session)

        with patch.object(service, "_check_red_flags", return_value=mock_red_flag), \
             patch.object(service, "_load_packages", return_value=mock_packages), \
             patch.object(service, "_load_symptom_tags", return_value=mock_tags), \
             patch.object(service, "_run_llm_analysis", return_value=mock_llm_result), \
             patch.object(service, "_save_session", return_value="test-uuid"):

            # when
            result = await service.analyze(questionnaire)

        # then
        assert "disclaimer" not in QuestionnaireResponse.model_fields


class TestQuestionnaireServiceComplementary:

    @pytest.mark.asyncio
    async def test_tag_matcher_complements_when_low_confidence(
        self, questionnaire, mock_session, mock_red_flag,
        mock_packages, mock_tags,
    ):
        # given
        low_confidence_result = LLMAnalysisResult(
            summary="요약입니다.",
            extracted_tags=["HEADACHE"],
            recommendations=[
                LLMPackageRecommendation(package_id=1, reason="이유", confidence=0.6),
            ],
            confidence=0.5,
        )
        service = QuestionnaireService(mock_session)
        tag_results = [
            MatchResult(package_id=2, package_name="뇌신경 검진", match_score=0.8, matched_tags=["HEADACHE"]),
        ]

        with patch.object(service, "_check_red_flags", return_value=mock_red_flag), \
             patch.object(service, "_load_packages", return_value=mock_packages), \
             patch.object(service, "_load_symptom_tags", return_value=mock_tags), \
             patch.object(service, "_run_llm_analysis", return_value=low_confidence_result), \
             patch.object(service, "_run_tag_matcher", return_value=tag_results), \
             patch.object(service, "_save_session", return_value="test-uuid"):

            # when
            result = await service.analyze(questionnaire)

        # then
        package_ids = [r.package_id for r in result.recommendations]
        assert 1 in package_ids
        assert 2 in package_ids
