"""
Base helper functions for date/time parsing.
"""

from __future__ import annotations

import logging
import re

import pendulum

from ..vocabulary import PERIOD_UNITS
from ..patterns import (
    WEEKDAY_PATTERN,
    PERIOD_UNIT_PATTERN,
    RANGE_PATTERNS,
    DASH_RANGE_PATTERN,
    TIME_HINT_PATTERN,
    DATE_HINT_PATTERN,
    DATE_EXTRACT_PATTERN,
    DURATION_PATTERN,
    TIME_RANGE_PATTERN,
    DUTCH_HOUR_PATTERN,
    DUTCH_HALF_PATTERN,
    DUTCH_KWART_OVER_PATTERN,
    DUTCH_KWART_VOOR_PATTERN,
)

logger = logging.getLogger(__name__)


def parse_number_word(text: str) -> int:
    """Parse number words like 'een', 'één', 'a', 'an' to integer."""
    t = text.lower().strip()
    if t in ("een", "één", "a", "an"):
        return 1
    try:
        return int(t)
    except ValueError:
        return 1


def normalize_duration_unit(unit: str) -> str | None:
    """Normalize duration unit to pendulum kwarg name."""
    u = unit.lower().rstrip("s").rstrip("en")

    unit_map = {
        "dag": "days",
        "day": "days",
        "d": "days",
        "week": "weeks",
        "wek": "weeks",
        "w": "weeks",
        "maand": "months",
        "month": "months",
        "jaar": "years",
        "year": "years",
        "uur": "hours",
        "hour": "hours",
        "h": "hours",
        "min": "minutes",
        "minuut": "minutes",
        "minute": "minutes",
    }

    return unit_map.get(u)


def is_weekday_reference(text: str) -> bool:
    """Check if text contains a weekday reference."""
    return bool(WEEKDAY_PATTERN.search(text.lower()))


def extract_period_unit(text: str) -> str | None:
    """Extract and normalize period unit from text, using word boundaries."""
    match = PERIOD_UNIT_PATTERN.search(text.lower())
    if match:
        return PERIOD_UNITS.get(match.group(1).lower())
    return None


def get_next_weekday(
    base: pendulum.DateTime,
    target_weekday: int,
    next_week: bool = False,
) -> pendulum.DateTime:
    """Get the next occurrence of a weekday from the base date."""
    current_weekday = base.weekday()

    if next_week:
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7
        else:
            days_ahead += 7
    else:
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7

    result = base.add(days=days_ahead).start_of("day")
    logger.debug(
        f"get_next_weekday: base={base.to_date_string()}, target={target_weekday}, "
        f"next_week={next_week} -> {result.to_date_string()}"
    )
    return result


def get_prev_weekday(base: pendulum.DateTime, target_weekday: int) -> pendulum.DateTime:
    """Get the previous occurrence of a weekday from the base date."""
    current_weekday = base.weekday()
    days_behind = (current_weekday - target_weekday) % 7
    if days_behind == 0:
        days_behind = 7

    result = base.subtract(days=days_behind).start_of("day")
    logger.debug(
        f"get_prev_weekday: base={base.to_date_string()}, target={target_weekday} -> {result.to_date_string()}"
    )
    return result


def get_nth_weekday_of_month(
    year: int,
    month: int,
    weekday: int,
    n: int,
    tz: str,
) -> pendulum.DateTime | None:
    """Get the nth occurrence of a weekday in a month.

    Args:
        year: Year
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)
        n: Occurrence (1=first, 2=second, ..., -1=last)
        tz: Timezone

    Returns:
        DateTime or None if not found
    """
    if n == -1:
        # Last occurrence: start from end of month
        dt = pendulum.datetime(year, month, 1, tz=tz).end_of("month").start_of("day")
        while dt.weekday() != weekday:
            dt = dt.subtract(days=1)
        return dt
    else:
        # Nth occurrence: find first, then add weeks
        dt = pendulum.datetime(year, month, 1, tz=tz)
        while dt.weekday() != weekday:
            dt = dt.add(days=1)
        dt = dt.add(weeks=n - 1)
        if dt.month != month:
            return None
        return dt


def has_time(text: str) -> bool:
    """Check if text contains a time indicator."""
    return TIME_HINT_PATTERN.search(text or "") is not None


def has_date(text: str) -> bool:
    """Check if text contains a date indicator."""
    return DATE_HINT_PATTERN.search(text or "") is not None


def find_range(text: str) -> tuple[str, str] | None:
    """Find a range expression in text and return (start, end) parts."""
    t = (text or "").strip()
    for pat in RANGE_PATTERNS:
        m = pat.search(t)
        if m:
            result = (m.group("a").strip(), m.group("b").strip())
            logger.debug(f"find_range: '{t}' -> {result}")
            return result

    m = DASH_RANGE_PATTERN.match(t)
    if m:
        result = (m.group("a").strip(), m.group("b").strip())
        logger.debug(f"find_range (dash): '{t}' -> {result}")
        return result

    return None


def parse_duration(text: str) -> pendulum.Duration | None:
    """Parse a duration expression from text."""
    m = DURATION_PATTERN.search(text or "")
    if not m:
        return None

    n = int(m.group("n"))
    u = m.group("u").lower()

    if u in ("uur", "uren", "h", "hour", "hours"):
        start_pos = m.start()
        before_text = text[:start_pos].lower().strip()

        duration_indicators = ("voor", "lang", "duur", "duurt", "over", "binnen", "na")
        if n <= 24 and not any(
            before_text.endswith(ind) for ind in duration_indicators
        ):
            if has_date(text) or any(
                w in text.lower() for w in ("morgen", "vandaag", "overmorgen")
            ):
                logger.debug(
                    f"parse_duration: '{text}' -> None (interpreted as time, not duration)"
                )
                return None

    result: pendulum.Duration | None = None

    if u.startswith("min") and u not in ("maand", "maanden", "month", "months"):
        result = pendulum.duration(minutes=n)
    elif u in ("uur", "uren", "h", "hour", "hours"):
        result = pendulum.duration(hours=n)
    elif u in ("dag", "dagen", "d", "day", "days"):
        result = pendulum.duration(days=n)
    elif u in ("week", "weken", "w", "weeks"):
        result = pendulum.duration(weeks=n)
    elif u in ("maand", "maanden", "month", "months"):
        result = pendulum.duration(months=n)
    elif u in ("jaar", "jaren", "year", "years"):
        result = pendulum.duration(years=n)

    if result:
        logger.debug(f"parse_duration: '{text}' -> {result}")

    return result


def normalize_dutch_time(text: str) -> str:
    """Normalize Dutch time expressions to standard format."""
    original_text = text

    def replace_half(match: re.Match) -> str:
        hour = int(match.group(1))
        actual_hour = hour - 1 if hour > 0 else 23
        return f"{actual_hour}:30"

    text = DUTCH_HALF_PATTERN.sub(replace_half, text)

    def replace_kwart_over(match: re.Match) -> str:
        hour = int(match.group(1))
        return f"{hour}:15"

    text = DUTCH_KWART_OVER_PATTERN.sub(replace_kwart_over, text)

    def replace_kwart_voor(match: re.Match) -> str:
        hour = int(match.group(1))
        actual_hour = hour - 1 if hour > 0 else 23
        return f"{actual_hour}:45"

    text = DUTCH_KWART_VOOR_PATTERN.sub(replace_kwart_voor, text)

    m = TIME_RANGE_PATTERN.search(text)
    if m:
        prefix = m.group(1)
        start_time = m.group(2)
        connector = m.group(4)
        end_time = m.group(5)

        if ":" not in start_time:
            start_time = f"{start_time}:00"
        if ":" not in end_time:
            end_time = f"{end_time}:00"

        new_range = f"{prefix} {start_time} {connector} {end_time}"
        text = text[: m.start()] + new_range + text[m.end() :]
    else:

        def replace_hour(match: re.Match) -> str:
            hour = match.group(1)
            return f"{hour}:00"

        text = DUTCH_HOUR_PATTERN.sub(replace_hour, text)

    if text != original_text:
        logger.debug(f"normalize_dutch_time: '{original_text}' -> '{text}'")

    return text


def extract_date_part(text: str) -> str:
    """Extract the date part from text."""
    m = DATE_EXTRACT_PATTERN.search(text)
    if m:
        result = m.group(0)
        logger.debug(f"extract_date_part: '{text}' -> '{result}'")
        return result
    return text


def period_bounds(
    text: str, anchor: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Get start/end bounds for period references like 'deze maand', 'this week'.

    Uses word boundaries to avoid matching 'maand' in 'maandag'.
    """
    if is_weekday_reference(text):
        return None

    unit = extract_period_unit(text)
    if not unit:
        return None

    result = (anchor.start_of(unit), anchor.end_of(unit))
    logger.debug(
        f"period_bounds: '{text}' -> {result[0].to_date_string()} to {result[1].to_date_string()}"
    )
    return result
