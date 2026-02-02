"""
Parser for vague time expressions (straks, binnenkort, soon, etc.)
"""

from __future__ import annotations

import logging

import pendulum

from ..vocabulary import VAGUE_TIME_EXPRESSIONS
from ..patterns import VAGUE_TIME_PATTERN

logger = logging.getLogger(__name__)


def parse_vague_time(
    text: str, now: pendulum.DateTime
) -> tuple[pendulum.DateTime, pendulum.DateTime] | None:
    """Parse vague time expressions like 'straks', 'binnenkort', 'vanavond', 'later'."""
    m = VAGUE_TIME_PATTERN.search(text.lower())
    if not m:
        return None

    expr = m.group(1).lower()
    config = VAGUE_TIME_EXPRESSIONS.get(expr)

    if config is None:
        return None

    expr_type = config.get("type")

    if expr_type == "future":
        delta_kwargs = {
            k: v for k, v in config.items() if k in ("hours", "minutes", "days")
        }
        target = now.add(**delta_kwargs)
        start = target
        end = target.add(hours=1)

    elif expr_type == "past":
        delta_kwargs = {}
        for k, v in config.items():
            if k in ("hours", "minutes", "days") and v < 0:
                delta_kwargs[k] = abs(v)
        target = now.subtract(**delta_kwargs)
        start = target
        end = target.add(hours=1)

    elif expr_type == "future_range":
        days = config.get("days", 7)
        start = now.start_of("day")
        end = now.add(days=days).end_of("day")

    elif expr_type == "past_range":
        days = abs(config.get("days", -7))
        start = now.subtract(days=days).start_of("day")
        end = now.end_of("day")

    elif expr_type == "current_range":
        days = config.get("days", 3)
        start = now.subtract(days=days // 2).start_of("day")
        end = now.add(days=days // 2).end_of("day")

    elif expr_type == "around_now":
        hours = config.get("hours", 1)
        start = now.subtract(hours=hours)
        end = now.add(hours=hours)

    elif expr_type == "fixed_today":
        hour = config.get("hour", 12)
        minute = config.get("minute", 0)
        target = now.set(hour=hour, minute=minute, second=0, microsecond=0)
        start = target
        end = target.add(hours=2)

    elif expr_type == "time_of_day":
        hour = config.get("hour", 12)
        start = now.set(hour=hour, minute=0, second=0, microsecond=0)
        end = start.add(hours=2)

    else:
        return None

    logger.debug(
        f"parse_vague_time: '{text}' -> {expr}: {start.to_datetime_string()} to {end.to_datetime_string()}"
    )
    return (start, end)
