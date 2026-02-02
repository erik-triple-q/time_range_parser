import pytest
from datetime import datetime

from date_textparser import parse_time_range


class TestMovingHolidays:
    """Tests voor bewegende feestdagen."""

    @pytest.fixture
    def now(self):
        return datetime(2026, 1, 30, 10, 0, 0)

    def test_pasen_2026(self, now):
        """Pasen 2026 = 5 april."""
        start, end = parse_time_range("pasen", now=now)
        assert start == datetime(2026, 4, 5, 0, 0, 0)
        assert end == datetime(2026, 4, 5, 23, 59, 59)

    def test_pasen_with_year(self, now):
        start, end = parse_time_range("pasen 2027", now=now)
        assert start == datetime(2027, 3, 28, 0, 0, 0)
        assert end == datetime(2027, 3, 28, 23, 59, 59)

    def test_goede_vrijdag(self, now):
        """Goede vrijdag = 2 dagen voor Pasen."""
        start, end = parse_time_range("goede vrijdag", now=now)
        assert start == datetime(2026, 4, 3, 0, 0, 0)
        assert end == datetime(2026, 4, 3, 23, 59, 59)

    def test_hemelvaartsdag(self, now):
        """Hemelvaart = 39 dagen na Pasen."""
        start, end = parse_time_range("hemelvaartsdag", now=now)
        assert start == datetime(2026, 5, 14, 0, 0, 0)
        assert end == datetime(2026, 5, 14, 23, 59, 59)

    def test_pinksteren(self, now):
        """Pinksteren = 49 dagen na Pasen."""
        start, end = parse_time_range("pinksteren", now=now)
        assert start == datetime(2026, 5, 24, 0, 0, 0)
        assert end == datetime(2026, 5, 24, 23, 59, 59)

    def test_tweede_paasdag(self, now):
        start, end = parse_time_range("tweede paasdag", now=now)
        assert start == datetime(2026, 4, 6, 0, 0, 0)
        assert end == datetime(2026, 4, 6, 23, 59, 59)

    def test_carnaval(self, now):
        """Carnaval = 49 dagen voor Pasen."""
        start, end = parse_time_range("carnaval", now=now)
        assert start == datetime(2026, 2, 15, 0, 0, 0)
        assert end == datetime(2026, 2, 15, 23, 59, 59)

    def test_easter_english(self, now):
        start, end = parse_time_range("easter 2026", now=now)
        assert start == datetime(2026, 4, 5, 0, 0, 0)
        assert end == datetime(2026, 4, 5, 23, 59, 59)

    def test_ascension_day(self, now):
        start, end = parse_time_range("ascension day", now=now)
        assert start == datetime(2026, 5, 14, 0, 0, 0)
        assert end == datetime(2026, 5, 14, 23, 59, 59)


class TestOrdinalWeekdaysExtended:
    """Extended tests voor ordinale weekdagen."""

    @pytest.fixture
    def now(self):
        return datetime(2026, 1, 30, 10, 0, 0)

    def test_eerste_maandag_van_maart(self, now):
        start, end = parse_time_range("eerste maandag van maart", now=now)
        assert start == datetime(2026, 3, 2, 0, 0, 0)
        assert end == datetime(2026, 3, 2, 23, 59, 59)

    def test_laatste_vrijdag_van_de_maand(self, now):
        start, end = parse_time_range("laatste vrijdag van de maand", now=now)
        assert start == datetime(2026, 1, 30, 0, 0, 0)
        assert end == datetime(2026, 1, 30, 23, 59, 59)

    def test_tweede_dinsdag_van_februari(self, now):
        start, end = parse_time_range("tweede dinsdag van februari", now=now)
        assert start == datetime(2026, 2, 10, 0, 0, 0)
        assert end == datetime(2026, 2, 10, 23, 59, 59)

    def test_derde_woensdag(self, now):
        """Derde woensdag zonder maand -> huidige maand."""
        start, end = parse_time_range("derde woensdag", now=now)
        # Januari 2026: 3e woensdag = 21 jan (verleden), dus februari = 18 feb
        assert start == datetime(2026, 2, 18, 0, 0, 0)
        assert end == datetime(2026, 2, 18, 23, 59, 59)

    def test_first_monday_of_march(self, now):
        start, end = parse_time_range("first monday of march", now=now)
        assert start == datetime(2026, 3, 2, 0, 0, 0)
        assert end == datetime(2026, 3, 2, 23, 59, 59)

    def test_last_friday_of_the_month(self, now):
        start, end = parse_time_range("last friday of the month", now=now)
        assert start == datetime(2026, 1, 30, 0, 0, 0)
        assert end == datetime(2026, 1, 30, 23, 59, 59)