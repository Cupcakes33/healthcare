from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import INTAKE_TYPE_CHAT, TAG_MATCHER_REASON
from app.core.chat_prompts import (
    CHAT_COMPLETE_MESSAGE,
    CHAT_SYSTEM_PROMPT,
    build_chat_analysis_prompt,
    build_greeting,
)
from app.domain.models import IntakeSession, Recommendation
from app.domain.schemas.chat import (
    ChatLLMResponse,
    ChatMessage,
    ChatResponse,
    ChatSessionState,
    ExtractedData,
)
from app.domain.schemas.llm import LLMAnalysisResult, LLMRequest
from app.domain.schemas.matcher import MatchRequest
from app.domain.schemas.patient import (
    InputSummary,
    PackageRecommendation,
    QuestionnaireResponse,
)
from app.service.llm_service import LLMProvider, LLMServiceError
from app.service.package_matcher.tag_matcher import TagMatcher
from app.service.package_service import PackageService
from app.service.red_flag_service import RedFlagService
from app.service.security import detect_injection, validate_output, validate_output_length
from app.service.symptom_tag_service import SymptomTagService

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

    async def complete(
        self,
        session_id: str,
        llm_provider: LLMProvider,
        db: AsyncSession,
    ) -> QuestionnaireResponse:
        session = self.get_session(session_id)

        user_messages = [m for m in session.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=400,
                detail="최소 1개 이상의 대화가 필요합니다",
            )

        self._check_daily_llm_limit()

        packages = await PackageService(db).get_packages(is_active=True)
        symptom_tags = await SymptomTagService(db).get_tags()

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

        recommendations: List[PackageRecommendation] = []
        summary: Optional[str] = None
        extracted_tags: List[str] = []

        try:
            llm_result = await self._run_chat_analysis(
                session, packages_dicts, tags_dicts, llm_provider,
            )
            summary = llm_result.summary
            extracted_tags = llm_result.extracted_tags

            package_map = {p.id: p.name for p in packages}
            for rec in llm_result.recommendations:
                pkg_name = package_map.get(rec.package_id, "")
                if pkg_name:
                    recommendations.append(
                        PackageRecommendation(
                            package_id=rec.package_id,
                            package_name=pkg_name,
                            match_score=rec.confidence,
                            reason=rec.reason,
                            matched_tags=extracted_tags,
                        )
                    )

            if (
                llm_result.confidence < settings.LLM_COMPLEMENT_CONFIDENCE_THRESHOLD
                or len(recommendations) < settings.LLM_COMPLEMENT_MIN_RECOMMENDATIONS
            ):
                tag_results = await TagMatcher(db).match(
                    MatchRequest(
                        extracted_tags=extracted_tags,
                        age=session.age,
                        gender=session.gender,
                    )
                )
                existing_ids = {r.package_id for r in recommendations}
                for r in tag_results:
                    if r.package_id not in existing_ids:
                        recommendations.append(
                            PackageRecommendation(
                                package_id=r.package_id,
                                package_name=r.package_name,
                                match_score=r.match_score,
                                reason=TAG_MATCHER_REASON,
                                matched_tags=r.matched_tags,
                            )
                        )
                        existing_ids.add(r.package_id)

        except LLMServiceError:
            logger.warning("채팅 분석 LLM 실패, TagMatcher fallback 사용")
            extracted_tags = session.extracted_data.symptoms
            tag_results = await TagMatcher(db).match(
                MatchRequest(
                    extracted_tags=extracted_tags,
                    age=session.age,
                    gender=session.gender,
                )
            )
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

        red_flag_service = RedFlagService()
        red_flag = red_flag_service.check(extracted_tags)

        extracted = session.extracted_data
        symptom_names = extracted.symptoms or [s for s in extracted_tags]
        duration = extracted.duration or "채팅 대화 기반"
        existing_conditions = extracted.existing_conditions or []

        input_summary = InputSummary(
            age=session.age,
            gender=session.gender,
            symptoms=symptom_names,
            duration=duration,
            existing_conditions=existing_conditions,
        )

        chat_history = [m.model_dump() for m in session.messages]

        session_key = await self._save_chat_session(
            db, session, summary, red_flag, recommendations,
            extracted_tags, input_summary, chat_history,
        )

        return QuestionnaireResponse(
            session_key=session_key,
            summary=summary,
            input_summary=input_summary,
            red_flag=red_flag,
            recommendations=recommendations,
        )

    async def _run_chat_analysis(
        self,
        session: ChatSessionState,
        packages: List[dict],
        symptom_tags: List[dict],
        llm_provider: LLMProvider,
    ) -> LLMAnalysisResult:
        system_prompt, user_prompt = build_chat_analysis_prompt(
            session.messages, session.age, session.gender,
            packages, symptom_tags,
        )

        valid_tag_codes = [t["code"] for t in symptom_tags]
        valid_package_ids = [p["id"] for p in packages]

        llm_request = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_override=settings.ANALYSIS_MODEL,
        )

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await llm_provider.generate(llm_request)
                self._increment_daily_llm_count()
                parsed = json.loads(response.content)
                result = LLMAnalysisResult(**parsed)
                result.extracted_tags = [
                    t for t in result.extracted_tags if t in valid_tag_codes
                ]
                result.recommendations = [
                    r for r in result.recommendations
                    if r.package_id in valid_package_ids
                ]
                return result
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning("분석 LLM 응답 파싱 실패 (시도 %d): %s", attempt + 1, e)
                if attempt >= settings.LLM_MAX_RETRIES:
                    raise LLMServiceError(f"분석 LLM 응답 파싱 실패: {e}") from e
            except LLMServiceError:
                if attempt >= settings.LLM_MAX_RETRIES:
                    raise

        raise LLMServiceError("분석 LLM 최대 재시도 초과")

    async def _save_chat_session(
        self,
        db: AsyncSession,
        session: ChatSessionState,
        summary: Optional[str],
        red_flag,
        recommendations: List[PackageRecommendation],
        extracted_tags: List[str],
        input_summary: InputSummary,
        chat_history: List[dict],
    ) -> str:
        session_key = str(uuid.uuid4())

        intake = IntakeSession(
            session_key=uuid.UUID(session_key),
            intake_type=INTAKE_TYPE_CHAT,
            age=session.age,
            gender=session.gender,
            selected_symptoms=input_summary.symptoms,
            duration=input_summary.duration,
            underlying_conditions=input_summary.existing_conditions,
            llm_summary=summary,
            extracted_tags=extracted_tags,
            red_flag_level=red_flag.level,
            red_flag_details=red_flag.model_dump(),
            chat_history=chat_history,
            llm_provider=settings.LLM_PROVIDER,
            llm_model=settings.ANALYSIS_MODEL,
            input_summary=input_summary.model_dump(),
        )
        db.add(intake)
        await db.flush()

        for idx, rec in enumerate(recommendations):
            db.add(
                Recommendation(
                    session_id=intake.id,
                    package_id=rec.package_id,
                    rank=idx + 1,
                    match_score=rec.match_score,
                    reason=rec.reason,
                    matched_tags=rec.matched_tags,
                )
            )

        await db.flush()
        return session_key

    async def process_message(
        self,
        session_id: str,
        message: str,
        llm_provider: LLMProvider,
        client_ip: str = "unknown",
    ) -> ChatResponse:
        session = self.get_session(session_id)
        self.validate_not_complete(session)
        self._check_rate_limit(client_ip)
        self._check_daily_llm_limit()

        session.messages.append(ChatMessage(role="user", content=message))

        if detect_injection(message):
            logger.warning("프롬프트 인젝션 감지: session=%s", session_id)
            reply = "죄송하지만 문진과 관련된 내용만 도움드릴 수 있습니다."
        else:
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

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await llm_provider.generate(llm_request)
                self._increment_daily_llm_count()

                if not validate_output(response.content):
                    logger.warning("LLM 응답에 금지 패턴 감지 (시도 %d)", attempt + 1)
                    if attempt >= settings.LLM_MAX_RETRIES:
                        return None
                    continue

                if not validate_output_length(response.content, settings.CHAT_MESSAGE_MAX_LENGTH):
                    logger.warning("LLM 응답 길이 초과 (시도 %d)", attempt + 1)
                    if attempt >= settings.LLM_MAX_RETRIES:
                        return None
                    continue

                parsed = json.loads(response.content)
                return ChatLLMResponse(**parsed)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning("LLM 응답 파싱 실패 (시도 %d): %s", attempt + 1, e)
                if attempt >= settings.LLM_MAX_RETRIES:
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
