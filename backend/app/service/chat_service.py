from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException

from app.core.config import settings
from app.core.chat_prompts import CHAT_COMPLETE_MESSAGE, CHAT_SYSTEM_PROMPT, build_greeting
from app.domain.schemas.chat import (
    ChatLLMResponse,
    ChatMessage,
    ChatResponse,
    ChatSessionState,
    ExtractedData,
)
from app.domain.schemas.llm import LLMRequest
from app.service.llm_service import LLMProvider, LLMServiceError
from app.service.red_flag_service import RedFlagService

logger = logging.getLogger(__name__)

_chat_sessions: Dict[str, ChatSessionState] = {}
_rate_limit_records: Dict[str, List[datetime]] = {}
_daily_llm_call_count: Dict[str, int] = {}



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

    async def process_message(
        self,
        session_id: str,
        message: str,
        llm_provider: LLMProvider,
    ) -> ChatResponse:
        session = self.get_session(session_id)
        self.validate_not_complete(session)
        self._check_daily_llm_limit()

        session.messages.append(ChatMessage(role="user", content=message))

        llm_response = await self._call_chat_llm(session, llm_provider)

        if llm_response is not None:
            self._merge_extracted_data(session, llm_response.extracted)
            reply = llm_response.reply
            if llm_response.is_sufficient:
                session.is_complete = True
        else:
            reply = "죄송합니다. 일시적인 오류가 발생했습니다. 다시 한번 말씀해주세요."

        session.messages.append(ChatMessage(role="assistant", content=reply))
        session.turn += 1

        red_flag_service = RedFlagService()
        red_flag = red_flag_service.check(session.extracted_data.symptoms)
        if red_flag.level == "EMERGENCY":
            session.is_complete = True
            reply = f"{red_flag.message} {reply}"
            session.messages[-1] = ChatMessage(role="assistant", content=reply)

        if session.turn >= session.max_turns and not session.is_complete:
            session.is_complete = True
            reply = f"{reply}\n\n{CHAT_COMPLETE_MESSAGE}"
            session.messages[-1] = ChatMessage(role="assistant", content=reply)

        return ChatResponse(
            chat_session_id=session_id,
            message=reply,
            turn=session.turn,
            max_turns=session.max_turns,
            is_complete=session.is_complete,
            extracted_so_far=session.extracted_data,
        )

    async def _call_chat_llm(
        self,
        session: ChatSessionState,
        llm_provider: LLMProvider,
    ) -> ChatLLMResponse | None:
        conversation = "\n".join(
            f"{'환자' if m.role == 'user' else '도우미'}: {m.content}"
            for m in session.messages
            if m.role != "system"
        )

        user_prompt = (
            f"환자 정보: {session.age}세, "
            f"{'남성' if session.gender == 'M' else '여성'}\n\n"
            f"대화 내용:\n{conversation}"
        )

        llm_request = LLMRequest(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model_override=settings.CHAT_MODEL,
        )

        for attempt in range(2):
            try:
                response = await llm_provider.generate(llm_request)
                self._increment_daily_llm_count()
                parsed = json.loads(response.content)
                return ChatLLMResponse(**parsed)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning("LLM 응답 파싱 실패 (시도 %d): %s", attempt + 1, e)
                if attempt >= 1:
                    return None
            except LLMServiceError as e:
                logger.error("LLM 호출 실패: %s", e)
                return None

        return None

    def _merge_extracted_data(
        self, session: ChatSessionState, new: ExtractedData
    ) -> None:
        existing = session.extracted_data
        existing.symptoms = list(set(existing.symptoms) | set(new.symptoms))
        if new.duration and not existing.duration:
            existing.duration = new.duration
        existing.existing_conditions = list(
            set(existing.existing_conditions) | set(new.existing_conditions)
        )

    def _check_daily_llm_limit(self) -> None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        count = _daily_llm_call_count.get(today, 0)
        if count >= settings.DAILY_LLM_CALL_LIMIT:
            raise HTTPException(
                status_code=503,
                detail="일일 서비스 이용 한도에 도달했습니다. 내일 다시 시도해주세요.",
            )

    def _increment_daily_llm_count(self) -> None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        _daily_llm_call_count[today] = _daily_llm_call_count.get(today, 0) + 1

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
