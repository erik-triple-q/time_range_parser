from __future__ import annotations
import logging
import os
import sys
from typing import Any
import re
from importlib.metadata import version, PackageNotFoundError

from mcp.server.fastmcp import FastMCP

from date_textparser import (
    parse_time_range_full,
    convert_to_timezone,
    expand_recurrence,
    calculate_duration,
    DEFAULT_TZ,
)
from date_textparser.core import normalize_timezone

# Ensure src is in path to import lib.external_time
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.append(src_path)
from lib.external_time import get_current_time_from_api

# Configure logging to stderr (important for MCP stdio)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("time-range-parser")

mcp = FastMCP("time-range-parser")


def get_app_version() -> str:
    try:
        return version("time-range-parser")
    except (ImportError, PackageNotFoundError):
        return "0.1.0"


# ─────────────────────────────────────────────────────────────────────────────
# Configuration & Custom Events (Point B)
# ─────────────────────────────────────────────────────────────────────────────

# In a real scenario, load this from a JSON/YAML file
CUSTOM_EVENTS = {
    "black friday 2025": "2025-11-28",
    "cyber monday 2025": "2025-12-01",
    "boekjaar start": "2026-04-01",
}


def check_custom_events(text: str) -> dict[str, Any] | None:
    """Check if text matches a known custom event."""
    key = text.strip().strip("'\"").lower()
    if key in CUSTOM_EVENTS:
        # Simple implementation: return the date as start/end
        # Ideally, parse the value to ensure ISO format
        val = CUSTOM_EVENTS[key]
        return {
            "input": text,
            "timezone": DEFAULT_TZ,
            "start": f"{val}T00:00:00",
            "end": f"{val}T23:59:59",
            "kind": "custom_event",
        }
    return None


def analyze_error_hint(text: str) -> str | None:
    """Analyze input to provide smart error hints (Point C)."""
    # Check for invalid quarters (Q5-Q9)
    if re.search(r"q[5-9]", text, re.IGNORECASE):
        return "Invalid quarter detected. Quarters must be between Q1 and Q4."
    # Check for invalid week numbers (>53)
    if re.search(r"week\s*([6-9]\d|[1-9]\d{2,})", text, re.IGNORECASE):
        return "Invalid week number. Weeks must be between 1 and 53."
    return None


@mcp.tool(name="resolve_time_range")
def resolve_time_range(
    text: str,
    timezone: str = DEFAULT_TZ,
    now_iso: str | None = None,
    fiscal_start_month: int = 1,
) -> dict[str, Any]:
    """
    Parse natural language date/time text into a start/end ISO-8601 range.
    Returns the parsed range and the 'kind' of expression (e.g. 'time', 'date', 'period').

    Output is SECOND resolution only (no microseconds).

    Args:
        text: Natural language input (NL/EN).
        timezone: IANA timezone (default: Europe/Amsterdam)
        now_iso: Optional ISO timestamp as reference for relative expressions
        fiscal_start_month: Start month of the fiscal year (1-12). Default: 1 (January).

    Returns:
        Dictionary with input, timezone, start, end (ISO-8601), and kind
    """
    logger.info(
        f"Tool 'resolve_time_range' called: text='{text}', timezone='{timezone}', fiscal_start={fiscal_start_month}"
    )

    # 1. Check Custom Events (Point B)
    custom_result = check_custom_events(text)
    if custom_result:
        custom_result["timezone"] = timezone  # Override default if needed
        return custom_result

    try:
        # Note: parse_time_range_full needs to be updated to accept fiscal_start_month
        result = parse_time_range_full(
            text=text, tz=timezone, now_iso=now_iso
        )  # TODO: Pass fiscal_start_month

        return {
            "input": text,
            "timezone": result.timezone,
            "start": result.start.set(microsecond=0).to_iso8601_string(),
            "end": result.end.set(microsecond=0).to_iso8601_string(),
            "kind": result.assumptions.get("kind"),
        }
    except Exception as e:
        # 2. Smart Error Responses (Point C)
        hint = analyze_error_hint(text)
        error_msg = f"{str(e)} - Hint: {hint}" if hint else str(e)

        logger.error(f"Error parsing '{text}': {error_msg}")
        return {"error": error_msg, "input": text}


@mcp.tool(name="convert_timezone")
def convert_timezone(
    text: str,
    target_timezone: str,
    source_timezone: str = DEFAULT_TZ,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Convert a date/time expression from one timezone to another.
    Example: text="15:00", source="Amsterdam", target="New York"
    """
    logger.info(
        f"Tool 'convert_timezone' called: text='{text}', from='{source_timezone}' to='{target_timezone}'"
    )
    try:
        return convert_to_timezone(
            text=text,
            target_tz=target_timezone,
            source_tz=source_timezone,
            now_iso=now_iso,
        )
    except Exception as e:
        logger.error(f"Error converting timezone: {e}")
        return {"error": str(e)}


@mcp.tool(name="expand_recurrence")
def expand_recurrence_tool(
    text: str,
    timezone: str = DEFAULT_TZ,
    count: int = 10,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Generate a list of dates based on a recurrence rule.
    Example: text="elke vrijdag", count=5 -> returns next 5 Fridays.
    """
    logger.info(f"Tool 'expand_recurrence' called: text='{text}', count={count}")
    try:
        return expand_recurrence(text=text, tz=timezone, now_iso=now_iso, count=count)
    except Exception as e:
        logger.error(f"Error expanding recurrence: {e}")
        return {"error": str(e)}


@mcp.tool(name="calculate_duration")
def calculate_duration_tool(
    start: str,
    end: str,
    timezone: str = DEFAULT_TZ,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the duration between two dates/times.
    Example: start="now", end="christmas" -> returns days/hours until christmas.
    """
    logger.info(f"Tool 'calculate_duration' called: start='{start}', end='{end}'")
    try:
        return calculate_duration(
            start_text=start, end_text=end, tz=timezone, now_iso=now_iso
        )
    except Exception as e:
        logger.error(f"Error calculating duration: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_world_time")
def get_world_time(city: str) -> dict[str, Any]:
    """
    Get the current time for a specific city or timezone via WorldTimeAPI.
    Example: city="New York" -> returns current time in America/New_York.
    """
    logger.info(f"Tool 'get_world_time' called: city='{city}'")
    try:
        # 1. Normalize to IANA timezone (e.g. "London" -> "Europe/London")
        timezone = normalize_timezone(city)

        # 2. Fetch from API
        time_iso = get_current_time_from_api(timezone)

        if time_iso:
            return {
                "city": city,
                "timezone": timezone,
                "current_time": time_iso,
                "source": "WorldTimeAPI",
            }
        else:
            return {
                "error": f"Could not fetch time for '{city}' (timezone: '{timezone}'). API might be down or timezone invalid."
            }
    except Exception as e:
        logger.error(f"Error in get_world_time: {e}")
        return {"error": str(e)}


@mcp.tool(name="server_info")
def server_info() -> dict[str, Any]:
    """Basic server info for clients."""
    return {
        "name": "time-range-parser",
        "version": get_app_version(),
        "description": "Natural language date/time range parser for Dutch and English",
        "default_timezone": DEFAULT_TZ,
        "resolution": "seconds",
        "capabilities": {
            "natural_language_parsing": True,
            "recurrence_expansion": True,
            "timezone_conversion": True,
            "duration_calculation": True,
        },
        "tools": [
            "resolve_time_range",
            "convert_timezone",
            "expand_recurrence",
            "calculate_duration",
            "get_world_time",
            "server_info",
        ],
    }


if __name__ == "__main__":
    # Check of we als SSE server moeten draaien (bv. in Docker)
    # Via --sse flag of environment variable
    if "--sse" in sys.argv or os.environ.get("MCP_TRANSPORT") == "sse":
        import argparse
        import uvicorn

        parser = argparse.ArgumentParser()
        parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
        parser.add_argument(
            "--port", type=int, default=int(os.environ.get("PORT", "9000"))
        )
        parser.add_argument("--sse", action="store_true")
        args, _ = parser.parse_known_args()

        logger.info(f"Starting SSE server on {args.host}:{args.port}")
        uvicorn.run(
            mcp.sse_app(), host=args.host, port=args.port, log_level=LOG_LEVEL.lower()
        )
    else:
        mcp.run()
