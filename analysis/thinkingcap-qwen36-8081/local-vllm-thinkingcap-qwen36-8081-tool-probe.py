#!/usr/bin/env python3
"""Validate ThinkingCap tool calls and reasoning replay on server60 port 8081."""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.response
from typing import Any

ENDPOINT = "http://100.92.238.117:8081/v1/chat/completions"
MODEL = "thinkingcap-qwen3.6-27b-awq-int4"
MAX_OUTPUT_TOKENS = 98_304
REQUEST_TIMEOUT_SECONDS = 900
SAMPLING = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 20,
    "min_p": 0.0,
    "repetition_penalty": 1.0,
}
CHAT_TEMPLATE_KWARGS = {
    "enable_thinking": True,
    "preserve_thinking": True,
}
RECORD_PROBE_TOOL = {
    "type": "function",
    "function": {
        "name": "record_probe",
        "description": "Record one exact tool-calling validation payload.",
        "parameters": {
            "type": "object",
            "properties": {
                "round": {"type": "integer"},
                "payload": {"type": "string"},
            },
            "required": ["round", "payload"],
            "additionalProperties": False,
        },
    },
}


def emit_probe_record(record: dict[str, Any]) -> None:
    """Write one compact tool-probe record as NDJSON."""
    print(json.dumps(record, ensure_ascii=False, separators=(",", ":")), flush=True)


def build_probe_payload(
    messages: list[dict[str, Any]], *, stream: bool
) -> dict[str, Any]:
    """Build the exact local-vLLM request contract under validation."""
    return {
        "model": MODEL,
        "messages": messages,
        "tools": [RECORD_PROBE_TOOL],
        "tool_choice": "auto",
        "stream": stream,
        "stream_options": {"include_usage": True} if stream else None,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "chat_template_kwargs": CHAT_TEMPLATE_KWARGS,
        **SAMPLING,
    }


def post_probe_request(payload: dict[str, Any]) -> urllib.response.addinfourl:
    """Send one JSON request to the exact server60 ThinkingCap endpoint."""
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS)


def extract_reasoning_text(message: dict[str, Any]) -> tuple[str, str | None]:
    """Read the first non-empty reasoning field supported by Pi's OpenAI adapter."""
    for field in ("reasoning_content", "reasoning", "reasoning_text"):
        value = message.get(field)
        if isinstance(value, str) and value:
            return value, field
    return "", None


def require_tool_function(tool_call: dict[str, Any]) -> dict[str, Any]:
    """Require the OpenAI-compatible function object inside a tool call."""
    function = tool_call.get("function")
    if not isinstance(function, dict):
        raise TypeError("ThinkingCap tool probe: function object was missing")
    return function


def decode_function_arguments(tool_call: dict[str, Any]) -> dict[str, Any]:
    """Decode and require a non-empty OpenAI-compatible function argument object."""
    raw_arguments = require_tool_function(tool_call).get("arguments")
    if not isinstance(raw_arguments, str) or not raw_arguments.strip():
        raise AssertionError("ThinkingCap tool probe: function arguments were empty")
    arguments = json.loads(raw_arguments)
    if not isinstance(arguments, dict) or not arguments:
        raise AssertionError(
            "ThinkingCap tool probe: function arguments were not an object"
        )
    return arguments


def assert_tool_response(
    message: dict[str, Any],
    finish_reason: Any,
    expected_arguments: dict[str, Any],
) -> dict[str, Any]:
    """Fail closed on malformed, raw, empty, duplicated, or unexpected tool calls."""
    reasoning_text, _ = extract_reasoning_text(message)
    visible_text = "\n".join(
        value
        for value in (reasoning_text, message.get("content"))
        if isinstance(value, str)
    )
    if "<tool_call" in visible_text:
        raise AssertionError("ThinkingCap tool probe: raw <tool_call> leaked into text")
    if finish_reason != "tool_calls":
        raise AssertionError(
            f"ThinkingCap tool probe: finish_reason was {finish_reason!r}, not 'tool_calls'"
        )
    tool_calls = message.get("tool_calls")
    if not isinstance(tool_calls, list) or len(tool_calls) != 1:
        raise AssertionError(
            f"ThinkingCap tool probe: expected one tool call, received {tool_calls!r}"
        )
    tool_call = tool_calls[0]
    if not isinstance(tool_call, dict):
        raise TypeError("ThinkingCap tool probe: tool call was not an object")
    if require_tool_function(tool_call).get("name") != "record_probe":
        raise AssertionError(
            f"ThinkingCap tool probe: unexpected tool name in {tool_call!r}"
        )
    arguments = decode_function_arguments(tool_call)
    if arguments != expected_arguments:
        raise AssertionError(
            f"ThinkingCap tool probe: arguments {arguments!r} != {expected_arguments!r}"
        )
    return tool_call


def run_streamed_tool_probe() -> None:
    """Require one streamed tool call with JSON-decodable exact arguments."""
    expected_arguments = {"round": 0, "payload": "streamed tool call"}
    payload = build_probe_payload(
        [
            {
                "role": "user",
                "content": (
                    'Call record_probe exactly once with round=0 and payload="streamed tool '
                    'call". Do not answer in prose.'
                ),
            }
        ],
        stream=True,
    )
    tool_call_chunks: dict[int, dict[str, Any]] = {}
    reasoning_parts: list[str] = []
    reasoning_field: str | None = None
    content_parts: list[str] = []
    finish_reason: Any = None
    usage: dict[str, Any] | None = None

    with post_probe_request(payload) as response:
        for raw_line in response:
            line = raw_line.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            event = json.loads(line.removeprefix("data: "))
            if isinstance(event.get("usage"), dict):
                usage = event["usage"]
            choices = event.get("choices") or []
            if not choices:
                continue
            choice = choices[0]
            if choice.get("finish_reason") is not None:
                finish_reason = choice["finish_reason"]
            delta = choice.get("delta") or {}
            delta_reasoning, delta_reasoning_field = extract_reasoning_text(delta)
            if delta_reasoning:
                reasoning_parts.append(delta_reasoning)
                reasoning_field = reasoning_field or delta_reasoning_field
            if isinstance(delta.get("content"), str):
                content_parts.append(delta["content"])
            for chunk in delta.get("tool_calls") or []:
                index = chunk.get("index", 0)
                aggregate = tool_call_chunks.setdefault(
                    index,
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    },
                )
                if isinstance(chunk.get("id"), str):
                    aggregate["id"] += chunk["id"]
                function_chunk = chunk.get("function") or {}
                if isinstance(function_chunk.get("name"), str):
                    aggregate["function"]["name"] += function_chunk["name"]
                if isinstance(function_chunk.get("arguments"), str):
                    aggregate["function"]["arguments"] += function_chunk["arguments"]

    message = {
        "role": "assistant",
        "content": "".join(content_parts) or None,
        "tool_calls": [tool_call_chunks[index] for index in sorted(tool_call_chunks)],
    }
    if reasoning_field:
        message[reasoning_field] = "".join(reasoning_parts)
    reasoning_text, _ = extract_reasoning_text(message)
    tool_call = assert_tool_response(message, finish_reason, expected_arguments)
    emit_probe_record(
        {
            "probe": "streamed-single-tool",
            "passed": True,
            "finishReason": finish_reason,
            "toolName": tool_call["function"]["name"],
            "arguments": expected_arguments,
            "reasoningField": reasoning_field,
            "reasoningChars": len(reasoning_text),
            "contentChars": len(message["content"] or ""),
            "usage": usage,
        }
    )


def request_nonstreamed_tool_call(
    messages: list[dict[str, Any]], expected_arguments: dict[str, Any]
) -> dict[str, Any]:
    """Request and validate one non-streamed tool call for a multi-turn conversation."""
    payload = build_probe_payload(messages, stream=False)
    payload.pop("stream_options")
    with post_probe_request(payload) as response:
        result = json.load(response)
    choices = result.get("choices") or []
    if len(choices) != 1:
        raise AssertionError(f"ThinkingCap tool probe: unexpected choices {choices!r}")
    choice = choices[0]
    message = choice.get("message") or {}
    tool_call = assert_tool_response(
        message, choice.get("finish_reason"), expected_arguments
    )
    return {
        "message": message,
        "toolCall": tool_call,
        "usage": result.get("usage"),
        "finishReason": choice.get("finish_reason"),
    }


def run_multiturn_reasoning_probe() -> None:
    """Require three exact tool turns while replaying prior reasoning content."""
    expected_turns = [
        {"round": 1, "payload": "first turn"},
        {"round": 2, "payload": "second turn"},
        {"round": 3, "payload": 'café\n第二行 <tag attr="x">& value</tag>'},
    ]
    messages: list[dict[str, Any]] = []
    previous_reasoning_chars = 0

    for expected_arguments in expected_turns:
        messages.append(
            {
                "role": "user",
                "content": (
                    "Call record_probe exactly once with these JSON arguments: "
                    f"{json.dumps(expected_arguments, ensure_ascii=False)}. Do not answer in prose."
                ),
            }
        )
        response = request_nonstreamed_tool_call(messages, expected_arguments)
        assistant_message = response["message"]
        reasoning_text, reasoning_field = extract_reasoning_text(assistant_message)
        reasoning_chars = len(reasoning_text)
        if reasoning_chars == 0:
            raise AssertionError(
                "ThinkingCap tool probe: assistant reasoning was empty"
            )
        messages.append(assistant_message)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": response["toolCall"]["id"],
                "content": json.dumps(
                    {"recorded": True, **expected_arguments}, ensure_ascii=False
                ),
            }
        )
        emit_probe_record(
            {
                "probe": "multiturn-tool",
                "passed": True,
                "round": expected_arguments["round"],
                "finishReason": response["finishReason"],
                "toolName": response["toolCall"]["function"]["name"],
                "arguments": expected_arguments,
                "reasoningField": reasoning_field,
                "reasoningChars": reasoning_chars,
                "priorReasoningCharsReplayed": previous_reasoning_chars,
                "usage": response["usage"],
            }
        )
        previous_reasoning_chars += reasoning_chars


def main() -> int:
    """Run all approved tool-calling checks and report one final contract record."""
    emit_probe_record(
        {
            "probe": "request-contract",
            "model": MODEL,
            "endpoint": ENDPOINT,
            "maxTokens": MAX_OUTPUT_TOKENS,
            "chatTemplateKwargs": CHAT_TEMPLATE_KWARGS,
            "thinkingTokenBudget": None,
            "toolChoice": "auto",
            "sampling": SAMPLING,
        }
    )
    try:
        run_streamed_tool_probe()
        run_multiturn_reasoning_probe()
    except (AssertionError, OSError, TimeoutError, TypeError, ValueError) as error:
        emit_probe_record(
            {
                "probe": "tool-calling-suite",
                "passed": False,
                "errorType": type(error).__name__,
                "error": str(error),
            }
        )
        return 1
    emit_probe_record({"probe": "tool-calling-suite", "passed": True})
    return 0


if __name__ == "__main__":
    sys.exit(main())
