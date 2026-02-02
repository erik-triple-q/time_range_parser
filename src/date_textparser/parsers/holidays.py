"""
Parsers for holiday expressions (fixed and moving holidays).
"""

from __future__ import annotations

import logging

import pendulum

from ..vocabulary import FIXED_HOLIDAYS, MOVING_HOLIDAYS
from ..patterns import MOVING_HOLIDAY_PATTERN

logger = logging.getLogger(__name__)


def calculate_easter(year: int) -> tuple[int, int]:
    """Calculate Easter Sunday using the Anonymous Gregorian algorithm.

    Returns (month, day) tuple.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    month = (h + L - 7 * m + 114) // 31
    day = ((h + L - 7 * m + 114) % 31) + 1
    return (month, day)


def get_easter(year: int, tz: str) -> pendulum.DateTime:
    """Get Easter Sunday for a given year."""
    month, day = calculate_easter(year)
    return pendulum.datetime(year, month, day, tz=tz)


def get_moving_holiday(name: str, year: int, tz: str) -> pendulum.DateTime | None:
    """Calculate date for moving holidays based on Easter.

    Dutch/Flemish moving holidays:
    - Pasen (Easter Sunday)
    - Tweede Paasdag (Easter Monday) = Easter + 1
    - Goede Vrijdag (Good Friday) = Easter - 2
    - Hemelvaartsdag (Ascension Day) = Easter + 39
    - Pinksteren (Whit Sunday/Pentecost) = Easter + 49
    - Tweede Pinksterdag (Whit Monday) = Easter + 50
    - Carnaval (Carnival Sunday) = Easter - 49
    - Aswoensdag (Ash Wednesday) = Easter - 46
    """
    name_lower = name.lower().strip()

    if name_lower in MOVING_HOLIDAYS:
        easter = get_easter(year, tz)
        offset = MOVING_HOLIDAYS[name_lower]
        return easter.add(days=offset)

    return None


def parse_holiday(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse fixed holiday expressions like 'kerst', 'koningsdag', 'nieuwjaar'."""
    t = text.lower().strip()

    for holiday, (month, day) in FIXED_HOLIDAYS.items():
        if holiday in t:
            year = now.year
            holiday_date = pendulum.datetime(year, month, day, tz=now.timezone_name)
            if holiday_date < now.start_of("day"):
                year += 1

            start = pendulum.datetime(year, month, day, tz=now.timezone_name)
            end = start.end_of("day")

            logger.debug(
                f"parse_holiday: '{text}' -> {holiday}: {start.to_date_string()}"
            )
            return (start, end)

    return None


def parse_moving_holiday(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse moving holiday expressions like 'pasen', 'hemelvaart 2026', 'goede vrijdag'."""
    m = MOVING_HOLIDAY_PATTERN.search(text.lower())
    if not m:
        return None

    holiday_name = m.group("holiday").lower()
    year_str = m.group("year")

    if year_str:
        year = int(year_str)
    else:
        year = now.year
        holiday_date = get_moving_holiday(
            holiday_name, year, now.timezone_name or "UTC"
        )
        if holiday_date and holiday_date < now.start_of("day"):
            year += 1

    result = get_moving_holiday(holiday_name, year, now.timezone_name or "UTC")
    if result is None:
        return None

    start = result.start_of("day")
    end = result.end_of("day")

    logger.debug(
        f"parse_moving_holiday: '{text}' -> {holiday_name}: {start.to_date_string()}"
    )
    return (start, end)
