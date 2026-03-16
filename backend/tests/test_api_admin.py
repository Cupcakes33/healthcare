from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import _login_attempts, _token_store, create_token
from app.domain.schemas.admin import AdminLoginResponse, PackageResponse
from app.main import app

LOGIN_URL = "/api/v1/admin/login"
STATS_URL = "/api/v1/admin/stats"
PACKAGES_URL = "/api/v1/admin/packages"

TEST_PASSWORD = "test-secure-password"


@pytest.fixture(autouse=True)
def clear_auth_state():
    _token_store.clear()
    _login_attempts.clear()
    yield
    _token_store.clear()
    _login_attempts.clear()


@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def override_get_db():
        yield mock_session

    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    yield mock_session
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_db):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def auth_header():
    token, _ = create_token()
    return {"Authorization": f"Bearer {token}"}


def _make_mock_package(**overrides):
    now = datetime.utcnow()
    pkg = MagicMock()
    pkg.id = overrides.get("id", 1)
    pkg.name = overrides.get("name", "기본 종합검진")
    pkg.description = overrides.get("description", "기본 건강 검진")
    pkg.hospital_name = overrides.get("hospital_name", "서울대병원")
    pkg.target_gender = overrides.get("target_gender", "ALL")
    pkg.min_age = overrides.get("min_age", 20)
    pkg.max_age = overrides.get("max_age", 100)
    pkg.price_range = overrides.get("price_range", "50~80만원")
    pkg.is_active = overrides.get("is_active", True)
    pkg.package_items = overrides.get("package_items", [])
    pkg.package_tags = overrides.get("package_tags", [])
    pkg.created_at = overrides.get("created_at", now)
    pkg.updated_at = overrides.get("updated_at", now)
    return pkg


class TestAdminLogin:
    async def test_valid_credentials_returns_200(self, client, mock_db):
        # given
        payload = {"username": "admin", "password": TEST_PASSWORD}

        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.ADMIN_USERNAME = "admin"
            mock_settings.ADMIN_PASSWORD = TEST_PASSWORD

            # when
            response = await client.post(LOGIN_URL, json=payload)

        # then
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "expires_at" in data
        AdminLoginResponse(**data)

    async def test_invalid_credentials_returns_401(self, client, mock_db):
        # given
        payload = {"username": "admin", "password": "wrong-password"}

        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.ADMIN_USERNAME = "admin"
            mock_settings.ADMIN_PASSWORD = TEST_PASSWORD

            # when
            response = await client.post(LOGIN_URL, json=payload)

        # then
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestAdminStats:
    async def test_with_auth_returns_200(self, client, mock_db, auth_header):
        # given
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # when
        response = await client.get(STATS_URL, headers=auth_header)

        # then
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "age_distribution" in data
        assert "top_symptoms" in data
        assert "top_packages" in data
        assert "red_flag_ratio" in data

    async def test_without_auth_returns_401_or_403(self, client, mock_db):
        # when
        response = await client.get(STATS_URL)

        # then
        assert response.status_code in (401, 403)


class TestAdminPackages:
    async def test_create_package_returns_201(self, client, mock_db, auth_header):
        # given
        payload = {
            "name": "테스트 패키지",
            "description": "테스트",
            "hospital_name": "테스트병원",
            "target_gender": "ALL",
            "min_age": 20,
            "max_age": 80,
            "price_range": "50만원",
            "symptom_tags": [],
            "item_ids": [1],
        }

        mock_package = _make_mock_package(name="테스트 패키지")

        with patch(
            "app.api.v1.endpoints.admin_packages.PackageService"
        ) as MockService:
            instance = MockService.return_value
            instance.create_package = AsyncMock(return_value=mock_package)
            instance.package_to_response = MagicMock(
                return_value=PackageResponse(
                    id=1,
                    name="테스트 패키지",
                    description="테스트",
                    hospital_name="테스트병원",
                    target_gender="ALL",
                    min_age=20,
                    max_age=80,
                    price_range="50만원",
                    is_active=True,
                    symptom_tags=[],
                    checkup_items=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

            # when
            response = await client.post(
                PACKAGES_URL, json=payload, headers=auth_header
            )

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "테스트 패키지"
        PackageResponse(**data)

    async def test_get_package_returns_200(self, client, mock_db, auth_header):
        # given
        mock_package = _make_mock_package()

        with patch(
            "app.api.v1.endpoints.admin_packages.PackageService"
        ) as MockService:
            instance = MockService.return_value
            instance.get_package = AsyncMock(return_value=mock_package)
            instance.package_to_response = MagicMock(
                return_value=PackageResponse(
                    id=1,
                    name="기본 종합검진",
                    description="기본 건강 검진",
                    hospital_name="서울대병원",
                    target_gender="ALL",
                    min_age=20,
                    max_age=100,
                    price_range="50~80만원",
                    is_active=True,
                    symptom_tags=[],
                    checkup_items=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

            # when
            response = await client.get(f"{PACKAGES_URL}/1", headers=auth_header)

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "기본 종합검진"
        PackageResponse(**data)

    async def test_update_nonexistent_package_returns_404(
        self, client, mock_db, auth_header
    ):
        # given
        payload = {
            "name": "수정",
            "hospital_name": "병원",
            "target_gender": "ALL",
            "min_age": 20,
            "max_age": 80,
            "price_range": "50만원",
            "symptom_tags": [],
            "item_ids": [1],
        }

        with patch(
            "app.api.v1.endpoints.admin_packages.PackageService"
        ) as MockService:
            instance = MockService.return_value
            instance.update_package = AsyncMock(
                side_effect=ValueError("패키지를 찾을 수 없습니다")
            )

            # when
            response = await client.put(
                f"{PACKAGES_URL}/999", json=payload, headers=auth_header
            )

        # then
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    async def test_delete_package_returns_200(self, client, mock_db, auth_header):
        # given
        with patch(
            "app.api.v1.endpoints.admin_packages.PackageService"
        ) as MockService:
            instance = MockService.return_value
            instance.delete_package = AsyncMock()

            # when
            response = await client.delete(
                f"{PACKAGES_URL}/1", headers=auth_header
            )

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "패키지가 비활성화되었습니다"

    async def test_create_without_auth_returns_401_or_403(self, client, mock_db):
        # given
        payload = {
            "name": "패키지",
            "hospital_name": "병원",
            "target_gender": "ALL",
            "min_age": 20,
            "max_age": 80,
            "price_range": "50만원",
            "item_ids": [1],
        }

        # when
        response = await client.post(PACKAGES_URL, json=payload)

        # then
        assert response.status_code in (401, 403)
