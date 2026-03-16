from __future__ import annotations

from typing import List

from pydantic import BaseModel
from typing_extensions import Literal


class MatchRequest(BaseModel):
    extracted_tags: List[str]
    age: int
    gender: Literal["M", "F"]


class MatchResult(BaseModel):
    package_id: int
    package_name: str
    match_score: float
    matched_tags: List[str]
