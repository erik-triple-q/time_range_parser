from __future__ import annotations

from datetime import datetime, timedelta
import pytest

from date_textparser.core import parse_time_range

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def now() -> datetime:
    """Maandag 2026-01-26 09:00 - maakt weekdag-tests ondubbelzinnig."""
    dt = datetime(2026, 1, 26, 9, 0, 0)
    print(f"\n🕒 Fixture 'now': {dt}")
    return dt


@pytest.fixture
def now_friday() -> datetime:
    """Vrijdag 2026-01-30 14:00 - voor weekend-gerelateerde tests."""
    dt = datetime(2026, 1, 30, 14, 0, 0)
    print(f"\n🕒 Fixture 'now_friday': {dt}")
    return dt


@pytest.fixture
def now_december() -> datetime:
    """December 2025 - voor jaar-overgang tests."""
    dt = datetime(2025, 12, 15, 10, 0, 0)
    print(f"\n🕒 Fixture 'now_december': {dt}")
    return dt


@pytest.fixture
def now_end_of_year() -> datetime:
    """31 december 2025 - voor jaarwisseling tests."""
    dt = datetime(2025, 12, 31, 10, 0, 0)
    print(f"\n🕒 Fixture 'now_end_of_year': {dt}")
    return dt


@pytest.fixture
def now_january() -> datetime:
    """Januari 2026 - voor vorige maand/jaar tests."""
    dt = datetime(2026, 1, 15, 10, 0, 0)
    print(f"\n🕒 Fixture 'now_january': {dt}")
    return dt


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────


def end_of_day(d: datetime) -> datetime:
    """Retourneert 23:59:59 van de gegeven dag (seconds-only)."""
    return datetime(d.year, d.month, d.day, 23, 59, 59)


def start_of_day(d: datetime) -> datetime:
    """Retourneert 00:00:00 van de gegeven dag."""
    return datetime(d.year, d.month, d.day, 0, 0, 0)


def print_result(
    text: str, now: datetime, start: datetime, end: datetime, description: str = ""
):
    """Print test resultaat naar console voor debugging."""
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
# Tests: Relatieve dagen (morgen, overmorgen, gisteren)
# ─────────────────────────────────────────────────────────────────────────────


class TestRelativeDays:
    """Tests voor relatieve dag-aanduidingen."""

    def test_morgen_is_full_day(self, now: datetime):
        """'morgen' zonder tijd -> hele dag."""
        start, end = parse_time_range("morgen", now=now)

        tomorrow = (now + timedelta(days=1)).date()
        expected_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)

        print_result("morgen", now, start, end, "Hele dag morgen verwacht")

        assert start == expected_start
        assert end == end_of_day(start)
        assert end < start + timedelta(days=1)

    def test_overmorgen_is_full_day(self, now: datetime):
        """'overmorgen' -> dag na morgen, hele dag."""
        start, end = parse_time_range("overmorgen", now=now)

        day_after = (now + timedelta(days=2)).date()
        expected_start = datetime(
            day_after.year, day_after.month, day_after.day, 0, 0, 0
        )

        print_result("overmorgen", now, start, end, "Hele dag overmorgen verwacht")

        assert start == expected_start
        assert end == end_of_day(start)

    def test_gisteren_is_full_day(self, now: datetime):
        """'gisteren' -> vorige dag, hele dag."""
        start, end = parse_time_range("gisteren", now=now)

        yesterday = (now - timedelta(days=1)).date()
        expected_start = datetime(
            yesterday.year, yesterday.month, yesterday.day, 0, 0, 0
        )

        print_result("gisteren", now, start, end, "Hele dag gisteren verwacht")

        assert start == expected_start
        assert end == end_of_day(start)

    def test_vandaag_is_full_day(self, now: datetime):
        """'vandaag' -> huidige dag, hele dag."""
        start, end = parse_time_range("vandaag", now=now)

        today = now.date()
        expected_start = datetime(today.year, today.month, today.day, 0, 0, 0)

        print_result("vandaag", now, start, end, "Hele dag vandaag verwacht")

        assert start == expected_start
        assert end == end_of_day(start)

    def test_eergisteren_is_full_day(self, now: datetime):
        """'eergisteren' -> twee dagen geleden."""
        start, end = parse_time_range("eergisteren", now=now)

        day_before_yesterday = (now - timedelta(days=2)).date()
        expected_start = datetime(
            day_before_yesterday.year,
            day_before_yesterday.month,
            day_before_yesterday.day,
            0,
            0,
            0,
        )

        print_result("eergisteren", now, start, end, "Hele dag eergisteren verwacht")

        assert start == expected_start
        assert end == end_of_day(start)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Relatieve dagen met tijd
# ─────────────────────────────────────────────────────────────────────────────


class TestRelativeDaysWithTime:
    """Tests voor relatieve dagen met specifieke tijd."""

    def test_morgen_15_00_default_60_minutes(self, now: datetime):
        """'morgen 15:00' met default 60 min -> 15:00-16:00."""
        start, end = parse_time_range("morgen 15:00", now=now, default_minutes=60)

        tomorrow = (now + timedelta(days=1)).date()
        expected_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 15, 0, 0)

        print_result("morgen 15:00", now, start, end, "60 minuten event verwacht")

        assert start == expected_start
        assert end == expected_start + timedelta(minutes=60)

    def test_morgen_om_15_00(self, now: datetime):
        """'morgen om 15:00' -> met voorzetsel 'om'."""
        start, end = parse_time_range("morgen om 15:00", now=now, default_minutes=60)

        tomorrow = (now + timedelta(days=1)).date()
        expected_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 15, 0, 0)

        print_result("morgen om 15:00", now, start, end, "Met voorzetsel 'om'")

        assert start == expected_start
        assert end == expected_start + timedelta(minutes=60)

    def test_morgen_9_uur_default_30_minutes(self, now: datetime):
        """'morgen 9 uur' met default 30 min."""
        start, end = parse_time_range("morgen 9 uur", now=now, default_minutes=30)

        tomorrow = (now + timedelta(days=1)).date()
        expected_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9, 0, 0)

        print_result("morgen 9 uur", now, start, end, "30 minuten event verwacht")

        assert start == expected_start
        assert end == expected_start + timedelta(minutes=30)

    def test_vandaag_14_30(self, now: datetime):
        """'vandaag 14:30' -> specifieke tijd vandaag."""
        start, end = parse_time_range("vandaag 14:30", now=now, default_minutes=60)

        today = now.date()
        expected_start = datetime(today.year, today.month, today.day, 14, 30, 0)

        print_result("vandaag 14:30", now, start, end, "60 minuten event verwacht")

        assert start == expected_start
        assert end == expected_start + timedelta(minutes=60)

    def test_overmorgen_10_00(self, now: datetime):
        """'overmorgen 10:00' -> specifieke tijd overmorgen."""
        start, end = parse_time_range("overmorgen 10:00", now=now, default_minutes=45)

        day_after = (now + timedelta(days=2)).date()
        expected_start = datetime(
            day_after.year, day_after.month, day_after.day, 10, 0, 0
        )

        print_result("overmorgen 10:00", now, start, end, "45 minuten event verwacht")

        assert start == expected_start
        assert end == expected_start + timedelta(minutes=45)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Expliciete tijdranges
# ─────────────────────────────────────────────────────────────────────────────


class TestExplicitTimeRanges:
    """Tests voor expliciete tijd-ranges (van X tot Y)."""

    def test_van_10_00_tot_12_30(self, now: datetime):
        """'van 10:00 tot 12:30' -> exacte tijden."""
        start, end = parse_time_range("van 10:00 tot 12:30", now=now)

        today = now.date()
        expected_start = datetime(today.year, today.month, today.day, 10, 0, 0)
        expected_end = datetime(today.year, today.month, today.day, 12, 30, 0)

        print_result(
            "van 10:00 tot 12:30", now, start, end, "Exacte tijd range verwacht"
        )

        assert start == expected_start
        assert end == expected_end

    def test_van_9_tot_17_uur(self, now: datetime):
        """'van 9 tot 17 uur' -> werkdag."""
        start, end = parse_time_range("van 9 tot 17 uur", now=now)

        today = now.date()
        expected_start = datetime(today.year, today.month, today.day, 9, 0, 0)
        expected_end = datetime(today.year, today.month, today.day, 17, 0, 0)

        print_result("van 9 tot 17 uur", now, start, end, "Werkdag 9-17 verwacht")

        assert start == expected_start
        assert end == expected_end

    def test_tussen_14_00_en_15_30(self, now: datetime):
        """'tussen 14:00 en 15:30' -> alternatieve syntax."""
        start, end = parse_time_range("tussen 14:00 en 15:30", now=now)

        today = now.date()
        expected_start = datetime(today.year, today.month, today.day, 14, 0, 0)
        expected_end = datetime(today.year, today.month, today.day, 15, 30, 0)

        print_result(
            "tussen 14:00 en 15:30", now, start, end, "Tijd range met 'tussen...en'"
        )

        assert start == expected_start
        assert end == expected_end

    def test_from_10_to_12(self, now: datetime):
        """'from 10:00 to 12:00' -> Engelse syntax."""
        start, end = parse_time_range("from 10:00 to 12:00", now=now)

        today = now.date()
        expected_start = datetime(today.year, today.month, today.day, 10, 0, 0)
        expected_end = datetime(today.year, today.month, today.day, 12, 0, 0)

        print_result("from 10:00 to 12:00", now, start, end, "Engels formaat")

        assert start == expected_start
        assert end == expected_end

    def test_van_8_tot_12(self, now: datetime):
        """'van 8 tot 12' -> zonder 'uur' keyword."""
        start, end = parse_time_range("van 8 tot 12", now=now)

        today = now.date()
        expected_start = datetime(today.year, today.month, today.day, 8, 0, 0)
        expected_end = datetime(today.year, today.month, today.day, 12, 0, 0)

        print_result("van 8 tot 12", now, start, end, "Zonder 'uur' keyword")

        assert start == expected_start
        assert end == expected_end

    # def test_swap_start_end_chronological(self):
    #     """
    #     Test dat start en end worden omgewisseld als start > end.
    #     Specifiek scenario: "van 5 mei tot 1 mei".
    #     """
    #     now = datetime(2026, 1, 1, 12, 0, 0)

    #     start, end = parse_time_range("van 5 mei tot 1 mei", now=now)

    #     print_result("van 5 mei tot 1 mei", now, start, end, "Swap check")

    #     # Verifieer dat start <= end (chronologisch)
    #     assert start <= end

    #     # Start moet 1 mei zijn
    #     assert start.month == 5
    #     assert start.day == 1
    #     # End moet 5 mei zijn
    #     assert end.month == 5
    #     assert end.day == 5

    def test_suffix_context_alignment(self):
        """
        Test dat 'tussen 1 en 2 gisteren' correct wordt uitgelijnd naar gisteren.
        """
        now = datetime(2026, 1, 1, 12, 0, 0)  # 1 jan
        start, end = parse_time_range("tussen 1 en 2 gisteren", now=now)

        # Beide moeten op 31 dec 2025 (gisteren) vallen
        assert start.year == 2025 and start.month == 12 and start.day == 31
        assert end.year == 2025 and end.month == 12 and end.day == 31

        # Tijd moet 01:00 - 02:00 zijn
        assert start.hour == 1
        assert end.day == 31
        assert end.hour == 2

    def test_gisteren_tussen_1_en_2(self, now: datetime):
        """'gisteren tussen 1 en 2' -> gisteren 01:00 - 02:00 (context prefix)."""
        # now = Maandag 26 jan 2026
        # gisteren = Zondag 25 jan
        start, end = parse_time_range("gisteren tussen 1 en 2", now=now)

        expected_start = datetime(2026, 1, 25, 1, 0, 0)
        expected_end = datetime(2026, 1, 25, 2, 0, 0)

        print_result("gisteren tussen 1 en 2", now, start, end, "Context prefix test")

        assert start == expected_start
        assert end == expected_end


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Weekdagen
# ─────────────────────────────────────────────────────────────────────────────


class TestWeekdays:
    """Tests voor weekdag-aanduidingen."""

    def test_tussen_maandag_en_woensdag(self, now: datetime):
        """'tussen maandag en woensdag' vanuit maandag -> deze week."""
        start, end = parse_time_range("tussen maandag en woensdag", now=now)

        print_result(
            "tussen maandag en woensdag",
            now,
            start,
            end,
            "Ma-wo range, start ma 00:00, end wo 23:59:59",
        )

        assert start == datetime(2026, 1, 26, 0, 0, 0)  # maandag 00:00
        assert end == datetime(2026, 1, 28, 23, 59, 59)  # woensdag 23:59:59

    def test_vrijdag(self, now: datetime):
        """'vrijdag' -> komende vrijdag, hele dag."""
        start, end = parse_time_range("vrijdag", now=now)

        print_result("vrijdag", now, start, end, "Komende vrijdag (30 jan) verwacht")

        # now = maandag 26 jan, vrijdag = 30 jan
        assert start == datetime(2026, 1, 30, 0, 0, 0)
        assert end == end_of_day(start)

    def test_volgende_dinsdag(self, now: datetime):
        """'volgende dinsdag' -> dinsdag volgende week."""
        start, end = parse_time_range("volgende dinsdag", now=now)

        print_result(
            "volgende dinsdag", now, start, end, "Volgende week dinsdag verwacht"
        )

        # now = maandag 26 jan, volgende dinsdag = 3 feb
        assert start == datetime(2026, 2, 3, 0, 0, 0)
        assert end == end_of_day(start)

    def test_woensdag_10_uur(self, now: datetime):
        """'woensdag 10 uur' -> specifieke tijd op woensdag."""
        start, end = parse_time_range("woensdag 10 uur", now=now, default_minutes=60)

        print_result("woensdag 10 uur", now, start, end, "Woensdag 10:00, 60 min event")

        # now = maandag 26 jan, woensdag = 28 jan
        assert start == datetime(2026, 1, 28, 10, 0, 0)
        assert end == datetime(2026, 1, 28, 11, 0, 0)

    def test_vorige_vrijdag(self, now: datetime):
        """'vorige vrijdag' -> vrijdag vorige week."""
        start, end = parse_time_range("vorige vrijdag", now=now)

        print_result("vorige vrijdag", now, start, end, "Vorige week vrijdag verwacht")

        # now = maandag 26 jan, vorige vrijdag = 23 jan
        assert start == datetime(2026, 1, 23, 0, 0, 0)
        assert end == end_of_day(start)

    def test_afgelopen_woensdag(self, now: datetime):
        """'afgelopen woensdag' -> woensdag vorige week."""
        start, end = parse_time_range("afgelopen woensdag", now=now)

        print_result(
            "afgelopen woensdag", now, start, end, "Afgelopen woensdag verwacht"
        )

        # now = maandag 26 jan, afgelopen woensdag = 21 jan
        assert start == datetime(2026, 1, 21, 0, 0, 0)
        assert end == end_of_day(start)

    def test_komende_donderdag(self, now: datetime):
        """'komende donderdag' -> donderdag volgende week."""
        start, end = parse_time_range("komende donderdag", now=now)

        print_result("komende donderdag", now, start, end, "Komende donderdag verwacht")

        # now = maandag 26 jan, komende donderdag = 5 feb (volgende week)
        assert start == datetime(2026, 2, 5, 0, 0, 0)
        assert end == end_of_day(start)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Week/Maand/Jaar periodes
# ─────────────────────────────────────────────────────────────────────────────


class TestPeriods:
    """Tests voor periode-aanduidingen (week, maand, jaar)."""

    def test_volgende_week(self, now: datetime):
        """'volgende week' -> ma t/m zo volgende week."""
        start, end = parse_time_range("volgende week", now=now)

        print_result("volgende week", now, start, end, "Week 2-8 feb verwacht (ma-zo)")

        assert start == datetime(2026, 2, 2, 0, 0, 0)
        assert end == datetime(2026, 2, 8, 23, 59, 59)

    def test_deze_week(self, now: datetime):
        """'deze week' -> huidige week ma t/m zo."""
        start, end = parse_time_range("deze week", now=now)

        print_result("deze week", now, start, end, "Week 26 jan - 1 feb verwacht")

        assert start == datetime(2026, 1, 26, 0, 0, 0)  # maandag
        assert end == datetime(2026, 2, 1, 23, 59, 59)  # zondag

    def test_volgende_maand(self, now: datetime):
        """'volgende maand' -> hele februari."""
        start, end = parse_time_range("volgende maand", now=now)

        print_result("volgende maand", now, start, end, "Februari 2026 verwacht")

        assert start == datetime(2026, 2, 1, 0, 0, 0)
        assert end == datetime(2026, 2, 28, 23, 59, 59)

    def test_deze_maand(self, now: datetime):
        """'deze maand' -> hele januari."""
        start, end = parse_time_range("deze maand", now=now)

        print_result("deze maand", now, start, end, "Januari 2026 verwacht")

        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end == datetime(2026, 1, 31, 23, 59, 59)

    def test_vorige_maand(self, now_january: datetime):
        """'vorige maand' in januari -> december vorig jaar."""
        start, end = parse_time_range("vorige maand", now=now_january)

        print_result("vorige maand", now_january, start, end, "December 2025 verwacht")

        assert start == datetime(2025, 12, 1, 0, 0, 0)
        assert end == datetime(2025, 12, 31, 23, 59, 59)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: ISO datums en datums in zinnen
# ─────────────────────────────────────────────────────────────────────────────


class TestISODates:
    """Tests voor ISO datum formaat en datums in langere tekst."""

    def test_iso_date_standalone(self, now: datetime):
        """'2025-11-01' -> hele dag."""
        start, end = parse_time_range("2025-11-01", now=now)

        print_result("2025-11-01", now, start, end, "1 november 2025, hele dag")

        assert start == datetime(2025, 11, 1, 0, 0, 0)
        assert end == end_of_day(start)

    def test_iso_date_in_sentence(self, now: datetime):
        """'wat is het maximum op 2025-11-01?' -> datum extraheren uit zin."""
        start, end = parse_time_range("wat is het maximum op 2025-11-01?", now=now)

        print_result(
            "wat is het maximum op 2025-11-01?",
            now,
            start,
            end,
            "Datum uit zin geëxtraheerd",
        )

        assert start == datetime(2025, 11, 1, 0, 0, 0)
        assert end == end_of_day(start)

    def test_date_with_query_prefix(self, now: datetime):
        """'statistieken voor 2025-12-25' -> kerstdag."""
        start, end = parse_time_range("statistieken voor 2025-12-25", now=now)

        print_result("statistieken voor 2025-12-25", now, start, end, "Kerstdag 2025")

        assert start == datetime(2025, 12, 25, 0, 0, 0)
        assert end == end_of_day(start)

    def test_eu_date_format(self, now: datetime):
        """'15-03-2026' -> EU formaat (dd-mm-yyyy)."""
        start, end = parse_time_range("15-03-2026", now=now)

        print_result("15-03-2026", now, start, end, "15 maart 2026, EU formaat")

        assert start == datetime(2026, 3, 15, 0, 0, 0)
        assert end == end_of_day(start)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Nederlandse maandnamen
# ─────────────────────────────────────────────────────────────────────────────


class TestDutchMonthNames:
    """Tests voor Nederlandse maand- en datumnotatie."""

    def test_vijf_januari(self, now: datetime):
        """'5 januari' -> 5 jan komend jaar indien nodig."""
        start, end = parse_time_range("5 januari 2026", now=now)

        print_result("5 januari 2026", now, start, end, "5 januari 2026")

        assert start == datetime(2026, 1, 5, 0, 0, 0)
        assert end == end_of_day(start)

    def test_eerste_februari(self, now: datetime):
        """'1 februari' -> volgende maand."""
        start, end = parse_time_range("1 februari", now=now)

        print_result("1 februari", now, start, end, "1 februari 2026")

        assert start == datetime(2026, 2, 1, 0, 0, 0)
        assert end == end_of_day(start)

    def test_op_15_maart(self, now: datetime):
        """'op 15 maart' -> met voorzetsel."""
        start, end = parse_time_range("op 15 maart", now=now)

        print_result("op 15 maart", now, start, end, "15 maart 2026")

        assert start == datetime(2026, 3, 15, 0, 0, 0)
        assert end == end_of_day(start)

    def test_abbreviated_month(self, now: datetime):
        """'5 jan' -> afgekorte maand."""
        start, end = parse_time_range("5 jan 2026", now=now)

        print_result("5 jan 2026", now, start, end, "5 januari 2026 (afkorting)")

        assert start == datetime(2026, 1, 5, 0, 0, 0)
        assert end == end_of_day(start)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Duur-aanduidingen
# ─────────────────────────────────────────────────────────────────────────────


class TestDurations:
    """Tests voor expliciete duur-aanduidingen."""

    def test_morgen_2_uur(self, now: datetime):
        """'morgen 2 uur' -> morgen om 2 uur OF 2 uur duratie?

        Dit is ambigu - we verwachten hier '2 uur' als tijd (02:00).
        """
        start, end = parse_time_range("morgen 2 uur", now=now, default_minutes=60)

        tomorrow = (now + timedelta(days=1)).date()

        print_result(
            "morgen 2 uur", now, start, end, "'2 uur' geïnterpreteerd als tijd 02:00"
        )

        assert start.date() == tomorrow

    def test_meeting_30_minuten(self, now: datetime):
        """'meeting morgen 30 minuten' -> duratie."""
        start, end = parse_time_range("morgen 30 minuten", now=now)

        print_result("morgen 30 minuten", now, start, end, "30 minuten duratie")

        assert (end - start) == timedelta(minutes=30)

    def test_3_dagen(self, now: datetime):
        """'3 dagen' vanaf nu."""
        start, end = parse_time_range("3 dagen", now=now)

        print_result("3 dagen", now, start, end, "3 dagen duratie vanaf nu")

        assert (end - start) == timedelta(days=3)

    def test_2_weken(self, now: datetime):
        """'2 weken' vanaf nu."""
        start, end = parse_time_range("2 weken", now=now)

        print_result("2 weken", now, start, end, "2 weken duratie vanaf nu")

        assert (end - start) == timedelta(weeks=2)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Middernacht / dag-overschrijding
# ─────────────────────────────────────────────────────────────────────────────


class TestMidnightCrossing:
    """Tests voor tijden die middernacht overschrijden."""

    def test_van_22_tot_02(self, now: datetime):
        """'van 22:00 tot 02:00' -> over middernacht."""
        start, end = parse_time_range("van 22:00 tot 02:00", now=now)

        print_result(
            "van 22:00 tot 02:00", now, start, end, "Nachtshift, over middernacht"
        )

        today = now.date()
        tomorrow = (now + timedelta(days=1)).date()

        assert start == datetime(today.year, today.month, today.day, 22, 0, 0)
        assert end == datetime(tomorrow.year, tomorrow.month, tomorrow.day, 2, 0, 0)

    def test_van_23_tot_01(self, now: datetime):
        """'van 23:00 tot 01:00' -> korte nachtperiode."""
        start, end = parse_time_range("van 23:00 tot 01:00", now=now)

        print_result(
            "van 23:00 tot 01:00",
            now,
            start,
            end,
            "Korte nachtperiode over middernacht",
        )

        today = now.date()
        tomorrow = (now + timedelta(days=1)).date()

        assert start == datetime(today.year, today.month, today.day, 23, 0, 0)
        assert end == datetime(tomorrow.year, tomorrow.month, tomorrow.day, 1, 0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Nederlandse tijdsuitdrukkingen
# ─────────────────────────────────────────────────────────────────────────────


class TestDutchTimeExpressions:
    """Tests voor typisch Nederlandse tijdsuitdrukkingen."""

    def test_half_10(self, now: datetime):
        """'half 10' -> 09:30."""
        start, end = parse_time_range("half 10", now=now, default_minutes=60)

        print_result("half 10", now, start, end, "Half 10 = 09:30")

        assert start.hour == 9
        assert start.minute == 30

    def test_kwart_over_3(self, now: datetime):
        """'kwart over 3' -> 03:15."""
        start, end = parse_time_range("kwart over 3", now=now, default_minutes=60)

        print_result("kwart over 3", now, start, end, "Kwart over 3 = 03:15")

        assert start.hour == 3
        assert start.minute == 15

    def test_kwart_voor_4(self, now: datetime):
        """'kwart voor 4' -> 03:45."""
        start, end = parse_time_range("kwart voor 4", now=now, default_minutes=60)

        print_result("kwart voor 4", now, start, end, "Kwart voor 4 = 03:45")

        assert start.hour == 3
        assert start.minute == 45

    def test_half_1(self, now: datetime):
        """'half 1' -> 00:30 (edge case)."""
        start, end = parse_time_range("half 1", now=now, default_minutes=60)

        print_result("half 1", now, start, end, "Half 1 = 00:30")

        assert start.hour == 0
        assert start.minute == 30

    def test_morgen_half_3(self, now: datetime):
        """'morgen half 3' -> morgen 02:30."""
        start, end = parse_time_range("morgen half 3", now=now, default_minutes=60)

        tomorrow = (now + timedelta(days=1)).date()

        print_result("morgen half 3", now, start, end, "Morgen half 3 = morgen 02:30")

        assert start.date() == tomorrow
        assert start.hour == 2
        assert start.minute == 30


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Edge cases
# ─────────────────────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases en speciale situaties."""

    def test_empty_string_raises(self, now: datetime):
        """Lege string moet ValueError geven."""
        with pytest.raises(ValueError, match="[Ll]ege"):
            parse_time_range("", now=now)

    def test_whitespace_only_raises(self, now: datetime):
        """Alleen whitespace moet ValueError geven."""
        with pytest.raises(ValueError, match="[Ll]ege"):
            parse_time_range("   ", now=now)

    def test_nonsense_raises(self, now: datetime):
        """Onherkenbare tekst moet ValueError geven."""
        with pytest.raises(ValueError):
            parse_time_range("qwerty asdfgh", now=now)

    def test_default_minutes_respected(self, now: datetime):
        """Verschillende default_minutes waarden."""
        start1, end1 = parse_time_range("morgen 10:00", now=now, default_minutes=30)
        start2, end2 = parse_time_range("morgen 10:00", now=now, default_minutes=90)

        print(f"\n30 min: {end1 - start1}")
        print(f"90 min: {end2 - start2}")

        assert (end1 - start1) == timedelta(minutes=30)
        assert (end2 - start2) == timedelta(minutes=90)

    def test_case_insensitivity(self, now: datetime):
        """Parser moet case-insensitive zijn."""
        start1, end1 = parse_time_range("MORGEN", now=now)
        start2, end2 = parse_time_range("morgen", now=now)
        start3, end3 = parse_time_range("Morgen", now=now)

        assert start1 == start2 == start3
        assert end1 == end2 == end3


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Jaar-overgang
# ─────────────────────────────────────────────────────────────────────────────


class TestYearTransition:
    """Tests voor jaar-overgangen."""

    def test_januari_from_december(self, now_december: datetime):
        """'5 januari' vanuit december -> volgend jaar."""
        start, end = parse_time_range("5 januari", now=now_december)

        print_result(
            "5 januari", now_december, start, end, "Vanuit dec 2025 -> jan 2026"
        )

        assert start == datetime(2026, 1, 5, 0, 0, 0)
        assert end == end_of_day(start)

    def test_volgende_week_year_boundary(self, now_december: datetime):
        """'volgende week' rond jaarwisseling."""
        # 15 dec 2025, volgende week = 22-28 dec
        start, end = parse_time_range("volgende week", now=now_december)

        print_result("volgende week", now_december, start, end, "Week rond kerst 2025")

        assert start.year == 2025
        assert start.month == 12

    def test_volgende_week_from_dec_31(self, now_end_of_year: datetime):
        """'volgende week' op 31 december -> januari volgend jaar."""
        start, end = parse_time_range("volgende week", now=now_end_of_year)

        print_result(
            "volgende week",
            now_end_of_year,
            start,
            end,
            "Volgende week vanuit 31 dec -> jan 2026",
        )

        assert start.year == 2026
        assert start.month == 1

    def test_vorige_jaar(self, now: datetime):
        """'vorig jaar' -> heel 2025."""
        start, end = parse_time_range("vorig jaar", now=now)

        print_result("vorig jaar", now, start, end, "Heel 2025")

        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end == datetime(2025, 12, 31, 23, 59, 59)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Engels
# ─────────────────────────────────────────────────────────────────────────────


class TestEnglish:
    """Tests voor Engelse invoer."""

    def test_tomorrow(self, now: datetime):
        """'tomorrow' -> morgen."""
        start, end = parse_time_range("tomorrow", now=now)

        tomorrow = (now + timedelta(days=1)).date()

        print_result("tomorrow", now, start, end, "Engels: morgen")

        assert start == datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        assert end == end_of_day(start)

    def test_next_monday(self, now: datetime):
        """'next monday' -> volgende maandag."""
        start, end = parse_time_range("next monday", now=now)

        print_result("next monday", now, start, end, "Engels: volgende maandag")

        # now = maandag 26 jan, next monday = 2 feb
        assert start == datetime(2026, 2, 2, 0, 0, 0)
        assert end == end_of_day(start)

    def test_from_to_english(self, now: datetime):
        """'from 9am to 5pm' -> Engelse AM/PM."""
        start, end = parse_time_range("from 9am to 5pm", now=now)

        today = now.date()

        print_result("from 9am to 5pm", now, start, end, "Engels AM/PM formaat")

        assert start == datetime(today.year, today.month, today.day, 9, 0, 0)
        assert end == datetime(today.year, today.month, today.day, 17, 0, 0)

    def test_last_friday(self, now: datetime):
        """'last friday' -> vorige vrijdag."""
        start, end = parse_time_range("last friday", now=now)

        print_result("last friday", now, start, end, "Engels: vorige vrijdag")

        # now = maandag 26 jan, last friday = 23 jan
        assert start == datetime(2026, 1, 23, 0, 0, 0)
        assert end == end_of_day(start)

    def test_yesterday(self, now: datetime):
        """'yesterday' -> gisteren."""
        start, end = parse_time_range("yesterday", now=now)

        yesterday = (now - timedelta(days=1)).date()

        print_result("yesterday", now, start, end, "Engels: gisteren")

        assert start == datetime(
            yesterday.year, yesterday.month, yesterday.day, 0, 0, 0
        )
        assert end == end_of_day(start)


class TestEnglishExtended:
    """Uitgebreide tests voor Engelse parsing."""

    def test_next_week(self, now: datetime):
        """'next week' -> hele volgende week."""
        start, end = parse_time_range("next week", now=now)
        print_result("next week", now, start, end, "Engels: next week")
        # now = 26 jan (ma), next week = 2 feb - 8 feb
        assert start == datetime(2026, 2, 2, 0, 0, 0)
        assert end == datetime(2026, 2, 8, 23, 59, 59)

    def test_in_2_days(self, now: datetime):
        """'in 2 days' -> over 2 dagen (duratie of datum?).
        Context 'in X days' impliceert vaak een datum in de toekomst of een deadline.
        De parser behandelt dit via 'in_duration' pattern als een datum-range (dag X).
        """
        start, end = parse_time_range("in 2 days", now=now)
        print_result("in 2 days", now, start, end, "Engels: in 2 days")
        target = (now + timedelta(days=2)).date()
        assert start.date() == target

    def test_2_weeks_ago(self, now: datetime):
        """'2 weeks ago' -> datum in verleden."""
        start, end = parse_time_range("2 weeks ago", now=now)
        print_result("2 weeks ago", now, start, end, "Engels: 2 weeks ago")
        target = (now - timedelta(weeks=2)).date()
        assert start.date() == target

    def test_written_date_english(self, now: datetime):
        """'fifth of january' -> 5 januari."""
        start, end = parse_time_range("fifth of january", now=now)
        print_result("fifth of january", now, start, end, "Engels: written number")
        # now = 26 jan 2026. 5 jan is verleden -> 2027 (prefer future default)
        assert start == datetime(2027, 1, 5, 0, 0, 0)

    def test_quarter_english(self, now: datetime):
        """'1st quarter 2025' -> Q1 2025."""
        start, end = parse_time_range("1st quarter 2025", now=now)
        print_result("1st quarter 2025", now, start, end, "Engels: 1st quarter")
        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end == datetime(2025, 3, 31, 23, 59, 59)

    def test_quarter_english_word(self, now: datetime):
        """'first quarter 2025' -> Q1 2025."""
        start, end = parse_time_range("first quarter 2025", now=now)
        print_result("first quarter 2025", now, start, end, "Engels: first quarter")
        assert start == datetime(2025, 1, 1, 0, 0, 0)

    def test_next_friday_time(self, now: datetime):
        """'next friday at 3pm'."""
        start, end = parse_time_range("next friday at 3pm", now=now, default_minutes=60)
        print_result("next friday at 3pm", now, start, end, "Engels: next friday 3pm")
        # now = ma 26 jan. next friday = 6 feb (want 'this friday' is 30 jan)
        # Let op: 'next friday' interpretatie kan variëren (komende vs volgende week).
        # In patterns.py: NEXT_WEEKDAY_PATTERN -> 'next friday'.
        # De logica in parsers.py (try_parse_next_weekday) bepaalt dit.
        # Meestal: als vandaag ma is, is 'next friday' de vrijdag van de volgende week.
        # 'this friday' zou 30 jan zijn.
        expected_date = datetime(2026, 2, 6, 15, 0, 0)  # 6 feb

        # Check of het 30 jan of 6 feb is.
        # Als de parser 'next' strikt als +1 week ziet of 'eerstvolgende'.
        # Dateparser library gedrag: 'next friday' vanuit maandag is vaak volgende week.
        assert start == expected_date

    def test_this_weekend(self, now: datetime):
        """'this weekend'."""
        start, end = parse_time_range("this weekend", now=now)
        print_result("this weekend", now, start, end, "Engels: this weekend")
        # now = ma 26 jan. Weekend = za 31 jan - zo 1 feb.
        assert start.date() == datetime(2026, 1, 31).date()
        assert end.date() == datetime(2026, 2, 1).date()

    def test_christmas(self, now: datetime):
        """'christmas' -> 25 dec."""
        start, end = parse_time_range("christmas", now=now)
        print_result("christmas", now, start, end, "Engels: christmas")
        assert start.month == 12
        assert start.day == 25


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Ambiguous cases
# ─────────────────────────────────────────────────────────────────────────────


class TestAmbiguousCases:
    """Tests voor ambigue invoer."""

    def test_2_uur_als_tijd_met_datum_context(self, now: datetime):
        """'morgen 2 uur' = 02:00, niet 2 uur duratie."""
        start, end = parse_time_range("morgen 2 uur", now=now)

        print_result(
            "morgen 2 uur", now, start, end, "Met datum context: tijd, niet duratie"
        )

        assert start.hour == 2
        tomorrow = (now + timedelta(days=1)).date()
        assert start.date() == tomorrow

    def test_2_uur_als_duratie_zonder_context(self, now: datetime):
        """'2 uur' zonder datum = duratie van 2 uur."""
        start, end = parse_time_range("2 uur", now=now)

        print_result("2 uur", now, start, end, "Zonder datum context: duratie")

        assert end > start

    def test_10_uur_meeting(self, now: datetime):
        """'10 uur meeting' -> waarschijnlijk duratie."""
        start, end = parse_time_range("10 uur", now=now)

        print_result("10 uur", now, start, end, "Ambigu: 10:00 of 10 uur duratie?")

        assert end > start


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Suffixes & Leap Years (Nieuwe functionaliteit)
# ─────────────────────────────────────────────────────────────────────────────


class TestSuffixesAndLeapYears:
    """Tests voor suffixes (1st, 2nd) en slimme schrikkeljaar-logica."""

    def test_english_suffixes(self, now: datetime):
        """'1st of march' -> 1 maart (Engelse suffix + tussenvoegsel)."""
        start, end = parse_time_range("1st of march", now=now)
        print_result("1st of march", now, start, end, "1st of march")
        assert start == datetime(2026, 3, 1, 0, 0, 0)

    def test_dutch_suffixes(self, now: datetime):
        """'1e mei' -> 1 mei (Nederlandse suffix)."""
        start, end = parse_time_range("1e mei", now=now)
        print_result("1e mei", now, start, end, "1e mei")
        assert start == datetime(2026, 5, 1, 0, 0, 0)

    def test_leap_year_logic(self, now: datetime):
        """'29 februari' in niet-schrikkeljaar (2026) -> moet naar 2028 springen."""
        # Now is 2026 (geen schrikkeljaar). 2027 ook niet. 2028 wel.
        start, end = parse_time_range("29 februari", now=now)
        print_result(
            "29 februari", now, start, end, "Sprong naar schrikkeljaar 2028 verwacht"
        )

        # De parser moet slim genoeg zijn om 2026 en 2027 over te slaan
        assert start == datetime(2028, 2, 29, 0, 0, 0)
        assert end == end_of_day(start)

    def test_year_boundary_smart(self, now_december: datetime):
        """'2 januari' vanuit december -> moet naar volgend jaar."""
        start, end = parse_time_range("2nd of january", now=now_december)
        print_result(
            "2nd of january", now_december, start, end, "Vanuit dec 2025 -> jan 2026"
        )

        assert start == datetime(2026, 1, 2, 0, 0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Complex Phrases & Variations
# ─────────────────────────────────────────────────────────────────────────────


class TestComplexPhrases:
    """Tests voor complexe zinsconstructies en variaties."""

    def test_on_1st_of_march(self, now: datetime):
        """'on 1st of March' -> 1 maart."""
        start, end = parse_time_range("on 1st of March", now=now)
        print_result("on 1st of March", now, start, end, "Engelse 'on' + suffix")
        assert start == datetime(2026, 3, 1, 0, 0, 0)
        assert end == end_of_day(start)

    def test_vijf_januari_written(self, now: datetime):
        """'vijf januari' -> 5 januari (uitgeschreven getal)."""
        start, end = parse_time_range("vijf januari", now=now)
        print_result("vijf januari", now, start, end, "Uitgeschreven dag")
        # now = 26 jan 2026. 5 jan is verleden -> 2027
        assert start == datetime(2027, 1, 5, 0, 0, 0)
        assert end == end_of_day(start)

    def test_start_end_year_phrases(self, now: datetime):
        """'Start 2025' en 'Eind 2024'."""
        # Start 2025 -> 1 jan 2025
        start, end = parse_time_range("Start 2025", now=now)
        print_result("Start 2025", now, start, end, "Begin van het jaar")
        assert start == datetime(2025, 1, 1, 0, 0, 0)
        assert end == end_of_day(start)

        # Eind 2024 -> 31 dec 2024
        start, end = parse_time_range("Eind 2024", now=now)
        print_result("Eind 2024", now, start, end, "Eind van het jaar")
        assert start == datetime(2024, 12, 31, 0, 0, 0)
        assert end == end_of_day(start)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: System Date (Real-time check)
# ─────────────────────────────────────────────────────────────────────────────


class TestSystemDate:
    """Test met de daadwerkelijke systeemdatum (geen fixture)."""

    def test_real_system_now(self):
        """Gebruik datetime.now() om te zien of het werkt met de huidige tijd."""
        real_now = datetime.now()
        print(f"\n🕒 Real System Time: {real_now}")

        start, end = parse_time_range("vandaag", now=real_now)
        print_result(
            "vandaag (real system time)",
            real_now,
            start,
            end,
            "Check met echte systeemklok",
        )

        assert start.date() == real_now.date()
        assert end.date() == real_now.date()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
