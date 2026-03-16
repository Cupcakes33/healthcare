from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.domain.schemas.patient import PackageRecommendation


class LLMRequest(BaseModel):
    system_prompt: str
    user_prompt: str


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str


class LLMAnalysisResult(BaseModel):
    summary: str
    extracted_tags: List[str]
    recommendations: List[PackageRecommendation]
    matched_tags: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
