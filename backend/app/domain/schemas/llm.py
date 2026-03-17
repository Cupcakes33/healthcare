from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    model_override: Optional[str] = None


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str


class LLMPackageRecommendation(BaseModel):
    package_id: int
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)


class LLMAnalysisResult(BaseModel):
    summary: str
    extracted_tags: List[str]
    recommendations: List[LLMPackageRecommendation]
    confidence: float = Field(ge=0.0, le=1.0)
