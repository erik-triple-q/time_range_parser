from __future__ import annotations

import pytest
from date_textparser.core import calculate_duration


class TestCalculateDuration:
    @pytest.fixture
    def now_iso(self):
        # Vrijdag 30 januari 2026, 12:00
        return "2026-01-30T12:00:00+01:00"

    def test_days_until_next_week(self, now_iso):
        """Vrijdag tot volgende week vrijdag = 7 dagen."""
        result = calculate_duration(
            start_text="vandaag", end_text="volgende vrijdag", now_iso=now_iso
        )

        dur = result["duration"]
        assert dur["total_days"] == 7.0
        assert "1 week" in dur["human_readable"]

    def test_business_days_over_weekend(self, now_iso):
        """
        Vrijdag (30 jan) tot Dinsdag (3 feb).
        Dagen: Vr->Za(1), Za->Zo(2), Zo->Ma(3), Ma->Di(4). Totaal 4 dagen.
        Werkdagen: Vr (1), Za (0), Zo (0), Ma (1). Totaal 2 werkdagen.
        """
        result = calculate_duration(
            start_text="vandaag", end_text="dinsdag", now_iso=now_iso
        )

        dur = result["duration"]
        assert dur["total_days"] == 4.0
        assert dur["business_days"] == 2

    def test_negative_duration(self, now_iso):
        """Vandaag tot gisteren."""
        result = calculate_duration(
            start_text="vandaag", end_text="gisteren", now_iso=now_iso
        )

        dur = result["duration"]
        assert dur["total_days"] == -1.0
        assert dur["business_days"] == -1

    def test_hours_diff(self, now_iso):
        # Use times strictly in the future relative to now (12:00) to avoid day shifts
        result = calculate_duration("13:00", "16:30", now_iso=now_iso)
        dur = result["duration"]
        assert dur["total_seconds"] == 3.5 * 3600
