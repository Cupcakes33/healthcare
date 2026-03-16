from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.schemas.patient import QuestionnaireRequest, QuestionnaireResponse
from app.service.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.post("/questionnaire", response_model=QuestionnaireResponse, status_code=200)
async def submit_questionnaire(
    request: QuestionnaireRequest,
    db: AsyncSession = Depends(get_db),
) -> QuestionnaireResponse:
    service = QuestionnaireService(db)
    result = await service.analyze(request)
    await db.commit()
    return result
