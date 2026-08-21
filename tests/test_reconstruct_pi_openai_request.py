from __future__ import annotations

from scripts.reconstruct_pi_openai_request import reconstruct_pi_openai_request


def test_reconstructs_pi_assistant_reasoning_tools_and_results() -> None:
    initial_request = {
        "model": "deepseek-v4",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": [{"type": "text", "text": "task"}]},
        ],
        "tools": [{"type": "function", "function": {"name": "read"}}],
        "stream": True,
    }
    session_entries = [
        {
            "type": "message",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "task"}],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "inspect",
                        "thinkingSignature": "reasoning_content",
                    },
                    {"type": "text", "text": "  "},
                    {
                        "type": "toolCall",
                        "id": "call-1",
                        "name": "read",
                        "arguments": {"path": "src/a.ts", "limit": 20},
                    },
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolCallId": "call-1",
                "toolName": "read",
                "content": [
                    {"type": "text", "text": "line 1"},
                    {"type": "text", "text": "line 2"},
                ],
                "isError": False,
            },
        },
    ]

    request = reconstruct_pi_openai_request(initial_request, session_entries)

    assert request == {
        "model": "deepseek-v4",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": [{"type": "text", "text": "task"}]},
            {
                "role": "assistant",
                "content": None,
                "reasoning_content": "inspect",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "read",
                            "arguments": '{"path":"src/a.ts","limit":20}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "content": "line 1\nline 2",
                "tool_call_id": "call-1",
            },
        ],
        "tools": [{"type": "function", "function": {"name": "read"}}],
        "stream": True,
    }


def test_can_remove_only_prior_assistant_reasoning() -> None:
    initial_request = {
        "model": "deepseek-v4",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "task"},
        ],
    }
    session_entries = [
        {"type": "message", "message": {"role": "user", "content": "task"}},
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "historical reasoning",
                        "thinkingSignature": "reasoning_content",
                    },
                    {
                        "type": "toolCall",
                        "id": "call-1",
                        "name": "bash",
                        "arguments": {"command": "true"},
                    },
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolCallId": "call-1",
                "content": [{"type": "text", "text": "(no output)"}],
            },
        },
    ]

    request = reconstruct_pi_openai_request(
        initial_request,
        session_entries,
        drop_assistant_reasoning=True,
    )

    assistant = request["messages"][2]
    assert assistant["reasoning_content"] == ""
    assert assistant["tool_calls"][0]["function"]["name"] == "bash"
    assert request["messages"][3] == {
        "role": "tool",
        "content": "(no output)",
        "tool_call_id": "call-1",
    }
