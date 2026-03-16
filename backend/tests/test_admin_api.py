from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import _login_attempts, _token_store, create_token
from app.main import app


class TestAdminAuth:

    @pytest.fixture
    def client(self):
        _token_store.clear()
        _login_attempts.clear()
        return TestClient(app)

    @patch("app.core.auth.settings")
    def test_login_success(self, mock_settings, client):
        # given
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "test-secure-pw"

        # when
        response = client.post("/api/v1/admin/login", json={
            "username": "admin",
            "password": "test-secure-pw",
        })

        # then
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "expires_at" in data

    @patch("app.core.auth.settings")
    def test_login_wrong_password(self, mock_settings, client):
        # given
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "test-secure-pw"

        # when
        response = client.post("/api/v1/admin/login", json={
            "username": "admin",
            "password": "wrong",
        })

        # then
        assert response.status_code == 401

    @patch("app.core.auth.settings")
    def test_login_wrong_username(self, mock_settings, client):
        # given
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "test-secure-pw"

        # when
        response = client.post("/api/v1/admin/login", json={
            "username": "hacker",
            "password": "test-secure-pw",
        })

        # then
        assert response.status_code == 401

    @patch("app.core.auth.settings")
    def test_login_empty_password_returns_500(self, mock_settings, client):
        # given
        mock_settings.ADMIN_PASSWORD = ""

        # when
        response = client.post("/api/v1/admin/login", json={
            "username": "admin",
            "password": "anything",
        })

        # then
        assert response.status_code == 500

    @patch("app.core.auth.settings")
    def test_brute_force_lockout(self, mock_settings, client):
        # given
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "test-secure-pw"

        # when
        for _ in range(5):
            client.post("/api/v1/admin/login", json={
                "username": "admin",
                "password": "wrong",
            })

        response = client.post("/api/v1/admin/login", json={
            "username": "admin",
            "password": "test-secure-pw",
        })

        # then
        assert response.status_code == 429


class TestAdminRoutes:

    @pytest.fixture
    def client(self):
        _token_store.clear()
        _login_attempts.clear()
        return TestClient(app)

    def test_packages_route_exists(self, client):
        routes = [route.path for route in app.routes]
        assert "/api/v1/admin/packages" in routes

    def test_stats_route_exists(self, client):
        routes = [route.path for route in app.routes]
        assert "/api/v1/admin/stats" in routes

    def test_packages_without_auth_returns_403(self, client):
        response = client.get("/api/v1/admin/packages")
        assert response.status_code == 403

    def test_stats_without_auth_returns_403(self, client):
        response = client.get("/api/v1/admin/stats")
        assert response.status_code == 403

    def test_packages_with_invalid_token_returns_401(self, client):
        response = client.get(
            "/api/v1/admin/packages",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
