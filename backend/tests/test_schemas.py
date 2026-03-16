import pytest
from pydantic import ValidationError

from app.domain.schemas import (
    MatchRequest,
    PackageCreateRequest,
    PackageRecommendation,
    QuestionnaireRequest,
    RedFlagResult,
)


class TestQuestionnaireRequest:
    def test_valid_request(self):
        # given / when
        req = QuestionnaireRequest(
            age=45, gender="M", symptoms=["CHEST_PAIN"], duration="1주일", existing_conditions=["고혈압"]
        )

        # then
        assert req.age == 45
        assert req.gender == "M"

    def test_negative_age_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError):
            QuestionnaireRequest(age=-1, gender="M", symptoms=["X"], duration="1주일", existing_conditions=[])

    def test_invalid_gender_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError):
            QuestionnaireRequest(age=30, gender="X", symptoms=["X"], duration="1주일", existing_conditions=[])

    def test_empty_symptoms_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError):
            QuestionnaireRequest(age=30, gender="M", symptoms=[], duration="1주일", existing_conditions=[])


class TestRedFlagResult:
    def test_valid_levels(self):
        # given / when / then
        for level in ["NONE", "CAUTION", "URGENT", "EMERGENCY"]:
            result = RedFlagResult(level=level, matched_rules=[], message="test")
            assert result.level == level

    def test_invalid_level_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError):
            RedFlagResult(level="INVALID", matched_rules=[], message="test")


class TestPackageRecommendation:
    def test_score_out_of_range_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError):
            PackageRecommendation(
                package_id=1, package_name="test", match_score=1.5, reason="r", matched_tags=[]
            )


class TestPackageCreateRequest:
    def test_empty_items_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError):
            PackageCreateRequest(
                name="test", hospital_name="h", target_gender="ALL",
                min_age=20, max_age=60, price_range="10만", item_ids=[]
            )

    def test_min_age_greater_than_max_age_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError, match="최소 나이는 최대 나이보다 클 수 없습니다"):
            PackageCreateRequest(
                name="test", hospital_name="h", target_gender="ALL",
                min_age=80, max_age=20, price_range="10만", item_ids=[1]
            )


class TestMatchRequest:
    def test_valid(self):
        # given / when
        req = MatchRequest(extracted_tags=["CHEST_PAIN"], age=45, gender="M")

        # then
        assert req.age == 45
