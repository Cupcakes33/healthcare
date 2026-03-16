from __future__ import annotations

import abc
from typing import List

from app.domain.schemas.matcher import MatchRequest, MatchResult


class PackageMatcher(abc.ABC):
    @abc.abstractmethod
    async def match(self, request: MatchRequest) -> List[MatchResult]:
        pass
