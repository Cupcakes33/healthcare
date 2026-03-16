from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.domain.models import (
    CheckupItem,
    CheckupPackage,
    CheckupPackageItem,
    PackageSymptomTag,
    SymptomTag,
)
from app.seed.packages import CHECKUP_ITEMS, PACKAGES, SYMPTOM_TAGS, seed


@pytest.mark.asyncio
async def test_seed_data():
    # given: 시드 실행
    await seed()

    # when: DB에서 수량 확인
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        tag_count = (await session.execute(select(func.count()).select_from(SymptomTag))).scalar()
        item_count = (await session.execute(select(func.count()).select_from(CheckupItem))).scalar()
        pkg_count = (await session.execute(select(func.count()).select_from(CheckupPackage))).scalar()
        pkg_item_count = (await session.execute(select(func.count()).select_from(CheckupPackageItem))).scalar()
        pkg_tag_count = (await session.execute(select(func.count()).select_from(PackageSymptomTag))).scalar()

        # then: 데이터 수량 검증
        assert tag_count == len(SYMPTOM_TAGS)
        assert item_count == len(CHECKUP_ITEMS)
        assert pkg_count == len(PACKAGES)
        assert pkg_item_count == sum(len(p["items"]) for p in PACKAGES)
        assert pkg_tag_count == sum(len(p["tags"]) for p in PACKAGES)

        # then: 기본 종합검진 존재
        result = await session.execute(
            select(CheckupPackage).where(CheckupPackage.name == "기본 종합검진")
        )
        assert result.scalar_one_or_none() is not None

        # then: relevance_score 범위 검증
        result = await session.execute(select(PackageSymptomTag))
        for tag in result.scalars().all():
            assert 0.0 <= float(tag.relevance_score) <= 1.0

    await engine.dispose()

    # when: 2회째 실행 (멱등성)
    await seed()

    engine2 = create_async_engine(settings.DATABASE_URL)
    session_factory2 = async_sessionmaker(engine2, expire_on_commit=False)

    async with session_factory2() as session:
        tag_count2 = (await session.execute(select(func.count()).select_from(SymptomTag))).scalar()
        pkg_count2 = (await session.execute(select(func.count()).select_from(CheckupPackage))).scalar()

        # then: 수량 변화 없음
        assert tag_count2 == len(SYMPTOM_TAGS)
        assert pkg_count2 == len(PACKAGES)

    await engine2.dispose()
