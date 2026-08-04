#!/usr/bin/env python3
"""Extract ThinkingCap 36_v2 evidence with a contextual stock-Qwen contrast."""

from __future__ import annotations

import json
import random
import re
import shlex
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
PACKET_DIR = REPORT_DIR / "packets"
BASE_RESULT_ROOT = Path(
    "/home/will/evals/deep-swe-bench/results/"
    "Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal"
)
THINKINGCAP_RESULT_ROOT = Path(
    "/home/will/evals/deep-swe-bench/results/"
    "thinkingcap-qwen3.6-27b-awq-int4/high/"
    "baseline-thinkingcap-qwen36@1.1.0"
)
BASE_RUN_STATE = Path(
    "/home/will/evals/deep-swe-bench/results/_runs/"
    "qwen36-27b-pi-codex-goal-high-36v2-r3-w2"
)
THINKINGCAP_RUN_STATE = Path(
    "/home/will/evals/deep-swe-bench/results/_runs/"
    "thinkingcap-qwen36-high-baseline-36v2-r3-w2--"
    "a7693b8e406dfb9fa87ba78605bcdb897e8d5e3e68be229665e76fd84c4004da"
)
CLASSIFICATION_PATH = REPORT_DIR / "classifications.json"
VALIDATION_PATTERN = re.compile(
    r"(?:^|[;&|]\s*)(?:[A-Z_][A-Z0-9_]*=[^ ]+\s+)*"
    r"(?:npm|pnpm|yarn|bun|go|cargo|uv|pytest|python|python3|ruby|bundle|make|"
    r"npx|deno|gradle|mvn|dotnet)[^\n]*(?:test|check|lint|build|vet|fmt|typecheck|"
    r"tsc|vitest|jest|ruff|mypy)|(?:^|[;&|]\s*)go\s+test|(?:^|[;&|]\s*)pytest",
    re.IGNORECASE,
)
MUTATION_PATTERN = re.compile(
    r"(?:apply_patch|sed\s+-i|perl\s+-[^\n ]*i|cat\s+[^\n]*(?:>|>>)|"
    r"tee\s+[^\n]+|git\s+(?:apply|checkout\s+-b)|python[^\n]*(?:write_text|open\())",
    re.IGNORECASE,
)


WATCHDOG_DIR = Path(
    "/home/will/evals/deep-swe-bench/.worktrees/"
    "baseline-thinkingcap-qwen36-1.1.0/runs/container-memory-watchdog/"
    "thinkingcap-qwen36-high-baseline-36v2-r3-w2"
)


def wilson_score_interval(successes: int, total: int) -> list[float]:
    """Return a two-sided 95% Wilson interval for a binary rate."""
    if total <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    rate = successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    margin = (
        z
        * ((rate * (1 - rate) / total + z * z / (4 * total * total)) ** 0.5)
        / denominator
    )
    return [center - margin, center + margin]


def load_ndjson(path: Path) -> list[dict[str, Any]]:
    """Load newline-delimited JSON records from a compact audit artifact."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def build_thinkingcap_run_audit(
    thinkingcap_cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Summarize immutable launch reuse, provenance groups, and memory pressure."""
    launch_plan = load_json(THINKINGCAP_RUN_STATE / "launch-plan.json")
    batch_cells = launch_plan["batchCells"]
    provenance_counts = Counter(
        (
            result.get("task_revision"),
            result.get("harness_revision"),
            result.get("launch_plan_identity"),
        )
        for result in thinkingcap_cells.values()
    )
    manual_events = load_ndjson(WATCHDOG_DIR / "manual_interventions.ndjson")
    peak_events = load_ndjson(WATCHDOG_DIR / "peaks.json")
    thinkingcap_marker = "dsw-baseline-thinkingcap-qwen36-1.1.0-"
    alerts = [
        event
        for event in manual_events
        if event.get("event") == "over_cap_alert_only"
        and thinkingcap_marker in str(event.get("container"))
    ]
    thinkingcap_peaks = [
        event
        for event in peak_events
        if thinkingcap_marker in str(event.get("container"))
    ]
    interventions = [
        event
        for event in manual_events
        if event.get("event") not in {"watchdog_start", "over_cap_alert_only"}
        and thinkingcap_marker in str(event.get("container"))
    ]
    return {
        "plan_identity": launch_plan["planIdentity"],
        "config_lock_identity": launch_plan["configs"][0]["lockIdentity"],
        "task_revision": launch_plan["runtime"]["taskRevision"],
        "harness_revision": launch_plan["runtime"]["harnessRevision"],
        "batch_entries": len(batch_cells),
        "exact_reused_entries": sum(
            cell.get("reuseReason") == "explicit_result_reuse" for cell in batch_cells
        ),
        "new_execution_entries": sum(
            not cell.get("existingResult") for cell in batch_cells
        ),
        "preflight_covered_entries": sum(
            cell.get("preflightCovered") is True for cell in batch_cells
        ),
        "provenance_groups": [
            {
                "task_revision": key[0],
                "harness_revision": key[1],
                "launch_plan_identity": key[2],
                "reps": count,
            }
            for key, count in sorted(
                provenance_counts.items(), key=lambda item: str(item[0])
            )
        ],
        "watchdog": {
            "cap_gib": 12,
            "thinkingcap_containers_observed": len(thinkingcap_peaks),
            "alert_events": len(alerts),
            "alert_containers": len({event.get("container") for event in alerts}),
            "interventions": len(interventions),
            "peak_container_gib": max(
                (
                    float(event.get("peak_container_mem_bytes") or 0) / (1024**3)
                    for event in thinkingcap_peaks
                ),
                default=0.0,
            ),
            "peak_container": max(
                thinkingcap_peaks,
                key=lambda event: float(event.get("peak_container_mem_bytes") or 0),
                default={},
            ).get("container"),
            "alert_reasons": dict(
                Counter(str(event.get("reason")) for event in alerts)
            ),
        },
    }


def build_thinkingcap_task_stability(
    thinkingcap_cells: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize solve, validity, partial, and efficiency stability by task."""
    rows = []
    for task in sorted({key[0] for key in thinkingcap_cells}):
        results = [thinkingcap_cells[(task, rep)] for rep in range(3)]
        partials = [float(result.get("reward_partial") or 0) for result in results]
        rows.append(
            {
                "task": task,
                "language": results[0].get("language"),
                "category": results[0].get("category"),
                "solves": sum(result.get("reward_binary") == 1 for result in results),
                "valid": sum(result_is_valid(result) for result in results),
                "mean_partial": statistics.mean(partials),
                "min_partial": min(partials),
                "max_partial": max(partials),
                "partial_range": max(partials) - min(partials),
                "total_tokens": sum(
                    int(result.get("total_tokens") or 0) for result in results
                ),
                "wall_sum_s": sum(
                    float(result.get("agent_wall_s") or 0) for result in results
                ),
            }
        )
    return rows


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object from an artifact path."""
    return json.loads(path.read_text())


def load_result_cells(root: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Load one result record for every task and rep under a config root."""
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    for path in root.glob("*/rep*/result.json"):
        result = load_json(path)
        key = (str(result["task"]), int(result["rep"]))
        if key in cells:
            raise ValueError(f"Qwen comparison: duplicate result cell {key}")
        result["_cell_root"] = str(path.parent)
        cells[key] = result
    return cells


def result_is_valid(result: dict[str, Any]) -> bool:
    """Return whether a result has a graded binary outcome."""
    return result.get("reward_binary") in (0, 1)


def outcome_name(result: dict[str, Any]) -> str:
    """Map one result to solved, unsolved, or invalid."""
    if result.get("reward_binary") == 1:
        return "solved"
    if result_is_valid(result):
        return "unsolved"
    return "invalid"


def result_metric_view(result: dict[str, Any]) -> dict[str, Any]:
    """Select stable grading, usage, and execution fields for one packet side."""
    fields = (
        "reward_binary",
        "reward_partial",
        "f2p",
        "f2p_passed",
        "f2p_total",
        "p2p",
        "p2p_passed",
        "p2p_total",
        "combined_total_tokens",
        "total_tokens",
        "input_tokens",
        "output_tokens",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_exit",
        "agent_timed_out",
        "verifier_exit",
    )
    view = {field: result.get(field) for field in fields}
    view["outcome"] = outcome_name(result)
    return view


def extract_message_text(content: Any) -> str:
    """Flatten text blocks from one Pi message content value."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    texts = []
    for block in content:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            texts.append(block["text"])
    return "\n".join(texts)


def normalize_packet_markdown_text(value: str) -> str:
    """Trim trailing whitespace from one extracted Markdown evidence block."""
    return "\n".join(line.rstrip() for line in value.splitlines()).strip()


def format_packet_validation_command(command: str) -> str:
    """Render a multiline shell command as one diff-clean Markdown line."""
    return " ⏎ ".join(line.strip() for line in command.splitlines() if line.strip())


def parse_simple_file_reads(command: str) -> list[str]:
    """Extract conservative exact-file reads from common shell commands."""
    paths: list[str] = []
    for segment in re.split(r"(?:&&|;|\|\|)", command):
        segment = segment.strip()
        if not segment:
            continue
        try:
            words = shlex.split(segment)
        except ValueError:
            continue
        if not words:
            continue
        executable = Path(words[0]).name
        candidates: list[str] = []
        if executable in {"cat", "head", "tail"}:
            candidates = [word for word in words[1:] if not word.startswith("-")]
        elif executable == "sed" and "-n" in words:
            candidates = [word for word in words[1:] if not word.startswith("-")][-1:]
        for candidate in candidates:
            if candidate in {"/dev/null", "-"} or any(
                char in candidate for char in "*$(){}"
            ):
                continue
            if "/" in candidate or "." in Path(candidate).name:
                paths.append(candidate)
    return paths


def classify_tool_result_error(tool_name: str, command: str, text: str) -> str:
    """Classify an errored tool result without treating every failure as transport."""
    lowered = text.lower()
    if tool_name == "bash":
        if VALIDATION_PATTERN.search(command):
            return "validation_nonzero"
        if re.search(r"(?:grep|rg|find|git\s+(?:diff|status|show)|ls)\b", command):
            return "diagnostic_nonzero"
        return "shell_nonzero_other"
    if tool_name == "edit":
        if any(
            token in lowered for token in ("oldtext", "not found", "match", "unique")
        ):
            return "edit_mismatch"
        return "edit_error_other"
    if tool_name == "read":
        return "read_failure"
    return "tool_error_other"


def parse_session_trace(cell_root: Path) -> dict[str, Any]:
    """Extract tool, reasoning, error, read-coverage, and validation evidence."""
    session_paths = sorted((cell_root / "session").glob("*.jsonl"))
    if len(session_paths) != 1:
        raise ValueError(
            f"Qwen comparison: expected one session in {cell_root}, found {len(session_paths)}"
        )

    assistant_turns = 0
    thinking_blocks = 0
    tool_calls: dict[str, dict[str, Any]] = {}
    tool_counts: Counter[str] = Counter()
    tool_results: Counter[str] = Counter()
    tool_errors: Counter[str] = Counter()
    error_causes: Counter[str] = Counter()
    thinking_signatures: Counter[str] = Counter()
    raw_stop_reasons: Counter[str] = Counter()
    stop_reasons: Counter[str] = Counter()
    successful_reads: list[str] = []
    reads_before_mutation: list[str] = []
    validation_commands: list[dict[str, Any]] = []
    bash_commands: list[dict[str, Any]] = []
    malformed_tool_calls = 0
    raw_tool_call_text_leaks = 0
    assistant_turns_without_thinking = 0
    first_mutation_turn: int | None = None
    first_validation_turn: int | None = None
    final_assistant_text = ""
    max_prompt_tokens = 0
    max_completion_tokens = 0
    assistant_errors = 0

    records = []
    for line in session_paths[0].read_text(errors="replace").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            assistant_errors += 1

    for record in records:
        if record.get("type") != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            assistant_errors += 1
            continue
        role = message.get("role")
        if role == "assistant":
            assistant_turns += 1
            final_text = extract_message_text(message.get("content"))
            if final_text:
                final_assistant_text = final_text
                raw_tool_call_text_leaks += (
                    "<tool_call>" in final_text or "</tool_call>" in final_text
                )
            if message.get("rawStopReason") is not None:
                raw_stop_reasons[str(message["rawStopReason"])] += 1
            if message.get("stopReason") is not None:
                stop_reasons[str(message["stopReason"])] += 1
            usage = message.get("usage")
            if isinstance(usage, dict):
                max_prompt_tokens = max(max_prompt_tokens, int(usage.get("input") or 0))
                max_completion_tokens = max(
                    max_completion_tokens, int(usage.get("output") or 0)
                )
            content = message.get("content")
            if not isinstance(content, list):
                assistant_errors += 1
                continue
            assistant_has_thinking = False
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "thinking":
                    assistant_has_thinking = True
                    thinking_blocks += 1
                    signature = block.get("thinkingSignature")
                    thinking_signatures[str(signature)] += 1
                if block.get("type") != "toolCall":
                    continue
                tool_name = block.get("name")
                arguments = block.get("arguments")
                call_id = block.get("id")
                if not isinstance(tool_name, str) or not isinstance(arguments, dict):
                    malformed_tool_calls += 1
                    continue
                command = (
                    str(arguments.get("command") or "") if tool_name == "bash" else ""
                )
                tool_counts[tool_name] += 1
                tool_calls[str(call_id)] = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "assistant_turn": assistant_turns,
                    "command": command,
                }
                mutates = tool_name in {"edit", "write"} or (
                    tool_name == "bash" and MUTATION_PATTERN.search(command)
                )
                if mutates and first_mutation_turn is None:
                    first_mutation_turn = assistant_turns
                if tool_name == "bash":
                    bash_commands.append(
                        {"turn": assistant_turns, "command": command[:2000]}
                    )
                    if VALIDATION_PATTERN.search(command):
                        validation_commands.append(
                            {"turn": assistant_turns, "command": command[:2000]}
                        )
                        if first_validation_turn is None:
                            first_validation_turn = assistant_turns
            if not assistant_has_thinking:
                assistant_turns_without_thinking += 1

        if role != "toolResult":
            continue
        call_id = str(message.get("toolCallId"))
        call = tool_calls.get(call_id, {})
        tool_name = str(message.get("toolName") or call.get("tool_name") or "unknown")
        tool_results[tool_name] += 1
        result_text = extract_message_text(message.get("content"))
        is_error = bool(message.get("isError"))
        if is_error:
            tool_errors[tool_name] += 1
            error_causes[
                classify_tool_result_error(
                    tool_name, str(call.get("command") or ""), result_text
                )
            ] += 1
            continue
        read_paths: list[str] = []
        arguments = call.get("arguments")
        if tool_name == "read" and isinstance(arguments, dict):
            path = arguments.get("path")
            if isinstance(path, str):
                read_paths.append(path)
        elif tool_name == "bash":
            read_paths.extend(parse_simple_file_reads(str(call.get("command") or "")))
        for read_path in read_paths:
            successful_reads.append(read_path)
            turn = int(call.get("assistant_turn") or 0)
            if first_mutation_turn is None or turn < first_mutation_turn:
                reads_before_mutation.append(read_path)

    unique_reads = sorted(set(successful_reads))
    unique_reads_before_mutation = sorted(set(reads_before_mutation))
    return {
        "session_path": str(session_paths[0]),
        "assistant_turns": assistant_turns,
        "thinking_blocks": thinking_blocks,
        "thinking_signatures": dict(thinking_signatures),
        "tool_counts": dict(tool_counts),
        "tool_results": dict(tool_results),
        "tool_errors": dict(tool_errors),
        "tool_error_causes": dict(error_causes),
        "malformed_tool_calls": malformed_tool_calls,
        "raw_tool_call_text_leaks": raw_tool_call_text_leaks,
        "assistant_turns_without_thinking": assistant_turns_without_thinking,
        "assistant_errors": assistant_errors,
        "raw_stop_reasons": dict(raw_stop_reasons),
        "stop_reasons": dict(stop_reasons),
        "max_prompt_tokens": max_prompt_tokens,
        "max_completion_tokens": max_completion_tokens,
        "successful_exact_file_reads": unique_reads,
        "successful_exact_file_read_count": len(unique_reads),
        "successful_exact_file_read_events": len(successful_reads),
        "repeated_exact_file_reads": len(successful_reads) - len(unique_reads),
        "pre_mutation_exact_file_reads": unique_reads_before_mutation,
        "pre_mutation_exact_file_read_count": len(unique_reads_before_mutation),
        "first_mutation_turn": first_mutation_turn,
        "first_validation_turn": first_validation_turn,
        "validation_commands": validation_commands,
        "bash_commands": bash_commands,
        "final_assistant_text": final_assistant_text[:6000],
    }


def parse_patch_stats(cell_root: Path) -> dict[str, Any]:
    """Extract changed files, line counts, binary markers, and a bounded excerpt."""
    patch_path = cell_root / "artifacts" / "model.patch"
    if not patch_path.exists():
        return {
            "path": str(patch_path),
            "bytes": 0,
            "lines": 0,
            "files": [],
            "files_count": 0,
            "adds": 0,
            "dels": 0,
            "changed_lines": 0,
            "binary_files": [],
            "excerpt": "",
        }
    patch_text = patch_path.read_text(errors="replace")
    files = re.findall(r"^diff --git a/(.+?) b/(.+?)$", patch_text, re.MULTILINE)
    changed_files = [right for _left, right in files]
    adds = sum(
        1
        for line in patch_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    dels = sum(
        1
        for line in patch_text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    )
    binary_files = re.findall(
        r"^Binary files .+ and b/(.+) differ$", patch_text, re.MULTILINE
    )
    excerpt_lines = patch_text.splitlines()[:180]
    return {
        "path": str(patch_path),
        "bytes": patch_path.stat().st_size,
        "lines": len(patch_text.splitlines()),
        "files": changed_files,
        "files_count": len(changed_files),
        "adds": adds,
        "dels": dels,
        "changed_lines": adds + dels,
        "binary_files": binary_files,
        "excerpt": "\n".join(excerpt_lines)[:16000],
    }


def parse_verifier_evidence(cell_root: Path) -> dict[str, Any]:
    """Extract verifier summary, failed tests, and timeout failure signatures."""
    ctrf_path = cell_root / "verifier" / "ctrf.json"
    reward_path = cell_root / "verifier" / "reward.json"
    evidence: dict[str, Any] = {
        "ctrf_path": str(ctrf_path),
        "reward_path": str(reward_path),
        "summary": {},
        "failed_tests": [],
        "reward": {},
        "raw_failure_signatures": [],
    }
    if ctrf_path.exists():
        ctrf = load_json(ctrf_path)
        results = ctrf.get("results", {})
        if isinstance(results, dict):
            evidence["summary"] = results.get("summary", {})
            tests = results.get("tests", [])
            if isinstance(tests, list):
                evidence["failed_tests"] = [
                    {
                        "name": test.get("name"),
                        "message": str(test.get("message") or "")[:2500],
                    }
                    for test in tests
                    if isinstance(test, dict) and test.get("status") == "failed"
                ]
    log_paths = (
        cell_root / "verifier" / "new.log",
        cell_root / "verifier" / "reports" / "new.log",
        cell_root / "verifier" / "reports" / "new_run.log",
        cell_root / "verifier" / "reports" / "base_run.log",
        cell_root / "verifier" / "run.log",
    )
    raw_failure_signatures: list[str] = []
    recovered_failed_tests: list[dict[str, str]] = []
    for log_path in log_paths:
        if not log_path.exists():
            continue
        for line in log_path.read_text(errors="replace").splitlines():
            stripped = line.strip()
            failed_match = re.match(r"FAILED\s+(.+?)(?:\s+-\s+|$)", stripped)
            if failed_match:
                recovered_failed_tests.append(
                    {"name": failed_match.group(1), "message": stripped[:2500]}
                )
            if any(
                marker in stripped
                for marker in (
                    "fatal error: stack overflow",
                    "goroutine stack exceeds",
                    "did not finishing joining its threads",
                    "Maximum call stack size exceeded",
                    "failed to get `",
                    "Could not resolve host",
                )
            ):
                raw_failure_signatures.append(stripped[:2500])
    if not evidence["failed_tests"] and recovered_failed_tests:
        deduplicated = {row["name"]: row for row in recovered_failed_tests}
        evidence["failed_tests"] = list(deduplicated.values())
    evidence["raw_failure_signatures"] = list(dict.fromkeys(raw_failure_signatures))[
        :40
    ]
    if reward_path.exists():
        evidence["reward"] = load_json(reward_path)
    return evidence


def load_provider_requests(cell_root: Path) -> list[dict[str, Any]]:
    """Load captured provider requests for one cell."""
    return [
        load_json(path)
        for path in sorted(
            (cell_root / "initial_context").glob("provider_request_*.json")
        )
    ]


def provider_contract_key(request: dict[str, Any]) -> tuple[Any, ...]:
    """Create a stable provider-delivery key for aggregate counts."""
    return (
        request.get("model"),
        request.get("max_tokens"),
        request.get("temperature"),
        request.get("top_p"),
        request.get("top_k"),
        request.get("min_p"),
        request.get("presence_penalty"),
        request.get("repetition_penalty"),
        json.dumps(request.get("chat_template_kwargs"), sort_keys=True),
        request.get("thinking_token_budget"),
    )


def aggregate_result_metrics(
    cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate strict, partial, grading, usage, and execution metrics."""
    results = list(cells.values())
    valid = [result for result in results if result_is_valid(result)]
    f2p_total = sum(int(result.get("f2p_total") or 0) for result in valid)
    p2p_total = sum(int(result.get("p2p_total") or 0) for result in valid)
    return {
        "cells": len(results),
        "valid": len(valid),
        "invalid": len(results) - len(valid),
        "solves": sum(result.get("reward_binary") == 1 for result in results),
        "mean_partial_all": statistics.mean(
            float(result.get("reward_partial") or 0) for result in results
        ),
        "median_partial_all": statistics.median(
            float(result.get("reward_partial") or 0) for result in results
        ),
        "mean_partial_valid": statistics.mean(
            float(result.get("reward_partial") or 0) for result in valid
        ),
        "f2p_passed": sum(int(result.get("f2p_passed") or 0) for result in valid),
        "f2p_total": f2p_total,
        "f2p_micro": (
            sum(int(result.get("f2p_passed") or 0) for result in valid) / f2p_total
        ),
        "p2p_passed": sum(int(result.get("p2p_passed") or 0) for result in valid),
        "p2p_total": p2p_total,
        "p2p_micro": (
            sum(int(result.get("p2p_passed") or 0) for result in valid) / p2p_total
        ),
        "total_tokens": sum(int(result.get("total_tokens") or 0) for result in results),
        "output_tokens": sum(
            int(result.get("output_tokens") or 0) for result in results
        ),
        "median_total_tokens": statistics.median(
            int(result.get("total_tokens") or 0) for result in results
        ),
        "wall_sum_s": sum(float(result.get("agent_wall_s") or 0) for result in results),
        "wall_median_s": statistics.median(
            float(result.get("agent_wall_s") or 0) for result in results
        ),
        "turns": sum(int(result.get("turns") or 0) for result in results),
        "median_turns": statistics.median(
            int(result.get("turns") or 0) for result in results
        ),
        "tool_calls": sum(int(result.get("tool_calls") or 0) for result in results),
        "median_tool_calls": statistics.median(
            int(result.get("tool_calls") or 0) for result in results
        ),
        "patch_bytes": sum(int(result.get("patch_bytes") or 0) for result in results),
        "median_patch_bytes": statistics.median(
            int(result.get("patch_bytes") or 0) for result in results
        ),
        "empty_patches": sum(
            int(result.get("patch_bytes") or 0) == 0 for result in results
        ),
    }


SELECTED_THINKINGCAP_PACKET_IDS = frozenset(
    {
        "fd-deterministic-multi-key-sorting__rep1",
        "fd-deterministic-multi-key-sorting__rep2",
        "go-git-worktree-merge-conflicts__rep2",
        "goreleaser-retry-publish-auditing__rep2",
        "httpx-multipart-response-parsing__rep2",
        "langchain-request-coalescing__rep0",
        "langchain-request-coalescing__rep1",
        "meriyah-explicit-resource-declarations__rep2",
        "mobly-grouped-test-barriers__rep1",
        "participle-grammar-conflict-analysis__rep2",
        "sql-formatter-bigquery-pipe-formatting__rep1",
        "tengo-destructuring-bindings__rep0",
        "tengo-destructuring-bindings__rep1",
        "true-myth-iterable-collection-combinators__rep0",
        "wazero-multi-module-snapshots__rep1",
    }
)


def packet_trigger_reasons(
    base_result: dict[str, Any], thinkingcap_result: dict[str, Any]
) -> list[str]:
    """Select the bounded ThinkingCap solve, failure, and resource cohort."""
    del base_result
    packet_id = f"{thinkingcap_result['task']}__rep{int(thinkingcap_result['rep'])}"
    if packet_id not in SELECTED_THINKINGCAP_PACKET_IDS:
        return []
    reasons: list[str] = []
    if thinkingcap_result.get("reward_binary") == 1:
        reasons.append("ThinkingCap strict solve")
    if not result_is_valid(thinkingcap_result):
        reasons.append("ThinkingCap invalid rep")
    if thinkingcap_result.get("agent_timed_out"):
        reasons.append("ThinkingCap agent timeout")
    if int(thinkingcap_result.get("patch_bytes") or 0) > 200_000:
        reasons.append("ThinkingCap patch > 200 KB")
    if packet_id == "meriyah-explicit-resource-declarations__rep2":
        reasons.append("watchdog memory outlier")
    if packet_id in {
        "fd-deterministic-multi-key-sorting__rep2",
        "go-git-worktree-merge-conflicts__rep2",
        "goreleaser-retry-publish-auditing__rep2",
        "tengo-destructuring-bindings__rep0",
        "wazero-multi-module-snapshots__rep1",
    }:
        reasons.append("representative low or unstable valid outcome")
    return reasons


def build_packet_side(result: dict[str, Any]) -> dict[str, Any]:
    """Build one side of a selected paired trajectory packet."""
    cell_root = Path(str(result["_cell_root"]))
    metrics = result_metric_view(result)
    trace = parse_session_trace(cell_root)
    patch_stats = parse_patch_stats(cell_root)
    verifier = parse_verifier_evidence(cell_root)
    validation_commands = trace["validation_commands"]
    last_validation_turn = (
        validation_commands[-1]["turn"] if validation_commands else None
    )
    stage_ledger = {
        "initialization_and_seam_location": {
            "unique_exact_file_reads": trace["successful_exact_file_read_count"],
            "pre_mutation_exact_file_reads": trace[
                "pre_mutation_exact_file_read_count"
            ],
            "first_mutation_turn": trace["first_mutation_turn"],
        },
        "implementation": {
            "changed_files": patch_stats["files"],
            "changed_lines": patch_stats["changed_lines"],
            "binary_files": patch_stats["binary_files"],
        },
        "validation": {
            "first_validation_turn": trace["first_validation_turn"],
            "last_validation_turn": last_validation_turn,
            "detected_validation_commands": len(validation_commands),
        },
        "completion_audit": {
            "final_text_recorded": bool(trace["final_assistant_text"]),
            "turns_after_last_validation": (
                trace["assistant_turns"] - last_validation_turn
                if last_validation_turn is not None
                else None
            ),
            "claimed_completion": bool(
                re.search(
                    r"\b(?:complete|completed|done|all tests pass)\b",
                    trace["final_assistant_text"],
                    re.IGNORECASE,
                )
            ),
        },
        "termination": {
            "outcome": metrics["outcome"],
            "agent_exit": metrics["agent_exit"],
            "agent_timed_out": metrics["agent_timed_out"],
            "verifier_exit": metrics["verifier_exit"],
        },
    }
    return {
        "result": metrics,
        "trace": trace,
        "patch_stats": patch_stats,
        "verifier": verifier,
        "stage_ledger": stage_ledger,
    }


def build_paired_cells(
    base_cells: dict[tuple[str, int], dict[str, Any]],
    thinkingcap_cells: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the complete 108-rep contextual comparison table."""
    rows = []
    for key in sorted(base_cells):
        base_result = base_cells[key]
        thinkingcap_result = thinkingcap_cells[key]
        row = {
            "task": key[0],
            "rep": key[1],
            "language": base_result.get("language"),
            "category": base_result.get("category"),
            "base": result_metric_view(base_result),
            "thinkingcap": result_metric_view(thinkingcap_result),
            "delta_partial": float(thinkingcap_result.get("reward_partial") or 0)
            - float(base_result.get("reward_partial") or 0),
            "delta_f2p": float(thinkingcap_result.get("f2p") or 0)
            - float(base_result.get("f2p") or 0),
            "delta_p2p": float(thinkingcap_result.get("p2p") or 0)
            - float(base_result.get("p2p") or 0),
            "delta_tokens": int(thinkingcap_result.get("total_tokens") or 0)
            - int(base_result.get("total_tokens") or 0),
            "delta_wall_s": float(thinkingcap_result.get("agent_wall_s") or 0)
            - float(base_result.get("agent_wall_s") or 0),
            "packet_triggers": packet_trigger_reasons(base_result, thinkingcap_result),
        }
        rows.append(row)
    return rows


def aggregate_session_delivery(
    cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Audit every session, provider request, and tool-result error for one side."""
    totals: Counter[str] = Counter()
    thinking_signatures: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    tool_results: Counter[str] = Counter()
    tool_errors: Counter[str] = Counter()
    tool_error_causes: Counter[str] = Counter()
    raw_stop_reasons: Counter[str] = Counter()
    contracts: Counter[tuple[Any, ...]] = Counter()
    max_prompt_tokens = 0
    max_completion_tokens = 0
    request_count = 0
    cells_with_length_stop = 0
    unique_read_counts: list[int] = []
    pre_mutation_read_counts: list[int] = []
    repeated_read_counts: list[int] = []
    validation_command_counts: list[int] = []

    for result in cells.values():
        cell_root = Path(str(result["_cell_root"]))
        trace = parse_session_trace(cell_root)
        totals["assistant_turns"] += trace["assistant_turns"]
        totals["thinking_blocks"] += trace["thinking_blocks"]
        totals["malformed_tool_calls"] += trace["malformed_tool_calls"]
        totals["raw_tool_call_text_leaks"] += trace["raw_tool_call_text_leaks"]
        totals["assistant_turns_without_thinking"] += trace[
            "assistant_turns_without_thinking"
        ]
        totals["assistant_errors"] += trace["assistant_errors"]
        thinking_signatures.update(trace["thinking_signatures"])
        tool_counts.update(trace["tool_counts"])
        tool_results.update(trace["tool_results"])
        tool_errors.update(trace["tool_errors"])
        tool_error_causes.update(trace["tool_error_causes"])
        raw_stop_reasons.update(trace["raw_stop_reasons"])
        max_prompt_tokens = max(max_prompt_tokens, trace["max_prompt_tokens"])
        max_completion_tokens = max(
            max_completion_tokens, trace["max_completion_tokens"]
        )
        if trace["raw_stop_reasons"].get("length", 0) or trace["stop_reasons"].get(
            "length", 0
        ):
            cells_with_length_stop += 1
        unique_read_counts.append(trace["successful_exact_file_read_count"])
        pre_mutation_read_counts.append(trace["pre_mutation_exact_file_read_count"])
        repeated_read_counts.append(trace["repeated_exact_file_reads"])
        validation_command_counts.append(len(trace["validation_commands"]))
        requests = load_provider_requests(cell_root)
        request_count += len(requests)
        contracts.update(provider_contract_key(request) for request in requests)

    contract_rows = []
    for key, count in contracts.items():
        contract_rows.append(
            {
                "count": count,
                "model": key[0],
                "max_tokens": key[1],
                "temperature": key[2],
                "top_p": key[3],
                "top_k": key[4],
                "min_p": key[5],
                "presence_penalty": key[6],
                "repetition_penalty": key[7],
                "chat_template_kwargs": json.loads(key[8]) if key[8] else None,
                "thinking_token_budget": key[9],
            }
        )
    return {
        **dict(totals),
        "thinking_signatures": dict(thinking_signatures),
        "tool_counts": dict(tool_counts),
        "tool_results": dict(tool_results),
        "tool_errors": dict(tool_errors),
        "tool_error_causes": dict(tool_error_causes),
        "raw_stop_reasons": dict(raw_stop_reasons),
        "max_prompt_tokens": max_prompt_tokens,
        "max_completion_tokens": max_completion_tokens,
        "cells_with_length_stop": cells_with_length_stop,
        "provider_request_count": request_count,
        "provider_contracts": contract_rows,
        "exact_file_reads_total_unique_by_cell": sum(unique_read_counts),
        "exact_file_reads_median_unique_by_cell": statistics.median(unique_read_counts),
        "pre_mutation_reads_total_unique_by_cell": sum(pre_mutation_read_counts),
        "pre_mutation_reads_median_unique_by_cell": statistics.median(
            pre_mutation_read_counts
        ),
        "repeated_read_events": sum(repeated_read_counts),
        "validation_commands": sum(validation_command_counts),
        "validation_commands_median_by_cell": statistics.median(
            validation_command_counts
        ),
    }


def build_split_rows(
    paired_cells: list[dict[str, Any]], field: str
) -> list[dict[str, Any]]:
    """Aggregate partial reward and invalid counts by task or language."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in paired_cells:
        groups[str(row[field])].append(row)
    output = []
    for name, rows in sorted(groups.items()):
        output.append(
            {
                field: name,
                "cells": len(rows),
                "base_mean_partial": statistics.mean(
                    float(row["base"]["reward_partial"] or 0) for row in rows
                ),
                "thinkingcap_mean_partial": statistics.mean(
                    float(row["thinkingcap"]["reward_partial"] or 0) for row in rows
                ),
                "delta_partial": statistics.mean(row["delta_partial"] for row in rows),
                "base_invalid": sum(
                    row["base"]["outcome"] == "invalid" for row in rows
                ),
                "thinkingcap_invalid": sum(
                    row["thinkingcap"]["outcome"] == "invalid" for row in rows
                ),
                "base_solves": sum(row["base"]["outcome"] == "solved" for row in rows),
                "thinkingcap_solves": sum(
                    row["thinkingcap"]["outcome"] == "solved" for row in rows
                ),
                "base_median_tokens": statistics.median(
                    int(row["base"]["total_tokens"] or 0) for row in rows
                ),
                "thinkingcap_median_tokens": statistics.median(
                    int(row["thinkingcap"]["total_tokens"] or 0) for row in rows
                ),
            }
        )
    return output


def compute_paired_statistics(paired_cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute churn, timeout sensitivity, and deterministic task-cluster inference."""
    all_deltas = [float(row["delta_partial"]) for row in paired_cells]
    common_valid = [
        row
        for row in paired_cells
        if row["base"]["outcome"] != "invalid"
        and row["thinkingcap"]["outcome"] != "invalid"
    ]
    common_valid_f2p_total = sum(
        int(row["base"]["f2p_total"] or 0) for row in common_valid
    )
    common_valid_p2p_total = sum(
        int(row["base"]["p2p_total"] or 0) for row in common_valid
    )
    task_deltas: dict[str, list[float]] = defaultdict(list)
    for row in paired_cells:
        task_deltas[row["task"]].append(float(row["delta_partial"]))
    task_means = [statistics.mean(values) for values in task_deltas.values()]
    observed = abs(statistics.mean(task_means))
    permutation_seed = 20260804
    permutation_samples = 100_000
    permutation_generator = random.Random(permutation_seed)
    permutation_exceedances = 0
    for _index in range(permutation_samples):
        permuted = statistics.mean(
            value if permutation_generator.random() < 0.5 else -value
            for value in task_means
        )
        permutation_exceedances += abs(permuted) >= observed - 1e-15
    permutation_p = (permutation_exceedances + 1) / (permutation_samples + 1)
    random_generator = random.Random(20260803)
    task_names = sorted(task_deltas)
    bootstrap = []
    for _index in range(20_000):
        sampled_tasks = [random_generator.choice(task_names) for _task in task_names]
        bootstrap.append(
            statistics.mean(
                value for task in sampled_tasks for value in task_deltas[task]
            )
        )
    bootstrap.sort()
    return {
        "matched_pairs": len(paired_cells),
        "common_valid_pairs": len(common_valid),
        "mean_delta_partial_all": statistics.mean(all_deltas),
        "median_delta_partial_all": statistics.median(all_deltas),
        "mean_delta_partial_common_valid": statistics.mean(
            float(row["delta_partial"]) for row in common_valid
        ),
        "median_delta_partial_common_valid": statistics.median(
            float(row["delta_partial"]) for row in common_valid
        ),
        "common_valid_base_f2p_micro": sum(
            int(row["base"]["f2p_passed"] or 0) for row in common_valid
        )
        / common_valid_f2p_total,
        "common_valid_thinkingcap_f2p_micro": sum(
            int(row["thinkingcap"]["f2p_passed"] or 0) for row in common_valid
        )
        / common_valid_f2p_total,
        "common_valid_base_p2p_micro": sum(
            int(row["base"]["p2p_passed"] or 0) for row in common_valid
        )
        / common_valid_p2p_total,
        "common_valid_thinkingcap_p2p_micro": sum(
            int(row["thinkingcap"]["p2p_passed"] or 0) for row in common_valid
        )
        / common_valid_p2p_total,
        "common_valid_f2p_total": common_valid_f2p_total,
        "common_valid_p2p_total": common_valid_p2p_total,
        "wins_gt_005": sum(delta > 0.05 for delta in all_deltas),
        "losses_lt_neg_005": sum(delta < -0.05 for delta in all_deltas),
        "ties_within_005": sum(abs(delta) <= 0.05 for delta in all_deltas),
        "thinkingcap_only_solves": sum(
            row["thinkingcap"]["outcome"] == "solved"
            and row["base"]["outcome"] != "solved"
            for row in paired_cells
        ),
        "base_only_solves": sum(
            row["base"]["outcome"] == "solved"
            and row["thinkingcap"]["outcome"] != "solved"
            for row in paired_cells
        ),
        "both_solved": sum(
            row["base"]["outcome"] == "solved"
            and row["thinkingcap"]["outcome"] == "solved"
            for row in paired_cells
        ),
        "invalid_discordance": sum(
            (row["base"]["outcome"] == "invalid")
            != (row["thinkingcap"]["outcome"] == "invalid")
            for row in paired_cells
        ),
        "task_cluster_bootstrap_95_ci": [
            bootstrap[int(0.025 * len(bootstrap))],
            bootstrap[int(0.975 * len(bootstrap)) - 1],
        ],
        "task_sign_flip_monte_carlo_p": permutation_p,
        "task_sign_flip_monte_carlo_seed": permutation_seed,
        "task_sign_flip_monte_carlo_samples": permutation_samples,
        "task_count": len(task_names),
        "bootstrap_seed": 20260803,
        "bootstrap_samples": len(bootstrap),
    }


def load_classifications() -> dict[str, dict[str, Any]]:
    """Load evidence-backed packet driver classifications when available."""
    if not CLASSIFICATION_PATH.exists():
        return {}
    return load_json(CLASSIFICATION_PATH)


def build_selected_packets(
    base_cells: dict[tuple[str, int], dict[str, Any]],
    thinkingcap_cells: dict[tuple[str, int], dict[str, Any]],
    paired_cells: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build review packets for cells matching the predeclared trigger rule."""
    classifications = load_classifications()
    selected = []
    for row in paired_cells:
        if not row["packet_triggers"]:
            continue
        key = (str(row["task"]), int(row["rep"]))
        packet_id = f"{key[0]}__rep{key[1]}"
        packet = {
            "packet_id": packet_id,
            "pair": {
                "task": key[0],
                "rep": key[1],
                "language": row["language"],
                "category": row["category"],
                "base_config": "qwen36-27b-pi-codex-goal",
                "thinkingcap_config": "baseline-thinkingcap-qwen36@1.1.0",
                "triggers": row["packet_triggers"],
            },
            "delta": {
                "partial": row["delta_partial"],
                "f2p": row["delta_f2p"],
                "p2p": row["delta_p2p"],
                "tokens": row["delta_tokens"],
                "wall_s": row["delta_wall_s"],
            },
            "base": build_packet_side(base_cells[key]),
            "thinkingcap": build_packet_side(thinkingcap_cells[key]),
            "classification": classifications.get(packet_id),
        }
        selected.append(packet)
    return selected


def render_packet_markdown(packet: dict[str, Any]) -> str:
    """Render one reviewable Markdown packet from extracted evidence."""
    pair = packet["pair"]
    base = packet["base"]
    thinkingcap = packet["thinkingcap"]
    lines = [
        f"# {pair['task']} · rep {pair['rep']}",
        "",
        f"- Language: `{pair['language']}`",
        f"- Category: `{pair['category']}`",
        f"- Selection triggers: {', '.join(pair['triggers'])}",
        "",
        "## Outcome delta",
        "",
        "| Metric | Stock Qwen | ThinkingCap | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, key in (
        ("Partial", "reward_partial"),
        ("F2P", "f2p"),
        ("P2P", "p2p"),
        ("Tokens", "total_tokens"),
        ("Wall seconds", "agent_wall_s"),
        ("Turns", "turns"),
        ("Tool calls", "tool_calls"),
        ("Patch bytes", "patch_bytes"),
    ):
        left = base["result"].get(key)
        right = thinkingcap["result"].get(key)
        try:
            delta = float(right or 0) - float(left or 0)
            rendered_delta = f"{delta:+.4f}"
        except (TypeError, ValueError):
            rendered_delta = "—"
        lines.append(f"| {label} | {left} | {right} | {rendered_delta} |")
    lines.extend(
        [
            f"| Outcome | {base['result']['outcome']} | {thinkingcap['result']['outcome']} | — |",
            "",
            "## Grading",
            "",
            f"- Stock Qwen failed tests: {len(base['verifier']['failed_tests'])}",
            f"- ThinkingCap failed tests: {len(thinkingcap['verifier']['failed_tests'])}",
            f"- Stock Qwen failures: {', '.join(test['name'] for test in base['verifier']['failed_tests'][:20]) or 'none / unavailable'}",
            f"- ThinkingCap failures: {', '.join(test['name'] for test in thinkingcap['verifier']['failed_tests'][:20]) or 'none / unavailable'}",
            f"- Stock Qwen raw failure signatures: {base['verifier']['raw_failure_signatures'] or 'none'}",
            f"- ThinkingCap raw failure signatures: {thinkingcap['verifier']['raw_failure_signatures'] or 'none'}",
            "",
            "## Stage ledger",
            "",
            f"- Stock Qwen: first mutation turn `{base['stage_ledger']['initialization_and_seam_location']['first_mutation_turn']}`, first/last validation `{base['stage_ledger']['validation']['first_validation_turn']}` / `{base['stage_ledger']['validation']['last_validation_turn']}`, termination `{base['stage_ledger']['termination']['outcome']}`.",
            f"- ThinkingCap: first mutation turn `{thinkingcap['stage_ledger']['initialization_and_seam_location']['first_mutation_turn']}`, first/last validation `{thinkingcap['stage_ledger']['validation']['first_validation_turn']}` / `{thinkingcap['stage_ledger']['validation']['last_validation_turn']}`, termination `{thinkingcap['stage_ledger']['termination']['outcome']}`.",
            "",
            "## Patch and repository coverage",
            "",
            f"- Stock Qwen changed `{base['patch_stats']['files_count']}` files: {', '.join(base['patch_stats']['files']) or 'none'}",
            f"- ThinkingCap changed `{thinkingcap['patch_stats']['files_count']}` files: {', '.join(thinkingcap['patch_stats']['files']) or 'none'}",
            f"- Stock Qwen patch: `{base['patch_stats']['adds']}+ / {base['patch_stats']['dels']}-`; binary files: {base['patch_stats']['binary_files'] or 'none'}",
            f"- ThinkingCap patch: `{thinkingcap['patch_stats']['adds']}+ / {thinkingcap['patch_stats']['dels']}-`; binary files: {thinkingcap['patch_stats']['binary_files'] or 'none'}",
            f"- Stock Qwen exact-file reads: `{base['trace']['successful_exact_file_read_count']}` unique, `{base['trace']['pre_mutation_exact_file_read_count']}` before first mutation, `{base['trace']['repeated_exact_file_reads']}` repeated events.",
            f"- ThinkingCap exact-file reads: `{thinkingcap['trace']['successful_exact_file_read_count']}` unique, `{thinkingcap['trace']['pre_mutation_exact_file_read_count']}` before first mutation, `{thinkingcap['trace']['repeated_exact_file_reads']}` repeated events.",
            "",
            "## Validation timeline",
            "",
            "### Stock Qwen",
            "",
        ]
    )
    lines.extend(
        f"- Turn {item['turn']}: `{format_packet_validation_command(item['command'])}`"
        for item in base["trace"]["validation_commands"][:30]
    )
    if not base["trace"]["validation_commands"]:
        lines.append("- No validation command detected.")
    lines.extend(["", "### ThinkingCap", ""])
    lines.extend(
        f"- Turn {item['turn']}: `{format_packet_validation_command(item['command'])}`"
        for item in thinkingcap["trace"]["validation_commands"][:30]
    )
    if not thinkingcap["trace"]["validation_commands"]:
        lines.append("- No validation command detected.")
    lines.extend(
        [
            "",
            "## Final assistant claims",
            "",
            "### Stock Qwen",
            "",
            normalize_packet_markdown_text(base["trace"]["final_assistant_text"])
            or "_No final text recorded._",
            "",
            "### ThinkingCap",
            "",
            normalize_packet_markdown_text(thinkingcap["trace"]["final_assistant_text"])
            or "_No final text recorded._",
            "",
            "## Classification",
            "",
        ]
    )
    classification = packet.get("classification")
    if classification:
        lines.extend(
            [
                f"- Primary bucket: **{classification['primary_bucket']}**",
                f"- Secondary bucket: {classification.get('secondary_bucket') or 'none'}",
                f"- Failure layer: {classification.get('failure_layer') or 'unresolved'}",
                f"- Mechanism: {classification['mechanism']}",
                f"- Confidence: {classification['confidence']}",
            ]
        )
        lines.extend(
            f"- Evidence: {evidence}" for evidence in classification.get("evidence", [])
        )
    else:
        lines.append("_Pending trajectory review._")
    return "\n".join(line.rstrip() for line in lines).rstrip()


def write_packet_artifacts(packets: list[dict[str, Any]]) -> None:
    """Write deterministic packet JSON and Markdown files."""
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    for old_path in PACKET_DIR.iterdir():
        if old_path.is_file():
            old_path.unlink()
    for packet in packets:
        packet_id = packet["packet_id"]
        (PACKET_DIR / f"{packet_id}.json").write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n"
        )
        (PACKET_DIR / f"{packet_id}.md").write_text(
            render_packet_markdown(packet) + "\n"
        )


def build_comparison_analysis() -> dict[str, Any]:
    """Build the complete local-model capability-shape comparison dataset."""
    base_cells = load_result_cells(BASE_RESULT_ROOT)
    thinkingcap_cells = load_result_cells(THINKINGCAP_RESULT_ROOT)
    if set(base_cells) != set(thinkingcap_cells):
        missing_base = sorted(set(thinkingcap_cells) - set(base_cells))
        missing_thinkingcap = sorted(set(base_cells) - set(thinkingcap_cells))
        raise ValueError(
            "Qwen comparison: unmatched cells; "
            f"missing_base={missing_base}, missing_thinkingcap={missing_thinkingcap}"
        )
    if len(base_cells) != 108:
        raise ValueError(
            f"ThinkingCap 36_v2 analysis: expected 108 matched reps, found {len(base_cells)}"
        )

    paired_cells = build_paired_cells(base_cells, thinkingcap_cells)
    base_delivery = aggregate_session_delivery(base_cells)
    thinkingcap_delivery = aggregate_session_delivery(thinkingcap_cells)
    packets = build_selected_packets(base_cells, thinkingcap_cells, paired_cells)
    write_packet_artifacts(packets)

    base_status = load_json(BASE_RUN_STATE / "status.json")
    thinkingcap_status = load_json(THINKINGCAP_RUN_STATE / "status.json")
    common_valid_keys = [
        key
        for key in base_cells
        if result_is_valid(base_cells[key]) and result_is_valid(thinkingcap_cells[key])
    ]
    grading_denominator_mismatches = [
        {
            "task": key[0],
            "rep": key[1],
            "field": field,
            "base": base_cells[key].get(field),
            "thinkingcap": thinkingcap_cells[key].get(field),
        }
        for key in common_valid_keys
        for field in ("f2p_total", "p2p_total")
        if base_cells[key].get(field) != thinkingcap_cells[key].get(field)
    ]
    analysis = {
        "question": (
            "What capability and efficiency profile did ThinkingCap demonstrate across "
            "36_v2, and how does it compare contextually with stock Qwen plus "
            "pi-codex-goal on the same task/rep addresses?"
        ),
        "roles": {
            "thinkingcap": "local subject",
            "base_qwen": "local contrast",
            "frontier_reference": None,
        },
        "comparison": {
            "subset": "36_v2",
            "reps": 3,
            "thinking": "high",
            "matched_pairs": 108,
            "unique_tasks": 36,
            "base_config": "qwen36-27b-pi-codex-goal",
            "thinkingcap_config": "baseline-thinkingcap-qwen36@1.1.0",
            "base_model": "local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4",
            "thinkingcap_model": "local-vllm/thinkingcap-qwen3.6-27b-awq-int4",
            "base_result_root": str(BASE_RESULT_ROOT),
            "thinkingcap_result_root": str(THINKINGCAP_RESULT_ROOT),
            "base_run_state": str(BASE_RUN_STATE),
            "thinkingcap_run_state": str(THINKINGCAP_RUN_STATE),
            "base_terminal_state": {
                "state": base_status.get("state"),
                "stage": base_status.get("stage"),
                "counts": base_status.get("counts"),
            },
            "thinkingcap_terminal_state": {
                "state": thinkingcap_status.get("state"),
                "stage": thinkingcap_status.get("stage"),
                "counts": thinkingcap_status.get("counts"),
            },
        },
        "delivery_classification": {
            "base_qwen": "ambiguous",
            "base_qwen_reason": (
                "All sessions and requests prove model, thinking, reasoning preservation, "
                "sampling, and tools. The older run lacks versioned config-lock and subject-version "
                "provenance, and captured requests omit max_tokens despite models.json declaring 81920."
            ),
            "thinkingcap": "delivered",
            "thinkingcap_reason": (
                "All cells carry versioned lock/plan provenance; captured requests pin model, "
                "max_tokens=98304, thinking, reasoning preservation, and sampling."
            ),
        },
        "substrate_comparability": {
            "shared": [
                "Pi execution with OpenAI-compatible local providers",
                "OpenAI-compatible completions API and qwen-chat-template thinking",
                "High thinking with enable_thinking=true and preserve_thinking=true",
                "Temperature 1.0, top_p 0.95, top_k 20, min_p 0.0, repetition_penalty 1.0",
                "262144-token declared context window",
                "Same 36 tasks and three rep ids per task",
                "Identical F2P and P2P denominators on every common-valid pair",
            ],
            "differences": [
                {
                    "surface": "Agent config behavior",
                    "base": "pi-codex-goal package, initial /create-goal transform, and goal tools",
                    "thinkingcap": "stock Pi baseline with no config-authored prompt text",
                    "intentional": False,
                },
                {
                    "surface": "Weights/checkpoint",
                    "base": "cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4",
                    "thinkingcap": "ThinkingCap fine-tune, compressed-tensors AWQ INT4",
                    "intentional": True,
                },
                {
                    "surface": "Endpoint/runtime",
                    "base": "server60:30000, vllm/vllm-openai:nightly documented 2026-07-04",
                    "thinkingcap": "server60:8081, vLLM 0.25.1 build 752a3a5",
                    "intentional": False,
                },
                {
                    "surface": "Outgoing output ceiling",
                    "base": "models.json declares 81920; all 72 captures omit max_tokens",
                    "thinkingcap": "all 72 captures send max_tokens=98304",
                    "intentional": False,
                },
                {
                    "surface": "Agent timeout",
                    "base": "legacy manifest unset; observed agent cutoffs at 5400 seconds",
                    "thinkingcap": "launch plan pins 3600 seconds",
                    "intentional": False,
                },
                {
                    "surface": "Pi/config provenance",
                    "base": "unversioned pi-codex-goal config; subject version and immutable launch plan absent",
                    "thinkingcap": "pi@0.83.0; versioned config lock and immutable launch plan",
                    "intentional": False,
                },
                {
                    "surface": "Input declaration",
                    "base": "text and image",
                    "thinkingcap": "text only",
                    "intentional": False,
                },
            ],
            "common_valid_pairs": len(common_valid_keys),
            "grading_denominator_mismatches": grading_denominator_mismatches,
        },
        "base": aggregate_result_metrics(base_cells),
        "thinkingcap": aggregate_result_metrics(thinkingcap_cells),
        "paired_statistics": compute_paired_statistics(paired_cells),
        "task_splits": build_split_rows(paired_cells, "task"),
        "language_splits": build_split_rows(paired_cells, "language"),
        "paired_cells": paired_cells,
        "delivery": {
            "base": base_delivery,
            "thinkingcap": thinkingcap_delivery,
        },
        "packet_rule": {
            "scope": "ThinkingCap-primary bounded cohort",
            "all_thinkingcap_solves": True,
            "all_thinkingcap_invalid_reps": True,
            "valid_agent_timeout": True,
            "patch_and_memory_outliers": True,
            "representative_low_or_unstable_valid_outcomes": True,
            "selected_packet_ids": sorted(SELECTED_THINKINGCAP_PACKET_IDS),
        },
        "packet_count": len(packets),
        "packet_ids": [packet["packet_id"] for packet in packets],
        "scaffoldability_ledger": [
            {
                "observed_weakness": "Recursive and cyclic state lacks explicit guards in participle reps 0/2, SuperJSON rep2, and recursive delegation rep2.",
                "failure_layer": "core model capability / repository understanding",
                "candidate_support": "A recursion-state completion check that names visited, in-progress, depth, identity-rehydration, and cycle tests.",
                "expected_mechanism": "Force the trajectory to represent recursive invariants before broad implementation and run one adversarial cycle case.",
                "non_targets": "Parser seam selection, retry call-site wiring, and generic timeout recovery.",
                "risk": "More validation tokens and possible overfitting if phrased with task-specific examples.",
                "minimal_experiment": "Same ThinkingCap serving contract on the four named cells, untreated versus one generic recursion-audit intervention.",
                "success_criterion": "No stack overflow; higher F2P without lower P2P; no increase in invalid cells or median tokens above 20%.",
            },
            {
                "observed_weakness": "Concurrency implementations miss join/complete/error/cancel cleanup in LangChain reps 1/2 and leave major grouped-phase gaps in Mobly rep0.",
                "failure_layer": "core model capability / execution control",
                "candidate_support": "A bounded lifecycle matrix and thread/task leak gate before completion.",
                "expected_mechanism": "Expose stuck waiters and missing cancellation with short local tests instead of a verifier-scale hang.",
                "non_targets": "Pure formatting and non-concurrent repository seams.",
                "risk": "Flaky timing tests unless synchronization uses deterministic barriers and bounded joins.",
                "minimal_experiment": "Use the current combined pi-check+timeout run as a first probe, then isolate a lifecycle-specific audit on LangChain reps 1/2 and Mobly rep0 under the same model/server.",
                "success_criterion": "All lifecycle tests terminate; no verifier timeout; F2P improves while P2P stays at 1.0.",
            },
            {
                "observed_weakness": "Large helper implementations are not always wired to the authoritative entry point, especially GoReleaser rep2 and stock SuperJSON rep2.",
                "failure_layer": "repository understanding",
                "candidate_support": "A call-site reachability and real-entrypoint integration check after adding wrappers or parallel helpers.",
                "expected_mechanism": "Verify that the production call graph reaches the new helper and that one real operation exercises it.",
                "non_targets": "Incorrect core algorithms after reachability is proven.",
                "risk": "Repository mapping adds reads and may encourage unnecessary refactoring.",
                "minimal_experiment": "Same-model A/B on GoReleaser rep2 and SuperJSON rep2 with a generic reachability audit only.",
                "success_criterion": "The real publisher/serializer calls the new path; targeted feature tests improve with no shared-surface regression.",
            },
            {
                "observed_weakness": "Completion claims outrun evidence; 9 of 10 selected ThinkingCap packets that claimed completion were still unsolved or invalid.",
                "failure_layer": "execution control",
                "candidate_support": "A final diff-scope, targeted-test, full-regression, and unresolved-failure audit such as pi-check.",
                "expected_mechanism": "Turn the model's own test output and changed-file list into a second-pass correction opportunity.",
                "non_targets": "Missing capability when the model cannot derive the required abstraction from available evidence.",
                "risk": "Extra tokens and latency; a generic audit may repeat work without discriminating failures.",
                "minimal_experiment": "Analyze the in-progress pi-check@1.4.0 plus Bash-timeout run after all cells finish; treat it as a combined intervention and isolate either mechanism only in a follow-up A/B.",
                "success_criterion": "More strict solves or materially higher common-valid F2P, no worse invalid rate, and bounded token/wall overhead.",
            },
        ],
        "negative_evidence": [
            "Do not change the tool parser: both sides produced zero malformed tool calls and preserved reasoning on every assistant turn.",
            "Do not raise the output ceiling: neither side recorded a length stop and maximum observed completion was below 11600 tokens.",
            "Do not grant blanket extra agent time: ThinkingCap used a shorter 3600-second limit yet finished two cells where stock Qwen exhausted 5400 seconds.",
            "Do not treat all tool errors as transport faults: most were failing validation or diagnostic shell commands; read and edit errors were bounded and interpretable.",
            "Do not infer a broad fine-tune quality gain from the all-rep partial edge: the common-valid mean delta is approximately zero, and the stock contrast also adds pi-codex-goal.",
        ],
        "packets": [
            {
                "packet_id": packet["packet_id"],
                "pair": packet["pair"],
                "delta": packet["delta"],
                "classification": packet["classification"],
            }
            for packet in packets
        ],
    }
    thinkingcap_metrics = analysis["thinkingcap"]
    thinkingcap_metrics["solve_rate"] = (
        thinkingcap_metrics["solves"] / thinkingcap_metrics["cells"]
    )
    thinkingcap_metrics["solve_rate_wilson_95_ci"] = wilson_score_interval(
        thinkingcap_metrics["solves"], thinkingcap_metrics["cells"]
    )
    analysis["thinkingcap_run_audit"] = build_thinkingcap_run_audit(thinkingcap_cells)
    analysis["thinkingcap_task_stability"] = build_thinkingcap_task_stability(
        thinkingcap_cells
    )
    analysis["thinkingcap_solve_reps"] = [
        {"task": key[0], "rep": key[1], **result_metric_view(result)}
        for key, result in sorted(thinkingcap_cells.items())
        if result.get("reward_binary") == 1
    ]
    analysis["thinkingcap_invalid_reps"] = [
        {"task": key[0], "rep": key[1], **result_metric_view(result)}
        for key, result in sorted(thinkingcap_cells.items())
        if not result_is_valid(result)
    ]
    analysis["contextual_contrast_limit"] = (
        "The stock checkpoint contrast is not a config control. It adds the "
        "pi-codex-goal package and initial goal transform, uses a different endpoint/runtime, "
        "has an 81920-token declared output ceiling with omitted max_tokens captures, allows "
        "longer legacy agent cutoffs, and lacks modern lock/plan provenance. Use it to bound "
        "capability and efficiency shape, not to attribute causality to fine-tuning."
    )
    analysis["scaffoldability_ledger"] = [
        {
            "observed_weakness": (
                "Only 3 of 108 reps solved strictly despite 67.6% feature-test micro and "
                "99.93% preservation-test micro; many reps stopped near, but below, complete."
            ),
            "failure_layer": "execution control / core model capability",
            "candidate_support": "A final requirement, diff-scope, targeted-test, and unresolved-failure audit such as pi-check.",
            "expected_mechanism": "Give the model one explicit second pass over its own evidence before termination.",
            "non_targets": "Missing abstractions the model cannot derive and verifier-only timeouts after agent exit.",
            "risk": "The 12_v2 pi-check treatment used 68% more tokens and did not improve common-valid mean partial.",
            "minimal_experiment": "Run the already-proven pi-check@1.4.0 plus Bash-timeout config on the same 36_v2 task/rep addresses.",
            "success_criterion": "More strict solves or materially higher common-valid F2P, no worse invalid rate, and token overhead below the prior 68% increase.",
        },
        {
            "observed_weakness": (
                "Four reps were invalid: LangChain reps 0/1, Mobly rep1, and HTTPX rep2; "
                "three ended in verifier timeout and two had agent timeout signatures."
            ),
            "failure_layer": "execution control / harness or grading",
            "candidate_support": "The established 360-second default Bash timeout plus a completion audit that checks lifecycle and teardown.",
            "expected_mechanism": "Bound individual validation commands and surface stuck waiters or teardown before the rep-level cutoff.",
            "non_targets": "A verifier hang that begins only after the agent exits and non-concurrent feature gaps.",
            "risk": "A Bash timeout can abort a useful long test and does not change the 3600-second agent limit.",
            "minimal_experiment": "Use the combined pi-check+timeout config, then add timeout-only and pi-check-only controls if invalid outcomes move.",
            "success_criterion": "At least three of four baseline-invalid addresses grade valid without creating new invalid addresses.",
        },
        {
            "observed_weakness": (
                "Scope and resource control broke in distinct ways: participle rep2 emitted a "
                "2.1 MB patch, Tengo destructuring reps 0/1 used 29.2M/32.9M tokens, and "
                "Meriyah rep2 peaked at 39.33 GiB during Vitest fan-out."
            ),
            "failure_layer": "execution control / repository understanding",
            "candidate_support": "A progress controller that checks changed-file scope, repeated validation, and bounded test parallelism.",
            "expected_mechanism": "Stop broad rewrites and repeated expensive test fan-out before they consume the remaining rep budget.",
            "non_targets": "Compact correct patches that still miss one hidden invariant.",
            "risk": "Overly rigid scope limits can block legitimate cross-file changes; test parallelism controls alter timing.",
            "minimal_experiment": "Instrument the pi-check run first; add a separate scope/progress guard only if the same signatures recur.",
            "success_criterion": "No patch above 200 KB, no container above 12 GiB, and lower p90 tokens without lower F2P.",
        },
        {
            "observed_weakness": (
                "Recurring low task means remained in Go worktree merge conflicts (0.544), "
                "GoReleaser retry auditing (0.586), Wazero snapshots (0.650), and recursive "
                "grammar analysis (0.680), with misses concentrated in lifecycle, retry, and cycle invariants."
            ),
            "failure_layer": "core model capability / repository understanding",
            "candidate_support": "A task-agnostic invariant matrix covering lifecycle states, retries, cleanup, recursion guards, and authoritative call-site reachability.",
            "expected_mechanism": "Force explicit edge-state representation before implementation and targeted tests for each state transition.",
            "non_targets": "Serving failures, malformed tool calls, and output truncation.",
            "risk": "Generic invariant checklists add tokens and can become ceremonial without repository-specific evidence.",
            "minimal_experiment": "After the combined pi-check run, select repeated failures and test one invariant-focused support in a same-model paired subset.",
            "success_criterion": "Higher F2P on targeted tasks with unchanged P2P and no increase in median tokens above 20%.",
        },
    ]
    max_completion = analysis["delivery"]["thinkingcap"]["max_completion_tokens"]
    analysis["negative_evidence"] = [
        "Do not change the tool parser: delivery produced no malformed tool calls or raw tool-call leaks.",
        f"Do not raise the output ceiling: there were no length stops and the largest observed completion was {max_completion} tokens against a 98304-token ceiling.",
        "Do not grant blanket extra rep time: the largest valid trajectories already consumed 29M to 33M tokens without strict completion.",
        "Do not treat ordinary tool errors as transport faults: the audit separates nonzero validation and diagnostic commands from edit/read failures.",
        "Do not attribute the contextual token reduction solely to fine-tuning: the stock contrast also changes goal tooling, endpoint/runtime, timeout policy, and provenance.",
    ]
    return analysis


def main() -> None:
    """Extract comparison evidence and write deterministic report inputs."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    analysis = build_comparison_analysis()
    output_path = REPORT_DIR / "analysis.json"
    output_path.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(
        "ThinkingCap 36_v2 analysis extracted: "
        f"{analysis['comparison']['matched_pairs']} pairs, "
        f"{analysis['packet_count']} packets -> {output_path}"
    )


if __name__ == "__main__":
    main()
