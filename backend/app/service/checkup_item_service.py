from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import CheckupItem


class CheckupItemService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_items(self) -> List[CheckupItem]:
        result = await self._session.execute(select(CheckupItem))
        return result.scalars().all()

    async def get_item(self, item_id: int) -> CheckupItem:
        result = await self._session.execute(
            select(CheckupItem).where(CheckupItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise ValueError(f"검진 항목을 찾을 수 없습니다: {item_id}")
        return item
