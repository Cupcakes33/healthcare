from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.service.package_service import PackageService
from app.service.checkup_item_service import CheckupItemService
from app.service.symptom_tag_service import SymptomTagService


class TestCheckupItemService:

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return CheckupItemService(mock_session)

    @pytest.mark.asyncio
    async def test_get_items(self, service, mock_session):
        # given
        item1 = MagicMock(id=1, code="BLOOD_TEST_CBC", name="일반혈액검사(CBC)", description="혈구 수 측정")
        item2 = MagicMock(id=2, code="ECG", name="심전도", description="심장 전기 활동 측정")
        result = MagicMock()
        result.scalars.return_value.all.return_value = [item1, item2]
        mock_session.execute.return_value = result

        # when
        items = await service.get_items()

        # then
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_get_item_not_found(self, service, mock_session):
        # given
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result

        # when / then
        with pytest.raises(ValueError, match="검진 항목을 찾을 수 없습니다"):
            await service.get_item(999)


class TestSymptomTagService:

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return SymptomTagService(mock_session)

    @pytest.mark.asyncio
    async def test_get_tags(self, service, mock_session):
        # given
        tag1 = MagicMock(id=1, code="HEADACHE", name="두통", category="신경계")
        tag2 = MagicMock(id=2, code="FATIGUE", name="피로감", category="전신")
        result = MagicMock()
        result.scalars.return_value.all.return_value = [tag1, tag2]
        mock_session.execute.return_value = result

        # when
        tags = await service.get_tags()

        # then
        assert len(tags) == 2

    @pytest.mark.asyncio
    async def test_get_tags_by_category(self, service, mock_session):
        # given
        tag1 = MagicMock(id=1, code="HEADACHE", name="두통", category="신경계")
        result = MagicMock()
        result.scalars.return_value.all.return_value = [tag1]
        mock_session.execute.return_value = result

        # when
        tags = await service.get_tags(category="신경계")

        # then
        assert len(tags) == 1

    @pytest.mark.asyncio
    async def test_get_tag_not_found(self, service, mock_session):
        # given
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result

        # when / then
        with pytest.raises(ValueError, match="증상 태그를 찾을 수 없습니다"):
            await service.get_tag(999)


class TestPackageService:

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return PackageService(mock_session)

    @pytest.mark.asyncio
    async def test_get_package_not_found(self, service, mock_session):
        # given
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result

        # when / then
        with pytest.raises(ValueError, match="패키지를 찾을 수 없습니다"):
            await service.get_package(999)

    @pytest.mark.asyncio
    async def test_delete_package_soft_delete(self, service, mock_session):
        # given
        package = MagicMock(id=1, is_active=True)
        result = MagicMock()
        result.scalar_one_or_none.return_value = package
        mock_session.execute.return_value = result

        # when
        await service.delete_package(1)

        # then
        assert package.is_active is False

    @pytest.mark.asyncio
    async def test_delete_package_not_found(self, service, mock_session):
        # given
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result

        # when / then
        with pytest.raises(ValueError, match="패키지를 찾을 수 없습니다"):
            await service.delete_package(999)
