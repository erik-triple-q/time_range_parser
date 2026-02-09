# time-range-parser

Natural language date/time range parser for Dutch and English. Designed as a **Model Context Protocol (MCP) server** for seamless integration with Claude Desktop, VS Code, Cursor, and other MCP clients.

For detailed API documentation, testing, and development guides, see [docs/TECHNICAL.md](docs/TECHNICAL.md).

---

## ✨ Features

### 🌍 Languages & Localization

- **Bilingual**: Full support for **Dutch** (🇳🇱) and **English** (🇬🇧/🇺🇸).
- **Dutch Time Notation**: Correctly interprets "half 3" as 14:30, "kwart over" (quarter past), "kwart voor" (quarter to).
- **Number Words**: Supports written numbers ("one", "twee", "fifteen").

### 📅 Date & Time Parsing

- **Relative Days**: `today`, `tomorrow`, `yesterday`, `overmorgen` (day after tomorrow), `eergisteren`.
- **Weekdays**: `next monday`, `last friday`, `coming tuesday`.
- **Compound Expressions**: `tomorrow afternoon`, `monday morning`, `vanavond` (tonight).
- **Specific Dates**: ISO-8601 (`2026-01-30`), EU format (`30-01-2026`), Natural (`5th of January`).

### ⏳ Ranges & Durations

- **Time Ranges**: `10:00 to 12:00`, `between 2pm and 4pm`.
- **Date Ranges**: `from Monday to Wednesday`, `January 1st to 5th`.
- **Durations**: `in 2 hours`, `3 days ago`, `for 30 minutes`.
- **Vague Times**: `soon`, `later`, `end of day`, `lunchtime`, `straks`.

### 📊 Business & Periods

- **Quarters**: `Q1 2025`, `3rd quarter`, `kwartaal 4`.
- **Semesters/Halves**: `H1`, `first half of the year`.
- **Week Numbers**: `week 42`.
- **Seasons**: `summer`, `winter`, `voorjaar`.
- **Recurrence**: `every friday`, `elke 2 weken`, `daily`.

### 🌐 Timezones

- **Conversion**: Convert times between zones (e.g., Amsterdam to New York).
- **Aliases**: Supports city names (`New York`, `London`) and abbreviations (`EST`, `CET`).
- **External Sync**: Optional integration with WorldTimeAPI for IP-based timezone detection and world time lookup.

### Holidays

- **Fixed**: Christmas, New Year, Valentine's Day.
- **Moving (Religious)**: Easter, Good Friday, Pentecost, Ascension Day (calculated dynamically).

---

## ✅ Output Policy

- **Resolution**: Seconds (no microseconds).
- **End times**: Inclusive/Exclusive logic handled to return precise ISO-8601 strings (e.g., end of day is `23:59:59`).

---

## 🎯 Primary Use Case: Text-to-SQL

This server is optimized to act as a deterministic middleware between an LLM and a Database.
LLMs often struggle with calculating exact dates for "last month" or "Q1". This server resolves them to precise ISO-8601 timestamps, allowing the LLM to generate accurate SQL queries.

**Example Flow:**

1. **User:** "Hoeveel omzet hadden we vorige maand?"
2. **LLM:** Calls `resolve_time_range("vorige maand")`
3. **Server:** Returns `{"start": "2026-02-01T00:00:00", "end": "2026-02-28T23:59:59"}`
4. **LLM:** Generates SQL: `SELECT sum(amount) FROM orders WHERE created_at BETWEEN '2026-02-01' AND '2026-02-28'`

> **Try it out:** See the example below to test this flow with the included demo script.

### Running the Text-to-SQL Example

To test the complete flow with the included example script, you'll need **two terminal windows**:

**Terminal 1** - Start the server in SSE mode:
```bash
uv run python server_main.py --sse
```

Wait for the server to start (you'll see `Uvicorn running on http://0.0.0.0:9000`).

**Terminal 2** - Run the example script:
```bash
uv run python examples/text_to_sql_example.py
```

You can also provide a custom query:
```bash
uv run python examples/text_to_sql_example.py "What was the revenue last month?"
```

---

## 📦 Installation

```bash
git clone <repo-url>
cd time_range_parser
uv sync
```

> **Note**: Run all commands from the project root.

---

## 📖 Supported Formats (Examples)

> Assuming today is **Friday, January 30, 2026**.
> Default timezone: `Europe/Amsterdam`.

| Input                  | Meaning                         | Example Output                        |
| ---------------------- | ------------------------------- | ------------------------------------- |
| `tomorrow 15:00`       | Tomorrow at 15:00 (1h duration) | `2026-01-31T15:00:00`                 |
| `from 10 to 12:30`     | Today 10:00 - 12:30             | `2026-01-30T10:00:00` → `...12:30:00` |
| `next friday`          | Next Friday (full day)          | `2026-02-06T00:00:00` → `...23:59:59` |
| `this week`            | This week (Mon-Sun)             | `2026-01-26` → `2026-02-01`           |
| `Q4 2025`              | 4th Quarter 2025                | `2025-10-01` → `2025-12-31`           |
| `half 3` (NL)          | 14:30 (1h duration)             | `2026-01-30T14:30:00`                 |
| `tussen ma en wo` (NL) | Mon 00:00 - Wed 23:59           | `2026-01-26` → `2026-01-28`           |

---

## 🔌 MCP Server

### Start (Standalone)

```bash
uv run python server_main.py --sse
```

### Available Tools

See [docs/TECHNICAL.md](docs/TECHNICAL.md) for the full API reference.

- `resolve_time_range`
- `resolve_time_range_simple`
- `resolve_time_range_debug`
- `convert_timezone`
- `expand_recurrence`
- `calculate_duration`
- `get_world_time`
- `server_info`

---

## 🐳 Docker

For running the server as an SSE (Server-Sent Events) endpoint.

**Build & Start:**

```bash
docker compose up --build
```

The server will listen on `http://localhost:9000/sse`.

See [docs/DOCKER.md](docs/DOCKER.md) for detailed commands.

---

## 🖥️ Client Configuration

Add the server to your MCP client configuration file.

### Claude Desktop

**Config Path:**

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "time-range-parser": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/time_range_parser",
        "python",
        "server_main.py"
      ]
    }
  }
}
```

### VS Code (Copilot) / Cursor

Add to `.vscode/mcp.json` or global config:

```json
{
  "mcpServers": {
    "time-range-parser": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/time_range_parser",
        "python",
        "server_main.py"
      ]
    }
  }
}
```

---

## 🧪 Testing & Verification

Before running tests, ensure project dependencies are installed (Hatch + `uv` env helper). From the project root run one of the following:

```bash
uv sync
# OR
pip install -e '.[dev]'
```

For convenience you can run the provided bootstrap script which runs the common setup steps for you:

```bash
# Make executable once:
chmod +x scripts/bootstrap.sh
# Then run:
./scripts/bootstrap.sh
```

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
uv run python examples/mcp_client_request.py
# OR
uv run python examples/mcp_client_httpx.py
```

This script connects to the running server, performs a handshake, lists tools, and runs a series of challenging test cases.

### 3. Manual Checks

**Quick Echo Check (Stdio):**

```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | uv run python server_main.py
```

**MCP Inspector:**

```bash
npx @modelcontextprotocol/inspector uv run python server_main.py
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

---

## 📄 License

MIT
