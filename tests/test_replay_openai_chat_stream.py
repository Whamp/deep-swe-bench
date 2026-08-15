from __future__ import annotations

import json

from scripts.replay_openai_chat_stream import consume_openai_chat_stream


def sse(data: object) -> bytes:
    return f"data: {json.dumps(data)}\n".encode()


def test_consumes_reasoning_text_tool_and_finish_deltas() -> None:
    lines = [
        sse({"choices": [{"delta": {"reasoning_content": "think"}}]}),
        sse({"choices": [{"delta": {"content": "answer"}}]}),
        sse(
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "read",
                                        "arguments": '{"path":"a"}',
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ),
        sse(
            {
                "choices": [
                    {
                        "delta": {},
                        "finish_reason": "tool_calls",
                        "stop_reason": "</DSML>",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            }
        ),
        b"data: [DONE]\n",
    ]

    result = consume_openai_chat_stream(lines, assistant_char_limit=100)

    assert result["classification"] == "completed"
    assert result["finish_reason"] == "tool_calls"
    assert result["stop_reason"] == "</DSML>"
    assert result["delta_char_counts"] == {
        "content": 6,
        "reasoning_content": 5,
        "tool_arguments": 12,
        "tool_name": 4,
    }
    assert result["first_chars"] == 'thinkanswerread{"path":"a"}'
    assert result["last_chars"] == result["first_chars"]
    assert result["usage"]["completion_tokens"] == 4


def test_stops_after_bounded_assistant_character_limit() -> None:
    lines = [
        sse({"choices": [{"delta": {"reasoning_content": "a" * 12}}]}),
        sse({"choices": [{"delta": {"reasoning_content": "b" * 9}}]}),
        sse({"choices": [{"delta": {"content": "must not be consumed"}}]}),
    ]

    result = consume_openai_chat_stream(lines, assistant_char_limit=20)

    assert result["classification"] == "assistant_char_limit"
    assert result["assistant_chars"] == 21
    assert result["delta_event_counts"] == {"reasoning_content": 2}
    assert "must not be consumed" not in result["last_chars"]
