from __future__ import annotations

import json
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from harness.zai_bounded_proxy import (
    RequestBudget,
    RequestLimitExceeded,
    aggregate_usage,
    make_server,
    request_limit_was_exceeded,
)


def test_request_budget_rejects_request_65() -> None:
    budget = RequestBudget(max_requests=64, max_concurrency=8)

    for expected_request_number in range(1, 65):
        with budget.admit() as request_number:
            assert request_number == expected_request_number

    with pytest.raises(RequestLimitExceeded), budget.admit():
        pass


def test_request_budget_never_exceeds_eight_concurrent_requests() -> None:
    budget = RequestBudget(max_requests=64, max_concurrency=8)
    release = threading.Event()
    admitted = 0
    admitted_lock = threading.Lock()
    first_eight_admitted = threading.Event()

    def request() -> None:
        nonlocal admitted
        with budget.admit():
            with admitted_lock:
                admitted += 1
                if admitted == 8:
                    first_eight_admitted.set()
            release.wait(timeout=2)

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(request) for _ in range(16)]
        assert first_eight_admitted.wait(timeout=1)
        time.sleep(0.05)
        assert budget.active_requests == 8
        assert admitted == 8
        release.set()
        for future in futures:
            future.result(timeout=2)

    assert budget.peak_concurrency == 8
    assert budget.requests_admitted == 16


def test_proxy_forwards_sse_and_logs_only_compact_usage(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    class UpstreamHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *args: object) -> None:
            return

        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            captured.update({"body": body, "headers": dict(self.headers)})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"OK"}}]}\n\n')
            self.wfile.write(
                b'data: {"choices":[],"usage":{"prompt_tokens":3,'
                b'"completion_tokens":2,"total_tokens":5}}\n\n'
            )
            self.wfile.write(b"data: [DONE]\n\n")

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    usage_log = tmp_path / "usage.jsonl"
    proxy = make_server(
        host="127.0.0.1",
        port=0,
        upstream_base_url=f"http://127.0.0.1:{upstream.server_port}",
        usage_log_path=usage_log,
        max_requests=64,
        max_concurrency=8,
    )
    threads = [
        threading.Thread(target=upstream.serve_forever, daemon=True),
        threading.Thread(target=proxy.serve_forever, daemon=True),
    ]
    for thread in threads:
        thread.start()
    request_body = b'{"messages":[{"content":"secret-prompt-marker"}]}'
    request = urllib.request.Request(
        f"http://127.0.0.1:{proxy.server_port}/chat/completions",
        data=request_body,
        headers={
            "Authorization": "Bearer secret-key-marker",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        response_body = urllib.request.urlopen(request, timeout=2).read()
    finally:
        proxy.shutdown()
        upstream.shutdown()
        proxy.server_close()
        upstream.server_close()

    assert b'"content":"OK"' in response_body
    assert captured["body"] == request_body
    captured_headers = captured["headers"]
    assert isinstance(captured_headers, dict)
    assert captured_headers["Authorization"] == "Bearer secret-key-marker"
    assert captured_headers["Accept-Encoding"] == "identity"
    compact_log = usage_log.read_text()
    assert "secret-prompt-marker" not in compact_log
    assert "secret-key-marker" not in compact_log
    assert '"content":"OK"' not in compact_log
    assert aggregate_usage(usage_log)["total_tokens"] == 5


def test_aggregate_usage_uses_pi_ai_token_semantics(tmp_path: Path) -> None:
    log = tmp_path / "usage.jsonl"
    records = [
        {
            "event": "request_completed",
            "request": 1,
            "status": 200,
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "prompt_tokens_details": {
                    "cached_tokens": 30,
                    "cache_write_tokens": 10,
                },
                "completion_tokens_details": {"reasoning_tokens": 7},
            },
        },
        {
            "event": "request_completed",
            "request": 2,
            "status": 200,
            "usage": {
                "prompt_tokens": 40,
                "completion_tokens": 5,
            },
        },
        {"event": "request_rejected", "reason": "max_requests_exceeded"},
    ]
    log.write_text("".join(json.dumps(record) + "\n" for record in records))

    assert request_limit_was_exceeded(log) is True
    assert aggregate_usage(log) == {
        "requests": 2,
        "input": 110,
        "output": 25,
        "cache_read": 20,
        "cache_write": 10,
        "total_tokens": 165,
        "reasoning": 7,
    }
