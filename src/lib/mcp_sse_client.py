from __future__ import annotations

import json
import logging
import queue
import threading
from dataclasses import dataclass
from typing import Any

import httpx

_LOGGER = logging.getLogger(__name__)


@dataclass
class JsonRpcResponse:
    id: int
    payload: dict[str, Any]


class McpSseClient:
    def __init__(
        self,
        base_url: str,
        connect_timeout: float = 15.0,
        post_timeout: float = 30.0,
    ):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse"
        self.connect_timeout = connect_timeout
        self.post_timeout = post_timeout
        self._client = httpx.Client(timeout=connect_timeout)

        self._messages_url: str | None = None
        self._rx_thread: threading.Thread | None = None
        self._stop = threading.Event()

        self._responses: dict[int, queue.Queue[dict[str, Any]]] = {}
        self._lock = threading.Lock()
        _LOGGER.info("McpSseClient initialized for %s", base_url)

    @property
    def messages_url(self) -> str:
        if not self._messages_url:
            raise RuntimeError("Not connected yet (messages_url unknown)")
        return self._messages_url

    def connect(self) -> None:
        """
        Start SSE reader thread and wait until we receive the session endpoint
        (messages URL with session_id).
        """
        if self._rx_thread and self._rx_thread.is_alive():
            return

        ready = threading.Event()
        err: list[BaseException] = []

        def rx():
            try:
                with self._client.stream(
                    "GET", self.sse_url, headers={"Accept": "text/event-stream"}
                ) as r:
                    r.raise_for_status()

                    event_type: str | None = None
                    data_lines: list[str] = []

                    for line in r.iter_lines():
                        if self._stop.is_set():
                            return
                        if line is None:
                            continue
                        line = line.strip("\r")

                        if line == "":
                            data = "\n".join(data_lines).strip()

                            if event_type == "endpoint":
                                # Handle endpoint event: tells us where to POST, incl session_id
                                if data and not self._messages_url:
                                    path = data
                                    if not path.startswith("/"):
                                        path = "/" + path
                                    self._messages_url = self.base_url + path
                                    _LOGGER.info(
                                        "Received messages endpoint: %s",
                                        self._messages_url,
                                    )
                                    ready.set()
                                # Reset event_type and data_lines for the next event
                                event_type = None
                                data_lines = []
                                continue  # Skip further processing for this event

                            # If it's not an endpoint event, try to parse as JSON-RPC response
                            # Often JSON-RPC responses are delivered as SSE "message" events,
                            # or as default events without an explicit 'event:' line.
                            if data:  # and (event_type is None or event_type == "message"): # More explicit check if needed
                                _LOGGER.debug(
                                    "Attempting to parse SSE data as JSON: %s", data
                                )
                                try:
                                    obj = json.loads(data)
                                    if (
                                        isinstance(obj, dict)
                                        and "id" in obj
                                        and isinstance(obj["id"], int)
                                    ):
                                        rpc_id = obj["id"]
                                        with self._lock:
                                            q = self._responses.get(rpc_id)
                                        if q:
                                            _LOGGER.debug(
                                                "Putting response for id=%d in queue",
                                                rpc_id,
                                            )
                                            q.put(obj)
                                except json.JSONDecodeError:
                                    _LOGGER.debug("SSE data was not JSON: %s", data)
                                except Exception:
                                    _LOGGER.warning(
                                        "Error processing SSE data: %s",
                                        data,
                                        exc_info=True,
                                    )

                            event_type = None
                            data_lines = []
                            continue

                        if line.startswith(":"):
                            continue
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            data_lines.append(line.split(":", 1)[1].lstrip())

            except httpx.HTTPStatusError as e:
                _LOGGER.error("SSE request failed: %s", e)
                err.append(e)
                ready.set()
            except Exception as e:
                _LOGGER.error("SSE reader failed: %s", e, exc_info=True)
                err.append(e)
                ready.set()

        _LOGGER.info("Starting SSE reader thread")
        self._rx_thread = threading.Thread(target=rx, daemon=True)
        self._rx_thread.start()

        if not ready.wait(self.connect_timeout):
            self.close()
            raise TimeoutError("Timed out waiting for endpoint event on /sse")

        if err:
            self.close()
            raise RuntimeError(f"SSE reader failed: {err[0]}") from err[0]

        if not self._messages_url:
            self.close()
            raise RuntimeError("Did not receive messages endpoint from SSE")

        _LOGGER.info("Connected successfully")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        _LOGGER.info("Closing connection")
        self._stop.set()
        try:
            self._client.close()
        except Exception:
            pass

    def _post(self, payload: dict[str, Any]) -> None:
        """
        POST a JSON-RPC message. For MCP-over-SSE, expect 202 Accepted with empty body.
        """
        _LOGGER.debug("POSTing to %s: %s", self.messages_url, payload)
        r = self._client.post(
            self.messages_url,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=self.post_timeout,
        )
        if r.status_code not in (200, 202):
            raise RuntimeError(
                f"POST failed: {r.status_code}\n"
                f"Content-Type: {r.headers.get('content-type')}\n"
                f"Body:\n{r.text}"
            )
        # ignore body; responses come via SSE

    def request(
        self,
        method: str,
        params: dict[str, Any] | None,
        *,
        id: int,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC request and wait for matching response id via SSE.
        """
        q: queue.Queue[dict[str, Any]] = queue.Queue()

        with self._lock:
            self._responses[id] = q

        try:
            _LOGGER.info("Sending request id=%d, method=%s", id, method)
            self._post(
                {"jsonrpc": "2.0", "id": id, "method": method, "params": params or {}}
            )

            try:
                resp = q.get(timeout=timeout_s)
                _LOGGER.info("Received response for id=%d", id)
                _LOGGER.debug("Response for id=%d: %s", id, resp)
            except queue.Empty:
                raise TimeoutError(f"No response for id={id} within {timeout_s}s")

            return resp
        finally:
            with self._lock:
                self._responses.pop(id, None)

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        """
        Send a JSON-RPC notification (no id). No response expected.
        """
        _LOGGER.info("Sending notification method=%s", method)
        self._post({"jsonrpc": "2.0", "method": method, "params": params or {}})
