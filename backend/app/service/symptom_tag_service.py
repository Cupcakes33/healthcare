from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import SymptomTag


class SymptomTagService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_tags(self, category: Optional[str] = None) -> List[SymptomTag]:
        stmt = select(SymptomTag)
        if category is not None:
            stmt = stmt.where(SymptomTag.category == category)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_tag(self, tag_id: int) -> SymptomTag:
        result = await self._session.execute(
            select(SymptomTag).where(SymptomTag.id == tag_id)
        )
        tag = result.scalar_one_or_none()
        if tag is None:
            raise ValueError(f"증상 태그를 찾을 수 없습니다: {tag_id}")
        return tag
