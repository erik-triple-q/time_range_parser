from __future__ import annotations

from datetime import datetime
import pytest
import pendulum

from date_textparser.core import (
    convert_to_timezone,
    normalize_timezone,
    parse_time_range_full,
)


class TestTimezoneAliases:
    """Test if friendly names like 'New York' are correctly mapped."""

    def test_normalize_new_york(self):
        assert normalize_timezone("New York") == "America/New_York"
        assert normalize_timezone("nyc") == "America/New_York"
        assert normalize_timezone("NY") == "America/New_York"

    def test_normalize_london(self):
        assert normalize_timezone("London") == "Europe/London"
        assert normalize_timezone("UK") == "Europe/London"

    def test_normalize_unknown_returns_input(self):
        # Unknown/Valid IANA zones should pass through
        assert normalize_timezone("Europe/Berlin") == "Europe/Berlin"
        assert normalize_timezone("Mars/City") == "Mars/City"

    def test_integration_in_parser(self):
        """Ensure parse_time_range_full accepts aliases."""
        # Should not raise InvalidTimezone
        result = parse_time_range_full("now", tz="New York")
        assert result.timezone == "America/New_York"
        assert result.start.timezone_name == "America/New_York"


class TestConvertTimezone:
    """Test the convert_to_timezone logic."""

    @pytest.fixture
    def now_iso(self):
        # 2026-01-30 15:00 Amsterdam
        return "2026-01-30T15:00:00+01:00"

    def test_amsterdam_to_new_york(self, now_iso):
        """15:00 AMS -> 09:00 NYC (6h difference in winter)."""
        res = convert_to_timezone(
            text="15:00", source_tz="Amsterdam", target_tz="New York", now_iso=now_iso
        )

        assert res["source_timezone"] == "Europe/Amsterdam"
        assert res["target_timezone"] == "America/New_York"

        # Check source (15:00)
        assert "15:00:00" in res["source_start"]

        # Check target (09:00)
        assert "09:00:00" in res["target_start"]

        # Check offset diff (-6 hours)
        assert res["utc_offset_diff_hours"] == -6.0

    def test_london_to_tokyo(self, now_iso):
        """12:00 London -> 21:00 Tokyo (9h difference)."""
        res = convert_to_timezone(
            text="12:00", source_tz="London", target_tz="Tokyo", now_iso=now_iso
        )

        assert res["source_timezone"] == "Europe/London"
        assert res["target_timezone"] == "Asia/Tokyo"

        # 12:00 London is 21:00 Tokyo
        assert "12:00:00" in res["source_start"]
        assert "21:00:00" in res["target_start"]
