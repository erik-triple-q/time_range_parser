"""
Parsers for weekday expressions (next monday, last friday, first monday of march, etc.)
"""

from __future__ import annotations

import logging

import pendulum

from ..vocabulary import ALL_WEEKDAYS, ORDINALS, MONTH_NAMES, DAY_PARTS
from ..patterns import (
    NEXT_WEEKDAY_PATTERN,
    PREV_WEEKDAY_PATTERN,
    ORDINAL_WEEKDAY_PATTERN,
    COMPOUND_DAY_PATTERN,
)
from .base import get_next_weekday, get_prev_weekday, get_nth_weekday_of_month

logger = logging.getLogger(__name__)


def try_parse_next_weekday(
    text: str, base: pendulum.DateTime
) -> pendulum.DateTime | None:
    """Try to parse 'volgende maandag', 'next friday' etc."""
    m = NEXT_WEEKDAY_PATTERN.search(text.lower())
    if not m:
        return None

    weekday_name = m.group(2).lower()
    target_weekday = ALL_WEEKDAYS.get(weekday_name)

    if target_weekday is None:
        return None

    result = get_next_weekday(base, target_weekday, next_week=True)
    logger.debug(f"try_parse_next_weekday: '{text}' -> {result.to_date_string()}")
    return result


def try_parse_prev_weekday(
    text: str, base: pendulum.DateTime
) -> pendulum.DateTime | None:
    """Try to parse 'vorige maandag', 'last friday' etc."""
    m = PREV_WEEKDAY_PATTERN.search(text.lower())
    if not m:
        return None

    weekday_name = m.group(2).lower()
    target_weekday = ALL_WEEKDAYS.get(weekday_name)

    if target_weekday is None:
        return None

    result = get_prev_weekday(base, target_weekday)
    logger.debug(f"try_parse_prev_weekday: '{text}' -> {result.to_date_string()}")
    return result


def parse_ordinal_weekday(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse 'eerste maandag van maart', 'last friday of the month', 'laatste vrijdag' etc."""
    m = ORDINAL_WEEKDAY_PATTERN.search(text.lower())
    if not m:
        return None

    ordinal_str = m.group("ordinal").lower()
    weekday_str = m.group("weekday").lower()
    month_str = m.group("month")
    year_str = m.group("year")

    ordinal = ORDINALS.get(ordinal_str)
    weekday = ALL_WEEKDAYS.get(weekday_str)

    if ordinal is None or weekday is None:
        return None

    # "last friday" without month context should be handled by prev_weekday parser
    if month_str is None and ordinal == -1:
        return None

    if year_str:
        year = int(year_str)
    else:
        year = now.year

    if month_str:
        month_lower = month_str.lower()
        if month_lower in ("maand", "month"):
            month = now.month
        else:
            month_val = MONTH_NAMES.get(month_lower)
            if month_val is None:
                return None
            month = month_val
    else:
        month = now.month

    result = get_nth_weekday_of_month(
        year, month, weekday, ordinal, now.timezone_name or "UTC"
    )
    if result is None:
        return None

    # If result is in the past and no explicit month/year, try next month
    if month_str is None and year_str is None and result < now.start_of("day"):
        next_month = now.add(months=1)
        result = get_nth_weekday_of_month(
            next_month.year,
            next_month.month,
            weekday,
            ordinal,
            now.timezone_name or "UTC",
        )
        if result is None:
            return None

    start = result.start_of("day")
    end = result.end_of("day")

    logger.debug(f"parse_ordinal_weekday: '{text}' -> {start.to_date_string()}")
    return (start, end)


def parse_compound_day(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse compound expressions like 'morgenochtend', 'maandagavond'."""
    m = COMPOUND_DAY_PATTERN.search(text.lower())
    if not m:
        return None

    day_str = m.group("day").lower()
    part_str = m.group("part").lower()

    if day_str == "vandaag":
        target = now
    elif day_str == "morgen":
        target = now.add(days=1)
    elif day_str == "overmorgen":
        target = now.add(days=2)
    elif day_str == "gisteren":
        target = now.subtract(days=1)
    elif day_str == "eergisteren":
        target = now.subtract(days=2)
    elif day_str in ALL_WEEKDAYS:
        weekday = ALL_WEEKDAYS[day_str]
        target = get_next_weekday(now, weekday, next_week=False)
    else:
        return None

    if part_str in DAY_PARTS:
        start_hour, end_hour = DAY_PARTS[part_str]
        if start_hour < end_hour:
            start = target.set(hour=start_hour, minute=0, second=0, microsecond=0)
            end = target.set(
                hour=end_hour - 1, minute=59, second=59, microsecond=999999
            )
        else:
            # Night case: spans midnight
            start = target.set(hour=start_hour, minute=0, second=0, microsecond=0)
            end = target.add(days=1).set(
                hour=end_hour - 1, minute=59, second=59, microsecond=999999
            )
    else:
        return None

    logger.debug(
        f"parse_compound_day: '{text}' -> {start.to_datetime_string()} to {end.to_datetime_string()}"
    )
    return (start, end)
