"""Build and evaluate the stock-Pi baseline trajectory dataset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.stats import rankdata

from .extractor import (
    PROCESS_FEATURE_NAMES,
    SEQUENCE_FEATURE_NAMES,
    NativeSessionParse,
    extract_session_process_features,
    parse_native_session,
    terminal_session_is_truncated,
)

LENGTH_FEATURE_NAMES = (
    "log_total_tokens",
    "log_turns",
    "log_agent_wall_s",
    "within_task_token_robust_z",
    "within_task_turn_robust_z",
)
CATEGORICAL_CONTROL_NAMES = ("model", "thinking_level", "config")
OPENING_PREDICTOR_NAMES = (
    "has_successful_source_mutation",
    "tool_calls_before_first_source_mutation",
    "reads_before_first_source_mutation",
    "unique_paths_read_before_first_source_mutation",
    "tests_before_first_source_mutation",
    "failed_tests_before_first_source_mutation",
    "first_source_mutation_call_fraction",
    "opening_ten_read_fraction",
    "opening_ten_source_mutation_fraction",
    "first_source_mutation_boundary_uncertain",
)
MUTATION_STYLE_PREDICTOR_NAMES = (
    "source_edit_calls",
    "source_write_calls",
    "failed_edit_calls",
    "failed_write_calls",
    "first_source_mutation_is_write",
    "mutation_tool_switches",
    "write_then_edit_same_target",
    "repeated_write_targets",
)
TEST_FLOW_PREDICTOR_NAMES = (
    "tests_after_first_source_mutation",
    "tool_calls_to_first_post_mutation_test",
    "source_mutations_before_first_post_mutation_test",
    "longest_source_mutation_streak_without_test",
    "tests_after_final_source_mutation",
    "has_passing_test_after_final_source_mutation",
    "source_mutations_after_passing_test",
    "pass_mutation_fail_patterns",
    "implementation_to_validation_transitions",
    "validation_to_implementation_backtracks",
)
SEQUENCE_PREDICTOR_NAMES = (
    OPENING_PREDICTOR_NAMES + MUTATION_STYLE_PREDICTOR_NAMES + TEST_FLOW_PREDICTOR_NAMES
)
PREDICTOR_SPECIFICATIONS = {
    "length": LENGTH_FEATURE_NAMES,
    "process": LENGTH_FEATURE_NAMES + PROCESS_FEATURE_NAMES,
    "opening": LENGTH_FEATURE_NAMES + OPENING_PREDICTOR_NAMES,
    "mutation_style": LENGTH_FEATURE_NAMES + MUTATION_STYLE_PREDICTOR_NAMES,
    "test_flow": LENGTH_FEATURE_NAMES + TEST_FLOW_PREDICTOR_NAMES,
    "sequence": LENGTH_FEATURE_NAMES + SEQUENCE_PREDICTOR_NAMES,
    "all_process": LENGTH_FEATURE_NAMES
    + PROCESS_FEATURE_NAMES
    + SEQUENCE_PREDICTOR_NAMES,
}
STOCK_PI_BASELINE_CONFIGS = (
    "baseline",
    "baseline@1.0.0",
    "baseline@1.1.0",
)
_REQUIRED_RESULT_FIELDS = (
    "task",
    "config",
    "rep",
    "model",
    "thinking_level",
    "reward_binary",
    "reward_partial",
    "total_tokens",
    "turns",
    "agent_wall_s",
    "agent_exit",
    "agent_timed_out",
    "verifier_exit",
)
_ARTIFACT_FIELDS = (
    "has_model_patch",
    "has_verifier_directory",
    "has_verifier_reward",
    "has_verifier_ctrf",
    "has_verifier_log",
)
_RESERVED_ROOT_DISPOSITIONS = {
    "_contaminated": "quarantined",
    "_runs": "run_state",
    "_archives": "archived",
    "_diagnostics": "diagnostic",
    "_throughput": "throughput",
}


def is_canonical_result_path(result_path: Path, results_root: Path) -> bool:
    """Accept only results/<model>/<thinking>/<config>/<task>/repN/result.json."""
    try:
        parts = result_path.relative_to(results_root).parts
    except ValueError:
        return False
    return (
        len(parts) == 6
        and result_path.name == "result.json"
        and not parts[0].startswith("_")
        and parts[4].startswith("rep")
        and parts[4][3:].isdigit()
    )


def classify_primary_model_disposition(
    result: dict[str, Any],
    *,
    session_count: int,
    terminal_stop_reason: str | None = None,
) -> str:
    """Assign one primary exclusion/censoring disposition in precedence order."""
    if session_count == 0:
        return "missing_session"
    if session_count > 1:
        return "ambiguous_multiple_sessions"
    if result.get("agent_timed_out") is True or result.get("agent_exit") == "timeout":
        return "agent_timeout"
    if terminal_stop_reason and terminal_stop_reason.lower() in {
        "length",
        "max_tokens",
        "max_output_tokens",
        "output_limit",
    }:
        return "terminal_output_truncation"
    if result.get("agent_exit") == "degeneration":
        return "agent_degeneration_truncation"
    if result.get("agent_exit") != 0:
        return "agent_infrastructure_error"
    verifier_exit = result.get("verifier_exit")
    if verifier_exit == "timeout":
        return "verifier_timeout"
    if verifier_exit == "skipped_empty_patch":
        return "verifier_skipped_empty_patch"
    if verifier_exit != 0:
        return "verifier_error"
    if result.get("reward_binary") not in (0, 1):
        return "invalid_binary_reward"
    if not isinstance(result.get("reward_partial"), (int, float)):
        return "missing_partial_reward"
    return "eligible"


def build_task_folds(
    rows: Sequence[dict[str, Any]], fold_count: int
) -> list[dict[str, list[str]]]:
    """Build deterministic size-balanced folds whose task sets never overlap."""
    task_counts = Counter(str(row["task"]) for row in rows)
    if fold_count < 2 or fold_count > len(task_counts):
        raise ValueError("fold_count must be between 2 and the number of tasks")
    ordered_tasks = sorted(
        task_counts,
        key=lambda task: (
            -task_counts[task],
            _stable_hash(task),
            task,
        ),
    )
    fold_tasks: list[list[str]] = [[] for _ in range(fold_count)]
    fold_sizes = [0] * fold_count
    for task in ordered_tasks:
        fold_index = min(range(fold_count), key=lambda idx: (fold_sizes[idx], idx))
        fold_tasks[fold_index].append(task)
        fold_sizes[fold_index] += task_counts[task]
    all_tasks = set(task_counts)
    return [
        {
            "train_tasks": sorted(all_tasks - set(test_tasks)),
            "test_tasks": sorted(test_tasks),
        }
        for test_tasks in fold_tasks
    ]


def discover_result_inventory(
    results_root: Path,
    *,
    allowed_configs: Collection[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Audit selected result schemas and artifacts without mutating the result tree."""
    allowed_config_set = set(allowed_configs) if allowed_configs is not None else None
    path_dispositions: Counter[str] = Counter()
    excluded_config_counts: Counter[str] = Counter()
    selected_result_paths: set[Path] = set()
    result_field_presence: Counter[str] = Counter()
    result_field_types: dict[str, Counter[str]] = defaultdict(Counter)
    verifier_reward_field_presence: Counter[str] = Counter()
    verifier_reward_field_types: dict[str, Counter[str]] = defaultdict(Counter)
    ctrf_top_level_fields: Counter[str] = Counter()
    ctrf_summary_field_presence: Counter[str] = Counter()
    ctrf_summary_field_types: dict[str, Counter[str]] = defaultdict(Counter)
    ctrf_path_variants: Counter[str] = Counter()
    patch_schema: Counter[str] = Counter()
    canonical_rows: list[dict[str, Any]] = []
    malformed_results: list[str] = []

    candidates = sorted(results_root.rglob("result.json"))
    for result_path in candidates:
        relative = result_path.relative_to(results_root)
        top = relative.parts[0]
        if not is_canonical_result_path(result_path, results_root):
            path_dispositions[_RESERVED_ROOT_DISPOSITIONS.get(top, "noncanonical")] += 1
            continue
        path_config = relative.parts[2]
        if allowed_config_set is not None and path_config not in allowed_config_set:
            path_dispositions["canonical_excluded_config"] += 1
            excluded_config_counts[path_config] += 1
            continue
        path_dispositions["canonical"] += 1
        selected_result_paths.add(result_path)
        try:
            result = json.loads(result_path.read_text())
        except (OSError, json.JSONDecodeError):
            malformed_results.append(relative.as_posix())
            continue
        if not isinstance(result, dict):
            malformed_results.append(relative.as_posix())
            continue
        for name, value in result.items():
            result_field_presence[name] += 1
            result_field_types[name][type(value).__name__] += 1

        cell_path = result_path.parent
        sessions = sorted((cell_path / "session").glob("*.jsonl"))
        patch_path = cell_path / "artifacts" / "model.patch"
        if patch_path.is_file():
            patch_size = patch_path.stat().st_size
            patch_schema["present"] += 1
            patch_schema["empty"] += int(patch_size == 0)
            patch_schema["nonempty"] += int(patch_size > 0)
            patch_schema["size_matches_result_patch_bytes"] += int(
                patch_size == result.get("patch_bytes")
            )
            with patch_path.open("rb") as patch_file:
                patch_prefix = patch_file.read(4096)
            patch_schema["unified_diff_header"] += int(b"diff --git " in patch_prefix)
        else:
            patch_schema["missing"] += 1

        reward_path = cell_path / "verifier" / "reward.json"
        reward_record = _load_json_object(reward_path)
        for name, value in reward_record.items():
            verifier_reward_field_presence[name] += 1
            verifier_reward_field_types[name][type(value).__name__] += 1
        ctrf_path = _first_verifier_ctrf(cell_path)
        if ctrf_path is not None:
            ctrf_path_variants[ctrf_path.relative_to(cell_path).as_posix()] += 1
            ctrf_record = _load_json_object(ctrf_path)
            ctrf_top_level_fields.update(ctrf_record.keys())
            results_record = ctrf_record.get("results")
            summary_record = (
                results_record.get("summary")
                if isinstance(results_record, dict)
                else None
            )
            if isinstance(summary_record, dict):
                for name, value in summary_record.items():
                    ctrf_summary_field_presence[name] += 1
                    ctrf_summary_field_types[name][type(value).__name__] += 1

        identity_mismatches = _result_identity_mismatches(
            result, result_path, results_root
        )
        row = {
            "cell_id": relative.parent.as_posix(),
            "result_path": str(result_path),
            "task": result.get("task"),
            "config": result.get("config"),
            "rep": result.get("rep"),
            "model": result.get("model"),
            "thinking_level": result.get("thinking_level"),
            "language": result.get("language"),
            "category": result.get("category"),
            "reward_binary": result.get("reward_binary"),
            "reward_partial": result.get("reward_partial"),
            "total_tokens": result.get("total_tokens"),
            "turns": result.get("turns"),
            "tool_calls": result.get("tool_calls"),
            "agent_wall_s": result.get("agent_wall_s"),
            "agent_exit": result.get("agent_exit"),
            "agent_timed_out": result.get("agent_timed_out"),
            "agent_resource_exhausted": result.get("agent_resource_exhausted"),
            "verifier_exit": result.get("verifier_exit"),
            "patch_bytes": result.get("patch_bytes"),
            "session_count": len(sessions),
            "session_path": str(sessions[0]) if len(sessions) == 1 else "",
            "session_bytes": sessions[0].stat().st_size if len(sessions) == 1 else 0,
            "identity_mismatches": ";".join(identity_mismatches),
            "has_model_patch": patch_path.is_file(),
            "has_verifier_directory": (cell_path / "verifier").is_dir(),
            "has_verifier_reward": (cell_path / "verifier" / "reward.json").is_file(),
            "has_verifier_ctrf": ctrf_path is not None,
            "has_verifier_log": (cell_path / "verifier" / "run.log").is_file(),
            "resource_policy_present": isinstance(result.get("resource_policy"), dict),
        }
        missing_required = [
            name for name in _REQUIRED_RESULT_FIELDS if name not in result
        ]
        if identity_mismatches:
            row["primary_disposition"] = "result_identity_mismatch"
        elif missing_required:
            row["primary_disposition"] = "missing_required_result_field"
        else:
            row["primary_disposition"] = classify_primary_model_disposition(
                result, session_count=len(sessions)
            )
        canonical_rows.append(row)

    native_session_dispositions: Counter[str] = Counter()
    native_session_candidates = [
        path for path in results_root.rglob("*.jsonl") if path.parent.name == "session"
    ]
    for session_path in native_session_candidates:
        top = session_path.relative_to(results_root).parts[0]
        result_path = session_path.parent.parent / "result.json"
        if result_path in selected_result_paths:
            native_session_dispositions["attached_to_selected_canonical_result"] += 1
        elif (
            is_canonical_result_path(result_path, results_root)
            and result_path.is_file()
        ):
            native_session_dispositions["attached_to_excluded_canonical_result"] += 1
        elif top.startswith("_"):
            native_session_dispositions[
                _RESERVED_ROOT_DISPOSITIONS.get(top, "reserved_noncanonical")
            ] += 1
        else:
            native_session_dispositions["canonical_root_without_result"] += 1

    canonical_count = path_dispositions["canonical"]
    reward_file_count = sum(bool(row["has_verifier_reward"]) for row in canonical_rows)
    ctrf_summary_count = max(ctrf_summary_field_presence.values(), default=0)
    audit = {
        "results_root": str(results_root),
        "analysis_scope": {
            "allowed_configs": (
                sorted(allowed_config_set) if allowed_config_set is not None else None
            ),
            "excluded_canonical_results": sum(excluded_config_counts.values()),
            "excluded_config_counts": dict(sorted(excluded_config_counts.items())),
        },
        "candidate_result_files": len(candidates),
        "path_dispositions": dict(sorted(path_dispositions.items())),
        "canonical_results_loaded": len(canonical_rows),
        "malformed_canonical_results": malformed_results,
        "candidate_native_session_files": len(native_session_candidates),
        "native_session_dispositions": dict(
            sorted(native_session_dispositions.items())
        ),
        "result_field_schema": {
            name: {
                "present": count,
                "missing": canonical_count - count,
                "types": dict(sorted(result_field_types[name].items())),
            }
            for name, count in sorted(result_field_presence.items())
        },
        "verifier_reward_schema": {
            name: {
                "present": count,
                "missing_from_reward_files": reward_file_count - count,
                "types": dict(sorted(verifier_reward_field_types[name].items())),
            }
            for name, count in sorted(verifier_reward_field_presence.items())
        },
        "verifier_ctrf_schema": {
            "path_variants": dict(sorted(ctrf_path_variants.items())),
            "top_level_field_presence": dict(sorted(ctrf_top_level_fields.items())),
            "summary_fields": {
                name: {
                    "present": count,
                    "missing_from_summaries": ctrf_summary_count - count,
                    "types": dict(sorted(ctrf_summary_field_types[name].items())),
                }
                for name, count in sorted(ctrf_summary_field_presence.items())
            },
        },
        "model_patch_schema": dict(sorted(patch_schema.items())),
        "artifact_availability": {
            name: {
                "present": sum(bool(row[name]) for row in canonical_rows),
                "missing": len(canonical_rows)
                - sum(bool(row[name]) for row in canonical_rows),
            }
            for name in _ARTIFACT_FIELDS
        },
        "session_count_distribution": dict(
            sorted(Counter(row["session_count"] for row in canonical_rows).items())
        ),
        "primary_disposition_counts": dict(
            sorted(
                Counter(row["primary_disposition"] for row in canonical_rows).items()
            )
        ),
        "reward_binary_distribution": dict(
            sorted(Counter(str(row["reward_binary"]) for row in canonical_rows).items())
        ),
    }
    return canonical_rows, audit


def select_analysis_tasks(
    inventory_rows: Sequence[dict[str, Any]], task_limit: int | None
) -> list[str]:
    """Select all eligible tasks, or a stable outcome-independent bounded subset."""
    eligible_tasks = {
        str(row["task"])
        for row in inventory_rows
        if row["primary_disposition"] == "eligible"
    }
    ordered_tasks = sorted(eligible_tasks, key=lambda task: (_stable_hash(task), task))
    if task_limit is None:
        return ordered_tasks
    if task_limit < 1 or task_limit > len(ordered_tasks):
        raise ValueError(
            f"task_limit must be between 1 and {len(ordered_tasks)}, got {task_limit}"
        )
    return ordered_tasks[:task_limit]


def extract_analysis_rows(
    inventory_rows: list[dict[str, Any]],
    analysis_tasks: Sequence[str],
    *,
    max_session_bytes: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse all initially eligible reps for selected tasks under an explicit byte cap."""
    selected_tasks = set(analysis_tasks)
    selected_inventory = [
        row
        for row in inventory_rows
        if row["primary_disposition"] == "eligible" and row["task"] in selected_tasks
    ]
    estimated_bytes = sum(int(row["session_bytes"]) for row in selected_inventory)
    if estimated_bytes > max_session_bytes:
        raise RuntimeError(
            "pilot session bytes exceed cap: "
            f"{estimated_bytes} > {max_session_bytes}; reduce --pilot-tasks or raise cap explicitly"
        )

    rows: list[dict[str, Any]] = []
    schema = {
        "record_types": Counter(),
        "roles": Counter(),
        "block_types": Counter(),
        "tool_names": Counter(),
        "stop_reasons": Counter(),
        "malformed_records": 0,
        "unresolved_tool_calls": 0,
        "orphan_tool_results": 0,
        "terminal_output_truncations": 0,
        "result_turn_mismatches": 0,
        "result_tool_call_mismatches": 0,
    }
    post_parse_dispositions: Counter[str] = Counter()

    for inventory in selected_inventory:
        parsed = parse_native_session(Path(inventory["session_path"]))
        _merge_session_schema(schema, parsed)
        if terminal_session_is_truncated(parsed):
            disposition = "terminal_output_truncation"
        elif parsed.malformed_records:
            disposition = "malformed_session_records"
        else:
            disposition = "eligible"
        post_parse_dispositions[disposition] += 1
        if disposition != "eligible":
            continue

        schema["result_turn_mismatches"] += int(
            inventory["turns"] != parsed.assistant_turns
        )
        schema["result_tool_call_mismatches"] += int(
            inventory["tool_calls"] != parsed.tool_calls
        )
        process_features = extract_session_process_features(parsed)
        row = {
            "cell_id": inventory["cell_id"],
            "task": inventory["task"],
            "model": inventory["model"],
            "thinking_level": inventory["thinking_level"],
            "config": inventory["config"],
            "rep": inventory["rep"],
            "language": inventory["language"],
            "category": inventory["category"],
            "reward_binary": int(inventory["reward_binary"]),
            "reward_partial": float(inventory["reward_partial"]),
            "total_tokens": int(inventory["total_tokens"]),
            "turns": int(inventory["turns"]),
            "tool_calls": int(inventory["tool_calls"] or 0),
            "agent_wall_s": float(inventory["agent_wall_s"]),
            "log_total_tokens": math.log1p(max(0, int(inventory["total_tokens"]))),
            "log_turns": math.log1p(max(0, int(inventory["turns"]))),
            "log_agent_wall_s": math.log1p(max(0.0, float(inventory["agent_wall_s"]))),
            "session_bytes": int(inventory["session_bytes"]),
            "session_malformed_records": parsed.malformed_records,
            "session_unresolved_tool_calls": parsed.unresolved_tool_calls,
            "session_orphan_tool_results": parsed.orphan_tool_results,
            "terminal_stop_reason": parsed.terminal_stop_reason or "",
            **process_features,
        }
        rows.append(row)

    _add_within_task_length_outliers(rows)
    schema_audit: dict[str, Any] = {
        key: dict(sorted(value.items())) if isinstance(value, Counter) else value
        for key, value in schema.items()
    }
    schema_audit.update(
        {
            "selected_pre_parse_reps": len(selected_inventory),
            "selected_session_bytes": estimated_bytes,
            "post_parse_disposition_counts": dict(
                sorted(post_parse_dispositions.items())
            ),
            "modeling_reps": len(rows),
            "semantic_feature_support": {
                "fully_observable_reps": sum(
                    row["semantic_event_coverage"] == 1.0 for row in rows
                ),
                "partially_observable_reps": sum(
                    0.0 < row["semantic_event_coverage"] < 1.0 for row in rows
                ),
                "opaque_only_reps": sum(
                    row["semantic_event_coverage"] == 0.0 for row in rows
                ),
                "reps_with_observable_tests": sum(
                    row["observable_test_runs"] > 0 for row in rows
                ),
                "reps_with_direct_mutations": sum(
                    row["direct_mutation_calls"] > 0 for row in rows
                ),
                "reps_with_source_mutations": sum(
                    row["has_successful_source_mutation"] > 0 for row in rows
                ),
                "reps_with_uncertain_first_source_mutation": sum(
                    row["first_source_mutation_boundary_uncertain"] > 0 for row in rows
                ),
                "reps_with_write_as_first_source_mutation": sum(
                    row["first_source_mutation_is_write"] > 0 for row in rows
                ),
                "patch_state_history": "unsupported",
                "nested_tool_operations": "unsupported",
                "test_outcome_oracle": "top-level test-command tool result isError only",
            },
        }
    )
    return rows, schema_audit


def evaluate_held_out_tasks(
    rows: Sequence[dict[str, Any]], fold_count: int
) -> dict[str, Any]:
    """Compare grouped trajectory feature specifications on held-out tasks."""
    folds = build_task_folds(rows, fold_count)
    prediction_names = ("prevalence", *PREDICTOR_SPECIFICATIONS)
    binary_predictions = {name: np.full(len(rows), np.nan) for name in prediction_names}
    partial_predictions = {
        name: np.full(len(rows), np.nan) for name in prediction_names
    }
    fold_reports: list[dict[str, Any]] = []

    for fold_index, fold in enumerate(folds):
        test_tasks = set(fold["test_tasks"])
        train_indices = [
            idx for idx, row in enumerate(rows) if row["task"] not in test_tasks
        ]
        test_indices = [
            idx for idx, row in enumerate(rows) if row["task"] in test_tasks
        ]
        train_rows = [rows[idx] for idx in train_indices]
        test_rows = [rows[idx] for idx in test_indices]
        y_train = np.array([row["reward_binary"] for row in train_rows], dtype=float)
        y_partial_train = np.array(
            [row["reward_partial"] for row in train_rows], dtype=float
        )
        if len(set(y_train)) < 2:
            raise RuntimeError(f"fold {fold_index} training outcomes have one class")

        binary_predictions["prevalence"][test_indices] = np.clip(
            y_train.mean(), 1e-6, 1 - 1e-6
        )
        partial_predictions["prevalence"][test_indices] = np.clip(
            y_partial_train.mean(), 0.0, 1.0
        )
        for model_name, numeric_names in PREDICTOR_SPECIFICATIONS.items():
            train_matrix, test_matrix = _encode_design(
                train_rows,
                test_rows,
                numeric_names=numeric_names,
                categorical_names=CATEGORICAL_CONTROL_NAMES,
            )
            coefficients = _fit_logistic(train_matrix, y_train)
            binary_predictions[model_name][test_indices] = _sigmoid(
                test_matrix @ coefficients
            )
            ridge_coefficients = _fit_ridge(train_matrix, y_partial_train)
            partial_predictions[model_name][test_indices] = np.clip(
                test_matrix @ ridge_coefficients, 0.0, 1.0
            )
        fold_reports.append(
            {
                "fold": fold_index,
                "train_tasks": fold["train_tasks"],
                "test_tasks": fold["test_tasks"],
                "train_reps": len(train_indices),
                "test_reps": len(test_indices),
                "test_successes": int(
                    sum(rows[idx]["reward_binary"] for idx in test_indices)
                ),
            }
        )

    y = np.array([row["reward_binary"] for row in rows], dtype=float)
    y_partial = np.array([row["reward_partial"] for row in rows], dtype=float)
    tasks = [str(row["task"]) for row in rows]
    binary_metrics = {
        name: _binary_metrics(y, predictions, tasks)
        for name, predictions in binary_predictions.items()
    }
    partial_metrics = {
        name: _partial_metrics(y_partial, predictions, tasks)
        for name, predictions in partial_predictions.items()
    }
    specification_deltas: dict[str, Any] = {}
    partial_specification_deltas: dict[str, Any] = {}
    for name in PREDICTOR_SPECIFICATIONS:
        if name == "length":
            continue
        specification_deltas[name] = {
            "log_loss": binary_metrics[name]["log_loss"]
            - binary_metrics["length"]["log_loss"],
            "brier": binary_metrics[name]["brier"] - binary_metrics["length"]["brier"],
            "auroc": binary_metrics[name]["auroc"] - binary_metrics["length"]["auroc"],
            "average_precision": binary_metrics[name]["average_precision"]
            - binary_metrics["length"]["average_precision"],
            "task_bootstrap_log_loss_delta_95pct": _bootstrap_task_log_loss_delta(
                y,
                binary_predictions["length"],
                binary_predictions[name],
                tasks,
            ),
        }
        partial_specification_deltas[name] = {
            "rmse": partial_metrics[name]["rmse"] - partial_metrics["length"]["rmse"],
            "mae": partial_metrics[name]["mae"] - partial_metrics["length"]["mae"],
        }
    return {
        "design": {
            "outcome": "reward_binary (1=success, 0=failure)",
            "partial_outcome": "reward_partial",
            "task_control": (
                "task-disjoint evaluation groups plus within-task unsupervised length "
                "normalization; task identity is intentionally not one-hot encoded because "
                "held-out tasks have no estimable fixed effect"
            ),
            "categorical_controls": list(CATEGORICAL_CONTROL_NAMES),
            "predictor_specifications": {
                name: list(features)
                for name, features in PREDICTOR_SPECIFICATIONS.items()
            },
            "censoring_controls": (
                "timeouts, truncations, nonzero agent exits, verifier errors, invalid rewards, "
                "and ambiguous sessions are excluded before modeling rather than used as predictors"
            ),
            "regularization": "fixed L2 penalty=1.0; no test-fold tuning",
            "fold_count": fold_count,
        },
        "folds": fold_reports,
        "binary_metrics": binary_metrics,
        "partial_metrics": partial_metrics,
        "specification_minus_length": specification_deltas,
        "partial_specification_minus_length": partial_specification_deltas,
        "process_minus_length": specification_deltas["process"],
        "partial_process_minus_length": partial_specification_deltas["process"],
    }


def evaluate_model_sensitivities(
    rows: Sequence[dict[str, Any]],
    fold_count: int,
    *,
    min_reps: int = 100,
    min_tasks: int = 12,
) -> dict[str, Any]:
    """Repeat held-out-task evaluation for models with adequate support."""
    results: dict[str, Any] = {}
    for model in sorted({str(row["model"]) for row in rows}):
        model_rows = [row for row in rows if row["model"] == model]
        task_count = len({row["task"] for row in model_rows})
        support = {
            "reps": len(model_rows),
            "tasks": task_count,
            "successes": sum(row["reward_binary"] for row in model_rows),
        }
        if len(model_rows) < min_reps or task_count < min_tasks:
            results[model] = {
                "status": "insufficient_support",
                "minimum_reps": min_reps,
                "minimum_tasks": min_tasks,
                **support,
            }
            continue
        results[model] = {
            "status": "evaluated",
            **support,
            "evaluation": evaluate_held_out_tasks(model_rows, fold_count),
        }
    return results


def summarize_analysis_features(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Summarize feature availability and distributions without fitting a model."""
    outcome_groups = {
        "failure": [row for row in rows if row["reward_binary"] == 0],
        "success": [row for row in rows if row["reward_binary"] == 1],
    }
    numeric_names = (
        "total_tokens",
        "turns",
        "agent_wall_s",
        *PROCESS_FEATURE_NAMES,
        *SEQUENCE_FEATURE_NAMES,
    )
    by_outcome = {
        outcome: {name: _numeric_distribution(group, name) for name in numeric_names}
        for outcome, group in outcome_groups.items()
    }
    task_rows = []
    for task in sorted({str(row["task"]) for row in rows}):
        group = [row for row in rows if row["task"] == task]
        task_rows.append(
            {
                "task": task,
                "reps": len(group),
                "successes": sum(row["reward_binary"] for row in group),
                "success_rate": sum(row["reward_binary"] for row in group) / len(group),
            }
        )
    config_support = []
    for config in sorted({str(row["config"]) for row in rows}):
        group = [row for row in rows if row["config"] == config]
        config_support.append(
            {
                "config": config,
                "reps": len(group),
                "tasks": len({row["task"] for row in group}),
                "models": sorted({str(row["model"]) for row in group}),
                "successes": sum(row["reward_binary"] for row in group),
                "mean_semantic_event_coverage": float(
                    np.mean([row["semantic_event_coverage"] for row in group])
                ),
                "reps_with_observable_tests": sum(
                    row["observable_test_runs"] > 0 for row in group
                ),
            }
        )
    model_support = []
    for model in sorted({str(row["model"]) for row in rows}):
        group = [row for row in rows if row["model"] == model]
        successes = sum(row["reward_binary"] for row in group)
        model_support.append(
            {
                "model": model,
                "reps": len(group),
                "tasks": len({row["task"] for row in group}),
                "successes": successes,
                "failures": len(group) - successes,
                "configs": sorted({str(row["config"]) for row in group}),
                "thinking_levels": sorted(
                    {str(row["thinking_level"]) for row in group}
                ),
            }
        )
    return {
        "reps": len(rows),
        "tasks": len({row["task"] for row in rows}),
        "models": len({row["model"] for row in rows}),
        "thinking_levels": len({row["thinking_level"] for row in rows}),
        "configs": len({row["config"] for row in rows}),
        "successes": len(outcome_groups["success"]),
        "failures": len(outcome_groups["failure"]),
        "partial_reward": _numeric_distribution(rows, "reward_partial"),
        "by_outcome": by_outcome,
        "by_task": task_rows,
        "config_semantic_support": config_support,
        "model_support": model_support,
        "measured_signal_boundaries": {
            "true_patch_state_churn": "unsupported; no intermediate patch snapshots",
            "direct_exact_edit_reversion": "supported only for successful edit calls exposing path/oldText/newText",
            "bash_or_nested_mutations": "not observable as edits",
            "nested_tool_read_search_test_semantics": "unsupported and counted as opaque",
            "test_transitions": "supported only for normalized top-level bash test commands with tool-result isError",
            "first_source_mutation": "first successful edit/write to a supported source-file extension; possible earlier shell mutations are flagged",
            "edit_vs_write": "supported for structured top-level edit/write calls; target purpose is conservatively path-classified",
            "phase_flow": "deterministic exploration/diagnosis/implementation/validation labels over supported events",
            "verifier_or_final_test_artifacts": "excluded from every predictor",
        },
    }


def summarize_task_controlled_feature_effects(
    rows: Sequence[dict[str, Any]], feature_names: Sequence[str]
) -> dict[str, Any]:
    """Summarize success/failure feature differences within contested tasks."""
    result: dict[str, Any] = {}
    tasks = sorted({str(row["task"]) for row in rows})
    for feature_name in feature_names:
        raw_deltas: list[float] = []
        standardized_deltas: list[float] = []
        for task in tasks:
            task_rows = [row for row in rows if row["task"] == task]
            success_values = [
                float(row[feature_name])
                for row in task_rows
                if row["reward_binary"] == 1
            ]
            failure_values = [
                float(row[feature_name])
                for row in task_rows
                if row["reward_binary"] == 0
            ]
            if not success_values or not failure_values:
                continue
            delta = float(np.mean(success_values) - np.mean(failure_values))
            raw_deltas.append(delta)
            task_standard_deviation = float(
                np.std(success_values + failure_values, ddof=0)
            )
            if task_standard_deviation > 0:
                standardized_deltas.append(delta / task_standard_deviation)
        if standardized_deltas:
            rng = np.random.default_rng(int(_stable_hash(feature_name), 16))
            values = np.array(standardized_deltas, dtype=float)
            bootstrap_means = np.mean(
                rng.choice(values, size=(2000, len(values)), replace=True), axis=1
            )
            interval = {
                "low": float(np.quantile(bootstrap_means, 0.025)),
                "high": float(np.quantile(bootstrap_means, 0.975)),
                "samples": 2000,
            }
        else:
            interval = {"low": None, "high": None, "samples": 0}
        result[feature_name] = {
            "contested_tasks": len(raw_deltas),
            "tasks_with_nonconstant_feature": len(standardized_deltas),
            "mean_success_minus_failure": float(np.mean(raw_deltas))
            if raw_deltas
            else None,
            "median_success_minus_failure": float(np.median(raw_deltas))
            if raw_deltas
            else None,
            "fraction_tasks_higher_in_success": (
                sum(delta > 0 for delta in raw_deltas) / len(raw_deltas)
                if raw_deltas
                else 0.0
            ),
            "mean_within_task_standardized_delta": float(np.mean(standardized_deltas))
            if standardized_deltas
            else None,
            "task_bootstrap_standardized_mean_95pct": interval,
        }
    return result


def run_baseline_analysis(
    results_root: Path,
    output_dir: Path,
    *,
    task_limit: int | None,
    fold_count: int,
    max_session_bytes: int,
) -> dict[str, Any]:
    """Build and evaluate the bounded stock-Pi baseline trajectory dataset."""
    inventory_rows, schema_audit = discover_result_inventory(
        results_root, allowed_configs=STOCK_PI_BASELINE_CONFIGS
    )
    analysis_tasks = select_analysis_tasks(inventory_rows, task_limit)
    analysis_rows, session_schema = extract_analysis_rows(
        inventory_rows, analysis_tasks, max_session_bytes=max_session_bytes
    )
    evaluation = evaluate_held_out_tasks(analysis_rows, fold_count)
    evaluation["model_sensitivities"] = evaluate_model_sensitivities(
        analysis_rows, fold_count
    )
    certain_boundary_rows = [
        row
        for row in analysis_rows
        if row["has_successful_source_mutation"] == 1
        and row["first_source_mutation_boundary_uncertain"] == 0
    ]
    evaluation["cohort_sensitivities"] = {
        "certain_first_source_mutation": {
            "reps": len(certain_boundary_rows),
            "excluded_reps": len(analysis_rows) - len(certain_boundary_rows),
            "evaluation": evaluate_held_out_tasks(certain_boundary_rows, fold_count),
        }
    }
    feature_summary = summarize_analysis_features(analysis_rows)
    task_controlled_effects = summarize_task_controlled_feature_effects(
        analysis_rows, PROCESS_FEATURE_NAMES + SEQUENCE_FEATURE_NAMES
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "baseline_cohort.csv", inventory_rows)
    _write_csv(output_dir / "baseline_features.csv", analysis_rows)
    (output_dir / "schema_audit.json").write_text(
        json.dumps(schema_audit, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "session_schema_audit.json").write_text(
        json.dumps(session_schema, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "held_out_task_evaluation.json").write_text(
        json.dumps(evaluation, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "feature_summary.json").write_text(
        json.dumps(feature_summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "task_controlled_feature_effects.json").write_text(
        json.dumps(task_controlled_effects, indent=2, sort_keys=True) + "\n"
    )
    selection_method = (
        "all eligible tasks in the stock-Pi baseline configs"
        if task_limit is None
        else "first task ids by blake2b-64(task), independent of outcomes"
    )
    manifest = {
        "analysis": "stock-pi-baseline-trajectory-process-signals",
        "git": _git_metadata(Path(__file__).resolve().parents[2]),
        "results_root": str(results_root.resolve()),
        "output_dir": str(output_dir.resolve()),
        "dataset": {
            "allowed_configs": list(STOCK_PI_BASELINE_CONFIGS),
            "method": selection_method,
            "task_limit": task_limit,
            "task_count": len(analysis_tasks),
            "tasks": analysis_tasks,
            "pre_parse_reps": session_schema["selected_pre_parse_reps"],
            "modeling_reps": session_schema["modeling_reps"],
            "session_bytes": session_schema["selected_session_bytes"],
            "max_session_bytes": max_session_bytes,
        },
        "outputs": [
            "baseline_cohort.csv",
            "baseline_features.csv",
            "schema_audit.json",
            "session_schema_audit.json",
            "held_out_task_evaluation.json",
            "feature_summary.json",
            "task_controlled_feature_effects.json",
            "baseline_manifest.json",
        ],
    }
    (output_dir / "baseline_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return {"manifest": manifest, "evaluation": evaluation}


def _result_identity_mismatches(
    result: dict[str, Any], result_path: Path, results_root: Path
) -> list[str]:
    model_leaf, thinking, config, task, rep_dir, _ = result_path.relative_to(
        results_root
    ).parts
    checks = {
        "model_leaf": str(result.get("model", "")).rsplit("/", 1)[-1] == model_leaf,
        "thinking_level": result.get("thinking_level") == thinking,
        "config": result.get("config") == config,
        "task": result.get("task") == task,
        "rep": result.get("rep") == int(rep_dir[3:]),
    }
    return [name for name, matches in checks.items() if not matches]


def _first_verifier_ctrf(cell_path: Path) -> Path | None:
    for path in (
        cell_path / "verifier" / "ctrf.json",
        cell_path / "verifier" / "reports" / "new-ctrf.json",
        cell_path / "verifier" / "reports" / "new_ctrf.json",
    ):
        if path.is_file():
            return path
    return None


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _merge_session_schema(schema: dict[str, Any], parsed: NativeSessionParse) -> None:
    for name in ("record_types", "roles", "block_types", "tool_names", "stop_reasons"):
        schema[name].update(getattr(parsed, name))
    schema["malformed_records"] += parsed.malformed_records
    schema["unresolved_tool_calls"] += parsed.unresolved_tool_calls
    schema["orphan_tool_results"] += parsed.orphan_tool_results
    schema["terminal_output_truncations"] += int(terminal_session_is_truncated(parsed))


def _add_within_task_length_outliers(rows: list[dict[str, Any]]) -> None:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row["task"])].append(row)
    for task_rows in by_task.values():
        for source, target in (
            ("log_total_tokens", "within_task_token_robust_z"),
            ("log_turns", "within_task_turn_robust_z"),
        ):
            values = np.array([float(row[source]) for row in task_rows])
            median = float(np.median(values))
            mad = float(np.median(np.abs(values - median)))
            scale = 1.4826 * mad
            for row in task_rows:
                row[target] = (float(row[source]) - median) / scale if scale else 0.0


def _encode_design(
    train_rows: Sequence[dict[str, Any]],
    test_rows: Sequence[dict[str, Any]],
    *,
    numeric_names: Sequence[str],
    categorical_names: Sequence[str],
) -> tuple[np.ndarray, np.ndarray]:
    train_numeric = np.array(
        [[float(row[name]) for name in numeric_names] for row in train_rows],
        dtype=float,
    )
    test_numeric = np.array(
        [[float(row[name]) for name in numeric_names] for row in test_rows], dtype=float
    )
    means = train_numeric.mean(axis=0)
    scales = train_numeric.std(axis=0)
    scales[scales < 1e-12] = 1.0
    train_parts = [np.ones((len(train_rows), 1)), (train_numeric - means) / scales]
    test_parts = [np.ones((len(test_rows), 1)), (test_numeric - means) / scales]
    for name in categorical_names:
        categories = sorted({str(row[name]) for row in train_rows})
        encoded_categories = categories[1:]
        train_parts.append(
            np.array(
                [
                    [
                        float(str(row[name]) == category)
                        for category in encoded_categories
                    ]
                    for row in train_rows
                ]
            )
        )
        test_parts.append(
            np.array(
                [
                    [
                        float(str(row[name]) == category)
                        for category in encoded_categories
                    ]
                    for row in test_rows
                ]
            )
        )
    return np.hstack(train_parts), np.hstack(test_parts)


def _fit_logistic(matrix: np.ndarray, outcomes: np.ndarray) -> np.ndarray:
    def objective(coefficients: np.ndarray) -> tuple[float, np.ndarray]:
        logits = matrix @ coefficients
        loss = np.mean(np.logaddexp(0.0, logits) - outcomes * logits)
        penalty = 0.5 * np.dot(coefficients[1:], coefficients[1:]) / len(outcomes)
        probabilities = _sigmoid(logits)
        gradient = matrix.T @ (probabilities - outcomes) / len(outcomes)
        gradient[1:] += coefficients[1:] / len(outcomes)
        return float(loss + penalty), gradient

    result = minimize(
        objective,
        np.zeros(matrix.shape[1]),
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 1000, "ftol": 1e-10},
    )
    if not result.success:
        raise RuntimeError(f"logistic fit failed: {result.message}")
    return np.asarray(result.x)


def _fit_ridge(matrix: np.ndarray, outcomes: np.ndarray) -> np.ndarray:
    penalty = np.eye(matrix.shape[1])
    penalty[0, 0] = 0.0
    return np.linalg.solve(matrix.T @ matrix + penalty, matrix.T @ outcomes)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    positive = values >= 0
    output = np.empty_like(values, dtype=float)
    output[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exponential = np.exp(values[~positive])
    output[~positive] = exponential / (1.0 + exponential)
    return output


def _binary_metrics(
    outcomes: np.ndarray, predictions: np.ndarray, tasks: Sequence[str]
) -> dict[str, float]:
    clipped = np.clip(predictions, 1e-6, 1 - 1e-6)
    losses = -(outcomes * np.log(clipped) + (1 - outcomes) * np.log(1 - clipped))
    by_task = defaultdict(list)
    for task, loss in zip(tasks, losses, strict=True):
        by_task[task].append(float(loss))
    return {
        "log_loss": float(losses.mean()),
        "macro_task_log_loss": float(
            np.mean([np.mean(values) for values in by_task.values()])
        ),
        "brier": float(np.mean((predictions - outcomes) ** 2)),
        "auroc": _auroc(outcomes, predictions),
        "average_precision": _average_precision(outcomes, predictions),
    }


def _partial_metrics(
    outcomes: np.ndarray, predictions: np.ndarray, tasks: Sequence[str]
) -> dict[str, float]:
    errors = predictions - outcomes
    by_task = defaultdict(list)
    for task, error in zip(tasks, errors, strict=True):
        by_task[task].append(float(error * error))
    return {
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "macro_task_rmse": float(
            np.mean([math.sqrt(np.mean(values)) for values in by_task.values()])
        ),
    }


def _auroc(outcomes: np.ndarray, predictions: np.ndarray) -> float:
    positives = outcomes == 1
    positive_count = int(positives.sum())
    negative_count = len(outcomes) - positive_count
    if not positive_count or not negative_count:
        return float("nan")
    ranks = rankdata(predictions, method="average")
    return float(
        (ranks[positives].sum() - positive_count * (positive_count + 1) / 2)
        / (positive_count * negative_count)
    )


def _average_precision(outcomes: np.ndarray, predictions: np.ndarray) -> float:
    order = np.argsort(-predictions, kind="stable")
    sorted_predictions = predictions[order]
    sorted_outcomes = outcomes[order]
    positive_count = sorted_outcomes.sum()
    if positive_count == 0:
        return float("nan")
    threshold_ends = np.r_[
        np.flatnonzero(np.diff(sorted_predictions)), len(sorted_predictions) - 1
    ]
    true_positives = np.cumsum(sorted_outcomes)[threshold_ends]
    predicted_positives = threshold_ends + 1
    precision = true_positives / predicted_positives
    recall = true_positives / positive_count
    recall_increments = np.diff(np.r_[0.0, recall])
    return float(np.sum(recall_increments * precision))


def _bootstrap_task_log_loss_delta(
    outcomes: np.ndarray,
    length_predictions: np.ndarray,
    process_predictions: np.ndarray,
    tasks: Sequence[str],
    *,
    samples: int = 2000,
) -> dict[str, float]:
    task_names = sorted(set(tasks))
    indices = {
        task: np.array([idx for idx, value in enumerate(tasks) if value == task])
        for task in task_names
    }
    rng = np.random.default_rng(20260814)
    deltas = []
    for _ in range(samples):
        selected = rng.choice(task_names, size=len(task_names), replace=True)
        sampled_indices = np.concatenate([indices[str(task)] for task in selected])
        y = outcomes[sampled_indices]
        length = np.clip(length_predictions[sampled_indices], 1e-6, 1 - 1e-6)
        process = np.clip(process_predictions[sampled_indices], 1e-6, 1 - 1e-6)
        length_loss = -np.mean(y * np.log(length) + (1 - y) * np.log(1 - length))
        process_loss = -np.mean(y * np.log(process) + (1 - y) * np.log(1 - process))
        deltas.append(float(process_loss - length_loss))
    low, high = np.quantile(deltas, [0.025, 0.975])
    return {"low": float(low), "high": float(high), "samples": samples}


def _numeric_distribution(
    rows: Sequence[dict[str, Any]], name: str
) -> dict[str, float | int]:
    values = np.array([float(row[name]) for row in rows], dtype=float)
    return {
        "n": len(values),
        "nonzero": int(np.count_nonzero(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "p90": float(np.quantile(values, 0.9)),
    }


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for name in row:
            if name not in fieldnames:
                fieldnames.append(name)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _git_metadata(repo_root: Path) -> dict[str, str]:
    def git(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            check=True,
            text=True,
            capture_output=True,
        )
        return completed.stdout.strip()

    return {
        "worktree": str(repo_root),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "base_ref": "origin/master",
        "base_revision": git("rev-parse", "origin/master"),
        "base_fallback_reason": "origin/main and local main were absent",
    }


def _stable_hash(value: str) -> str:
    return hashlib.blake2b(value.encode(), digest_size=8).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and evaluate the stock-Pi baseline trajectory dataset."
    )
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/trajectory_process_signals/artifacts"),
    )
    parser.add_argument(
        "--task-limit",
        type=int,
        help="Optional stable task subset; omit to analyze every eligible baseline task.",
    )
    parser.add_argument("--folds", type=int, default=4)
    parser.add_argument("--max-session-bytes", type=int, default=536_870_912)
    args = parser.parse_args()
    result = run_baseline_analysis(
        args.results,
        args.output,
        task_limit=args.task_limit,
        fold_count=args.folds,
        max_session_bytes=args.max_session_bytes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
