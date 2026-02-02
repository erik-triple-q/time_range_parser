"""
Parsers for period expressions (quarters, weeks, half-years, seasons, etc.)
"""

from __future__ import annotations

import logging
from typing import cast

import pendulum

from ..vocabulary import SEASONS, MONTH_NAMES, HALF_YEARS
from ..patterns import (
    QUARTER_PATTERN,
    WEEK_NUMBER_PATTERN,
    HALF_YEAR_PATTERN,
    SEASON_EXPR_PATTERN,
    MONTH_EXPR_PATTERN,
    WEEKEND_PATTERN,
    PAST_PERIOD_PATTERN,
    FUTURE_PERIOD_PATTERN,
    YEAR_BOUNDARY_PATTERN,
)

logger = logging.getLogger(__name__)


def parse_quarter(
    text: str, now: pendulum.DateTime, fiscal_start_month: int = 1
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse quarter expressions like 'Q4 2025', '4e kwartaal', 'vierde kwartaal 2025'."""
    m = QUARTER_PATTERN.search(text.lower())
    if not m:
        return None

    quarter: int | None = None

    q_notation = m.group("q_notation")
    quarter_num = m.group("quarter_num")
    ordinal_group = m.group("ordinal")

    if q_notation:
        quarter = int(q_notation[1])
    elif quarter_num:
        quarter = int(quarter_num)
    elif ordinal_group:
        ordinal = ordinal_group.lower()
        ordinal_map = {
            "1e": 1,
            "eerste": 1,
            "1ste": 1,
            "2e": 2,
            "tweede": 2,
            "2de": 2,
            "3e": 3,
            "derde": 3,
            "3de": 3,
            "4e": 4,
            "vierde": 4,
            "4de": 4,
            "1st": 1,
            "first": 1,
            "2nd": 2,
            "second": 2,
            "3rd": 3,
            "third": 3,
            "4th": 4,
            "fourth": 4,
        }
        quarter = ordinal_map.get(ordinal)

    if quarter is None:
        return None

    year_group = m.group("year")
    year = int(year_group) if year_group else now.year

    # Calculate start month based on fiscal year offset
    # Standard: Q1=1, Q2=4, Q3=7, Q4=10
    # With offset: Add (fiscal_start_month - 1) months
    months_offset = fiscal_start_month - 1
    start_month = ((quarter - 1) * 3 + 1) + months_offset

    # Adjust year if month overflows 12 (e.g. Q4 starting in Jan of next year)
    while start_month > 12:
        start_month -= 12
        year += 1

    start = pendulum.datetime(year, start_month, 1, tz=now.timezone_name)
    end = start.add(months=3).subtract(microseconds=1)

    logger.debug(
        f"parse_quarter: '{text}' -> Q{quarter} {year}: {start.to_date_string()} to {end.to_date_string()}"
    )
    return (start, end)


def parse_week_number(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse week number expressions like 'week 43', 'wk 12 2026'."""
    m = WEEK_NUMBER_PATTERN.search(text.lower())
    if not m:
        return None

    week_group = m.group("week")
    if not week_group:
        return None
    week = int(week_group)
    year_group = m.group("year")
    year = int(year_group) if year_group else now.year

    if not 1 <= week <= 53:
        return None

    try:
        start = cast(
            pendulum.DateTime,
            pendulum.parse(f"{year}-W{week:02d}-1", tz=now.timezone_name),
        )
        end = start.end_of("week")

        logger.debug(
            f"parse_week_number: '{text}' -> week {week} {year}: {start.to_date_string()} to {end.to_date_string()}"
        )
        return (start, end)
    except Exception as e:
        logger.warning(f"parse_week_number: failed to parse week {week} {year}: {e}")
        return None


def parse_half_year(
    text: str, now: pendulum.DateTime, fiscal_start_month: int = 1
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse half-year expressions like 'H1 2025', 'eerste helft', '2e semester'."""
    m = HALF_YEAR_PATTERN.search(text.lower())
    if not m:
        return None

    half: int | None = None

    h_notation = m.group("h_notation")
    text_group = m.group("text")

    if h_notation:
        half = int(h_notation[1])
    elif text_group:
        text_match = text_group.lower()
        for pattern, h in HALF_YEARS.items():
            if pattern in text_match:
                half = h
                break

    if half is None:
        return None

    year_group = m.group("year")
    year = int(year_group) if year_group else now.year

    # H1 covers months 1-6, H2 covers 7-12 (relative to start)
    # Add fiscal offset
    months_offset = fiscal_start_month - 1
    base_start_month = 1 if half == 1 else 7
    start_month = base_start_month + months_offset

    while start_month > 12:
        start_month -= 12
        year += 1

    start = pendulum.datetime(year, start_month, 1, tz=now.timezone_name)
    end = start.add(months=6).subtract(microseconds=1)

    logger.debug(
        f"parse_half_year: '{text}' -> H{half} {year}: {start.to_date_string()} to {end.to_date_string()}"
    )
    return (start, end)


def parse_season(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse season expressions like 'zomer 2025', 'deze winter', 'volgende lente'."""
    m = SEASON_EXPR_PATTERN.search(text.lower())
    if not m:
        return None

    season_group = m.group("season")
    if not season_group:
        return None
    season_name = season_group.lower()
    modifier = m.group("modifier")
    year_group = m.group("year")
    explicit_year = int(year_group) if year_group else None

    if season_name not in SEASONS:
        return None

    start_month, end_month = SEASONS[season_name]

    if explicit_year:
        year = explicit_year
    elif modifier:
        mod = modifier.lower()
        if mod in ("volgende", "volgend", "next"):
            year = now.year + 1
        elif mod in ("vorige", "vorig", "last", "previous", "afgelopen"):
            year = now.year - 1
        else:
            year = now.year
    else:
        year = now.year

    if start_month > end_month:  # winter case: Dec-Feb
        if modifier and modifier.lower() in (
            "vorige",
            "vorig",
            "last",
            "previous",
            "afgelopen",
        ):
            start = pendulum.datetime(year, start_month, 1, tz=now.timezone_name)
            end = pendulum.datetime(
                year + 1, end_month, 1, tz=now.timezone_name
            ).end_of("month")
        else:
            start = pendulum.datetime(year, start_month, 1, tz=now.timezone_name)
            end = pendulum.datetime(
                year + 1, end_month, 1, tz=now.timezone_name
            ).end_of("month")
    else:
        start = pendulum.datetime(year, start_month, 1, tz=now.timezone_name)
        end = pendulum.datetime(year, end_month, 1, tz=now.timezone_name).end_of(
            "month"
        )

    logger.debug(
        f"parse_season: '{text}' -> {season_name} {year}: {start.to_date_string()} to {end.to_date_string()}"
    )
    return (start, end)


def parse_month_expr(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse month expressions like 'januari 2025', 'begin maart', 'eind april'."""
    m = MONTH_EXPR_PATTERN.search(text.lower())
    if not m:
        return None

    month_group = m.group("month")
    if not month_group:
        return None
    month_name = month_group.lower()
    position = m.group("position")
    year_group = m.group("year")
    explicit_year = int(year_group) if year_group else None

    if month_name not in MONTH_NAMES:
        return None

    month = MONTH_NAMES[month_name]
    year = explicit_year if explicit_year else now.year

    if not explicit_year and month < now.month:
        year = now.year + 1

    month_start = pendulum.datetime(year, month, 1, tz=now.timezone_name)
    month_end = month_start.end_of("month")

    if position:
        pos = position.lower()
        if pos in ("begin", "start"):
            start = month_start
            end = month_start.add(days=9).end_of("day")
        elif pos in ("eind", "end"):
            start = month_end.subtract(days=9).start_of("day")
            end = month_end
        elif pos in ("medio", "half", "midden", "mid"):
            start = month_start.add(days=10)
            end = month_start.add(days=19).end_of("day")
        else:
            start = month_start
            end = month_end
    else:
        start = month_start
        end = month_end

    logger.debug(
        f"parse_month_expr: '{text}' -> {start.to_date_string()} to {end.to_date_string()}"
    )
    return (start, end)


def parse_weekend(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse weekend expressions like 'weekend', 'dit weekend', 'volgend weekend'."""
    m = WEEKEND_PATTERN.search(text.lower())
    if not m:
        return None

    modifier = m.group("modifier")

    # Calculate Saturday of the current week (Mon=0 ... Sun=6)
    # If today is Sunday (6), Saturday (5) was yesterday (-1)
    this_saturday = now.add(days=5 - now.weekday()).start_of("day")

    if modifier:
        mod = modifier.lower()
        if mod in ("volgend", "volgende", "next"):
            saturday = this_saturday.add(weeks=1)
        elif mod in ("vorig", "vorige", "last", "afgelopen"):
            saturday = this_saturday.subtract(weeks=1)
        else:
            saturday = this_saturday
    else:
        if now.weekday() > 5:
            saturday = this_saturday.add(weeks=1)
        else:
            saturday = this_saturday

    start = saturday
    end = saturday.add(days=1).end_of("day")

    logger.debug(
        f"parse_weekend: '{text}' -> {start.to_date_string()} to {end.to_date_string()}"
    )
    return (start, end)


def parse_past_period(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse 'afgelopen jaar', 'vorige maand', 'afgelopen week' etc."""
    m = PAST_PERIOD_PATTERN.search(text.lower())
    if not m:
        return None

    unit_group = m.group("unit")
    if not unit_group:
        return None
    period = unit_group.lower()

    if period == "jaar":
        start = now.subtract(years=1).start_of("year")
        end = start.end_of("year")
    elif period == "maand":
        start = now.subtract(months=1).start_of("month")
        end = start.end_of("month")
    elif period == "week":
        start = now.subtract(weeks=1).start_of("week")
        end = start.end_of("week")
    else:
        return None

    logger.debug(
        f"parse_past_period: '{text}' -> {start.to_date_string()} to {end.to_date_string()}"
    )
    return (start, end)


def parse_future_period(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse 'volgende maand', 'komend jaar', 'next week' etc."""
    m = FUTURE_PERIOD_PATTERN.search(text.lower())
    if not m:
        return None

    unit_group = m.group("unit")
    if not unit_group:
        return None
    period = unit_group.lower()

    if period in ("jaar", "year"):
        start = now.add(years=1).start_of("year")
        end = start.end_of("year")
    elif period in ("maand", "month"):
        start = now.add(months=1).start_of("month")
        end = start.end_of("month")
    elif period == "week":
        start = now.add(weeks=1).start_of("week")
        end = start.end_of("week")
    else:
        return None

    logger.debug(
        f"parse_future_period: '{text}' -> {start.to_date_string()} to {end.to_date_string()}"
    )
    return (start, end)


def parse_year_boundary(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse 'Start 2025', 'Eind 2024'."""
    m = YEAR_BOUNDARY_PATTERN.search(text)
    if not m:
        return None

    boundary_type_group = m.group("type")
    year_group = m.group("year")

    if not boundary_type_group or not year_group:
        return None
    boundary_type = boundary_type_group.lower()
    year = int(year_group)

    if boundary_type in ("begin", "start"):
        start = pendulum.datetime(year, 1, 1, tz=now.timezone_name)
        end = start.end_of("day")
    else:  # eind, end
        start = pendulum.datetime(year, 12, 31, tz=now.timezone_name)
        end = start.end_of("day")

    logger.debug(f"parse_year_boundary: '{text}' -> {start.to_date_string()}")
    return (start, end)
