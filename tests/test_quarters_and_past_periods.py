"""Tests for quarter and past period parsing."""

import pytest
from datetime import datetime

from date_textparser import parse_time_range, parse_time_range_full


class TestQuarters:
    """Tests for quarter parsing (Q1, Q2, Q3, Q4, kwartaal notaties)."""

    @pytest.fixture
    def now(self):
        """Reference date: January 30, 2026."""
        return datetime(2026, 1, 30, 10, 0, 0)

    # --- Q notation tests ---

    def test_q1_current_year(self, now):
        start, end = parse_time_range("Q1", now=now)
        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end.year == 2026
        assert end.month == 3
        assert end.day == 31
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59

    def test_q2_current_year(self, now):
        start, end = parse_time_range("Q2", now=now)
        assert start == datetime(2026, 4, 1, 0, 0, 0)
        assert end.month == 6
        assert end.day == 30
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59

    def test_q3_current_year(self, now):
        start, end = parse_time_range("Q3", now=now)
        assert start == datetime(2026, 7, 1, 0, 0, 0)
        assert end.month == 9
        assert end.day == 30
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59

    def test_q4_current_year(self, now):
        start, end = parse_time_range("Q4", now=now)
        assert start == datetime(2026, 10, 1, 0, 0, 0)
        assert end.month == 12
        assert end.day == 31
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59

    def test_q4_with_year(self, now):
        start, end = parse_time_range("Q4 2025", now=now)
        assert start == datetime(2025, 10, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31
        assert end.second == 59

    def test_q1_with_year(self, now):
        start, end = parse_time_range("Q1 2027", now=now)
        assert start == datetime(2027, 1, 1, 0, 0, 0)
        assert end.year == 2027
        assert end.month == 3
        assert end.day == 31
        assert end.second == 59

    # --- Dutch ordinal notation tests ---

    def test_eerste_kwartaal(self, now):
        start, end = parse_time_range("eerste kwartaal", now=now)
        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end.month == 3
        assert end.second == 59

    def test_tweede_kwartaal(self, now):
        start, end = parse_time_range("tweede kwartaal", now=now)
        assert start == datetime(2026, 4, 1, 0, 0, 0)
        assert end.month == 6
        assert end.second == 59

    def test_derde_kwartaal(self, now):
        start, end = parse_time_range("derde kwartaal", now=now)
        assert start == datetime(2026, 7, 1, 0, 0, 0)
        assert end.month == 9
        assert end.second == 59

    def test_vierde_kwartaal(self, now):
        start, end = parse_time_range("vierde kwartaal", now=now)
        assert start == datetime(2026, 10, 1, 0, 0, 0)
        assert end.month == 12
        assert end.second == 59

    def test_vierde_kwartaal_2025(self, now):
        start, end = parse_time_range("vierde kwartaal 2025", now=now)
        assert start == datetime(2025, 10, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31
        assert end.second == 59

    # --- Numeric ordinal notation tests ---

    def test_1e_kwartaal(self, now):
        start, end = parse_time_range("1e kwartaal", now=now)
        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end.month == 3
        assert end.second == 59

    def test_2e_kwartaal(self, now):
        start, end = parse_time_range("2e kwartaal", now=now)
        assert start == datetime(2026, 4, 1, 0, 0, 0)
        assert end.month == 6
        assert end.second == 59

    def test_3e_kwartaal(self, now):
        start, end = parse_time_range("3e kwartaal", now=now)
        assert start == datetime(2026, 7, 1, 0, 0, 0)
        assert end.month == 9
        assert end.second == 59

    def test_4e_kwartaal(self, now):
        start, end = parse_time_range("4e kwartaal", now=now)
        assert start == datetime(2026, 10, 1, 0, 0, 0)
        assert end.month == 12
        assert end.second == 59

    def test_4e_kwartaal_2025(self, now):
        start, end = parse_time_range("4e kwartaal 2025", now=now)
        assert start == datetime(2025, 10, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12
        assert end.second == 59

    # --- Alternative ordinal notations ---

    def test_1ste_kwartaal(self, now):
        start, end = parse_time_range("1ste kwartaal", now=now)
        assert start == datetime(2026, 1, 1, 0, 0, 0)

    def test_2de_kwartaal(self, now):
        start, end = parse_time_range("2de kwartaal", now=now)
        assert start == datetime(2026, 4, 1, 0, 0, 0)

    def test_3de_kwartaal(self, now):
        start, end = parse_time_range("3de kwartaal", now=now)
        assert start == datetime(2026, 7, 1, 0, 0, 0)

    def test_4de_kwartaal(self, now):
        start, end = parse_time_range("4de kwartaal", now=now)
        assert start == datetime(2026, 10, 1, 0, 0, 0)

    # --- "kwartaal X" notation ---

    def test_kwartaal_1(self, now):
        start, end = parse_time_range("kwartaal 1", now=now)
        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end.month == 3
        assert end.second == 59

    def test_kwartaal_2(self, now):
        start, end = parse_time_range("kwartaal 2", now=now)
        assert start == datetime(2026, 4, 1, 0, 0, 0)

    def test_kwartaal_3(self, now):
        start, end = parse_time_range("kwartaal 3", now=now)
        assert start == datetime(2026, 7, 1, 0, 0, 0)

    def test_kwartaal_4(self, now):
        start, end = parse_time_range("kwartaal 4", now=now)
        assert start == datetime(2026, 10, 1, 0, 0, 0)

    def test_kwartaal_4_2025(self, now):
        start, end = parse_time_range("kwartaal 4 2025", now=now)
        assert start == datetime(2025, 10, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.second == 59

    # --- Case insensitivity ---

    def test_q4_lowercase(self, now):
        start, end = parse_time_range("q4 2025", now=now)
        assert start == datetime(2025, 10, 1, 0, 0, 0)

    def test_q4_uppercase(self, now):
        start, end = parse_time_range("Q4 2025", now=now)
        assert start == datetime(2025, 10, 1, 0, 0, 0)

    def test_vierde_kwartaal_mixed_case(self, now):
        start, end = parse_time_range("Vierde Kwartaal 2025", now=now)
        assert start == datetime(2025, 10, 1, 0, 0, 0)

    # --- Kind metadata ---

    def test_quarter_kind_metadata(self, now):
        result = parse_time_range_full("Q4 2025", now_iso=now.isoformat())
        assert result.assumptions["kind"] == "quarter"


class TestPastPeriods:
    """Tests for past period parsing (afgelopen jaar, vorige maand, etc.)."""

    @pytest.fixture
    def now(self):
        """Reference date: January 30, 2026."""
        return datetime(2026, 1, 30, 10, 0, 0)

    # --- Afgelopen jaar tests ---

    def test_afgelopen_jaar(self, now):
        start, end = parse_time_range("afgelopen jaar", now=now)
        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59

    def test_vorig_jaar(self, now):
        start, end = parse_time_range("vorig jaar", now=now)
        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31
        assert end.second == 59

    def test_vorige_jaar(self, now):
        start, end = parse_time_range("vorige jaar", now=now)
        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.second == 59

    def test_laatste_jaar(self, now):
        start, end = parse_time_range("laatste jaar", now=now)
        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.second == 59

    # --- Afgelopen maand tests ---

    def test_afgelopen_maand(self, now):
        start, end = parse_time_range("afgelopen maand", now=now)
        assert start == datetime(2025, 12, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31
        assert end.second == 59

    def test_vorige_maand(self, now):
        start, end = parse_time_range("vorige maand", now=now)
        assert start == datetime(2025, 12, 1, 0, 0, 0)
        assert end.month == 12
        assert end.second == 59

    def test_laatste_maand(self, now):
        start, end = parse_time_range("laatste maand", now=now)
        assert start == datetime(2025, 12, 1, 0, 0, 0)
        assert end.second == 59

    # --- Afgelopen week tests ---

    def test_afgelopen_week(self, now):
        # January 30, 2026 is Friday
        # Previous week: Monday Jan 19 - Sunday Jan 25
        start, end = parse_time_range("afgelopen week", now=now)
        assert start.year == 2026
        assert start.month == 1
        assert start.day == 19  # Monday of previous week
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert end.day == 25  # Sunday of previous week
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59

    def test_vorige_week(self, now):
        start, end = parse_time_range("vorige week", now=now)
        assert start.month == 1
        assert start.day == 19

    def test_laatste_week(self, now):
        start, end = parse_time_range("laatste week", now=now)
        assert start.month == 1
        assert start.day == 19

    # --- Edge cases: year boundary ---

    def test_afgelopen_jaar_at_year_start(self):
        """Test afgelopen jaar when now is early January."""
        now = datetime(2026, 1, 5, 10, 0, 0)
        start, end = parse_time_range("afgelopen jaar", now=now)
        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12

    def test_afgelopen_maand_at_year_start(self):
        """Test afgelopen maand when now is January (should give December of previous year)."""
        now = datetime(2026, 1, 15, 10, 0, 0)
        start, end = parse_time_range("afgelopen maand", now=now)
        assert start == datetime(2025, 12, 1, 0, 0, 0)
        assert end.year == 2025
        assert end.month == 12

    # --- Kind metadata ---

    def test_past_period_kind_metadata(self, now):
        result = parse_time_range_full("afgelopen jaar", now_iso=now.isoformat())
        assert result.assumptions["kind"] == "past_period"


class TestFuturePeriods:
    """Tests for future period parsing (volgend kwartaal, etc.)."""

    @pytest.fixture
    def now(self):
        """Reference date: January 30, 2026."""
        return datetime(2026, 1, 30, 10, 0, 0)

    def test_volgend_kwartaal(self, now):
        # Now is Jan 2026 (Q1). Next quarter is Q2 (Apr-Jun).
        start, end = parse_time_range("volgend kwartaal", now=now)
        assert start == datetime(2026, 4, 1, 0, 0, 0)
        assert end.month == 6
        assert end.day == 30
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59


class TestQuartersAndPastPeriodsIntegration:
    """Integration tests to ensure quarters and past periods work with other features."""

    @pytest.fixture
    def now(self):
        return datetime(2026, 1, 30, 10, 0, 0)

    def test_quarter_does_not_interfere_with_time_ranges(self, now):
        """Ensure quarter parsing doesn't break normal time ranges."""
        start, end = parse_time_range("van 10:00 tot 12:00", now=now)
        assert start.hour == 10
        assert end.hour == 12

    def test_quarter_does_not_interfere_with_weekdays(self, now):
        """Ensure quarter parsing doesn't break weekday parsing."""
        start, end = parse_time_range("maandag", now=now)
        assert start.weekday() == 0  # Monday

    def test_past_period_does_not_interfere_with_relative_days(self, now):
        """Ensure past period parsing doesn't break 'morgen', 'vandaag' etc."""
        start, end = parse_time_range("morgen", now=now)
        assert start.day == 31

    def test_quarter_in_sentence_context(self, now):
        """Test quarter parsing works even with surrounding text."""
        start, end = parse_time_range("Q4 2025", now=now)
        assert start.year == 2025
        assert start.month == 10


class TestQuarterBoundaryCalculations:
    """Tests for correct quarter boundary calculations."""

    @pytest.fixture
    def now(self):
        return datetime(2026, 6, 15, 10, 0, 0)

    def test_q1_ends_march_31(self, now):
        start, end = parse_time_range("Q1", now=now)
        assert end.month == 3
        assert end.day == 31

    def test_q2_ends_june_30(self, now):
        start, end = parse_time_range("Q2", now=now)
        assert end.month == 6
        assert end.day == 30

    def test_q3_ends_september_30(self, now):
        start, end = parse_time_range("Q3", now=now)
        assert end.month == 9
        assert end.day == 30

    def test_q4_ends_december_31(self, now):
        start, end = parse_time_range("Q4", now=now)
        assert end.month == 12
        assert end.day == 31

    def test_q1_leap_year(self):
        """Test Q1 in a leap year still ends March 31."""
        now = datetime(2024, 2, 15, 10, 0, 0)  # 2024 is a leap year
        start, end = parse_time_range("Q1", now=now)
        assert end.month == 3
        assert end.day == 31
