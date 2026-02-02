# Technical Documentation

This document contains the API reference, testing instructions, and development guidelines for the `time-range-parser` MCP server.

## 🛠️ API Reference (Tools)

### `resolve_time_range`

Parses natural language into a structured time range.

- **Arguments**:
  - `text` (str): The input text (e.g., "tomorrow 3pm").
  - `timezone` (str, optional): IANA timezone (default: `Europe/Amsterdam`).
  - `now_iso` (str, optional): Reference time in ISO-8601 format.

### `resolve_time_range_simple`

Same as above, but returns a minimal JSON response (only start/end/timezone).

### `resolve_time_range_debug`

Returns detailed debug information, including internal assumptions made by the parser.

### `convert_timezone`

Converts a time expression from a source timezone to a target timezone.

- **Arguments**:
  - `text` (str): Time expression (e.g., "15:00").
  - `target_timezone` (str): Destination timezone (e.g., "America/New_York").
  - `source_timezone` (str, optional): Origin timezone (default: `Europe/Amsterdam`).

### `expand_recurrence`

Generates a list of future dates based on a recurring pattern.

- **Arguments**:
  - `text` (str): Pattern (e.g., "every friday", "daily").
  - `count` (int, optional): Number of dates to generate (default: 10).

### `calculate_duration`

Calculates the duration between two natural language points in time.

- **Arguments**:
  - `start` (str): Start expression (e.g., "now").
  - `end` (str): End expression (e.g., "next week").

### `server_info`

Returns metadata about the server configuration.

---

## 💡 Technical Tips & Tricks

### Deterministic SQL Generation & Testing

For **Text-to-SQL** applications, reproducibility is key. When generating queries for regression tests, relative terms like "last month" must always resolve to the same dates. Use the `now_iso` argument to freeze the reference time:

```json
{
  "text": "tomorrow",
  "now_iso": "2025-01-01T12:00:00"
}
```

### Timezone Handling

The server uses `pendulum` for robust timezone support. You can use:

- **IANA names**: `Europe/Amsterdam`, `America/New_York`.
- **Aliases**: `NYC`, `London`, `EST`, `CET`.

### External Time & IP Detection

The server includes `src/lib/external_time.py` which implements integration with WorldTimeAPI.

**Functions:**

- `get_local_timezone_from_ip()`: Detects the server's timezone based on its public IP.
- `get_valid_timezones()`: Fetches a list of valid IANA timezones.
- `get_current_time_from_api(timezone)`: Fetches the current time for a specific timezone.

> **Note**: These functions use `httpx` with short timeouts (2.0s - 5.0s) to ensure non-blocking behavior.

---

## 🧪 Testing & Verification

### 1. Unit Tests

Run the comprehensive test suite to verify parsing logic:

```bash
uv run pytest

# Run with coverage
uv run pytest --cov=date_textparser
```

### 2. Integration Test (MCP Client)

To test the full MCP flow (SSE connection, JSON-RPC handshake, tool calls), use the included client script.

**Step 1: Start the server (SSE mode)**

```bash
# Using Docker
docker compose up

# OR using Python directly
uv run python server_main.py --sse
```

**Step 2: Run the test client**

```bash
uv run python mcp_client_httpx.py
```

---

## 🛠️ Development

### Linting & Formatting

```bash
# Format code
uv run ruff format src/

# Lint code
uv run ruff check src/ --fix

# Type checking
uv run mypy src/
```
