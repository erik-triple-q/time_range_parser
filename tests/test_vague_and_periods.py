from __future__ import annotations

from datetime import datetime, timedelta
import pytest

from date_textparser.core import parse_time_range

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def now() -> datetime:
    """Vrijdag 2026-01-30 14:00:00"""
    return datetime(2026, 1, 30, 14, 0, 0)


@pytest.fixture
def now_sunday() -> datetime:
    """Zondag 2026-02-01 10:00:00"""
    return datetime(2026, 2, 1, 10, 0, 0)


def end_of_day(d: datetime) -> datetime:
    return datetime(d.year, d.month, d.day, 23, 59, 59)


def print_result(
    text: str, now: datetime, start: datetime, end: datetime, description: str = ""
):
    print(f"\n{'─' * 60}")
    print(f"Input:       '{text}'")
    print(f"Now:         {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})")
    print(
        f"Start:       {start.strftime('%Y-%m-%d %H:%M:%S')} ({start.strftime('%A')})"
    )
    print(f"End:         {end.strftime('%Y-%m-%d %H:%M:%S')} ({end.strftime('%A')})")
    duration = end - start
    print(f"Duration:    {duration}")
    if description:
        print(f"Description: {description}")
    print(f"{'─' * 60}")


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Vage tijdsaanduidingen (straks, vanavond, etc.)
# ─────────────────────────────────────────────────────────────────────────────


class TestVagueTimes:
    """Tests voor parsers/vague.py"""

    def test_straks(self, now: datetime):
        """'straks' -> +2 uur (default config)."""
        start, end = parse_time_range("straks", now=now)
        print_result("straks", now, start, end, "+2 uur")
        # Config: "straks": {"hours": 2, "type": "future"}
        expected_start = now + timedelta(hours=2)
        assert start == expected_start
        assert end == expected_start + timedelta(hours=1)

    def test_vanavond(self, now: datetime):
        """'vanavond' -> 20:00 vandaag."""
        start, end = parse_time_range("vanavond", now=now)
        print_result("vanavond", now, start, end, "20:00 vandaag")
        expected_start = datetime(2026, 1, 30, 20, 0, 0)
        assert start == expected_start

    def test_lunchtijd(self, now: datetime):
        """'lunchtijd' -> 12:30 vandaag."""
        start, end = parse_time_range("lunchtijd", now=now)
        print_result("lunchtijd", now, start, end, "12:30 vandaag")
        expected_start = datetime(2026, 1, 30, 12, 30, 0)
        assert start == expected_start

    def test_binnenkort(self, now: datetime):
        """'binnenkort' -> range van 7 dagen."""
        start, end = parse_time_range("binnenkort", now=now)
        print_result("binnenkort", now, start, end, "Range van 7 dagen")
        # Config: "binnenkort": {"days": 7, "type": "future_range"}
        # Start = begin van vandaag, End = over 7 dagen
        assert start == datetime(2026, 1, 30, 0, 0, 0)
        assert end == datetime(2026, 2, 6, 23, 59, 59)

    def test_zojuist(self, now: datetime):
        """'zojuist' -> 10 min geleden."""
        start, end = parse_time_range("zojuist", now=now)
        print_result("zojuist", now, start, end, "-10 minuten")
        expected_start = now - timedelta(minutes=10)
        assert start == expected_start


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Seizoenen
# ─────────────────────────────────────────────────────────────────────────────


class TestSeasons:
    """Tests voor parse_season in parsers/periods.py"""

    def test_zomer_2026(self, now: datetime):
        """'zomer 2026' -> juni t/m augustus."""
        start, end = parse_time_range("zomer 2026", now=now)
        print_result("zomer 2026", now, start, end, "Zomer 2026")
        assert start == datetime(2026, 6, 1, 0, 0, 0)
        assert end == datetime(2026, 8, 31, 23, 59, 59)

    def test_deze_winter(self, now: datetime):
        """'deze winter' (vanuit jan 2026) -> dec 2026 t/m feb 2027?
        Of dec 2025 t/m feb 2026?

        De logica in parse_season gebruikt now.year.
        Winter is (12, 2). Start > End, dus cross-year.
        Start = Dec 2026, End = Feb 2027.
        """
        start, end = parse_time_range("deze winter", now=now)
        print_result("deze winter", now, start, end, "Winter 2026/2027")
        assert start == datetime(2026, 12, 1, 0, 0, 0)
        assert end == datetime(2027, 2, 28, 23, 59, 59)

    def test_vorige_winter(self, now: datetime):
        """'vorige winter' -> dec 2025 t/m feb 2026."""
        start, end = parse_time_range("vorige winter", now=now)
        # Modifier 'vorige' -> year - 1 = 2025
        # Winter logic met modifier 'vorige': start dec 2025, end feb 2026
        print_result("vorige winter", now, start, end, "Winter 2025/2026")
        assert start == datetime(2025, 12, 1, 0, 0, 0)
        assert end == datetime(2026, 2, 28, 23, 59, 59)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Weeknummers
# ─────────────────────────────────────────────────────────────────────────────


class TestWeekNumbers:
    """Tests voor parse_week_number."""

    def test_week_42(self, now: datetime):
        """'week 42' -> ISO week 42 in 2026."""
        start, end = parse_time_range("week 42", now=now)
        print_result("week 42", now, start, end, "Week 42 2026")
        # Week 42 2026 begint op maandag 12 oktober 2026
        assert start == datetime(2026, 10, 12, 0, 0, 0)
        assert end == datetime(2026, 10, 18, 23, 59, 59)

    def test_week_1_2025(self, now: datetime):
        """'week 1 2025' -> expliciet jaar."""
        start, end = parse_time_range("week 1 2025", now=now)
        print_result("week 1 2025", now, start, end, "Week 1 2025")
        # Week 1 2025 begint op maandag 30 dec 2024 (ISO logica)
        assert start == datetime(2024, 12, 30, 0, 0, 0)
        assert end == datetime(2025, 1, 5, 23, 59, 59)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Half jaar (Semesters)
# ─────────────────────────────────────────────────────────────────────────────


class TestHalfYears:
    """Tests voor parse_half_year."""

    def test_h1_2026(self, now: datetime):
        """'H1' -> Jan t/m Jun."""
        start, end = parse_time_range("H1", now=now)
        print_result("H1", now, start, end, "Eerste helft 2026")
        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end == datetime(2026, 6, 30, 23, 59, 59)

    def test_tweede_helft_2025(self, now: datetime):
        """'tweede helft 2025' -> Jul t/m Dec."""
        start, end = parse_time_range("tweede helft 2025", now=now)
        print_result("tweede helft 2025", now, start, end, "Tweede helft 2025")
        assert start == datetime(2025, 7, 1, 0, 0, 0)
        assert end == datetime(2025, 12, 31, 23, 59, 59)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Weekends
# ─────────────────────────────────────────────────────────────────────────────


class TestWeekends:
    """Tests voor parse_weekend."""

    def test_dit_weekend_from_friday(self, now: datetime):
        """'dit weekend' vanuit vrijdag -> komende zaterdag/zondag."""
        # Now = Vrijdag 30 jan
        # Weekend = Zat 31 jan & Zon 1 feb
        start, end = parse_time_range("dit weekend", now=now)
        print_result("dit weekend", now, start, end, "Komend weekend (vanuit vrijdag)")
        assert start == datetime(2026, 1, 31, 0, 0, 0)
        assert end == datetime(2026, 2, 1, 23, 59, 59)

    def test_volgend_weekend(self, now: datetime):
        """'volgend weekend' -> weekend erop."""
        # Now = 30 jan. Dit weekend = 31 jan/1 feb.
        # Volgend weekend = 7 feb / 8 feb.
        start, end = parse_time_range("volgend weekend", now=now)
        print_result("volgend weekend", now, start, end, "Weekend erop")
        assert start == datetime(2026, 2, 7, 0, 0, 0)
        assert end == datetime(2026, 2, 8, 23, 59, 59)

    def test_weekend_from_sunday(self, now_sunday: datetime):
        """'weekend' vanuit zondag -> volgende zaterdag (niet vandaag)."""
        # Now = Zondag 1 feb.
        # Logic: if now.weekday() > 5 (Sunday is 6), add week.
        # Next saturday = 7 feb.
        start, end = parse_time_range("weekend", now=now_sunday)
        print_result(
            "weekend", now_sunday, start, end, "Weekend vanuit zondag (volgende week)"
        )
        assert start == datetime(2026, 2, 7, 0, 0, 0)

    def test_dit_weekend_from_sunday(self, now_sunday: datetime):
        """'dit weekend' vanuit zondag -> gisteren en vandaag."""
        # Now = Zondag 1 feb.
        # Dit weekend = Zat 31 jan & Zon 1 feb.
        start, end = parse_time_range("dit weekend", now=now_sunday)
        print_result(
            "dit weekend",
            now_sunday,
            start,
            end,
            "Dit weekend vanuit zondag (gisteren/vandaag)",
        )
        assert start == datetime(2026, 1, 31, 0, 0, 0)
        assert end == datetime(2026, 2, 1, 23, 59, 59)
