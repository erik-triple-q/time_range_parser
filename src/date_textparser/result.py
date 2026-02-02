"""
Result dataclass for parsed time ranges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pendulum


@dataclass
class ParseResult:
    """Result of parsing a time range expression.

    Attributes:
        start: Start datetime of the range
        end: End datetime of the range
        timezone: IANA timezone string
        assumptions: Dictionary of parsing metadata and assumptions made
    """

    start: pendulum.DateTime
    end: pendulum.DateTime
    timezone: str
    assumptions: dict[str, Any]
