from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.domain.models import IntakeSession, Recommendation
from app.domain.schemas.patient import (
    InputSummary,
    PackageRecommendation,
    QuestionnaireResponse,
    RedFlagResult,
)

router = APIRouter()


@router.get("/result/{session_key}", response_model=QuestionnaireResponse)
async def get_result(
    session_key: str,
    db: AsyncSession = Depends(get_db),
) -> QuestionnaireResponse:
    try:
        uuid.UUID(session_key)
    except ValueError:
        raise HTTPException(status_code=404, detail="문진 결과를 찾을 수 없습니다")

    stmt = (
        select(IntakeSession)
        .where(IntakeSession.session_key == session_key)
        .options(
            selectinload(IntakeSession.recommendations).selectinload(Recommendation.package)
        )
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="문진 결과를 찾을 수 없습니다")

    red_flag_details = session.red_flag_details or {}
    red_flag = RedFlagResult(
        level=session.red_flag_level,
        matched_rules=red_flag_details.get("matched_rules", []),
        message=red_flag_details.get("message", ""),
    )

    input_summary_data = session.input_summary or {}
    input_summary = InputSummary(
        age=input_summary_data.get("age", session.age),
        gender=input_summary_data.get("gender", session.gender),
        symptoms=input_summary_data.get("symptoms", []),
        duration=input_summary_data.get("duration", session.duration),
        existing_conditions=input_summary_data.get("existing_conditions", []),
    )

    sorted_recs = sorted(session.recommendations, key=lambda r: r.rank)
    recommendations = [
        PackageRecommendation(
            package_id=rec.package_id,
            package_name=rec.package.name if rec.package else "",
            match_score=float(rec.match_score),
            reason=rec.reason or "",
            matched_tags=rec.matched_tags or [],
        )
        for rec in sorted_recs
    ]

    return QuestionnaireResponse(
        session_key=str(session.session_key),
        summary=session.llm_summary,
        input_summary=input_summary,
        red_flag=red_flag,
        recommendations=recommendations,
    )
