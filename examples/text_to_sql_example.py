"""
Text-to-SQL Example - Demonstrates how the MCP server resolves time ranges for SQL queries.

IMPORTANT: This script requires the MCP server to be running first in SSE mode.

Start the server in a separate terminal:
    uv run python server_main.py --sse

Then run this example:
    uv run python examples/text_to_sql_example.py
    uv run python examples/text_to_sql_example.py "What was revenue last month?"
"""

import json
import sys
import os
from datetime import datetime

# Zorg dat we src/lib kunnen vinden
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from lib.mcp_sse_client import McpSseClient

# Configuratie
HOST = "localhost"
PORT = 9000
BASE_URL = f"http://{HOST}:{PORT}"


def process_query(client, user_query: str, now_iso: str | None = None):
    """
    Stuurt de user_query naar de MCP tool en toont de gegenereerde SQL.
    """
    print(f"\n👤 User: '{user_query}'")
    # We sturen de volledige query naar de tool. De parser probeert de tijd eruit te halen.
    print(f"🔌 Agent: Roept tool 'resolve_time_range' aan...")

    print(f"    (met now_iso={now_iso if now_iso else 'Server Default'})")

    arguments = {"text": user_query}
    if now_iso:
        arguments["now_iso"] = now_iso

    resp = client.request(
        "tools/call",
        {
            "name": "resolve_time_range",
            "arguments": arguments,
        },
        id=100,
    )

    # Verwerk resultaat
    result = client.extract_result(resp)

    if result is None:
        print(f"⚠️ Geen resultaat ontvangen.")
        return

    if isinstance(result, dict):
        # Check op RPC error
        if "code" in result and "message" in result:
            print(f"❌ RPC Error: {result}")
            return

        # Check op Tool error
        if "error" in result:
            print(f"❌ Server Error: {result['error']}")
            return

        # Happy path
        start_iso = result.get("start")
        end_iso = result.get("end")

        if start_iso and end_iso:
            print(f"✅ Server: {start_iso} t/m {end_iso}")

            # SQL Generatie
            sql = f"""
SELECT sum(amount)
FROM revenue
WHERE created_at BETWEEN '{start_iso}' AND '{end_iso}';
            """.strip()

            print(f"\n📄 Gegenereerde SQL:\n{'-'*30}\n{sql}\n{'-'*30}")
        else:
            print(f"⚠️ Onverwacht antwoord formaat: {json.dumps(result, indent=2)}")
    else:
        print(f"⚠️ Kon content niet parsen als JSON of onverwacht formaat: {result}")


def main():
    print(f"🤖 Text-to-SQL Agent Mock gestart...")

    if len(sys.argv) > 1:
        user_query = sys.argv[1]
    else:
        user_query = "Hoeveel omzet draaiden we vorig kwartaal?"

    try:
        # McpSseClient handelt de SSE connectie en handshake af in __enter__
        client = McpSseClient(BASE_URL)
        # Override SSE URL to point to /mcp/sse since the server mounts MCP at /mcp
        client.sse_url = f"{BASE_URL}/mcp/sse"

        with client:

            # 1. Initialize (Handshake)
            print("🔌 Initializing...")
            init_resp = client.request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "sql-agent", "version": "1.0"},
                },
                id=1,
            )

            if "error" in init_resp:
                print(f"❌ Init Error: {init_resp['error']}")
                return

            client.notify("notifications/initialized")

            # 2. Scenario's
            process_query(client, user_query)

    except Exception as e:
        print(f"❌ Error: {e}")
        if "httpx" in str(e) or "Connection refused" in str(e):
            print("💡 Check of de server draait en of 'httpx' geïnstalleerd is.")


if __name__ == "__main__":
    main()
