from __future__ import annotations

from decimal import Decimal
from typing import List

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import CheckupPackage, PackageSymptomTag, SymptomTag
from app.domain.schemas.matcher import MatchRequest, MatchResult
from app.service.package_matcher.interface import PackageMatcher

MAX_RESULTS = 3
FALLBACK_PACKAGE_NAME = "기본 종합검진"


class TagMatcher(PackageMatcher):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def match(self, request: MatchRequest) -> List[MatchResult]:
        stmt = (
            select(
                CheckupPackage.id,
                CheckupPackage.name,
                PackageSymptomTag.relevance_score,
                SymptomTag.code,
            )
            .join(PackageSymptomTag, CheckupPackage.id == PackageSymptomTag.package_id)
            .join(SymptomTag, PackageSymptomTag.symptom_tag_id == SymptomTag.id)
            .where(
                CheckupPackage.is_active == True,
                SymptomTag.code.in_(request.extracted_tags),
                or_(
                    CheckupPackage.target_gender == "ALL",
                    CheckupPackage.target_gender == request.gender,
                ),
                CheckupPackage.min_age <= request.age,
                CheckupPackage.max_age >= request.age,
            )
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        if not rows:
            return await self._fallback()

        package_scores = await self._calculate_scores(rows, request.extracted_tags)

        sorted_packages = sorted(
            package_scores.values(),
            key=lambda x: x["match_score"],
            reverse=True,
        )

        return [
            MatchResult(
                package_id=p["package_id"],
                package_name=p["package_name"],
                match_score=round(p["match_score"], 2),
                matched_tags=p["matched_tags"],
            )
            for p in sorted_packages[:MAX_RESULTS]
        ]

    async def _calculate_scores(self, rows, extracted_tags: List[str]) -> dict:
        package_data: dict = {}
        for pkg_id, pkg_name, relevance, tag_code in rows:
            score = float(relevance) if isinstance(relevance, Decimal) else relevance
            if pkg_id not in package_data:
                package_data[pkg_id] = {
                    "package_id": pkg_id,
                    "package_name": pkg_name,
                    "matched_score_sum": 0.0,
                    "matched_tags": [],
                }
            package_data[pkg_id]["matched_score_sum"] += score
            package_data[pkg_id]["matched_tags"].append(tag_code)

        total_stmt = (
            select(
                PackageSymptomTag.package_id,
                PackageSymptomTag.relevance_score,
            )
            .where(PackageSymptomTag.package_id.in_(list(package_data.keys())))
        )
        total_result = await self._session.execute(total_stmt)
        total_rows = total_result.all()

        max_scores: dict = {}
        for pkg_id, relevance in total_rows:
            score = float(relevance) if isinstance(relevance, Decimal) else relevance
            max_scores[pkg_id] = max_scores.get(pkg_id, 0.0) + score

        for pkg_id, data in package_data.items():
            max_possible = max_scores.get(pkg_id, 1.0)
            data["match_score"] = (
                data["matched_score_sum"] / max_possible if max_possible > 0 else 0.0
            )

        return package_data

    async def _fallback(self) -> List[MatchResult]:
        stmt = select(CheckupPackage).where(
            CheckupPackage.is_active == True,
            CheckupPackage.name == FALLBACK_PACKAGE_NAME,
        )
        result = await self._session.execute(stmt)
        package = result.scalar_one_or_none()

        if package is None:
            return []

        return [
            MatchResult(
                package_id=package.id,
                package_name=package.name,
                match_score=0.5,
                matched_tags=[],
            )
        ]
