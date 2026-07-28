#!/usr/bin/env python3
"""Measure why native read guidance changes Pi Fabric trajectory cost."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path
from typing import Any

SEARCH_REFS = {"pi.grep", "pi.find", "pi.ls"}
READ_REFS = {"pi.read"}
MUTATION_REFS = {"pi.edit", "pi.write"}
VERIFY_COMMAND = re.compile(
    r"(?:^|[;&|]\s*|\b)(?:pytest|python\s+-m\s+pytest|npm\s+(?:test|run\s+(?:test|lint|typecheck))|"
    r"pnpm\s+(?:test|lint|typecheck)|yarn\s+(?:test|lint|typecheck)|cargo\s+(?:test|check|clippy)|"
    r"go\s+test|ruff\s+(?:check|format)|mypy|pyright|ty\s+check|tsc(?:\s|$)|make\s+(?:test|check))"
)
CONTROL_FLOW = re.compile(r"\b(?:if|switch|for|while|try)\b")
PROMISE_ALL = re.compile(r"Promise\.all")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def message_usage(message: dict[str, Any]) -> dict[str, int]:
    usage = message.get("usage") or {}
    return {
        "cache_read": int(usage.get("cacheRead", 0) or 0),
        "input": int(usage.get("input", 0) or 0),
        "output": int(usage.get("output", 0) or 0),
    }


def operation_refs(operations: list[dict[str, Any]]) -> set[str]:
    return {str(operation.get("ref", "")) for operation in operations}


def parse_read_operation(
    operation: dict[str, Any], call_index: int
) -> dict[str, Any] | None:
    if operation.get("ref") != "pi.read":
        return None
    args = operation.get("args") or {}
    path = args.get("path")
    if not isinstance(path, str) or not path:
        return None
    offset = args.get("offset", 1)
    limit = args.get("limit")
    return {
        "path": path,
        "offset": int(offset) if isinstance(offset, int | float) else 1,
        "limit": int(limit) if isinstance(limit, int | float) else None,
        "call_index": call_index,
    }


def call_from_messages(
    assistant_message: dict[str, Any], tool_call: dict[str, Any], call_index: int
) -> dict[str, Any]:
    arguments = tool_call.get("arguments") or {}
    return {
        "index": call_index,
        "tool_call_id": tool_call.get("id"),
        "code": str(arguments.get("code", "")),
        "usage": message_usage(assistant_message),
        "operations": [],
        "result_chars": 0,
        "success": None,
        "native_parallel": False,
    }


def decorate_call(call: dict[str, Any]) -> dict[str, Any]:
    refs = operation_refs(call["operations"])
    call["has_search"] = bool(refs & SEARCH_REFS)
    call["has_read"] = bool(refs & READ_REFS)
    call["has_mutation"] = bool(refs & MUTATION_REFS)
    call["has_bash"] = "pi.bash" in refs
    call["promise_all"] = bool(PROMISE_ALL.search(call["code"]))
    call["parallel"] = call["native_parallel"] or call["promise_all"]
    call["control_flow"] = bool(CONTROL_FLOW.search(call["code"]))
    call["reads"] = [
        read
        for operation in call["operations"]
        if (read := parse_read_operation(operation, call["index"])) is not None
    ]
    call["mutation_paths"] = [
        str((operation.get("args") or {}).get("path"))
        for operation in call["operations"]
        if operation.get("ref") in MUTATION_REFS
        and isinstance((operation.get("args") or {}).get("path"), str)
    ]
    return call


def finalize_call(
    call: dict[str, Any], tool_result_message: dict[str, Any]
) -> dict[str, Any]:
    details = tool_result_message.get("details") or {}
    trace = details.get("trace") or {}
    operations = trace.get("operations") or []
    call["operations"] = [item for item in operations if isinstance(item, dict)]
    call["result_chars"] = sum(
        len(str(item.get("text", "")))
        for item in tool_result_message.get("content") or []
        if isinstance(item, dict) and item.get("type") == "text"
    )
    call["success"] = bool(
        details.get("success", not tool_result_message.get("isError"))
    )
    return decorate_call(call)


def parse_fabric_session(path: Path, task: str, rep: int) -> dict[str, Any]:
    calls: list[dict[str, Any]] = []
    pending: dict[str, dict[str, Any]] = {}
    for raw_line in path.read_text(errors="replace").splitlines():
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "message":
            continue
        message = record.get("message") or {}
        if message.get("role") == "assistant":
            for item in message.get("content") or []:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "toolCall" and item.get("name") == "fabric_exec":
                    call = call_from_messages(message, item, len(calls) + len(pending))
                    pending[str(item.get("id"))] = call
        elif (
            message.get("role") == "toolResult"
            and message.get("toolName") == "fabric_exec"
        ):
            call = pending.pop(str(message.get("toolCallId")), None)
            if call is not None:
                calls.append(finalize_call(call, message))
    calls.sort(key=lambda call: call["index"])
    for index, call in enumerate(calls):
        call["index"] = index
        for read in call["reads"]:
            read["call_index"] = index
    return {"task": task, "rep": rep, "calls": calls, "session": str(path)}


def parse_native_session(path: Path, task: str, rep: int) -> dict[str, Any]:
    calls: list[dict[str, Any]] = []
    pending: dict[str, dict[str, Any]] = {}
    for raw_line in path.read_text(errors="replace").splitlines():
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "message":
            continue
        message = record.get("message") or {}
        if message.get("role") == "assistant":
            tool_calls = [
                item
                for item in message.get("content") or []
                if isinstance(item, dict) and item.get("type") == "toolCall"
            ]
            if not tool_calls:
                continue
            call = {
                "index": len(calls) + len({id(group) for group in pending.values()}),
                "tool_call_id": None,
                "code": "",
                "usage": message_usage(message),
                "operations": [
                    {
                        "ref": f"pi.{item.get('name', '')}",
                        "args": item.get("arguments") or {},
                    }
                    for item in tool_calls
                ],
                "result_chars": 0,
                "success": True,
                "native_parallel": len(tool_calls) > 1,
                "remaining_ids": {str(item.get("id")) for item in tool_calls},
            }
            for item in tool_calls:
                pending[str(item.get("id"))] = call
        elif message.get("role") == "toolResult":
            tool_call_id = str(message.get("toolCallId"))
            call = pending.pop(tool_call_id, None)
            if call is None:
                continue
            call["result_chars"] += sum(
                len(str(item.get("text", "")))
                for item in message.get("content") or []
                if isinstance(item, dict) and item.get("type") == "text"
            )
            call["success"] = call["success"] and not bool(message.get("isError"))
            call["remaining_ids"].discard(tool_call_id)
            if not call["remaining_ids"]:
                call.pop("remaining_ids")
                calls.append(decorate_call(call))
    calls.sort(key=lambda call: call["index"])
    for index, call in enumerate(calls):
        call["index"] = index
        for read in call["reads"]:
            read["call_index"] = index
    return {"task": task, "rep": rep, "calls": calls, "session": str(path)}


def read_ranges_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left["limit"] is None or right["limit"] is None:
        return True
    left_end = left["offset"] + left["limit"] - 1
    right_end = right["offset"] + right["limit"] - 1
    return left["offset"] <= right_end and right["offset"] <= left_end


def verification_operation(operation: dict[str, Any]) -> bool:
    if operation.get("ref") != "pi.bash":
        return False
    command = str((operation.get("args") or {}).get("command", ""))
    return bool(VERIFY_COMMAND.search(command))


def call_category(call: dict[str, Any]) -> str:
    if call["has_mutation"]:
        return "mutation"
    if any(verification_operation(operation) for operation in call["operations"]):
        return "verification"
    if call["has_search"] or call["has_read"]:
        return "retrieval"
    if call["has_bash"]:
        return "bash_other"
    return "other"


def summarize_read_fragmentation(calls: list[dict[str, Any]]) -> dict[str, int]:
    prior_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    repeated = overlapping = exact = 0
    for call in calls:
        for read in call["reads"]:
            prior_cross_call = [
                prior
                for prior in prior_by_path[read["path"]]
                if prior["call_index"] != read["call_index"]
            ]
            if prior_cross_call:
                repeated += 1
            if any(read_ranges_overlap(prior, read) for prior in prior_cross_call):
                overlapping += 1
            if any(
                prior["offset"] == read["offset"] and prior["limit"] == read["limit"]
                for prior in prior_cross_call
            ):
                exact += 1
            prior_by_path[read["path"]].append(read)
    return {
        "cross_call_repeated_path_reads": repeated,
        "cross_call_overlapping_reads": overlapping,
        "cross_call_exact_rereads": exact,
    }


def summarize_trajectory(trajectory: dict[str, Any]) -> dict[str, Any]:
    calls = trajectory["calls"]
    first_mutation = next(
        (index for index, call in enumerate(calls) if call["has_mutation"]), None
    )
    mutation_boundary = first_mutation if first_mutation is not None else 0
    search_to_read = read_to_read = retrieval_continuation_cache = 0
    transition_cache: Counter[str] = Counter()
    for previous, current in pairwise(calls):
        if previous["has_search"] and not previous["has_read"] and current["has_read"]:
            search_to_read += 1
            transition_cache["search_only_to_read"] += current["usage"]["cache_read"]
        if previous["has_read"] and current["has_read"]:
            read_to_read += 1
            transition_cache["read_to_read"] += current["usage"]["cache_read"]
        if (previous["has_search"] or previous["has_read"]) and (
            current["has_search"] or current["has_read"]
        ):
            retrieval_continuation_cache += current["usage"]["cache_read"]
    categories = [call_category(call) for call in calls]
    transition_counts = Counter(pairwise(categories))
    mutation_seen = False
    verification_operations_after_mutation = 0
    verification_calls_after_mutation: set[int] = set()
    for call in calls:
        for operation in call["operations"]:
            if operation.get("ref") in MUTATION_REFS:
                mutation_seen = True
            elif mutation_seen and verification_operation(operation):
                verification_operations_after_mutation += 1
                verification_calls_after_mutation.add(call["index"])
    mutation_paths = [path for call in calls for path in call["mutation_paths"]]
    unique_mutation_paths = set(mutation_paths)
    calls_after_first_mutation = (
        len(calls) - first_mutation - 1 if first_mutation is not None else 0
    )
    calls_after_boundary = (
        calls[first_mutation + 1 :] if first_mutation is not None else []
    )
    metrics: dict[str, Any] = {
        "task": trajectory["task"],
        "rep": trajectory["rep"],
        "outer_calls": len(calls),
        "nested_operations": sum(len(call["operations"]) for call in calls),
        "successful_calls": sum(call["success"] is True for call in calls),
        "failed_calls": sum(call["success"] is False for call in calls),
        "promise_all_calls": sum(call["promise_all"] for call in calls),
        "parallel_calls": sum(call["parallel"] for call in calls),
        "control_flow_calls": sum(call["control_flow"] for call in calls),
        "single_operation_calls": sum(len(call["operations"]) == 1 for call in calls),
        "multi_operation_calls": sum(len(call["operations"]) > 1 for call in calls),
        "read_calls": sum(call["has_read"] for call in calls),
        "read_operations": sum(len(call["reads"]) for call in calls),
        "whole_file_read_operations": sum(
            read["limit"] is None for call in calls for read in call["reads"]
        ),
        "bounded_read_operations": sum(
            read["limit"] is not None for call in calls for read in call["reads"]
        ),
        "operation_count_histogram": dict(
            Counter(len(call["operations"]) for call in calls)
        ),
        "search_only_calls": sum(
            call["has_search"] and not call["has_read"] for call in calls
        ),
        "read_only_calls": sum(
            call["has_read"] and not call["has_search"] and not call["has_mutation"]
            for call in calls
        ),
        "same_call_search_and_read": sum(
            call["has_search"] and call["has_read"] for call in calls
        ),
        "trajectories_with_explicit_mutation": int(first_mutation is not None),
        "mutation_calls": sum(category == "mutation" for category in categories),
        "mutation_operations": sum(
            operation.get("ref") in MUTATION_REFS
            for call in calls
            for operation in call["operations"]
        ),
        "unique_mutation_paths": len(unique_mutation_paths),
        "repeated_mutation_path_operations": len(mutation_paths)
        - len(unique_mutation_paths),
        "consecutive_mutation_transitions": transition_counts[("mutation", "mutation")],
        "mutation_to_verification_transitions": transition_counts[
            ("mutation", "verification")
        ],
        "verification_to_mutation_transitions": transition_counts[
            ("verification", "mutation")
        ],
        "search_only_to_read_transitions": search_to_read,
        "read_to_read_transitions": read_to_read,
        "retrieval_calls_before_first_mutation": sum(
            call["has_search"] or call["has_read"] for call in calls[:mutation_boundary]
        ),
        "calls_before_first_mutation": mutation_boundary,
        "cache_read_before_first_mutation": sum(
            call["usage"]["cache_read"] for call in calls[:mutation_boundary]
        ),
        "calls_after_first_mutation": calls_after_first_mutation,
        "cache_read_after_first_mutation": sum(
            call["usage"]["cache_read"] for call in calls_after_boundary
        ),
        "mutation_call_cache_read": sum(
            call["usage"]["cache_read"]
            for call, category in zip(calls, categories, strict=True)
            if category == "mutation"
        ),
        "post_mutation_retrieval_calls": sum(
            call_category(call) == "retrieval" for call in calls_after_boundary
        ),
        "cache_read_for_retrieval_continuations": retrieval_continuation_cache,
        "cache_read_search_only_to_read": transition_cache["search_only_to_read"],
        "cache_read_read_to_read": transition_cache["read_to_read"],
        "verification_operations_after_mutation": verification_operations_after_mutation,
        "verification_calls_after_mutation": len(verification_calls_after_mutation),
        "returned_result_chars": sum(call["result_chars"] for call in calls),
        "assistant_cache_read": sum(call["usage"]["cache_read"] for call in calls),
        "assistant_input": sum(call["usage"]["input"] for call in calls),
        "assistant_output": sum(call["usage"]["output"] for call in calls),
    }
    metrics.update(summarize_read_fragmentation(calls))
    return metrics


def aggregate_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count_keys = [
        key
        for key, value in rows[0].items()
        if key not in {"task", "rep"} and isinstance(value, int | float)
    ]
    total = {key: sum(row[key] for row in rows) for key in count_keys}
    trajectory_medians = {
        key: statistics.median(row[key] for row in rows) for key in count_keys
    }
    calls = total["outer_calls"]
    operation_histogram: Counter[int] = Counter()
    for row in rows:
        operation_histogram.update(
            {
                int(count): frequency
                for count, frequency in row["operation_count_histogram"].items()
            }
        )
    operation_counts = sorted(
        operation_count
        for operation_count, frequency in operation_histogram.items()
        for _ in range(frequency)
    )
    return {
        "trajectories": len(rows),
        "totals": total,
        "trajectory_medians": trajectory_medians,
        "call_operation_distribution": {
            "histogram": dict(sorted(operation_histogram.items())),
            "median": statistics.median(operation_counts),
            "p90": operation_counts[math.ceil(len(operation_counts) * 0.9) - 1],
            "max": max(operation_counts),
        },
        "rates": {
            "promise_all_call_share": total["promise_all_calls"] / calls,
            "multi_operation_call_share": total["multi_operation_calls"] / calls,
            "single_operation_call_share": total["single_operation_calls"] / calls,
            "failed_call_share": total["failed_calls"] / calls,
            "same_call_search_and_read_per_search_only_to_read": (
                total["same_call_search_and_read"]
                / max(1, total["search_only_to_read_transitions"])
            ),
            "cross_call_repeated_reads_per_read_call": (
                total["cross_call_repeated_path_reads"] / max(1, total["read_calls"])
            ),
            "overlap_share_of_cross_call_repeated_reads": (
                total["cross_call_overlapping_reads"]
                / max(1, total["cross_call_repeated_path_reads"])
            ),
        },
    }


def final_patch_metrics(path: Path) -> dict[str, int]:
    text = path.read_text(errors="replace") if path.exists() else ""
    return {
        "final_patch_bytes": len(text.encode()),
        "final_patch_files": len(
            re.findall(r"^diff --git a/(.+?) b/", text, re.MULTILINE)
        ),
        "final_patch_additions": sum(
            line.startswith("+") and not line.startswith("+++")
            for line in text.splitlines()
        ),
        "final_patch_deletions": sum(
            line.startswith("-") and not line.startswith("---")
            for line in text.splitlines()
        ),
    }


def load_config_trajectories(
    results_root: Path,
    config: str,
    tasks: set[str],
    session_parser: Callable[[Path, str, int], dict[str, Any]] = parse_fabric_session,
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    trajectory_rows: list[dict[str, Any]] = []
    result_rows: dict[tuple[str, int], dict[str, Any]] = {}
    config_root = results_root / "gpt-5.6-sol/low" / config
    for result_path in sorted(config_root.glob("*/rep*/result.json")):
        task = result_path.parents[1].name
        if task not in tasks:
            continue
        rep = int(result_path.parent.name.removeprefix("rep"))
        session_paths = sorted((result_path.parent / "session").glob("*.jsonl"))
        if len(session_paths) != 1:
            raise ValueError(
                f"Expected one session for {task}/rep{rep}: {session_paths}"
            )
        trajectory = session_parser(session_paths[0], task, rep)
        metrics = summarize_trajectory(trajectory)
        metrics.update(
            final_patch_metrics(result_path.parent / "artifacts/model.patch")
        )
        trajectory_rows.append(metrics)
        result_rows[(task, rep)] = load_json(result_path)
    if len(trajectory_rows) != len(tasks) * 3:
        raise ValueError(
            f"Expected {len(tasks) * 3} trajectories for {config}, found {len(trajectory_rows)}"
        )
    return trajectory_rows, result_rows


def aggregate_outcomes(
    result_rows: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, float | int]:
    rows = list(result_rows.values())
    return {
        "trajectories": len(rows),
        "solves": sum(int(row["reward_binary"]) == 1 for row in rows),
        "mean_partial_reward": statistics.mean(
            float(row["reward_partial"]) for row in rows
        ),
        "total_tokens": sum(int(row["combined_total_tokens"]) for row in rows),
        "total_cost_usd": sum(float(row["combined_cost_usd"]) for row in rows),
    }


def paired_task_deltas(
    historical: list[dict[str, Any]],
    guided: list[dict[str, Any]],
    historical_results: dict[tuple[str, int], dict[str, Any]],
    guided_results: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    historical_by_key = {(row["task"], row["rep"]): row for row in historical}
    guided_by_key = {(row["task"], row["rep"]): row for row in guided}
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for key in sorted(historical_by_key):
        left = historical_by_key[key]
        right = guided_by_key[key]
        by_task[key[0]].append(
            {
                "token_delta": int(guided_results[key]["combined_total_tokens"])
                - int(historical_results[key]["combined_total_tokens"]),
                "token_ratio": int(guided_results[key]["combined_total_tokens"])
                / int(historical_results[key]["combined_total_tokens"]),
                "reward_delta": float(guided_results[key]["reward_partial"])
                - float(historical_results[key]["reward_partial"]),
                "call_delta": right["outer_calls"] - left["outer_calls"],
                "retrieval_before_mutation_delta": right[
                    "retrieval_calls_before_first_mutation"
                ]
                - left["retrieval_calls_before_first_mutation"],
                "search_to_read_delta": right["search_only_to_read_transitions"]
                - left["search_only_to_read_transitions"],
                "read_to_read_delta": right["read_to_read_transitions"]
                - left["read_to_read_transitions"],
                "repeated_path_delta": right["cross_call_repeated_path_reads"]
                - left["cross_call_repeated_path_reads"],
                "promise_all_delta": right["promise_all_calls"]
                - left["promise_all_calls"],
                "mutation_call_delta": right["mutation_calls"] - left["mutation_calls"],
                "mutation_operation_delta": right["mutation_operations"]
                - left["mutation_operations"],
                "repeated_mutation_path_delta": right[
                    "repeated_mutation_path_operations"
                ]
                - left["repeated_mutation_path_operations"],
                "calls_after_first_mutation_delta": right["calls_after_first_mutation"]
                - left["calls_after_first_mutation"],
            }
        )
    output = []
    for task, rows in by_task.items():
        output.append(
            {
                "task": task,
                **{key: statistics.mean(row[key] for row in rows) for key in rows[0]},
            }
        )
    return sorted(output, key=lambda row: row["token_delta"], reverse=True)


def pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = statistics.mean(left)
    right_mean = statistics.mean(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((x - left_mean) ** 2 for x in left)
        * sum((y - right_mean) ** 2 for y in right)
    )
    return numerator / denominator if denominator else None


def delta_correlations(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    token_deltas = [float(row["token_delta"]) for row in rows]
    return {
        key: pearson(token_deltas, [float(row[key]) for row in rows])
        for key in [
            "call_delta",
            "retrieval_before_mutation_delta",
            "search_to_read_delta",
            "read_to_read_delta",
            "repeated_path_delta",
            "promise_all_delta",
            "mutation_call_delta",
            "mutation_operation_delta",
            "repeated_mutation_path_delta",
            "calls_after_first_mutation_delta",
        ]
    }


def comparison_summary(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    left_results: dict[tuple[str, int], dict[str, Any]],
    right_results: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    task_deltas = paired_task_deltas(left, right, left_results, right_results)
    return {
        "task_delta_correlations": delta_correlations(task_deltas),
        "largest_token_regressions": task_deltas[:10],
        "largest_token_improvements": list(reversed(task_deltas[-10:])),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--subset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = set(args.subset.read_text().split())
    baseline_config = "baseline"
    historical_config = "pi-fabric"
    guided_config = "pi-fabric-native-read-guidance@1.0.0"
    baseline, baseline_results = load_config_trajectories(
        args.results_root, baseline_config, tasks, parse_native_session
    )
    historical, historical_results = load_config_trajectories(
        args.results_root, historical_config, tasks
    )
    guided, guided_results = load_config_trajectories(
        args.results_root, guided_config, tasks
    )
    summary = {
        "scope": {
            "tasks": len(tasks),
            "repetitions": 3,
            "trajectories_per_config": len(historical),
            "baseline_config": baseline_config,
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
            "historical_config": historical_config,
            "guided_config": guided_config,
        },
        "baseline": {
            **aggregate_metrics(baseline),
            "outcomes": aggregate_outcomes(baseline_results),
        },
        "historical": {
            **aggregate_metrics(historical),
            "outcomes": aggregate_outcomes(historical_results),
        },
        "guided": {
            **aggregate_metrics(guided),
            "outcomes": aggregate_outcomes(guided_results),
        },
        "comparisons": {
            "baseline_to_historical": comparison_summary(
                baseline, historical, baseline_results, historical_results
            ),
            "historical_to_guided": comparison_summary(
                historical, guided, historical_results, guided_results
            ),
        },
        "limitations": [
            "Fabric trace operations record references and arguments but not hidden nested-result sizes, so Stage 1 cannot measure raw-to-returned compression.",
            "The original baseline-versus-Fabric comparison uses matched trajectories from the same benchmark comparison and is not version-confounded.",
            "Historical Fabric is 0.25.6 and guided Fabric is 0.28.4 plus guidance; that later task-level delta is diagnostic, not a same-version causal estimate.",
            "Vanilla Pi can dispatch multiple native tools from one assistant message; the analysis groups those parallel tool calls into one outer turn for comparison with one fabric_exec call.",
            "The trace strips edit/write payload text, so Stage 1 can count mutation rounds and paths but cannot compare intermediate edit payload sizes.",
            "Mutation timing uses explicit pi.edit/pi.write operations; mutation performed inside pi.bash is a known blind spot.",
            "Verification classification uses command-family matching and may omit project-specific verification commands.",
        ],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output / "trajectory-metrics.json").write_text(
        json.dumps(
            {"baseline": baseline, "historical": historical, "guided": guided},
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
