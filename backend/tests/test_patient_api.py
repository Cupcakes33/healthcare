from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestPatientAPIRoutes:

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_questionnaire_route_exists(self, client):
        routes = [route.path for route in app.routes]
        assert "/api/v1/questionnaire" in routes

    def test_result_route_exists(self, client):
        routes = [route.path for route in app.routes]
        assert "/api/v1/result/{session_key}" in routes

    def test_questionnaire_validation_error(self, client):
        response = client.post("/api/v1/questionnaire", json={})
        assert response.status_code == 422

    def test_questionnaire_invalid_gender(self, client):
        response = client.post("/api/v1/questionnaire", json={
            "age": 30,
            "gender": "X",
            "symptoms": ["HEADACHE"],
            "duration": "1주",
            "existing_conditions": [],
        })
        assert response.status_code == 422

    def test_result_invalid_uuid_returns_404(self, client):
        # given
        invalid_key = "nonexistent-key"

        # when
        response = client.get(f"/api/v1/result/{invalid_key}")

        # then
        assert response.status_code == 404
