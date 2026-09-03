"""Build self-contained verifier evidence for persisted benchmark results."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import cast

RESULT_SCHEMA_VERSION = 2
VERIFIER_SUMMARY_SCHEMA_VERSION = 1
RAW_VERIFIER_RETENTION_ENV = "DEEP_SWE_RETAIN_RAW_VERIFIER_EVIDENCE"
_FAILURE_EXCERPT_BYTES = 32 * 1024
_TEST_DIAGNOSTIC_BYTES = 16 * 1024
_TRUNCATION_MARKER = b"\n...[truncated]...\n"
_NONPASSING_TEST_STATUSES = frozenset({"failed", "skipped", "pending", "other"})
_REWARD_RESULT_FIELDS = {
    "reward": "reward_binary",
    "partial": "reward_partial",
    "f2p": "f2p",
    "f2p_passed": "f2p_passed",
    "f2p_total": "f2p_total",
    "p2p": "p2p",
    "p2p_passed": "p2p_passed",
    "p2p_total": "p2p_total",
}


class VerifierEvidenceMismatchError(ValueError):
    """Report raw verifier evidence that disagrees with its result record."""


def raw_verifier_retention_requested() -> bool:
    """Return whether the operator requested full raw verifier retention."""
    return os.environ.get(RAW_VERIFIER_RETENTION_ENV) == "1"


def _read_json_object(path: Path) -> dict[str, object]:
    document: object = json.loads(path.read_text())
    if not isinstance(document, dict):
        raise TypeError(f"Verifier evidence JSON must be an object: {path}")
    return cast(dict[str, object], document)


def _validate_reward_result_fields(
    cell: Path,
    result_record: Mapping[str, object],
) -> None:
    reward_path = cell / "verifier" / "reward.json"
    if not reward_path.is_file():
        return
    reward = _read_json_object(reward_path)
    mismatches = {
        result_field: {
            "result": result_record[result_field],
            "reward": reward[reward_field],
        }
        for reward_field, result_field in _REWARD_RESULT_FIELDS.items()
        if reward_field in reward
        and result_field in result_record
        and reward[reward_field] != result_record[result_field]
    }
    if mismatches:
        raise VerifierEvidenceMismatchError(
            "Verifier reward evidence mismatch: "
            f"cell={cell}; fields={sorted(mismatches)}"
        )


def _raw_verifier_artifact_totals(cell: Path) -> dict[str, int]:
    paths = list((cell / "verifier").rglob("*"))
    verifier_stdout = cell / "logs" / "verifier.stdout.txt"
    if verifier_stdout.is_file():
        paths.append(verifier_stdout)
    files = [path for path in paths if path.is_file()]
    return {
        "file_count": len(files),
        "bytes": sum(path.stat().st_size for path in files),
    }


def _bounded_test_diagnostic(value: str) -> tuple[str, dict[str, int] | None]:
    raw_value = value.encode()
    if len(raw_value) <= _TEST_DIAGNOSTIC_BYTES:
        return value, None
    retained_bytes = _TEST_DIAGNOSTIC_BYTES - len(_TRUNCATION_MARKER)
    prefix_bytes = retained_bytes // 2
    suffix_bytes = retained_bytes - prefix_bytes
    retained = (
        raw_value[:prefix_bytes].decode("utf-8", errors="ignore")
        + _TRUNCATION_MARKER.decode()
        + raw_value[-suffix_bytes:].decode("utf-8", errors="ignore")
    )
    return retained, {
        "original_bytes": len(raw_value),
        "retained_bytes": len(retained.encode()),
    }


def _compact_ctrf_test(test: Mapping[str, object]) -> dict[str, object]:
    compacted = {
        key: value
        for key, value in test.items()
        if key
        in {
            "name",
            "status",
            "suite",
            "filePath",
            "duration",
            "message",
            "trace",
        }
    }
    truncated_fields: dict[str, dict[str, int]] = {}
    for field in ("message", "trace"):
        value = compacted.get(field)
        if isinstance(value, str):
            compacted[field], truncation = _bounded_test_diagnostic(value)
            if truncation is not None:
                truncated_fields[field] = truncation
    if truncated_fields:
        compacted["truncated_fields"] = truncated_fields
    return compacted


def _find_ctrf_report(cell: Path) -> Path | None:
    for relative_path in (
        "verifier/ctrf.json",
        "verifier/reports/new-ctrf.json",
        "verifier/reports/new_ctrf.json",
    ):
        candidate = cell / relative_path
        if candidate.is_file():
            return candidate
    return None


def _read_verifier_memory_events(cell: Path) -> dict[str, int] | None:
    memory_events_path = cell / "verifier" / "memory-events.txt"
    if not memory_events_path.is_file():
        return None
    counters: dict[str, int] = {}
    for line in memory_events_path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 2:
            try:
                counters[fields[0]] = int(fields[1])
            except ValueError:
                continue
    return counters or None


def _read_verifier_failure_excerpt(cell: Path) -> dict[str, object] | None:
    stdout_path = cell / "logs" / "verifier.stdout.txt"
    if not stdout_path.is_file():
        return None
    raw_output = stdout_path.read_bytes()
    excerpt = raw_output[-_FAILURE_EXCERPT_BYTES:]
    return {
        "source": str(stdout_path.relative_to(cell)),
        "original_bytes": len(raw_output),
        "truncated": len(excerpt) < len(raw_output),
        "text": excerpt.decode("utf-8", errors="replace"),
    }


def with_compact_verifier_evidence(
    cell: Path,
    result_record: Mapping[str, object],
    *,
    retain_raw_verifier_evidence: bool = False,
) -> dict[str, object]:
    """Return a schema-v2 result containing compact verifier test evidence."""
    _validate_reward_result_fields(cell, result_record)
    report_path = _find_ctrf_report(cell)
    test_summary: dict[str, object] | None = None
    tool: dict[str, object] | None = None
    nonpassing_tests: list[dict[str, object]] = []
    if report_path is not None:
        report = _read_json_object(report_path)
        results = report.get("results")
        if not isinstance(results, dict):
            raise TypeError(f"Verifier CTRF results must be an object: {report_path}")
        raw_summary = results.get("summary")
        raw_tool = results.get("tool")
        tests = results.get("tests")
        if not isinstance(raw_summary, dict) or not isinstance(raw_tool, dict):
            raise TypeError(
                f"Verifier CTRF summary and tool must be objects: {report_path}"
            )
        if not isinstance(tests, list):
            raise TypeError(f"Verifier CTRF tests must be a list: {report_path}")
        test_summary = dict(raw_summary)
        tool = dict(raw_tool)
        nonpassing_tests = [
            _compact_ctrf_test(test)
            for test in tests
            if isinstance(test, dict)
            and test.get("status") in _NONPASSING_TEST_STATUSES
        ]
    verifier_summary: dict[str, object] = {
        "schema_version": VERIFIER_SUMMARY_SCHEMA_VERSION,
        "raw_evidence_retained": retain_raw_verifier_evidence,
        "source_report": (
            str(report_path.relative_to(cell)) if report_path is not None else None
        ),
        "tests": test_summary,
        "tool": tool,
        "nonpassing_tests": nonpassing_tests,
        "raw_artifacts": _raw_verifier_artifact_totals(cell),
    }
    if report_path is not None:
        verifier_summary["source_report_bytes"] = report_path.stat().st_size
    memory_events = _read_verifier_memory_events(cell)
    if memory_events is not None:
        verifier_summary["memory_events"] = memory_events
    if report_path is None or result_record.get("verifier_exit") not in {None, 0, "0"}:
        failure_excerpt = _read_verifier_failure_excerpt(cell)
        if failure_excerpt is not None:
            verifier_summary["failure_excerpt"] = failure_excerpt
    compacted = dict(result_record)
    compacted["result_schema_version"] = RESULT_SCHEMA_VERSION
    compacted["verifier_summary"] = verifier_summary
    return compacted


def _atomic_write_json(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(document, output, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        temporary_path.replace(path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary_path.unlink(missing_ok=True)


def _is_nonnegative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def is_compact_verifier_result(result_record: Mapping[str, object]) -> bool:
    """Return whether a result contains the complete versioned verifier summary."""
    summary = result_record.get("verifier_summary")
    if (
        result_record.get("result_schema_version") != RESULT_SCHEMA_VERSION
        or not isinstance(summary, dict)
        or summary.get("schema_version") != VERIFIER_SUMMARY_SCHEMA_VERSION
    ):
        return False
    raw_artifacts = summary.get("raw_artifacts")
    nonpassing_tests = summary.get("nonpassing_tests")
    source_report = summary.get("source_report")
    tests = summary.get("tests")
    tool = summary.get("tool")
    return (
        isinstance(summary.get("raw_evidence_retained"), bool)
        and "source_report" in summary
        and (source_report is None or isinstance(source_report, str))
        and "tests" in summary
        and (tests is None or isinstance(tests, dict))
        and "tool" in summary
        and (tool is None or isinstance(tool, dict))
        and isinstance(nonpassing_tests, list)
        and all(isinstance(test, dict) for test in nonpassing_tests)
        and isinstance(raw_artifacts, dict)
        and _is_nonnegative_int(raw_artifacts.get("file_count"))
        and _is_nonnegative_int(raw_artifacts.get("bytes"))
    )


def prune_raw_verifier_evidence(cell: Path) -> None:
    """Delete raw verifier files only for a validated compact result."""
    result_path = cell / "result.json"
    persisted = _read_json_object(result_path)
    if not is_compact_verifier_result(persisted):
        raise ValueError(
            "Raw verifier evidence prune refused: compact result missing "
            f"at {result_path}"
        )
    summary = cast(dict[str, object], persisted["verifier_summary"])
    if summary.get("raw_evidence_retained") is True:
        return
    verifier_directory = cell / "verifier"
    if verifier_directory.exists():
        shutil.rmtree(verifier_directory)
    (cell / "logs" / "verifier.stdout.txt").unlink(missing_ok=True)


def write_compact_verifier_result(
    cell: Path,
    result_record: Mapping[str, object],
    *,
    retain_raw_verifier_evidence: bool = False,
) -> dict[str, object]:
    """Atomically publish a compact result before pruning raw verifier files."""
    result_path = cell / "result.json"
    if is_compact_verifier_result(result_record):
        compacted = dict(result_record)
        if not result_path.is_file():
            _atomic_write_json(result_path, compacted)
    else:
        compacted = with_compact_verifier_evidence(
            cell,
            result_record,
            retain_raw_verifier_evidence=retain_raw_verifier_evidence,
        )
        _atomic_write_json(result_path, compacted)
    prune_raw_verifier_evidence(cell)
    return compacted
