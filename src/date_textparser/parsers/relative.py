"""
Parsers for relative time expressions (ago, in X days, etc.)
"""

from __future__ import annotations

import logging

import pendulum

from ..vocabulary import DUTCH_NUMBER_WORDS, ENGLISH_NUMBER_WORDS, MONTH_NAMES, ORDINALS
from ..patterns import IN_DURATION_PATTERN, AGO_PATTERN, DUTCH_DAY_MONTH_PATTERN
from .base import parse_number_word, normalize_duration_unit

logger = logging.getLogger(__name__)

_ALL_NUMBER_WORDS = {**DUTCH_NUMBER_WORDS, **ENGLISH_NUMBER_WORDS, **ORDINALS}


def parse_in_duration(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse 'over 2 weken', 'in 3 dagen', 'over een maand' etc."""
    m = IN_DURATION_PATTERN.search(text.lower())
    if not m:
        return None

    n = parse_number_word(m.group("n"))
    unit = normalize_duration_unit(m.group("unit"))

    if not unit:
        return None

    kwargs = {unit: n}
    target = now.add(**kwargs)

    start = target.start_of("day")
    end = target.end_of("day")

    logger.debug(f"parse_in_duration: '{text}' -> {start.to_date_string()}")
    return (start, end)


def parse_ago(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse '2 weken geleden', '3 dagen geleden', 'a month ago' etc."""
    m = AGO_PATTERN.search(text.lower())
    if not m:
        return None

    n = parse_number_word(m.group("n"))
    unit = normalize_duration_unit(m.group("unit"))

    if not unit:
        return None

    kwargs = {unit: n}
    target = now.subtract(**kwargs)

    start = target.start_of("day")
    end = target.end_of("day")

    logger.debug(f"parse_ago: '{text}' -> {start.to_date_string()}")
    return (start, end)


def parse_dutch_day_month(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse 'vijf januari', '5 januari', 'op 15 maart' etc."""
    m = DUTCH_DAY_MONTH_PATTERN.search(text.lower())
    if not m:
        return None

    day_group = m.group("day")
    month_group = m.group("month")

    if not day_group or not month_group:
        return None

    day_str = day_group.lower()
    month_str = month_group.lower()
    year_str = m.group("year")

    if day_str in _ALL_NUMBER_WORDS:
        day = _ALL_NUMBER_WORDS[day_str]
    else:
        try:
            # Strip suffixes like 'st', 'nd', 'e', 'ste' (e.g. "1st" -> "1")
            day = int("".join(filter(str.isdigit, day_str)))
        except ValueError:
            return None

    if not 1 <= day <= 31:
        return None

    month = MONTH_NAMES.get(month_str)
    if month is None:
        return None

    if year_str:
        year = int(year_str)
    else:
        year = now.year
        # Try to find the first valid date starting from 'year' (handling leap years and past dates)
        for offset in range(5):  # Check current year + next 4 years
            y = year + offset
            try:
                test_date = pendulum.datetime(y, month, day, tz=now.timezone_name)
                # If valid date is in the past (and we didn't specify a year), try next year
                if offset == 0 and test_date < now.start_of("day"):
                    continue
                year = y
                break
            except ValueError:
                # Invalid date (e.g. 29 Feb in non-leap year), try next year
                continue

    try:
        start = pendulum.datetime(year, month, day, tz=now.timezone_name)
        end = start.end_of("day")
        logger.debug(f"parse_dutch_day_month: '{text}' -> {start.to_date_string()}")
        return (start, end)
    except ValueError:
        return None
