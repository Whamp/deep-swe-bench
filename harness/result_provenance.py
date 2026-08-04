"""Validate immutable result provenance for reuse and comparisons."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

_COMMON_RESULT_PROVENANCE_FIELDS = (
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
RESULT_PROVENANCE_FIELDS = (
    *_COMMON_RESULT_PROVENANCE_FIELDS,
    "resource_policy",
    "subject_runtime_identity",
)
_COMPARISON_SHARED_FIELDS = (
    "harness_revision",
    "model",
    "resource_policy",
    "subject",
    "subject_runtime_identity",
    "subject_version",
    "thinking_level",
)
_COMPARISON_TASK_FIELDS = (
    "immutable_image_identities",
    "task_revision",
    "verifier_identity",
)
_MODERN_PROVENANCE_MARKERS = frozenset(
    {
        "config_lock_identity",
        "harness_revision",
        "immutable_image_identities",
        "subject",
        "subject_runtime_identity",
        "subject_version",
        "task_revision",
        "verifier_identity",
    }
)


class ResultProvenance(TypedDict):
    """Define modern setup identity shared by planning and result records."""

    config: str
    config_lock_identity: str | None
    harness_revision: str
    immutable_image_identities: dict[str, str]
    model: str
    rep: int
    resource_policy: NotRequired[dict[str, object]]
    subject: str
    subject_runtime_identity: NotRequired[dict[str, object]]
    subject_version: str
    task: str
    task_revision: str
    thinking_level: str
    verifier_identity: str


class ConfirmedResultProvenance(ResultProvenance):
    """Add the exact confirmed launch that wrote a canonical result."""

    launch_plan_identity: str


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
        field: record[field] for field in RESULT_PROVENANCE_FIELDS if field in record
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


def is_legacy_result_record(record: Mapping[str, object]) -> bool:
    """Return whether a result predates every modern provenance marker."""
    return not any(field in record for field in _MODERN_PROVENANCE_MARKERS)


def _required_result_provenance_fields(
    record: Mapping[str, object],
) -> tuple[str, ...]:
    """Require subject-specific runtime identity only where it exists."""
    if record.get("subject") == "omp":
        return (*_COMMON_RESULT_PROVENANCE_FIELDS, "subject_runtime_identity")
    return _COMMON_RESULT_PROVENANCE_FIELDS


def _comparison_provenance_error(
    result_path: Path,
    mismatches: Mapping[str, object],
) -> ValueError:
    return ValueError(
        "Comparison result provenance mismatch: "
        f"path={result_path}; incompatible fields={dict(mismatches)!r}"
    )


def _comparison_path_mismatches(
    selected: ComparisonResult,
    model: str,
    thinking: str,
    *,
    require_fields: bool,
) -> dict[str, object]:
    """Compare result fields represented by the canonical cell address."""
    expected = {
        "config": selected.config,
        "model": model,
        "rep": selected.rep,
        "task": selected.task,
        "thinking_level": thinking,
    }
    return {
        field: {"expected": value, "recorded": selected.record.get(field)}
        for field, value in expected.items()
        if (require_fields or field in selected.record)
        and selected.record.get(field) != value
    }


def _reference_field_mismatches(
    current: Mapping[str, object],
    reference: Mapping[str, object],
) -> dict[str, object]:
    return {
        field: {"expected": expected, "recorded": current.get(field)}
        for field, expected in reference.items()
        if current.get(field) != expected
    }


def _comparison_shared_mismatches(
    record: Mapping[str, object],
    reference: Mapping[str, object] | None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Compare provenance fixed across every result in a comparison."""
    current = {field: record.get(field) for field in _COMPARISON_SHARED_FIELDS}
    mismatches = (
        {} if reference is None else _reference_field_mismatches(current, reference)
    )
    return current, mismatches


def _comparison_lock_mismatches(
    selected: ComparisonResult,
    config_locks: dict[str, object],
) -> dict[str, object]:
    """Compare one config release's lock across all selected reps."""
    lock_identity = selected.record.get("config_lock_identity")
    if selected.config not in config_locks:
        config_locks[selected.config] = lock_identity
        return {}
    if config_locks[selected.config] == lock_identity:
        return {}
    return {
        "config_lock_identity": {
            "expected": config_locks[selected.config],
            "recorded": lock_identity,
        }
    }


def _comparison_task_mismatches(
    selected: ComparisonResult,
    task_provenance: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Compare task revision, verifier, and images within one paired task."""
    current = {field: selected.record.get(field) for field in _COMPARISON_TASK_FIELDS}
    reference = task_provenance.setdefault(selected.task, current)
    return _reference_field_mismatches(current, reference)


def _require_compatible_legacy_comparison(
    model: str,
    thinking: str,
    selected_results: Sequence[ComparisonResult],
) -> None:
    """Validate only address fields that historical records actually carry."""
    for selected in selected_results:
        mismatches = _comparison_path_mismatches(
            selected,
            model,
            thinking,
            require_fields=False,
        )
        if mismatches:
            raise _comparison_provenance_error(
                selected.result_path,
                mismatches,
            )


def require_compatible_comparison_results(
    model: str,
    thinking: str,
    configs: Sequence[str],
    selected_results: list[ComparisonResult],
    *,
    allow_legacy_results: bool = False,
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
    legacy_results = [
        selected
        for selected in selected_results
        if is_legacy_result_record(selected.record)
    ]
    if allow_legacy_results and legacy_results:
        if len(legacy_results) != len(selected_results):
            raise _comparison_provenance_error(
                legacy_results[0].result_path,
                {
                    "legacy_provenance": (
                        "mixed modern and legacy results are incompatible"
                    )
                },
            )
        _require_compatible_legacy_comparison(
            model,
            thinking,
            selected_results,
        )
        return

    shared_reference: dict[str, object] | None = None
    config_locks: dict[str, object] = {}
    task_provenance: dict[str, dict[str, object]] = {}
    for selected in selected_results:
        record = selected.record
        mismatches = _comparison_path_mismatches(
            selected,
            model,
            thinking,
            require_fields=True,
        )
        missing = [
            field
            for field in _required_result_provenance_fields(record)
            if field not in record
        ]
        if missing:
            mismatches["missing_provenance"] = missing
        current_shared, shared_mismatches = _comparison_shared_mismatches(
            record,
            shared_reference,
        )
        if shared_reference is None:
            shared_reference = current_shared
        mismatches.update(shared_mismatches)
        mismatches.update(_comparison_lock_mismatches(selected, config_locks))
        mismatches.update(_comparison_task_mismatches(selected, task_provenance))
        if mismatches:
            raise _comparison_provenance_error(
                selected.result_path,
                mismatches,
            )
