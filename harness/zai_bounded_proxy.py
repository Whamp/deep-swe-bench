#!/usr/bin/env python3
"""Account direct ZAI requests and limit only their simultaneous concurrency.

The proxy never records request or response content. It forwards only to the
fixed ZAI Coding Plan endpoint and writes compact request status, reasoning
controls, and usage data. Total requests are not limited.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ZAI_CODING_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
_HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class RequestConcurrencyLimit:
    """Limit simultaneous requests without imposing a total request cutoff."""

    def __init__(self, *, max_concurrency: int) -> None:
        if max_concurrency < 1:
            raise ValueError("request concurrency limit must be positive")
        self.max_concurrency = max_concurrency
        self._semaphore = threading.BoundedSemaphore(max_concurrency)
        self._lock = threading.Lock()
        self.requests_admitted = 0
        self.active_requests = 0
        self.peak_concurrency = 0

    @contextmanager
    def admit(self) -> Iterator[int]:
        with self._lock:
            self.requests_admitted += 1
            request_number = self.requests_admitted
        self._semaphore.acquire()
        with self._lock:
            self.active_requests += 1
            self.peak_concurrency = max(
                self.peak_concurrency,
                self.active_requests,
            )
        try:
            yield request_number
        finally:
            with self._lock:
                self.active_requests -= 1
            self._semaphore.release()


class CompactUsageLog:
    """Append content-free provider request and usage records."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, object]) -> None:
        with self._lock, self.path.open("a") as output:
            output.write(json.dumps(record, separators=(",", ":")) + "\n")


def _last_stream_usage(response_body: bytes) -> dict[str, object] | None:
    last_usage = None
    for line in response_body.splitlines():
        if not line.startswith(b"data:"):
            continue
        payload = line.removeprefix(b"data:").strip()
        if not payload or payload == b"[DONE]":
            continue
        try:
            event = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        usage = event.get("usage") if isinstance(event, dict) else None
        if isinstance(usage, dict):
            last_usage = usage
    return last_usage


def _json_usage(response_body: bytes) -> dict[str, object] | None:
    try:
        document = json.loads(response_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    usage = document.get("usage") if isinstance(document, dict) else None
    return usage if isinstance(usage, dict) else None


def extract_usage(response_body: bytes, content_type: str) -> dict[str, object] | None:
    """Extract only the final provider usage object from an SSE or JSON body."""
    if "text/event-stream" in content_type:
        return _last_stream_usage(response_body)
    return _json_usage(response_body)


def summarize_zai_request_thinking(path: Path) -> dict[str, int | bool]:
    """Separate tool-enabled executor requests from tool-free maintenance calls."""
    admitted_requests: list[dict[str, object]] = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict) and record.get("event") == "request_admitted":
                admitted_requests.append(record)
    executor_requests = [
        record
        for record in admitted_requests
        if isinstance(record.get("toolCount"), int) and record["toolCount"] > 0
    ]
    max_thinking_requests = [
        record
        for record in executor_requests
        if record.get("enableThinking") is True
        and record.get("reasoningEffort") is None
    ]
    return {
        "executor_requests": len(executor_requests),
        "executor_max_thinking_requests": len(max_thinking_requests),
        "executor_wire_max_thinking": bool(executor_requests)
        and len(max_thinking_requests) == len(executor_requests),
        "maintenance_requests": len(admitted_requests) - len(executor_requests),
    }


def aggregate_usage(path: Path) -> dict[str, int]:
    """Aggregate completed provider requests using pi-ai token semantics."""
    totals = {
        "requests": 0,
        "input": 0,
        "output": 0,
        "cache_read": 0,
        "cache_write": 0,
        "total_tokens": 0,
        "reasoning": 0,
    }
    if not path.exists():
        return totals
    for line in path.read_text().splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("event") != "request_completed":
            continue
        totals["requests"] += 1
        usage = record.get("usage")
        if not isinstance(usage, dict):
            continue
        prompt = int(usage.get("prompt_tokens") or 0)
        output = int(usage.get("completion_tokens") or 0)
        prompt_details = usage.get("prompt_tokens_details")
        if not isinstance(prompt_details, dict):
            prompt_details = {}
        cache_write = int(prompt_details.get("cache_write_tokens") or 0)
        reported_cached = int(
            prompt_details.get("cached_tokens")
            or usage.get("prompt_cache_hit_tokens")
            or 0
        )
        cache_read = (
            max(0, reported_cached - cache_write)
            if cache_write > 0
            else reported_cached
        )
        completion_details = usage.get("completion_tokens_details")
        if not isinstance(completion_details, dict):
            completion_details = {}
        totals["input"] += max(0, prompt - cache_read - cache_write)
        totals["output"] += output
        totals["cache_read"] += cache_read
        totals["cache_write"] += cache_write
        totals["reasoning"] += int(completion_details.get("reasoning_tokens") or 0)
        totals["total_tokens"] += prompt + output
    return totals


def make_server(
    *,
    host: str,
    port: int,
    upstream_base_url: str,
    usage_log_path: Path,
    max_concurrency: int,
) -> ThreadingHTTPServer:
    """Create a concurrency-limited proxy server for focused tests and runs."""
    request_limit = RequestConcurrencyLimit(max_concurrency=max_concurrency)
    usage_log = CompactUsageLog(usage_log_path)
    upstream_base_url = upstream_base_url.rstrip("/")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, _format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            if self.path != "/health":
                self.send_error(404)
                return
            payload = json.dumps(
                {
                    "ok": True,
                    "maxConcurrency": request_limit.max_concurrency,
                    "requestsAdmitted": request_limit.requests_admitted,
                    "peakConcurrency": request_limit.peak_concurrency,
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self) -> None:
            with request_limit.admit() as request_number:
                self._forward(request_number)

        def _forward(self, request_number: int) -> None:
            started = time.monotonic()
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            headers = {
                name: value
                for name, value in self.headers.items()
                if name.lower() not in _HOP_BY_HOP_HEADERS
            }
            # Keep SSE usage records readable without storing response content.
            headers["Accept-Encoding"] = "identity"
            try:
                request_document = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                request_document = {}
            if not isinstance(request_document, dict):
                request_document = {}
            tools = request_document.get("tools")
            usage_log.append(
                {
                    "event": "request_admitted",
                    "request": request_number,
                    "enableThinking": request_document.get("enable_thinking"),
                    "reasoningEffort": request_document.get("reasoning_effort"),
                    "toolCount": len(tools) if isinstance(tools, list) else 0,
                }
            )
            upstream_request = urllib.request.Request(
                f"{upstream_base_url}{self.path}",
                data=body,
                headers=headers,
                method="POST",
            )
            try:
                upstream = urllib.request.urlopen(upstream_request, timeout=1800)
            except urllib.error.HTTPError as error:
                upstream = error
            except (OSError, ValueError) as error:
                usage_log.append(
                    {
                        "event": "request_failed",
                        "request": request_number,
                        "durationMs": round((time.monotonic() - started) * 1000),
                        "errorType": type(error).__name__,
                    }
                )
                payload = json.dumps(
                    {
                        "error": {
                            "message": f"ZAI proxy transport failed: {type(error).__name__}",
                            "type": "proxy_transport_error",
                        }
                    }
                ).encode()
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return

            content_type = upstream.headers.get(
                "Content-Type", "application/octet-stream"
            )
            is_stream = "text/event-stream" in content_type
            self.send_response(upstream.status)
            for name, value in upstream.headers.items():
                if name.lower() not in _HOP_BY_HOP_HEADERS:
                    self.send_header(name, value)
            response_parts = []
            if not is_stream:
                response_body = upstream.read()
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                try:
                    self.wfile.write(response_body)
                except OSError:
                    # The provider call still counts if Prime Agent disconnects.
                    pass
            else:
                # HTTP/1.0 connection close frames the body while each SSE chunk
                # reaches Prime Agent immediately.
                self.end_headers()
                client_connected = True
                while chunk := upstream.read(64 * 1024):
                    response_parts.append(chunk)
                    if client_connected:
                        try:
                            self.wfile.write(chunk)
                            self.wfile.flush()
                        except OSError:
                            client_connected = False
                response_body = b"".join(response_parts)
            usage_log.append(
                {
                    "event": "request_completed",
                    "request": request_number,
                    "status": upstream.status,
                    "durationMs": round((time.monotonic() - started) * 1000),
                    "usage": extract_usage(response_body, content_type),
                }
            )

    server = ThreadingHTTPServer((host, port), Handler)
    server.request_concurrency_limit = request_limit  # type: ignore[attr-defined]
    return server


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--usage-log", type=Path, required=True)
    parser.add_argument("--max-concurrency", type=int, default=8)
    args = parser.parse_args()
    server = make_server(
        host=args.host,
        port=args.port,
        upstream_base_url=ZAI_CODING_BASE_URL,
        usage_log_path=args.usage_log,
        max_concurrency=args.max_concurrency,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
