from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException

from app.core.config import settings
from app.core.chat_prompts import build_greeting
from app.domain.schemas.chat import (
    ChatMessage,
    ChatResponse,
    ChatSessionState,
    ExtractedData,
)

logger = logging.getLogger(__name__)

_chat_sessions: Dict[str, ChatSessionState] = {}
_rate_limit_records: Dict[str, List[datetime]] = {}


class ChatService:

    def start_session(self, age: int, gender: str, client_ip: str) -> ChatResponse:
        self._cleanup_expired()
        self._check_rate_limit(client_ip)
        self._check_active_session_limit()

        session_id = str(uuid.uuid4())
        greeting = build_greeting(age, gender)

        session = ChatSessionState(
            chat_session_id=session_id,
            age=age,
            gender=gender,
            messages=[
                ChatMessage(role="assistant", content=greeting),
            ],
            turn=1,
            max_turns=settings.CHAT_MAX_TURNS,
            extracted_data=ExtractedData(),
            is_complete=False,
            created_at=datetime.utcnow(),
        )

        _chat_sessions[session_id] = session

        return ChatResponse(
            chat_session_id=session_id,
            message=greeting,
            turn=1,
            max_turns=settings.CHAT_MAX_TURNS,
            is_complete=False,
        )

    def get_session(self, session_id: str) -> ChatSessionState:
        self._cleanup_expired()
        session = _chat_sessions.get(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail="채팅 세션을 찾을 수 없습니다",
            )
        return session

    def validate_not_complete(self, session: ChatSessionState) -> None:
        if session.is_complete:
            raise HTTPException(
                status_code=400,
                detail="이미 완료된 세션입니다",
            )

    def remove_session(self, session_id: str) -> None:
        _chat_sessions.pop(session_id, None)

    def _check_rate_limit(self, client_ip: str) -> None:
        now = datetime.utcnow()
        records = _rate_limit_records.get(client_ip, [])

        records = [t for t in records if now - t < timedelta(hours=1)]
        _rate_limit_records[client_ip] = records

        minute_ago = now - timedelta(minutes=1)
        recent_minute = sum(1 for t in records if t > minute_ago)

        if recent_minute >= settings.CHAT_RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="요청 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.",
            )

        if len(records) >= settings.CHAT_RATE_LIMIT_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail="요청 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.",
            )

        records.append(now)

    def _check_active_session_limit(self) -> None:
        if len(_chat_sessions) >= settings.CHAT_MAX_ACTIVE_SESSIONS:
            raise HTTPException(
                status_code=503,
                detail="현재 많은 사용자가 이용 중입니다. 잠시 후 다시 시도해주세요.",
            )

    def _cleanup_expired(self) -> None:
        now = datetime.utcnow()
        ttl = timedelta(minutes=settings.CHAT_SESSION_TTL_MINUTES)
        expired = [
            sid for sid, s in _chat_sessions.items()
            if now - s.created_at > ttl
        ]
        for sid in expired:
            del _chat_sessions[sid]
