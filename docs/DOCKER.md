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

### Start (without rebuild)
```bash
docker compose up
```

### Detached (in the background)
```bash
docker compose up -d
```

### Follow logs
```bash
docker compose logs -f
```

Only one service:
```bash
docker compose logs -f date-textparser-mcp
```

### Stop
```bash
docker compose down
```

### Stop + clean volumes
```bash
docker compose down -v
```

### Force rebuild (no cache)
```bash
docker compose build --no-cache
docker compose up
```

### Container status
```bash
docker compose ps
```

### Shell in container (debug)
```bash
docker compose exec date-textparser-mcp sh
```

---

## Health / Connectivity checks

### Check if server is listening (adjust port if needed)
```bash
curl -i http://localhost:9000/
```

### Open SSE endpoint (expect stream output)
```bash
curl -N http://localhost:9000/sse
```

Tip: stop with `CTRL+C`.

---

## MCP flow (SSE + messages)

MCP over SSE typically works like this:
1) Open SSE: `GET /sse`
2) Read `event: endpoint` → it contains the `/messages/?session_id=...` URL
3) POST JSON-RPC to that messages URL
4) Responses come back via the open SSE stream

### Open SSE and see endpoint
```bash
curl -N http://localhost:9000/sse
```

### Example: JSON-RPC initialize (POST to messages URL)
Replace `SESSION_ID` with what you get from the SSE `endpoint` event.

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

> Note: you often get `202 Accepted`. The actual response comes via SSE.

### Then: initialized notification (no id)
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

### "ModuleNotFoundError: No module named …"
- Check if your package is actually installed in the image (wheel/venv during build).
- Check your project layout (`src/<package_name>/__init__.py`).

### "ClosedResourceError" / responses not coming back
- SSE connection must remain open while you do POSTs.
- Always use the `messages` URL with the session_id that belongs to your SSE connection.

### Port changed?
- Host port (left) comes from `docker-compose.yml`, e.g. `9000:8000`
- Container port (right) is where the app listens.

---

## Cleanup (reclaim space)

### Clean up old images/containers
```bash
docker system prune
```

### Everything including unused images/volumes (careful)
```bash
docker system prune -a --volumes
```
```