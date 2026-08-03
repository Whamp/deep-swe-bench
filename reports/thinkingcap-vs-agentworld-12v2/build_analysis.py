#!/usr/bin/env python3
"""Build the paired ThinkingCap versus Qwen-AgentWorld analysis dataset."""

from __future__ import annotations

import collections
import json
import random
import re
import statistics
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = Path(__file__).resolve().parent
RESULTS_ROOT = Path("/home/will/evals/deep-swe-bench/results")
TASKS_ROOT = Path("/home/will/evals/deep-swe/tasks")

AGENTWORLD_RESULT_ROOT = (
    RESULTS_ROOT / "qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0"
)
THINKINGCAP_RESULT_ROOT = (
    RESULTS_ROOT / "thinkingcap-qwen3.6-27b-awq-int4/high/"
    "baseline-thinkingcap-qwen36@1.1.0"
)
AGENTWORLD_RUN_ROOT = (
    RESULTS_ROOT / "_runs/qwen-agentworld-35b-high-baseline-12v2-r3-w4--"
    "baf0b1a25d28c42ca27e320876e7946b8d4168eea03d9e952b23c56603c1ae40"
)
THINKINGCAP_RUN_ROOT = (
    RESULTS_ROOT / "_runs/thinkingcap-qwen36-high-baseline-12v2-r3-w2--"
    "f7e37b79a65eca1f42896fff9c5800cf968988791cbf9cd61845b48607bc9f5c"
)

TASK_ORDER = [
    "superjson-error-stack-serialization",
    "obsidian-linter-link-format-conversion",
    "participle-grammar-conflict-analysis",
    "dateutil-rfc5545-timezone-interop",
    "langchain-request-coalescing",
    "claude-code-by-agents-recursive-delegation",
    "go-critic-doc-link-checker",
    "mobly-grouped-test-barriers",
    "tengo-callable-instance-isolation",
    "adaptix-name-mapping-aliases",
    "goreleaser-retry-publish-auditing",
    "sql-formatter-bigquery-pipe-formatting",
]

PACKET_CLASSIFICATIONS: dict[tuple[str, int], dict[str, Any]] = {
    ("sql-formatter-bigquery-pipe-formatting", 1): {
        "winner": "ThinkingCap",
        "primary_bucket": "under-implementation",
        "secondary_bucket": "validation gap",
        "confidence": "high",
        "earliest_divergence": "implementation breadth",
        "mechanism": (
            "AgentWorld added the core pipe token and grammar path but omitted behavior needed "
            "for 14 of 26 feature tests, including aggregate/group-by, joins, subqueries, "
            "keyword case, bitwise OR, semicolons, and multi-step pipes. ThinkingCap changed "
            "the same core seam, added broader formatter/parser handling and task-focused tests, "
            "and passed all 26 feature tests plus all 5,709 preservation tests."
        ),
        "guidance_implication": (
            "For syntax features, enumerate every clause family and ambiguity from the request, "
            "then require focused tests for each family before the full regression suite."
        ),
    },
    ("langchain-request-coalescing", 0): {
        "winner": "AgentWorld",
        "primary_bucket": "resource exhaustion",
        "secondary_bucket": "validation gap",
        "confidence": "high",
        "earliest_divergence": "validation and termination",
        "mechanism": (
            "ThinkingCap spent the full 3,600-second agent budget, stopped during tool use, and "
            "never reached a validation command or completion audit. AgentWorld completed a "
            "similar three-file implementation and earned 43 of 50 feature tests, although it "
            "still missed backend result delivery, clear/cancellation, and batch semantics."
        ),
        "guidance_implication": (
            "Time-box concurrency design, run the supplied focused suite after the first vertical "
            "slice, and reserve time to test register/join/complete and waiter cancellation."
        ),
    },
    ("langchain-request-coalescing", 2): {
        "winner": "ThinkingCap",
        "primary_bucket": "resource exhaustion",
        "secondary_bucket": "validation gap",
        "confidence": "high",
        "earliest_divergence": "validation and termination",
        "mechanism": (
            "AgentWorld spent the full agent budget and stopped before completing or validating "
            "the wrapper integration. ThinkingCap finished, ran the focused coalescing tests, and "
            "earned 43 of 50 feature tests; its remaining failures centered on backend result/error "
            "delivery and event-stream behavior."
        ),
        "guidance_implication": (
            "Add an explicit halfway checkpoint: if no end-to-end coalesced call has passed by then, "
            "reduce scope to one complete sync/async path before adding batch and stream variants."
        ),
    },
    ("superjson-error-stack-serialization", 0): {
        "winner": "ThinkingCap",
        "primary_bucket": "cross-scope regression",
        "secondary_bucket": "under-implementation",
        "confidence": "high",
        "earliest_divergence": "serialization integration",
        "mechanism": (
            "AgentWorld's transformer integration regressed existing custom class, transformer, "
            "symbol, typed-array, and instance-isolation behavior while also missing stack/cause "
            "features. ThinkingCap preserved far more of the existing surface and implemented more "
            "feature cases, but still broke three cause-related preservation tests."
        ),
        "guidance_implication": (
            "Route new Error metadata through the existing transformation protocol and run the full "
            "custom-transformer/class regression suite after each schema change."
        ),
    },
    ("superjson-error-stack-serialization", 1): {
        "winner": "ThinkingCap",
        "primary_bucket": "protocol/interface drift",
        "secondary_bucket": "under-implementation",
        "confidence": "high",
        "earliest_divergence": "contract representation",
        "mechanism": (
            "AgentWorld failed exact annotation and mode contracts such as Error/stack, Error/frames, "
            "mode=off, instance isolation, and cause handling, producing 56 failed tests. ThinkingCap "
            "matched the observable schema and all preservation tests, with 11 feature edge cases left."
        ),
        "guidance_implication": (
            "Write the exact serialized annotation strings and mode semantics as invariants before "
            "implementation; reject an internal representation that cannot round-trip them exactly."
        ),
    },
    ("goreleaser-retry-publish-auditing", 2): {
        "winner": "AgentWorld",
        "primary_bucket": "wrong seam/layer",
        "secondary_bucket": "under-implementation",
        "confidence": "medium",
        "earliest_divergence": "seam selection",
        "mechanism": (
            "AgentWorld put attempt tracking in artifact/publish-oriented code and passed 9 of 29 "
            "feature tests. ThinkingCap built broader retry helpers across eight files but omitted "
            "the central artifact attempt-history path expected by many tests and passed 2 of 29. "
            "Neither implementation completed the retry-and-audit contract."
        ),
        "guidance_implication": (
            "Locate the single artifact metadata seam before adding transport-specific retries; one "
            "attempt record must cover upload, artifactory, and blob publishers consistently."
        ),
    },
    ("tengo-callable-instance-isolation", 0): {
        "winner": "ThinkingCap",
        "primary_bucket": "under-implementation",
        "secondary_bucket": "missing invariant/guard",
        "confidence": "high",
        "earliest_divergence": "runtime-context model",
        "mechanism": (
            "AgentWorld made CompiledFunction callable but did not preserve closure state, returned "
            "callables, recursive/imported functions, global mutation, or compiled-instance isolation; "
            "it passed 2 of 23 feature tests. ThinkingCap wired more runtime and compiled-instance "
            "state and passed 18 of 23, missing five nested clone/rebind/error-frame cases."
        ),
        "guidance_implication": (
            "Model ownership of globals, constants, closures, and returned callables explicitly, then "
            "test cloning and rebinding across two compiled instances before broad VM changes."
        ),
    },
}


def read_json(path: Path) -> Any:
    """Read one UTF-8 JSON artifact."""
    return json.loads(path.read_text())


def percentile(values: list[float | int], probability: float) -> float:
    """Calculate an interpolated percentile without external dependencies."""
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def load_task_metadata() -> dict[str, dict[str, Any]]:
    """Load task titles and languages; difficulty is absent from the task contract."""
    metadata: dict[str, dict[str, Any]] = {}
    for task in TASK_ORDER:
        task_document = tomllib.loads((TASKS_ROOT / task / "task.toml").read_text())
        values = task_document["metadata"]
        metadata[task] = {
            "task": task,
            "title": values["display_title"],
            "description": values["display_description"],
            "language": values["language"].title(),
            "category": values["category"],
            "difficulty": None,
        }
    return metadata


def load_result_cells(result_root: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Load exactly one result for each task and rep in the 12_v2 comparison."""
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    for result_path in result_root.glob("*/rep*/result.json"):
        result = read_json(result_path)
        key = (result["task"], int(result["rep"]))
        if key in cells:
            raise ValueError(f"Duplicate benchmark result: {key}")
        result["artifact_root"] = str(result_path.parent)
        cells[key] = result
    expected = {(task, rep) for task in TASK_ORDER for rep in range(3)}
    if cells.keys() != expected:
        missing = sorted(expected - cells.keys())
        extra = sorted(cells.keys() - expected)
        raise ValueError(f"Result pairing mismatch: missing={missing}, extra={extra}")
    return cells


def summarize_result_cells(
    cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Calculate intention-to-treat, valid-only, test, usage, and patch metrics."""
    rows = list(cells.values())
    valid = [row for row in rows if row["reward_binary"] >= 0]
    f2p_passed = sum(row["f2p_passed"] for row in valid)
    f2p_total = sum(row["f2p_total"] for row in valid)
    p2p_passed = sum(row["p2p_passed"] for row in valid)
    p2p_total = sum(row["p2p_total"] for row in valid)
    largest_patch = max(rows, key=lambda row: row["patch_bytes"])
    return {
        "cells": len(rows),
        "valid": len(valid),
        "invalid": len(rows) - len(valid),
        "solves": sum(row["reward_binary"] == 1 for row in rows),
        "solve_rate_all": sum(row["reward_binary"] == 1 for row in rows) / len(rows),
        "solve_rate_valid": sum(row["reward_binary"] == 1 for row in valid)
        / len(valid),
        "mean_partial_all": statistics.mean(row["reward_partial"] for row in rows),
        "median_partial_all": statistics.median(row["reward_partial"] for row in rows),
        "mean_partial_valid": statistics.mean(row["reward_partial"] for row in valid),
        "f2p_passed": f2p_passed,
        "f2p_total": f2p_total,
        "f2p_micro": f2p_passed / f2p_total,
        "p2p_passed": p2p_passed,
        "p2p_total": p2p_total,
        "p2p_micro": p2p_passed / p2p_total,
        "input_tokens": sum(row["input_tokens"] for row in rows),
        "output_tokens": sum(row["output_tokens"] for row in rows),
        "total_tokens": sum(row["total_tokens"] for row in rows),
        "median_total_tokens": statistics.median(row["total_tokens"] for row in rows),
        "p90_total_tokens": percentile([row["total_tokens"] for row in rows], 0.9),
        "median_output_tokens": statistics.median(row["output_tokens"] for row in rows),
        "p90_output_tokens": percentile([row["output_tokens"] for row in rows], 0.9),
        "wall_sum_s": sum(row["agent_wall_s"] for row in rows),
        "wall_median_s": statistics.median(row["agent_wall_s"] for row in rows),
        "wall_p90_s": percentile([row["agent_wall_s"] for row in rows], 0.9),
        "turns": sum(row["turns"] for row in rows),
        "median_turns": statistics.median(row["turns"] for row in rows),
        "tool_calls": sum(row["tool_calls"] for row in rows),
        "median_tool_calls": statistics.median(row["tool_calls"] for row in rows),
        "patch_bytes": sum(row["patch_bytes"] for row in rows),
        "median_patch_bytes": statistics.median(row["patch_bytes"] for row in rows),
        "p90_patch_bytes": percentile([row["patch_bytes"] for row in rows], 0.9),
        "largest_patch": {
            "task": largest_patch["task"],
            "rep": largest_patch["rep"],
            "bytes": largest_patch["patch_bytes"],
        },
        "empty_patches": sum(row["patch_bytes"] == 0 for row in rows),
        "agent_timeouts": sum(row["agent_exit"] == "timeout" for row in rows),
        "verifier_timeouts": sum(row["verifier_exit"] == "timeout" for row in rows),
    }


def summarize_groups(
    cells: dict[tuple[str, int], dict[str, Any]],
    task_metadata: dict[str, dict[str, Any]],
    group_name: str,
) -> list[dict[str, Any]]:
    """Calculate task-level or language-level aggregate metrics."""
    grouped: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for (task, _rep), result in cells.items():
        key = task if group_name == "task" else task_metadata[task]["language"]
        grouped[key].append(result)
    summaries = []
    for key, rows in grouped.items():
        valid = [row for row in rows if row["reward_binary"] >= 0]
        f2p_passed = sum(row["f2p_passed"] for row in valid)
        f2p_total = sum(row["f2p_total"] for row in valid)
        p2p_passed = sum(row["p2p_passed"] for row in valid)
        p2p_total = sum(row["p2p_total"] for row in valid)
        summary = {
            group_name: key,
            "cells": len(rows),
            "valid": len(valid),
            "invalid": len(rows) - len(valid),
            "solves": sum(row["reward_binary"] == 1 for row in rows),
            "mean_partial": statistics.mean(row["reward_partial"] for row in rows),
            "median_partial": statistics.median(row["reward_partial"] for row in rows),
            "f2p_micro": f2p_passed / f2p_total if f2p_total else None,
            "p2p_micro": p2p_passed / p2p_total if p2p_total else None,
            "median_tokens": statistics.median(row["total_tokens"] for row in rows),
            "median_wall_s": statistics.median(row["agent_wall_s"] for row in rows),
            "wall_sum_s": sum(row["agent_wall_s"] for row in rows),
        }
        if group_name == "task":
            summary.update(task_metadata[key])
        summaries.append(summary)
    return sorted(summaries, key=lambda row: row[group_name])


def scan_session_delivery(result_root: Path) -> dict[str, Any]:
    """Audit saved session messages for thinking, tool, and stop behavior."""
    counts: collections.Counter[str] = collections.Counter()
    signatures: collections.Counter[str] = collections.Counter()
    tool_names: collections.Counter[str] = collections.Counter()
    malformed: list[dict[str, Any]] = []
    raw_tool_call_leaks: list[dict[str, Any]] = []
    max_prompt = {"tokens": 0, "cell": None}
    max_completion = {"tokens": 0, "cell": None}
    length_stop_cells: set[str] = set()
    for session_path in result_root.glob("*/rep*/session/*.jsonl"):
        cell = "/".join(session_path.parts[-4:-1])
        for line_number, line in enumerate(
            session_path.read_text(errors="replace").splitlines(), 1
        ):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                counts["bad_json_lines"] += 1
                continue
            if record.get("type") != "message":
                continue
            message = record.get("message", {})
            role = message.get("role")
            if role == "toolResult":
                counts["tool_results"] += 1
                if message.get("isError"):
                    counts["tool_result_errors"] += 1
                continue
            if role != "assistant":
                continue
            counts["assistant_messages"] += 1
            stop_reason = str(message.get("stopReason"))
            raw_stop_reason = str(message.get("rawStopReason"))
            counts[f"stop_reason:{stop_reason}"] += 1
            counts[f"raw_stop_reason:{raw_stop_reason}"] += 1
            if stop_reason == "length" or raw_stop_reason == "length":
                length_stop_cells.add(cell)
            usage = message.get("usage") or {}
            prompt_tokens = usage.get("input") or 0
            completion_tokens = usage.get("output") or 0
            if prompt_tokens > max_prompt["tokens"]:
                max_prompt = {"tokens": prompt_tokens, "cell": cell}
            if completion_tokens > max_completion["tokens"]:
                max_completion = {"tokens": completion_tokens, "cell": cell}
            for block in message.get("content") or []:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                counts[f"block:{block_type}"] += 1
                if block_type == "thinking":
                    signatures[str(block.get("thinkingSignature"))] += 1
                elif block_type == "toolCall":
                    tool_name = block.get("name")
                    arguments = block.get("arguments")
                    tool_names[str(tool_name)] += 1
                    if (
                        not isinstance(tool_name, str)
                        or not tool_name
                        or not isinstance(arguments, dict)
                    ):
                        malformed.append(
                            {
                                "cell": cell,
                                "line": line_number,
                                "tool_name": tool_name,
                                "arguments_type": type(arguments).__name__,
                            }
                        )
                elif block_type == "text" and re.search(
                    r"<tool_call>|<function=", str(block.get("text", "")), re.IGNORECASE
                ):
                    raw_tool_call_leaks.append({"cell": cell, "line": line_number})
    return {
        "assistant_messages": counts["assistant_messages"],
        "thinking_blocks": counts["block:thinking"],
        "thinking_signatures": dict(signatures),
        "tool_call_blocks": counts["block:toolCall"],
        "tool_results": counts["tool_results"],
        "tool_result_errors": counts["tool_result_errors"],
        "text_blocks": counts["block:text"],
        "stop_reasons": {
            key.removeprefix("stop_reason:"): value
            for key, value in counts.items()
            if key.startswith("stop_reason:")
        },
        "raw_stop_reasons": {
            key.removeprefix("raw_stop_reason:"): value
            for key, value in counts.items()
            if key.startswith("raw_stop_reason:")
        },
        "tool_names": dict(tool_names),
        "malformed_tool_calls": malformed,
        "raw_tool_call_leaks": raw_tool_call_leaks,
        "bad_json_lines": counts["bad_json_lines"],
        "max_single_prompt": max_prompt,
        "max_single_completion": max_completion,
        "length_stop_cells": sorted(length_stop_cells),
    }


def scan_provider_delivery(
    result_root: Path,
    expected_model: str,
    expected_max_tokens: int,
    expected_temperature: float,
) -> dict[str, Any]:
    """Verify every saved provider request against its config contract."""
    failures = []
    request_paths = sorted(
        result_root.glob("*/rep*/initial_context/provider_request_*.json")
    )
    expected = {
        "model": expected_model,
        "max_tokens": expected_max_tokens,
        "temperature": expected_temperature,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "repetition_penalty": 1.0,
    }
    for request_path in request_paths:
        payload = read_json(request_path)
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                failures.append(
                    {
                        "path": str(request_path),
                        "field": key,
                        "actual": payload.get(key),
                        "expected": expected_value,
                    }
                )
        kwargs = payload.get("chat_template_kwargs", {})
        if kwargs.get("enable_thinking") is not True:
            failures.append({"path": str(request_path), "field": "enable_thinking"})
        if kwargs.get("preserve_thinking") is not True:
            failures.append({"path": str(request_path), "field": "preserve_thinking"})
        if "thinking_token_budget" in kwargs or "thinking_token_budget" in payload:
            failures.append(
                {"path": str(request_path), "field": "thinking_token_budget"}
            )
    return {
        "captured_requests": len(request_paths),
        "failures": failures,
        "expected": expected,
        "enable_thinking": True,
        "preserve_thinking": True,
        "thinking_token_budget": None,
    }


def summarize_run(run_root: Path) -> dict[str, Any]:
    """Summarize terminal run state and outcome accounting."""
    status = read_json(run_root / "status.json")
    manifest = read_json(run_root / "manifest.json")
    outcomes: collections.Counter[str] = collections.Counter(
        cell["outcome"]
        for cell in status["cells"].values()
        if cell.get("kind") == "batch"
    )
    started = datetime.fromisoformat(status["started_at"])
    completed = datetime.fromisoformat(status["completed_at"])
    return {
        "run_id": manifest["run_id"],
        "run_key": manifest["run_key"],
        "launch_plan_identity": manifest["launch_plan_identity"],
        "state": status["state"],
        "stage": status["stage"],
        "started_at": status["started_at"],
        "completed_at": status["completed_at"],
        "elapsed_s": (completed - started).total_seconds(),
        "workers": manifest["workers"],
        "agent_timeout_s": manifest["agent_timeout_s"],
        "subject": f"{manifest['agent']}@0.83.0",
        "model": manifest["model"],
        "thinking": manifest["thinking"],
        "subset": manifest["selection"]["name"],
        "reps": manifest["runs"],
        "outcomes": dict(outcomes),
    }


def paired_bootstrap_interval(
    agentworld: dict[tuple[str, int], dict[str, Any]],
    thinkingcap: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Bootstrap paired partial-reward delta by task to retain rep clustering."""
    generator = random.Random(20260803)
    values = []
    for _ in range(20_000):
        sampled_tasks = [generator.choice(TASK_ORDER) for _ in TASK_ORDER]
        values.append(
            statistics.mean(
                thinkingcap[(task, rep)]["reward_partial"]
                - agentworld[(task, rep)]["reward_partial"]
                for task in sampled_tasks
                for rep in range(3)
            )
        )
    values.sort()
    return {
        "method": "task-clustered paired bootstrap",
        "seed": 20260803,
        "samples": len(values),
        "lower_95": values[499],
        "upper_95": values[19_499],
    }


def build_pair_rows(
    agentworld: dict[tuple[str, int], dict[str, Any]],
    thinkingcap: dict[tuple[str, int], dict[str, Any]],
    task_metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build one comparison record per matched task and rep."""
    pairs = []
    for task in TASK_ORDER:
        for rep in range(3):
            left = agentworld[(task, rep)]
            right = thinkingcap[(task, rep)]
            pairs.append(
                {
                    **task_metadata[task],
                    "rep": rep,
                    "agentworld": compact_result(left),
                    "thinkingcap": compact_result(right),
                    "delta_thinkingcap_minus_agentworld": (
                        right["reward_partial"] - left["reward_partial"]
                    ),
                }
            )
    return pairs


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    """Select the result fields required by the report and packets."""
    fields = [
        "reward_binary",
        "reward_partial",
        "f2p",
        "f2p_passed",
        "f2p_total",
        "p2p",
        "p2p_passed",
        "p2p_total",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_exit",
        "agent_timed_out",
        "verifier_exit",
        "artifact_root",
    ]
    return {field: result.get(field) for field in fields}


def build_paired_summary(pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate net, churn, timeout, and paired-efficiency views."""
    both_valid = [
        row
        for row in pair_rows
        if row["agentworld"]["reward_binary"] >= 0
        and row["thinkingcap"]["reward_binary"] >= 0
    ]
    deltas = [row["delta_thinkingcap_minus_agentworld"] for row in pair_rows]
    both_valid_deltas = [
        row["delta_thinkingcap_minus_agentworld"] for row in both_valid
    ]
    task_deltas = {
        task: statistics.mean(
            row["delta_thinkingcap_minus_agentworld"]
            for row in pair_rows
            if row["task"] == task
        )
        for task in TASK_ORDER
    }
    return {
        "pairs": len(pair_rows),
        "both_solved": sum(
            row["agentworld"]["reward_binary"] == 1
            and row["thinkingcap"]["reward_binary"] == 1
            for row in pair_rows
        ),
        "agentworld_only_solves": sum(
            row["agentworld"]["reward_binary"] == 1
            and row["thinkingcap"]["reward_binary"] != 1
            for row in pair_rows
        ),
        "thinkingcap_only_solves": sum(
            row["thinkingcap"]["reward_binary"] == 1
            and row["agentworld"]["reward_binary"] != 1
            for row in pair_rows
        ),
        "mean_partial_delta": statistics.mean(deltas),
        "median_partial_delta": statistics.median(deltas),
        "thinkingcap_partial_wins": sum(delta > 0 for delta in deltas),
        "agentworld_partial_wins": sum(delta < 0 for delta in deltas),
        "exact_partial_ties": sum(delta == 0 for delta in deltas),
        "thinkingcap_material_wins_gt_005": sum(delta > 0.05 for delta in deltas),
        "agentworld_material_wins_gt_005": sum(delta < -0.05 for delta in deltas),
        "ties_within_005": sum(abs(delta) <= 0.05 for delta in deltas),
        "agentworld_only_invalid": sum(
            row["agentworld"]["reward_binary"] < 0
            and row["thinkingcap"]["reward_binary"] >= 0
            for row in pair_rows
        ),
        "thinkingcap_only_invalid": sum(
            row["thinkingcap"]["reward_binary"] < 0
            and row["agentworld"]["reward_binary"] >= 0
            for row in pair_rows
        ),
        "both_invalid": sum(
            row["agentworld"]["reward_binary"] < 0
            and row["thinkingcap"]["reward_binary"] < 0
            for row in pair_rows
        ),
        "both_valid_pairs": len(both_valid),
        "both_valid_mean_partial_delta": statistics.mean(both_valid_deltas),
        "both_valid_median_partial_delta": statistics.median(both_valid_deltas),
        "both_valid_thinkingcap_wins": sum(delta > 0 for delta in both_valid_deltas),
        "both_valid_agentworld_wins": sum(delta < 0 for delta in both_valid_deltas),
        "both_valid_ties": sum(delta == 0 for delta in both_valid_deltas),
        "thinkingcap_task_wins": sum(delta > 0 for delta in task_deltas.values()),
        "agentworld_task_wins": sum(delta < 0 for delta in task_deltas.values()),
        "task_ties": sum(delta == 0 for delta in task_deltas.values()),
        "task_deltas": task_deltas,
    }


def parse_patch_stats(cell_root: Path) -> dict[str, Any]:
    """Extract changed files and line counts from one saved model patch."""
    patch_path = cell_root / "artifacts/model.patch"
    patch = patch_path.read_text(errors="replace")
    files = re.findall(r"^diff --git a/(.*?) b/", patch, re.MULTILINE)
    additions = sum(
        line.startswith("+") and not line.startswith("+++")
        for line in patch.splitlines()
    )
    deletions = sum(
        line.startswith("-") and not line.startswith("---")
        for line in patch.splitlines()
    )
    return {
        "path": str(patch_path),
        "bytes": len(patch.encode()),
        "files": files,
        "files_count": len(files),
        "additions": additions,
        "deletions": deletions,
        "changed_lines": additions + deletions,
    }


def parse_verifier_failures(cell_root: Path) -> dict[str, Any]:
    """Extract structured failing test names from CTRF when grading completed."""
    ctrf_path = cell_root / "verifier/ctrf.json"
    if not ctrf_path.exists():
        return {"ctrf_path": None, "summary": None, "failed_tests": []}
    ctrf = read_json(ctrf_path)
    tests = ctrf["results"]["tests"]
    return {
        "ctrf_path": str(ctrf_path),
        "summary": ctrf["results"]["summary"],
        "failed_tests": [
            test["name"] for test in tests if test.get("status") == "failed"
        ],
    }


def parse_session_trace(cell_root: Path) -> dict[str, Any]:
    """Extract the tool mix, validation commands, and final summary from a session."""
    tool_counts: collections.Counter[str] = collections.Counter()
    validation_commands: list[str] = []
    final_text = ""
    validation_pattern = re.compile(
        r"(?:go test|pytest|npm test|npm run|yarn test|pnpm test|npx tsc|"
        r"uv run|cargo test|make test)",
        re.IGNORECASE,
    )
    session_paths = sorted(cell_root.glob("session/*.jsonl"))
    for session_path in session_paths:
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "message":
                continue
            message = record.get("message", {})
            if message.get("role") != "assistant":
                continue
            for block in message.get("content") or []:
                if block.get("type") == "toolCall":
                    tool_name = str(block.get("name"))
                    tool_counts[tool_name] += 1
                    if tool_name == "bash":
                        command = str((block.get("arguments") or {}).get("command", ""))
                        if validation_pattern.search(command):
                            validation_commands.append(command)
                elif block.get("type") == "text":
                    final_text = str(block.get("text", ""))
    return {
        "session_paths": [str(path) for path in session_paths],
        "tool_counts": dict(tool_counts),
        "validation_commands": validation_commands,
        "final_text": final_text,
    }


def build_packet_side(result: dict[str, Any]) -> dict[str, Any]:
    """Build one model side of a trajectory packet."""
    cell_root = Path(result["artifact_root"])
    return {
        "result": compact_result(result),
        "patch": parse_patch_stats(cell_root),
        "trace": parse_session_trace(cell_root),
        "verifier": parse_verifier_failures(cell_root),
    }


def packet_trigger_reason(pair: dict[str, Any]) -> list[str]:
    """Apply the predeclared trajectory packet selection rule."""
    reasons = []
    left = pair["agentworld"]
    right = pair["thinkingcap"]
    if (left["reward_binary"] == 1) != (right["reward_binary"] == 1):
        reasons.append("strict solve flip")
    if (left["reward_binary"] < 0) != (right["reward_binary"] < 0):
        reasons.append("invalid-outcome discordance")
    if abs(pair["delta_thinkingcap_minus_agentworld"]) > 0.10:
        reasons.append("absolute partial-reward delta above 0.10")
    return reasons


def build_trajectory_packets(
    pair_rows: list[dict[str, Any]],
    agentworld_cells: dict[tuple[str, int], dict[str, Any]],
    thinkingcap_cells: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build self-contained evidence packets for every triggered pair."""
    packets = []
    for pair in pair_rows:
        reasons = packet_trigger_reason(pair)
        if not reasons:
            continue
        key = (pair["task"], pair["rep"])
        classification = PACKET_CLASSIFICATIONS.get(key)
        if classification is None:
            raise ValueError(f"Missing packet classification for {key}")
        packets.append(
            {
                "pair": {
                    "task": pair["task"],
                    "rep": pair["rep"],
                    "title": pair["title"],
                    "description": pair["description"],
                    "language": pair["language"],
                    "category": pair["category"],
                    "difficulty": pair["difficulty"],
                    "difficulty_note": "Difficulty is not recorded in task.toml.",
                    "left": "AgentWorld",
                    "right": "ThinkingCap",
                },
                "selection_reasons": reasons,
                "agentworld": build_packet_side(agentworld_cells[key]),
                "thinkingcap": build_packet_side(thinkingcap_cells[key]),
                "classification": classification,
            }
        )
    return packets


def render_packet_markdown(packet: dict[str, Any]) -> str:
    """Render one evidence packet as reviewable Markdown."""
    pair = packet["pair"]
    left = packet["agentworld"]
    right = packet["thinkingcap"]
    classification = packet["classification"]

    def side_table_row(label: str, side: dict[str, Any]) -> str:
        result = side["result"]
        return (
            f"| {label} | {result['reward_binary']} | {result['reward_partial']:.3f} | "
            f"{result['f2p_passed']}/{result['f2p_total']} | "
            f"{result['p2p_passed']}/{result['p2p_total']} | "
            f"{result['total_tokens']:,} | {result['agent_wall_s']:.1f}s | "
            f"{result['turns']} | {result['tool_calls']} | {result['patch_bytes']:,} |"
        )

    def failure_list(side: dict[str, Any]) -> str:
        failures = side["verifier"]["failed_tests"]
        if not failures:
            return "- No structured failures were recorded."
        return "\n".join(f"- `{failure}`" for failure in failures)

    return f"""# {pair["title"]} · rep {pair["rep"]}

- Task: `{pair["task"]}`
- Language: {pair["language"]}
- Category: {pair["category"]}
- Difficulty: not recorded in `task.toml`
- Packet trigger: {", ".join(packet["selection_reasons"])}

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{side_table_row("AgentWorld", left)}
{side_table_row("ThinkingCap", right)}

## Patch scope

**AgentWorld:** {left["patch"]["files_count"]} files, +{left["patch"]["additions"]}/-{left["patch"]["deletions"]} lines.

{", ".join(f"`{path}`" for path in left["patch"]["files"])}

**ThinkingCap:** {right["patch"]["files_count"]} files, +{right["patch"]["additions"]}/-{right["patch"]["deletions"]} lines.

{", ".join(f"`{path}`" for path in right["patch"]["files"])}

## Validation commands

**AgentWorld**

{chr(10).join(f"- `{command}`" for command in left["trace"]["validation_commands"]) or "- None detected."}

**ThinkingCap**

{chr(10).join(f"- `{command}`" for command in right["trace"]["validation_commands"]) or "- None detected."}

## Verifier failures

### AgentWorld

{failure_list(left)}

### ThinkingCap

{failure_list(right)}

## Classification

- Winner: **{classification["winner"]}**
- Primary bucket: **{classification["primary_bucket"]}**
- Secondary bucket: {classification["secondary_bucket"]}
- Earliest divergence: {classification["earliest_divergence"]}
- Confidence: {classification["confidence"]}

{classification["mechanism"]}

**Process hypothesis:** {classification["guidance_implication"]}

## Artifact roots

- AgentWorld: `{left["result"]["artifact_root"]}`
- ThinkingCap: `{right["result"]["artifact_root"]}`
"""


def write_packets(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Write JSON and Markdown packet files and return report links."""
    packet_root = REPORT_ROOT / "packets"
    packet_root.mkdir(parents=True, exist_ok=True)
    index = []
    for packet in packets:
        task = packet["pair"]["task"]
        rep = packet["pair"]["rep"]
        stem = f"{task}__rep{rep}"
        json_path = packet_root / f"{stem}.json"
        markdown_path = packet_root / f"{stem}.md"
        json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
        markdown_path.write_text(render_packet_markdown(packet))
        index.append(
            {
                "task": task,
                "rep": rep,
                "json": f"packets/{json_path.name}",
                "markdown": f"packets/{markdown_path.name}",
                "selection_reasons": packet["selection_reasons"],
                "classification": packet["classification"],
            }
        )
    return index


def build_analysis() -> dict[str, Any]:
    """Build the complete paired comparison dataset from canonical artifacts."""
    task_metadata = load_task_metadata()
    agentworld_cells = load_result_cells(AGENTWORLD_RESULT_ROOT)
    thinkingcap_cells = load_result_cells(THINKINGCAP_RESULT_ROOT)
    pair_rows = build_pair_rows(agentworld_cells, thinkingcap_cells, task_metadata)
    packets = build_trajectory_packets(pair_rows, agentworld_cells, thinkingcap_cells)
    packet_index = write_packets(packets)
    agentworld = summarize_result_cells(agentworld_cells)
    thinkingcap = summarize_result_cells(thinkingcap_cells)
    if agentworld["f2p_total"] != thinkingcap["f2p_total"]:
        raise ValueError("Feature-test denominators differ across valid outcomes")
    if agentworld["p2p_total"] != thinkingcap["p2p_total"]:
        raise ValueError("Preservation-test denominators differ across valid outcomes")
    return {
        "comparison": {
            "name": "ThinkingCap Qwen3.6 27B versus Qwen-AgentWorld 35B-A3B",
            "subset": "12_v2",
            "reps": 3,
            "pairs": 36,
            "subject": "pi@0.83.0",
            "thinking": "high",
            "delta_direction": "ThinkingCap minus AgentWorld",
            "comparison_class": "paired model/config-bundle comparison",
            "causal_limit": (
                "The models, checkpoints, endpoints, sampling temperatures, output ceilings, "
                "and worker counts differ. The output ceilings were not reached."
            ),
            "packet_selection_rule": (
                "Select every strict solve flip, invalid-outcome discordance, or pair with "
                "absolute partial-reward delta above 0.10."
            ),
        },
        "configs": {
            "agentworld": {
                "label": "Qwen-AgentWorld 35B-A3B",
                "config": "baseline-qwen-agentworld-35b@1.0.0",
                "model": "local-vllm/qwen-agentworld-35b-a3b",
                "architecture": "Qwen3_5MoeForConditionalGeneration",
                "checkpoint": "Qwen/Qwen-AgentWorld-35B-A3B",
                "quantization": "AWQ INT4 via compressed-tensors",
                "endpoint": "http://100.92.238.117:8080/v1",
                "context_window": 262_144,
                "max_tokens": 65_536,
                "temperature": 0.6,
                "workers": 4,
                "prompt_text": "stock Pi; no config-authored prompt text",
            },
            "thinkingcap": {
                "label": "ThinkingCap Qwen3.6 27B",
                "config": "baseline-thinkingcap-qwen36@1.1.0",
                "model": "local-vllm/thinkingcap-qwen3.6-27b-awq-int4",
                "architecture": "Qwen3_5ForConditionalGeneration",
                "checkpoint": "bottlecapai/ThinkingCap-Qwen3.6-27B",
                "base_model": "Qwen/Qwen3.6-27B",
                "quantization": "AWQ INT4 via compressed-tensors",
                "endpoint": "http://100.92.238.117:8081/v1",
                "context_window": 262_144,
                "max_tokens": 98_304,
                "temperature": 1.0,
                "workers": 2,
                "prompt_text": "stock Pi; no config-authored prompt text",
            },
            "shared_runtime": {
                "host": "server60",
                "vllm": "0.25.1",
                "image_identity": "sha256:e4f88a835143cd22aee2397a26ec6bb80b3a4a6fe0c882bcbc63822904766089",
                "tensor_parallel_size": 2,
                "max_model_len": 262_144,
                "max_num_seqs": 4,
                "max_num_batched_tokens": 8_192,
                "kv_cache_dtype": "fp8",
                "reasoning_parser": "qwen3",
                "tool_call_parser": "qwen3_coder",
                "thinking": "high",
                "preserve_thinking": True,
                "thinking_token_budget": None,
                "sampling_shared": {
                    "top_p": 0.95,
                    "top_k": 20,
                    "min_p": 0.0,
                    "repetition_penalty": 1.0,
                },
            },
        },
        "runs": {
            "agentworld": summarize_run(AGENTWORLD_RUN_ROOT),
            "thinkingcap": summarize_run(THINKINGCAP_RUN_ROOT),
        },
        "aggregate": {
            "agentworld": agentworld,
            "thinkingcap": thinkingcap,
        },
        "paired": {
            **build_paired_summary(pair_rows),
            "bootstrap_95": paired_bootstrap_interval(
                agentworld_cells, thinkingcap_cells
            ),
        },
        "delivery": {
            "agentworld": {
                "session": scan_session_delivery(AGENTWORLD_RESULT_ROOT),
                "provider": scan_provider_delivery(
                    AGENTWORLD_RESULT_ROOT,
                    "qwen-agentworld-35b-a3b",
                    65_536,
                    0.6,
                ),
            },
            "thinkingcap": {
                "session": scan_session_delivery(THINKINGCAP_RESULT_ROOT),
                "provider": scan_provider_delivery(
                    THINKINGCAP_RESULT_ROOT,
                    "thinkingcap-qwen3.6-27b-awq-int4",
                    98_304,
                    1.0,
                ),
            },
        },
        "tasks": {
            "metadata": task_metadata,
            "agentworld": summarize_groups(agentworld_cells, task_metadata, "task"),
            "thinkingcap": summarize_groups(thinkingcap_cells, task_metadata, "task"),
        },
        "languages": {
            "agentworld": summarize_groups(agentworld_cells, task_metadata, "language"),
            "thinkingcap": summarize_groups(
                thinkingcap_cells, task_metadata, "language"
            ),
        },
        "pairs": pair_rows,
        "packet_index": packet_index,
    }


def validate_analysis(analysis: dict[str, Any]) -> None:
    """Fail closed when core comparison or delivery invariants do not hold."""
    if analysis["comparison"]["pairs"] != 36:
        raise ValueError("Comparison must contain 36 matched pairs")
    for model in ("agentworld", "thinkingcap"):
        aggregate = analysis["aggregate"][model]
        delivery = analysis["delivery"][model]
        run = analysis["runs"][model]
        if aggregate["cells"] != 36:
            raise ValueError(f"{model}: expected 36 results")
        if run["state"] != "completed" or run["stage"] != "done":
            raise ValueError(f"{model}: run is not terminal")
        if delivery["provider"]["captured_requests"] != 72:
            raise ValueError(f"{model}: expected 72 captured requests")
        if delivery["provider"]["failures"]:
            raise ValueError(f"{model}: provider delivery mismatch")
        session = delivery["session"]
        if session["malformed_tool_calls"] or session["raw_tool_call_leaks"]:
            raise ValueError(f"{model}: malformed or leaked tool calls")
        if session["length_stop_cells"]:
            raise ValueError(f"{model}: unexpected output-length stop")
        if session["thinking_blocks"] != session["assistant_messages"]:
            raise ValueError(f"{model}: missing thinking block")
    if len(analysis["packet_index"]) != 7:
        raise ValueError("Expected seven predeclared trajectory packets")


def main() -> None:
    """Write the analysis dataset and trajectory packets."""
    analysis = build_analysis()
    validate_analysis(analysis)
    output_path = REPORT_ROOT / "analysis.json"
    output_path.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(output_path)


if __name__ == "__main__":
    main()
