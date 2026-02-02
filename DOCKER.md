# Date TextParser MCP — Handy Commands

This file contains the most used commands for development, Docker, and quick checks.

---

## Prerequisites (Local)
- Docker Desktop + `docker compose`
- (Optional) Python 3.12+ for running locally without Docker

---

## Docker / Compose

### Build + Start
```bash
docker compose up --build
```

### Start (zonder rebuild)
```bash
docker compose up
```

### Detached (op de achtergrond)
```bash
docker compose up -d
```

### Logs volgen
```bash
docker compose logs -f
```

Alleen één service:
```bash
docker compose logs -f date-textparser-mcp
```

### Stoppen
```bash
docker compose down
```

### Stoppen + volumes opruimen
```bash
docker compose down -v
```

### Force rebuild (geen cache)
```bash
docker compose build --no-cache
docker compose up
```

### Container status
```bash
docker compose ps
```

### Shell in de container (debug)
```bash
docker compose exec date-textparser-mcp sh
```

---

## Health / Connectivity checks

### Check of de server luistert (pas poort aan indien nodig)
```bash
curl -i http://localhost:9000/
```

### SSE endpoint openzetten (verwacht stream output)
```bash
curl -N http://localhost:9000/sse
```

Tip: stop met `CTRL+C`.

---

## MCP flow (SSE + messages)

MCP over SSE werkt typisch zo:
1) Open SSE: `GET /sse`
2) Lees `event: endpoint` → daar staat de `/messages/?session_id=...` URL
3) POST JSON-RPC naar die messages URL
4) Responses komen terug via de open SSE stream

### SSE openen en endpoint zien
```bash
curl -N http://localhost:9000/sse
```

### Voorbeeld: JSON-RPC initialize (POST naar messages URL)
Vervang `SESSION_ID` met wat je uit het SSE `endpoint` event krijgt.

```bash
curl -i \
  -H "Content-Type: application/json" \
  -X POST "http://localhost:9000/messages/?session_id=SESSION_ID" \
  -d '{
    "jsonrpc":"2.0",
    "id": 1,
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "clientInfo":{"name":"curl","version":"0.1.0"}
    }
  }'
```

> Let op: vaak krijg je `202 Accepted`. De echte response komt via SSE.

### Daarna: initialized notification (geen id)
```bash
curl -i \
  -H "Content-Type: application/json" \
  -X POST "http://localhost:9000/messages/?session_id=SESSION_ID" \
  -d '{
    "jsonrpc":"2.0",
    "method":"notifications/initialized",
    "params":{}
  }'
```

### Tools list
```bash
curl -i \
  -H "Content-Type: application/json" \
  -X POST "http://localhost:9000/messages/?session_id=SESSION_ID" \
  -d '{
    "jsonrpc":"2.0",
    "id": 2,
    "method":"tools/list",
    "params":{}
  }'
```

### Tool call (voorbeeld)
```bash
curl -i \
  -H "Content-Type: application/json" \
  -X POST "http://localhost:9000/messages/?session_id=SESSION_ID" \
  -d '{
    "jsonrpc":"2.0",
    "id": 3,
    "method":"tools/call",
    "params":{
      "name":"resolve_time_range",
      "arguments":{"text":"tussen maandag en woensdag","tz":"Europe/Amsterdam"}
    }
  }'
```

---

## Debugging / Troubleshooting

### “ModuleNotFoundError: No module named …”
- Check of je package echt geïnstalleerd wordt in de image (wheel/venv tijdens build).
- Check je project layout (`src/<package_name>/__init__.py`).

### “ClosedResourceError” / responses komen niet terug
- SSE verbinding moet open blijven terwijl je POSTs doet.
- Gebruik altijd de `messages` URL met de session_id die bij jouw SSE connectie hoort.

### Poort gewijzigd?
- Host-poort (links) komt uit `docker-compose.yml`, bv. `9000:8000`
- Container-poort (rechts) is waar de app luistert.

---

## Cleanup (ruimte terugwinnen)

### Oude images/containers opruimen
```bash
docker system prune
```

### Alles inclusief ongebruikte images/volumes (voorzichtig)
```bash
docker system prune -a --volumes
```
```