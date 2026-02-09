# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A bilingual (Dutch/English) natural language date/time parser exposed as a Model Context Protocol (MCP) server. Primary use case: deterministic time range resolution for Text-to-SQL applications where LLMs need precise ISO-8601 timestamps for queries.

## Essential Commands

### Development Setup
```bash
uv sync                                    # Install dependencies
chmod +x scripts/bootstrap.sh && ./scripts/bootstrap.sh  # Bootstrap script
```

### Testing
```bash
uv run pytest                             # Run all tests
uv run pytest tests/test_time_range_parser.py  # Run specific test file
uv run pytest -k "test_function_name"     # Run specific test
uv run pytest --cov=date_textparser       # Run with coverage
```

### Code Quality
```bash
uv run ruff format src/                   # Format code
uv run ruff check src/ --fix              # Lint and auto-fix
uv run mypy src/                          # Type checking
```

### Running the Server
```bash
# STDIO mode (for Claude Desktop / MCP clients):
uv run python server_main.py

# SSE mode (for HTTP/SSE clients):
uv run python server_main.py --sse
# Server listens on http://localhost:9000/mcp/sse

# Docker:
docker compose up --build
```

### Integration Testing
```bash
# Terminal 1: Start server in SSE mode
uv run python server_main.py --sse

# Terminal 2: Run MCP client test
uv run python mcp_client_httpx.py
```

## Code Architecture

### Core Parsing Flow

The parsing pipeline follows a **waterfall strategy** with specialized parsers tried in order:

1. **server_main.py**: MCP server entry point
   - Uses FastMCP framework to expose tools
   - Handles transport (STDIO or SSE)
   - Context resolution via `_resolve_context()` (timezone + now_iso)
   - Custom event checking (e.g., "black friday 2025")
   - Error hint analysis for better error messages

2. **src/date_textparser/core.py**: Main parsing engine
   - `_parse_time_range_internal()`: Central parser orchestrator
   - Tries specialized parsers first (quarters, holidays, weekdays, etc.)
   - Falls back to explicit range detection (RANGE_PATTERNS)
   - Finally uses dateparser library with Dutch time normalization
   - Returns `ParseResult` with start/end + assumptions metadata

3. **src/date_textparser/parsers/**: Specialized parser modules
   - `base.py`: Common utilities (time detection, duration parsing, etc.)
   - `holidays.py`: Fixed holidays (Christmas, New Year) + moving holidays (Easter)
   - `periods.py`: Quarters, semesters, seasons, month expressions
   - `weekdays.py`: Next/previous weekday logic
   - `relative.py`: Past/future periods ("last month", "next quarter")
   - `vague.py`: Vague time expressions ("soon", "lunchtime", "end of day")

4. **src/lib/external_time.py**: WorldTimeAPI integration
   - File-based cache with TTL (1h for IP, 5min for time info)
   - `get_local_timezone_from_ip()`: Timezone detection from public IP
   - Only active when `USE_WORLDTIME_API=true`
   - Cache location: `/cache/time_range_parser_cache.json`

### Key Design Decisions

**Time Resolution**: All outputs use **second resolution** (no microseconds). This is enforced via `_floor_to_seconds()` and `.set(microsecond=0)`.

**Deterministic Parsing**: The `now_iso` parameter allows freezing the reference time. Critical for test reproducibility and SQL query regression testing.

**Dutch Time Notation**: "half 3" → 14:30, "kwart over 2" → 14:15. Handled by `normalize_dutch_time()` in parsers/base.py before passing to dateparser.

**Weekday Range Logic**: "tussen maandag en woensdag" always uses the **current week** (Mon-Sun relative to now). See `_weekday_range_this_week()` in core.py.

**Range Parsing Context**: When parsing ranges like "tussen 1 en 2 gisteren", the parser uses prefix/suffix context to determine if numbers are times (1:00) or dates.

## Important Parsing Patterns

### How the Parser Handles Ambiguity

1. **Explicit ranges** (via RANGE_PATTERNS): "from X to Y", "tussen X en Y"
   - Start parsed with `prefer_future=False`
   - End inherits date context from start if missing
   - Weekday-to-weekday ranges use current week

2. **Relative expressions**: "last month", "next quarter"
   - Past periods use `PAST_PERIOD_PATTERN`
   - Future periods use `FUTURE_PERIOD_PATTERN`
   - Quarter calculation: manual 3-month arithmetic (not pendulum.start_of("quarter"))

3. **Weekday expressions**: "next friday", "last monday"
   - Strict parsers in weekdays.py take precedence over dateparser
   - Only fall back to dateparser if time component detected

4. **Single moments**: "tomorrow 3pm"
   - If has time: apply default duration (60min)
   - If date only: expand to full day (00:00:00 - 23:59:59)

## Environment Variables

Configure via `.env` or environment:

- `USE_WORLDTIME_API`: Enable WorldTimeAPI integration (default: false)
- `TRANSPORT_TYPE`: "stdio" or "sse" (default: stdio)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `TZ`: Default timezone (default: Europe/Amsterdam)
- `HOST`, `PORT`: Server binding for SSE mode (default: 0.0.0.0:9000)
- `CACHE_DIR`: Cache location for WorldTimeAPI calls (default: /cache)

## Testing Philosophy

**Test structure**: Tests are organized by feature area, not by file structure:
- `test_time_range_parser.py`: Core parsing scenarios
- `test_quarters_and_past_periods.py`: Business periods
- `test_holidays.py`: Holiday calculations
- `test_timezone_conversion.py`: Timezone conversion
- `test_now_iso.py`: Deterministic parsing with frozen time

**Fixtures**: `conftest.py` provides `fixed_now` (2026-01-30 12:00 CET) for reproducible tests.

**Adding new parsers**:
1. Create parser function in appropriate `parsers/*.py` file
2. Add to `specialized_parsers` list in `core.py:_parse_time_range_internal()`
3. Add comprehensive tests with various phrasings
4. Update vocabulary.py if adding new keywords

## MCP Tool Implementation

Tools are defined in `server_main.py` using `@mcp.tool()` decorator:
- Each tool calls `_resolve_context()` first to normalize timezone and now_iso
- Errors are caught and returned as `{"error": str(e)}` dicts
- All tools log their inputs for debugging

**Adding a new tool**:
1. Define function with `@mcp.tool(name="tool_name")` decorator
2. Add docstring (becomes tool description for LLM)
3. Call `_resolve_context()` if needs timezone/now_iso
4. Return dict with results or `{"error": "..."}` on failure
5. Add to "tools" list in `server_info()` tool

## Common Pitfalls

**Pendulum microseconds**: Always call `.set(microsecond=0)` or `_floor_to_seconds()` on pendulum datetime objects before returning them. Failure to do so will cause test failures due to resolution mismatch.

**Weekday edge cases**: When parsing "next friday", if today is Friday, the parser returns NEXT Friday (7 days ahead), not today. This is controlled by strict weekday parsers in weekdays.py.

**Year boundary issues**: Ranges like "van 5 mei tot 1 mei" (May 5 to May 1) are corrected if parser puts end in next year without explicit year in input. See year correction logic in core.py range parsing.

**Dutch time parsing**: Always use `normalize_dutch_time()` before passing to dateparser. Don't add Dutch time normalization to dateparser settings.

**API timeout**: WorldTimeAPI calls use short timeouts (2-5s). Never increase these as it blocks server startup in Docker environments.

## File Organization

```
server_main.py                 # MCP server, tool definitions
src/
  date_textparser/
    core.py                    # Main parsing engine
    patterns.py                # Regex patterns for range/period detection
    vocabulary.py              # Keywords, timezones, aliases
    result.py                  # ParseResult dataclass
    parsers/
      base.py                  # Shared utilities
      holidays.py              # Fixed/moving holidays
      periods.py               # Quarters, semesters, seasons
      relative.py              # Past/future periods
      vague.py                 # Vague time expressions
      weekdays.py              # Weekday calculations
  lib/
    external_time.py           # WorldTimeAPI integration
tests/                         # Organized by feature, not by file
```
