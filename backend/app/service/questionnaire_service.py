from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.models import IntakeSession, Recommendation
from app.domain.schemas.llm import LLMAnalysisResult
from app.domain.schemas.matcher import MatchRequest, MatchResult
from app.domain.schemas.patient import (
    InputSummary,
    PackageRecommendation,
    QuestionnaireRequest,
    QuestionnaireResponse,
    RedFlagResult,
)
from app.service.llm_service import (
    LLMServiceError,
    analyze_questionnaire,
    get_llm_provider,
)
from app.service.package_service import PackageService
from app.service.red_flag_service import RedFlagService
from app.service.package_matcher.tag_matcher import TagMatcher
from app.service.symptom_tag_service import SymptomTagService

logger = logging.getLogger(__name__)

TAG_MATCHER_REASON = "태그 매칭 기반 자동 추천"


class QuestionnaireService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def analyze(self, request: QuestionnaireRequest) -> QuestionnaireResponse:
        red_flag = self._check_red_flags(request.symptoms)
        packages = await self._load_packages()
        symptom_tags = await self._load_symptom_tags()

        recommendations: List[PackageRecommendation] = []
        summary: Optional[str] = None
        extracted_tags: List[str] = []

        try:
            llm_result = await self._run_llm_analysis(request, packages, symptom_tags)
            summary = llm_result.summary
            extracted_tags = llm_result.extracted_tags

            recommendations = self._llm_to_recommendations(llm_result, packages)

            if self._needs_complement(llm_result, recommendations):
                tag_results = await self._run_tag_matcher(request, llm_result.extracted_tags)
                recommendations = self._merge_recommendations(recommendations, tag_results)

        except LLMServiceError:
            logger.warning("LLM 분석 실패, TagMatcher fallback 사용")
            extracted_tags = request.symptoms
            tag_results = await self._run_tag_matcher(request, request.symptoms)
            recommendations = [
                PackageRecommendation(
                    package_id=r.package_id,
                    package_name=r.package_name,
                    match_score=r.match_score,
                    reason=TAG_MATCHER_REASON,
                    matched_tags=r.matched_tags,
                )
                for r in tag_results
            ]

        recommendations = recommendations[:settings.MAX_RECOMMENDATIONS]

        code_to_name = {t.code: t.name for t in symptom_tags}
        symptom_names = [code_to_name.get(s, s) for s in request.symptoms]

        session_key = await self._save_session(
            request, summary, red_flag, recommendations, extracted_tags, symptom_names,
        )

        input_summary = InputSummary(
            age=request.age,
            gender=request.gender,
            symptoms=symptom_names,
            duration=request.duration,
            existing_conditions=request.existing_conditions,
        )

        return QuestionnaireResponse(
            session_key=session_key,
            summary=summary,
            input_summary=input_summary,
            red_flag=red_flag,
            recommendations=recommendations,
        )

    def _check_red_flags(self, symptoms: List[str]) -> RedFlagResult:
        service = RedFlagService()
        return service.check(symptoms)

    async def _load_packages(self):
        service = PackageService(self._session)
        return await service.get_packages(is_active=True)

    async def _load_symptom_tags(self):
        service = SymptomTagService(self._session)
        return await service.get_tags()

    async def _run_llm_analysis(
        self,
        request: QuestionnaireRequest,
        packages,
        symptom_tags,
    ) -> LLMAnalysisResult:
        provider = get_llm_provider()

        packages_dicts = [
            {
                "id": p.id, "name": p.name,
                "description": p.description or "",
                "hospital_name": p.hospital_name,
                "target_gender": p.target_gender,
                "min_age": p.min_age, "max_age": p.max_age,
                "price_range": p.price_range,
            }
            for p in packages
        ]
        tags_dicts = [
            {"code": t.code, "name": t.name, "category": t.category}
            for t in symptom_tags
        ]

        return await analyze_questionnaire(
            request, packages_dicts, tags_dicts, provider,
        )

    async def _run_tag_matcher(
        self, request: QuestionnaireRequest, extracted_tags: List[str],
    ) -> List[MatchResult]:
        matcher = TagMatcher(self._session)
        match_request = MatchRequest(
            extracted_tags=extracted_tags,
            age=request.age,
            gender=request.gender,
        )
        return await matcher.match(match_request)

    def _llm_to_recommendations(
        self, llm_result: LLMAnalysisResult, packages,
    ) -> List[PackageRecommendation]:
        package_map = {p.id: p.name for p in packages}
        recommendations = []
        for rec in llm_result.recommendations:
            pkg_name = package_map.get(rec.package_id, "")
            if not pkg_name:
                continue
            recommendations.append(
                PackageRecommendation(
                    package_id=rec.package_id,
                    package_name=pkg_name,
                    match_score=rec.confidence,
                    reason=rec.reason,
                    matched_tags=llm_result.extracted_tags,
                )
            )
        return recommendations

    def _needs_complement(
        self, llm_result: LLMAnalysisResult, recommendations: List[PackageRecommendation],
    ) -> bool:
        return (
            llm_result.confidence < settings.LLM_COMPLEMENT_CONFIDENCE_THRESHOLD
            or len(recommendations) < settings.LLM_COMPLEMENT_MIN_RECOMMENDATIONS
        )

    def _merge_recommendations(
        self,
        llm_recs: List[PackageRecommendation],
        tag_results: List[MatchResult],
    ) -> List[PackageRecommendation]:
        existing_ids = {r.package_id for r in llm_recs}
        merged = list(llm_recs)

        for r in tag_results:
            if r.package_id not in existing_ids:
                merged.append(
                    PackageRecommendation(
                        package_id=r.package_id,
                        package_name=r.package_name,
                        match_score=r.match_score,
                        reason=TAG_MATCHER_REASON,
                        matched_tags=r.matched_tags,
                    )
                )
                existing_ids.add(r.package_id)

        return merged

    async def _save_session(
        self,
        request: QuestionnaireRequest,
        summary: Optional[str],
        red_flag: RedFlagResult,
        recommendations: List[PackageRecommendation],
        extracted_tags: List[str],
        symptom_names: List[str],
    ) -> str:
        session_key = str(uuid.uuid4())

        intake = IntakeSession(
            session_key=uuid.UUID(session_key),
            age=request.age,
            gender=request.gender,
            selected_symptoms=request.symptoms,
            duration=request.duration,
            underlying_conditions=request.existing_conditions,
            llm_summary=summary,
            extracted_tags=extracted_tags,
            red_flag_level=red_flag.level,
            red_flag_details=red_flag.model_dump(),
            llm_provider=settings.LLM_PROVIDER,
            llm_model=getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", ""),
            input_summary={
                "age": request.age,
                "gender": request.gender,
                "symptoms": symptom_names,
                "duration": request.duration,
                "existing_conditions": request.existing_conditions,
            },
        )
        self._session.add(intake)
        await self._session.flush()

        for idx, rec in enumerate(recommendations):
            self._session.add(
                Recommendation(
                    session_id=intake.id,
                    package_id=rec.package_id,
                    rank=idx + 1,
                    match_score=rec.match_score,
                    reason=rec.reason,
                    matched_tags=rec.matched_tags,
                )
            )

        await self._session.flush()
        return session_key
