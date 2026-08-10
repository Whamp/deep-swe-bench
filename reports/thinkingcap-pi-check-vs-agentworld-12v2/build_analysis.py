#!/usr/bin/env python3
"""Build the four-way ThinkingCap and AgentWorld pi-check comparison dataset."""

from __future__ import annotations

import collections
import itertools
import json
import random
import re
import statistics
import tomllib
from pathlib import Path
from typing import Any

REPORT_ROOT = Path(__file__).resolve().parent
RESULTS_ROOT = Path("/home/will/evals/deep-swe-bench/results")
TASKS_ROOT = Path("/home/will/evals/deep-swe/tasks")

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

CONFIG_SPECS: dict[str, dict[str, Any]] = {
    "thinkingcap_baseline": {
        "label": "ThinkingCap baseline",
        "short_label": "TC base",
        "role": "same-model config control",
        "result_root": RESULTS_ROOT
        / "thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0",
        "config": "baseline-thinkingcap-qwen36@1.1.0",
        "model": "local-vllm/thinkingcap-qwen3.6-27b-awq-int4",
        "request_model": "thinkingcap-qwen3.6-27b-awq-int4",
        "checkpoint": "ThinkingCap Qwen3.6 27B AWQ INT4",
        "endpoint": "server60:8081",
        "temperature": 1.0,
        "max_tokens": 98_304,
        "workers": 2,
        "treatment": False,
        "trace_file": None,
    },
    "thinkingcap_pi_check": {
        "label": "ThinkingCap pi-check + timeout",
        "short_label": "TC check",
        "role": "local subject",
        "result_root": RESULTS_ROOT
        / "thinkingcap-qwen3.6-27b-awq-int4/high/pi-check@1.4.0",
        "config": "pi-check@1.4.0",
        "model": "local-vllm/thinkingcap-qwen3.6-27b-awq-int4",
        "request_model": "thinkingcap-qwen3.6-27b-awq-int4",
        "checkpoint": "ThinkingCap Qwen3.6 27B AWQ INT4",
        "endpoint": "server60:8081",
        "temperature": 1.0,
        "max_tokens": 98_304,
        "workers": 2,
        "treatment": True,
        "trace_file": "thinkingcap-bash-timeout.ndjson",
    },
    "agentworld_baseline": {
        "label": "AgentWorld baseline",
        "short_label": "AW base",
        "role": "local contrast",
        "result_root": RESULTS_ROOT
        / "qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0",
        "config": "baseline-qwen-agentworld-35b@1.0.0",
        "model": "local-vllm/qwen-agentworld-35b-a3b",
        "request_model": "qwen-agentworld-35b-a3b",
        "checkpoint": "Qwen-AgentWorld 35B-A3B AWQ INT4",
        "endpoint": "server60:8080",
        "temperature": 0.6,
        "max_tokens": 65_536,
        "workers": 4,
        "treatment": False,
        "trace_file": None,
    },
    "agentworld_pi_check": {
        "label": "AgentWorld pi-check + timeout",
        "short_label": "AW check",
        "role": "local contrast",
        "result_root": RESULTS_ROOT / "qwen-agentworld-35b-a3b/high/pi-check@1.3.0",
        "config": "pi-check@1.3.0",
        "model": "local-vllm/qwen-agentworld-35b-a3b",
        "request_model": "qwen-agentworld-35b-a3b",
        "checkpoint": "Qwen-AgentWorld 35B-A3B AWQ INT4",
        "endpoint": "server60:8080",
        "temperature": 0.6,
        "max_tokens": 65_536,
        "workers": 4,
        "treatment": True,
        "trace_file": "qwen-agentworld-bash-timeout.ndjson",
    },
}

PACKET_RULE = (
    "ThinkingCap baseline versus pi-check: select every strict-solve flip, invalid-outcome "
    "discordance, absolute partial-score change of at least 0.10, or absolute feature-test "
    "rate change of at least 0.50 when both attempts graded."
)


def read_json(path: Path) -> Any:
    """Read one UTF-8 JSON artifact."""
    return json.loads(path.read_text())


def load_task_metadata() -> dict[str, dict[str, Any]]:
    """Load display metadata for the fixed 12_v2 task set."""
    metadata: dict[str, dict[str, Any]] = {}
    for task in TASK_ORDER:
        document = tomllib.loads((TASKS_ROOT / task / "task.toml").read_text())
        values = document["metadata"]
        metadata[task] = {
            "task": task,
            "title": values["display_title"],
            "language": values["language"].title(),
            "category": values["category"],
        }
    return metadata


def load_result_cells(result_root: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Load one immutable result for every task and rep in 12_v2."""
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    for result_path in sorted(result_root.glob("*/rep*/result.json")):
        result = read_json(result_path)
        task = result_path.parents[1].name
        rep = int(result_path.parent.name.removeprefix("rep"))
        result["task"] = task
        result["rep"] = rep
        result["artifact_root"] = str(result_path.parent)
        cells[(task, rep)] = result
    expected = {(task, rep) for task in TASK_ORDER for rep in range(3)}
    if set(cells) != expected:
        raise ValueError(
            "ThinkingCap pi-check comparison pairing mismatch: "
            f"root={result_root}, missing={sorted(expected - set(cells))}, "
            f"extra={sorted(set(cells) - expected)}"
        )
    return cells


def result_is_valid(result: dict[str, Any]) -> bool:
    """Return whether a benchmark attempt produced a usable grade."""
    return result.get("reward_binary") in {0, 1}


def result_status(result: dict[str, Any]) -> str:
    """Return a plain status label for one benchmark attempt."""
    if result.get("reward_binary") == 1:
        return "solved"
    if result_is_valid(result):
        return "graded"
    if result.get("agent_exit") == "timeout":
        return "agent timeout"
    if result.get("verifier_exit") == "timeout":
        return "verifier timeout"
    return "invalid"


def percentile(values: list[int | float], probability: float) -> float:
    """Calculate an interpolated percentile without external dependencies."""
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def summarize_config_results(
    cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Summarize score, grade, usage, and execution metrics for one config."""
    rows = list(cells.values())
    valid = [row for row in rows if result_is_valid(row)]
    f2p_passed = sum(int(row.get("f2p_passed") or 0) for row in valid)
    f2p_total = sum(int(row.get("f2p_total") or 0) for row in valid)
    p2p_passed = sum(int(row.get("p2p_passed") or 0) for row in valid)
    p2p_total = sum(int(row.get("p2p_total") or 0) for row in valid)
    return {
        "cells": len(rows),
        "valid": len(valid),
        "invalid": len(rows) - len(valid),
        "solves": sum(row.get("reward_binary") == 1 for row in rows),
        "mean_partial_all": statistics.mean(
            float(row.get("reward_partial") or 0) for row in rows
        ),
        "median_partial_all": statistics.median(
            float(row.get("reward_partial") or 0) for row in rows
        ),
        "mean_partial_valid": statistics.mean(
            float(row.get("reward_partial") or 0) for row in valid
        ),
        "f2p_passed": f2p_passed,
        "f2p_total": f2p_total,
        "f2p_micro": f2p_passed / f2p_total,
        "p2p_passed": p2p_passed,
        "p2p_total": p2p_total,
        "p2p_micro": p2p_passed / p2p_total,
        "input_tokens": sum(int(row.get("input_tokens") or 0) for row in rows),
        "output_tokens": sum(int(row.get("output_tokens") or 0) for row in rows),
        "total_tokens": sum(int(row.get("total_tokens") or 0) for row in rows),
        "median_total_tokens": statistics.median(
            int(row.get("total_tokens") or 0) for row in rows
        ),
        "wall_sum_s": sum(float(row.get("agent_wall_s") or 0) for row in rows),
        "wall_median_s": statistics.median(
            float(row.get("agent_wall_s") or 0) for row in rows
        ),
        "turns": sum(int(row.get("turns") or 0) for row in rows),
        "tool_calls": sum(int(row.get("tool_calls") or 0) for row in rows),
        "patch_bytes": sum(int(row.get("patch_bytes") or 0) for row in rows),
        "agent_timeouts": sum(row.get("agent_exit") == "timeout" for row in rows),
        "verifier_timeouts": sum(row.get("verifier_exit") == "timeout" for row in rows),
    }


def load_session_records(cell_root: Path) -> list[dict[str, Any]]:
    """Load native Pi session records for one benchmark attempt."""
    records: list[dict[str, Any]] = []
    for session_path in sorted(cell_root.glob("session/*.jsonl")):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def message_text(message: dict[str, Any]) -> str:
    """Extract plain text from one Pi message."""
    parts: list[str] = []
    for item in message.get("content") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "\n".join(parts)


def classify_tool_error(tool_name: str, result_text: str) -> str:
    """Classify one recorded tool-result error by concrete cause."""
    text = result_text.lower()
    if tool_name == "bash":
        return "shell nonzero / diagnostic"
    if tool_name == "edit" and text.startswith("validation failed for tool"):
        return "malformed edit arguments"
    if tool_name == "edit" and (
        "could not find" in text or "old text must match" in text
    ):
        return "edit target mismatch"
    if tool_name == "edit":
        return "edit no-op / other"
    if tool_name == "read" and (
        "enoent" in text or "no such file" in text or "not found" in text
    ):
        return "read missing file"
    if tool_name == "read" and ("offset" in text or "range" in text):
        return "read range error"
    return f"{tool_name} other"


def summarize_timeout_trace(cell_root: Path, trace_file: str | None) -> dict[str, Any]:
    """Summarize the per-cell Bash timeout audit trace."""
    if trace_file is None:
        return {"present": False, "records": 0, "actions": {}}
    trace_path = cell_root / trace_file
    if not trace_path.exists():
        return {"present": False, "records": 0, "actions": {}}
    actions: collections.Counter[str] = collections.Counter()
    records = 0
    for line in trace_path.read_text().splitlines():
        if not line.strip():
            continue
        records += 1
        actions[str(json.loads(line).get("action"))] += 1
    return {"present": True, "records": records, "actions": dict(actions)}


def analyze_cell_session(cell_root: Path, trace_file: str | None) -> dict[str, Any]:
    """Measure treatment delivery, tool behavior, and post-check work in one session."""
    records = load_session_records(cell_root)
    reaudit_index: int | None = None
    tool_results: dict[str, dict[str, Any]] = {}
    user_messages = 0
    for index, record in enumerate(records):
        if record.get("type") != "message":
            continue
        message = record.get("message") or {}
        if message.get("role") == "user":
            user_messages += 1
            if "Re-audit every requirement" in message_text(message):
                reaudit_index = index
        elif message.get("role") == "toolResult":
            tool_results[str(message.get("toolCallId"))] = message

    counts: collections.Counter[str] = collections.Counter()
    tool_calls: collections.Counter[str] = collections.Counter()
    tool_errors: collections.Counter[str] = collections.Counter()
    error_causes: collections.Counter[str] = collections.Counter()
    post_check_mutations: list[dict[str, Any]] = []
    malformed_tool_calls = 0
    raw_tool_call_leaks = 0
    final_text = ""
    max_prompt_tokens = 0
    max_completion_tokens = 0

    for record_index, record in enumerate(records):
        if record.get("type") != "message":
            continue
        message = record.get("message") or {}
        if message.get("role") != "assistant":
            continue
        counts["assistant_messages"] += 1
        usage = message.get("usage") or {}
        input_tokens = int(usage.get("input") or 0)
        output_tokens = int(usage.get("output") or 0)
        counts["session_input_tokens"] += input_tokens
        counts["session_output_tokens"] += output_tokens
        max_prompt_tokens = max(max_prompt_tokens, input_tokens)
        max_completion_tokens = max(max_completion_tokens, output_tokens)
        after_reaudit = reaudit_index is not None and record_index > reaudit_index
        if after_reaudit:
            counts["post_check_messages"] += 1
            counts["post_check_input_tokens"] += input_tokens
            counts["post_check_output_tokens"] += output_tokens
        for item in message.get("content") or []:
            if not isinstance(item, dict):
                continue
            block_type = item.get("type")
            if block_type == "thinking":
                counts["thinking_blocks"] += 1
            elif block_type == "text":
                final_text = str(item.get("text", ""))
                if re.search(
                    r"<tool_call>|<function=", final_text, flags=re.IGNORECASE
                ):
                    raw_tool_call_leaks += 1
            elif block_type == "toolCall":
                counts["tool_call_blocks"] += 1
                tool_name = str(item.get("name"))
                arguments = item.get("arguments")
                tool_calls[tool_name] += 1
                if not isinstance(arguments, dict) or not tool_name:
                    malformed_tool_calls += 1
                tool_result = tool_results.get(str(item.get("id")))
                if tool_result is not None and tool_result.get("isError"):
                    tool_errors[tool_name] += 1
                    error_causes[
                        classify_tool_error(tool_name, message_text(tool_result))
                    ] += 1
                if after_reaudit:
                    counts["post_check_tool_calls"] += 1
                    if tool_name == "bash":
                        counts["post_check_bash_calls"] += 1
                    if tool_name in {"edit", "write"}:
                        counts["post_check_mutation_calls"] += 1
                        arguments_dict = (
                            arguments if isinstance(arguments, dict) else {}
                        )
                        post_check_mutations.append(
                            {
                                "tool": tool_name,
                                "path": arguments_dict.get("path"),
                                "old_excerpt": str(arguments_dict.get("oldText", ""))[
                                    :300
                                ],
                                "new_excerpt": str(arguments_dict.get("newText", ""))[
                                    :300
                                ],
                            }
                        )

    timeout_trace = summarize_timeout_trace(cell_root, trace_file)
    return {
        "user_messages": user_messages,
        "reaudit_delivered": reaudit_index is not None,
        "assistant_messages": counts["assistant_messages"],
        "thinking_blocks": counts["thinking_blocks"],
        "tool_call_blocks": counts["tool_call_blocks"],
        "tool_calls": dict(tool_calls),
        "tool_errors": dict(tool_errors),
        "error_causes": dict(error_causes),
        "malformed_tool_calls": malformed_tool_calls,
        "raw_tool_call_leaks": raw_tool_call_leaks,
        "max_prompt_tokens": max_prompt_tokens,
        "max_completion_tokens": max_completion_tokens,
        "session_input_tokens": counts["session_input_tokens"],
        "session_output_tokens": counts["session_output_tokens"],
        "post_check_messages": counts["post_check_messages"],
        "post_check_input_tokens": counts["post_check_input_tokens"],
        "post_check_output_tokens": counts["post_check_output_tokens"],
        "post_check_tool_calls": counts["post_check_tool_calls"],
        "post_check_bash_calls": counts["post_check_bash_calls"],
        "post_check_mutation_calls": counts["post_check_mutation_calls"],
        "post_check_mutations": post_check_mutations,
        "timeout_trace": timeout_trace,
        "final_text": final_text[-2_000:],
    }


def provider_request_matches(spec: dict[str, Any], cell_root: Path) -> bool:
    """Verify the saved first provider request against the config contract."""
    request_paths = sorted(
        (cell_root / "initial_context").glob("provider_request_*.json")
    )
    if not request_paths:
        return False
    request = read_json(request_paths[0])
    return (
        request.get("model") == spec["request_model"]
        and request.get("max_tokens") == spec["max_tokens"]
        and request.get("temperature") == spec["temperature"]
        and request.get("top_p") == 0.95
        and request.get("top_k") == 20
        and request.get("min_p") == 0
        and request.get("repetition_penalty") == 1
        and request.get("chat_template_kwargs")
        == {"enable_thinking": True, "preserve_thinking": True}
        and "thinking_token_budget" not in request
    )


def merge_counter(target: collections.Counter[str], values: dict[str, int]) -> None:
    """Merge a JSON-style integer mapping into one counter."""
    for key, value in values.items():
        target[key] += int(value)


def summarize_config_delivery(
    spec: dict[str, Any],
    cells: dict[tuple[str, int], dict[str, Any]],
    sessions: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate provider, pi-check, timeout, and tool-delivery evidence."""
    totals: collections.Counter[str] = collections.Counter()
    tool_calls: collections.Counter[str] = collections.Counter()
    tool_errors: collections.Counter[str] = collections.Counter()
    error_causes: collections.Counter[str] = collections.Counter()
    timeout_actions: collections.Counter[str] = collections.Counter()
    request_shape_cells = 0
    delivered_cells = 0
    for key, result in cells.items():
        cell_root = Path(result["artifact_root"])
        session = sessions[key]
        request_matches = provider_request_matches(spec, cell_root)
        request_shape_cells += int(request_matches)
        merge_counter(tool_calls, session["tool_calls"])
        merge_counter(tool_errors, session["tool_errors"])
        merge_counter(error_causes, session["error_causes"])
        merge_counter(timeout_actions, session["timeout_trace"]["actions"])
        for field in [
            "assistant_messages",
            "thinking_blocks",
            "tool_call_blocks",
            "malformed_tool_calls",
            "raw_tool_call_leaks",
            "session_input_tokens",
            "session_output_tokens",
            "post_check_messages",
            "post_check_input_tokens",
            "post_check_output_tokens",
            "post_check_tool_calls",
            "post_check_bash_calls",
            "post_check_mutation_calls",
        ]:
            totals[field] += int(session[field])
        totals["reaudit_cells"] += int(session["reaudit_delivered"])
        totals["timeout_trace_cells"] += int(session["timeout_trace"]["present"])
        totals["cells_with_post_check_mutation"] += int(
            session["post_check_mutation_calls"] > 0
        )
        treatment_delivered = (
            session["reaudit_delivered"] and session["timeout_trace"]["present"]
            if spec["treatment"]
            else True
        )
        delivered_cells += int(request_matches and treatment_delivered)

    session_tokens = totals["session_input_tokens"] + totals["session_output_tokens"]
    post_check_tokens = (
        totals["post_check_input_tokens"] + totals["post_check_output_tokens"]
    )
    return {
        "classification": "delivered" if delivered_cells == 36 else "missing",
        "delivered_cells": delivered_cells,
        "request_shape_cells": request_shape_cells,
        "reaudit_cells": totals["reaudit_cells"],
        "timeout_trace_cells": totals["timeout_trace_cells"],
        "timeout_actions": dict(timeout_actions),
        "assistant_messages": totals["assistant_messages"],
        "thinking_blocks": totals["thinking_blocks"],
        "tool_call_blocks": totals["tool_call_blocks"],
        "tool_calls": dict(tool_calls),
        "tool_errors": dict(tool_errors),
        "tool_error_causes": dict(error_causes),
        "total_tool_errors": sum(tool_errors.values()),
        "malformed_tool_calls": totals["malformed_tool_calls"],
        "raw_tool_call_leaks": totals["raw_tool_call_leaks"],
        "session_tokens": session_tokens,
        "post_check_tokens": post_check_tokens,
        "post_check_token_share": post_check_tokens / session_tokens
        if session_tokens
        else 0,
        "post_check_tool_calls": totals["post_check_tool_calls"],
        "post_check_bash_calls": totals["post_check_bash_calls"],
        "post_check_mutation_calls": totals["post_check_mutation_calls"],
        "cells_with_post_check_mutation": totals["cells_with_post_check_mutation"],
    }


def exact_task_signflip_pvalue(task_deltas: list[float]) -> float:
    """Calculate an exact two-sided sign-flip p-value over 12 task means."""
    observed = abs(statistics.mean(task_deltas))
    permutations = [
        abs(statistics.mean(sign * delta for sign, delta in zip(signs, task_deltas)))
        for signs in itertools.product((-1, 1), repeat=len(task_deltas))
    ]
    return sum(value >= observed - 1e-15 for value in permutations) / len(permutations)


def task_bootstrap_interval(task_deltas: list[float]) -> list[float]:
    """Calculate a deterministic task-cluster bootstrap interval."""
    random_source = random.Random(20260804)
    draws: list[float] = []
    for _ in range(20_000):
        sample = [
            task_deltas[random_source.randrange(len(task_deltas))] for _ in task_deltas
        ]
        draws.append(statistics.mean(sample))
    draws.sort()
    return [draws[500], draws[19_499]]


def build_pair_comparison(
    left_name: str,
    right_name: str,
    config_cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
) -> dict[str, Any]:
    """Compare two configs on all 36 paired attempts and shared valid attempts."""
    left = config_cells[left_name]
    right = config_cells[right_name]
    keys = [(task, rep) for task in TASK_ORDER for rep in range(3)]
    deltas = [
        float(right[key].get("reward_partial") or 0)
        - float(left[key].get("reward_partial") or 0)
        for key in keys
    ]
    common_valid = [
        key
        for key in keys
        if result_is_valid(left[key]) and result_is_valid(right[key])
    ]
    common_partial_deltas = [
        float(right[key]["reward_partial"]) - float(left[key]["reward_partial"])
        for key in common_valid
    ]
    task_deltas = [
        statistics.mean(
            float(right[(task, rep)].get("reward_partial") or 0)
            - float(left[(task, rep)].get("reward_partial") or 0)
            for rep in range(3)
        )
        for task in TASK_ORDER
    ]

    def common_grade(
        side: dict[tuple[str, int], dict[str, Any]], prefix: str
    ) -> dict[str, Any]:
        f2p_passed = sum(int(side[key]["f2p_passed"]) for key in common_valid)
        f2p_total = sum(int(side[key]["f2p_total"]) for key in common_valid)
        p2p_passed = sum(int(side[key]["p2p_passed"]) for key in common_valid)
        p2p_total = sum(int(side[key]["p2p_total"]) for key in common_valid)
        return {
            f"{prefix}_f2p_passed": f2p_passed,
            f"{prefix}_f2p_total": f2p_total,
            f"{prefix}_f2p_micro": f2p_passed / f2p_total,
            f"{prefix}_p2p_passed": p2p_passed,
            f"{prefix}_p2p_total": p2p_total,
            f"{prefix}_p2p_micro": p2p_passed / p2p_total,
            f"{prefix}_mean_f2p": statistics.mean(
                float(side[key]["f2p"]) for key in common_valid
            ),
            f"{prefix}_mean_p2p": statistics.mean(
                float(side[key]["p2p"]) for key in common_valid
            ),
            f"{prefix}_mean_partial": statistics.mean(
                float(side[key]["reward_partial"]) for key in common_valid
            ),
        }

    left_summary = summarize_config_results(left)
    right_summary = summarize_config_results(right)
    return {
        "left": left_name,
        "right": right_name,
        "direction": f"{right_name} minus {left_name}",
        "pairs": 36,
        "mean_partial_delta_all": statistics.mean(deltas),
        "median_partial_delta_all": statistics.median(deltas),
        "wins_over_0_05": sum(delta > 0.05 for delta in deltas),
        "losses_below_minus_0_05": sum(delta < -0.05 for delta in deltas),
        "ties_within_0_05": sum(abs(delta) <= 0.05 for delta in deltas),
        "right_only_solves": sum(
            right[key].get("reward_binary") == 1 and left[key].get("reward_binary") != 1
            for key in keys
        ),
        "left_only_solves": sum(
            left[key].get("reward_binary") == 1 and right[key].get("reward_binary") != 1
            for key in keys
        ),
        "right_only_invalid": sum(
            not result_is_valid(right[key]) and result_is_valid(left[key])
            for key in keys
        ),
        "left_only_invalid": sum(
            not result_is_valid(left[key]) and result_is_valid(right[key])
            for key in keys
        ),
        "common_valid_pairs": len(common_valid),
        "common_valid_mean_partial_delta": statistics.mean(common_partial_deltas),
        "common_valid_median_partial_delta": statistics.median(common_partial_deltas),
        "task_mean_deltas": dict(zip(TASK_ORDER, task_deltas)),
        "task_signflip_p": exact_task_signflip_pvalue(task_deltas),
        "task_bootstrap_95": task_bootstrap_interval(task_deltas),
        "token_ratio": right_summary["total_tokens"] / left_summary["total_tokens"],
        "wall_ratio": right_summary["wall_sum_s"] / left_summary["wall_sum_s"],
        "turn_ratio": right_summary["turns"] / left_summary["turns"],
        "tool_call_ratio": right_summary["tool_calls"] / left_summary["tool_calls"],
        **common_grade(left, "left_common"),
        **common_grade(right, "right_common"),
    }


def build_task_rows(
    config_cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
    metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build task-level means for every config."""
    rows: list[dict[str, Any]] = []
    for task in TASK_ORDER:
        row: dict[str, Any] = {**metadata[task]}
        for config_name, cells in config_cells.items():
            values = [cells[(task, rep)] for rep in range(3)]
            row[config_name] = {
                "solves": sum(value.get("reward_binary") == 1 for value in values),
                "invalid": sum(not result_is_valid(value) for value in values),
                "mean_partial": statistics.mean(
                    float(value.get("reward_partial") or 0) for value in values
                ),
                "median_tokens": statistics.median(
                    int(value.get("total_tokens") or 0) for value in values
                ),
            }
        rows.append(row)
    return rows


def build_language_rows(
    config_cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
    metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build language-level means for every config."""
    rows: list[dict[str, Any]] = []
    for language in sorted({values["language"] for values in metadata.values()}):
        keys = [
            (task, rep)
            for task in TASK_ORDER
            if metadata[task]["language"] == language
            for rep in range(3)
        ]
        row: dict[str, Any] = {"language": language, "cells": len(keys)}
        for config_name, cells in config_cells.items():
            values = [cells[key] for key in keys]
            row[config_name] = {
                "solves": sum(value.get("reward_binary") == 1 for value in values),
                "invalid": sum(not result_is_valid(value) for value in values),
                "mean_partial": statistics.mean(
                    float(value.get("reward_partial") or 0) for value in values
                ),
                "median_tokens": statistics.median(
                    int(value.get("total_tokens") or 0) for value in values
                ),
            }
        rows.append(row)
    return rows


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    """Keep the review-relevant fields from one result record."""
    keys = [
        "reward_binary",
        "reward_partial",
        "f2p",
        "f2p_passed",
        "f2p_total",
        "p2p",
        "p2p_passed",
        "p2p_total",
        "agent_exit",
        "agent_timed_out",
        "verifier_exit",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "total_tokens",
        "output_tokens",
        "patch_bytes",
    ]
    return {key: result.get(key) for key in keys}


def parse_patch_summary(cell_root: Path) -> dict[str, Any]:
    """Summarize changed files and line movement from a model.patch artifact."""
    patch_path = cell_root / "artifacts/model.patch"
    if not patch_path.exists():
        return {
            "path": str(patch_path),
            "bytes": 0,
            "files": [],
            "additions": 0,
            "deletions": 0,
        }
    text = patch_path.read_text(errors="replace")
    files = re.findall(r"^diff --git a/(.+?) b/(.+?)$", text, flags=re.MULTILINE)
    additions = sum(
        1
        for line in text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    deletions = sum(
        1
        for line in text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    )
    return {
        "path": str(patch_path),
        "bytes": patch_path.stat().st_size,
        "files": [right for _, right in files],
        "additions": additions,
        "deletions": deletions,
    }


def parse_verifier_failures(cell_root: Path) -> dict[str, Any]:
    """Extract failed-test names and bounded messages from CTRF artifacts."""
    ctrf_path = cell_root / "verifier/ctrf.json"
    failed: list[dict[str, str]] = []
    if ctrf_path.exists():
        document = read_json(ctrf_path)
        results = document.get("results")
        if not isinstance(results, dict):
            raise ValueError(f"CTRF results missing or invalid: {ctrf_path}")
        tests = results.get("tests")
        if not isinstance(tests, list):
            raise ValueError(f"CTRF tests missing or invalid: {ctrf_path}")
        for test in tests:
            if not isinstance(test, dict):
                raise TypeError(f"CTRF test record invalid: {ctrf_path}")
            if test.get("status") == "failed":
                failed.append(
                    {
                        "name": str(test.get("name", "")),
                        "message": str(test.get("message", ""))[:2_000],
                    }
                )
    return {"path": str(ctrf_path), "failed_count": len(failed), "failed_tests": failed}


def packet_trigger_reasons(
    baseline: dict[str, Any], treatment: dict[str, Any]
) -> list[str]:
    """Apply the predeclared ThinkingCap trajectory-packet selection rule."""
    reasons: list[str] = []
    if (baseline.get("reward_binary") == 1) != (treatment.get("reward_binary") == 1):
        reasons.append("strict-solve flip")
    if result_is_valid(baseline) != result_is_valid(treatment):
        reasons.append("invalid-outcome discordance")
    partial_delta = float(treatment.get("reward_partial") or 0) - float(
        baseline.get("reward_partial") or 0
    )
    if abs(partial_delta) >= 0.10:
        reasons.append(f"absolute partial-score change {partial_delta:+.3f}")
    if result_is_valid(baseline) and result_is_valid(treatment):
        f2p_delta = float(treatment.get("f2p") or 0) - float(baseline.get("f2p") or 0)
        if abs(f2p_delta) >= 0.50:
            reasons.append(f"absolute feature-test change {f2p_delta:+.3f}")
    return reasons


def build_packet_side(
    result: dict[str, Any], session: dict[str, Any]
) -> dict[str, Any]:
    """Build one reviewable side of a selected trajectory packet."""
    cell_root = Path(result["artifact_root"])
    return {
        "result_path": str(cell_root / "result.json"),
        "status": result_status(result),
        "metrics": compact_result(result),
        "patch": parse_patch_summary(cell_root),
        "verifier": parse_verifier_failures(cell_root),
        "session": {
            "reaudit_delivered": session["reaudit_delivered"],
            "tool_calls": session["tool_calls"],
            "tool_errors": session["tool_errors"],
            "post_check_tool_calls": session["post_check_tool_calls"],
            "post_check_bash_calls": session["post_check_bash_calls"],
            "post_check_mutation_calls": session["post_check_mutation_calls"],
            "post_check_mutations": session["post_check_mutations"],
            "final_text": session["final_text"],
        },
    }


def build_trajectory_packets(
    config_cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
    config_sessions: dict[str, dict[tuple[str, int], dict[str, Any]]],
    metadata: dict[str, dict[str, Any]],
    classifications: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build selected ThinkingCap baseline-versus-treatment trajectory packets."""
    baseline = config_cells["thinkingcap_baseline"]
    treatment = config_cells["thinkingcap_pi_check"]
    packets: list[dict[str, Any]] = []
    for task in TASK_ORDER:
        for rep in range(3):
            key = (task, rep)
            reasons = packet_trigger_reasons(baseline[key], treatment[key])
            if not reasons:
                continue
            packet_key = f"{task}__rep{rep}"
            if packet_key not in classifications:
                raise ValueError(f"Missing packet classification: {packet_key}")
            packets.append(
                {
                    "packet_key": packet_key,
                    "task": task,
                    "rep": rep,
                    "title": metadata[task]["title"],
                    "language": metadata[task]["language"],
                    "trigger_reasons": reasons,
                    "partial_delta": float(treatment[key].get("reward_partial") or 0)
                    - float(baseline[key].get("reward_partial") or 0),
                    "baseline": build_packet_side(
                        baseline[key], config_sessions["thinkingcap_baseline"][key]
                    ),
                    "treatment": build_packet_side(
                        treatment[key], config_sessions["thinkingcap_pi_check"][key]
                    ),
                    "classification": classifications[packet_key],
                }
            )
    if set(classifications) != {packet["packet_key"] for packet in packets}:
        raise ValueError(
            "Packet classifications do not match the predeclared packet rule"
        )
    return packets


def render_packet_markdown(packet: dict[str, Any]) -> str:
    """Render one selected trajectory packet as readable Markdown."""
    baseline = packet["baseline"]
    treatment = packet["treatment"]
    classification = packet["classification"]

    def side_lines(label: str, side: dict[str, Any]) -> list[str]:
        metrics = side["metrics"]
        failed_names = [test["name"] for test in side["verifier"]["failed_tests"][:30]]
        return [
            f"### {label}",
            "",
            f"- Status: `{side['status']}`",
            f"- Binary / partial: `{metrics['reward_binary']}` / `{metrics['reward_partial']}`",
            f"- F2P: `{metrics['f2p_passed']}/{metrics['f2p_total']}`; P2P: `{metrics['p2p_passed']}/{metrics['p2p_total']}`",
            f"- Tokens / wall: `{metrics['total_tokens']}` / `{metrics['agent_wall_s']}s`",
            f"- Turns / tools: `{metrics['turns']}` / `{metrics['tool_calls']}`",
            f"- Changed files: `{', '.join(side['patch']['files']) or 'none'}`",
            f"- Failed tests: `{side['verifier']['failed_count']}`",
            f"- Post-check tools / mutations: `{side['session']['post_check_tool_calls']}` / `{side['session']['post_check_mutation_calls']}`",
            "",
            "Failed-test sample:",
            "",
            *([f"- `{name}`" for name in failed_names] or ["- None recorded"]),
            "",
            "Final claim:",
            "",
            side["session"]["final_text"].strip() or "_No final text recorded._",
            "",
        ]

    lines = [
        f"# {packet['title']} · rep {packet['rep']}",
        "",
        f"Task: `{packet['task']}` · Language: {packet['language']}",
        "",
        f"Selected because: {', '.join(packet['trigger_reasons'])}.",
        "",
        *side_lines("ThinkingCap baseline", baseline),
        *side_lines("ThinkingCap pi-check + timeout", treatment),
        "## Classification",
        "",
        f"- Effect: **{classification['effect']}**",
        f"- Primary cause: **{classification['primary_bucket']}**",
        f"- Secondary cause: **{classification['secondary_bucket']}**",
        f"- Confidence: **{classification['confidence']}**",
        "",
        classification["mechanism"],
        "",
        f"**Practical lesson:** {classification['lesson']}",
    ]
    return "\n".join(line.rstrip() for line in lines).rstrip() + "\n"


def build_full_cell_rows(
    config_cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
    packet_keys: set[str],
) -> list[dict[str, Any]]:
    """Build the complete task-by-rep denominator for the HTML report."""
    rows: list[dict[str, Any]] = []
    for task in TASK_ORDER:
        for rep in range(3):
            key = (task, rep)
            rows.append(
                {
                    "task": task,
                    "rep": rep,
                    "packet_key": f"{task}__rep{rep}"
                    if f"{task}__rep{rep}" in packet_keys
                    else None,
                    "configs": {
                        config_name: {
                            "status": result_status(cells[key]),
                            "reward_binary": cells[key].get("reward_binary"),
                            "reward_partial": cells[key].get("reward_partial"),
                            "f2p": cells[key].get("f2p"),
                            "p2p": cells[key].get("p2p"),
                            "total_tokens": cells[key].get("total_tokens"),
                        }
                        for config_name, cells in config_cells.items()
                    },
                }
            )
    return rows


def validate_analysis(analysis: dict[str, Any]) -> None:
    """Fail closed when the comparison denominator or treatment proof is incomplete."""
    if len(analysis["full_cell_rows"]) != 36:
        raise ValueError("ThinkingCap pi-check comparison must contain 36 full rows")
    if len(analysis["packets"]) != 9:
        raise ValueError("ThinkingCap pi-check packet rule must select exactly 9 rows")
    for config_name, config in analysis["configs"].items():
        if config["aggregate"]["cells"] != 36:
            raise ValueError(f"Config {config_name} does not contain 36 attempts")
        if config["delivery"]["classification"] != "delivered":
            raise ValueError(f"Config {config_name} delivery was not proven")
        if config["delivery"]["malformed_tool_calls"] != 0:
            raise ValueError(f"Config {config_name} contains malformed tool calls")
    expected_treatments = {"thinkingcap_pi_check", "agentworld_pi_check"}
    for config_name in expected_treatments:
        delivery = analysis["configs"][config_name]["delivery"]
        if delivery["reaudit_cells"] != 36 or delivery["timeout_trace_cells"] != 36:
            raise ValueError(
                f"Config {config_name} treatment did not reach every attempt"
            )


def build_analysis() -> dict[str, Any]:
    """Build and validate the full four-config comparison artifact."""
    metadata = load_task_metadata()
    config_cells: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    config_sessions: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    config_output: dict[str, Any] = {}
    for config_name, spec in CONFIG_SPECS.items():
        cells = load_result_cells(spec["result_root"])
        sessions = {
            key: analyze_cell_session(Path(result["artifact_root"]), spec["trace_file"])
            for key, result in cells.items()
        }
        config_cells[config_name] = cells
        config_sessions[config_name] = sessions
        config_output[config_name] = {
            key: value
            for key, value in spec.items()
            if key not in {"result_root", "request_model", "trace_file"}
        }
        config_output[config_name]["result_root"] = str(spec["result_root"])
        config_output[config_name]["aggregate"] = summarize_config_results(cells)
        config_output[config_name]["delivery"] = summarize_config_delivery(
            spec, cells, sessions
        )

    classifications = read_json(REPORT_ROOT / "classifications.json")
    packets = build_trajectory_packets(
        config_cells, config_sessions, metadata, classifications
    )
    packet_keys = {packet["packet_key"] for packet in packets}
    analysis = {
        "comparison": {
            "name": "ThinkingCap pi-check versus baseline and Qwen-AgentWorld",
            "subset": "12_v2",
            "tasks": 12,
            "reps": 3,
            "attempts_per_config": 36,
            "total_trajectories": 144,
            "thinking": "high",
            "subject": "pi@0.83.0",
            "packet_rule": PACKET_RULE,
            "packet_count": len(packets),
            "roles": {
                config_name: spec["role"] for config_name, spec in CONFIG_SPECS.items()
            },
            "causal_limit": (
                "Each within-model comparison changes two mechanisms together: pi-check and a "
                "360-second default Bash timeout. Independent reps add ordinary run variance. "
                "The cross-model comparison also changes checkpoint, architecture, endpoint, "
                "temperature, output ceiling, and worker count."
            ),
        },
        "configs": config_output,
        "pairs": {
            "thinkingcap_treatment": build_pair_comparison(
                "thinkingcap_baseline", "thinkingcap_pi_check", config_cells
            ),
            "agentworld_treatment": build_pair_comparison(
                "agentworld_baseline", "agentworld_pi_check", config_cells
            ),
            "pi_check_models": build_pair_comparison(
                "agentworld_pi_check", "thinkingcap_pi_check", config_cells
            ),
            "baseline_models": build_pair_comparison(
                "agentworld_baseline", "thinkingcap_baseline", config_cells
            ),
        },
        "task_rows": build_task_rows(config_cells, metadata),
        "language_rows": build_language_rows(config_cells, metadata),
        "full_cell_rows": build_full_cell_rows(config_cells, packet_keys),
        "packets": packets,
        "conclusions": {
            "thinkingcap": (
                "The combined setup improved ThinkingCap's run completion, not its stable-attempt "
                "quality: invalid outcomes fell from 3 to 1 and all-cell mean partial rose by "
                "0.054, while the 32 attempts graded on both sides changed by -0.001 partial."
            ),
            "cost": (
                "ThinkingCap used 67.8% more tokens and 39.9% more agent wall time. The post-check "
                "stage itself consumed 108.4M tokens, 30.6% of the treatment run."
            ),
            "agentworld": (
                "AgentWorld did not receive the same reliability benefit: invalid outcomes rose "
                "from 3 to 4, all-cell mean partial fell by 0.030, and token use rose by 45.0%."
            ),
            "cross_model": (
                "Under the combined setup, ThinkingCap and AgentWorld used nearly the same total "
                "tokens, but ThinkingCap produced more valid attempts and higher feature coverage."
            ),
            "decision": (
                "Keep the 360-second Bash guard as a candidate reliability control. Do not adopt "
                "pi-check as an efficiency improvement: it added substantial tokens and produced "
                "no strict solve. Run timeout-only and pi-check-only controls before assigning cause."
            ),
        },
    }
    validate_analysis(analysis)
    return analysis


def write_analysis_artifacts(analysis: dict[str, Any]) -> None:
    """Write deterministic JSON and Markdown artifacts for the comparison."""
    packet_root = REPORT_ROOT / "packets"
    packet_root.mkdir(parents=True, exist_ok=True)
    expected_names: set[str] = set()
    for packet in analysis["packets"]:
        stem = packet["packet_key"]
        expected_names.update({f"{stem}.json", f"{stem}.md"})
        (packet_root / f"{stem}.json").write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n"
        )
        (packet_root / f"{stem}.md").write_text(render_packet_markdown(packet))
    for path in packet_root.iterdir():
        if path.is_file() and path.name not in expected_names:
            path.unlink()
    (REPORT_ROOT / "analysis.json").write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n"
    )


def main() -> None:
    """Build all comparison data and packet artifacts."""
    analysis = build_analysis()
    write_analysis_artifacts(analysis)
    print(
        "ThinkingCap pi-check comparison extracted: "
        f"{len(analysis['full_cell_rows'])} paired rows, "
        f"{len(analysis['packets'])} packets -> {REPORT_ROOT / 'analysis.json'}"
    )


if __name__ == "__main__":
    main()
