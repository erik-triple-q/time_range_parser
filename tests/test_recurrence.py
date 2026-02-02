from __future__ import annotations

import pytest
from date_textparser.core import expand_recurrence


class TestExpandRecurrence:
    @pytest.fixture
    def now_iso(self):
        # Vrijdag 30 januari 2026, 12:00
        return "2026-01-30T12:00:00+01:00"

    def test_every_friday_starts_today(self, now_iso):
        """Als het vandaag vrijdag is, moet de reeks vandaag beginnen."""
        result = expand_recurrence("elke vrijdag", now_iso=now_iso, count=3)
        dates = result["dates"]

        assert len(dates) == 3
        assert "2026-01-30" in dates[0]  # Vandaag (vrijdag)
        assert "2026-02-06" in dates[1]  # Volgende week
        assert "2026-02-13" in dates[2]

        assert result["rule"]["unit"] == "weeks"
        assert result["rule"]["weekday"] == 4  # Vrijdag = 4

    def test_every_monday_starts_next_week(self, now_iso):
        """Als het vandaag vrijdag is, moet 'elke maandag' volgende week beginnen."""
        result = expand_recurrence("elke maandag", now_iso=now_iso, count=2)
        dates = result["dates"]

        assert "2026-02-02" in dates[0]  # Maandag 2 feb
        assert "2026-02-09" in dates[1]

    def test_daily_recurrence(self, now_iso):
        result = expand_recurrence("dagelijks", now_iso=now_iso, count=3)
        dates = result["dates"]

        assert "2026-01-30" in dates[0]
        assert "2026-01-31" in dates[1]
        assert "2026-02-01" in dates[2]
        assert result["rule"]["unit"] == "days"

    def test_interval_parsing(self, now_iso):
        """Test 'elke 2 weken'."""
        result = expand_recurrence("elke 2 weken", now_iso=now_iso, count=3)
        dates = result["dates"]

        assert "2026-01-30" in dates[0]
        assert "2026-02-13" in dates[1]  # +14 dagen
        assert result["rule"]["interval"] == 2
        assert result["rule"]["unit"] == "weeks"

    def test_monthly_recurrence(self, now_iso):
        """Test 'maandelijks'."""
        result = expand_recurrence("maandelijks", now_iso=now_iso, count=2)
        dates = result["dates"]

        assert "2026-01-30" in dates[0]
        # Pendulum/datetime behavior: Jan 30 + 1 month -> Feb 28 (non-leap) or Mar 2?
        # We checken alleen of de maand correct is opgehoogd.
        assert "2026-02" in dates[1]
        assert result["rule"]["unit"] == "months"

    def test_timezone_conversion_implicit(self):
        """
        Als input 'daily' is met timezone 'New York', en now_iso is in Amsterdam (12:00),
        dan moet de output in New York tijd zijn (06:00).
        """
        ams_noon = "2026-01-30T12:00:00+01:00"
        result = expand_recurrence("daily", tz="New York", now_iso=ams_noon, count=1)

        first_date = result["dates"][0]
        # 12:00 AMS = 06:00 EST
        assert "06:00:00" in first_date
        assert "-05:00" in first_date  # EST offset

    def test_unknown_pattern_raises_error(self):
        with pytest.raises(ValueError, match="Kon geen herhalingspatroon herkennen"):
            expand_recurrence("hallo wereld")
