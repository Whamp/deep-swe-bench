from __future__ import annotations

import json
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from harness.zai_bounded_proxy import (
    RequestConcurrencyLimit,
    aggregate_usage,
    make_server,
    summarize_zai_request_thinking,
)


def test_request_concurrency_limit_allows_more_than_64_requests() -> None:
    limit = RequestConcurrencyLimit(max_concurrency=8)

    for expected_request_number in range(1, 130):
        with limit.admit() as request_number:
            assert request_number == expected_request_number


def test_request_concurrency_limit_never_exceeds_eight_requests() -> None:
    limit = RequestConcurrencyLimit(max_concurrency=8)
    release = threading.Event()
    admitted = 0
    admitted_lock = threading.Lock()
    first_eight_admitted = threading.Event()

    def request() -> None:
        nonlocal admitted
        with limit.admit():
            with admitted_lock:
                admitted += 1
                if admitted == 8:
                    first_eight_admitted.set()
            release.wait(timeout=2)

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(request) for _ in range(16)]
        assert first_eight_admitted.wait(timeout=1)
        time.sleep(0.05)
        assert limit.active_requests == 8
        assert admitted == 8
        release.set()
        for future in futures:
            future.result(timeout=2)

    assert limit.peak_concurrency == 8
    assert limit.requests_admitted == 16


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
        max_concurrency=8,
    )
    threads = [
        threading.Thread(target=upstream.serve_forever, daemon=True),
        threading.Thread(target=proxy.serve_forever, daemon=True),
    ]
    for thread in threads:
        thread.start()
    request_body = (
        b'{"model":"glm-5.2","enable_thinking":true,'
        b'"messages":[{"content":"secret-prompt-marker"}],'
        b'"tools":[{"type":"function","function":{"name":"ipython"}}]}'
    )
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
    assert summarize_zai_request_thinking(usage_log) == {
        "executor_requests": 1,
        "executor_max_thinking_requests": 1,
        "executor_wire_max_thinking": True,
        "maintenance_requests": 0,
    }
    admitted = json.loads(usage_log.read_text().splitlines()[0])
    assert admitted == {
        "event": "request_admitted",
        "request": 1,
        "enableThinking": True,
        "reasoningEffort": None,
        "toolCount": 1,
    }


def test_thinking_summary_excludes_non_reasoning_maintenance_calls(
    tmp_path: Path,
) -> None:
    log = tmp_path / "usage.jsonl"
    records = [
        {
            "event": "request_admitted",
            "request": 1,
            "enableThinking": True,
            "reasoningEffort": None,
            "toolCount": 1,
        },
        {
            "event": "request_admitted",
            "request": 2,
            "enableThinking": False,
            "reasoningEffort": None,
            "toolCount": 0,
        },
    ]
    log.write_text("".join(json.dumps(record) + "\n" for record in records))

    assert summarize_zai_request_thinking(log) == {
        "executor_requests": 1,
        "executor_max_thinking_requests": 1,
        "executor_wire_max_thinking": True,
        "maintenance_requests": 1,
    }


def test_thinking_summary_rejects_non_reasoning_executor_calls(tmp_path: Path) -> None:
    log = tmp_path / "usage.jsonl"
    record = {
        "event": "request_admitted",
        "request": 1,
        "enableThinking": False,
        "reasoningEffort": None,
        "toolCount": 1,
    }
    log.write_text(json.dumps(record) + "\n")

    assert summarize_zai_request_thinking(log)["executor_wire_max_thinking"] is False


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
    ]
    log.write_text("".join(json.dumps(record) + "\n" for record in records))

    assert aggregate_usage(log) == {
        "requests": 2,
        "input": 110,
        "output": 25,
        "cache_read": 20,
        "cache_write": 10,
        "total_tokens": 165,
        "reasoning": 7,
    }
