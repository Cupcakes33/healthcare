from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.schemas.chat import (
    ChatCompleteRequest,
    ChatMessageRequest,
    ChatResponse,
    ChatStartRequest,
)
from app.domain.schemas.patient import QuestionnaireResponse
from app.service.chat_service import ChatService
from app.service.llm_service import get_llm_provider

router = APIRouter()


@router.post("/start", response_model=ChatResponse, status_code=200)
async def start_chat(request: ChatStartRequest, req: Request) -> ChatResponse:
    client_ip = req.client.host if req.client else "unknown"
    service = ChatService()
    return service.start_session(request.age, request.gender, client_ip)


@router.post("/message", response_model=ChatResponse, status_code=200)
async def send_message(request: ChatMessageRequest) -> ChatResponse:
    service = ChatService()
    provider = get_llm_provider()
    return await service.process_message(
        request.chat_session_id, request.message, provider,
    )


@router.post("/complete", response_model=QuestionnaireResponse, status_code=200)
async def complete_chat(
    request: ChatCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> QuestionnaireResponse:
    service = ChatService()
    provider = get_llm_provider()
    result = await service.complete(request.chat_session_id, provider, db)
    await db.commit()
    return result
