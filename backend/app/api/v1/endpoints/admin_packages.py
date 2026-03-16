from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.database import get_db
from app.domain.schemas.admin import (
    PackageCreateRequest,
    PackageListItem,
    PackageResponse,
    PackageUpdateRequest,
)
from app.service.package_service import PackageService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/packages", response_model=List[PackageListItem])
async def list_packages(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    service = PackageService(db)
    packages = await service.get_packages(is_active=is_active)
    return [service.package_to_list_item(p) for p in packages]


@router.get("/packages/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = PackageService(db)
    try:
        package = await service.get_package(package_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="패키지를 찾을 수 없습니다")

    return service.package_to_response(package)


@router.post("/packages", response_model=PackageResponse, status_code=201)
async def create_package(
    data: PackageCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PackageService(db)
    package = await service.create_package(data)
    await db.commit()
    return service.package_to_response(package)


@router.put("/packages/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: int,
    data: PackageUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PackageService(db)
    try:
        package = await service.update_package(package_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="패키지를 찾을 수 없습니다")
    await db.commit()
    return service.package_to_response(package)


@router.delete("/packages/{package_id}")
async def delete_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = PackageService(db)
    try:
        await service.delete_package(package_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="패키지를 찾을 수 없습니다")
    await db.commit()
    return {"success": True, "message": "패키지가 비활성화되었습니다"}
