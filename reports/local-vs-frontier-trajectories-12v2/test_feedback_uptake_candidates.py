import json
from pathlib import Path

import pytest

from build_feedback_uptake_candidates import (
    load_feedback_candidate_dataset,
    write_feedback_candidate_dataset,
)
from feedback_uptake_candidates import (
    MAX_CANDIDATE_WINDOW_BYTES,
    build_feedback_candidate_units,
    validate_feedback_candidate_units,
)
from feedback_uptake_events import build_feedback_uptake_packet
from test_feedback_uptake_events import (
    assistant_message,
    tool_call,
    tool_result,
    write_feedback_uptake_cell,
)


def test_candidate_window_is_bounded_and_source_addressed(tmp_path: Path) -> None:
    huge_failure = (
        "setup output\n"
        + "x" * 100_000
        + "\nfatal: ambiguous argument 'src/a.py': unknown revision or path\n"
        + "y" * 100_000
    )
    huge_command = "git diff src/a.py | head -200 # " + "z" * 100_000
    records = [
        assistant_message(
            "assistant-1",
            "2026-01-01T00:00:01Z",
            tool_call("call-1", "bash", {"command": huge_command}),
        ),
        tool_result(
            "result-1",
            "call-1",
            "bash",
            huge_failure,
            is_error=False,
            timestamp="2026-01-01T00:00:02Z",
        ),
    ]
    for turn in range(2, 7):
        records.extend(
            [
                assistant_message(
                    f"assistant-{turn}",
                    f"2026-01-01T00:00:0{turn + 1}Z",
                    tool_call(
                        f"call-{turn}",
                        "read",
                        {"path": f"/app/src/follow-up-{turn}.py"},
                    ),
                ),
                tool_result(
                    f"result-{turn}",
                    f"call-{turn}",
                    "read",
                    "source contents " + str(turn),
                    is_error=False,
                    timestamp=f"2026-01-01T00:00:{turn + 7:02d}Z",
                ),
            ]
        )
    cell_root = write_feedback_uptake_cell(tmp_path, records)
    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-a", rep=0, cell_root=cell_root
    )

    units = build_feedback_candidate_units([packet])

    assert len(units) == 1
    unit = units[0]
    assert unit["candidate_unit_id"] == "frontier/task-a/rep0/tool-call-1"
    assert unit["source_event_kind"] == "tool_call_result"
    assert unit["focal_event"]["action_source"] == {
        "session_path": packet["events"][0]["action_session_path"],
        "jsonl_line": packet["events"][0]["action_jsonl_line"],
        "record_id": "assistant-1",
        "tool_call_id": "call-1",
    }
    assert unit["focal_event"]["observation_source"] == {
        "session_path": packet["events"][0]["observation_session_path"],
        "jsonl_line": packet["events"][0]["observation_jsonl_line"],
        "record_id": "result-1",
        "tool_call_id": "call-1",
    }
    assert len(unit["following_assistant_responses"]) == 3
    assert [
        response["assistant_response_ordinal"]
        for response in unit["following_assistant_responses"]
    ] == [2, 3, 4]
    serialized = json.dumps(unit, ensure_ascii=False, separators=(",", ":"))
    assert len(serialized.encode()) <= MAX_CANDIDATE_WINDOW_BYTES
    assert huge_failure not in serialized
    assert huge_command not in serialized
    assert "fatal: ambiguous argument" in serialized
    validate_feedback_candidate_units(units, packets=[packet])


def test_assistant_error_and_missing_result_remain_distinct_linked_candidates(
    tmp_path: Path,
) -> None:
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
                        tool_call("call-1", "edit", {"path": "internal", "edits": []})
                    ],
                    "stopReason": "error",
                    "errorMessage": "WebSocket error",
                    "diagnostics": [{"type": "provider_transport_failure"}],
                },
            }
        ],
    )
    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-a", rep=0, cell_root=cell_root
    )

    units = build_feedback_candidate_units([packet])

    assert [unit["source_event_kind"] for unit in units] == [
        "assistant_response",
        "tool_call_result",
    ]
    assert units[0]["related_candidate_unit_ids"] == [
        "frontier/task-a/rep0/tool-call-1"
    ]
    assert units[1]["related_candidate_unit_ids"] == [
        "frontier/task-a/rep0/assistant-response-1"
    ]
    validate_feedback_candidate_units(units, packets=[packet])


def test_candidate_dataset_manifest_freezes_exact_jsonl_bytes(tmp_path: Path) -> None:
    cell_root = write_feedback_uptake_cell(
        tmp_path / "source",
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
                "FAILED tests/test_a.py::test_a\n",
                is_error=False,
                timestamp="2026-01-01T00:00:02Z",
            ),
        ],
    )
    packet = build_feedback_uptake_packet(
        model_key="frontier", task="task-a", rep=0, cell_root=cell_root
    )
    units = build_feedback_candidate_units([packet])
    dataset_root = tmp_path / "candidates"

    manifest = write_feedback_candidate_dataset(
        units, packets=[packet], dataset_root=dataset_root
    )
    loaded_manifest, loaded_units = load_feedback_candidate_dataset(
        dataset_root, packets=[packet]
    )

    assert loaded_manifest == manifest
    assert loaded_units == units
    assert manifest["candidate_unit_count"] == 1
    assert len(manifest["candidate_set_sha256"]) == 64
    assert manifest["candidate_unit_ids"] == [units[0]["candidate_unit_id"]]

    units_path = dataset_root / "units.jsonl"
    units_path.write_text(units_path.read_text() + "{}\n")
    with pytest.raises(ValueError, match="candidate set SHA-256 mismatch"):
        load_feedback_candidate_dataset(dataset_root, packets=[packet])
