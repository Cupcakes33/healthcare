from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import case, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.database import get_db
from app.domain.models import CheckupPackage, IntakeSession, Recommendation, SymptomTag
from app.domain.schemas.admin import (
    PackageCount,
    StatsResponse,
    SymptomCount,
)

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = await _total_sessions(db)
    age_dist = await _age_distribution(db)
    intake_dist = await _intake_type_distribution(db)
    top_symptoms = await _top_symptoms(db)
    top_packages = await _top_packages(db)
    red_flag = await _red_flag_ratio(db, total)

    return StatsResponse(
        total_sessions=total,
        age_distribution=age_dist,
        intake_type_distribution=intake_dist,
        top_symptoms=top_symptoms,
        top_packages=top_packages,
        red_flag_ratio=red_flag,
    )


async def _total_sessions(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(IntakeSession.id)))
    return result.scalar() or 0


async def _intake_type_distribution(db: AsyncSession) -> dict:
    stmt = (
        select(IntakeSession.intake_type, func.count().label("cnt"))
        .group_by(IntakeSession.intake_type)
    )
    result = await db.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


async def _age_distribution(db: AsyncSession) -> dict:
    age_group = case(
        (IntakeSession.age < 20, "10대"),
        (IntakeSession.age < 30, "20대"),
        (IntakeSession.age < 40, "30대"),
        (IntakeSession.age < 50, "40대"),
        (IntakeSession.age < 60, "50대"),
        else_="60대 이상",
    )
    stmt = (
        select(age_group.label("group"), func.count().label("cnt"))
        .group_by(age_group)
    )
    result = await db.execute(stmt)
    return {row.group: row.cnt for row in result.all()}


async def _top_symptoms(db: AsyncSession) -> list:
    stmt = text("""
        SELECT COALESCE(st.name, tag) AS symptom_name, COUNT(*) as cnt
        FROM intake_session, jsonb_array_elements_text(extracted_tags) AS tag
        LEFT JOIN symptom_tag st ON st.code = tag
        GROUP BY symptom_name
        ORDER BY cnt DESC
        LIMIT 5
    """)
    result = await db.execute(stmt)
    return [SymptomCount(name=row[0], count=row[1]) for row in result.all()]


async def _top_packages(db: AsyncSession) -> list:
    stmt = (
        select(CheckupPackage.name, func.count(Recommendation.id).label("cnt"))
        .join(Recommendation, CheckupPackage.id == Recommendation.package_id)
        .group_by(CheckupPackage.name)
        .order_by(func.count(Recommendation.id).desc())
        .limit(3)
    )
    result = await db.execute(stmt)
    return [PackageCount(name=row[0], count=row[1]) for row in result.all()]


async def _red_flag_ratio(db: AsyncSession, total: int) -> float:
    if total == 0:
        return 0.0

    flagged_result = await db.execute(
        select(func.count(IntakeSession.id))
        .where(IntakeSession.red_flag_level != "NONE")
    )
    flagged = flagged_result.scalar() or 0
    return round(flagged / total, 2)
