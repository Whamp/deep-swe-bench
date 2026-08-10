from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

SCANNER_PATH = (
    Path(__file__).parents[1]
    / "analysis"
    / "read-long-lines-incidence"
    / "scan_read_long_lines.py"
)
SPEC = importlib.util.spec_from_file_location("scan_read_long_lines", SCANNER_PATH)
assert SPEC and SPEC.loader
scan_read_long_lines = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scan_read_long_lines)


@given(st.text())
def test_utf16_len_matches_javascript_string_length(value: str) -> None:
    expected = sum(2 if ord(character) > 0xFFFF else 1 for character in value)
    assert scan_read_long_lines.utf16_len(value) == expected


def write_synthetic_read_session(
    result_path: Path,
    *,
    line: str,
    offset: int | None = None,
    limit: int | None = None,
) -> None:
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "config": "baseline",
                "task": "synthetic-long-line-task",
                "rep": 0,
            }
        )
    )
    arguments: dict[str, object] = {"path": "fixture.txt"}
    if offset is not None:
        arguments["offset"] = offset
    if limit is not None:
        arguments["limit"] = limit
    records = [
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "toolCall",
                        "id": "read-call",
                        "name": "read",
                        "arguments": arguments,
                    }
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolCallId": "read-call",
                "toolName": "read",
                "content": [{"type": "text", "text": line}],
                "isError": False,
            },
        },
    ]
    session_dir = result_path.parent / "session"
    session_dir.mkdir()
    (session_dir / "root.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records)
    )


def test_scan_rep_counts_ordinary_long_line_counterfactual(tmp_path: Path) -> None:
    result_path = (
        tmp_path
        / "results"
        / "model"
        / "high"
        / "baseline"
        / "synthetic-long-line-task"
        / "rep0"
        / "result.json"
    )
    write_synthetic_read_session(result_path, line="x" * 2_105, offset=7, limit=10)

    rep, activations, reads = scan_read_long_lines.scan_rep(result_path)

    assert rep["ordinary_long_read_results"] == 1
    assert rep["ordinary_long_lines"] == 1
    assert rep["omitted_characters"] == 105
    assert rep["net_characters_saved"] == 105 - rep["notice_characters"]
    assert activations[0]["source_line"] == 7
    assert reads[0]["ordinary_affected"] == 1


def test_scan_rep_exempts_limit_one_full_line_read(tmp_path: Path) -> None:
    result_path = (
        tmp_path
        / "results"
        / "model"
        / "high"
        / "baseline"
        / "synthetic-long-line-task"
        / "rep0"
        / "result.json"
    )
    write_synthetic_read_session(result_path, line="x" * 2_105, offset=7, limit=1)

    rep, activations, reads = scan_read_long_lines.scan_rep(result_path)

    assert rep["long_read_results"] == 1
    assert rep["ordinary_long_read_results"] == 0
    assert rep["exempt_long_read_results"] == 1
    assert rep["omitted_characters"] == 0
    assert activations[0]["ordinary_affected"] == 0
    assert reads[0]["exempt_limit_1"] == 1
