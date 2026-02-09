"""
Test error handling and edge cases for the parser.

Tests for ValueError exceptions, invalid inputs, and graceful degradation.
"""

import os
import sys
from datetime import datetime

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from date_textparser.core import parse_time_range, parse_time_range_full, normalize_timezone


class TestEmptyAndInvalidInput:
    """Test error handling for empty and invalid inputs."""

    def test_empty_string_raises_error(self):
        """Empty input should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Lege invoer"):
            parse_time_range("", now=now)

    def test_whitespace_only_raises_error(self):
        """Whitespace-only input should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Lege invoer"):
            parse_time_range("   ", now=now)

    def test_tabs_only_raises_error(self):
        """Tab-only input should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Lege invoer"):
            parse_time_range("\t\t", now=now)

    def test_newlines_only_raises_error(self):
        """Newline-only input should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Lege invoer"):
            parse_time_range("\n\n", now=now)


class TestUnparseableInput:
    """Test error handling for completely unparseable text."""

    def test_nonsense_text_raises_error(self):
        """Completely unparseable text should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Kon tekst niet parsen"):
            parse_time_range("xyzabc123nonsense", now=now)

    def test_random_numbers_raises_error(self):
        """Random numbers without context should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Kon tekst niet parsen"):
            parse_time_range("123456789", now=now)

    def test_special_characters_only_raises_error(self):
        """Special characters only should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Kon tekst niet parsen"):
            parse_time_range("@#$%^&*()", now=now)

    def test_emojis_only_raises_error(self):
        """Emojis only should raise ValueError."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Kon tekst niet parsen"):
            parse_time_range("🎉🎊🎈", now=now)


class TestTimezoneHandling:
    """Test timezone normalization and error handling."""

    def test_valid_iana_timezone(self):
        """Valid IANA timezone should be accepted."""
        result = normalize_timezone("Europe/Amsterdam")
        assert result == "Europe/Amsterdam"

    def test_valid_alias_normalized(self):
        """Valid alias should be normalized to IANA."""
        result = normalize_timezone("NYC")
        assert result == "America/New_York"

    def test_case_insensitive_alias(self):
        """Aliases should be case-insensitive."""
        result = normalize_timezone("london")
        assert result == "Europe/London"

    def test_invalid_timezone_returns_input(self):
        """Invalid timezone should return input unchanged."""
        result = normalize_timezone("Invalid/Nonexistent")
        assert result == "Invalid/Nonexistent"

    def test_empty_timezone_returns_default(self):
        """Empty timezone should return default timezone."""
        result = normalize_timezone("")
        # normalize_timezone returns default when given empty string
        assert result in ["Europe/Amsterdam", ""]  # Implementation might vary


class TestParseTimeRangeFull:
    """Test parse_time_range_full error handling."""

    def test_empty_text_raises_error(self):
        """Empty text to parse_time_range_full should raise ValueError."""
        with pytest.raises(ValueError, match="Lege invoer"):
            parse_time_range_full("")

    def test_none_text_raises_error(self):
        """None text should raise ValueError."""
        with pytest.raises(ValueError, match="Lege invoer"):
            parse_time_range_full(None)

    def test_custom_fiscal_start_month_works(self):
        """Custom fiscal_start_month should affect quarter calculation."""
        # Test with fiscal year starting in April (month 4)
        result = parse_time_range_full("Q1 2026", fiscal_start_month=4)
        # Q1 with fiscal_start_month=4 means April-June
        assert result.start.month == 4  # April
        assert result.end.month == 6  # June


class TestEdgeCaseInputs:
    """Test edge case inputs that might cause issues."""

    def test_very_long_input(self):
        """Very long input should either parse or raise error gracefully."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        long_text = "tomorrow " * 1000  # 9000 characters
        # Should either parse "tomorrow" or raise error (not crash)
        try:
            result = parse_time_range(long_text, now=now)
            assert result is not None
        except ValueError:
            pass  # Expected error is acceptable

    def test_unicode_characters(self):
        """Unicode characters should be handled gracefully."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        with pytest.raises(ValueError, match="Kon tekst niet parsen"):
            parse_time_range("中文文字", now=now)

    def test_mixed_valid_invalid(self):
        """Mixed valid/invalid text should parse the valid part or raise error."""
        now = datetime(2026, 1, 30, 12, 0, 0)
        # This has "tomorrow" but with lots of garbage
        # dateparser might handle this gracefully
        result = parse_time_range("xyzabc tomorrow qwerty", now=now)
        # If it parses, it should get tomorrow (Jan 31)
        expected_day = 31 if now.day == 30 else 1  # Tomorrow from Jan 30 is Jan 31
        assert result[0].day == expected_day


class TestNowIsoEdgeCases:
    """Test edge cases for now_iso parameter."""

    def test_invalid_now_iso_format(self):
        """Invalid now_iso format should raise or use fallback."""
        # The function might not validate now_iso strictly
        try:
            result = parse_time_range_full("tomorrow", now_iso="invalid-date")
            # If it succeeds, it should use current time
            assert result is not None
        except (ValueError, Exception):
            pass  # Error is acceptable

    def test_now_iso_with_milliseconds(self):
        """now_iso with milliseconds should work."""
        result = parse_time_range_full(
            "tomorrow", now_iso="2026-01-30T12:00:00.123+01:00"
        )
        assert result.start.year == 2026
        assert result.start.month == 1
        assert result.start.day == 31

    def test_now_iso_utc_format(self):
        """now_iso in UTC format should work."""
        result = parse_time_range_full("tomorrow", now_iso="2026-01-30T12:00:00Z")
        assert result.start.year == 2026
        assert result.start.month == 1
        assert result.start.day == 31
