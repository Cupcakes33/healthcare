from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import (
    CheckupPackage,
    CheckupPackageItem,
    PackageSymptomTag,
)
from app.domain.schemas.admin import PackageCreateRequest, PackageUpdateRequest


class PackageService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_packages(self, is_active: Optional[bool] = None) -> List[CheckupPackage]:
        stmt = select(CheckupPackage)
        if is_active is not None:
            stmt = stmt.where(CheckupPackage.is_active == is_active)
        stmt = stmt.order_by(CheckupPackage.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_package(self, package_id: int) -> CheckupPackage:
        stmt = (
            select(CheckupPackage)
            .where(CheckupPackage.id == package_id)
            .options(
                selectinload(CheckupPackage.package_items),
                selectinload(CheckupPackage.package_tags),
            )
        )
        result = await self._session.execute(stmt)
        package = result.scalar_one_or_none()
        if package is None:
            raise ValueError(f"패키지를 찾을 수 없습니다: {package_id}")
        return package

    async def create_package(self, data: PackageCreateRequest) -> CheckupPackage:
        package = CheckupPackage(
            name=data.name,
            description=data.description,
            hospital_name=data.hospital_name,
            target_gender=data.target_gender,
            min_age=data.min_age,
            max_age=data.max_age,
            price_range=data.price_range,
        )
        self._session.add(package)
        await self._session.flush()

        for item_id in data.item_ids:
            self._session.add(
                CheckupPackageItem(package_id=package.id, item_id=item_id)
            )

        for tag_input in data.symptom_tags:
            self._session.add(
                PackageSymptomTag(
                    package_id=package.id,
                    symptom_tag_id=tag_input.symptom_tag_id,
                    relevance_score=tag_input.relevance_score,
                )
            )

        await self._session.flush()
        return await self.get_package(package.id)

    async def update_package(self, package_id: int, data: PackageUpdateRequest) -> CheckupPackage:
        package = await self.get_package(package_id)

        package.name = data.name
        package.description = data.description
        package.hospital_name = data.hospital_name
        package.target_gender = data.target_gender
        package.min_age = data.min_age
        package.max_age = data.max_age
        package.price_range = data.price_range

        for pi in package.package_items:
            await self._session.delete(pi)

        for pt in package.package_tags:
            await self._session.delete(pt)

        await self._session.flush()

        for item_id in data.item_ids:
            self._session.add(
                CheckupPackageItem(package_id=package.id, item_id=item_id)
            )

        for tag_input in data.symptom_tags:
            self._session.add(
                PackageSymptomTag(
                    package_id=package.id,
                    symptom_tag_id=tag_input.symptom_tag_id,
                    relevance_score=tag_input.relevance_score,
                )
            )

        await self._session.flush()
        return await self.get_package(package.id)

    async def delete_package(self, package_id: int) -> None:
        result = await self._session.execute(
            select(CheckupPackage).where(CheckupPackage.id == package_id)
        )
        package = result.scalar_one_or_none()
        if package is None:
            raise ValueError(f"패키지를 찾을 수 없습니다: {package_id}")
        package.is_active = False
