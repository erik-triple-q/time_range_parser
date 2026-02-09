"""
MCP Client Test (using requests library) - Alternative SSE client implementation.

IMPORTANT: This script requires the MCP server to be running first in SSE mode.

Start the server in a separate terminal:
    uv run python server_main.py --sse

Then run this test:
    uv run python examples/mcp_client_request.py
"""

import json
import sys
import threading
import time

try:
    import requests
except ImportError:
    print("❌ Module 'requests' ontbreekt. Installeer met: uv add requests (of pip install requests)")
    sys.exit(1)

# Configuratie
HOST = "localhost"
PORT = 9000
BASE_URL = f"http://{HOST}:{PORT}"
SSE_URL = f"{BASE_URL}/mcp/sse"

def main():
    print(f"🔵 Starten van MCP flow test op {BASE_URL}...")
    
    # 1. Start SSE Listener in een aparte thread
    session_data = {"endpoint": None}
    stop_event = threading.Event()
    
    def listen_sse():
        try:
            print(f"🎧 Verbinden met SSE stream: {SSE_URL}")
            with requests.get(SSE_URL, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if stop_event.is_set():
                        break
                    
                    if line:
                        decoded = line.decode('utf-8')
                        
                        # MCP SSE format:
                        # event: endpoint
                        # data: /messages/?session_id=...
                        if decoded.startswith("data:") and "session_id=" in decoded:
                            endpoint = decoded.replace("data:", "").strip()
                            session_data["endpoint"] = endpoint
                            print(f"✅ Session Endpoint ontvangen: {endpoint}")
                        
                        # Print JSON-RPC responses
                        elif decoded.startswith("data:") and session_data["endpoint"]:
                            content = decoded.replace("data:", "").strip()
                            try:
                                data = json.loads(content)
                                print(f"\n📩 Response ontvangen:\n{json.dumps(data, indent=2)}")
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            print(f"❌ SSE Error: {e}")

    thread = threading.Thread(target=listen_sse, daemon=True)
    thread.start()

    # 2. Wacht op session ID
    print("⏳ Wachten op session ID...")
    timeout = 10
    start = time.time()
    while not session_data["endpoint"]:
        if time.time() - start > timeout:
            print("❌ Timeout: Geen session ID ontvangen.")
            stop_event.set()
            return
        time.sleep(0.1)

    messages_url = f"{BASE_URL}{session_data['endpoint']}"
    
    def send_rpc(method, params=None, req_id=None):
        payload = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if req_id is not None:
            payload["id"] = req_id
        print(f"📤 Sending {method} (id={req_id})...")
        try:
            requests.post(messages_url, json=payload).raise_for_status()
        except Exception as e:
            print(f"❌ POST Error: {e}")

    # 3. Voer de flow uit
    send_rpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "python-test", "version": "1.0"}
    }, req_id=1)
    
    time.sleep(0.5)
    send_rpc("notifications/initialized")
    
    time.sleep(0.5)
    send_rpc("tools/list", req_id=2)
    
    time.sleep(0.5)
    send_rpc("tools/call", {"name": "resolve_time_range", "arguments": {"text": "tussen maandag en woensdag"}}, req_id=3)
    
    time.sleep(0.5)
    send_rpc("tools/call", {
        "name": "convert_timezone", 
        "arguments": {"text": "15:00", "source_timezone": "Amsterdam", "target_timezone": "New York"}
    }, req_id=4)
    
    time.sleep(0.5)
    send_rpc("tools/call", {
        "name": "expand_recurrence", 
        "arguments": {"text": "elke 2 weken", "count": 3}
    }, req_id=5)
    
    time.sleep(0.5)
    send_rpc("tools/call", {
        "name": "calculate_duration", 
        "arguments": {"start": "vandaag", "end": "volgende week vrijdag"}
    }, req_id=6)
    
    # 20 Challenging test calls
    challenges = [
        "morgen half 3",                   # NL tijdnotatie
        "tussen maandag en woensdag",      # Dag range
        "van 22:00 tot 02:00",             # Midnight crossing
        "eerste maandag van maart",        # Ordinaal
        "Q3 2025",                         # Kwartaal
        "afgelopen jaar",                  # Verleden periode
        "pasen 2026",                      # Feestdag
        "next friday from 2 to 4 pm",      # Engels complex
        "3 dagen",                         # Duur
        "kwart voor 5",                    # NL tijdnotatie
        "vorig jaar",                      # Verleden
        "deze week",                       # Huidige periode
        "overmorgen 9 uur",                # Relatief + tijd
        "tussen 14:00 en 15:30",           # Range syntax
        "last friday",                     # Engels verleden
        "tweede kerstdag",                 # Feestdag
        "laatste vrijdag van de maand",    # Ordinaal relatief
        "van 9 tot 17 uur",                # Werkdag
        "komende donderdag",               # Relatief weekdag
        "15-03-2026"                       # Expliciet
    ]

    time.sleep(2)
    req_id = 10
    for text in challenges:
        send_rpc("tools/call", {
            "name": "resolve_time_range",
            "arguments": {"text": text}
        }, req_id=req_id)
        req_id += 1
        time.sleep(0.1)

    time.sleep(3)
    stop_event.set()
    print("🏁 Test klaar.")

if __name__ == "__main__":
    main()
