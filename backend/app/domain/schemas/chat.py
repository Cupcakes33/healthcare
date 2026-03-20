from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal


class ChatStartRequest(BaseModel):
    age: int = Field(ge=1, le=150)
    gender: Literal["M", "F"]


class ChatMessageRequest(BaseModel):
    chat_session_id: str
    message: str = Field(min_length=1, max_length=500)


class ChatCompleteRequest(BaseModel):
    chat_session_id: str


class SlotStatus(str, Enum):
    NOT_ASKED = "NOT_ASKED"
    FILLED = "FILLED"
    NEGATIVE = "NEGATIVE"
    UNKNOWN = "UNKNOWN"


class SlotState(BaseModel):
    status: SlotStatus = SlotStatus.NOT_ASKED
    value: Optional[str] = None


class InterviewState(BaseModel):
    symptom: SlotState = Field(default_factory=SlotState)
    duration: SlotState = Field(default_factory=SlotState)
    severity: SlotState = Field(default_factory=SlotState)
    history: SlotState = Field(default_factory=SlotState)
    last_asked_slot: Optional[str] = None
    red_flags: List[str] = Field(default_factory=list)


class ExtractedData(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    duration: Optional[str] = None
    severity: Optional[str] = None
    existing_conditions: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    chat_session_id: str
    message: str
    turn: int
    max_turns: int
    is_complete: bool
    can_analyze: bool = False
    extracted_so_far: Optional[ExtractedData] = None


class ChatLLMResponse(BaseModel):
    reply: str
    extracted: ExtractedData
    is_sufficient: bool


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatSessionState(BaseModel):
    chat_session_id: str
    age: int
    gender: str
    messages: List[ChatMessage] = Field(default_factory=list)
    turn: int = 0
    max_turns: int = 8
    extracted_data: ExtractedData = Field(default_factory=ExtractedData)
    interview_state: InterviewState = Field(default_factory=InterviewState)
    is_complete: bool = False
    created_at: datetime
