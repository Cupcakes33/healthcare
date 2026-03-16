from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.domain.schemas.patient import QuestionnaireRequest


@pytest.fixture
def sample_questionnaire():
    return QuestionnaireRequest(
        age=45,
        gender="M",
        symptoms=["HEADACHE", "FATIGUE", "DIZZINESS"],
        duration="2주",
        existing_conditions=["고혈압"],
    )


@pytest.fixture
def sample_packages():
    return [
        {"id": 1, "name": "기본 종합검진", "description": "기본 건강 검진", "hospital_name": "서울대병원", "target_gender": "ALL", "min_age": 20, "max_age": 100, "price_range": "50~80만원"},
        {"id": 2, "name": "뇌신경 검진", "description": "뇌 및 신경 관련 정밀 검진", "hospital_name": "세브란스병원", "target_gender": "ALL", "min_age": 30, "max_age": 100, "price_range": "80~120만원"},
        {"id": 3, "name": "심혈관 검진", "description": "심장 및 혈관 정밀 검진", "hospital_name": "삼성서울병원", "target_gender": "ALL", "min_age": 30, "max_age": 100, "price_range": "100~150만원"},
    ]


@pytest.fixture
def sample_symptom_tags():
    return [
        {"id": 1, "code": "HEADACHE", "name": "두통"},
        {"id": 2, "code": "FATIGUE", "name": "피로감"},
        {"id": 3, "code": "DIZZINESS", "name": "어지러움"},
        {"id": 4, "code": "CHEST_PAIN", "name": "흉통"},
    ]


@pytest.fixture
def mock_db_session():
    return AsyncMock()
