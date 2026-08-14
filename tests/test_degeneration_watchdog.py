from __future__ import annotations

import json
from dataclasses import asdict, replace

import pytest

from harness.degeneration_watchdog import (
    DegenerationWatchdog,
    coding_agent_early_gate_watchdog,
    coding_agent_response_gate_watchdog,
    degeneration_watchdog_policy_from_mapping,
)


def test_coding_agent_early_gate_profile_is_explicit() -> None:
    policy = coding_agent_early_gate_watchdog()

    assert policy.profile == "coding-agent-early-gate-v1"
    assert policy.max_assistant_chars_per_turn == 180_000
    assert policy.max_assistant_output_tokens_per_turn == 50_000
    assert policy.max_tool_calls_per_turn == 24
    assert policy.max_identical_tool_calls_per_turn == 4
    assert policy.max_tool_calls_without_progress == 48
    assert policy.progress_tool_names == ("edit", "write")


def test_coding_agent_response_gate_profile_has_no_cross_turn_heuristic() -> None:
    policy = coding_agent_response_gate_watchdog()

    assert policy.profile == "coding-agent-response-gate-v1"
    assert policy.max_assistant_chars_per_turn == 180_000
    assert policy.max_assistant_output_tokens_per_turn == 50_000
    assert policy.max_tool_calls_per_turn == 24
    assert policy.max_identical_tool_calls_per_turn == 4
    assert policy.max_tool_calls_without_progress is None
    assert policy.progress_tool_names == ()
    assert degeneration_watchdog_policy_from_mapping(asdict(policy)) == policy


def test_response_gate_allows_many_unique_single_bash_turns() -> None:
    watchdog = DegenerationWatchdog(coding_agent_response_gate_watchdog())

    for index in range(100):
        assert watchdog.observe({"type": "turn_start"}) is None
        assert (
            watchdog.observe(
                {
                    "type": "tool_execution_start",
                    "toolName": "bash",
                    "args": {"command": f"sed -n '{index + 1}p' src/module.py"},
                }
            )
            is None
        )
        assert (
            watchdog.observe(
                {
                    "type": "tool_execution_end",
                    "toolName": "bash",
                    "isError": False,
                }
            )
            is None
        )


def test_response_gate_still_rejects_large_tool_batch() -> None:
    watchdog = DegenerationWatchdog(coding_agent_response_gate_watchdog())
    assert watchdog.observe({"type": "turn_start"}) is None

    for index in range(24):
        assert (
            watchdog.observe(
                {
                    "type": "tool_execution_start",
                    "toolName": "read",
                    "args": {"path": f"/app/file-{index}"},
                }
            )
            is None
        )
    violation = watchdog.observe(
        {
            "type": "tool_execution_start",
            "toolName": "read",
            "args": {"path": "/app/file-24"},
        }
    )

    assert violation is not None
    assert violation.reason == "tool_calls_per_turn"


def test_confirmed_profile_rejects_threshold_drift() -> None:
    drifted = replace(
        coding_agent_early_gate_watchdog(),
        max_tool_calls_per_turn=25,
    )

    with pytest.raises(ValueError, match="thresholds drifted"):
        degeneration_watchdog_policy_from_mapping(asdict(drifted))


def test_rejects_one_extremely_long_unfinished_assistant_turn() -> None:
    policy = replace(
        coding_agent_early_gate_watchdog(),
        max_assistant_chars_per_turn=10,
    )
    watchdog = DegenerationWatchdog(policy)

    assert watchdog.observe({"type": "turn_start"}) is None
    violation = watchdog.observe(
        {
            "type": "message_update",
            "assistantMessageEvent": {
                "type": "thinking_delta",
                "delta": "x" * 11,
            },
        }
    )

    assert violation is not None
    assert violation.reason == "assistant_chars_per_turn"
    assert violation.observed == 11
    assert violation.limit == 10


def test_rejects_exact_excessive_assistant_output_tokens() -> None:
    policy = replace(
        coding_agent_early_gate_watchdog(),
        max_assistant_output_tokens_per_turn=10,
    )
    watchdog = DegenerationWatchdog(policy)

    violation = watchdog.observe(
        {
            "type": "message_end",
            "message": {"role": "assistant", "usage": {"output": 11}},
        }
    )

    assert violation is not None
    assert violation.reason == "assistant_output_tokens_per_turn"


def test_rejects_large_or_repeated_tool_batch() -> None:
    base = coding_agent_early_gate_watchdog()
    batch_watchdog = DegenerationWatchdog(
        replace(
            base,
            max_tool_calls_per_turn=2,
            max_identical_tool_calls_per_turn=10,
        )
    )
    batch_watchdog.observe({"type": "turn_start"})
    for index in range(2):
        assert (
            batch_watchdog.observe(
                {
                    "type": "tool_execution_start",
                    "toolName": "read",
                    "args": {"path": f"/app/file-{index}"},
                }
            )
            is None
        )
    batch_violation = batch_watchdog.observe(
        {
            "type": "tool_execution_start",
            "toolName": "read",
            "args": {"path": "/app/file-3"},
        }
    )
    assert batch_violation is not None
    assert batch_violation.reason == "tool_calls_per_turn"

    repeat_watchdog = DegenerationWatchdog(
        replace(
            base,
            max_tool_calls_per_turn=10,
            max_identical_tool_calls_per_turn=2,
        )
    )
    event = {
        "type": "tool_execution_start",
        "toolName": "read",
        "args": {"path": "/app/src/index.ts", "offset": 1, "limit": 200},
    }
    assert repeat_watchdog.observe(event) is None
    assert repeat_watchdog.observe(event) is None
    repeat_violation = repeat_watchdog.observe(event)
    assert repeat_violation is not None
    assert repeat_violation.reason == "identical_tool_calls_per_turn"
    assert repeat_violation.tool_name == "read"
    assert len(repeat_violation.tool_signature_sha256 or "") == 64
    assert "/app/src/index.ts" not in json.dumps(repeat_violation.to_dict())


def test_successful_write_resets_no_progress_counter() -> None:
    policy = replace(
        coding_agent_early_gate_watchdog(),
        max_tool_calls_per_turn=20,
        max_identical_tool_calls_per_turn=20,
        max_tool_calls_without_progress=2,
    )
    watchdog = DegenerationWatchdog(policy)
    read = {
        "type": "tool_execution_start",
        "toolName": "read",
        "args": {"path": "/app/src/index.ts"},
    }

    assert watchdog.observe(read) is None
    assert watchdog.observe(read | {"args": {"path": "/app/src/types.ts"}}) is None
    assert (
        watchdog.observe(
            {
                "type": "tool_execution_start",
                "toolName": "write",
                "args": {"path": "/app/src/new.ts", "content": "secret"},
            }
        )
        is None
    )
    assert (
        watchdog.observe(
            {
                "type": "tool_execution_end",
                "toolName": "write",
                "isError": False,
            }
        )
        is None
    )
    assert watchdog.observe(read) is None
    assert watchdog.observe(read | {"args": {"path": "/app/src/types.ts"}}) is None
    violation = watchdog.observe(read | {"args": {"path": "/app/src/transformer.ts"}})
    assert violation is not None
    assert violation.reason == "tool_calls_without_progress"
