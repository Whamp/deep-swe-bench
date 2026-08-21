"""Build the staged read-long-lines pilot comparison report."""

from __future__ import annotations

import argparse
import collections
import html
import importlib.util
import json
import math
import statistics
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = REPORT_DIR.parents[1]
TASKS = ("fd-deterministic-multi-key-sorting", "abs-module-cache-flags")
REPS = range(3)
PARTIAL_DELTA_PACKET_THRESHOLD = 0.1
MODEL_SPECS = {
    "sol": {
        "label": "GPT-5.6 Sol",
        "model_leaf": "gpt-5.6-sol",
        "model": "openai-codex/gpt-5.6-sol",
        "thinking": "low",
        "baseline_config": "baseline@1.1.0",
    },
    "terra": {
        "label": "GPT-5.6 Terra",
        "model_leaf": "gpt-5.6-terra",
        "model": "openai-codex/gpt-5.6-terra",
        "thinking": "low",
        "baseline_config": "baseline@1.1.0",
    },
    "luna": {
        "label": "GPT-5.6 Luna",
        "model_leaf": "gpt-5.6-luna",
        "model": "openai-codex/gpt-5.6-luna",
        "thinking": "low",
        "baseline_config": "baseline@1.1.0",
    },
    "flash": {
        "label": "DeepSeek V4 Flash 0731",
        "model_leaf": "deepseek-v4-flash-0731",
        "model": "openrouter/deepseek/deepseek-v4-flash-0731",
        "thinking": "low",
        "baseline_config": "baseline-openrouter-deepseek-v4-flash-0731@1.0.0",
    },
    "glm": {
        "label": "GLM-5.2",
        "model_leaf": "glm-5.2",
        "model": "zai/glm-5.2",
        "thinking": "max",
        "baseline_config": "baseline@1.1.0",
    },
}
EXTENSION_CONFIG = "read-long-lines@1.0.0"


def extension_notice_length(line_number: int, total_characters: int) -> int:
    """Return extension notice length in Unicode code points."""
    return len(
        f"[Line {line_number} shortened: showing 2,000 of "
        f"{total_characters:,} characters. Use offset={line_number}, limit=1 "
        "to read the complete line.]"
    )


def preview_event_notice_characters(event: dict[str, Any]) -> int:
    """Return all preview-notice characters inserted for one telemetry event."""
    lines = event.get("shortenedLines")
    if not isinstance(lines, list):
        return 0
    notice_characters = sum(
        extension_notice_length(int(line["lineNumber"]), int(line["totalCharacters"]))
        for line in lines
        if isinstance(line, dict) and "lineNumber" in line and "totalCharacters" in line
    )
    if lines:
        notice_characters += 2 + max(0, len(lines) - 1)
    return notice_characters


def parse_read_long_lines_telemetry(
    records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize non-context read-long-lines telemetry from one Pi session."""
    registered_events = 0
    preview_events: list[dict[str, Any]] = []
    shortened_lines = 0
    omitted_characters = 0
    notice_characters = 0
    for record in records:
        if record.get("type") != "custom":
            continue
        if record.get("customType") != "read-long-lines.telemetry":
            continue
        data = record.get("data")
        if not isinstance(data, dict) or data.get("schemaVersion") != 1:
            continue
        if data.get("event") == "registered":
            registered_events += 1
            continue
        if data.get("event") != "previewed":
            continue
        preview_events.append(data)
        lines = data.get("shortenedLines")
        if not isinstance(lines, list):
            lines = []
        shortened_lines += len(lines)
        omitted_characters += int(data.get("omittedCharacters", 0))
        notice_characters += preview_event_notice_characters(data)
    return {
        "registered_events": registered_events,
        "preview_events": len(preview_events),
        "shortened_lines": shortened_lines,
        "omitted_characters": omitted_characters,
        "notice_characters": notice_characters,
        "net_characters_saved": omitted_characters - notice_characters,
        "events": preview_events,
    }


def summarize_usage_through_first_mutation(
    records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Sum native session usage through the first explicit edit or write call.

    The mutation-decision assistant message is included because its provider request and
    generated tool call are consumed before the mutation tool executes.
    """
    usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
    }
    native_to_report_fields = {
        "input": "input_tokens",
        "output": "output_tokens",
        "cacheRead": "cache_read_tokens",
        "cacheWrite": "cache_write_tokens",
        "reasoning": "reasoning_tokens",
        "totalTokens": "total_tokens",
    }
    assistant_messages = 0
    first_mutation: dict[str, Any] | None = None
    for record in records:
        if record.get("type") != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        assistant_messages += 1
        native_usage = message.get("usage")
        if isinstance(native_usage, dict):
            for native_field, report_field in native_to_report_fields.items():
                usage[report_field] += int(native_usage.get(native_field, 0) or 0)
            cost = native_usage.get("cost")
            if isinstance(cost, dict):
                usage["cost_usd"] += float(cost.get("total", 0) or 0)
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "toolCall":
                continue
            if block.get("name") not in {"edit", "write"}:
                continue
            arguments = block.get("arguments")
            if not isinstance(arguments, dict):
                arguments = {}
            first_mutation = {
                "tool": str(block.get("name")),
                "tool_call_id": str(block.get("id", "")),
                "path": str(arguments.get("path", "")),
            }
            break
        if first_mutation is not None:
            break
    return {
        "boundary_found": first_mutation is not None,
        "first_mutation_tool": first_mutation["tool"] if first_mutation else None,
        "first_mutation_tool_call_id": (
            first_mutation["tool_call_id"] if first_mutation else None
        ),
        "first_mutation_path": first_mutation["path"] if first_mutation else None,
        "first_mutation_turn": assistant_messages if first_mutation else None,
        "assistant_messages": assistant_messages,
        "usage": usage,
    }


def normalize_read_path(path: Any) -> str:
    """Normalize task-root read paths so `/app/src/x` matches `src/x`."""
    normalized = str(path or "").replace("\\", "/")
    if normalized.startswith("/app/"):
        normalized = normalized.removeprefix("/app/")
    return normalized.removeprefix("./")


def extract_read_tool_exchanges(
    records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Pair each read tool call with its persisted text result."""
    calls: dict[str, dict[str, Any]] = {}
    exchanges: list[dict[str, Any]] = []
    assistant_turn = 0
    for record in records:
        if record.get("type") != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        if message.get("role") == "assistant":
            assistant_turn += 1
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if (
                    not isinstance(block, dict)
                    or block.get("type") != "toolCall"
                    or block.get("name") != "read"
                ):
                    continue
                arguments = block.get("arguments")
                if not isinstance(arguments, dict):
                    arguments = {}
                tool_call_id = str(block.get("id", ""))
                calls[tool_call_id] = {
                    "tool_call_id": tool_call_id,
                    "assistant_turn": assistant_turn,
                    "path": str(arguments.get("path", "")),
                    "normalized_path": normalize_read_path(arguments.get("path")),
                    "offset": int(arguments.get("offset", 1) or 1),
                    "limit": (
                        int(arguments["limit"])
                        if arguments.get("limit") is not None
                        else None
                    ),
                }
            continue
        if message.get("role") != "toolResult" or message.get("toolName") != "read":
            continue
        tool_call_id = str(message.get("toolCallId", ""))
        call = calls.get(tool_call_id)
        if call is None:
            continue
        content = message.get("content")
        if not isinstance(content, list):
            content = []
        text = "\n".join(
            str(block.get("text", ""))
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
        exchanges.append(
            {
                **call,
                "result_characters": len(text),
                "is_error": message.get("isError") is True,
            }
        )
    return exchanges


def compare_activated_read_results(
    baseline_records: Iterable[dict[str, Any]],
    extension_records: Iterable[dict[str, Any]],
    telemetry: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare each activated read with its own and paired-baseline counterfactual."""
    baseline_reads = extract_read_tool_exchanges(baseline_records)
    extension_reads = extract_read_tool_exchanges(extension_records)
    extension_by_id = {read["tool_call_id"]: read for read in extension_reads}
    comparisons = []
    for event in telemetry.get("events", []):
        if not isinstance(event, dict):
            continue
        extension_read = extension_by_id.get(str(event.get("toolCallId", "")))
        if extension_read is None:
            raise ValueError(
                "Read long-lines report previewed read result missing: "
                f"{event.get('toolCallId', '')}"
            )
        same_path = [
            read
            for read in baseline_reads
            if read["normalized_path"] == extension_read["normalized_path"]
        ]
        exact = [
            read
            for read in same_path
            if read["offset"] == extension_read["offset"]
            and read["limit"] == extension_read["limit"]
        ]
        baseline_match = (
            "exact_arguments"
            if exact
            else "same_path_different_arguments"
            if same_path
            else "missing"
        )
        matched_baseline = exact[0] if exact else None
        omitted_characters = int(event.get("omittedCharacters", 0) or 0)
        notice_characters = preview_event_notice_characters(event)
        net_characters_saved = omitted_characters - notice_characters
        extension_result_characters = int(extension_read["result_characters"])
        comparisons.append(
            {
                "tool_call_id": extension_read["tool_call_id"],
                "normalized_path": extension_read["normalized_path"],
                "offset": extension_read["offset"],
                "limit": extension_read["limit"],
                "extension_result_characters": extension_result_characters,
                "counterfactual_result_characters": (
                    extension_result_characters + net_characters_saved
                ),
                "omitted_characters": omitted_characters,
                "notice_characters": notice_characters,
                "net_characters_saved": net_characters_saved,
                "baseline_match": baseline_match,
                "baseline_result_characters": (
                    int(matched_baseline["result_characters"])
                    if matched_baseline is not None
                    else None
                ),
            }
        )
    return comparisons


def select_trajectory_packets(
    pairs: list[dict[str, Any]],
    *,
    partial_delta_threshold: float = PARTIAL_DELTA_PACKET_THRESHOLD,
) -> list[dict[str, Any]]:
    """Select solve flips, material partial shifts, and activated pairs."""
    selected = []
    for pair in pairs:
        baseline = pair["baseline"]
        extension = pair["extension"]
        binary_flip = baseline["reward_binary"] != extension["reward_binary"]
        partial_shift = (
            abs(extension["reward_partial"] - baseline["reward_partial"])
            >= partial_delta_threshold
        )
        activated = pair["telemetry"]["preview_events"] > 0
        if binary_flip or partial_shift or activated:
            selected.append(pair)
    return selected


def summarize_metric(pairs: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    """Summarize one numeric result metric across paired cells."""
    baseline_values = [float(pair["baseline"].get(metric, 0) or 0) for pair in pairs]
    extension_values = [float(pair["extension"].get(metric, 0) or 0) for pair in pairs]
    baseline_total = sum(baseline_values)
    extension_total = sum(extension_values)
    return {
        "baseline": baseline_total,
        "extension": extension_total,
        "delta": extension_total - baseline_total,
        "delta_fraction": (
            extension_total / baseline_total - 1 if baseline_total else None
        ),
        "baseline_mean": statistics.mean(baseline_values),
        "extension_mean": statistics.mean(extension_values),
        "baseline_median": statistics.median(baseline_values),
        "extension_median": statistics.median(extension_values),
        "paired_delta_median": statistics.median(
            right - left
            for left, right in zip(baseline_values, extension_values, strict=True)
        ),
    }


def summarize_pre_mutation_pairs(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate paired native usage through each arm's first source mutation."""
    if not pairs:
        return {"pairs": 0, "complete_boundaries": 0, "metrics": {}}
    complete = [
        pair
        for pair in pairs
        if pair["baseline_pre_mutation"]["boundary_found"]
        and pair["extension_pre_mutation"]["boundary_found"]
    ]
    metrics = {}
    for metric in (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
        "total_tokens",
        "cost_usd",
    ):
        baseline_values = [
            float(pair["baseline_pre_mutation"]["usage"][metric]) for pair in complete
        ]
        extension_values = [
            float(pair["extension_pre_mutation"]["usage"][metric]) for pair in complete
        ]
        baseline_total = sum(baseline_values)
        extension_total = sum(extension_values)
        paired_deltas = [
            right - left
            for left, right in zip(baseline_values, extension_values, strict=True)
        ]
        metrics[metric] = {
            "baseline": baseline_total,
            "extension": extension_total,
            "delta": extension_total - baseline_total,
            "delta_fraction": (
                extension_total / baseline_total - 1 if baseline_total else None
            ),
            "paired_delta_median": statistics.median(paired_deltas),
            "pairs_lower_with_extension": sum(delta < 0 for delta in paired_deltas),
            "pairs_higher_with_extension": sum(delta > 0 for delta in paired_deltas),
            "paired_deltas": paired_deltas,
        }
    baseline_context = sum(
        float(pair["baseline_pre_mutation"]["usage"]["input_tokens"])
        + float(pair["baseline_pre_mutation"]["usage"]["cache_read_tokens"])
        for pair in complete
    )
    extension_context = sum(
        float(pair["extension_pre_mutation"]["usage"]["input_tokens"])
        + float(pair["extension_pre_mutation"]["usage"]["cache_read_tokens"])
        for pair in complete
    )
    return {
        "pairs": len(pairs),
        "complete_boundaries": len(complete),
        "metrics": metrics,
        "context_input_tokens": {
            "baseline": baseline_context,
            "extension": extension_context,
            "delta": extension_context - baseline_context,
            "delta_fraction": (
                extension_context / baseline_context - 1 if baseline_context else None
            ),
        },
    }


def summarize_activated_read_results(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate direct activated-read payload reduction and baseline match quality."""
    comparisons = [
        comparison
        for pair in pairs
        for comparison in pair["activated_read_comparisons"]
    ]
    match_counts = collections.Counter(
        comparison["baseline_match"] for comparison in comparisons
    )
    extension_characters = sum(
        comparison["extension_result_characters"] for comparison in comparisons
    )
    counterfactual_characters = sum(
        comparison["counterfactual_result_characters"] for comparison in comparisons
    )
    exact = [
        comparison
        for comparison in comparisons
        if comparison["baseline_match"] == "exact_arguments"
    ]
    exact_baseline_characters = sum(
        int(comparison["baseline_result_characters"] or 0) for comparison in exact
    )
    exact_extension_characters = sum(
        comparison["extension_result_characters"] for comparison in exact
    )
    return {
        "activated_reads": len(comparisons),
        "baseline_match_counts": dict(match_counts),
        "extension_result_characters": extension_characters,
        "counterfactual_result_characters": counterfactual_characters,
        "net_characters_saved": counterfactual_characters - extension_characters,
        "reduction_fraction": (
            extension_characters / counterfactual_characters - 1
            if counterfactual_characters
            else None
        ),
        "exact_baseline_matches": len(exact),
        "exact_baseline_result_characters": exact_baseline_characters,
        "exact_extension_result_characters": exact_extension_characters,
        "exact_baseline_delta_characters": (
            exact_extension_characters - exact_baseline_characters
        ),
    }


def exact_sign_test_p(baseline_only: int, extension_only: int) -> float:
    """Return the two-sided exact sign-test p-value for binary discordance."""
    discordant = baseline_only + extension_only
    if not discordant:
        return 1.0
    tail = min(baseline_only, extension_only)
    return min(
        1.0,
        2
        * sum(math.comb(discordant, index) for index in range(tail + 1))
        / (2**discordant),
    )


def baseline_counterfactual_activated(pair: dict[str, Any]) -> bool:
    """Return whether stock Pi exposed an ordinary long read in one pair."""
    counterfactual = pair.get("baseline_counterfactual")
    if not isinstance(counterfactual, dict):
        return False
    return int(counterfactual.get("ordinary_long_read_results", 0)) > 0


def summarize_paired_results(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Separate net outcome changes, churn, efficiency, and mechanism delivery."""
    agreement = collections.Counter(
        (pair["baseline"]["reward_binary"], pair["extension"]["reward_binary"])
        for pair in pairs
    )
    metrics = {
        metric: summarize_metric(pairs, metric)
        for metric in (
            "reward_partial",
            "total_tokens",
            "input_tokens",
            "cache_read_tokens",
            "output_tokens",
            "agent_wall_s",
            "turns",
            "tool_calls",
            "cost_usd",
        )
    }
    activated = [pair for pair in pairs if pair["telemetry"]["preview_events"]]
    activated_tokens = (
        summarize_metric(activated, "total_tokens") if activated else None
    )
    baseline_f2p_passed = sum(
        pair["baseline"].get("f2p_passed", 0) or 0 for pair in pairs
    )
    baseline_f2p_total = sum(
        pair["baseline"].get("f2p_total", 0) or 0 for pair in pairs
    )
    extension_f2p_passed = sum(
        pair["extension"].get("f2p_passed", 0) or 0 for pair in pairs
    )
    extension_f2p_total = sum(
        pair["extension"].get("f2p_total", 0) or 0 for pair in pairs
    )
    baseline_p2p_passed = sum(
        pair["baseline"].get("p2p_passed", 0) or 0 for pair in pairs
    )
    baseline_p2p_total = sum(
        pair["baseline"].get("p2p_total", 0) or 0 for pair in pairs
    )
    extension_p2p_passed = sum(
        pair["extension"].get("p2p_passed", 0) or 0 for pair in pairs
    )
    extension_p2p_total = sum(
        pair["extension"].get("p2p_total", 0) or 0 for pair in pairs
    )
    summary = {
        "pairs": len(pairs),
        "trajectories": len(pairs) * 2,
        "baseline_solves": sum(pair["baseline"]["reward_binary"] for pair in pairs),
        "extension_solves": sum(pair["extension"]["reward_binary"] for pair in pairs),
        "both_solved": agreement[(1, 1)],
        "baseline_only_solved": agreement[(1, 0)],
        "extension_only_solved": agreement[(0, 1)],
        "neither_solved": agreement[(0, 0)],
        "sign_test_p": exact_sign_test_p(agreement[(1, 0)], agreement[(0, 1)]),
        "discordant_pairs": agreement[(1, 0)] + agreement[(0, 1)],
        "activated_solve_flips": sum(
            pair["telemetry"]["preview_events"] > 0
            and pair["baseline"]["reward_binary"] != pair["extension"]["reward_binary"]
            for pair in pairs
        ),
        "activated_pairs": len(activated),
        "registered_pairs": sum(
            pair["telemetry"].get("registered_events", 0) == 1 for pair in pairs
        ),
        "preview_events": sum(pair["telemetry"]["preview_events"] for pair in pairs),
        "shortened_lines": sum(
            pair["telemetry"].get("shortened_lines", 0) for pair in pairs
        ),
        "omitted_characters": sum(
            pair["telemetry"]["omitted_characters"] for pair in pairs
        ),
        "net_characters_saved": sum(
            pair["telemetry"]["net_characters_saved"] for pair in pairs
        ),
        "focused_recovery_reads": sum(
            pair.get("focused_recovery_reads", 0) for pair in pairs
        ),
        "baseline_counterfactual_activated_pairs": sum(
            baseline_counterfactual_activated(pair) for pair in pairs
        ),
        "activated_total_tokens": activated_tokens,
        "f2p": {
            "baseline_passed": baseline_f2p_passed,
            "baseline_total": baseline_f2p_total,
            "extension_passed": extension_f2p_passed,
            "extension_total": extension_f2p_total,
        },
        "p2p": {
            "baseline_passed": baseline_p2p_passed,
            "baseline_total": baseline_p2p_total,
            "extension_passed": extension_p2p_passed,
            "extension_total": extension_p2p_total,
        },
        "timeouts": {
            "baseline": sum(
                bool(pair["baseline"].get("agent_timed_out")) for pair in pairs
            ),
            "extension": sum(
                bool(pair["extension"].get("agent_timed_out")) for pair in pairs
            ),
        },
        "nonzero_agent_exits": {
            "baseline": sum(pair["baseline"].get("agent_exit") != 0 for pair in pairs),
            "extension": sum(
                pair["extension"].get("agent_exit") != 0 for pair in pairs
            ),
        },
        **metrics,
    }
    return summary


def load_python_module(name: str, path: Path) -> Any:
    """Load one repository helper from a non-package analysis directory."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Read long-lines report module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_session_records(
    cell_root: Path, newest_root_session: Any
) -> tuple[Path, list[dict[str, Any]]]:
    """Load valid records from the newest root Pi session for one result cell."""
    session_path = newest_root_session(cell_root / "session")
    if session_path is None:
        raise ValueError(f"Read long-lines report session missing: {cell_root}")
    records = []
    for raw in session_path.read_text(errors="replace").splitlines():
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return session_path, records


def summarize_session_tools(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract a compact tool timeline, read recovery count, and error causes."""
    calls: list[dict[str, Any]] = []
    call_by_id: dict[str, dict[str, Any]] = {}
    errors = collections.Counter()
    by_tool_errors = collections.Counter()
    by_tool_results = collections.Counter()
    assistant_turn = 0
    event_index = 0
    for record in records:
        if record.get("type") != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        if message.get("role") == "assistant":
            assistant_turn += 1
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "toolCall":
                    continue
                event_index += 1
                arguments = block.get("arguments")
                if not isinstance(arguments, dict):
                    arguments = {}
                event = {
                    "event": event_index,
                    "turn": assistant_turn,
                    "tool": str(block.get("name", "unknown")),
                    "tool_call_id": str(block.get("id", "")),
                    "path": arguments.get("path", ""),
                    "offset": arguments.get("offset", ""),
                    "limit": arguments.get("limit", ""),
                }
                if event["tool"] == "bash":
                    command = str(arguments.get("command", ""))
                    event["command"] = command[:240]
                calls.append(event)
                call_by_id[event["tool_call_id"]] = event
            continue
        if message.get("role") != "toolResult":
            continue
        tool = str(message.get("toolName", "unknown"))
        by_tool_results[tool] += 1
        if message.get("isError") is not True:
            continue
        by_tool_errors[tool] += 1
        text = "\n".join(
            str(block.get("text", ""))
            for block in (message.get("content") or [])
            if isinstance(block, dict) and block.get("type") == "text"
        ).lower()
        if tool == "edit" and any(
            phrase in text
            for phrase in (
                "could not find the exact text",
                "must be unique",
                "did not match",
            )
        ):
            errors["edit target text did not match"] += 1
        elif tool == "edit" and "validation failed for tool" in text:
            errors["malformed edit arguments"] += 1
        elif tool == "bash":
            errors["shell command returned nonzero"] += 1
        elif tool == "read":
            errors["read request failed"] += 1
        else:
            errors[f"other {tool} failure"] += 1
        call = call_by_id.get(str(message.get("toolCallId", "")))
        if call is not None:
            call["failed"] = True
    return {
        "assistant_turns": assistant_turn,
        "tool_calls": calls,
        "tool_counts": dict(collections.Counter(call["tool"] for call in calls)),
        "tool_results": sum(by_tool_results.values()),
        "tool_errors": sum(by_tool_errors.values()),
        "by_tool_results": dict(by_tool_results),
        "by_tool_errors": dict(by_tool_errors),
        "error_categories": dict(errors),
    }


def focused_recovery_read_count(
    tool_summary: dict[str, Any], telemetry: dict[str, Any]
) -> int:
    """Count focused offset/limit=1 reads after a preview of the same path."""
    preview_by_call = {
        str(event.get("toolCallId", "")): event for event in telemetry["events"]
    }
    calls = tool_summary["tool_calls"]
    call_positions = {call["tool_call_id"]: index for index, call in enumerate(calls)}
    recoveries = 0
    for tool_call_id, event in preview_by_call.items():
        start = call_positions.get(tool_call_id, -1)
        path = event.get("path")
        line_numbers = {
            int(line["lineNumber"])
            for line in event.get("shortenedLines", [])
            if isinstance(line, dict) and "lineNumber" in line
        }
        for call in calls[start + 1 :]:
            if call["tool"] != "read" or call.get("path") != path:
                continue
            if call.get("limit") != 1:
                continue
            try:
                offset = int(call.get("offset"))
            except (TypeError, ValueError):
                continue
            if offset in line_numbers:
                recoveries += 1
    return recoveries


def parse_patch_summary(cell_root: Path) -> dict[str, Any]:
    """Summarize changed files and line counts from one saved model patch."""
    patch_path = cell_root / "artifacts" / "model.patch"
    patch = patch_path.read_text(errors="replace") if patch_path.is_file() else ""
    changed_files = []
    added = deleted = 0
    for line in patch.splitlines():
        if line.startswith("diff --git a/"):
            changed_files.append(line.split(" b/", 1)[0].removeprefix("diff --git a/"))
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            deleted += 1
    return {
        "path": str(patch_path),
        "bytes": len(patch.encode()),
        "changed_files": list(dict.fromkeys(changed_files)),
        "added_lines": added,
        "deleted_lines": deleted,
    }


def parse_verifier_failures(cell_root: Path) -> list[str]:
    """Return failed CTRF test names without copying verbose failure payloads."""
    path = cell_root / "verifier" / "ctrf.json"
    if not path.is_file():
        return []
    document = json.loads(path.read_text())
    results = document.get("results")
    if not isinstance(results, dict):
        return []
    tests = results.get("tests", [])
    return [
        str(test.get("name", "unknown"))
        for test in tests
        if isinstance(test, dict) and test.get("status") == "failed"
    ]


def first_tool_divergence(
    baseline_tools: dict[str, Any], extension_tools: dict[str, Any]
) -> dict[str, Any]:
    """Find the first differing tool choice in two compact timelines."""
    left = baseline_tools["tool_calls"]
    right = extension_tools["tool_calls"]
    for index, (left_event, right_event) in enumerate(
        zip(left, right, strict=False), 1
    ):
        left_key = (left_event["tool"], left_event.get("path", ""))
        right_key = (right_event["tool"], right_event.get("path", ""))
        if left_key != right_key:
            return {"event": index, "baseline": left_key, "extension": right_key}
    if len(left) != len(right):
        return {
            "event": min(len(left), len(right)) + 1,
            "baseline": "timeline ended" if len(left) < len(right) else "continued",
            "extension": "timeline ended" if len(right) < len(left) else "continued",
        }
    return {
        "event": None,
        "baseline": "same tool sequence",
        "extension": "same tool sequence",
    }


def load_pilot_pairs(results_root: Path, model_keys: list[str]) -> list[dict[str, Any]]:
    """Load and validate exact task/rep pairs for the requested model cohort."""
    incidence = load_python_module(
        "read_long_lines_incidence",
        REPOSITORY_ROOT / "analysis/read-long-lines-incidence/scan_read_long_lines.py",
    )
    pairs = []
    for model_key in model_keys:
        spec = MODEL_SPECS[model_key]
        model_root = results_root / spec["model_leaf"] / spec["thinking"]
        for task in TASKS:
            for rep in REPS:
                baseline_root = (
                    model_root / spec["baseline_config"] / task / f"rep{rep}"
                )
                extension_root = model_root / EXTENSION_CONFIG / task / f"rep{rep}"
                baseline_path = baseline_root / "result.json"
                extension_path = extension_root / "result.json"
                if not baseline_path.is_file() or not extension_path.is_file():
                    raise ValueError(
                        "Read long-lines report pair incomplete: "
                        f"model={model_key} task={task} rep={rep}"
                    )
                baseline = json.loads(baseline_path.read_text())
                extension = json.loads(extension_path.read_text())
                if (
                    baseline["model"] != spec["model"]
                    or extension["model"] != spec["model"]
                ):
                    raise ValueError(
                        f"Read long-lines report model mismatch: {model_key}/{task}/rep{rep}"
                    )
                if (
                    baseline["thinking_level"] != spec["thinking"]
                    or extension["thinking_level"] != spec["thinking"]
                ):
                    raise ValueError(
                        f"Read long-lines report thinking mismatch: {model_key}/{task}/rep{rep}"
                    )
                for key in (
                    "subject_version",
                    "harness_revision",
                    "task_revision",
                    "immutable_image_identities",
                    "resource_policy",
                    "arm_settings",
                ):
                    if baseline.get(key) != extension.get(key):
                        raise ValueError(
                            f"Read long-lines report provenance mismatch: {model_key}/{task}/rep{rep}/{key}"
                        )
                if baseline.get("arm_pi_flags") not in (None, []):
                    raise ValueError(
                        f"Read long-lines report baseline flags leaked: {model_key}/{task}/rep{rep}"
                    )
                if extension.get("arm_pi_flags") != [
                    "-e",
                    "/arm/extensions/read-long-lines.ts",
                ]:
                    raise ValueError(
                        f"Read long-lines report extension flags missing: {model_key}/{task}/rep{rep}"
                    )
                for prompt_field in (
                    "system_preamble_chars",
                    "orchestration_chars",
                    "append_system_prompt_chars",
                ):
                    if (
                        baseline.get(prompt_field) != 0
                        or extension.get(prompt_field) != 0
                    ):
                        raise ValueError(
                            "Read long-lines report config prompt text detected: "
                            f"{model_key}/{task}/rep{rep}/{prompt_field}"
                        )
                _, baseline_records = load_session_records(
                    baseline_root, incidence.newest_root_session
                )
                extension_session_path, extension_records = load_session_records(
                    extension_root, incidence.newest_root_session
                )
                baseline_tools = summarize_session_tools(baseline_records)
                extension_tools = summarize_session_tools(extension_records)
                telemetry = parse_read_long_lines_telemetry(extension_records)
                baseline_pre_mutation = summarize_usage_through_first_mutation(
                    baseline_records
                )
                extension_pre_mutation = summarize_usage_through_first_mutation(
                    extension_records
                )
                activated_read_comparisons = compare_activated_read_results(
                    baseline_records, extension_records, telemetry
                )
                if telemetry["registered_events"] != 1:
                    raise ValueError(
                        "Read long-lines report delivery marker invalid: "
                        f"model={model_key} task={task} rep={rep} markers={telemetry['registered_events']}"
                    )
                baseline_counterfactual, _, _ = incidence.scan_rep(baseline_path)
                pair_id = f"{model_key}--{task}--rep{rep}"
                pair = {
                    "pair_id": pair_id,
                    "model_key": model_key,
                    "model_label": spec["label"],
                    "model": spec["model"],
                    "thinking": spec["thinking"],
                    "task": task,
                    "rep": rep,
                    "baseline_config": spec["baseline_config"],
                    "extension_config": EXTENSION_CONFIG,
                    "baseline": baseline,
                    "extension": extension,
                    "baseline_root": str(baseline_root),
                    "extension_root": str(extension_root),
                    "extension_session": str(extension_session_path),
                    "baseline_counterfactual": baseline_counterfactual,
                    "telemetry": telemetry,
                    "activated_read_comparisons": activated_read_comparisons,
                    "baseline_pre_mutation": baseline_pre_mutation,
                    "extension_pre_mutation": extension_pre_mutation,
                    "baseline_tools": baseline_tools,
                    "extension_tools": extension_tools,
                    "focused_recovery_reads": focused_recovery_read_count(
                        extension_tools, telemetry
                    ),
                }
                pairs.append(pair)
    return pairs


def compact_read_long_lines_result(result: dict[str, Any]) -> dict[str, Any]:
    """Keep report-facing result fields and provenance without raw prompts."""
    fields = (
        "reward_binary",
        "reward_partial",
        "f2p",
        "f2p_passed",
        "f2p_total",
        "p2p",
        "p2p_passed",
        "p2p_total",
        "total_tokens",
        "input_tokens",
        "cache_read_tokens",
        "output_tokens",
        "cost_usd",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_timed_out",
        "agent_exit",
        "verifier_exit",
        "config_lock_identity",
        "launch_plan_identity",
        "harness_revision",
        "task_revision",
        "subject_version",
    )
    return {field: result.get(field) for field in fields}


def compact_pair(pair: dict[str, Any]) -> dict[str, Any]:
    """Convert one loaded pair to a durable report snapshot row."""
    return {
        key: pair[key]
        for key in (
            "pair_id",
            "model_key",
            "model_label",
            "model",
            "thinking",
            "task",
            "rep",
            "baseline_config",
            "extension_config",
            "focused_recovery_reads",
        )
    } | {
        "baseline": compact_read_long_lines_result(pair["baseline"]),
        "extension": compact_read_long_lines_result(pair["extension"]),
        "baseline_counterfactual": {
            key: pair["baseline_counterfactual"][key]
            for key in (
                "read_results",
                "ordinary_long_read_results",
                "ordinary_long_lines",
                "omitted_characters",
                "notice_characters",
                "net_characters_saved",
            )
        },
        "telemetry": pair["telemetry"],
        "activated_read_comparisons": pair["activated_read_comparisons"],
        "pre_mutation": {
            "baseline": pair["baseline_pre_mutation"],
            "extension": pair["extension_pre_mutation"],
        },
        "baseline_tool_errors": {
            key: pair["baseline_tools"][key]
            for key in (
                "tool_results",
                "tool_errors",
                "by_tool_errors",
                "error_categories",
            )
        },
        "extension_tool_errors": {
            key: pair["extension_tools"][key]
            for key in (
                "tool_results",
                "tool_errors",
                "by_tool_errors",
                "error_categories",
            )
        },
    }


def packet_trigger_labels(pair: dict[str, Any]) -> list[str]:
    """Name every predeclared reason one trajectory pair entered packet review."""
    labels = []
    if pair["baseline"]["reward_binary"] != pair["extension"]["reward_binary"]:
        labels.append("binary solve flip")
    if (
        abs(pair["extension"]["reward_partial"] - pair["baseline"]["reward_partial"])
        >= PARTIAL_DELTA_PACKET_THRESHOLD
    ):
        labels.append("material partial shift")
    if pair["telemetry"]["preview_events"]:
        labels.append("mechanism activated")
    return labels


def build_trajectory_packet(pair: dict[str, Any]) -> dict[str, Any]:
    """Build a reviewable paired packet without raw model reasoning or tool payloads."""
    baseline_root = Path(pair["baseline_root"])
    extension_root = Path(pair["extension_root"])
    baseline_patch = parse_patch_summary(baseline_root)
    extension_patch = parse_patch_summary(extension_root)
    baseline_failed_tests = parse_verifier_failures(baseline_root)
    extension_failed_tests = parse_verifier_failures(extension_root)
    activated = pair["telemetry"]["preview_events"] > 0
    binary_changed = (
        pair["baseline"]["reward_binary"] != pair["extension"]["reward_binary"]
    )
    if not activated:
        driver = "likely variance"
        mechanism = (
            "The extension loaded, but no line was shortened. The tool description was "
            "visible, so a behavioral effect is possible, but direct context removal cannot "
            "explain this pair."
        )
    elif binary_changed:
        driver = "likely variance"
        mechanism = (
            "Shortening occurred before a solve flip, but this single trajectory does not "
            "separate context protection from ordinary trajectory variance."
        )
    else:
        driver = "likely variance"
        mechanism = (
            "Shortening removed context, but binary outcome was stable and observed token "
            "movement remained trajectory-dependent."
        )
    divergence = first_tool_divergence(pair["baseline_tools"], pair["extension_tools"])
    return {
        "pair_id": pair["pair_id"],
        "model": pair["model_label"],
        "thinking": pair["thinking"],
        "task": pair["task"],
        "rep": pair["rep"],
        "triggers": packet_trigger_labels(pair),
        "baseline": compact_read_long_lines_result(pair["baseline"]),
        "extension": compact_read_long_lines_result(pair["extension"]),
        "telemetry": pair["telemetry"],
        "activated_read_comparisons": pair["activated_read_comparisons"],
        "pre_mutation": {
            "baseline": pair["baseline_pre_mutation"],
            "extension": pair["extension_pre_mutation"],
            "total_token_delta": (
                pair["extension_pre_mutation"]["usage"]["total_tokens"]
                - pair["baseline_pre_mutation"]["usage"]["total_tokens"]
            ),
        },
        "focused_recovery_reads": pair["focused_recovery_reads"],
        "token_delta": pair["extension"]["total_tokens"]
        - pair["baseline"]["total_tokens"],
        "partial_delta": pair["extension"]["reward_partial"]
        - pair["baseline"]["reward_partial"],
        "patches": {"baseline": baseline_patch, "extension": extension_patch},
        "failed_tests": {
            "baseline": baseline_failed_tests,
            "extension": extension_failed_tests,
        },
        "tool_results": {
            "baseline": {
                key: pair["baseline_tools"][key]
                for key in (
                    "tool_counts",
                    "tool_results",
                    "tool_errors",
                    "error_categories",
                )
            },
            "extension": {
                key: pair["extension_tools"][key]
                for key in (
                    "tool_counts",
                    "tool_results",
                    "tool_errors",
                    "error_categories",
                )
            },
        },
        "stage_ledger": {
            "initialization": {
                "baseline_first_tool": pair["baseline_tools"]["tool_calls"][:1],
                "extension_first_tool": pair["extension_tools"]["tool_calls"][:1],
            },
            "first_tool_divergence": divergence,
            "implementation": {
                "baseline_changed_files": baseline_patch["changed_files"],
                "extension_changed_files": extension_patch["changed_files"],
            },
            "validation": {
                "baseline_failed_tests": baseline_failed_tests,
                "extension_failed_tests": extension_failed_tests,
            },
            "termination": {
                "baseline_agent_exit": pair["baseline"].get("agent_exit"),
                "extension_agent_exit": pair["extension"].get("agent_exit"),
                "baseline_timeout": pair["baseline"].get("agent_timed_out"),
                "extension_timeout": pair["extension"].get("agent_timed_out"),
            },
        },
        "classification": {
            "primary_driver": driver,
            "mechanism": mechanism,
            "confidence": "low" if binary_changed else "medium",
        },
    }


def aggregate_tool_errors(pairs: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    """Aggregate tool-result errors by tool and cause for one comparison arm."""
    summary = collections.Counter()
    by_tool = collections.Counter()
    results = errors = 0
    key = f"{arm}_tools"
    for pair in pairs:
        tools = pair[key]
        results += tools["tool_results"]
        errors += tools["tool_errors"]
        summary.update(tools["error_categories"])
        by_tool.update(tools["by_tool_errors"])
    return {
        "tool_results": results,
        "tool_errors": errors,
        "error_rate": errors / results if results else 0,
        "by_tool_errors": dict(by_tool),
        "error_categories": dict(summary),
    }


def build_snapshot(
    pairs: list[dict[str, Any]], model_keys: list[str]
) -> dict[str, Any]:
    """Build the versioned data contract consumed by HTML and later supplements."""
    model_summaries = {}
    for model_key in model_keys:
        model_pairs = [pair for pair in pairs if pair["model_key"] == model_key]
        model_summaries[model_key] = summarize_paired_results(model_pairs)
    task_summaries = {}
    for task in TASKS:
        task_pairs = [pair for pair in pairs if pair["task"] == task]
        task_summaries[task] = summarize_paired_results(task_pairs)
    selected = select_trajectory_packets(pairs)
    activated_pairs = [pair for pair in pairs if pair["telemetry"]["preview_events"]]
    return {
        "schema_version": 1,
        "comparison": {
            "left": "stock Pi baseline",
            "right": EXTENSION_CONFIG,
            "tasks": list(TASKS),
            "reps": list(REPS),
            "model_keys": model_keys,
            "model_specs": {key: MODEL_SPECS[key] for key in model_keys},
            "deferred_models": [key for key in MODEL_SPECS if key not in model_keys],
            "partial_delta_packet_threshold": PARTIAL_DELTA_PACKET_THRESHOLD,
        },
        "summary": summarize_paired_results(pairs),
        "activated_read_results": summarize_activated_read_results(activated_pairs),
        "activated_pre_mutation": summarize_pre_mutation_pairs(activated_pairs),
        "by_model": model_summaries,
        "by_task": task_summaries,
        "tool_errors": {
            "baseline": aggregate_tool_errors(pairs, "baseline"),
            "extension": aggregate_tool_errors(pairs, "extension"),
        },
        "packet_ids": [pair["pair_id"] for pair in selected],
        "pairs": [compact_pair(pair) for pair in pairs],
    }


def percent_fraction(value: float | None, digits: int = 1, signed: bool = False) -> str:
    """Format a fractional value as a report percentage."""
    if value is None:
        return "n/a"
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value * 100:.{digits}f}%"


def outcome_label(pair: dict[str, Any]) -> tuple[str, str]:
    """Return the complete-table outcome label and CSS class."""
    left = pair["baseline"]["reward_binary"]
    right = pair["extension"]["reward_binary"]
    if left == right == 1:
        return "both solved", "good"
    if left == right == 0:
        return "neither solved", "neutral"
    if right == 1:
        return "extension only", "good"
    return "baseline only", "bad"


def render_report_html(snapshot: dict[str, Any]) -> str:
    """Render one self-contained Tailnet report from the durable snapshot."""
    summary = snapshot["summary"]
    pairs = snapshot["pairs"]
    model_keys = snapshot["comparison"]["model_keys"]
    tokens = summary["total_tokens"]
    partial = summary["reward_partial"]
    activated_tokens = summary["activated_total_tokens"]
    direct_reads = snapshot["activated_read_results"]
    pre_mutation = snapshot["activated_pre_mutation"]
    pre_mutation_tokens = pre_mutation["metrics"]["total_tokens"]
    pre_mutation_context = pre_mutation["context_input_tokens"]
    model_rows = []
    for key in model_keys:
        spec = MODEL_SPECS[key]
        row = snapshot["by_model"][key]
        model_rows.append(
            "<tr>"
            f"<td><strong>{html.escape(spec['label'])}</strong><br><span class='muted'>{spec['thinking']}</span></td>"
            f"<td class='num'>{row['activated_pairs']}/6</td>"
            f"<td class='num'>{row['baseline_solves']} → {row['extension_solves']}</td>"
            f"<td class='num'>{row['reward_partial']['baseline_mean']:.3f} → {row['reward_partial']['extension_mean']:.3f}</td>"
            f"<td class='num'>{percent_fraction(row['total_tokens']['delta_fraction'], signed=True)}</td>"
            f"<td class='num'>{percent_fraction(row['agent_wall_s']['delta_fraction'], signed=True)}</td>"
            "</tr>"
        )
    task_rows = []
    for task in TASKS:
        row = snapshot["by_task"][task]
        task_rows.append(
            "<tr>"
            f"<td class='mono'>{html.escape(task)}</td>"
            f"<td class='num'>{row['activated_pairs']}/{row['pairs']}</td>"
            f"<td class='num'>{row['baseline_counterfactual_activated_pairs']}/{row['pairs']}</td>"
            f"<td class='num'>{row['baseline_solves']} → {row['extension_solves']}</td>"
            f"<td class='num'>{row['reward_partial']['baseline_mean']:.3f} → {row['reward_partial']['extension_mean']:.3f}</td>"
            f"<td class='num'>{percent_fraction(row['total_tokens']['delta_fraction'], signed=True)}</td>"
            "</tr>"
        )
    pair_rows = []
    for pair in pairs:
        outcome, css = outcome_label(pair)
        activation = (
            f"{pair['telemetry']['net_characters_saved']:,} chars"
            if pair["telemetry"]["preview_events"]
            else "—"
        )
        pair_rows.append(
            "<tr>"
            f"<td>{html.escape(pair['model_label'])}</td>"
            f"<td class='mono'>{html.escape(pair['task'])}</td>"
            f"<td class='num'>{pair['rep']}</td>"
            f"<td class='num'>{activation}</td>"
            f"<td><span class='tag {css}'>{outcome}</span></td>"
            f"<td class='num'>{pair['extension']['reward_partial'] - pair['baseline']['reward_partial']:+.3f}</td>"
            f"<td class='num'>{pair['baseline']['total_tokens'] / 1e6:.2f}M → {pair['extension']['total_tokens'] / 1e6:.2f}M</td>"
            f"<td class='num'>{pair['extension']['total_tokens'] - pair['baseline']['total_tokens']:+,}</td>"
            "</tr>"
        )
    activated_rows = []
    baseline_match_labels = {
        "exact_arguments": "exact",
        "same_path_different_arguments": "different range",
        "missing": "not read",
    }
    for pair in pairs:
        if not pair["telemetry"]["preview_events"]:
            continue
        comparison = pair["activated_read_comparisons"][0]
        baseline_phase = pair["pre_mutation"]["baseline"]
        extension_phase = pair["pre_mutation"]["extension"]
        phase_delta = (
            extension_phase["usage"]["total_tokens"]
            - baseline_phase["usage"]["total_tokens"]
        )
        activated_rows.append(
            "<tr>"
            f"<td>{html.escape(pair['model_label'])}</td>"
            f"<td class='num'>rep{pair['rep']}</td>"
            f"<td>{baseline_match_labels[comparison['baseline_match']]}</td>"
            f"<td class='num'>{comparison['counterfactual_result_characters']:,} → {comparison['extension_result_characters']:,}</td>"
            f"<td class='num'>{baseline_phase['usage']['total_tokens']:,} → {extension_phase['usage']['total_tokens']:,}</td>"
            f"<td class='num'>{phase_delta:+,}</td>"
            f"<td class='num'>{baseline_phase['first_mutation_turn']} → {extension_phase['first_mutation_turn']}</td>"
            "</tr>"
        )
    packet_rows = []
    pair_by_id = {pair["pair_id"]: pair for pair in pairs}
    for packet_id in snapshot["packet_ids"]:
        pair = pair_by_id[packet_id]
        triggers = []
        if pair["baseline"]["reward_binary"] != pair["extension"]["reward_binary"]:
            triggers.append("solve flip")
        if (
            abs(
                pair["extension"]["reward_partial"] - pair["baseline"]["reward_partial"]
            )
            >= PARTIAL_DELTA_PACKET_THRESHOLD
        ):
            triggers.append("partial shift")
        if pair["telemetry"]["preview_events"]:
            triggers.append("activated")
        packet_rows.append(
            "<tr>"
            f"<td><a href='packets/{html.escape(packet_id)}.json'>{html.escape(packet_id)}</a></td>"
            f"<td>{', '.join(triggers)}</td>"
            f"<td class='num'>{pair['extension']['total_tokens'] - pair['baseline']['total_tokens']:+,}</td>"
            "</tr>"
        )
    baseline_errors = snapshot["tool_errors"]["baseline"]
    extension_errors = snapshot["tool_errors"]["extension"]
    f2p = summary["f2p"]
    p2p = summary["p2p"]
    baseline_f2p = f2p["baseline_passed"] / f2p["baseline_total"]
    extension_f2p = f2p["extension_passed"] / f2p["extension_total"]
    baseline_p2p = p2p["baseline_passed"] / p2p["baseline_total"]
    extension_p2p = p2p["extension_passed"] / p2p["extension_total"]
    activated_delta_text = (
        f"{activated_tokens['delta']:+,.0f} tokens ({percent_fraction(activated_tokens['delta_fraction'], signed=True)})"
        if activated_tokens
        else "n/a"
    )
    cohort_labels = ", ".join(MODEL_SPECS[key]["label"] for key in model_keys)
    deferred_keys = snapshot["comparison"]["deferred_models"]
    if deferred_keys:
        deferred_labels = ", ".join(MODEL_SPECS[key]["label"] for key in deferred_keys)
        staging_text = (
            f"This snapshot covers {cohort_labels}; {deferred_labels} remains deferred "
            "until its quota-bound run completes."
        )
        supplement_callout = (
            f"<strong>Staged report.</strong> {html.escape(deferred_labels)} is intentionally "
            "excluded until its paired plans finish. Regenerating with the completed model "
            "key will add it without changing metrics or packet triggers."
        )
    else:
        staging_text = f"This final snapshot covers {cohort_labels}."
        supplement_callout = "<strong>Complete cohort.</strong> All configured pilot model leaves are included."
    abs_summary = snapshot["by_task"]["abs-module-cache-flags"]
    css = (REPORT_DIR / "report.css").read_text()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>Read long lines · staged DeepSWE pilot</title><style>{css}</style></head><body><div class="wrap">
<header class="hero">
<span class="eyebrow">Activated-read analysis · same-model config control · staged pilot</span>
<h1>Reads got smaller. Pre-mutation tokens did not.</h1>
<p class="subtitle">The primary cohort is the {summary["activated_pairs"]} pairs where <code>read-long-lines@1.0.0</code> actually shortened a result. Usage is measured only through the first explicit <code>edit</code> or <code>write</code> call. {html.escape(staging_text)}</p>
<div class="pillrow"><span class="pill caution">activation {summary["activated_pairs"]}/{summary["pairs"]}</span><span class="pill good">read payload {percent_fraction(direct_reads["reduction_fraction"])}</span><span class="pill caution">pre-mutation tokens {percent_fraction(pre_mutation_tokens["delta_fraction"], signed=True)}</span><span class="pill neutral">whole session {percent_fraction(activated_tokens["delta_fraction"], signed=True)}</span></div>
<div class="stats">
<div class="stat"><span class="label">Activated pairs</span><span class="value">{summary["activated_pairs"]}</span><span class="sub">of {summary["pairs"]} matched pairs</span></div>
<div class="stat"><span class="label">Read-result payload</span><span class="value">{direct_reads["counterfactual_result_characters"]:,} → {direct_reads["extension_result_characters"]:,}</span><span class="sub good">{direct_reads["net_characters_saved"]:,} characters removed</span></div>
<div class="stat"><span class="label">Exact baseline reads</span><span class="value">{direct_reads["exact_baseline_matches"]}/{direct_reads["activated_reads"]}</span><span class="sub">same path, offset, and limit</span></div>
<div class="stat"><span class="label">Pre-mutation tokens</span><span class="value">{pre_mutation_tokens["baseline"] / 1e6:.3f}M → {pre_mutation_tokens["extension"] / 1e6:.3f}M</span><span class="sub caution">{pre_mutation_tokens["delta"]:+,.0f} · {percent_fraction(pre_mutation_tokens["delta_fraction"], signed=True)}</span></div>
<div class="stat"><span class="label">Input + cache read</span><span class="value">{pre_mutation_context["baseline"] / 1e6:.3f}M → {pre_mutation_context["extension"] / 1e6:.3f}M</span><span class="sub caution">{pre_mutation_context["delta"]:+,.0f} · {percent_fraction(pre_mutation_context["delta_fraction"], signed=True)}</span></div>
</div></header>
<section><div class="section-head"><div><h2>Direct answer</h2><p>Separate the tool-result payload from the exploration phase and from the later implementation trajectory.</p></div></div>
<div class="callout good"><strong>At the read boundary: yes.</strong> The five activated results shrank from a reconstructed {direct_reads["counterfactual_result_characters"]:,} to {direct_reads["extension_result_characters"]:,} characters, a {percent_fraction(direct_reads["reduction_fraction"])} reduction after notice overhead. Three exact Flash baseline matches independently confirm {direct_reads["exact_baseline_result_characters"]:,} → {direct_reads["exact_extension_result_characters"]:,} characters.</div>
<div class="callout caution"><strong>Through first mutation: no aggregate token saving.</strong> Native executor usage moved {pre_mutation_tokens["baseline"]:,.0f} → {pre_mutation_tokens["extension"]:,.0f}, or {pre_mutation_tokens["delta"]:+,.0f} ({percent_fraction(pre_mutation_tokens["delta_fraction"], signed=True)}). The extension was lower in {pre_mutation_tokens["pairs_lower_with_extension"]}/5 pairs and higher in {pre_mutation_tokens["pairs_higher_with_extension"]}/5; the paired median was {pre_mutation_tokens["paired_delta_median"]:+,.0f} tokens.</div>
<div class="callout"><strong>The context-bearing portion also rose slightly.</strong> Input plus cache-read usage through first mutation moved {pre_mutation_context["baseline"]:,.0f} → {pre_mutation_context["extension"]:,.0f}, or {percent_fraction(pre_mutation_context["delta_fraction"], signed=True)}. This phase boundary includes the assistant message that generates the first mutation call because those tokens are consumed before the tool executes.</div>
<div class="callout good"><strong>No recovery penalty observed.</strong> Models made {summary["focused_recovery_reads"]} focused <code>offset=N, limit=1</code> recovery reads after previews.</div>
</section>
<section><div class="section-head"><div><h2>Per-model comparison</h2><p>Heterogeneous token movement with zero activation in Terra and Luna is direct evidence that aggregate deltas are dominated by trajectory churn.</p></div></div><div class="table-wrap"><table><thead><tr><th>Model</th><th class="num">Activated</th><th class="num">Solves B → E</th><th class="num">Mean partial B → E</th><th class="num">Token Δ</th><th class="num">Wall Δ</th></tr></thead><tbody>{"".join(model_rows)}</tbody></table></div></section>
<section><div class="section-head"><div><h2>Task split</h2><p>The two targeted tasks behaved differently. Baseline exposure is a counterfactual scan of stock read results; treatment activation is extension telemetry.</p></div></div><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Treatment activated</th><th class="num">Baseline exposed</th><th class="num">Solves B → E</th><th class="num">Mean partial B → E</th><th class="num">Token Δ</th></tr></thead><tbody>{"".join(task_rows)}</tbody></table></div><div class="callout caution"><strong><code>abs-module-cache-flags</code> did not test the mechanism.</strong> It activated 0/{len(model_keys) * 3}, moved solves {abs_summary["baseline_solves"]} → {abs_summary["extension_solves"]}, and used {percent_fraction(abs_summary["total_tokens"]["delta_fraction"], signed=True)} tokens. Those changes cannot be direct context-removal effects.</div></section>
<section><div class="section-head"><div><h2>Activated reads through first mutation</h2><p>Every activation shortened the same two lines in <code>fd-deterministic-multi-key-sorting/src/main.rs</code> by 1,559 net characters. “Exact” means the paired baseline used the same normalized path, offset, and limit; other payload counterfactuals are reconstructed from treatment telemetry.</p></div></div><div class="table-wrap"><table><thead><tr><th>Model</th><th class="num">Rep</th><th>Baseline read</th><th class="num">Read chars no extension → extension</th><th class="num">Pre-mutation tokens B → E</th><th class="num">Phase Δ</th><th class="num">First mutation turn B → E</th></tr></thead><tbody>{"".join(activated_rows)}</tbody></table></div><div class="callout"><strong>Match coverage:</strong> {direct_reads["baseline_match_counts"].get("exact_arguments", 0)} exact, {direct_reads["baseline_match_counts"].get("same_path_different_arguments", 0)} same file with a different range, and {direct_reads["baseline_match_counts"].get("missing", 0)} paired baseline that never read the file.</div></section>
<div class="grid-2"><section><div class="section-head"><div><h2>Outcome churn</h2><p>Net solves hide {summary["discordant_pairs"]} discordant pairs and lower mean partial reward.</p></div></div><div class="grid-4"><div class="mini"><span class="big good-text">{summary["both_solved"]}</span><span class="cap">both solved</span></div><div class="mini"><span class="big bad-text">{summary["baseline_only_solved"]}</span><span class="cap">baseline only</span></div><div class="mini"><span class="big good-text">{summary["extension_only_solved"]}</span><span class="cap">extension only</span></div><div class="mini"><span class="big neutral-text">{summary["neither_solved"]}</span><span class="cap">neither</span></div></div><div class="callout"><strong>Binary {summary["extension_solves"] - summary["baseline_solves"]:+d}, partial {(partial["extension_mean"] - partial["baseline_mean"]) * 100:+.1f} points.</strong> {summary["activated_solve_flips"]} of {summary["discordant_pairs"]} solve flips activated shortening, so the mechanism does not explain the net solve delta.</div><div class="table-wrap"><table><thead><tr><th>Grading</th><th class="num">Baseline</th><th class="num">Extension</th></tr></thead><tbody><tr><td>F2P</td><td class="num">{f2p["baseline_passed"]}/{f2p["baseline_total"]} · {percent_fraction(baseline_f2p)}</td><td class="num">{f2p["extension_passed"]}/{f2p["extension_total"]} · {percent_fraction(extension_f2p)}</td></tr><tr><td>P2P</td><td class="num">{p2p["baseline_passed"]}/{p2p["baseline_total"]} · {percent_fraction(baseline_p2p)}</td><td class="num">{p2p["extension_passed"]}/{p2p["extension_total"]} · {percent_fraction(extension_p2p)}</td></tr></tbody></table></div><div class="small muted">Timeout sensitivity is unchanged: {summary["timeouts"]["baseline"]} baseline and {summary["timeouts"]["extension"]} extension timeouts; no cells are reclassified.</div></section>
<section><div class="section-head"><div><h2>Tool-result errors</h2><p>Errors are classified by cause rather than treated as broken tools.</p></div></div><table><thead><tr><th>Arm</th><th class="num">Errors</th><th class="num">Results</th><th class="num">Rate</th></tr></thead><tbody><tr><td>Baseline</td><td class="num">{baseline_errors["tool_errors"]}</td><td class="num">{baseline_errors["tool_results"]}</td><td class="num">{percent_fraction(baseline_errors["error_rate"])}</td></tr><tr><td>Extension</td><td class="num">{extension_errors["tool_errors"]}</td><td class="num">{extension_errors["tool_results"]}</td><td class="num">{percent_fraction(extension_errors["error_rate"])}</td></tr></tbody></table><div class="small muted">Baseline causes: {html.escape(str(baseline_errors["error_categories"]))}<br>Extension causes: {html.escape(str(extension_errors["error_categories"]))}</div></section></div>
<section><div class="section-head"><div><h2>Complete task × rep table</h2><p>All {summary["pairs"]} pairs appear before any filtered packet cohort.</p></div></div><div class="table-wrap"><table class="compact"><thead><tr><th>Model</th><th>Task</th><th class="num">Rep</th><th class="num">Activation</th><th>Outcome</th><th class="num">Partial Δ</th><th class="num">Tokens B → E</th><th class="num">Token Δ</th></tr></thead><tbody>{"".join(pair_rows)}</tbody></table></div></section>
<section><div class="section-head"><div><h2>Trajectory packets</h2><p>Predeclared selection: every binary flip, |partial Δ| ≥ {PARTIAL_DELTA_PACKET_THRESHOLD:.1f}, or actual preview activation. Packets contain patch files/stats, failed test names, compact tool evidence, first tool divergence, and classification—never raw reasoning.</p></div></div><div class="table-wrap"><table><thead><tr><th>Pair packet</th><th>Triggers</th><th class="num">Token Δ</th></tr></thead><tbody>{"".join(packet_rows)}</tbody></table></div></section>
<section><div class="section-head"><div><h2>Conclusion</h2></div></div><div class="callout caution"><strong>The extension saves read payload, but this pilot does not show pre-mutation token savings.</strong> The direct payload reduction is deterministic; cumulative usage through first mutation was effectively flat and slightly adverse in aggregate, with only five activated pairs.</div><div class="callout"><strong>Whole-session movement is a sensitivity metric, not the answer.</strong> Activated whole sessions moved {activated_delta_text}, but later implementation and validation divergence overwhelms the small read intervention. Across all {summary["pairs"]} intention-to-treat pairs, tokens moved {percent_fraction(tokens["delta_fraction"], signed=True)}.</div><div class="callout caution">{supplement_callout}</div></section>
<div class="foot">Snapshot: <code>reports/read-long-lines-pilot/data/snapshot.json</code> · builder: <code>build_read_long_lines_report.py</code> · {summary["pairs"]} pairs / {summary["trajectories"]} trajectories · subject <code>pi@0.84.1</code></div>
</div></body></html>"""


def write_report_artifacts(
    pairs: list[dict[str, Any]], snapshot: dict[str, Any], output_dir: Path
) -> None:
    """Write deterministic JSON packets and the self-contained HTML report."""
    data_dir = output_dir / "data"
    packet_dir = output_dir / "packets"
    data_dir.mkdir(parents=True, exist_ok=True)
    packet_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "snapshot.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    )
    selected_ids = set(snapshot["packet_ids"])
    for pair in pairs:
        if pair["pair_id"] not in selected_ids:
            continue
        packet = build_trajectory_packet(pair)
        (packet_dir / f"{pair['pair_id']}.json").write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n"
        )
    for stale_packet in packet_dir.glob("*.json"):
        if stale_packet.stem not in selected_ids:
            stale_packet.unlink()
    (output_dir / "index.html").write_text(render_report_html(snapshot))


def parse_arguments() -> argparse.Namespace:
    """Parse the reproducible report-build command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=tuple(MODEL_SPECS),
        default=["sol", "terra", "luna", "flash"],
    )
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    return parser.parse_args()


def main() -> None:
    """Build a complete staged report for the requested finished model leaves."""
    arguments = parse_arguments()
    pairs = load_pilot_pairs(arguments.results_root.resolve(), arguments.models)
    snapshot = build_snapshot(pairs, arguments.models)
    write_report_artifacts(pairs, snapshot, arguments.output_dir.resolve())
    print(
        f"wrote read-long-lines report: pairs={snapshot['summary']['pairs']} "
        f"activated={snapshot['summary']['activated_pairs']} "
        f"packets={len(snapshot['packet_ids'])}"
    )


if __name__ == "__main__":
    main()
