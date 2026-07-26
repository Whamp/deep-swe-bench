"""Evaluate confirmed-launch preflight evidence after subject execution."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import TypedDict, cast


class PreflightDiagnostic(TypedDict):
    """Describe one failed generic or config-authored requirement."""

    reason: str
    requirement: str
    target: str


def preflight_diagnostic(
    requirement: str,
    target: str,
    reason: str,
) -> PreflightDiagnostic:
    """Build one stable structured preflight failure diagnostic."""
    return {"reason": reason, "requirement": requirement, "target": target}


def evaluate_generic_preflight(
    cell_root: Path,
    result_record: Mapping[str, object],
) -> list[PreflightDiagnostic]:
    """Evaluate subject, native usage, and RPC transport evidence."""
    diagnostics: list[PreflightDiagnostic] = []
    if result_record.get("agent_exit") != 0:
        diagnostics.append(
            preflight_diagnostic(
                "subject_cell",
                "result.agent_exit",
                f"expected 0, got {result_record.get('agent_exit')!r}",
            )
        )
    if result_record.get("agent_timed_out"):
        diagnostics.append(
            preflight_diagnostic(
                "subject_cell",
                "result.agent_timed_out",
                "expected false, got true",
            )
        )
    total_tokens = result_record.get("total_tokens")
    if (
        not isinstance(total_tokens, int | float)
        or isinstance(total_tokens, bool)
        or total_tokens <= 0
    ):
        diagnostics.append(
            preflight_diagnostic(
                "usage_evidence",
                "result.total_tokens",
                f"expected a positive number, got {total_tokens!r}",
            )
        )
    if not list((cell_root / "session").glob("*.jsonl")):
        diagnostics.append(
            preflight_diagnostic(
                "native_session_evidence",
                "session/*.jsonl",
                "required native session evidence is missing",
            )
        )
    rpc_log = cell_root / "logs" / "pi-rpc-runner.jsonl"
    rpc_text = rpc_log.read_text(errors="replace") if rpc_log.is_file() else ""
    for marker, target in (
        ('"event":"prompt_sent"', "prompt_sent"),
        ('"event":"quiescent"', "quiescent"),
        ('"transport":"rpc"', "transport=rpc"),
    ):
        if marker not in rpc_text:
            diagnostics.append(
                preflight_diagnostic(
                    "transport_evidence",
                    f"logs/pi-rpc-runner.jsonl:{target}",
                    "required RPC transport evidence is missing",
                )
            )
    return diagnostics


def _result_value(
    result_record: Mapping[str, object],
    dotted_field: str,
) -> object:
    value: object = result_record
    for part in dotted_field.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = cast(Mapping[str, object], value)[part]
    return value


def _evaluate_structured_results(
    contract: Mapping[str, object],
    result_record: Mapping[str, object],
) -> list[PreflightDiagnostic]:
    diagnostics: list[PreflightDiagnostic] = []
    for field, expected in cast(
        Mapping[str, object], contract.get("equalsResultValues", {})
    ).items():
        actual = _result_value(result_record, field)
        if actual != expected:
            diagnostics.append(
                preflight_diagnostic(
                    "equalsResultValues",
                    f"result.{field}",
                    f"expected {expected!r}, got {actual!r}",
                )
            )
    for field, minimum in cast(
        Mapping[str, object], contract.get("minResultValues", {})
    ).items():
        actual = _result_value(result_record, field)
        if (
            not isinstance(actual, int | float)
            or isinstance(actual, bool)
            or not isinstance(minimum, int | float)
            or actual < minimum
        ):
            diagnostics.append(
                preflight_diagnostic(
                    "minResultValues",
                    f"result.{field}",
                    f"expected at least {minimum!r}, got {actual!r}",
                )
            )
    return diagnostics


def _evaluate_required_files(
    contract: Mapping[str, object],
    cell_root: Path,
    repository_root: Path,
) -> list[PreflightDiagnostic]:
    diagnostics: list[PreflightDiagnostic] = []
    for assertion_kind, root in (
        ("requireFiles", cell_root),
        ("requireRepoFiles", repository_root),
    ):
        for pattern in cast(list[str], contract.get(assertion_kind, [])):
            if not any(path.is_file() for path in root.glob(pattern)):
                diagnostics.append(
                    preflight_diagnostic(
                        assertion_kind,
                        pattern,
                        "required file evidence is missing",
                    )
                )
    return diagnostics


def _evaluate_usage_records(
    contract: Mapping[str, object],
    cell_root: Path,
) -> list[PreflightDiagnostic]:
    diagnostics: list[PreflightDiagnostic] = []
    assertions = cast(
        list[Mapping[str, object]], contract.get("requireUsageRecords", [])
    )
    for assertion in assertions:
        globs = cast(list[str], assertion["globs"])
        expected = cast(Mapping[str, object], assertion["equals"])
        minimum = cast(int, assertion["minimum"])
        matching_records = 0
        for pattern in globs:
            for usage_path in cell_root.glob(pattern):
                if not usage_path.is_file():
                    continue
                for line in usage_path.read_text(errors="replace").splitlines():
                    try:
                        record: object = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, Mapping):
                        continue
                    structured_record = cast(Mapping[str, object], record)
                    if all(
                        _result_value(structured_record, field) == value
                        for field, value in expected.items()
                    ):
                        matching_records += 1
        if matching_records < minimum:
            diagnostics.append(
                preflight_diagnostic(
                    "requireUsageRecords",
                    f"{globs[0]}:structured-records",
                    f"expected at least {minimum}, got {matching_records}",
                )
            )
    return diagnostics


def _iter_json_records(
    path: Path,
    record_format: str,
) -> Iterator[Mapping[str, object]]:
    """Yield object records from one JSON object or JSONL artifact."""
    try:
        raw = path.read_text(errors="replace")
    except OSError:
        return
    if record_format == "json":
        try:
            record: object = json.loads(raw)
        except json.JSONDecodeError:
            return
        if isinstance(record, Mapping):
            yield cast(Mapping[str, object], record)
        return
    for line in raw.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, Mapping):
            yield cast(Mapping[str, object], record)


def _evaluate_json_records(
    contract: Mapping[str, object],
    cell_root: Path,
) -> list[PreflightDiagnostic]:
    """Count JSON records whose dotted fields match contract values."""
    diagnostics: list[PreflightDiagnostic] = []
    assertions = cast(
        list[Mapping[str, object]], contract.get("requireJsonRecords", [])
    )
    for assertion in assertions:
        globs = cast(list[str], assertion["globs"])
        record_format = cast(str, assertion["format"])
        expected = cast(Mapping[str, object], assertion["equals"])
        minimum = cast(int, assertion["minimum"])
        matching_records = 0
        for pattern in globs:
            for path in cell_root.glob(pattern):
                if not path.is_file():
                    continue
                for record in _iter_json_records(path, record_format):
                    if all(
                        _result_value(record, field) == value
                        for field, value in expected.items()
                    ):
                        matching_records += 1
        if matching_records < minimum:
            diagnostics.append(
                preflight_diagnostic(
                    "requireJsonRecords",
                    f"{globs[0]}:{record_format}-records",
                    f"expected at least {minimum}, got {matching_records}",
                )
            )
    return diagnostics


def _evaluate_extension_markers(
    contract: Mapping[str, object],
    cell_root: Path,
) -> list[PreflightDiagnostic]:
    diagnostics: list[PreflightDiagnostic] = []
    for assertion_kind, marker_required in (
        ("requireExtensionMarkers", True),
        ("forbidExtensionMarkers", False),
    ):
        assertions = cast(
            list[Mapping[str, object]], contract.get(assertion_kind, [])
        )
        for assertion in assertions:
            globs = cast(list[str], assertion["globs"])
            marker = cast(str, assertion["marker"])
            marker_found = any(
                marker in path.read_text(errors="replace")
                for pattern in globs
                for path in cell_root.glob(pattern)
                if path.is_file()
            )
            failed = not marker_found if marker_required else marker_found
            if failed:
                expectation = "present" if marker_required else "absent"
                diagnostics.append(
                    preflight_diagnostic(
                        assertion_kind,
                        f"{globs[0]}:{marker}",
                        f"extension machine marker must be {expectation}",
                    )
                )
    return diagnostics


def evaluate_config_preflight(
    repository_root: Path,
    cell_root: Path,
    contract_path: Path | None,
    result_record: Mapping[str, object],
) -> list[PreflightDiagnostic]:
    """Evaluate every durable assertion in a versioned smoke contract."""
    if contract_path is None:
        return []
    try:
        contract_value: object = json.loads(contract_path.read_text())
    except (json.JSONDecodeError, OSError) as error:
        return [
            preflight_diagnostic(
                "smoke_contract",
                str(contract_path),
                f"contract could not be evaluated: {error}",
            )
        ]
    if not isinstance(contract_value, Mapping):
        return [
            preflight_diagnostic(
                "smoke_contract",
                str(contract_path),
                "contract root is not an object",
            )
        ]
    contract = cast(Mapping[str, object], contract_value)
    return [
        *_evaluate_structured_results(contract, result_record),
        *_evaluate_required_files(contract, cell_root, repository_root),
        *_evaluate_usage_records(contract, cell_root),
        *_evaluate_json_records(contract, cell_root),
        *_evaluate_extension_markers(contract, cell_root),
    ]
