#!/usr/bin/env python3
"""Reconstruct a Pi OpenAI chat request from a saved native session."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def _text_content(blocks: object) -> list[str]:
    if not isinstance(blocks, list):
        return []
    return [
        block["text"]
        for block in blocks
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]


def _convert_user_message(message: dict[str, Any]) -> dict[str, Any]:
    content = message.get("content")
    if isinstance(content, str):
        return {"role": "user", "content": content}
    if not isinstance(content, list):
        raise TypeError("Pi request reconstruction: user content must be text blocks")
    converted = []
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "text":
            raise ValueError(
                "Pi request reconstruction: only text user blocks are supported"
            )
        text = block.get("text")
        if not isinstance(text, str):
            raise TypeError("Pi request reconstruction: user text must be a string")
        converted.append({"type": "text", "text": text})
    return {"role": "user", "content": converted}


def _convert_assistant_message(message: dict[str, Any]) -> dict[str, Any]:
    blocks = message.get("content")
    if not isinstance(blocks, list):
        raise TypeError("Pi request reconstruction: assistant content must be blocks")
    converted: dict[str, Any] = {"role": "assistant", "content": None}
    text = "".join(part for part in _text_content(blocks) if part.strip())
    if text:
        converted["content"] = text

    thinking_blocks = [
        block
        for block in blocks
        if isinstance(block, dict)
        and block.get("type") == "thinking"
        and isinstance(block.get("thinking"), str)
        and block["thinking"].strip()
    ]
    if thinking_blocks:
        signature = thinking_blocks[0].get("thinkingSignature")
        if isinstance(signature, str) and signature:
            converted[signature] = "\n".join(
                str(block["thinking"]) for block in thinking_blocks
            )

    tool_calls = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "toolCall":
            continue
        tool_call_id = block.get("id")
        name = block.get("name")
        arguments = block.get("arguments")
        if not isinstance(tool_call_id, str) or not isinstance(name, str):
            raise TypeError("Pi request reconstruction: invalid tool call identity")
        tool_calls.append(
            {
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(
                        arguments,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                },
            }
        )
    if tool_calls:
        converted["tool_calls"] = tool_calls
    if "reasoning_content" not in converted:
        converted["reasoning_content"] = ""
    if converted["content"] is None and not tool_calls:
        raise ValueError(
            "Pi request reconstruction: empty assistant message is not replayable"
        )
    return converted


def _convert_tool_result(message: dict[str, Any]) -> dict[str, Any]:
    tool_call_id = message.get("toolCallId")
    if not isinstance(tool_call_id, str) or not tool_call_id:
        raise ValueError("Pi request reconstruction: tool result lacks tool call id")
    text_parts = _text_content(message.get("content"))
    content = "\n".join(text_parts) if text_parts else "(no tool output)"
    return {
        "role": "tool",
        "content": content,
        "tool_call_id": tool_call_id,
    }


def reconstruct_pi_openai_request(
    initial_request: dict[str, Any],
    session_entries: list[dict[str, Any]],
    *,
    completed_assistant_turns: int | None = None,
    drop_assistant_reasoning: bool = False,
) -> dict[str, Any]:
    """Rebuild the next OpenAI request from Pi's completed session messages."""
    if completed_assistant_turns is not None and completed_assistant_turns < 0:
        raise ValueError("Pi request reconstruction: turn count cannot be negative")
    initial_messages = initial_request.get("messages")
    if not isinstance(initial_messages, list) or len(initial_messages) < 2:
        raise ValueError(
            "Pi request reconstruction: initial request needs system and user messages"
        )
    messages = [
        entry["message"]
        for entry in session_entries
        if entry.get("type") == "message" and isinstance(entry.get("message"), dict)
    ]
    if not messages or messages[0].get("role") != "user":
        raise ValueError(
            "Pi request reconstruction: session must start with a user message"
        )
    if _convert_user_message(messages[0]) != initial_messages[-1]:
        raise ValueError(
            "Pi request reconstruction: initial request and session user differ"
        )

    request = copy.deepcopy(initial_request)
    reconstructed_messages = copy.deepcopy(initial_messages)
    assistant_turns = 0
    for message in messages[1:]:
        role = message.get("role")
        if role == "assistant":
            if (
                completed_assistant_turns is not None
                and assistant_turns >= completed_assistant_turns
            ):
                break
            converted_assistant = _convert_assistant_message(message)
            if drop_assistant_reasoning:
                for field in ("reasoning", "reasoning_content", "reasoning_text"):
                    converted_assistant.pop(field, None)
                converted_assistant["reasoning_content"] = ""
            reconstructed_messages.append(converted_assistant)
            assistant_turns += 1
        elif role == "toolResult":
            reconstructed_messages.append(_convert_tool_result(message))
        elif role == "user":
            reconstructed_messages.append(_convert_user_message(message))
        else:
            raise ValueError(
                f"Pi request reconstruction: unsupported session role {role!r}"
            )
    request["messages"] = reconstructed_messages
    return request


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _load_json_lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


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
    parser.add_argument("--initial-request", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--completed-assistant-turns", type=int)
    parser.add_argument("--drop-assistant-reasoning", action="store_true")
    parser.add_argument("--validate-request", type=Path)
    args = parser.parse_args()

    request = reconstruct_pi_openai_request(
        _load_json(args.initial_request),
        _load_json_lines(args.session),
        completed_assistant_turns=args.completed_assistant_turns,
        drop_assistant_reasoning=args.drop_assistant_reasoning,
    )
    if args.validate_request is not None:
        expected = _load_json(args.validate_request)
        if request != expected:
            raise SystemExit(
                "Pi request reconstruction mismatch against saved provider request"
            )
    byte_count, sha256 = _write_private_json(args.output, request)
    print(
        json.dumps(
            {
                "assistant_messages": sum(
                    message.get("role") == "assistant"
                    for message in request["messages"]
                ),
                "bytes": byte_count,
                "messages": len(request["messages"]),
                "output": str(args.output),
                "sha256": sha256,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
