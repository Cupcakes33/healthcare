from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Literal


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    expires_at: datetime


class SymptomTagScore(BaseModel):
    symptom_tag_id: int
    relevance_score: float = Field(ge=0.0, le=1.0)


class PackageCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    hospital_name: str
    target_gender: Literal["M", "F", "ALL"]
    min_age: int = Field(ge=0)
    max_age: int = Field(ge=0)
    price_range: str
    symptom_tags: List[SymptomTagScore] = Field(default_factory=list)
    item_ids: List[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_age_range(self):
        if self.min_age > self.max_age:
            raise ValueError("최소 나이는 최대 나이보다 클 수 없습니다")
        return self


PackageUpdateRequest = PackageCreateRequest


class SymptomTagInfo(BaseModel):
    id: int
    code: str
    name: str
    relevance_score: float

    model_config = ConfigDict(from_attributes=True)


class CheckupItemInfo(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class PackageListItem(BaseModel):
    id: int
    name: str
    hospital_name: str
    target_gender: str
    min_age: int
    max_age: int
    price_range: str
    is_active: bool
    item_count: int
    tag_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PackageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    hospital_name: str
    target_gender: str
    min_age: int
    max_age: int
    price_range: str
    is_active: bool
    symptom_tags: List[SymptomTagInfo]
    checkup_items: List[CheckupItemInfo]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SymptomCount(BaseModel):
    name: str
    count: int


class PackageCount(BaseModel):
    name: str
    count: int


class StatsResponse(BaseModel):
    total_sessions: int
    age_distribution: dict
    top_symptoms: List[SymptomCount]
    top_packages: List[PackageCount]
    red_flag_ratio: float
