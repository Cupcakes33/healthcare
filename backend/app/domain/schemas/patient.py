from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field
from typing_extensions import Literal


class QuestionnaireRequest(BaseModel):
    age: int = Field(ge=1, le=150)
    gender: Literal["M", "F"]
    symptoms: List[str] = Field(min_length=1)
    duration: str
    existing_conditions: List[str] = Field(default_factory=list)


class InputSummary(BaseModel):
    age: int
    gender: str
    symptoms: List[str]
    duration: str
    existing_conditions: List[str]


class RedFlagResult(BaseModel):
    level: Literal["NONE", "CAUTION", "URGENT", "EMERGENCY"]
    matched_rules: List[str]
    message: str


class PackageRecommendation(BaseModel):
    package_id: int
    package_name: str
    match_score: float = Field(ge=0.0, le=1.0)
    reason: str
    matched_tags: List[str]


class QuestionnaireResponse(BaseModel):
    session_key: str
    summary: str
    input_summary: InputSummary
    red_flag: RedFlagResult
    recommendations: List[PackageRecommendation]
    disclaimer: str
