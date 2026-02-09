"""
Date text parser for Dutch and English natural language date expressions.
"""

from __future__ import annotations

try:
    import dateparser
except ImportError as e:
    raise ImportError(
        "Missing dependency 'dateparser'. Install project dependencies before running tests or using the package. "
        "Run 'uv sync' or 'pip install -e .[dev]' from the project root."
    ) from e
import logging
import re
import warnings
from datetime import datetime as dt_datetime
from typing import Any, Callable, cast

try:
    import pendulum
except ImportError as e:
    raise ImportError(
        "Missing dependency 'pendulum'. Install project dependencies before running tests or using the package. "
        "Run 'uv sync' or 'pip install -e .[dev]' from the project root."
    ) from e

from .vocabulary import (
    DEFAULT_TZ,
    DEFAULT_EVENT_DURATION_MINUTES,
    TIMEZONE_ALIASES,
    RECURRENCE_KEYWORDS,
    ALL_WEEKDAYS,
    DURATION_UNITS,
    PERIOD_UNITS,
    RELATIVE_DAYS,
    TIMEZONES,
)
from .result import ParseResult
from .parsers import (
    normalize_dutch_time,
    has_time,
    has_date,
    parse_duration,
    period_bounds,
    try_parse_next_weekday,
    try_parse_prev_weekday,
    extract_date_part,
    parse_quarter,
    parse_week_number,
    parse_half_year,
    parse_season,
    parse_month_expr,
    parse_weekend,
    parse_past_period,
    parse_future_period,
    parse_year_boundary,
    parse_holiday,
    parse_moving_holiday,
    parse_in_duration,
    parse_ago,
    parse_dutch_day_month,
    parse_ordinal_weekday,
    parse_compound_day,
    parse_vague_time,
)
from .patterns import (
    PAST_PERIOD_PATTERN,
    FUTURE_PERIOD_PATTERN,
    NEXT_WEEKDAY_PATTERN,
    PREV_WEEKDAY_PATTERN,
    RANGE_PATTERNS,
)

logger = logging.getLogger(__name__)

NOW_KEYWORDS: set[str] = {"nu", "now", "sysdate"}


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

# Enrich TIMEZONE_ALIASES from TIMEZONES list
for _tz in TIMEZONES:
    _lower_tz = _tz.lower()
    if _lower_tz not in TIMEZONE_ALIASES:
        TIMEZONE_ALIASES[_lower_tz] = _tz

    if "/" in _tz:
        _city = _tz.split("/")[-1].replace("_", " ").lower()
        if _city not in TIMEZONE_ALIASES:
            TIMEZONE_ALIASES[_city] = _tz


def normalize_timezone(tz: str) -> str:
    """Normalize timezone string, handling common aliases (e.g. 'New York')."""
    if not tz:
        return DEFAULT_TZ

    cleaned = tz.strip().strip("'\"")
    lower = cleaned.lower()

    if lower in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[lower]

    return cleaned


def _resolve_now(now_iso: str | None, tz: str) -> pendulum.DateTime:
    """Resolve 'now' from an ISO string or get the current time in the given timezone."""
    if now_iso:
        # The `tz` here acts as a default for naive timestamps.
        parsed = pendulum.parse(now_iso, tz=tz)
        # Ensure the final object is in the target timezone.
        return cast(pendulum.DateTime, parsed).in_timezone(tz)
    return pendulum.now(tz)


def _to_naive_datetime(dt: pendulum.DateTime) -> dt_datetime:
    return dt_datetime(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond
    )


def _dateparser_settings(
    tz: str, base: pendulum.DateTime, prefer_future: bool = True
) -> dict[str, Any]:
    return {
        "RETURN_AS_TIMEZONE_AWARE": True,
        "TIMEZONE": tz,
        "TO_TIMEZONE": tz,
        "RELATIVE_BASE": _to_naive_datetime(base),
        "PREFER_DATES_FROM": "future" if prefer_future else "current_period",
        "PREFER_DAY_OF_MONTH": "first",
        "LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD": 0.2,
    }


def _floor_to_seconds(dt: pendulum.DateTime) -> pendulum.DateTime:
    return dt.set(microsecond=0)


def _safe_dateparser_parse(
    text: str,
    settings: dict[str, Any],
) -> dt_datetime | None:
    """Parse with dateparser, suppressing known deprecation warnings."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return dateparser.parse(text, settings=settings, languages=["nl", "en"])


def _is_plain_weekday(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in ALL_WEEKDAYS


def _weekday_index(text: str) -> int | None:
    return ALL_WEEKDAYS.get((text or "").strip().lower())


def _parse_dt(
    text: str,
    tz: str,
    base: pendulum.DateTime,
    prefer_future: bool = True,
) -> pendulum.DateTime | None:
    logger.debug(
        f"_parse_dt: text='{text}', base={base.to_datetime_string()}, prefer_future={prefer_future}"
    )

    # Only use strict next_weekday parser if there is no time component.
    # If there is time (e.g. "next friday at 3pm"), let dateparser handle the full string.
    if not has_time(text):
        next_weekday_result = try_parse_next_weekday(text, base)
        if next_weekday_result is not None:
            return _floor_to_seconds(next_weekday_result)

    prev_weekday_result = try_parse_prev_weekday(text, base)
    if prev_weekday_result is not None:
        return _floor_to_seconds(prev_weekday_result)

    normalized_text = normalize_dutch_time(text)

    # Clean up 'at' before time digits to help dateparser (e.g. "next friday at 3pm" -> "next friday 3pm")
    text_for_parser = re.sub(r"\bat\s+(?=\d)", "", normalized_text, flags=re.IGNORECASE)

    dt = _safe_dateparser_parse(
        text_for_parser,
        settings=_dateparser_settings(tz, base, prefer_future),
    )

    if dt is None:
        date_part = extract_date_part(text)
        if date_part != text:
            logger.debug(f"_parse_dt: trying extracted date part '{date_part}'")
            dt = _safe_dateparser_parse(
                date_part,
                settings=_dateparser_settings(tz, base, prefer_future),
            )

    # Fallback: if dateparser failed completely, try strict weekday parsers again.
    # This handles cases where 'has_time' was True (so we skipped strict parsing initially),
    # but dateparser failed to parse the complex string. We at least return the date.
    if dt is None:
        next_weekday_result = try_parse_next_weekday(text, base)
        if next_weekday_result is not None:
            # If text has time, try to re-parse with explicit date to capture time
            if has_time(text):
                m = NEXT_WEEKDAY_PATTERN.search(text)
                if m:
                    iso_date = next_weekday_result.to_date_string()
                    # Replace the relative day with absolute date
                    new_text = text[: m.start()] + f" {iso_date} " + text[m.end() :]
                    new_text = " ".join(new_text.split())

                    dt_retry = _safe_dateparser_parse(
                        new_text,
                        settings=_dateparser_settings(tz, base, prefer_future),
                    )
                    if dt_retry:
                        if dt_retry.tzinfo is None:
                            result = pendulum.instance(dt_retry, tz=tz)
                        else:
                            result = pendulum.instance(dt_retry).in_timezone(tz)
                        return _floor_to_seconds(result)

            return _floor_to_seconds(next_weekday_result)

        prev_weekday_result = try_parse_prev_weekday(text, base)
        if prev_weekday_result is not None:
            if has_time(text):
                m = PREV_WEEKDAY_PATTERN.search(text)
                if m:
                    iso_date = prev_weekday_result.to_date_string()
                    new_text = text[: m.start()] + f" {iso_date} " + text[m.end() :]
                    new_text = " ".join(new_text.split())

                    dt_retry = _safe_dateparser_parse(
                        new_text,
                        settings=_dateparser_settings(tz, base, prefer_future),
                    )
                    if dt_retry:
                        if dt_retry.tzinfo is None:
                            result = pendulum.instance(dt_retry, tz=tz)
                        else:
                            result = pendulum.instance(dt_retry).in_timezone(tz)
                        return _floor_to_seconds(result)

            return _floor_to_seconds(prev_weekday_result)

    if dt is None:
        logger.warning(f"_parse_dt: could not parse '{text}'")
        return None

    if dt.tzinfo is None:
        result = pendulum.instance(dt, tz=tz)
    else:
        result = pendulum.instance(dt).in_timezone(tz)

    return _floor_to_seconds(result)


def _normalize_date_only(
    dt: pendulum.DateTime, original_text: str
) -> pendulum.DateTime:
    if has_date(original_text) and not has_time(original_text):
        return dt.start_of("day").set(microsecond=0)
    return _floor_to_seconds(dt)


def _parse_end_with_start_base(
    end_text: str,
    start: pendulum.DateTime,
    tz: str,
) -> pendulum.DateTime | None:
    end_dt = _parse_dt(end_text, tz, base=start, prefer_future=False)
    if end_dt is None:
        return None

    if (not has_date(end_text)) and has_time(end_text):
        end_dt = start.set(
            hour=end_dt.hour,
            minute=end_dt.minute,
            second=end_dt.second,
            microsecond=0,
        )

    end_dt = _normalize_date_only(end_dt, end_text)
    return _floor_to_seconds(end_dt)


def _finalize_result(result: ParseResult) -> ParseResult:
    s = result.start.set(microsecond=0)
    e = result.end.set(microsecond=0)
    return ParseResult(
        start=s,
        end=e,
        timezone=result.timezone,
        assumptions=result.assumptions,
    )


def _weekday_range_this_week(
    a: str,
    b: str,
    *,
    now: pendulum.DateTime,
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """
    Handle ranges like 'tussen maandag en woensdag' robustly:
    - start = weekday within the current week of 'now' (Mon..Sun)
    - end = weekday within same week as start (>= start), as end-of-day.

    This matches the test expectation for 'tussen maandag en woensdag'.
    """
    if not (_is_plain_weekday(a) and _is_plain_weekday(b)):
        return None

    wa = _weekday_index(a)
    wb = _weekday_index(b)
    if wa is None or wb is None:
        return None

    week_start = now.start_of("week")  # Monday 00:00 in pendulum
    start = week_start.add(days=wa).start_of("day")
    end = week_start.add(days=wb).end_of("day")

    # If end would be before start (e.g., "vrijdag tot maandag"),
    # interpret end as next week's weekday.
    if end < start:
        end = end.add(weeks=1)

    return start, end


def _parse_relative_quarter(
    text: str, now: pendulum.DateTime, fiscal_start_month: int = 1
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Handle 'vorig kwartaal', 'next quarter' explicitly."""

    # Calculate start of current quarter (fiscal or calendar)
    # Adjust for fiscal year if fiscal_start_month != 1
    adjusted_month = (now.month - fiscal_start_month) % 12
    start_month = (adjusted_month // 3) * 3 + fiscal_start_month
    if start_month > 12:
        start_month -= 12
    current_q_start = now.replace(
        month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    # Adjust year if we wrapped around
    if now.month < fiscal_start_month and start_month >= fiscal_start_month:
        current_q_start = current_q_start.subtract(years=1)

    # Past
    match = PAST_PERIOD_PATTERN.search(text)
    if match:
        unit_name = match.group("unit").lower()
        logger.debug(f"_parse_relative_quarter: matched past unit '{unit_name}'")
        unit = PERIOD_UNITS.get(unit_name)
        if unit == "quarter":
            start = current_q_start.subtract(months=3)
            end = start.add(months=3).subtract(microseconds=1)
            return start, end

    # Future
    match = FUTURE_PERIOD_PATTERN.search(text)
    if match:
        unit_name = match.group("unit").lower()
        logger.debug(f"_parse_relative_quarter: matched future unit '{unit_name}'")
        unit = PERIOD_UNITS.get(unit_name)
        if unit == "quarter":
            start = current_q_start.add(months=3)
            end = start.add(months=3).subtract(microseconds=1)
            return start, end

    return None


# =============================================================================
# INTERNAL PARSER
# =============================================================================


def _parse_time_range_internal(
    text: str,
    tz: str,
    now: pendulum.DateTime,
    default_minutes: int = DEFAULT_EVENT_DURATION_MINUTES,
    fiscal_start_month: int = 1,
) -> ParseResult:
    text = (text or "").strip().strip("'\"")
    if not text:
        logger.warning("Empty input provided")
        raise ValueError("Lege invoer.")

    logger.info(f"Parsing: '{text}' (now={now.to_datetime_string()}, tz={tz})")

    if text.lower() in NOW_KEYWORDS:
        logger.debug(f"Recognized 'now' keyword: '{text}'")
        start = now
        end = start.add(minutes=default_minutes)
        result = ParseResult(
            start=start,
            end=end,
            timezone=tz,
            assumptions={
                "kind": "now_keyword_with_default_duration",
                "default_minutes": default_minutes,
                "base_now": now.to_iso8601_string(),
            },
        )
        return _finalize_result(result)

    normalized_text = normalize_dutch_time(text)

    ParserFunc = Callable[
        [str, pendulum.DateTime], "tuple[pendulum.DateTime, pendulum.DateTime] | None"
    ]
    specialized_parsers: list[tuple[str, ParserFunc]] = [
        ("quarter", parse_quarter),
        ("relative_quarter", _parse_relative_quarter),
        ("year_boundary", parse_year_boundary),
        ("week_number", parse_week_number),
        ("half_year", parse_half_year),
        ("ordinal_weekday", parse_ordinal_weekday),
        ("compound_day", parse_compound_day),
        ("season", parse_season),
        ("moving_holiday", parse_moving_holiday),
        ("holiday", parse_holiday),
        ("weekend", parse_weekend),
        ("past_period", parse_past_period),
        ("future_period", parse_future_period),
        ("in_duration", parse_in_duration),
        ("ago", parse_ago),
        ("dutch_day_month", parse_dutch_day_month),
        ("month_expr", parse_month_expr),
        ("vague_time", parse_vague_time),
    ]

    for kind, parser in specialized_parsers:
        # Quarter parsers need fiscal_start_month parameter
        if kind in ("quarter", "relative_quarter"):
            parsed = parser(text, now, fiscal_start_month)
        else:
            parsed = parser(text, now)
        if parsed:
            s, e = parsed
            result = ParseResult(
                start=s,
                end=e,
                timezone=tz,
                assumptions={"kind": kind, "base_now": now.to_iso8601_string()},
            )
            return _finalize_result(result)

    # 1) Explicit range
    rng = None
    for pattern in RANGE_PATTERNS:
        m = pattern.search(normalized_text)
        if m:
            a_val = m.group("a")
            b_val = m.group("b")
            # Check for prefix context (e.g. "gisteren tussen 10 en 11")
            prefix = ""
            if m.start() > 0:
                prefix = normalized_text[: m.start()].strip()

            # Heuristic: if prefix OR suffix (b_val) implies a specific day,
            # treat small numbers as time (e.g. "1" -> "1:00")
            context_text = (prefix + " " + b_val).lower()
            is_specific_day = any(w in context_text for w in RELATIVE_DAYS) or any(
                w in context_text for w in ALL_WEEKDAYS
            )

            if is_specific_day:
                if a_val.isdigit() and int(a_val) <= 24:
                    a_val = f"{a_val}:00"

                # Also fix b_val digits (e.g. "2 gisteren" -> "2:00 gisteren")
                def _repl_time(match: re.Match[str]) -> str:
                    val = int(match.group(1))
                    if val <= 24:
                        return f"{val}:00"
                    return match.group(0)

                b_val = re.sub(r"(?<![:.])\b(\d{1,2})\b(?![.:])", _repl_time, b_val)

            if prefix:
                logger.debug(f"Found prefix '{prefix}' for range, prepending to parts")
                a_val = f"{prefix} {a_val}"
                b_val = f"{prefix} {b_val}"
            rng = (a_val, b_val)
            break

    if rng:
        a, b = rng
        logger.debug(f"Found explicit range: '{a}' to '{b}'")

        # ✅ Special case: weekday-to-weekday ranges (e.g., maandag..woensdag)
        weekday_range = _weekday_range_this_week(a, b, now=now)
        if weekday_range is not None:
            start, end = weekday_range
            result = ParseResult(
                start=start,
                end=end,
                timezone=tz,
                assumptions={
                    "kind": "explicit_range",
                    "range_split": [a, b],
                    "base_now": now.to_iso8601_string(),
                    "weekday_range_mode": "this_week",
                },
            )
            return _finalize_result(result)

        start_parsed = _parse_dt(a, tz, base=now, prefer_future=False)
        if start_parsed is None:
            raise ValueError(f"Kon start niet parsen: {a!r}")
        start = _normalize_date_only(start_parsed, a)

        # FIX: If b has a date, parse it absolutely (relative to now), not relative to start.
        # This prevents "1 mei" being parsed as next year (relative to start) when start is "5 mei".
        if has_date(b):
            end_parsed = _parse_dt(b, tz, base=now, prefer_future=False)
            if end_parsed is None:
                raise ValueError(f"Kon eind niet parsen: {b!r}")
            # Note: end_of_day normalization happens below
            end = _normalize_date_only(end_parsed, b)
        else:
            end_parsed = _parse_end_with_start_base(b, start, tz)
            if end_parsed is None:
                raise ValueError(f"Kon eind niet parsen: {b!r}")
            end = end_parsed

        inferred_next_day = False
        if end < start and (not has_date(b)) and has_time(b):
            end = end.add(days=1)
            inferred_next_day = True
            logger.debug("Inferred next day for end time (midnight crossing)")

        if has_date(b) and not has_time(b):
            end = end.end_of("day")

        # Suffix context fix: If 'a' has no date (e.g. "1"), but 'b' does (e.g. "2 gisteren"),
        # and they ended up on different dates, align 'start' to 'end'.
        if (not has_date(a)) and has_date(b):
            if start.date() != end.date():
                logger.debug(
                    f"Aligning start date to end date (suffix context in '{b}')"
                )
                start = start.set(year=end.year, month=end.month, day=end.day)

        # FIX: If start and end are same month but end is later year, assume typo and fix year.
        # e.g. "van 5 mei tot 1 mei" -> parsed as May 5 2026 to May 1 2027.
        if (
            start.month == end.month
            and end.year > start.year
            and not re.search(r"\d{4}", b)
        ):
            logger.debug("Correcting end year (assumed typo in range with same month)")
            end = end.set(year=start.year)

        # Safety check: ensure chronological order (e.g. "tussen 1 en 2 gisteren")
        if start > end:
            logger.debug(
                f"Swapping start and end because start > end ({start} > {end})"
            )
            start, end = end, start

        result = ParseResult(
            start=start,
            end=end,
            timezone=tz,
            assumptions={
                "kind": "explicit_range",
                "range_split": [a, b],
                "base_now": now.to_iso8601_string(),
                "end_time_only": (not has_date(b)) and has_time(b),
                "inferred_next_day": inferred_next_day,
            },
        )
        return _finalize_result(result)

    # 2) Single moment/period
    start_parsed = _parse_dt(normalized_text, tz, base=now, prefer_future=True)
    if start_parsed is None:
        raise ValueError(f"Kon tekst niet parsen: {text!r}")
    start = start_parsed

    dur = parse_duration(text)
    if dur is not None:
        end = start + dur
        result = ParseResult(
            start=start,
            end=end,
            timezone=tz,
            assumptions={
                "kind": "duration",
                "duration": str(dur),
                "base_now": now.to_iso8601_string(),
            },
        )
        return _finalize_result(result)

    bounds = period_bounds(text, start)
    if bounds:
        s, e = bounds
        result = ParseResult(
            start=s,
            end=e,
            timezone=tz,
            assumptions={"kind": "period_bounds", "base_now": now.to_iso8601_string()},
        )
        return _finalize_result(result)

    if has_time(text):
        end = start.add(minutes=default_minutes)
        result = ParseResult(
            start=start,
            end=end,
            timezone=tz,
            assumptions={
                "kind": "time_with_default_duration",
                "default_minutes": default_minutes,
                "base_now": now.to_iso8601_string(),
            },
        )
        return _finalize_result(result)

    start = start.start_of("day")
    end = start.end_of("day")
    result = ParseResult(
        start=start,
        end=end,
        timezone=tz,
        assumptions={"kind": "date_whole_day", "base_now": now.to_iso8601_string()},
    )
    return _finalize_result(result)


# =============================================================================
# PUBLIC API
# =============================================================================


def parse_time_range(
    text: str,
    *,
    now: dt_datetime,
    default_minutes: int = DEFAULT_EVENT_DURATION_MINUTES,
    tz: str = DEFAULT_TZ,
) -> tuple[dt_datetime, dt_datetime]:
    tz = normalize_timezone(tz)
    now_pendulum = pendulum.datetime(
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        now.second,
        now.microsecond,
        tz=tz,
    )

    result = _parse_time_range_internal(text, tz, now_pendulum, default_minutes)

    return (
        dt_datetime(
            result.start.year,
            result.start.month,
            result.start.day,
            result.start.hour,
            result.start.minute,
            result.start.second,
            0,
        ),
        dt_datetime(
            result.end.year,
            result.end.month,
            result.end.day,
            result.end.hour,
            result.end.minute,
            result.end.second,
            0,
        ),
    )


def parse_time_range_tz(
    text: str,
    *,
    now: dt_datetime,
    default_minutes: int = DEFAULT_EVENT_DURATION_MINUTES,
    tz: str = DEFAULT_TZ,
) -> tuple[pendulum.DateTime, pendulum.DateTime]:
    tz = normalize_timezone(tz)
    now_pendulum = pendulum.datetime(
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        now.second,
        now.microsecond,
        tz=tz,
    )
    result = _parse_time_range_internal(text, tz, now_pendulum, default_minutes)
    return result.start, result.end


def parse_time_range_full(
    text: str,
    tz: str = DEFAULT_TZ,
    now_iso: str | None = None,
    default_minutes: int = DEFAULT_EVENT_DURATION_MINUTES,
    fiscal_start_month: int = 1,
) -> ParseResult:
    text = (text or "").strip()
    if not text:
        raise ValueError("Lege invoer.")

    tz = normalize_timezone(tz)
    now = _resolve_now(now_iso, tz)
    return _parse_time_range_internal(
        text, tz, now, default_minutes=default_minutes, fiscal_start_month=fiscal_start_month
    )


def convert_to_timezone(
    text: str,
    target_tz: str,
    source_tz: str = DEFAULT_TZ,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Parse text in source_tz and convert the result to target_tz.
    """
    source_tz = normalize_timezone(source_tz)
    target_tz = normalize_timezone(target_tz)

    # Parse in source timezone
    result = parse_time_range_full(text, tz=source_tz, now_iso=now_iso)

    s_target = result.start.in_timezone(target_tz)
    e_target = result.end.in_timezone(target_tz)

    return {
        "input": text,
        "source_timezone": source_tz,
        "target_timezone": target_tz,
        "source_start": result.start.to_iso8601_string(),
        "target_start": s_target.to_iso8601_string(),
        "source_end": result.end.to_iso8601_string(),
        "target_end": e_target.to_iso8601_string(),
        "utc_offset_diff_hours": (
            (s_target.offset - result.start.offset) / 3600.0
            if s_target.offset is not None and result.start.offset is not None
            else 0.0
        ),
    }


def expand_recurrence(
    text: str,
    tz: str = DEFAULT_TZ,
    now_iso: str | None = None,
    count: int = 10,
) -> dict[str, Any]:
    """
    Generate a list of dates based on a recurrence rule (e.g. 'every friday').
    """
    tz = normalize_timezone(tz)
    now = _resolve_now(now_iso, tz)
    normalized = text.lower()

    interval_val = 1
    unit = None
    weekday_idx = None

    # 1. Check for explicit number (e.g. "every 2 weeks")
    number_match = re.search(r"(\d+)", normalized)
    if number_match:
        interval_val = int(number_match.group(1))

    # 2. Check for specific weekday (e.g. "every Friday")
    for wd_name, wd_idx in ALL_WEEKDAYS.items():
        if wd_name in normalized:
            weekday_idx = wd_idx
            unit = "weeks"  # Implies weekly recurrence
            break

    # 3. Check for units if no weekday found
    if not unit:
        for u_name, u_std in DURATION_UNITS.items():
            if re.search(r"\b" + re.escape(u_name) + r"\b", normalized):
                unit = u_std
                break

    # 4. Handle keywords like "daily", "monthly"
    if "dagelijks" in normalized or "daily" in normalized:
        unit = "days"
        interval_val = 1
    elif "wekelijks" in normalized or "weekly" in normalized:
        unit = "weeks"
        interval_val = 1
    elif "maandelijks" in normalized or "monthly" in normalized:
        unit = "months"
        interval_val = 1
    elif "jaarlijks" in normalized or "yearly" in normalized:
        unit = "years"
        interval_val = 1

    if not unit:
        # Fallback: if "elke" is present but no unit, assume days?
        # For now, if we can't determine unit, we can't generate.
        if any(k in normalized for k in RECURRENCE_KEYWORDS):
            # Default to days if ambiguous but clearly a recurrence request
            unit = "days"
        else:
            raise ValueError(f"Kon geen herhalingspatroon herkennen in: '{text}'")

    # Determine start date
    current = now

    # If weekday specified, advance to next occurrence
    if weekday_idx is not None:
        if current.day_of_week != weekday_idx:
            current = current.next(cast(Any, weekday_idx))
        # If today IS the day, we include it (or should we skip? Let's include)

    dates = []
    for _ in range(count):
        dates.append(current.to_iso8601_string())
        current = current.add(**{unit: interval_val})

    return {
        "input": text,
        "timezone": tz,
        "rule": {"interval": interval_val, "unit": unit, "weekday": weekday_idx},
        "dates": dates,
    }


def calculate_duration(
    start_text: str,
    end_text: str,
    tz: str = DEFAULT_TZ,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the difference between two dates/times.
    """
    tz = normalize_timezone(tz)

    # Parse both inputs independently relative to 'now'
    res_a = parse_time_range_full(start_text, tz=tz, now_iso=now_iso)
    res_b = parse_time_range_full(end_text, tz=tz, now_iso=now_iso)

    dt_a = res_a.start
    dt_b = res_b.start

    diff = dt_b - dt_a

    # Business days calculation (simple Mon-Fri)
    if dt_b < dt_a:
        start_iter, end_iter = dt_b, dt_a
        sign = -1
    else:
        start_iter, end_iter = dt_a, dt_b
        sign = 1

    business_days = 0
    curr = start_iter
    # Iterate by day to count weekdays
    while curr.date() < end_iter.date():
        if curr.day_of_week not in (pendulum.SATURDAY, pendulum.SUNDAY):
            business_days += 1
        curr = curr.add(days=1)

    business_days *= sign

    return {
        "input_start": start_text,
        "input_end": end_text,
        "timezone": tz,
        "start_iso": dt_a.to_iso8601_string(),
        "end_iso": dt_b.to_iso8601_string(),
        "duration": {
            "total_days": diff.total_days(),
            "total_seconds": diff.total_seconds(),
            "business_days": business_days,
            "human_readable": diff.in_words(locale="en"),
        },
    }
