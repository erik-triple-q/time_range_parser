import json
import sys
import threading
import time

try:
    import requests
except ImportError:
    print("❌ Module 'requests' ontbreekt. Installeer met: uv add requests")
    sys.exit(1)

# Configuratie
HOST = "localhost"
PORT = 9000
BASE_URL = f"http://{HOST}:{PORT}"
SSE_URL = f"{BASE_URL}/sse"

# Shared state om het resultaat van de server op te vangen
state = {
    "endpoint": None,
    "latest_result": None,
    "stop_event": threading.Event()
}

def listen_sse():
    """Luistert naar SSE events en vangt JSON-RPC responses op."""
    try:
        with requests.get(SSE_URL, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if state["stop_event"].is_set():
                    break
                if line:
                    decoded = line.decode('utf-8')
                    
                    if decoded.startswith("data:") and "session_id=" in decoded:
                        state["endpoint"] = decoded.replace("data:", "").strip()
                    
                    elif decoded.startswith("data:") and state["endpoint"]:
                        content = decoded.replace("data:", "").strip()
                        try:
                            data = json.loads(content)
                            # Als het een resultaat is van onze tool call
                            if "result" in data:
                                state["latest_result"] = data["result"]
                        except json.JSONDecodeError:
                            pass
    except Exception:
        pass

def main():
    print(f"🤖 Text-to-SQL Agent Mock gestart...")
    
    # 1. Start verbinding
    thread = threading.Thread(target=listen_sse, daemon=True)
    thread.start()

    # Wacht op sessie
    timeout = 5
    start = time.time()
    while not state["endpoint"]:
        if time.time() - start > timeout:
            print("❌ Geen verbinding met server. Draait 'uv run python server_main.py'?")
            return
        time.sleep(0.1)

    messages_url = f"{BASE_URL}{state['endpoint']}"
    
    def send_rpc(method, params=None, req_id=None):
        payload = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if req_id: payload["id"] = req_id
        requests.post(messages_url, json=payload)

    # Handshake
    send_rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "sql-agent", "version": "1.0"}}, 1)
    send_rpc("notifications/initialized")
    time.sleep(0.5)

    # 2. Scenario
    user_query = "Hoeveel omzet draaiden we vorig kwartaal?"
    extracted_time = "vorig kwartaal"
    
    print(f"\n👤 User: '{user_query}'")
    print(f"🧠 LLM: Tijdsaanduiding herkend: '{extracted_time}'")
    print(f"🔌 LLM: Roept tool 'resolve_time_range' aan...")

    # 3. Tool Call
    send_rpc("tools/call", {
        "name": "resolve_time_range",
        "arguments": {
            "text": extracted_time,
            "now_iso": "2026-01-01T12:00:00"  # Fixed reference time for deterministic SQL
        }
    }, req_id=100)

    # Wacht op antwoord
    time.sleep(1)
    
    if state["latest_result"]:
        # Parse het resultaat (MCP geeft content list terug)
        content_json = state["latest_result"]["content"][0]["text"]
        time_data = json.loads(content_json)
        
        if "error" in time_data:
            print(f"❌ Server Error: {time_data['error']}")
            if "Invalid unit" in str(time_data['error']) and "quarter" in str(time_data['error']):
                print("\n💡 OORZAAK: De server draait nog oude code.")
                print("   De fix voor 'quarter' staat wel op schijf, maar is nog niet geladen.")
                print("   👉 Herstart je server proces (server_main.py of docker).")
        else:
            start_iso = time_data.get("start")
            end_iso = time_data.get("end")
            
            if start_iso and end_iso:
                print(f"✅ Server: {start_iso} t/m {end_iso}")
                
                # 4. SQL Generatie
                sql = f"""
SELECT sum(amount) 
FROM revenue 
WHERE created_at BETWEEN '{start_iso}' AND '{end_iso}';
                """.strip()
                
                print(f"\n📄 Gegenereerde SQL:\n{'-'*30}\n{sql}\n{'-'*30}")
            else:
                print(f"⚠️ Onverwacht antwoord formaat: {json.dumps(time_data, indent=2)}")
    else:
        print("❌ Geen antwoord ontvangen van server.")

    state["stop_event"].set()

if __name__ == "__main__":
    main()