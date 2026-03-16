from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.schemas.matcher import MatchRequest, MatchResult
from app.service.package_matcher.interface import PackageMatcher
from app.service.package_matcher.tag_matcher import TagMatcher


class TestPackageMatcherInterface:

    def test_is_abstract(self):
        with pytest.raises(TypeError):
            PackageMatcher()

    def test_tag_matcher_is_package_matcher(self):
        mock_session = MagicMock()
        matcher = TagMatcher(session=mock_session)
        assert isinstance(matcher, PackageMatcher)


class TestTagMatcher:

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def matcher(self, mock_session):
        return TagMatcher(session=mock_session)

    @pytest.fixture
    def match_request(self):
        return MatchRequest(
            extracted_tags=["HEADACHE", "FATIGUE"],
            age=45,
            gender="M",
        )

    def _mock_execute_results(self, mock_session, first_rows, second_rows=None):
        first_result = MagicMock()
        first_result.all.return_value = first_rows

        if second_rows is not None:
            second_result = MagicMock()
            second_result.all.return_value = second_rows
            mock_session.execute = AsyncMock(
                side_effect=[first_result, second_result]
            )
        else:
            mock_session.execute = AsyncMock(return_value=first_result)

    @pytest.mark.asyncio
    async def test_match_returns_scored_results(self, matcher, mock_session, match_request):
        # given
        matched_rows = [
            (1, "기본 종합검진", Decimal("0.80"), "HEADACHE"),
            (1, "기본 종합검진", Decimal("0.60"), "FATIGUE"),
            (2, "뇌신경 검진", Decimal("0.90"), "HEADACHE"),
        ]
        total_rows = [
            (1, Decimal("0.80")),
            (1, Decimal("0.60")),
            (1, Decimal("0.70")),
            (2, Decimal("0.90")),
            (2, Decimal("0.50")),
        ]
        self._mock_execute_results(mock_session, matched_rows, total_rows)

        # when
        results = await matcher.match(match_request)

        # then
        assert len(results) >= 1
        assert all(isinstance(r, MatchResult) for r in results)
        assert all(0.0 <= r.match_score <= 1.0 for r in results)

    @pytest.mark.asyncio
    async def test_match_sorted_by_score_descending(self, matcher, mock_session, match_request):
        # given
        matched_rows = [
            (1, "패키지A", Decimal("0.30"), "HEADACHE"),
            (2, "패키지B", Decimal("0.90"), "HEADACHE"),
            (2, "패키지B", Decimal("0.80"), "FATIGUE"),
        ]
        total_rows = [
            (1, Decimal("0.30")),
            (1, Decimal("0.50")),
            (2, Decimal("0.90")),
            (2, Decimal("0.80")),
        ]
        self._mock_execute_results(mock_session, matched_rows, total_rows)

        # when
        results = await matcher.match(match_request)

        # then
        assert results[0].package_name == "패키지B"
        assert results[0].match_score >= results[-1].match_score

    @pytest.mark.asyncio
    async def test_match_max_three_results(self, matcher, mock_session, match_request):
        # given
        matched_rows = [
            (i, f"패키지{i}", Decimal("0.50"), "HEADACHE")
            for i in range(1, 6)
        ]
        total_rows = [
            (i, Decimal("0.50")) for i in range(1, 6)
        ]
        self._mock_execute_results(mock_session, matched_rows, total_rows)

        # when
        results = await matcher.match(match_request)

        # then
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_match_includes_matched_tags(self, matcher, mock_session, match_request):
        # given
        matched_rows = [
            (1, "기본 종합검진", Decimal("0.80"), "HEADACHE"),
            (1, "기본 종합검진", Decimal("0.60"), "FATIGUE"),
        ]
        total_rows = [
            (1, Decimal("0.80")),
            (1, Decimal("0.60")),
        ]
        self._mock_execute_results(mock_session, matched_rows, total_rows)

        # when
        results = await matcher.match(match_request)

        # then
        assert "HEADACHE" in results[0].matched_tags
        assert "FATIGUE" in results[0].matched_tags

    @pytest.mark.asyncio
    async def test_fallback_when_no_match(self, matcher, mock_session, match_request):
        # given
        first_result = MagicMock()
        first_result.all.return_value = []

        fallback_pkg = MagicMock()
        fallback_pkg.id = 1
        fallback_pkg.name = "기본 종합검진"
        fallback_result = MagicMock()
        fallback_result.scalar_one_or_none.return_value = fallback_pkg

        mock_session.execute = AsyncMock(
            side_effect=[first_result, fallback_result]
        )

        # when
        results = await matcher.match(match_request)

        # then
        assert len(results) == 1
        assert results[0].package_name == "기본 종합검진"
        assert results[0].match_score == 0.5
        assert results[0].matched_tags == []

    @pytest.mark.asyncio
    async def test_fallback_empty_when_no_default_package(self, matcher, mock_session, match_request):
        # given
        first_result = MagicMock()
        first_result.all.return_value = []

        fallback_result = MagicMock()
        fallback_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[first_result, fallback_result]
        )

        # when
        results = await matcher.match(match_request)

        # then
        assert results == []

    @pytest.mark.asyncio
    async def test_no_match_returns_fallback_when_demographics_filter_out(self, matcher, mock_session):
        # given
        request_female_young = MatchRequest(
            extracted_tags=["HEADACHE"],
            age=25,
            gender="F",
        )
        first_result = MagicMock()
        first_result.all.return_value = []

        fallback_result = MagicMock()
        fallback_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[first_result, fallback_result]
        )

        # when
        results = await matcher.match(request_female_young)

        # then
        assert results == []

    @pytest.mark.asyncio
    async def test_match_score_calculation(self, matcher, mock_session, match_request):
        # given
        matched_rows = [
            (1, "패키지A", Decimal("0.80"), "HEADACHE"),
        ]
        total_rows = [
            (1, Decimal("0.80")),
            (1, Decimal("0.60")),
        ]
        self._mock_execute_results(mock_session, matched_rows, total_rows)

        # when
        results = await matcher.match(match_request)

        # then
        expected_score = round(0.80 / (0.80 + 0.60), 2)
        assert results[0].match_score == expected_score
