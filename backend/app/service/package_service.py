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
from app.domain.schemas.admin import (
    CheckupItemInfo,
    PackageCreateRequest,
    PackageListItem,
    PackageResponse,
    PackageUpdateRequest,
    SymptomTagInfo,
)


class PackageService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_packages(self, is_active: Optional[bool] = None) -> List[CheckupPackage]:
        stmt = (
            select(CheckupPackage)
            .options(
                selectinload(CheckupPackage.package_items),
                selectinload(CheckupPackage.package_tags),
            )
        )
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
                selectinload(CheckupPackage.package_items).selectinload(CheckupPackageItem.item),
                selectinload(CheckupPackage.package_tags).selectinload(PackageSymptomTag.symptom_tag),
            )
        )
        result = await self._session.execute(stmt)
        package = result.scalar_one_or_none()
        if package is None:
            raise ValueError(f"패키지를 찾을 수 없습니다: {package_id}")
        return package

    def package_to_response(self, package: CheckupPackage) -> PackageResponse:
        symptom_tags = []
        for pt in (package.package_tags or []):
            tag = pt.symptom_tag
            if tag:
                symptom_tags.append(
                    SymptomTagInfo(
                        id=tag.id, code=tag.code, name=tag.name,
                        relevance_score=float(pt.relevance_score),
                    )
                )

        checkup_items = []
        for pi in (package.package_items or []):
            item = pi.item
            if item:
                checkup_items.append(
                    CheckupItemInfo(id=item.id, code=item.code, name=item.name)
                )

        return PackageResponse(
            id=package.id,
            name=package.name,
            description=package.description,
            hospital_name=package.hospital_name,
            target_gender=package.target_gender,
            min_age=package.min_age,
            max_age=package.max_age,
            price_range=package.price_range,
            is_active=package.is_active,
            symptom_tags=symptom_tags,
            checkup_items=checkup_items,
            created_at=package.created_at,
            updated_at=package.updated_at,
        )

    def package_to_list_item(self, package: CheckupPackage) -> PackageListItem:
        return PackageListItem(
            id=package.id,
            name=package.name,
            hospital_name=package.hospital_name,
            target_gender=package.target_gender,
            min_age=package.min_age,
            max_age=package.max_age,
            price_range=package.price_range,
            is_active=package.is_active,
            item_count=len(package.package_items) if package.package_items else 0,
            tag_count=len(package.package_tags) if package.package_tags else 0,
            created_at=package.created_at,
        )

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
