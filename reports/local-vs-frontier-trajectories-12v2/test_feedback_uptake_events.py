import copy
import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from build_feedback_uptake_events import (
    load_feedback_uptake_event_files,
    write_feedback_uptake_event_files,
)
from feedback_uptake_candidate_signals import detect_tool_result_candidate_signals
from feedback_uptake_event_validation import validate_feedback_uptake_packets
from feedback_uptake_events import (
    MAX_SOURCE_SNIPPET_CHARS,
    MIN_SOURCE_SNIPPET_CHARS,
    MODEL_ROLES,
    bounded_source_snippets,
    build_feedback_uptake_packet,
)


def write_feedback_uptake_cell(
    tmp_path: Path,
    records: list[dict[str, Any]],
    *,
    task: str = "task-a",
    rep: int = 0,
    result_overrides: dict[str, Any] | None = None,
) -> Path:
    """Write one minimal result cell for feedback event extraction tests."""
    cell_root = tmp_path / task / f"rep{rep}"
    session_root = cell_root / "session"
    session_root.mkdir(parents=True)
    session_records = [
        {"type": "session", "id": "session-1", "timestamp": "2026-01-01T00:00:00Z"},
        *records,
    ]
    (session_root / "session.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in session_records)
    )
    result = {
        "task": task,
        "rep": rep,
        "reward_binary": 0,
        "reward_partial": 0.5,
        "f2p_passed": 1,
        "f2p_total": 2,
        "p2p_passed": 3,
        "p2p_total": 3,
        "agent_exit": 0,
        "agent_timed_out": False,
        "agent_wall_s": 12.5,
        "model": "test/model",
        "config": "test-config",
        "thinking_level": "high",
    }
    result.update(result_overrides or {})
    (cell_root / "result.json").write_text(json.dumps(result))
    return cell_root


def assistant_message(
    event_id: str,
    turn_timestamp: str,
    *tool_calls: dict[str, Any],
) -> dict[str, Any]:
    """Build one assistant message containing an ordered tool-call group."""
    return {
        "type": "message",
        "id": event_id,
        "timestamp": turn_timestamp,
        "message": {"role": "assistant", "content": list(tool_calls)},
    }


def tool_call(call_id: str, name: str, arguments: Any) -> dict[str, Any]:
    """Build one exact assistant tool-call content block."""
    return {"type": "toolCall", "id": call_id, "name": name, "arguments": arguments}


def tool_result(
    event_id: str,
    call_id: str,
    tool_name: str,
    text: str,
    *,
    is_error: bool,
    timestamp: str,
) -> dict[str, Any]:
    """Build one tool result linked to an assistant tool call."""
    return {
        "type": "message",
        "id": event_id,
        "timestamp": timestamp,
        "message": {
            "role": "toolResult",
            "toolCallId": call_id,
            "toolName": tool_name,
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
        },
    }


@given(st.text(max_size=2_000))
def test_bounded_source_snippets_satisfy_evidence_contract(text: str) -> None:
    snippets = bounded_source_snippets(text)

    assert len(snippets) <= 2
    assert bool(snippets) is (len(text) >= MIN_SOURCE_SNIPPET_CHARS)
    for snippet in snippets:
        assert MIN_SOURCE_SNIPPET_CHARS <= len(snippet["text"])
        assert len(snippet["text"]) <= MAX_SOURCE_SNIPPET_CHARS
        assert text[snippet["start_char"] : snippet["end_char"]] == snippet["text"]


def test_build_feedback_uptake_packet_joins_results_and_next_action(
    tmp_path: Path,
) -> None:
    long_result = "validation passed\n" + "x" * 400
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "bash", {"command": "pytest tests -q"}),
            ),
            tool_result(
                "result-1",
                "call-1",
                "bash",
                long_result,
                is_error=False,
                timestamp="2026-01-01T00:00:02Z",
            ),
            assistant_message(
                "assistant-2",
                "2026-01-01T00:00:03Z",
                tool_call(
                    "call-2",
                    "edit",
                    {
                        "path": "/app/src/a.py",
                        "edits": [{"oldText": "a", "newText": "b"}],
                    },
                ),
            ),
            tool_result(
                "result-2",
                "call-2",
                "edit",
                "Successfully replaced 1 block(s) in /app/src/a.py.",
                is_error=False,
                timestamp="2026-01-01T00:00:04Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="frontier",
        task="task-a",
        rep=0,
        cell_root=cell_root,
    )

    first, second = packet["events"]
    assert packet["trajectory_id"] == "frontier/task-a/rep0"
    assert packet["session_id"] == "session-1"
    assert [first["action_event_ordinal"], second["action_event_ordinal"]] == [1, 2]
    assert [first["assistant_turn"], second["assistant_turn"]] == [1, 2]
    assert first["parallel_group_id"] == "assistant-1"
    assert first["tool_call_id"] == "call-1"
    assert first["tool_arguments"] == {"command": "pytest tests -q"}
    assert first["tool_kind"] == "validation_command"
    assert first["is_validation_command"] is True
    assert first["observation_event_id"] == "result-1"
    assert first["observation_tool_call_id"] == "call-1"
    assert first["observation_text"] == long_result
    assert 1 <= len(first["source_snippets"]) <= 3
    assert all(
        20 <= len(snippet["text"]) <= 300 for snippet in first["source_snippets"]
    )
    assert first["next_action"]["assistant_event_id"] == "assistant-2"
    assert first["next_action"]["assistant_turn"] == 2
    assert first["next_action"]["tool_calls"] == [
        {
            "action_event_ordinal": 2,
            "tool_call_id": "call-2",
            "tool_name": "edit",
        }
    ]
    assert second["next_action"] is None


def test_build_feedback_uptake_packet_classifies_malformed_edit_arguments(
    tmp_path: Path,
) -> None:
    malformed_arguments = {
        "edits": [{"path": "/app/src/a.py", "oldText": "before", "newText": "after"}]
    }
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "edit", malformed_arguments),
            ),
            tool_result(
                "result-1",
                "call-1",
                "edit",
                'Validation failed for tool "edit":\n'
                "  - path: must have required properties path\n\n"
                "Received arguments:\n" + json.dumps(malformed_arguments),
                is_error=True,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="agentworld",
        task="task-a",
        rep=0,
        cell_root=cell_root,
    )

    event = packet["events"][0]
    assert event["observation_is_error"] is True
    assert event["raw_result_signature"] == "reported_error"
    assert "edit_argument_schema_error" in event["candidate_signal_types"]
    assert event["raw_exit_code"] is None


def test_build_feedback_uptake_packet_classifies_stale_edit_text(
    tmp_path: Path,
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call(
                    "call-1",
                    "edit",
                    {
                        "path": "/app/src/a.py",
                        "edits": [{"oldText": "stale", "newText": "replacement"}],
                    },
                ),
            ),
            tool_result(
                "result-1",
                "call-1",
                "edit",
                "Could not find the exact text in /app/src/a.py. The old text must match exactly.",
                is_error=True,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="thinkingcap", task="task-a", rep=0, cell_root=cell_root
    )

    assert "edit_application_rejection" in packet["events"][0]["candidate_signal_types"]


@pytest.mark.parametrize(
    "rejection_text",
    [
        "edits[2] and edits[3] overlap in src/a.py. Merge them into one edit or target disjoint regions.",
        "No changes made to /app/src/a.py. The replacement produced identical content.",
    ],
)
def test_build_feedback_uptake_packet_classifies_exact_edit_application_rejections(
    tmp_path: Path, rejection_text: str
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call(
                    "call-1",
                    "edit",
                    {
                        "path": "/app/src/a.py",
                        "edits": [{"oldText": "before", "newText": "after"}],
                    },
                ),
            ),
            tool_result(
                "result-1",
                "call-1",
                "edit",
                rejection_text,
                is_error=True,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-a", rep=0, cell_root=cell_root
    )

    assert "edit_application_rejection" in packet["events"][0]["candidate_signal_types"]


def test_build_feedback_uptake_packet_classifies_read_failure(tmp_path: Path) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "read", {"path": "/app/missing.py"}),
            ),
            tool_result(
                "result-1",
                "call-1",
                "read",
                "File not found: /app/missing.py",
                is_error=True,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="thinkingcap", task="task-a", rep=0, cell_root=cell_root
    )

    event = packet["events"][0]
    assert event["tool_kind"] == "repository_read"
    assert event["result_kind"] == "read_result"
    assert event["raw_result_signature"] == "reported_error"
    assert "read_error" in event["candidate_signal_types"]


def test_diagnostic_nonzero_command_is_not_classified_as_mechanical_tool_failure(
    tmp_path: Path,
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "bash", {"command": "grep Missing src/a.py"}),
            ),
            tool_result(
                "result-1",
                "call-1",
                "bash",
                "(no output)\n\nCommand exited with code 1",
                is_error=True,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="agentworld", task="task-a", rep=0, cell_root=cell_root
    )

    event = packet["events"][0]
    assert event["tool_kind"] == "shell_command"
    assert event["is_validation_command"] is False
    assert event["result_kind"] == "command_result"
    assert event["raw_result_signature"] == "explicit_nonzero_exit"
    assert "explicit_nonzero_exit" in event["candidate_signal_types"]
    assert event["raw_exit_code"] == 1


@pytest.mark.parametrize(
    "command,result_text",
    [
        (
            'go test ./checkers -run "TestCheckers/brokenDocLink" 2>&1 | head -100',
            "--- FAIL: TestCheckers (0.06s)\nFAIL\texample/checkers\t0.287s\nFAIL\n",
        ),
        (
            "python -m pytest tests/test_aliases.py 2>&1 | tail -30",
            (
                "FAILED tests/test_aliases.py::test_schema\n"
                "========================= 1 failed, 14 passed in 0.05s =========================\n"
            ),
        ),
        (
            "python -m pytest tests/test_runnable.py 2>&1 | tail -30",
            "ERROR tests/test_runnable.py\n1 error in 0.30s\n",
        ),
    ],
)
def test_build_feedback_uptake_packet_classifies_exact_zero_status_test_failures(
    tmp_path: Path, command: str, result_text: str
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "bash", {"command": command}),
            ),
            tool_result(
                "result-1",
                "call-1",
                "bash",
                result_text,
                is_error=False,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="thinkingcap", task="task-a", rep=0, cell_root=cell_root
    )

    event = packet["events"][0]
    assert event["raw_result_signature"] == "reported_success"
    assert "failure_text_with_zero_status" in event["candidate_signal_types"]
    assert any(
        "FAIL" in snippet["text"]
        or "failed" in snippet["text"]
        or "error" in snippet["text"]
        for snippet in event["source_snippets"]
    )


@pytest.mark.parametrize(
    "command,result_text,expected_detector",
    [
        (
            "go build ./... 2>&1 | head -50",
            '# example/internal/publish\ninternal/publish/attempts.go:5:2: "fmt" imported and not used\n',
            "go_compiler_diagnostic",
        ),
        (
            "yarn test -- --testPathPattern=bigquery 2>&1 | grep pipe",
            "  ✓ formats simple pipe query\n  ✕ formats pipe query with GROUP BY\n",
            "test_failure_glyph",
        ),
        (
            "git diff src/a.py | head -200",
            "fatal: ambiguous argument 'src/a.py': unknown revision or path\n",
            "fatal_command_diagnostic",
        ),
    ],
)
def test_build_feedback_uptake_packet_flags_high_recall_hidden_failure_candidates(
    tmp_path: Path,
    command: str,
    result_text: str,
    expected_detector: str,
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "bash", {"command": command}),
            ),
            tool_result(
                "result-1",
                "call-1",
                "bash",
                result_text,
                is_error=False,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="thinkingcap", task="task-a", rep=0, cell_root=cell_root
    )

    event = packet["events"][0]
    assert event["raw_result_facts"] == {
        "has_result": True,
        "reported_is_error": False,
        "explicit_exit_code": None,
    }
    assert "failure_text_with_zero_status" in event["candidate_signal_types"]
    assert expected_detector in {
        signal["detector_id"] for signal in event["candidate_signals"]
    }
    assert all("semantic_label" not in signal for signal in event["candidate_signals"])


@given(st.text(max_size=200), st.text(max_size=200))
def test_failure_text_candidate_spans_are_exact_source_excerpts(
    prefix: str, suffix: str
) -> None:
    result_text = (
        prefix
        + "\nfatal: ambiguous argument 'src/a.py': unknown revision or path\n"
        + suffix
    )

    signals = detect_tool_result_candidate_signals(
        tool_name="bash",
        result_text=result_text,
        reported_is_error=False,
        has_result=True,
        explicit_exit_code=None,
    )

    text_signals = [
        signal for signal in signals if signal["source_kind"] == "observation_text"
    ]
    assert text_signals
    for signal in text_signals:
        assert (
            result_text[signal["start_char"] : signal["end_char"]]
            == signal["matched_text"]
        )
        assert "semantic_label" not in signal


def test_nonvalidation_failure_words_remain_candidate_not_semantic_outcome(
    tmp_path: Path,
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "bash", {"command": "cat notes.txt"}),
            ),
            tool_result(
                "result-1",
                "call-1",
                "bash",
                "FAILED tests/example.py::documented_example",
                is_error=False,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-a", rep=0, cell_root=cell_root
    )

    event = packet["events"][0]
    assert event["raw_result_signature"] == "reported_success"
    assert event["candidate_signal_types"] == ["failure_text_with_zero_status"]
    assert all("semantic_label" not in signal for signal in event["candidate_signals"])


def test_build_feedback_uptake_packet_retains_assistant_transport_diagnostics(
    tmp_path: Path,
) -> None:
    diagnostic = {
        "type": "provider_transport_failure",
        "error": {
            "message": "WebSocket idle timeout after 300000ms",
            "retryable": True,
        },
    }
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            {
                "type": "message",
                "id": "assistant-1",
                "timestamp": "2026-01-01T00:00:01Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        tool_call(
                            "call-1",
                            "edit",
                            {
                                "path": "/app/src/a.py",
                                "edits": [{"oldText": "a", "newText": "b"}],
                            },
                        )
                    ],
                    "stopReason": "error",
                    "errorMessage": "WebSocket idle timeout after 300000ms",
                    "diagnostics": [diagnostic],
                },
            },
            assistant_message(
                "assistant-2",
                "2026-01-01T00:00:02Z",
                tool_call(
                    "call-2",
                    "edit",
                    {
                        "path": "/app/src/a.py",
                        "edits": [{"oldText": "a", "newText": "b"}],
                    },
                ),
            ),
            tool_result(
                "result-2",
                "call-2",
                "edit",
                "Successfully replaced 1 block(s) in /app/src/a.py.",
                is_error=False,
                timestamp="2026-01-01T00:00:03Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-a", rep=0, cell_root=cell_root
    )

    first_response = packet["assistant_responses"][0]
    assert packet["schema_version"] == 3
    assert packet["assistant_response_count"] == 2
    assert packet["assistant_error_count"] == 1
    assert first_response["assistant_event_id"] == "assistant-1"
    assert first_response["stop_reason"] == "error"
    assert first_response["error_message"] == "WebSocket idle timeout after 300000ms"
    assert first_response["diagnostics"] == [diagnostic]
    assert first_response["tool_call_ids"] == ["call-1"]
    assert first_response["candidate_signal_types"] == [
        "assistant_response_error",
        "provider_transport_failure",
    ]
    assert packet["events"][0]["assistant_response_ordinal"] == 1
    assert packet["events"][0]["raw_result_signature"] == "observation_missing"


def test_build_feedback_uptake_packet_retains_missing_result_at_timeout(
    tmp_path: Path,
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call(
                    "call-1", "bash", {"command": "python probes/request_coalescing.py"}
                ),
            )
        ],
        result_overrides={"agent_exit": "timeout", "agent_timed_out": True},
    )

    packet = build_feedback_uptake_packet(
        model_key="thinkingcap", task="task-a", rep=0, cell_root=cell_root
    )

    event = packet["events"][0]
    assert packet["termination_kind"] == "agent_timeout"
    assert packet["missing_result_count"] == 1
    assert event["result_kind"] == "missing_result"
    assert event["raw_result_signature"] == "observation_missing"
    assert event["candidate_signal_types"] == ["missing_observation"]
    assert event["observation_event_id"] is None
    assert event["next_action"] is None


def test_build_feedback_uptake_packet_links_immediate_unchanged_retry(
    tmp_path: Path,
) -> None:
    edit_arguments = {
        "path": "/app/src/a.py",
        "edits": [{"oldText": "stale", "newText": "replacement"}],
    }
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "edit", edit_arguments),
            ),
            tool_result(
                "result-1",
                "call-1",
                "edit",
                "Could not find the exact text in /app/src/a.py.",
                is_error=True,
                timestamp="2026-01-01T00:00:02Z",
            ),
            assistant_message(
                "assistant-2",
                "2026-01-01T00:00:03Z",
                tool_call("call-2", "edit", edit_arguments),
            ),
            tool_result(
                "result-2",
                "call-2",
                "edit",
                "Successfully replaced 1 block(s) in /app/src/a.py.",
                is_error=False,
                timestamp="2026-01-01T00:00:04Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="agentworld", task="task-a", rep=0, cell_root=cell_root
    )

    next_action = packet["events"][0]["next_action"]
    assert next_action["assistant_event_id"] == "assistant-2"
    assert next_action["assistant_turn_distance"] == 1
    assert next_action["tool_calls"][0]["tool_call_id"] == "call-2"
    linked_event = next(
        event
        for event in packet["events"]
        if event["tool_call_id"] == next_action["tool_calls"][0]["tool_call_id"]
    )
    assert linked_event["tool_arguments"] == edit_arguments


def valid_feedback_uptake_population(source_root: Path) -> list[dict[str, Any]]:
    """Build the exact 108-packet population from independently readable sources."""
    packets = []
    for model_key in MODEL_ROLES:
        for task_index in range(12):
            task = f"task-{task_index:02d}"
            for rep in range(3):
                call_id = f"call-{model_key}-{task_index}-{rep}"
                cell_root = write_feedback_uptake_cell(
                    source_root / model_key,
                    [
                        assistant_message(
                            f"assistant-{call_id}",
                            "2026-01-01T00:00:01Z",
                            tool_call(
                                call_id,
                                "bash",
                                {"command": "python -m pytest tests -q"},
                            ),
                        ),
                        tool_result(
                            f"result-{call_id}",
                            call_id,
                            "bash",
                            "1 passed in 0.01 seconds",
                            is_error=False,
                            timestamp="2026-01-01T00:00:02Z",
                        ),
                    ],
                    task=task,
                    rep=rep,
                )
                packets.append(
                    build_feedback_uptake_packet(
                        model_key=model_key,
                        task=task,
                        rep=rep,
                        cell_root=cell_root,
                    )
                )
    return packets


def test_validate_feedback_uptake_packets_accepts_exact_population(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")

    validate_feedback_uptake_packets(
        packets, expected_tasks=[f"task-{index:02d}" for index in range(12)]
    )


def test_validate_feedback_uptake_packets_rejects_incomplete_population(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")

    with pytest.raises(ValueError, match="exactly 108 packets"):
        validate_feedback_uptake_packets(
            packets[:-1], expected_tasks=[f"task-{index:02d}" for index in range(12)]
        )


def test_validate_feedback_uptake_packets_rejects_duplicate_address(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")
    packets[-1] = copy.deepcopy(packets[0])

    with pytest.raises(ValueError, match="duplicate trajectory addresses"):
        validate_feedback_uptake_packets(
            packets, expected_tasks=[f"task-{index:02d}" for index in range(12)]
        )


def test_validate_feedback_uptake_packets_rejects_broken_result_link(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")
    packets[0]["events"][0]["observation_tool_call_id"] = "wrong-call-id"

    with pytest.raises(ValueError, match="call/result link mismatch"):
        validate_feedback_uptake_packets(
            packets, expected_tasks=[f"task-{index:02d}" for index in range(12)]
        )


def test_validate_feedback_uptake_packets_rejects_invented_source_ids(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")
    event = packets[0]["events"][0]
    event["tool_call_id"] = "invented-call-id"
    event["observation_tool_call_id"] = "invented-call-id"

    with pytest.raises(ValueError, match="invalid assistant tool-call links"):
        validate_feedback_uptake_packets(
            packets, expected_tasks=[f"task-{index:02d}" for index in range(12)]
        )


def test_validate_feedback_uptake_packets_rejects_skipped_source_next_action(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")
    cell_root = write_feedback_uptake_cell(
        tmp_path / "next-action-source" / "frontier",
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-1", "bash", {"command": "python -m pytest tests -q"}),
            ),
            tool_result(
                "result-1",
                "call-1",
                "bash",
                "1 failed, 14 passed in 0.05 seconds",
                is_error=False,
                timestamp="2026-01-01T00:00:02Z",
            ),
            assistant_message(
                "assistant-2",
                "2026-01-01T00:00:03Z",
                tool_call("call-2", "read", {"path": "/app/src/first_action.py"}),
            ),
            tool_result(
                "result-2",
                "call-2",
                "read",
                "first action source contents",
                is_error=False,
                timestamp="2026-01-01T00:00:04Z",
            ),
            assistant_message(
                "assistant-3",
                "2026-01-01T00:00:05Z",
                tool_call("call-3", "read", {"path": "/app/src/later_action.py"}),
            ),
            tool_result(
                "result-3",
                "call-3",
                "read",
                "later action source contents",
                is_error=False,
                timestamp="2026-01-01T00:00:06Z",
            ),
        ],
        task="task-00",
        rep=0,
    )
    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-00", rep=0, cell_root=cell_root
    )
    packets[0] = packet
    packet["events"][0]["next_action"] = copy.deepcopy(
        packet["events"][1]["next_action"]
    )

    with pytest.raises(ValueError, match="differs from source.*next_action"):
        validate_feedback_uptake_packets(
            packets, expected_tasks=[f"task-{index:02d}" for index in range(12)]
        )


def test_validate_feedback_uptake_packets_rejects_short_source_snippet(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")
    snippet = packets[0]["events"][0]["source_snippets"][0]
    snippet["text"] = snippet["text"][:5]
    snippet["end_char"] = snippet["start_char"] + 5

    with pytest.raises(ValueError, match="invalid source snippet"):
        validate_feedback_uptake_packets(
            packets, expected_tasks=[f"task-{index:02d}" for index in range(12)]
        )


def test_parallel_tool_results_join_by_id_before_shared_next_action(
    tmp_path: Path,
) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path,
        [
            assistant_message(
                "assistant-1",
                "2026-01-01T00:00:01Z",
                tool_call("call-read", "read", {"path": "/app/a.py"}),
                tool_call("call-bash", "bash", {"command": "grep x a.py"}),
            ),
            tool_result(
                "result-bash",
                "call-bash",
                "bash",
                "match",
                is_error=False,
                timestamp="2026-01-01T00:00:02Z",
            ),
            tool_result(
                "result-read",
                "call-read",
                "read",
                "contents",
                is_error=False,
                timestamp="2026-01-01T00:00:03Z",
            ),
            assistant_message(
                "assistant-2",
                "2026-01-01T00:00:04Z",
                tool_call(
                    "call-edit",
                    "edit",
                    {
                        "path": "/app/a.py",
                        "edits": [{"oldText": "x", "newText": "y"}],
                    },
                ),
            ),
            tool_result(
                "result-edit",
                "call-edit",
                "edit",
                "Successfully replaced 1 block(s) in /app/a.py.",
                is_error=False,
                timestamp="2026-01-01T00:00:05Z",
            ),
        ],
    )

    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-a", rep=0, cell_root=cell_root
    )

    read_event, bash_event, _ = packet["events"]
    assert read_event["action_event_ordinal"] == 1
    assert bash_event["action_event_ordinal"] == 2
    assert read_event["observation_event_id"] == "result-read"
    assert bash_event["observation_event_id"] == "result-bash"
    assert read_event["next_action"] == bash_event["next_action"]
    assert read_event["next_action"]["assistant_event_id"] == "assistant-2"


def test_write_feedback_uptake_event_files_replaces_complete_tree(
    tmp_path: Path,
) -> None:
    packets = valid_feedback_uptake_population(tmp_path / "population")
    tasks = [f"task-{index:02d}" for index in range(12)]
    event_root = tmp_path / "events"
    event_root.mkdir()
    (event_root / "stale.json").write_text("{}")

    written_paths = write_feedback_uptake_event_files(
        packets, expected_tasks=tasks, event_root=event_root
    )
    reloaded_packets = load_feedback_uptake_event_files(event_root)

    assert len(written_paths) == 108
    assert len(reloaded_packets) == 108
    assert not (event_root / "stale.json").exists()
    assert (event_root / "frontier" / "task-00__rep0.json") in written_paths
    validate_feedback_uptake_packets(reloaded_packets, expected_tasks=tasks)
