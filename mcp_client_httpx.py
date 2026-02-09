from __future__ import annotations

import json
import time
from typing import Any
import sys
import os
import httpx

from mcp_sse_client import McpSseClient

BASE_URL = "http://localhost:9000/mcp"
SSE_URL = f"{BASE_URL}/sse"  # This is for reference; McpSseClient uses BASE_URL


class MarkdownReporter:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def header(self, level: int, text: str) -> None:
        self.lines.append(f"{'#' * level} {text}")
        self.lines.append("")

    def text(self, text: str) -> None:
        self.lines.append(text)
        self.lines.append("")

    def code_block(self, code: str, lang: str = "json") -> None:
        self.lines.append(f"```{lang}")
        self.lines.append(code)
        self.lines.append("```")
        self.lines.append("")

    def tool_call(
        self, tool_name: str, arguments: dict[str, Any], response: dict[str, Any]
    ) -> None:
        # Determine a label for the test case
        if "text" in arguments:
            self.lines.append(f"**Input**: `{arguments['text']}`")
        elif "start_text" in arguments:
            self.lines.append(f"**Input**: `{arguments['start_text']}`")
        elif "start" in arguments:
            self.lines.append(f"**Input**: `{arguments['start']}`")
        else:
            self.lines.append(f"**Tool**: `{tool_name}`")

        # Format arguments nicely
        args_str = ", ".join(f"`{k}={v}`" for k, v in arguments.items())
        self.lines.append(f"- **Arguments**: {args_str}")

        if "result" in response:
            result = response["result"]

            # Try to parse inner content if it exists (Standard MCP)
            content_data = None
            if "content" in result and isinstance(result["content"], list):
                for item in result["content"]:
                    if item.get("type") == "text":
                        try:
                            content_data = json.loads(item["text"])
                            break
                        except (json.JSONDecodeError, TypeError):
                            pass

            if content_data:
                if "error" in content_data:
                    self.lines.append(
                        '- <span style="color:red;">**Tool Error**</span>:'
                    )
                    self.code_block(json.dumps(content_data, indent=2))
                else:
                    # Pretty print the parsed JSON from the tool
                    self.lines.append("- **Result**:")
                    self.code_block(json.dumps(content_data, indent=2))
            else:
                # Fallback
                self.lines.append("- **Raw Result**:")
                self.code_block(json.dumps(result, indent=2))

        elif "error" in response:
            self.lines.append('- <span style="color:red;">**RPC Error**</span>:')
            self.code_block(json.dumps(response["error"], indent=2))
        else:
            self.lines.append("- **Unknown Response**:")
            self.code_block(json.dumps(response, indent=2))

        self.lines.append("---")
        self.lines.append("")

    def print_report(self) -> None:
        print("\n".join(self.lines))


def run_and_report_calls(
    reporter: MarkdownReporter,
    mcp_client: McpSseClient,
    req_id_counter: list[int],
    tool_name: str,
    calls: list[str | dict[str, Any]],
    section_header: str,
) -> None:
    """Helper to run a list of tool calls and add them to the report."""
    reporter.header(3, section_header)
    for call_info in calls:
        if isinstance(call_info, str):
            arguments = {"text": call_info}
        else:
            arguments = call_info

        resp = mcp_client.request(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
            id=req_id_counter[0],
        )
        req_id_counter[0] += 1
        reporter.tool_call(tool_name, arguments, resp)
        time.sleep(0.1)


def main() -> None:
    reporter = MarkdownReporter()
    reporter.header(1, "MCP Client Test Report")
    reporter.text(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 0. Health Check
    reporter.header(2, "0. Health Check")
    # Derive root URL from BASE_URL which is http://.../mcp
    root_url = BASE_URL.removesuffix("/mcp")
    health_url = f"{root_url}/health"
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(health_url)
            r.raise_for_status()
            health_data = r.json()
            reporter.text(f"✅ Health check passed: `{health_url}`")
            reporter.code_block(json.dumps(health_data, indent=2))
    except Exception as e:
        reporter.text(f"❌ Health check failed for `{health_url}`:")
        reporter.code_block(str(e), lang="text")

    try:
        c = McpSseClient(BASE_URL)
        c.connect()
        reporter.text(f"✅ Connected to `{BASE_URL}`")
    except (RuntimeError, TimeoutError) as e:
        reporter.text(f"❌ Connection failed: {e}")
        reporter.print_report()
        return

    req_id_counter = [1]  # Use a list to make it mutable across functions

    # 1) Initialize
    reporter.header(2, "1. Initialization")
    init_resp = c.request(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-client-httpx", "version": "0.2.0"},
        },
        id=req_id_counter[0],
    )
    req_id_counter[0] += 1

    server_info = init_resp.get("result", {}).get("serverInfo", {})
    reporter.text(f"- **Server Name**: `{server_info.get('name', 'unknown')}`")
    reporter.text(f"- **Server Version**: `{server_info.get('version', 'unknown')}`")

    # 2) Notify initialized
    c.notify("notifications/initialized", {})

    # 3) List tools
    reporter.header(2, "2. Available Tools")
    tools_resp = c.request("tools/list", {}, id=req_id_counter[0])
    req_id_counter[0] += 1

    tools = tools_resp.get("result", {}).get("tools", [])
    if tools:
        for t in tools:
            reporter.text(
                f"- **{t['name']}**: {t.get('description', 'No description')}"
            )
    else:
        reporter.text("No tools found.")

    # --- Group tests by tool and then by test file ---

    # 4) Tool: resolve_time_range
    reporter.header(2, "3. Tool: `resolve_time_range`")

    tests_time_range_parser = [
        "morgen",
        "morgen 15:00",
        "van 10:00 tot 12:30",
        "tussen maandag en woensdag",
        "volgende week",
        "2025-11-01",
        "5 januari 2026",
        "morgen 2 uur",
        "van 22:00 tot 02:00",
        "half 10",
        "vorig jaar",
        "tomorrow",
        "1st of march",
        "29 februari",  # Leap year
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "resolve_time_range",
        tests_time_range_parser,
        "From `test_time_range_parser.py`",
    )

    tests_quarters_and_past = [
        "Q1",
        "Q4 2025",
        "eerste kwartaal",
        "afgelopen jaar",
        "vorige maand",
        "afgelopen week",
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "resolve_time_range",
        tests_quarters_and_past,
        "From `test_quarters_and_past_periods.py`",
    )

    tests_vague_and_periods = [
        "straks",
        "vanavond",
        "zomer 2026",
        "week 42",
        "H1",
        "dit weekend",
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "resolve_time_range",
        tests_vague_and_periods,
        "From `test_vague_and_periods.py`",
    )

    tests_holidays = [
        "pasen 2026",
        "goede vrijdag",
        "hemelvaartsdag",
        "eerste maandag van maart",
        "laatste vrijdag van de maand",
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "resolve_time_range",
        tests_holidays,
        "From `test_holidays.py`",
    )

    tests_coverage_gaps = [
        "morgenochtend",
        "binnenkort",
        "begin januari 2026",
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "resolve_time_range",
        tests_coverage_gaps,
        "From `test_coverage_gaps.py`",
    )

    # 5) Tool: expand_recurrence
    reporter.header(2, "4. Tool: `expand_recurrence`")
    tests_recurrence = [
        {"text": "elke vrijdag", "count": 3},
        {"text": "dagelijks", "count": 3},
        {"text": "elke 2 weken", "count": 3},
        {"text": "maandelijks", "count": 2},
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "expand_recurrence",
        tests_recurrence,
        "From `test_recurrence.py`",
    )

    # 6) Tool: calculate_duration
    reporter.header(2, "5. Tool: `calculate_duration`")
    tests_duration = [
        {"start": "vandaag", "end": "volgende vrijdag"},
        {"start": "vandaag", "end": "dinsdag"},
        {"start": "13:00", "end": "16:30"},
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "calculate_duration",
        tests_duration,
        "From `test_duration.py`",
    )

    # 7) Tool: convert_timezone
    reporter.header(2, "6. Tool: `convert_timezone`")
    tests_timezone = [
        {
            "text": "15:00",
            "source_timezone": "Amsterdam",
            "target_timezone": "New York",
        },
        {"text": "12:00", "source_timezone": "London", "target_timezone": "Tokyo"},
        {
            "text": "22:00",
            "source_timezone": "cairo",
            "target_timezone": "sydney",
        },
        {"text": "now", "source_timezone": "UTC", "target_timezone": "kolkata"},
        {
            "text": "12:00",
            "source_timezone": "Amsterdam",
            "target_timezone": "Mars/City",
        },
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "convert_timezone",
        tests_timezone,
        "From `test_timezone_conversion.py`",
    )

    # 8) Tool: server_info
    reporter.header(2, "7. Tool: `server_info`")
    run_and_report_calls(
        reporter, c, req_id_counter, "server_info", [{}], "Server Metadata"
    )

    # 9) Deterministic Tests (now_iso)
    reporter.header(2, "8. Deterministic Tests (`now_iso`)")
    tests_now_iso = [
        {
            "text": "morgen",
            "now_iso": "2026-01-01T12:00:00",
        },
        {
            "text": "vorig kwartaal",
            "now_iso": "2026-01-01T12:00:00",
        },
    ]
    run_and_report_calls(
        reporter,
        c,
        req_id_counter,
        "resolve_time_range",
        tests_now_iso,
        "Fixed Reference Time (2026-01-01)",
    )

    c.close()
    reporter.print_report()


if __name__ == "__main__":
    main()
