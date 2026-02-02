from datetime import datetime, timedelta
import pytest

from date_textparser.core import parse_time_range, expand_recurrence


@pytest.fixture
def now():
    # Maandag 26 januari 2026, 09:00
    return datetime(2026, 1, 26, 9, 0, 0)


class TestCompoundDays:
    """Tests voor samengestelde dagen (src/date_textparser/parsers/weekdays.py)."""

    def test_morgenochtend(self, now):
        # Morgen = dinsdag 27 jan. Ochtend = 06:00 - 12:00
        s, e = parse_time_range("morgenochtend", now=now)
        assert s.day == 27
        assert s.hour == 6
        assert e.hour == 11
        assert e.minute == 59

    def test_gisterenavond(self, now):
        # Gisteren = zondag 25 jan. Avond = 18:00 - 23:00
        s, e = parse_time_range("gisterenavond", now=now)
        assert s.day == 25
        assert s.hour == 18
        assert e.hour == 22

    def test_vrijdagnacht(self, now):
        # Vrijdag = 30 jan. Nacht = 23:00 - 06:00 (volgende dag)
        s, e = parse_time_range("vrijdagnacht", now=now)
        assert s.day == 30
        assert s.hour == 23
        assert e.day == 31
        assert e.hour == 5

    def test_overmorgen_middag(self, now):
        # Overmorgen = woensdag 28 jan. Middag = 12:00 - 18:00
        s, e = parse_time_range("overmorgenmiddag", now=now)
        assert s.day == 28
        assert s.hour == 12
        assert e.hour == 17


class TestVagueTimes:
    """Tests voor vage tijdsaanduidingen (src/date_textparser/parsers/vague.py)."""

    def test_binnenkort(self, now):
        # future_range, 7 dagen
        s, e = parse_time_range("binnenkort", now=now)
        assert s.date() == now.date()
        assert (e - s).days >= 6

    def test_onlangs(self, now):
        # past_range
        s, e = parse_time_range("onlangs", now=now)
        assert s < now
        assert e <= end_of_day(now)

    def test_deze_dagen(self, now):
        # current_range
        s, e = parse_time_range("deze dagen", now=now)
        # Zou rond 'now' moeten liggen
        assert s <= now <= e

    def test_vroeg_laat(self, now):
        # time_of_day
        s_vroeg, _ = parse_time_range("vroeg", now=now)
        assert s_vroeg.hour == 7

        s_laat, _ = parse_time_range("laat", now=now)
        assert s_laat.hour == 22


class TestMonthModifiers:
    """Tests voor maand modifiers (src/date_textparser/parsers/periods.py)."""

    def test_begin_januari(self, now):
        s, e = parse_time_range("begin januari 2026", now=now)
        assert s.day == 1
        assert e.day == 10

    def test_eind_januari(self, now):
        s, e = parse_time_range("eind januari 2026", now=now)
        # Eind is laatste 9-10 dagen
        assert s.day > 20
        assert e.day == 31

    def test_medio_januari(self, now):
        s, e = parse_time_range("medio januari 2026", now=now)
        assert s.day == 11
        assert e.day == 20


class TestRecurrenceAndDuration:
    """Tests voor recurrence en lange duraties (base.py & dateparser.py)."""

    def test_recurrence_keywords(self, now):
        # Test de NL keywords die in expand_recurrence zitten
        r = expand_recurrence("dagelijks", now_iso=now.isoformat())
        assert r["rule"]["unit"] == "days"

        r = expand_recurrence("wekelijks", now_iso=now.isoformat())
        assert r["rule"]["unit"] == "weeks"

        r = expand_recurrence("maandelijks", now_iso=now.isoformat())
        assert r["rule"]["unit"] == "months"

        r = expand_recurrence("jaarlijks", now_iso=now.isoformat())
        assert r["rule"]["unit"] == "years"

    def test_long_durations(self, now):
        # Test 'maanden' en 'jaren' in parse_duration (base.py)
        # "vandaag 3 maanden" -> start vandaag, duur 3 maanden
        s, e = parse_time_range("vandaag 3 maanden", now=now)
        assert (e.year * 12 + e.month) - (s.year * 12 + s.month) == 3

        s, e = parse_time_range("vandaag 1 jaar", now=now)
        assert e.year == s.year + 1


def end_of_day(dt):
    return dt.replace(hour=23, minute=59, second=59, microsecond=0)
