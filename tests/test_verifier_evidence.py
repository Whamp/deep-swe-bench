import json
from pathlib import Path
from typing import Any, cast

import pytest

from harness.verifier_evidence import (
    VerifierEvidenceMismatchError,
    prune_raw_verifier_evidence,
    with_compact_verifier_evidence,
    write_compact_verifier_result,
)


def write_verified_cell(cell: Path) -> dict[str, object]:
    verifier = cell / "verifier"
    verifier.mkdir(parents=True)
    (cell / "logs").mkdir()
    (verifier / "reward.json").write_text(
        json.dumps(
            {
                "reward": 0,
                "partial": 0.75,
                "f2p": 0.5,
                "f2p_passed": 1,
                "f2p_total": 2,
                "p2p": 1.0,
                "p2p_passed": 3,
                "p2p_total": 3,
            }
        )
    )
    (verifier / "ctrf.json").write_text(
        json.dumps(
            {
                "reportFormat": "CTRF",
                "results": {
                    "tool": {"name": "pytest"},
                    "summary": {
                        "tests": 5,
                        "passed": 4,
                        "failed": 1,
                        "skipped": 0,
                        "pending": 0,
                        "other": 0,
                    },
                    "tests": [
                        {"name": "passing case", "status": "passed"},
                        {
                            "name": "failing case",
                            "status": "failed",
                            "suite": "feature",
                            "filePath": "tests/test_feature.py",
                            "message": "expected true",
                            "trace": "assert false",
                        },
                    ],
                },
            }
        )
    )
    (cell / "logs" / "verifier.stdout.txt").write_text("raw verifier output\n")
    return {
        "task": "example-task",
        "reward_binary": 0,
        "reward_partial": 0.75,
        "f2p": 0.5,
        "f2p_passed": 1,
        "f2p_total": 2,
        "p2p": 1.0,
        "p2p_passed": 3,
        "p2p_total": 3,
        "verifier_exit": 0,
    }


def test_compact_verifier_evidence_preserves_result_and_failed_test(
    tmp_path: Path,
) -> None:
    result = write_verified_cell(tmp_path)

    compacted = with_compact_verifier_evidence(tmp_path, result)

    assert compacted["task"] == "example-task"
    assert compacted["reward_partial"] == 0.75
    assert compacted["result_schema_version"] == 2
    assert compacted["verifier_summary"] == {
        "schema_version": 1,
        "raw_evidence_retained": False,
        "source_report": "verifier/ctrf.json",
        "source_report_bytes": (tmp_path / "verifier" / "ctrf.json").stat().st_size,
        "tests": {
            "tests": 5,
            "passed": 4,
            "failed": 1,
            "skipped": 0,
            "pending": 0,
            "other": 0,
        },
        "tool": {"name": "pytest"},
        "nonpassing_tests": [
            {
                "name": "failing case",
                "status": "failed",
                "suite": "feature",
                "filePath": "tests/test_feature.py",
                "message": "expected true",
                "trace": "assert false",
            }
        ],
        "raw_artifacts": {
            "file_count": 3,
            "bytes": sum(
                path.stat().st_size
                for path in (
                    tmp_path / "verifier" / "reward.json",
                    tmp_path / "verifier" / "ctrf.json",
                    tmp_path / "logs" / "verifier.stdout.txt",
                )
            ),
        },
    }


def test_write_compact_verifier_result_prunes_raw_evidence(tmp_path: Path) -> None:
    result = write_verified_cell(tmp_path)

    write_compact_verifier_result(tmp_path, result)

    persisted = json.loads((tmp_path / "result.json").read_text())
    assert persisted["result_schema_version"] == 2
    assert persisted["verifier_summary"]["nonpassing_tests"][0]["name"] == (
        "failing case"
    )
    assert not (tmp_path / "verifier").exists()
    assert not (tmp_path / "logs" / "verifier.stdout.txt").exists()


def test_write_compact_verifier_result_can_retain_raw_evidence(tmp_path: Path) -> None:
    result = write_verified_cell(tmp_path)

    write_compact_verifier_result(
        tmp_path,
        result,
        retain_raw_verifier_evidence=True,
    )

    persisted = json.loads((tmp_path / "result.json").read_text())
    assert persisted["verifier_summary"]["raw_evidence_retained"] is True
    assert (tmp_path / "verifier" / "ctrf.json").is_file()
    assert (tmp_path / "logs" / "verifier.stdout.txt").is_file()


def test_reward_mismatch_preserves_raw_evidence(tmp_path: Path) -> None:
    result = write_verified_cell(tmp_path)
    result["f2p_passed"] = 2

    with pytest.raises(VerifierEvidenceMismatchError, match="f2p_passed"):
        write_compact_verifier_result(tmp_path, result)

    assert not (tmp_path / "result.json").exists()
    assert (tmp_path / "verifier" / "reward.json").is_file()
    assert (tmp_path / "logs" / "verifier.stdout.txt").is_file()


def test_crash_without_ctrf_retains_bounded_stdout_tail(tmp_path: Path) -> None:
    (tmp_path / "verifier").mkdir()
    (tmp_path / "logs").mkdir()
    verifier_stdout = tmp_path / "logs" / "verifier.stdout.txt"
    verifier_stdout.write_text("important prefix\n" + "x" * 40_000)
    result = {
        "task": "crashed-task",
        "reward_binary": 0,
        "reward_partial": 0,
        "verifier_exit": 137,
    }

    compacted = with_compact_verifier_evidence(tmp_path, result)

    summary = cast(dict[str, Any], compacted["verifier_summary"])
    assert summary["source_report"] is None
    assert summary["tests"] is None
    assert summary["nonpassing_tests"] == []
    assert summary["failure_excerpt"] == {
        "source": "logs/verifier.stdout.txt",
        "original_bytes": 40_017,
        "truncated": True,
        "text": "x" * 32_768,
    }


def test_compact_verifier_evidence_keeps_memory_event_counters(tmp_path: Path) -> None:
    result = write_verified_cell(tmp_path)
    (tmp_path / "verifier" / "memory-events.txt").write_text(
        "low 0\nhigh 0\nmax 234\noom 1\noom_kill 1\n"
    )

    compacted = with_compact_verifier_evidence(tmp_path, result)

    summary = cast(dict[str, Any], compacted["verifier_summary"])
    assert summary["memory_events"] == {
        "low": 0,
        "high": 0,
        "max": 234,
        "oom": 1,
        "oom_kill": 1,
    }


def test_write_compact_verifier_result_is_idempotent(tmp_path: Path) -> None:
    result = write_verified_cell(tmp_path)
    write_compact_verifier_result(tmp_path, result)
    result_path = tmp_path / "result.json"
    first_bytes = result_path.read_bytes()
    persisted = json.loads(first_bytes)

    write_compact_verifier_result(tmp_path, persisted)

    assert result_path.read_bytes() == first_bytes


def test_prune_refuses_incomplete_compact_summary(tmp_path: Path) -> None:
    verifier = tmp_path / "verifier"
    verifier.mkdir()
    raw_report = verifier / "ctrf.json"
    raw_report.write_text("raw evidence\n")
    (tmp_path / "result.json").write_text(
        json.dumps(
            {
                "result_schema_version": 2,
                "verifier_summary": {
                    "schema_version": 1,
                    "nonpassing_tests": [],
                    "raw_artifacts": {},
                },
            }
        )
    )

    with pytest.raises(ValueError, match="compact result missing"):
        prune_raw_verifier_evidence(tmp_path)

    assert raw_report.is_file()


def test_failed_test_diagnostics_are_bounded_with_both_ends(tmp_path: Path) -> None:
    result = write_verified_cell(tmp_path)
    report_path = tmp_path / "verifier" / "ctrf.json"
    report = json.loads(report_path.read_text())
    long_message = "begin:" + "x" * 20_000 + ":end"
    report["results"]["tests"][1]["message"] = long_message
    report_path.write_text(json.dumps(report))

    compacted = with_compact_verifier_evidence(tmp_path, result)

    summary = cast(dict[str, Any], compacted["verifier_summary"])
    failed_test = summary["nonpassing_tests"][0]
    retained_message = failed_test["message"]
    assert retained_message.startswith("begin:")
    assert retained_message.endswith(":end")
    assert len(retained_message.encode()) <= 16 * 1024
    assert failed_test["truncated_fields"]["message"] == {
        "original_bytes": len(long_message.encode()),
        "retained_bytes": len(retained_message.encode()),
    }
