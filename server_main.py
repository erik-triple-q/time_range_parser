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
    convert_to_timezone as core_convert_to_timezone,
    expand_recurrence,
    calculate_duration,
    DEFAULT_TZ,
)
from date_textparser.core import normalize_timezone
from date_textparser.vocabulary import TIMEZONE_ALIASES

# Ensure src is in path to import lib.external_time
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.append(src_path)
from lib.external_time import (
    get_current_time_from_api,
    get_local_timezone_from_ip,
    get_time_info_from_api,
    get_ip_info,
)

# Configure logging to stderr (important for MCP stdio)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("time-range-parser")

mcp = FastMCP("time-range-parser")

# This will hold the effective default timezone, which can be updated at startup.
_effective_default_tz = DEFAULT_TZ


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


def _resolve_context(
    timezone: str | None, now_iso: str | None
) -> tuple[str, str | None]:
    """
    Resolve effective timezone and 'now' timestamp, potentially using external APIs.

    Fallback strategy:
    - If USE_WORLDTIME_API is False (or fails), we rely on DEFAULT_TZ and system time.
    - TIMEZONE_ALIASES are used for normalization (static list if API is off).
    """
    # 1. Resolve Timezone
    if timezone is None:
        timezone = get_local_timezone_from_ip()

    # Apply smart normalization to ensure we have a valid IANA zone if possible
    if timezone:
        timezone = normalize_timezone(timezone)

    final_tz = timezone or _effective_default_tz

    # 2. Resolve Now
    if now_iso is None:
        now_iso = get_current_time_from_api(final_tz)

    return final_tz, now_iso


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
    timezone: str | None = None,
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
    final_tz, final_now_iso = _resolve_context(timezone, now_iso)
    logger.info(
        f"Tool 'resolve_time_range' called: text='{text}', timezone='{final_tz}', fiscal_start={fiscal_start_month}"
    )

    # 1. Check Custom Events (Point B)
    custom_result = check_custom_events(text)
    if custom_result:
        custom_result["timezone"] = final_tz  # Override default if needed
        return custom_result

    try:
        # Note: parse_time_range_full needs to be updated to accept fiscal_start_month
        result = parse_time_range_full(
            text=text, tz=final_tz, now_iso=final_now_iso
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
    source_timezone: str | None = None,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Convert a date/time expression from one timezone to another.
    Example: text="15:00", source="Amsterdam", target="New York"
    """
    final_source_tz, final_now_iso = _resolve_context(source_timezone, now_iso)
    final_target_tz = normalize_timezone(target_timezone)
    logger.info(
        f"Tool 'convert_timezone' called: text='{text}', from='{final_source_tz}' to='{final_target_tz}'"
    )
    try:
        return core_convert_to_timezone(
            text=text,
            target_tz=final_target_tz,
            source_tz=final_source_tz,
            now_iso=final_now_iso,
        )
    except Exception as e:
        logger.error(f"Error converting timezone: {e}")
        return {"error": str(e)}


@mcp.tool(name="expand_recurrence")
def expand_recurrence_tool(
    text: str,
    timezone: str | None = None,
    count: int = 10,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Generate a list of dates based on a recurrence rule.
    Example: text="elke vrijdag", count=5 -> returns next 5 Fridays.
    """
    final_tz, final_now_iso = _resolve_context(timezone, now_iso)
    logger.info(
        f"Tool 'expand_recurrence' called: text='{text}', count={count}, timezone='{final_tz}'"
    )
    try:
        return expand_recurrence(
            text=text, tz=final_tz, now_iso=final_now_iso, count=count
        )
    except Exception as e:
        logger.error(f"Error expanding recurrence: {e}")
        return {"error": str(e)}


@mcp.tool(name="calculate_duration")
def calculate_duration_tool(
    start: str,
    end: str,
    timezone: str | None = None,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the duration between two dates/times.
    Example: start="now", end="christmas" -> returns days/hours until christmas.
    """
    final_tz, final_now_iso = _resolve_context(timezone, now_iso)
    logger.info(
        f"Tool 'calculate_duration' called: start='{start}', end='{end}', timezone='{final_tz}'"
    )
    try:
        return calculate_duration(
            start_text=start, end_text=end, tz=final_tz, now_iso=final_now_iso
        )
    except Exception as e:
        logger.error(f"Error calculating duration: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_dst_status")
def get_dst_status(timezone: str | None = None) -> dict[str, Any]:
    """
    Get Daylight Saving Time (DST) information for a timezone.
    Returns whether DST is active, and when the next transition occurs.
    """
    final_tz, _ = _resolve_context(timezone, None)
    logger.info(f"Tool 'get_dst_status' called for timezone='{final_tz}'")

    info = get_time_info_from_api(final_tz)
    if not info:
        return {"error": f"Could not fetch time info for '{final_tz}'"}

    return {
        "timezone": final_tz,
        "is_dst": info.get("dst"),
        "dst_abbreviation": info.get("abbreviation"),
        "dst_start": info.get("dst_from"),
        "dst_end": info.get("dst_until"),
        "utc_offset": info.get("utc_offset"),
        "raw_offset": info.get("raw_offset"),
    }


@mcp.tool(name="get_calendar_info")
def get_calendar_info(timezone: str | None = None) -> dict[str, Any]:
    """
    Get calendar information like week number, day of year, and day of week.
    Useful for business logic (e.g. 'What week is it?').
    """
    final_tz, _ = _resolve_context(timezone, None)
    logger.info(f"Tool 'get_calendar_info' called for timezone='{final_tz}'")

    info = get_time_info_from_api(final_tz)
    if not info:
        return {"error": f"Could not fetch time info for '{final_tz}'"}

    return {
        "timezone": final_tz,
        "week_number": info.get("week_number"),
        "day_of_year": info.get("day_of_year"),
        "day_of_week": info.get("day_of_week"),
        "date": info.get("datetime", "")[:10],  # Extract YYYY-MM-DD
        "iso_week_date": f"{info.get('datetime', '')[:4]}-W{info.get('week_number')}",
    }


@mcp.tool(name="get_world_time")
def get_world_time(city: str) -> dict[str, Any]:
    """
    Get the current time for a specific city or timezone via WorldTimeAPI.
    Example: city="New York" -> returns current time in America/New_York.
    """
    use_worldtime_api = os.environ.get("USE_WORLDTIME_API", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    if not use_worldtime_api:
        logger.warning(
            "Tool 'get_world_time' called, but WorldTimeAPI is disabled by server configuration."
        )
        return {"error": "WorldTimeAPI is disabled by server configuration."}

    logger.info(f"Tool 'get_world_time' called: city='{city}'")
    try:
        # 1. Normalize to IANA timezone (e.g. "London" -> "Europe/London")
        timezone = normalize_timezone(city)

        # 2. Fetch from API
        info = get_time_info_from_api(timezone)

        if info:
            return {
                "city": city,
                "timezone": timezone,
                "current_time": info.get("datetime"),
                "utc_offset": info.get("utc_offset"),
                "dst": info.get("dst"),
                "week_number": info.get("week_number"),
                "day_of_year": info.get("day_of_year"),
                "abbreviation": info.get("abbreviation"),
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
    # Try to get the most accurate default timezone for reporting
    ip_info = get_ip_info()
    detected_tz = ip_info.get("timezone") if ip_info else None
    client_ip = ip_info.get("client_ip") if ip_info else "unknown"

    return {
        "name": "time-range-parser",
        "version": get_app_version(),
        "description": "Natural language date/time range parser for Dutch and English",
        "default_timezone": detected_tz or _effective_default_tz,
        "public_ip": client_ip,
        "resolution": "seconds",
        "capabilities": {
            "natural_language_parsing": True,
            "recurrence_expansion": True,
            "timezone_conversion": True,
            "duration_calculation": True,
            "dst_awareness": True,
            "calendar_info": True,
        },
        "tools": [
            "resolve_time_range",
            "convert_timezone",
            "expand_recurrence",
            "calculate_duration",
            "get_dst_status",
            "get_calendar_info",
            "get_world_time",
            "server_info",
        ],
    }


if __name__ == "__main__":
    # Check for WorldTimeAPI usage at startup
    use_worldtime_api = os.environ.get("USE_WORLDTIME_API", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    if use_worldtime_api:
        logger.info(
            "USE_WORLDTIME_API is true. Attempting to detect local timezone from public IP..."
        )

        detected_tz = get_local_timezone_from_ip()
        if detected_tz:
            logger.info(
                f"WorldTimeAPI detected timezone '{detected_tz}'. Overriding default '{_effective_default_tz}'."
            )
            _effective_default_tz = detected_tz
        else:
            logger.warning(
                f"Could not detect timezone from WorldTimeAPI. Using default '{_effective_default_tz}'."
            )

    # Determine transport type
    transport_type = os.environ.get("TRANSPORT_TYPE", "stdio").lower()

    # Legacy support: Check for --sse flag or MCP_TRANSPORT env var
    if "--sse" in sys.argv or os.environ.get("MCP_TRANSPORT") == "sse":
        transport_type = "sse"

    if transport_type in ("sse", "http"):
        import argparse
        from fastapi import FastAPI, responses
        import uvicorn

        # Create a main FastAPI application to act as a router
        app = FastAPI(
            title="Time Range Parser MCP Server",
            version=get_app_version(),
            description="MCP server mounted at /mcp",
        )

        @app.get("/health")
        async def health_check() -> dict[str, Any]:
            """Health check endpoint to verify server status."""
            return {"status": "online", "version": get_app_version()}

        @app.get("/", response_class=responses.HTMLResponse, include_in_schema=False)
        async def root_info():
            """Provides a simple HTML page with information about the server and its endpoints."""
            version = get_app_version()
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Time Range Parser MCP Server</title>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; color: #212529; }}
                        .container {{ max-width: 800px; margin: 2em auto; padding: 2em; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); }}
                        h1 {{ color: #005a9c; }}
                        h2 {{ color: #343a40; border-bottom: 2px solid #dee2e6; padding-bottom: 0.3em; margin-top: 1.5em;}}
                        code {{ background-color: #e9ecef; padding: 0.2em 0.4em; border-radius: 3px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }}
                        ul {{ list-style-type: none; padding: 0; }}
                        li {{ background-color: #f8f9fa; margin: 0.5em 0; padding: 1em; border: 1px solid #dee2e6; border-radius: 5px; display: flex; align-items: center; }}
                        a {{ color: #007bff; text-decoration: none; font-weight: 500; }}
                        a:hover {{ text-decoration: underline; }}
                        .description {{ color: #6c757d; margin-left: 1em; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Time Range Parser MCP Server</h1>
                        <p>Version: <strong>{version}</strong></p>
                        <p>This server provides natural language date/time parsing services via the <strong>MCP (Multi-purpose Communication Protocol)</strong>.</p>
                        <h2>Available Endpoints</h2>
                        <ul>
                            <li><a href="/docs"><code>/docs</code></a><span class="description">&mdash; OpenAPI (Swagger) documentation for REST endpoints.</span></li>
                            <li><a href="/redoc"><code>/redoc</code></a><span class="description">&mdash; Alternative ReDoc documentation.</span></li>
                            <li><a href="/health"><code>/health</code></a><span class="description">&mdash; Health check endpoint. Returns server status and version.</span></li>
                            <li><code>/mcp/sse</code><span class="description">&mdash; The main Server-Sent Events (SSE) endpoint for establishing an MCP session.</li>
                        </ul>
                        <h2>Usage</h2>
                        <p>To interact with the server, connect to the <code>/mcp/sse</code> endpoint with an MCP-compatible client. The server will provide a unique URL for posting messages.</p>
                    </div>
                </body>
            </html>
            """
            return responses.HTMLResponse(content=html_content)

        # Mount the MCP application onto the /mcp path
        app.mount("/mcp", mcp.sse_app())

        parser = argparse.ArgumentParser()
        parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
        parser.add_argument(
            "--port", type=int, default=int(os.environ.get("PORT", "9000"))
        )
        parser.add_argument("--sse", action="store_true")
        args, _ = parser.parse_known_args()

        logger.info(
            f"Starting server with transport '{transport_type}' on {args.host}:{args.port}"
        )
        logger.info(f"MCP endpoint available at http://{args.host}:{args.port}/mcp")
        uvicorn.run(app, host=args.host, port=args.port, log_level=LOG_LEVEL.lower())
    else:
        # Default to stdio
        mcp.run()
