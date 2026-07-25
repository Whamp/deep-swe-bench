"""Validate immutable result provenance for reuse and comparisons."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

RESULT_PROVENANCE_FIELDS = (
    "config",
    "config_lock_identity",
    "harness_revision",
    "immutable_image_identities",
    "model",
    "rep",
    "subject",
    "subject_version",
    "task",
    "task_revision",
    "thinking_level",
    "verifier_identity",
)
_COMPARISON_SHARED_FIELDS = (
    "harness_revision",
    "model",
    "subject",
    "subject_version",
    "task_revision",
    "thinking_level",
)
_COMPARISON_TASK_FIELDS = (
    "immutable_image_identities",
    "verifier_identity",
)


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Pair one selected result record with its canonical cell address."""

    result_path: Path
    config: str
    task: str
    rep: int
    record: dict[str, object]


def read_result_record(
    result_path: Path,
    *,
    error_prefix: str = "Result provenance mismatch",
) -> Mapping[str, object]:
    """Read one canonical result as a provenance-bearing JSON object."""
    try:
        record = json.loads(result_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"{error_prefix}: path={result_path}; result is unreadable: {error}"
        ) from error
    if not isinstance(record, Mapping):
        raise TypeError(
            f"{error_prefix}: path={result_path}; result must be a JSON object"
        )
    return cast(Mapping[str, object], record)


def recorded_result_provenance(
    record: Mapping[str, object],
) -> dict[str, object]:
    """Retain only provenance actually recorded by a result artifact."""
    return {
        field: record[field]
        for field in RESULT_PROVENANCE_FIELDS
        if field in record
    }


def result_file_identity(result_path: Path) -> str:
    """Identify the exact immutable result bytes reviewed for reuse."""
    return f"sha256:{hashlib.sha256(result_path.read_bytes()).hexdigest()}"


def result_provenance_mismatches(
    record: Mapping[str, object],
    expected: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Return every recorded result field incompatible with expected setup."""
    return {
        field: {"expected": value, "recorded": record.get(field)}
        for field, value in expected.items()
        if record.get(field) != value
    }


def _comparison_provenance_error(
    result_path: Path,
    mismatches: Mapping[str, object],
) -> ValueError:
    return ValueError(
        "Comparison result provenance mismatch: "
        f"path={result_path}; incompatible fields={dict(mismatches)!r}"
    )


def require_compatible_comparison_results(
    model: str,
    thinking: str,
    configs: Sequence[str],
    selected_results: list[ComparisonResult],
) -> None:
    """Reject selected comparison reps that do not share one exact setup."""
    config_order = {config: index for index, config in enumerate(configs)}
    selected_results.sort(
        key=lambda result: (
            config_order[result.config],
            result.task,
            result.rep,
        )
    )
    shared_reference: dict[str, object] | None = None
    config_locks: dict[str, object] = {}
    task_provenance: dict[str, dict[str, object]] = {}
    for selected in selected_results:
        record = selected.record
        missing = [
            field for field in RESULT_PROVENANCE_FIELDS if field not in record
        ]
        expected_path_fields = {
            "config": selected.config,
            "model": model,
            "rep": selected.rep,
            "task": selected.task,
            "thinking_level": thinking,
        }
        mismatches: dict[str, object] = {
            field: {"expected": value, "recorded": record.get(field)}
            for field, value in expected_path_fields.items()
            if record.get(field) != value
        }
        if missing:
            mismatches["missing_provenance"] = missing
        current_shared = {
            field: record.get(field) for field in _COMPARISON_SHARED_FIELDS
        }
        if shared_reference is None:
            shared_reference = current_shared
        else:
            for field, expected in shared_reference.items():
                if current_shared[field] != expected:
                    mismatches[field] = {
                        "expected": expected,
                        "recorded": current_shared[field],
                    }
        lock_identity = record.get("config_lock_identity")
        if selected.config not in config_locks:
            config_locks[selected.config] = lock_identity
        elif config_locks[selected.config] != lock_identity:
            mismatches["config_lock_identity"] = {
                "expected": config_locks[selected.config],
                "recorded": lock_identity,
            }
        current_task = {
            field: record.get(field) for field in _COMPARISON_TASK_FIELDS
        }
        if selected.task not in task_provenance:
            task_provenance[selected.task] = current_task
        else:
            for field, expected in task_provenance[selected.task].items():
                if current_task[field] != expected:
                    mismatches[field] = {
                        "expected": expected,
                        "recorded": current_task[field],
                    }
        if mismatches:
            raise _comparison_provenance_error(
                selected.result_path,
                mismatches,
            )
