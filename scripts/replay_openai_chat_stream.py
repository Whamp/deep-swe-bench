#!/usr/bin/env python3
"""Replay one OpenAI chat payload and retain bounded streaming evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_RESPONSE_SAMPLE_CHARS = 16_384
_REASONING_FIELDS = ("reasoning_content", "reasoning", "reasoning_text")


class _BoundedTextSample:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.first = ""
        self.last_chunks: deque[str] = deque()
        self.last_chars = 0
        self.total_chars = 0

    def append(self, text: str) -> None:
        self.total_chars += len(text)
        first_remaining = self.limit - len(self.first)
        if first_remaining > 0:
            self.first += text[:first_remaining]
        if not text:
            return
        self.last_chunks.append(text)
        self.last_chars += len(text)
        while self.last_chars > self.limit:
            excess = self.last_chars - self.limit
            first_chunk = self.last_chunks[0]
            if len(first_chunk) <= excess:
                self.last_chunks.popleft()
                self.last_chars -= len(first_chunk)
            else:
                self.last_chunks[0] = first_chunk[excess:]
                self.last_chars -= excess

    def last(self) -> str:
        return "".join(self.last_chunks)


@dataclass
class _OpenAIStreamState:
    assistant_char_limit: int
    sample: _BoundedTextSample = field(
        default_factory=lambda: _BoundedTextSample(_RESPONSE_SAMPLE_CHARS)
    )
    delta_char_counts: Counter[str] = field(default_factory=Counter)
    delta_event_counts: Counter[str] = field(default_factory=Counter)
    finish_reason: object = None
    stop_reason: object = None
    usage: object = field(default_factory=dict)

    def append(self, field_name: str, value: object) -> bool:
        if not isinstance(value, str) or not value:
            return False
        self.sample.append(value)
        self.delta_char_counts[field_name] += len(value)
        self.delta_event_counts[field_name] += 1
        return self.sample.total_chars > self.assistant_char_limit

    def result(self, classification: str) -> dict[str, Any]:
        return {
            "assistant_chars": self.sample.total_chars,
            "classification": classification,
            "delta_char_counts": dict(self.delta_char_counts),
            "delta_event_counts": dict(self.delta_event_counts),
            "finish_reason": self.finish_reason,
            "first_chars": self.sample.first,
            "last_chars": self.sample.last(),
            "stop_reason": self.stop_reason,
            "usage": self.usage if isinstance(self.usage, dict) else {},
        }


def _iter_openai_sse_chunks(
    lines: Iterable[bytes | str],
) -> Iterator[dict[str, Any] | None]:
    for raw_line in lines:
        line = (
            raw_line.decode("utf-8", errors="replace")
            if isinstance(raw_line, bytes)
            else raw_line
        ).strip()
        if not line or line.startswith(":") or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            yield None
            return
        chunk = json.loads(data)
        if isinstance(chunk, dict):
            yield chunk


def _append_tool_call_deltas(state: _OpenAIStreamState, delta: dict[str, Any]) -> bool:
    tool_calls = delta.get("tool_calls")
    if not isinstance(tool_calls, list):
        return False
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue
        function = tool_call.get("function")
        if not isinstance(function, dict):
            continue
        if state.append("tool_name", function.get("name")):
            return True
        if state.append("tool_arguments", function.get("arguments")):
            return True
    return False


def consume_openai_chat_stream(
    lines: Iterable[bytes | str],
    *,
    assistant_char_limit: int,
) -> dict[str, Any]:
    """Consume OpenAI SSE lines and classify completion or bounded runaway."""
    if assistant_char_limit <= 0:
        raise ValueError("OpenAI replay: assistant character limit must be positive")
    state = _OpenAIStreamState(assistant_char_limit)
    for chunk in _iter_openai_sse_chunks(lines):
        if chunk is None:
            return state.result("completed")
        if isinstance(chunk.get("usage"), dict):
            state.usage = chunk["usage"]
        choices = chunk.get("choices")
        if (
            not isinstance(choices, list)
            or not choices
            or not isinstance(choices[0], dict)
        ):
            continue
        choice = choices[0]
        if choice.get("finish_reason") is not None:
            state.finish_reason = choice.get("finish_reason")
        if choice.get("stop_reason") is not None:
            state.stop_reason = choice.get("stop_reason")
        delta = choice.get("delta")
        if not isinstance(delta, dict):
            continue
        limit_reached = False
        for field_name in _REASONING_FIELDS:
            if state.append(field_name, delta.get(field_name)):
                limit_reached = True
            if isinstance(delta.get(field_name), str) and delta[field_name]:
                break
        if limit_reached:
            return state.result("assistant_char_limit")
        if state.append("content", delta.get("content")):
            return state.result("assistant_char_limit")
        if _append_tool_call_deltas(state, delta):
            return state.result("assistant_char_limit")
    return state.result("stream_ended_without_done")


def _write_private_json(path: Path, value: object) -> tuple[int, str]:
    encoded = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_bytes(encoded)
    temporary_path.chmod(0o600)
    temporary_path.replace(path)
    return len(encoded), hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--assistant-char-limit", type=int, default=180_000)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--api-key-env")
    args = parser.parse_args()

    request_payload = json.loads(args.request.read_text())
    request_payload.pop("return_prompt_text", None)
    request_payload["stream"] = True
    request_payload["stream_options"] = {"include_usage": True}
    if args.max_tokens is not None:
        if args.max_tokens <= 0:
            parser.error("--max-tokens must be positive")
        request_payload["max_tokens"] = args.max_tokens
    encoded_request = json.dumps(
        request_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    headers = {"Content-Type": "application/json"}
    if args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            raise SystemExit(f"OpenAI replay: {args.api_key_env} is not set")
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        args.endpoint,
        data=encoded_request,
        headers=headers,
        method="POST",
    )
    started = time.monotonic()
    result: dict[str, Any]
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            result = consume_openai_chat_stream(
                response,
                assistant_char_limit=args.assistant_char_limit,
            )
            result["http_status"] = response.status
    except urllib.error.HTTPError as error:
        body = error.read(16_384).decode("utf-8", errors="replace")
        result = {
            "classification": "http_error",
            "http_status": error.code,
            "response_body": body,
        }
    result.update(
        {
            "elapsed_s": round(time.monotonic() - started, 3),
            "endpoint": args.endpoint,
            "request_bytes": len(encoded_request),
            "request_sha256": hashlib.sha256(encoded_request).hexdigest(),
        }
    )
    byte_count, sha256 = _write_private_json(args.output, result)
    print(
        json.dumps(
            {
                "bytes": byte_count,
                "classification": result["classification"],
                "output": str(args.output),
                "sha256": sha256,
            },
            sort_keys=True,
        )
    )
    return 0 if result["classification"] == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
