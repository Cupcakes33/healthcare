from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.auth import _token_store, create_token
from app.main import app


class TestAdminAuth:

    @pytest.fixture
    def client(self):
        _token_store.clear()
        return TestClient(app)

    def test_login_success(self, client):
        response = client.post("/api/v1/admin/login", json={
            "username": "admin",
            "password": "1111",
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "expires_at" in data

    def test_login_wrong_password(self, client):
        response = client.post("/api/v1/admin/login", json={
            "username": "admin",
            "password": "wrong",
        })
        assert response.status_code == 401

    def test_login_wrong_username(self, client):
        response = client.post("/api/v1/admin/login", json={
            "username": "hacker",
            "password": "1111",
        })
        assert response.status_code == 401


class TestAdminRoutes:

    @pytest.fixture
    def client(self):
        _token_store.clear()
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
