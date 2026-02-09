"""
Parameterized tests for common patterns.

This file demonstrates efficient testing using pytest.mark.parametrize to reduce duplication.
"""

from datetime import datetime, timedelta
import pytest

from date_textparser.core import parse_time_range, normalize_timezone


class TestRelativeDaysParameterized:
    """Parameterized tests for relative day expressions."""

    @pytest.mark.parametrize(
        "text,day_offset",
        [
            ("morgen", 1),
            ("gisteren", -1),
            ("vandaag", 0),
            ("overmorgen", 2),
            ("eergisteren", -2),
            ("tomorrow", 1),
            ("yesterday", -1),
            ("today", 0),
        ],
    )
    def test_relative_days_full_day_ranges(self, text, day_offset):
        """Test that relative day expressions return full day ranges."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        start, end = parse_time_range(text, now=now)

        expected_date = (now + timedelta(days=day_offset)).date()
        expected_start = datetime(
            expected_date.year, expected_date.month, expected_date.day, 0, 0, 0
        )
        expected_end = datetime(
            expected_date.year, expected_date.month, expected_date.day, 23, 59, 59
        )

        assert start == expected_start, f"Start mismatch for '{text}'"
        assert end == expected_end, f"End mismatch for '{text}'"
        # Verify it's a full day (23h 59m 59s)
        assert (end - start).total_seconds() == 86399


class TestRelativeDaysWithTimeParameterized:
    """Parameterized tests for relative days with explicit times."""

    @pytest.mark.parametrize(
        "text,day_offset,expected_hour",
        [
            ("morgen 15:00", 1, 15),
            ("morgen 9 uur", 1, 9),
            ("tomorrow 3pm", 1, 15),
            ("vandaag 14:30", 0, 14),
            ("overmorgen 10:00", 2, 10),
            ("gisteren 16:00", -1, 16),
        ],
    )
    def test_relative_days_with_time(self, text, day_offset, expected_hour):
        """Test relative days with explicit time use default duration."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        start, end = parse_time_range(text, now=now)

        expected_date = (now + timedelta(days=day_offset)).date()

        assert start.date() == expected_date
        assert start.hour == expected_hour
        # Default duration is 60 minutes
        assert (end - start).total_seconds() == 3600


class TestTimezoneAliasesParameterized:
    """Parameterized tests for timezone normalization."""

    @pytest.mark.parametrize(
        "alias,expected_tz",
        [
            ("New York", "America/New_York"),
            ("NYC", "America/New_York"),
            ("nyc", "America/New_York"),  # Case insensitive
            ("London", "Europe/London"),
            ("london", "Europe/London"),
            ("Amsterdam", "Europe/Amsterdam"),
            ("amsterdam", "Europe/Amsterdam"),
            ("Tokyo", "Asia/Tokyo"),
            ("Los Angeles", "America/Los_Angeles"),
            ("Paris", "Europe/Paris"),
            ("Berlin", "Europe/Berlin"),
        ],
    )
    def test_timezone_aliases_normalization(self, alias, expected_tz):
        """Test that various timezone aliases normalize correctly."""
        result = normalize_timezone(alias)
        assert result == expected_tz, f"Failed to normalize '{alias}'"


class TestWeekdaysParameterized:
    """Parameterized tests for weekday expressions."""

    @pytest.mark.parametrize(
        "weekday_nl,weekday_en,expected_weekday",
        [
            ("maandag", "monday", 0),
            ("dinsdag", "tuesday", 1),
            ("woensdag", "wednesday", 2),
            ("donderdag", "thursday", 3),
            ("vrijdag", "friday", 4),
            ("zaterdag", "saturday", 5),
            ("zondag", "sunday", 6),
        ],
    )
    def test_weekday_bilingual(self, weekday_nl, weekday_en, expected_weekday):
        """Test that both Dutch and English weekday names work."""
        now = datetime(2026, 1, 26, 9, 0, 0)  # Monday

        # Test Dutch
        start_nl, end_nl = parse_time_range(weekday_nl, now=now)
        assert start_nl.weekday() == expected_weekday

        # Test English
        start_en, end_en = parse_time_range(weekday_en, now=now)
        assert start_en.weekday() == expected_weekday

        # Both should produce same result
        assert start_nl.date() == start_en.date()


class TestExplicitTimeRangesParameterized:
    """Parameterized tests for explicit time ranges."""

    @pytest.mark.parametrize(
        "text,expected_start_hour,expected_end_hour",
        [
            ("van 10:00 tot 12:30", 10, 12),
            ("van 9 tot 17 uur", 9, 17),
            ("tussen 14:00 en 15:30", 14, 15),
            ("from 10 to 12", 10, 12),
            ("van 8 tot 12", 8, 12),
        ],
    )
    def test_explicit_time_ranges(self, text, expected_start_hour, expected_end_hour):
        """Test explicit time ranges with 'van...tot' and 'tussen...en' patterns."""
        now = datetime(2026, 1, 30, 9, 0, 0)
        start, end = parse_time_range(text, now=now)

        assert start.hour == expected_start_hour
        assert end.hour >= expected_end_hour  # End might be 12:30, 15:30, etc.


class TestDutchTimeExpressionsParameterized:
    """Parameterized tests for Dutch time notation."""

    @pytest.mark.parametrize(
        "text,expected_hour,expected_minute",
        [
            ("half 10", 9, 30),  # Half past 9 = 9:30
            ("kwart over 3", 3, 15),  # Quarter past 3 = 3:15
            ("kwart voor 4", 3, 45),  # Quarter to 4 = 3:45
            ("half 1", 0, 30),  # Half past 12 (midnight) = 0:30
            ("morgen half 3", 2, 30),  # Tomorrow at half past 2 = 2:30
        ],
    )
    def test_dutch_time_notation(self, text, expected_hour, expected_minute):
        """Test Dutch time expressions like 'half 10' and 'kwart over 3'.

        Note: Dutch 'half X' means 'half past (X-1)', so 'half 3' = 2:30
        """
        now = datetime(2026, 1, 30, 12, 0, 0)
        start, end = parse_time_range(text, now=now)

        assert start.hour == expected_hour
        assert start.minute == expected_minute


class TestPeriodExpressionsParameterized:
    """Parameterized tests for period expressions."""

    @pytest.mark.parametrize(
        "text,period_type",
        [
            ("volgende week", "week"),
            ("deze week", "week"),
            ("vorige week", "week"),
            ("volgende maand", "month"),
            ("deze maand", "month"),
            ("vorige maand", "month"),
            ("next week", "week"),
            ("this week", "week"),
            ("last week", "week"),
            ("next month", "month"),
            ("this month", "month"),
            ("last month", "month"),
        ],
    )
    def test_period_expressions_return_ranges(self, text, period_type):
        """Test that period expressions return appropriate ranges."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        start, end = parse_time_range(text, now=now)

        # All should return valid ranges
        assert start < end
        assert start.microsecond == 0
        assert end.microsecond == 0

        # Verify appropriate duration
        duration_days = (end - start).days
        if period_type == "week":
            assert 6 <= duration_days <= 7  # Week ranges
        elif period_type == "month":
            assert 27 <= duration_days <= 31  # Month ranges


class TestQuarterExpressionsParameterized:
    """Parameterized tests for quarter expressions."""

    @pytest.mark.parametrize(
        "text,expected_start_month,expected_end_month",
        [
            ("Q1 2026", 1, 3),
            ("Q2 2026", 4, 6),
            ("Q3 2026", 7, 9),
            ("Q4 2026", 10, 12),
            ("eerste kwartaal 2026", 1, 3),
            ("tweede kwartaal 2026", 4, 6),
            ("derde kwartaal 2026", 7, 9),
            ("vierde kwartaal 2026", 10, 12),
        ],
    )
    def test_quarter_expressions(self, text, expected_start_month, expected_end_month):
        """Test quarter expressions in various formats."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        start, end = parse_time_range(text, now=now)

        assert start.month == expected_start_month
        assert start.day == 1
        assert end.month == expected_end_month
        # End should be last day of the month
        assert end.day >= 28


class TestDurationExpressionsParameterized:
    """Parameterized tests for duration expressions."""

    @pytest.mark.parametrize(
        "text,time_unit",
        [
            ("2 uur", "hours"),
            ("30 minuten", "minutes"),
            ("3 dagen", "days"),
            ("2 weken", "weeks"),
            ("1 maand", "months"),
            ("2 hours", "hours"),
            ("30 minutes", "minutes"),
            ("3 days", "days"),
            ("2 weeks", "weeks"),
        ],
    )
    def test_duration_expressions_create_ranges(self, text, time_unit):
        """Test that duration expressions create appropriate ranges."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        start, end = parse_time_range(text, now=now)

        # Should create a range
        assert start <= end
        # Duration should be positive
        duration = (end - start).total_seconds()
        assert duration > 0


class TestEnglishNlEquivalence:
    """Test that English and Dutch expressions produce equivalent results."""

    @pytest.mark.parametrize(
        "dutch,english",
        [
            ("morgen", "tomorrow"),
            ("gisteren", "yesterday"),
            ("volgende vrijdag", "next friday"),
            ("vorige maandag", "last monday"),
            ("deze week", "this week"),
            ("volgende maand", "next month"),
        ],
    )
    def test_dutch_english_equivalence(self, dutch, english):
        """Ensure Dutch and English inputs produce equivalent results."""
        now = datetime(2026, 1, 30, 12, 0, 0)

        start_nl, end_nl = parse_time_range(dutch, now=now)
        start_en, end_en = parse_time_range(english, now=now)

        # Dates should match exactly
        assert start_nl.date() == start_en.date()
        assert end_nl.date() == end_en.date()

        # Times should be very close (allow for minor parsing differences)
        assert abs((start_en - start_nl).total_seconds()) < 60
        assert abs((end_en - end_nl).total_seconds()) < 60
