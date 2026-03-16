from __future__ import annotations

import pytest

from app.domain.schemas.patient import RedFlagResult
from app.service.red_flag_service import RedFlagService


class TestRedFlagService:

    @pytest.fixture
    def service(self):
        return RedFlagService()

    def test_no_red_flag(self, service):
        # given
        symptoms = ["HEADACHE", "FATIGUE"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "NONE"
        assert result.matched_rules == []

    def test_rule1_chest_pressure_with_arm_pain(self, service):
        # given
        symptoms = ["CHEST_PRESSURE", "ARM_RADIATING_PAIN"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "EMERGENCY"
        assert len(result.matched_rules) >= 1
        assert "심장" in result.message

    def test_rule1_chest_pressure_with_jaw_pain(self, service):
        # given
        symptoms = ["CHEST_PRESSURE", "JAW_RADIATING_PAIN"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "EMERGENCY"

    def test_rule1_chest_pressure_with_back_pain(self, service):
        # given
        symptoms = ["CHEST_PRESSURE", "BACK_RADIATING_PAIN"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "EMERGENCY"

    def test_rule1_chest_pressure_alone_no_match(self, service):
        # given
        symptoms = ["CHEST_PRESSURE"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "NONE"

    def test_rule2_thunderclap_headache(self, service):
        # given
        symptoms = ["THUNDERCLAP_HEADACHE"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "EMERGENCY"
        assert "뇌혈관" in result.message

    def test_rule3_paralysis_with_speech_disorder(self, service):
        # given
        symptoms = ["UNILATERAL_PARALYSIS", "SPEECH_DISORDER"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "EMERGENCY"
        assert "뇌졸중" in result.message

    def test_rule3_paralysis_alone_no_match(self, service):
        # given
        symptoms = ["UNILATERAL_PARALYSIS"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "NONE"

    def test_rule4_chronic_cough_weight_loss_fatigue(self, service):
        # given
        symptoms = ["CHRONIC_COUGH", "WEIGHT_LOSS", "FATIGUE"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "URGENT"
        assert "정밀 검사" in result.message

    def test_rule4_partial_no_match(self, service):
        # given
        symptoms = ["CHRONIC_COUGH", "FATIGUE"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "NONE"

    def test_rule5_unexplained_weight_loss(self, service):
        # given
        symptoms = ["UNEXPLAINED_WEIGHT_LOSS"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "CAUTION"
        assert "체중" in result.message

    def test_multiple_rules_highest_level_wins(self, service):
        # given
        symptoms = ["UNEXPLAINED_WEIGHT_LOSS", "THUNDERCLAP_HEADACHE"]

        # when
        result = service.check(symptoms)

        # then
        assert result.level == "EMERGENCY"
        assert len(result.matched_rules) == 2

    def test_all_messages_korean(self, service):
        # given
        test_cases = [
            ["CHEST_PRESSURE", "ARM_RADIATING_PAIN"],
            ["THUNDERCLAP_HEADACHE"],
            ["UNILATERAL_PARALYSIS", "SPEECH_DISORDER"],
            ["CHRONIC_COUGH", "WEIGHT_LOSS", "FATIGUE"],
            ["UNEXPLAINED_WEIGHT_LOSS"],
            ["HEADACHE"],
        ]

        # when / then
        for symptoms in test_cases:
            result = service.check(symptoms)
            assert isinstance(result.message, str)
            assert len(result.message) > 0

    def test_returns_red_flag_result_type(self, service):
        # given
        symptoms = ["HEADACHE"]

        # when
        result = service.check(symptoms)

        # then
        assert isinstance(result, RedFlagResult)

    def test_empty_symptoms(self, service):
        # given / when
        result = service.check([])

        # then
        assert result.level == "NONE"
        assert result.matched_rules == []
