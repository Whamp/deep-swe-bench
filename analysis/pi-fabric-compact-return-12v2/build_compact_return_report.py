#!/usr/bin/env python3
"""Build the paired Pi Fabric compact-return 12v2 analysis report."""

from __future__ import annotations

import argparse
import html
import json
import math
import random
import re
import statistics
from collections import defaultdict
from itertools import product
from pathlib import Path
from typing import Any

CONTROL_CONFIG = "pi-fabric-output-telemetry@1.0.0"
COMPACT_CONFIG = "pi-fabric-compact-return@1.0.0"
TELEMETRY_KIND = "pi-fabric.output-telemetry.v1"
COMPACT_MARKER = "pi_fabric.compact_return.v1"
EXPECTED_CELLS_PER_CONFIG = 36
TELEMETRY_FIELDS = (
    "nestedOperationCount",
    "nestedMeasuredResultCount",
    "nestedRawResultChars",
    "nestedRawResultBytes",
    "nestedSandboxResultChars",
    "nestedSandboxResultBytes",
    "nestedTruncatedResults",
    "formattedValueChars",
    "formattedValueBytes",
    "logChars",
    "logBytes",
    "rawOutputChars",
    "rawOutputBytes",
    "returnedTextChars",
    "returnedTextBytes",
)
MUTATION_REFS = {"pi.edit", "pi.write"}
READ_REF = "pi.read"
VERIFY_COMMAND = re.compile(
    r"(?:^|[;&|]\s*|\b)(?:pytest|python\s+-m\s+pytest|npm\s+(?:test|run\s+(?:test|lint|typecheck))|"
    r"pnpm\s+(?:test|lint|typecheck)|yarn\s+(?:test|lint|typecheck)|cargo\s+(?:test|check|clippy)|"
    r"go\s+test|ruff\s+(?:check|format)|mypy|pyright|ty\s+check|tsc(?:\s|$)|make\s+(?:test|check))"
)


def load_json(path: Path) -> dict[str, Any]:
    """Read one JSON object from a benchmark artifact."""
    return json.loads(path.read_text())


def text_chars(message: dict[str, Any]) -> int:
    """Count visible text characters in a native Pi message."""
    return sum(
        len(str(item.get("text", "")))
        for item in message.get("content") or []
        if isinstance(item, dict) and item.get("type") == "text"
    )


def read_ranges_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Return whether two line-bounded reads overlap; unbounded reads always overlap."""
    if left["limit"] is None or right["limit"] is None:
        return True
    left_end = left["offset"] + left["limit"] - 1
    right_end = right["offset"] + right["limit"] - 1
    return left["offset"] <= right_end and right["offset"] <= left_end


def parse_read_operation(
    operation: dict[str, Any], call_index: int
) -> dict[str, Any] | None:
    """Normalize one nested pi.read operation for reread analysis."""
    if operation.get("ref") != READ_REF:
        return None
    arguments = operation.get("args") or {}
    path = arguments.get("path")
    if not isinstance(path, str) or not path:
        return None
    offset = arguments.get("offset", 1)
    limit = arguments.get("limit")
    return {
        "path": path,
        "offset": int(offset) if isinstance(offset, int | float) else 1,
        "limit": int(limit) if isinstance(limit, int | float) else None,
        "call_index": call_index,
    }


def telemetry_invariant_errors(telemetry: dict[str, Any]) -> list[str]:
    """Return compact-return telemetry contract violations for one Fabric result."""
    errors: list[str] = []
    for field in TELEMETRY_FIELDS:
        value = telemetry.get(field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{field} must be a non-negative integer")
    if errors:
        return errors
    if telemetry["nestedMeasuredResultCount"] > telemetry["nestedOperationCount"]:
        errors.append("nested measured results exceed operations")
    if telemetry["nestedTruncatedResults"] > telemetry["nestedMeasuredResultCount"]:
        errors.append("nested truncated results exceed measured results")
    for stem in (
        "nestedRawResult",
        "nestedSandboxResult",
        "formattedValue",
        "log",
        "rawOutput",
        "returnedText",
    ):
        if telemetry[f"{stem}Bytes"] < telemetry[f"{stem}Chars"]:
            errors.append(f"{stem} bytes are smaller than characters")
    if telemetry["returnedTextChars"] > max(telemetry["rawOutputChars"], 11):
        errors.append("returned text exceeds raw output or empty-output fallback")
    return errors


def summarize_session(session_path: Path) -> dict[str, float | int]:
    """Summarize Fabric telemetry and nested trajectory behavior for one session."""
    calls: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        session_path.read_text(errors="replace").splitlines(), 1
    ):
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "message":
            continue
        message = record.get("message") or {}
        if (
            message.get("role") != "toolResult"
            or message.get("toolName") != "fabric_exec"
        ):
            continue
        details = message.get("details") or {}
        telemetry = details.get("telemetry")
        if not isinstance(telemetry, dict) or telemetry.get("kind") != TELEMETRY_KIND:
            raise ValueError(
                f"Missing {TELEMETRY_KIND} at {session_path}:{line_number}"
            )
        errors = telemetry_invariant_errors(telemetry)
        if errors:
            raise ValueError(
                f"Invalid telemetry at {session_path}:{line_number}: {errors}"
            )
        operations = [
            operation
            for operation in ((details.get("trace") or {}).get("operations") or [])
            if isinstance(operation, dict)
        ]
        trace_operation_count = len(operations)
        visible_text_chars = text_chars(message)
        calls.append(
            {
                "telemetry": telemetry,
                "operations": operations,
                "traceOperationCount": trace_operation_count,
                "traceAuditCountDiffers": int(
                    trace_operation_count != telemetry["nestedOperationCount"]
                ),
                "visibleTextChars": visible_text_chars,
                "visibleTextDiffers": int(
                    visible_text_chars != telemetry["returnedTextChars"]
                ),
                "fabricErrorResult": int(bool(message.get("isError"))),
            }
        )
    if not calls:
        raise ValueError(f"No Fabric telemetry records in {session_path}")

    prior_reads: dict[str, list[dict[str, Any]]] = defaultdict(list)
    repeated_reads = overlapping_reads = exact_rereads = 0
    read_operations = whole_file_reads = 0
    mutation_calls = mutation_operations = verification_operations = 0
    first_mutation_call: int | None = None
    for call_index, call in enumerate(calls):
        refs = {str(operation.get("ref", "")) for operation in call["operations"]}
        call_mutations = sum(
            operation.get("ref") in MUTATION_REFS for operation in call["operations"]
        )
        if call_mutations:
            mutation_calls += 1
            mutation_operations += call_mutations
            if first_mutation_call is None:
                first_mutation_call = call_index
        for operation in call["operations"]:
            if operation.get("ref") == "pi.bash" and VERIFY_COMMAND.search(
                str((operation.get("args") or {}).get("command", ""))
            ):
                verification_operations += 1
            read = parse_read_operation(operation, call_index)
            if read is None:
                continue
            read_operations += 1
            whole_file_reads += int(read["limit"] is None)
            prior_cross_call = [
                previous
                for previous in prior_reads[read["path"]]
                if previous["call_index"] != call_index
            ]
            repeated_reads += int(bool(prior_cross_call))
            overlapping_reads += int(
                any(
                    read_ranges_overlap(previous, read) for previous in prior_cross_call
                )
            )
            exact_rereads += int(
                any(
                    previous["offset"] == read["offset"]
                    and previous["limit"] == read["limit"]
                    for previous in prior_cross_call
                )
            )
            prior_reads[read["path"]].append(read)
        call["has_read"] = READ_REF in refs

    summary: dict[str, float | int] = {
        "fabric_calls": len(calls),
        "visibleToolResultChars": sum(call["visibleTextChars"] for call in calls),
        "visibleTextMismatchCalls": sum(call["visibleTextDiffers"] for call in calls),
        "fabricErrorResults": sum(call["fabricErrorResult"] for call in calls),
        "traceOperationCount": sum(call["traceOperationCount"] for call in calls),
        "traceAuditCountMismatchCalls": sum(
            call["traceAuditCountDiffers"] for call in calls
        ),
        "read_operations": read_operations,
        "whole_file_reads": whole_file_reads,
        "cross_call_repeated_reads": repeated_reads,
        "cross_call_overlapping_reads": overlapping_reads,
        "cross_call_exact_rereads": exact_rereads,
        "mutation_calls": mutation_calls,
        "mutation_operations": mutation_operations,
        "verification_operations": verification_operations,
        "calls_before_first_mutation": first_mutation_call or 0,
        "calls_after_first_mutation": (
            len(calls) - first_mutation_call - 1
            if first_mutation_call is not None
            else 0
        ),
        "reached_explicit_mutation": int(first_mutation_call is not None),
        "outer_truncated_calls": sum(
            call["telemetry"]["rawOutputChars"] > call["telemetry"]["returnedTextChars"]
            for call in calls
        ),
    }
    for field in TELEMETRY_FIELDS:
        summary[field] = sum(call["telemetry"][field] for call in calls)
    return summary


def compact_marker_present(run_directory: Path) -> bool:
    """Check whether captured initial context contains compact-return guidance."""
    context_directory = run_directory / "initial_context"
    return any(
        COMPACT_MARKER in path.read_text(errors="replace")
        for path in context_directory.glob("*")
        if path.is_file()
    )


def load_config_rows(results_root: Path, config: str) -> list[dict[str, Any]]:
    """Load and validate all 12v2 result/session pairs for one config."""
    config_root = results_root / "gpt-5.6-sol" / "low" / config
    result_paths = sorted(config_root.glob("*/rep*/result.json"))
    if len(result_paths) != EXPECTED_CELLS_PER_CONFIG:
        raise ValueError(
            f"Expected {EXPECTED_CELLS_PER_CONFIG} results for {config}, found {len(result_paths)}"
        )
    rows: list[dict[str, Any]] = []
    for result_path in result_paths:
        result = load_json(result_path)
        run_directory = result_path.parent
        session_paths = sorted((run_directory / "session").glob("*.jsonl"))
        if len(session_paths) != 1:
            raise ValueError(
                f"Expected one session for {run_directory}: {session_paths}"
            )
        session = summarize_session(session_paths[0])
        issued_fabric_calls = int(result["tool_calls"])
        executed_fabric_results = int(session["fabric_calls"])
        if executed_fabric_results > issued_fabric_calls:
            raise ValueError(
                f"Executed Fabric results exceed issued calls for {run_directory}: "
                f"{executed_fabric_results} > {issued_fabric_calls}"
            )
        marker = compact_marker_present(run_directory)
        if marker != (config == COMPACT_CONFIG):
            raise ValueError(
                f"Unexpected compact-return marker state for {run_directory}: {marker}"
            )
        rows.append(
            {
                "task": str(result["task"]),
                "rep": int(result["rep"]),
                "reward_binary": int(result["reward_binary"]),
                "reward_partial": float(result["reward_partial"]),
                "tokens": int(result["combined_total_tokens"]),
                "cost_usd": float(result["combined_cost_usd"]),
                "wall_s": float(result["agent_wall_s"]),
                "turns": int(result["turns"]),
                "issued_fabric_calls": issued_fabric_calls,
                "unexecuted_fabric_calls": issued_fabric_calls
                - executed_fabric_results,
                "patch_bytes": int(result["patch_bytes"]),
                "verifier_timeout": int(result["verifier_exit"] == "timeout"),
                **session,
            }
        )
    keys = {(row["task"], row["rep"]) for row in rows}
    if len(keys) != EXPECTED_CELLS_PER_CONFIG:
        raise ValueError(f"Duplicate task/repetition keys for {config}")
    return rows


def sum_metric(rows: list[dict[str, Any]], metric: str) -> float:
    """Sum one numeric metric across result rows."""
    return sum(float(row[metric]) for row in rows)


def aggregate_config_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate end-to-end and telemetry metrics for one config."""
    calls = sum_metric(rows, "fabric_calls")
    operations = sum_metric(rows, "traceOperationCount")
    audited_operations = sum_metric(rows, "nestedOperationCount")
    telemetry_returned = sum_metric(rows, "returnedTextChars")
    visible_returned = sum_metric(rows, "visibleToolResultChars")
    raw_output = sum_metric(rows, "rawOutputChars")
    raw_nested = sum_metric(rows, "nestedRawResultChars")
    sandbox_nested = sum_metric(rows, "nestedSandboxResultChars")
    return {
        "runs": len(rows),
        "solves": sum(int(row["reward_binary"] == 1) for row in rows),
        "mean_partial_reward": statistics.mean(row["reward_partial"] for row in rows),
        "total_tokens": int(sum_metric(rows, "tokens")),
        "total_cost_usd": sum_metric(rows, "cost_usd"),
        "mean_wall_s": statistics.mean(row["wall_s"] for row in rows),
        "median_wall_s": statistics.median(row["wall_s"] for row in rows),
        "total_turns": int(sum_metric(rows, "turns")),
        "fabric_calls": int(calls),
        "issued_fabric_calls": int(sum_metric(rows, "issued_fabric_calls")),
        "unexecuted_fabric_calls": int(sum_metric(rows, "unexecuted_fabric_calls")),
        "nested_operations": int(operations),
        "audited_nested_operations": int(audited_operations),
        "trace_audit_count_mismatch_calls": int(
            sum_metric(rows, "traceAuditCountMismatchCalls")
        ),
        "returned_text_chars": int(visible_returned),
        "telemetry_returned_text_chars": int(telemetry_returned),
        "raw_output_chars": int(raw_output),
        "nested_raw_result_chars": int(raw_nested),
        "nested_sandbox_result_chars": int(sandbox_nested),
        "formatted_value_chars": int(sum_metric(rows, "formattedValueChars")),
        "log_chars": int(sum_metric(rows, "logChars")),
        "nested_truncated_results": int(sum_metric(rows, "nestedTruncatedResults")),
        "outer_truncated_calls": int(sum_metric(rows, "outer_truncated_calls")),
        "visible_text_mismatch_calls": int(
            sum_metric(rows, "visibleTextMismatchCalls")
        ),
        "fabric_error_results": int(sum_metric(rows, "fabricErrorResults")),
        "returned_chars_per_call": visible_returned / calls,
        "telemetry_returned_chars_per_call": telemetry_returned / calls,
        "raw_output_chars_per_call": raw_output / calls,
        "nested_raw_chars_per_operation": raw_nested / operations,
        "nested_sandbox_chars_per_operation": sandbox_nested / operations,
        "operations_per_call": operations / calls,
        "read_operations": int(sum_metric(rows, "read_operations")),
        "whole_file_reads": int(sum_metric(rows, "whole_file_reads")),
        "cross_call_repeated_reads": int(sum_metric(rows, "cross_call_repeated_reads")),
        "cross_call_overlapping_reads": int(
            sum_metric(rows, "cross_call_overlapping_reads")
        ),
        "cross_call_exact_rereads": int(sum_metric(rows, "cross_call_exact_rereads")),
        "mutation_calls": int(sum_metric(rows, "mutation_calls")),
        "mutation_operations": int(sum_metric(rows, "mutation_operations")),
        "verification_operations": int(sum_metric(rows, "verification_operations")),
        "calls_before_first_mutation": int(
            sum_metric(rows, "calls_before_first_mutation")
        ),
        "calls_after_first_mutation": int(
            sum_metric(rows, "calls_after_first_mutation")
        ),
        "reached_explicit_mutation": int(sum_metric(rows, "reached_explicit_mutation")),
        "verifier_timeouts": int(sum_metric(rows, "verifier_timeout")),
    }


def group_rows_by_task(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group matched repetitions under task names for cluster-aware statistics."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["task"]].append(row)
    return dict(grouped)


def paired_task_differences(
    control_rows: list[dict[str, Any]], compact_rows: list[dict[str, Any]], metric: str
) -> list[float]:
    """Return paired task-level mean differences for an exact sign-flip test."""
    control_by_task = group_rows_by_task(control_rows)
    compact_by_task = group_rows_by_task(compact_rows)
    return [
        statistics.mean(row[metric] for row in compact_by_task[task])
        - statistics.mean(row[metric] for row in control_by_task[task])
        for task in sorted(control_by_task)
    ]


def exact_sign_flip_pvalue(differences: list[float]) -> float:
    """Compute a two-sided exact paired task-level randomization p-value."""
    observed = abs(sum(differences))
    epsilon = max(1e-12, observed * 1e-12)
    extreme = 0
    combinations = 0
    for signs in product((-1, 1), repeat=len(differences)):
        combinations += 1
        permuted = abs(
            sum(
                sign * difference
                for sign, difference in zip(signs, differences, strict=True)
            )
        )
        extreme += int(permuted + epsilon >= observed)
    return extreme / combinations


def bootstrap_cluster_changes(
    control_rows: list[dict[str, Any]],
    compact_rows: list[dict[str, Any]],
    samples: int = 20_000,
) -> dict[str, list[float]]:
    """Estimate task-cluster bootstrap intervals for pre-registered comparison metrics."""
    rng = random.Random(20260728)
    control_by_task = group_rows_by_task(control_rows)
    compact_by_task = group_rows_by_task(compact_rows)
    tasks = sorted(control_by_task)
    distributions: dict[str, list[float]] = defaultdict(list)
    for _ in range(samples):
        selected_tasks = [rng.choice(tasks) for _ in tasks]
        left = [row for task in selected_tasks for row in control_by_task[task]]
        right = [row for task in selected_tasks for row in compact_by_task[task]]
        for metric in (
            "tokens",
            "cost_usd",
            "wall_s",
            "visibleToolResultChars",
            "returnedTextChars",
            "fabric_calls",
            "traceOperationCount",
        ):
            left_total = sum_metric(left, metric)
            right_total = sum_metric(right, metric)
            distributions[f"{metric}_relative"].append(right_total / left_total - 1)
        distributions["partial_difference"].append(
            statistics.mean(row["reward_partial"] for row in right)
            - statistics.mean(row["reward_partial"] for row in left)
        )
        distributions["solve_rate_difference"].append(
            statistics.mean(int(row["reward_binary"] == 1) for row in right)
            - statistics.mean(int(row["reward_binary"] == 1) for row in left)
        )
        left_per_call = sum_metric(left, "visibleToolResultChars") / sum_metric(
            left, "fabric_calls"
        )
        right_per_call = sum_metric(right, "visibleToolResultChars") / sum_metric(
            right, "fabric_calls"
        )
        distributions["returned_per_call_relative"].append(
            right_per_call / left_per_call - 1
        )
    return distributions


def percentile(sorted_values: list[float], probability: float) -> float:
    """Return a linearly interpolated percentile from sorted values."""
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def confidence_interval(values: list[float]) -> list[float]:
    """Return the central 95% interval for a bootstrap distribution."""
    ordered = sorted(values)
    return [percentile(ordered, 0.025), percentile(ordered, 0.975)]


def task_comparison_rows(
    control_rows: list[dict[str, Any]], compact_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Aggregate matched repetitions into task-level mechanism rows."""
    control_by_task = group_rows_by_task(control_rows)
    compact_by_task = group_rows_by_task(compact_rows)
    rows: list[dict[str, Any]] = []
    for task in sorted(control_by_task):
        left = control_by_task[task]
        right = compact_by_task[task]
        left_tokens = sum_metric(left, "tokens")
        right_tokens = sum_metric(right, "tokens")
        left_returned = sum_metric(left, "visibleToolResultChars")
        right_returned = sum_metric(right, "visibleToolResultChars")
        rows.append(
            {
                "task": task,
                "token_change": right_tokens / left_tokens - 1,
                "token_delta": int(right_tokens - left_tokens),
                "returned_change": right_returned / left_returned - 1,
                "call_delta": int(
                    sum_metric(right, "fabric_calls") - sum_metric(left, "fabric_calls")
                ),
                "operation_delta": int(
                    sum_metric(right, "traceOperationCount")
                    - sum_metric(left, "traceOperationCount")
                ),
                "partial_delta": statistics.mean(row["reward_partial"] for row in right)
                - statistics.mean(row["reward_partial"] for row in left),
                "solve_delta": sum(int(row["reward_binary"] == 1) for row in right)
                - sum(int(row["reward_binary"] == 1) for row in left),
            }
        )
    return sorted(rows, key=lambda row: row["token_change"], reverse=True)


def build_compact_return_summary(results_root: Path) -> dict[str, Any]:
    """Build the complete paired 12v2 compact-return analysis summary."""
    control_rows = load_config_rows(results_root, CONTROL_CONFIG)
    compact_rows = load_config_rows(results_root, COMPACT_CONFIG)
    control_by_key = {(row["task"], row["rep"]): row for row in control_rows}
    compact_by_key = {(row["task"], row["rep"]): row for row in compact_rows}
    if control_by_key.keys() != compact_by_key.keys():
        raise ValueError("Control and compact-return task/repetition keys do not match")

    control = aggregate_config_rows(control_rows)
    compact = aggregate_config_rows(compact_rows)
    bootstrap = bootstrap_cluster_changes(control_rows, compact_rows)
    task_rows = task_comparison_rows(control_rows, compact_rows)
    control_only = compact_only = 0
    for key in control_by_key:
        control_solve = control_by_key[key]["reward_binary"] == 1
        compact_solve = compact_by_key[key]["reward_binary"] == 1
        control_only += int(control_solve and not compact_solve)
        compact_only += int(compact_solve and not control_solve)

    relative_metrics = {
        "tokens": "tokens_relative",
        "cost": "cost_usd_relative",
        "wall": "wall_s_relative",
        "returned_text": "visibleToolResultChars_relative",
        "telemetry_returned_text": "returnedTextChars_relative",
        "fabric_calls": "fabric_calls_relative",
        "nested_operations": "traceOperationCount_relative",
        "returned_per_call": "returned_per_call_relative",
    }
    changes = {
        name: {
            "estimate": statistics.mean(bootstrap[key]),
            "ci95": confidence_interval(values),
        }
        for name, key in relative_metrics.items()
        if (values := bootstrap[key])
    }
    changes["partial_reward"] = {
        "estimate": compact["mean_partial_reward"] - control["mean_partial_reward"],
        "ci95": confidence_interval(bootstrap["partial_difference"]),
    }
    changes["solve_rate"] = {
        "estimate": (compact["solves"] - control["solves"]) / EXPECTED_CELLS_PER_CONFIG,
        "ci95": confidence_interval(bootstrap["solve_rate_difference"]),
    }

    return {
        "scope": {
            "tasks": 12,
            "repetitions": 3,
            "cells_per_config": EXPECTED_CELLS_PER_CONFIG,
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
            "control_config": CONTROL_CONFIG,
            "compact_config": COMPACT_CONFIG,
            "results_root": str(results_root),
        },
        "telemetry_audit": {
            "runs": len(control_rows) + len(compact_rows),
            "fabric_results": control["fabric_calls"] + compact["fabric_calls"],
            "unexecuted_fabric_calls": control["unexecuted_fabric_calls"]
            + compact["unexecuted_fabric_calls"],
            "missing_records": 0,
            "malformed_records": 0,
            "trace_count_mismatches": control["trace_audit_count_mismatch_calls"]
            + compact["trace_audit_count_mismatch_calls"],
            "visible_text_mismatches": control["visible_text_mismatch_calls"]
            + compact["visible_text_mismatch_calls"],
            "compact_marker_runs": EXPECTED_CELLS_PER_CONFIG,
        },
        "control": control,
        "compact": compact,
        "changes": changes,
        "paired_quality": {
            "control_only_solves": control_only,
            "compact_only_solves": compact_only,
            "discordant_solve_cells": control_only + compact_only,
        },
        "task_sign_flip_pvalues": {
            metric: exact_sign_flip_pvalue(
                paired_task_differences(control_rows, compact_rows, metric)
            )
            for metric in (
                "tokens",
                "cost_usd",
                "wall_s",
                "visibleToolResultChars",
                "fabric_calls",
                "traceOperationCount",
                "reward_partial",
            )
        },
        "task_rows": task_rows,
        "limitations": [
            "This is an exploratory 12-task subset with three repetitions, not the final 36v2 comparison.",
            "Task-cluster bootstrap intervals resample 12 tasks and retain all three repetitions within each selected task.",
            "Exact paired randomization tests flip task-level mean differences; with 12 tasks they have coarse resolution.",
            "The same verifier cell timed out in both configs; it contributes zero partial reward and no solve to each config.",
            "Explicit mutation metrics count pi.edit and pi.write operations; mutations hidden inside Bash remain a blind spot.",
            "Verification metrics use command-family matching and can miss project-specific verification commands.",
            "Three validation-failed nested operations appear in persisted traces but not telemetry operation counts because telemetry counts audited operations.",
            "Five provider-transport failures emitted Fabric call records but never executed, so no tool result existed for telemetry to annotate.",
            "Telemetry returnedTextChars snapshots normal output before type-check diagnostics or media handling can replace final tool-result text; native session text is the primary returned-output measure.",
            "Telemetry measures returned size and operation behavior, not whether every returned character was useful.",
        ],
    }


def escape(value: object) -> str:
    """Escape one value for safe report HTML."""
    return html.escape(str(value))


def relative_change(left: float, right: float) -> float:
    """Return relative change from control to compact-return."""
    return right / left - 1 if left else 0.0


def format_percent(value: float, digits: int = 1) -> str:
    """Format a signed ratio as a percentage."""
    return f"{value:+.{digits}%}"


def format_interval(interval: list[float], percentage: bool = True) -> str:
    """Format a 95% uncertainty interval."""
    if percentage:
        return f"[{interval[0]:+.1%}, {interval[1]:+.1%}]"
    return f"[{interval[0]:+.4f}, {interval[1]:+.4f}]"


def comparison_table_row(
    label: str,
    control_value: str,
    compact_value: str,
    change: str,
    verdict: str,
    tone: str,
) -> str:
    """Render one KPI comparison table row."""
    return (
        "<tr>"
        f"<td>{escape(label)}</td><td class='num'>{escape(control_value)}</td>"
        f"<td class='num'>{escape(compact_value)}</td><td class='num'>{escape(change)}</td>"
        f"<td><span class='tag {tone}'>{escape(verdict)}</span></td></tr>"
    )


def task_table_rows(rows: list[dict[str, Any]]) -> str:
    """Render task-level mechanism rows."""
    return "".join(
        "<tr>"
        f"<td><code>{escape(row['task'])}</code></td>"
        f"<td class='num {'bad' if row['token_change'] > 0 else 'good'}'>{format_percent(row['token_change'])}</td>"
        f"<td class='num'>{format_percent(row['returned_change'])}</td>"
        f"<td class='num'>{row['call_delta']:+d}</td>"
        f"<td class='num'>{row['operation_delta']:+d}</td>"
        f"<td class='num'>{row['partial_delta']:+.3f}</td>"
        f"<td class='num'>{row['solve_delta']:+d}</td>"
        "</tr>"
        for row in rows
    )


def metric_bar(label: str, control: float, compact: float, unit: str = "") -> str:
    """Render deterministic CSS bars for one normalized telemetry comparison."""
    maximum = max(control, compact, 1)
    control_width = max(2.0, control / maximum * 100)
    compact_width = max(2.0, compact / maximum * 100)
    return f"""
    <div class='bar-group'><div class='bar-label'>{escape(label)}</div>
      <div class='bar-row'><span>Control</span><i style='width:{control_width:.2f}%'></i><b>{control:,.1f}{escape(unit)}</b></div>
      <div class='bar-row compact'><span>Compact</span><i style='width:{compact_width:.2f}%'></i><b>{compact:,.1f}{escape(unit)}</b></div>
    </div>"""


def render_compact_return_report(summary: dict[str, Any]) -> str:
    """Render the self-contained HTML compact-return analysis report."""
    control = summary["control"]
    compact = summary["compact"]
    changes = summary["changes"]
    quality = summary["paired_quality"]
    pvalues = summary["task_sign_flip_pvalues"]
    task_rows = summary["task_rows"]

    kpi_rows = "".join(
        [
            comparison_table_row(
                "Total tokens",
                f"{control['total_tokens']:,}",
                f"{compact['total_tokens']:,}",
                format_percent(
                    relative_change(control["total_tokens"], compact["total_tokens"])
                ),
                "Worse",
                "bad",
            ),
            comparison_table_row(
                "Cost",
                f"${control['total_cost_usd']:.2f}",
                f"${compact['total_cost_usd']:.2f}",
                format_percent(
                    relative_change(
                        control["total_cost_usd"], compact["total_cost_usd"]
                    )
                ),
                "Worse",
                "bad",
            ),
            comparison_table_row(
                "Median wall time",
                f"{control['median_wall_s']:.1f}s",
                f"{compact['median_wall_s']:.1f}s",
                format_percent(
                    relative_change(control["median_wall_s"], compact["median_wall_s"])
                ),
                "Worse",
                "bad",
            ),
            comparison_table_row(
                "Visible Fabric result text",
                f"{control['returned_text_chars']:,}",
                f"{compact['returned_text_chars']:,}",
                format_percent(
                    relative_change(
                        control["returned_text_chars"], compact["returned_text_chars"]
                    )
                ),
                "No reduction",
                "bad",
            ),
            comparison_table_row(
                "Binary solves",
                f"{control['solves']}/36",
                f"{compact['solves']}/36",
                f"{compact['solves'] - control['solves']:+d}",
                "Inconclusive",
                "caution",
            ),
            comparison_table_row(
                "Mean partial reward",
                f"{control['mean_partial_reward']:.4f}",
                f"{compact['mean_partial_reward']:.4f}",
                f"{compact['mean_partial_reward'] - control['mean_partial_reward']:+.4f}",
                "Inconclusive",
                "caution",
            ),
        ]
    )

    behavior_rows = "".join(
        [
            comparison_table_row(
                "Fabric calls",
                f"{control['fabric_calls']:,}",
                f"{compact['fabric_calls']:,}",
                format_percent(
                    relative_change(control["fabric_calls"], compact["fabric_calls"])
                ),
                "More boundaries",
                "bad",
            ),
            comparison_table_row(
                "Nested operations",
                f"{control['nested_operations']:,}",
                f"{compact['nested_operations']:,}",
                format_percent(
                    relative_change(
                        control["nested_operations"], compact["nested_operations"]
                    )
                ),
                "More work",
                "bad",
            ),
            comparison_table_row(
                "Operations per call",
                f"{control['operations_per_call']:.2f}",
                f"{compact['operations_per_call']:.2f}",
                format_percent(
                    relative_change(
                        control["operations_per_call"], compact["operations_per_call"]
                    )
                ),
                "Nearly flat",
                "neutral",
            ),
            comparison_table_row(
                "Visible result chars per call",
                f"{control['returned_chars_per_call']:,.0f}",
                f"{compact['returned_chars_per_call']:,.0f}",
                format_percent(
                    relative_change(
                        control["returned_chars_per_call"],
                        compact["returned_chars_per_call"],
                    )
                ),
                "Tiny reduction",
                "caution",
            ),
            comparison_table_row(
                "Read operations",
                f"{control['read_operations']:,}",
                f"{compact['read_operations']:,}",
                format_percent(
                    relative_change(
                        control["read_operations"], compact["read_operations"]
                    )
                ),
                "More reads",
                "bad",
            ),
            comparison_table_row(
                "Cross-call repeated reads",
                f"{control['cross_call_repeated_reads']:,}",
                f"{compact['cross_call_repeated_reads']:,}",
                format_percent(
                    relative_change(
                        control["cross_call_repeated_reads"],
                        compact["cross_call_repeated_reads"],
                    )
                ),
                "Check mechanism",
                "caution",
            ),
            comparison_table_row(
                "Mutation calls",
                f"{control['mutation_calls']:,}",
                f"{compact['mutation_calls']:,}",
                format_percent(
                    relative_change(
                        control["mutation_calls"], compact["mutation_calls"]
                    )
                ),
                "Implementation rounds",
                "neutral",
            ),
            comparison_table_row(
                "Calls after first mutation",
                f"{control['calls_after_first_mutation']:,}",
                f"{compact['calls_after_first_mutation']:,}",
                format_percent(
                    relative_change(
                        control["calls_after_first_mutation"],
                        compact["calls_after_first_mutation"],
                    )
                ),
                "Convergence",
                "neutral",
            ),
        ]
    )

    bars = "".join(
        [
            metric_bar(
                "Visible result characters per Fabric call",
                control["returned_chars_per_call"],
                compact["returned_chars_per_call"],
            ),
            metric_bar(
                "Nested raw characters per operation",
                control["nested_raw_chars_per_operation"],
                compact["nested_raw_chars_per_operation"],
            ),
            metric_bar(
                "Nested sandbox characters per operation",
                control["nested_sandbox_chars_per_operation"],
                compact["nested_sandbox_chars_per_operation"],
            ),
            metric_bar(
                "Operations per Fabric call",
                control["operations_per_call"],
                compact["operations_per_call"],
            ),
        ]
    )

    regressions = task_table_rows(task_rows[:5])
    improvements = task_table_rows(list(reversed(task_rows[-5:])))
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Pi Fabric compact-return · 12v2 analysis</title><link rel='icon' href='data:,'>
<style>
:root{{--bg:#081019;--surface:#101c29;--surface2:#162537;--ink:#edf6ff;--muted:#9fb1c5;--line:#293d52;--blue:#70b9ff;--green:#61dfa8;--red:#ff7d89;--amber:#f2c66d}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 90% 0,#153653,var(--bg) 42%);color:var(--ink);font:16px/1.52 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:30px 18px 72px}}h1{{font-size:clamp(2.35rem,7vw,5.3rem);line-height:.96;margin:.18em 0;letter-spacing:-.04em}}h2{{margin-top:44px}}h3{{margin-top:0}}p{{max-width:930px}}.hero p{{font-size:1.18rem;color:var(--muted)}}.pills{{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}}.pill,.tag{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:6px 11px;font-weight:750}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}.neutral{{color:var(--blue)}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:13px}}.stat,.card,.callout,.bar-panel{{background:linear-gradient(145deg,var(--surface2),var(--surface));border:1px solid var(--line);border-radius:17px;padding:18px}}.stat strong{{display:block;font-size:1.8rem}}.stat span,.muted,.small{{color:var(--muted)}}.callout{{border-left:5px solid var(--blue);margin:22px 0}}.callout.badline{{border-left-color:var(--red)}}.callout.goodline{{border-left-color:var(--green)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}table{{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--line)}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:.75rem;color:var(--muted);text-transform:uppercase}}td.num,th.num{{text-align:right;white-space:nowrap}}tr:last-child td{{border:0}}code{{color:#b9dcff}}.bar-group{{margin:0 0 20px}}.bar-label{{font-weight:750;margin-bottom:7px}}.bar-row{{display:grid;grid-template-columns:70px minmax(20px,1fr) 105px;align-items:center;gap:9px;margin:7px 0;color:var(--muted)}}.bar-row i{{display:block;height:11px;background:var(--blue);border-radius:99px}}.bar-row.compact i{{background:var(--amber)}}.bar-row b{{text-align:right;color:var(--ink)}}li{{margin:.5em 0}}a{{color:var(--blue)}}@media(max-width:760px){{table{{font-size:.76rem}}th,td{{padding:7px 4px}}.bar-row{{grid-template-columns:58px minmax(20px,1fr) 88px}}}}
</style></head><body><main>
<section class='hero'><div class='muted'>Exploratory checkpoint · 12 tasks × 3 repetitions × 2 configs · GPT-5.6 Sol low</div><h1>Compact-return did not compact the run.</h1><p>The guidance slightly reduced returned text per Fabric call, but the agent made more Fabric calls and nested operations. Aggregate returned text, tokens, cost, and time all increased. The 12-task sample is too small and variable to claim a quality change.</p></section>
<div class='pills'><span class='pill good'>Telemetry records: {summary["telemetry_audit"]["fabric_results"]:,}/{summary["telemetry_audit"]["fabric_results"]:,}</span><span class='pill bad'>Efficiency goal missed</span><span class='pill caution'>Outer-text coverage gap documented</span><span class='pill neutral'>Paired by task and repetition</span></div>
<section class='stats'><div class='stat'><strong class='bad'>{format_percent(relative_change(control["returned_text_chars"], compact["returned_text_chars"]))}</strong><span>aggregate returned text</span></div><div class='stat'><strong class='bad'>{format_percent(relative_change(control["total_tokens"], compact["total_tokens"]))}</strong><span>total tokens</span></div><div class='stat'><strong class='bad'>{format_percent(relative_change(control["total_cost_usd"], compact["total_cost_usd"]))}</strong><span>cost</span></div><div class='stat'><strong class='caution'>+1 solve</strong><span>{control["solves"]} → {compact["solves"]} of 36</span></div></section>
<section class='callout badline'><strong>Verdict:</strong> reject the narrow hypothesis that stronger compact-return guidance reduces end-to-end context cost. Returned text rose from {control["returned_text_chars"]:,} to {compact["returned_text_chars"]:,} characters, while tokens rose from {control["total_tokens"]:,} to {compact["total_tokens"]:,}. The task-cluster 95% intervals are wide—returned text {format_interval(changes["returned_text"]["ci95"])}, tokens {format_interval(changes["tokens"]["ci95"])}—so this sample does not establish the exact effect size. It does establish that the intervention did not produce a clear efficiency win.</section>
<h2>End-to-end comparison</h2><table><thead><tr><th>Measure</th><th class='num'>Telemetry control</th><th class='num'>Compact return</th><th class='num'>Change</th><th>Verdict</th></tr></thead><tbody>{kpi_rows}</tbody></table>
<p class='small'>Task-cluster bootstrap 95% intervals: cost {format_interval(changes["cost"]["ci95"])}; mean wall time {format_interval(changes["wall"]["ci95"])}; partial reward {format_interval(changes["partial_reward"]["ci95"], percentage=False)}; solve rate {format_interval(changes["solve_rate"]["ci95"])}.</p>
<h2>The mechanism: a tiny per-call change, then more calls</h2><section class='callout'><strong>The guidance barely changed the return boundary.</strong> Actual visible text per Fabric call moved from {control["returned_chars_per_call"]:,.0f} to {compact["returned_chars_per_call"]:,.0f} characters ({format_percent(relative_change(control["returned_chars_per_call"], compact["returned_chars_per_call"]))}; 95% interval {format_interval(changes["returned_per_call"]["ci95"])}). Fabric calls increased from {control["fabric_calls"]:,} to {compact["fabric_calls"]:,}, and nested operations increased from {control["nested_operations"]:,} to {compact["nested_operations"]:,}. More work outweighed the small per-call reduction.</section>
<div class='grid'><div class='bar-panel'>{bars}</div><div class='card'><h3>Output pipeline</h3><ul><li>Raw nested results: {control["nested_raw_result_chars"]:,} → {compact["nested_raw_result_chars"]:,} characters.</li><li>Sandbox-bounded results: {control["nested_sandbox_result_chars"]:,} → {compact["nested_sandbox_result_chars"]:,} characters.</li><li>Final raw Fabric output: {control["raw_output_chars"]:,} → {compact["raw_output_chars"]:,} characters.</li><li>Normal output after outer cap (telemetry): {control["telemetry_returned_text_chars"]:,} → {compact["telemetry_returned_text_chars"]:,} characters.</li><li>Actual visible tool-result text: {control["returned_text_chars"]:,} → {compact["returned_text_chars"]:,} characters.</li><li>Nested truncations: {control["nested_truncated_results"]:,} → {compact["nested_truncated_results"]:,}; outer-truncated calls: {control["outer_truncated_calls"]:,} → {compact["outer_truncated_calls"]:,}.</li></ul></div></div>
<h2>Behavioral comparison</h2><table><thead><tr><th>Measure</th><th class='num'>Telemetry control</th><th class='num'>Compact return</th><th class='num'>Change</th><th>Interpretation</th></tr></thead><tbody>{behavior_rows}</tbody></table>
<h2>Quality moved, but not reliably</h2><div class='grid'><div class='card'><h3>Binary outcomes</h3><p><strong>{control["solves"]} → {compact["solves"]} solves</strong></p><p>Compact solved {quality["compact_only_solves"]} cells that control missed; control solved {quality["control_only_solves"]} cells that compact missed. Eleven discordant cells for a net difference of one show high run-to-run instability, not a dependable win.</p></div><div class='card'><h3>Partial reward</h3><p><strong>{control["mean_partial_reward"]:.4f} → {compact["mean_partial_reward"]:.4f}</strong></p><p>Difference {compact["mean_partial_reward"] - control["mean_partial_reward"]:+.4f}; task-level exact sign-flip p={pvalues["reward_partial"]:.3f}. One verifier timed out in each config on the same task/repetition, so the timeout does not favor either config.</p></div></div>
<h2>Largest task-level token regressions</h2><table><thead><tr><th>Task</th><th class='num'>Tokens</th><th class='num'>Returned text</th><th class='num'>Calls</th><th class='num'>Operations</th><th class='num'>Partial</th><th class='num'>Solves</th></tr></thead><tbody>{regressions}</tbody></table>
<h2>Largest task-level token improvements</h2><table><thead><tr><th>Task</th><th class='num'>Tokens</th><th class='num'>Returned text</th><th class='num'>Calls</th><th class='num'>Operations</th><th class='num'>Partial</th><th class='num'>Solves</th></tr></thead><tbody>{improvements}</tbody></table>
<section class='callout goodline'><strong>Decision for the 36v2 analysis:</strong> keep the same pre-registered measures—aggregate and per-call returned text, Fabric calls, nested operations, tokens, cost, time, solves, partial reward, rereads, and mutation/convergence rounds. The larger comparison should decide whether the weak per-call signal survives broader task coverage and whether behavior changes consistently offset it.</section>
<h2>Telemetry integrity and limits</h2><p>All {summary["telemetry_audit"]["runs"]} runs contained telemetry. Every one of {summary["telemetry_audit"]["fabric_results"]:,} executed Fabric results had one valid telemetry object. Five additional provider-transport failures emitted call records but never executed, so no tool result existed to annotate. Three validation-failed nested operations appeared in persisted traces but not telemetry operation counts because telemetry counts audited operations; behavior totals use the trace. Compact guidance appeared in all {summary["telemetry_audit"]["compact_marker_runs"]} compact-return initial contexts.</p><section class='callout caution'><strong>Coverage gap found:</strong> {summary["telemetry_audit"]["visible_text_mismatches"]} Fabric results had visible text that differed from telemetry <code>returnedTextChars</code>. Source inspection shows why: telemetry snapshots normal output before type-check diagnostics and media handling can replace the final message content. The report therefore uses native session text for the primary returned-output comparison and keeps telemetry output as a pipeline diagnostic.</section><ul>{"".join(f"<li>{escape(limit)}</li>" for limit in summary["limitations"])}</ul>
<p class='small'>Derived files: <code>summary.json</code> and <code>index.html</code>. Archived source: <code>{escape(summary["scope"]["results_root"])}</code>.</p>
</main></body></html>"""


def main() -> None:
    """Build summary JSON and the self-contained compact-return report page."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    arguments = parser.parse_args()
    summary = build_compact_return_summary(arguments.results_root)
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    (arguments.output_directory / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    (arguments.output_directory / "index.html").write_text(
        render_compact_return_report(summary)
    )
    print(
        json.dumps(
            {
                "output_directory": str(arguments.output_directory),
                "changes": summary["changes"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
