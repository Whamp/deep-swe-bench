#!/usr/bin/env python3
"""Extract the full-113 baseline versus testing-skills paired evidence ledger."""

from __future__ import annotations

import json
import math
import random
import re
import statistics
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path("/home/will/evals/deep-swe-bench/results")
CANONICAL_ROOT = RESULTS_ROOT / "gpt-5.6-sol/low"
TASKS_ROOT = Path("/home/will/evals/deep-swe/tasks")
SUBSET_PATH = REPOSITORY_ROOT / "subsets/113_v0.txt"
SUBSET_36_PATH = REPOSITORY_ROOT / "subsets/36_v2.txt"
LEFT_CONFIG = "baseline@1.1.0"
RIGHT_CONFIG = "testing-skills@1.1.0"
CONFIGS = (LEFT_CONFIG, RIGHT_CONFIG)
EXPECTED_LOCKS = {
    LEFT_CONFIG: "sha256:c6311a9ff6fc7becacbdd1ce59d9f473d62cf30abce9f1b0c355b13cd241660e",
    RIGHT_CONFIG: "sha256:fc27e36bb3e113548a12c958abbc5a7a4b08f1059cb9261d330b8160dc8bcf54",
}
FULL_RUN_KEY = (
    "gpt56-sol-low-baseline-vs-testing-skills-1-1-ful--"
    "c48f3f717959c476ecc8f2b0daf81d06b96878eda9ce4b44419213938d2c2f10"
)
WAZERO_RUN_KEY = (
    "gpt56-sol-low-baseline-vs-testing-skills-1-1-waz--"
    "bc18a1a2af72f803a2ff6233e0afbc5c27c4ca0a046017f5ba0c5a2fb37eb147"
)
QUARANTINE_ROOTS = {
    "resource-oom": (
        RESULTS_ROOT / "_contaminated/resource-oom" / FULL_RUN_KEY,
        RESULTS_ROOT / "_contaminated/resource-oom" / WAZERO_RUN_KEY,
    ),
    "harness-failure": (RESULTS_ROOT / "_contaminated/harness-failure" / FULL_RUN_KEY,),
}
ANALYSIS_PATH = Path(__file__).with_name("full113-comparison.json")
SKILL_NAMES = ("testing", "fuzzing", "property-based-testing")
SPECIALIST_NAMES = ("fuzzing", "property-based-testing")
FUZZ_TARGET_PATTERN = re.compile(r"func\s+Fuzz\w*\s*\([^)]*\*testing\.F", re.IGNORECASE)
PROPERTY_TEST_PATTERN = re.compile(
    r"\b(@given|hypothesis\.given|fc\.assert|proptest!|quickcheck!|rapid\.Check)\b",
    re.IGNORECASE,
)
TEST_PATH_PATTERN = re.compile(
    r"(^|/)(test|tests|spec)|[._-](test|tests|spec)\.", re.IGNORECASE
)
VALIDATION_COMMAND_PATTERN = re.compile(
    r"\b(test|tests|pytest|cargo test|go test|npm test|pnpm test|yarn test|"
    r"vitest|jest|ruff|mypy|pyright|tsc|lint|check|build)\b",
    re.IGNORECASE,
)


def read_tasks(path: Path) -> list[str]:
    """Read a task selector without blank lines or comments."""
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def task_metadata(task: str) -> dict[str, Any]:
    """Read stable task title, category, and language from task.toml."""
    path = TASKS_ROOT / task / "task.toml"
    document = tomllib.loads(path.read_text())
    metadata = document["metadata"]
    return {
        "title": metadata.get("display_title")
        or metadata.get("original_title")
        or task,
        "category": metadata.get("category", "unknown"),
        "language": metadata.get("language", "unknown"),
        "difficulty": None,
    }


def result_cell_key(path: Path) -> tuple[str, str, int]:
    """Recover config, task, and rep from a result artifact path."""
    parts = path.parts
    config = next(config for config in CONFIGS if config in parts)
    config_index = parts.index(config)
    task = parts[config_index + 1]
    rep = int(parts[config_index + 2].removeprefix("rep"))
    return config, task, rep


def load_result_cells(tasks: set[str]) -> dict[tuple[str, str, int], dict[str, Any]]:
    """Load every planned canonical or quarantined cell exactly once."""
    cells: dict[tuple[str, str, int], dict[str, Any]] = {}
    sources = [("canonical", CANONICAL_ROOT)]
    for category, roots in QUARANTINE_ROOTS.items():
        sources.extend((category, root) for root in roots)
    for disposition, root in sources:
        if not root.exists():
            continue
        for result_path in root.glob("**/result.json"):
            if not any(config in result_path.parts for config in CONFIGS):
                continue
            key = result_cell_key(result_path)
            if key[1] not in tasks or key[2] >= 3:
                continue
            if key in cells:
                raise RuntimeError(f"Duplicate result cell {key}: {result_path}")
            cells[key] = {
                "path": result_path.parent,
                "result": json.loads(result_path.read_text()),
                "disposition": disposition,
            }
    expected = {
        (config, task, rep) for config in CONFIGS for task in tasks for rep in range(3)
    }
    if set(cells) != expected:
        missing = sorted(expected - set(cells))
        extra = sorted(set(cells) - expected)
        raise RuntimeError(
            f"Result coverage mismatch: missing={missing}, extra={extra}"
        )
    return cells


def verify_result_provenance(cells: dict[tuple[str, str, int], dict[str, Any]]) -> dict:
    """Assert the model, thinking, locks, exits, and resource dispositions."""
    verifier_statuses = Counter()
    launch_plans = Counter()
    dispositions = Counter()
    for (config, task, rep), cell in cells.items():
        result = cell["result"]
        context = f"{config}/{task}/rep{rep}"
        expected = {
            "model": "openai-codex/gpt-5.6-sol",
            "thinking_level": "low",
            "subject_version": "pi@0.84.1",
            "config_lock_identity": EXPECTED_LOCKS[config],
            "agent_exit": 0,
            "agent_timed_out": False,
        }
        for field, value in expected.items():
            if result.get(field) != value:
                raise RuntimeError(
                    f"Provenance mismatch for {context}: {field}={result.get(field)!r}"
                )
        events = result.get("subject_memory_events") or {}
        if cell["disposition"] == "canonical" and events.get("oom_kill", 0):
            raise RuntimeError(f"Canonical OOM contamination leaked into {context}")
        if cell["disposition"] == "resource-oom" and not events.get("oom_kill", 0):
            raise RuntimeError(f"OOM quarantine lacks OOM evidence: {context}")
        if (
            cell["disposition"] == "harness-failure"
            and result.get("verifier_exit") != 127
        ):
            raise RuntimeError(f"Harness quarantine lacks exit 127: {context}")
        verifier_statuses[str(result.get("verifier_exit"))] += 1
        launch_plans[str(result.get("launch_plan_identity"))] += 1
        dispositions[cell["disposition"]] += 1
    return {
        "cells": len(cells),
        "dispositions": dict(dispositions),
        "verifier_statuses": dict(verifier_statuses),
        "launch_plan_identities": dict(launch_plans),
    }


def read_session_records(cell_path: Path) -> list[dict[str, Any]]:
    """Read native Pi session records for one cell."""
    records = []
    for session_path in sorted((cell_path / "session").glob("*.jsonl")):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def session_text(cell_path: Path) -> str:
    """Concatenate native Pi session records for skill-delivery checks."""
    return "\n".join(
        path.read_text(errors="replace")
        for path in sorted((cell_path / "session").glob("*.jsonl"))
    )


def patch_text(cell_path: Path) -> str:
    """Read the model patch when one exists."""
    path = cell_path / "artifacts/model.patch"
    return path.read_text(errors="replace") if path.exists() else ""


def added_patch_lines(cell_path: Path) -> list[str]:
    """Return added patch lines, excluding diff metadata."""
    return [
        line[1:]
        for line in patch_text(cell_path).splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def patch_summary(cell_path: Path) -> dict[str, Any]:
    """Summarize changed paths and line counts from a unified diff."""
    patch = patch_text(cell_path)
    paths = re.findall(r"^\+\+\+ b/(.+)$", patch, re.MULTILINE)
    added = sum(
        line.startswith("+") and not line.startswith("+++")
        for line in patch.splitlines()
    )
    deleted = sum(
        line.startswith("-") and not line.startswith("---")
        for line in patch.splitlines()
    )
    added_text = "\n".join(added_patch_lines(cell_path))
    return {
        "changed_paths": paths,
        "changed_files": len(paths),
        "added_lines": added,
        "deleted_lines": deleted,
        "test_patch": any(TEST_PATH_PATTERN.search(path) for path in paths),
        "fuzz_target": bool(FUZZ_TARGET_PATTERN.search(added_text)),
        "property_test": bool(PROPERTY_TEST_PATTERN.search(added_text)),
    }


def failed_verifier_tests(cell_path: Path) -> list[str]:
    """Read failed feature and preservation test names from CTRF."""
    path = cell_path / "verifier/ctrf.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text())
    results = report.get("results")
    if not isinstance(results, dict):
        raise TypeError(f"CTRF report has no results object: {path}")
    tests = results.get("tests")
    if not isinstance(tests, list):
        raise TypeError(f"CTRF report has no tests list: {path}")
    return [
        str(test.get("name", "unnamed test"))
        for test in tests
        if test.get("status") == "failed"
    ]


def skill_reads(cell_path: Path) -> dict[str, bool]:
    """Return which configured skill entrypoints the model read."""
    text = session_text(cell_path)
    return {name: f"/arm/skills/{name}/SKILL.md" in text for name in SKILL_NAMES}


def skill_advertisement(cell_path: Path) -> dict[str, bool]:
    """Return which configured skills appeared in the captured prompt."""
    path = cell_path / "initial_context/system_prompt.txt"
    prompt = path.read_text(errors="replace")
    return {name: f"<name>{name}</name>" in prompt for name in SKILL_NAMES}


def result_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """Select result fields used by paired efficacy and packet analysis."""
    fields = (
        "reward_binary",
        "reward_partial",
        "f2p_passed",
        "f2p_total",
        "p2p_passed",
        "p2p_total",
        "total_tokens",
        "combined_cost_usd",
        "agent_wall_s",
        "tool_calls",
        "turns",
        "patch_bytes",
        "verifier_exit",
    )
    return {field: result.get(field) for field in fields}


def tool_result_error_category(tool: str, text: str) -> str:
    """Classify recorded tool errors by their operational cause."""
    if tool == "bash":
        return "nonzero_diagnostic_command"
    lowered = text.lower()
    if any(
        marker in lowered
        for marker in (
            "invalid arguments",
            "schema validation",
            "malformed argument",
            "failed to parse arguments",
        )
    ):
        return "malformed_arguments"
    if tool == "edit":
        return "edit_target_mismatch"
    if tool == "read":
        return "missing_file_or_range"
    return "parser_transport_or_other"


def tool_error_audit(cell_paths: list[Path]) -> dict[str, Any]:
    """Count tool results and classify every recorded error."""
    totals = Counter()
    errors = Counter()
    categories = Counter()
    for cell_path in cell_paths:
        for record in read_session_records(cell_path):
            message = record.get("message", {})
            if message.get("role") != "toolResult":
                continue
            tool = str(message.get("toolName", "unknown"))
            totals[tool] += 1
            if not message.get("isError"):
                continue
            errors[tool] += 1
            text = " ".join(
                str(part.get("text", ""))
                for part in message.get("content", [])
                if isinstance(part, dict)
            )
            categories[tool_result_error_category(tool, text)] += 1
    if sum(errors.values()) != sum(categories.values()):
        raise RuntimeError("Tool error classifier did not cover every error")
    return {
        "tool_results": sum(totals.values()),
        "errors": sum(errors.values()),
        "by_tool_total": dict(totals),
        "by_tool_error": dict(errors),
        "by_cause": dict(categories),
    }


def compact_tool_timeline(cell_path: Path) -> list[dict[str, Any]]:
    """Build a compact, ordered tool-call timeline for a trajectory packet."""
    timeline = []
    call_index: dict[str, int] = {}
    for record in read_session_records(cell_path):
        message = record.get("message", {})
        if message.get("role") == "assistant":
            for part in message.get("content", []):
                if not isinstance(part, dict) or part.get("type") != "toolCall":
                    continue
                arguments = part.get("arguments", {})
                summary = (
                    arguments.get("path") or arguments.get("command") or str(arguments)
                )
                event = {
                    "ordinal": len(timeline) + 1,
                    "tool": part.get("name"),
                    "summary": str(summary)[:300],
                    "is_error": None,
                    "error_cause": None,
                }
                timeline.append(event)
                call_index[str(part.get("id"))] = len(timeline) - 1
        elif message.get("role") == "toolResult":
            index = call_index.get(str(message.get("toolCallId")))
            if index is None:
                continue
            is_error = bool(message.get("isError"))
            timeline[index]["is_error"] = is_error
            if is_error:
                text = " ".join(
                    str(part.get("text", ""))
                    for part in message.get("content", [])
                    if isinstance(part, dict)
                )
                timeline[index]["error_cause"] = tool_result_error_category(
                    str(message.get("toolName", "unknown")), text
                )
    return timeline


def successful_exact_reads(cell_path: Path) -> list[str]:
    """List exact file paths successfully read by the model."""
    return sorted(
        {
            event["summary"]
            for event in compact_tool_timeline(cell_path)
            if event["tool"] == "read" and event["is_error"] is False
        }
    )


def build_stage_ledger(cell_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Summarize execution stages from initialization through termination."""
    timeline = compact_tool_timeline(cell_path)
    first_mutation = next(
        (event["ordinal"] for event in timeline if event["tool"] in ("edit", "write")),
        None,
    )
    reads_before_mutation = sum(
        event["tool"] == "read"
        and event["is_error"] is False
        and (first_mutation is None or event["ordinal"] < first_mutation)
        for event in timeline
    )
    validations = [
        event
        for event in timeline
        if event["tool"] == "bash"
        and (first_mutation is None or event["ordinal"] > first_mutation)
        and VALIDATION_COMMAND_PATTERN.search(event["summary"])
    ]
    completion_audits = [
        event
        for event in timeline
        if event["tool"] == "bash" and re.search(r"git (diff|status)", event["summary"])
    ]
    return {
        "initialization": {"skill_reads": skill_reads(cell_path)},
        "contract_representation": "task instruction delivered in initial user message",
        "seam_location": {
            "successful_reads_before_first_edit_or_write": reads_before_mutation,
            "first_edit_or_write_ordinal": first_mutation,
        },
        "implementation": patch_summary(cell_path),
        "targeted_and_regression_validation": {
            "validation_commands_after_first_edit_or_write": len(validations),
            "commands": [event["summary"] for event in validations[-8:]],
        },
        "completion_audit": {
            "git_diff_or_status_commands": len(completion_audits),
            "commands": [event["summary"] for event in completion_audits[-4:]],
        },
        "termination": {
            "agent_exit": result.get("agent_exit"),
            "agent_timed_out": result.get("agent_timed_out"),
            "verifier_exit": result.get("verifier_exit"),
        },
    }


def packet_selection_reasons(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    """Apply the predeclared material-trajectory packet rule."""
    reasons = []
    if (left["reward_binary"] == 1) != (right["reward_binary"] == 1):
        reasons.append("binary_solve_flip")
    if (left["reward_binary"] < 0) != (right["reward_binary"] < 0):
        reasons.append("negative_reward_mismatch")
    if abs(right["reward_partial"] - left["reward_partial"]) >= 0.05:
        reasons.append("absolute_partial_delta_at_least_0.05")
    return reasons


def primary_driver(losing: dict[str, Any]) -> str:
    """Classify the narrowest grading-backed failure driver."""
    if losing.get("patch_bytes", 0) == 0:
        return "under-implementation"
    if losing.get("p2p_passed", 0) < losing.get("p2p_total", 0):
        return "cross-scope regression"
    missing_feature = losing.get("f2p_total", 0) - losing.get("f2p_passed", 0)
    if missing_feature > 3:
        return "under-implementation"
    if missing_feature > 0:
        return "missing invariant/guard"
    return "likely variance"


def first_consequential_divergence(
    left_patch: dict[str, Any],
    right_patch: dict[str, Any],
    left_result: dict[str, Any],
    right_result: dict[str, Any],
) -> str:
    """Name the earliest supported implementation divergence for a packet."""
    left_paths = set(left_patch["changed_paths"])
    right_paths = set(right_patch["changed_paths"])
    if not left_paths or not right_paths:
        return (
            "One config terminated without a patch while the other implemented changes."
        )
    if not left_paths & right_paths:
        return "The configs selected disjoint implementation seams with no changed-file overlap."
    lower = (
        left_result
        if left_result["reward_partial"] < right_result["reward_partial"]
        else right_result
    )
    missing = lower.get("f2p_total", 0) - lower.get("f2p_passed", 0)
    return (
        "The configs reached an overlapping implementation seam, but the lower-scoring "
        f"patch left {missing} feature checks unsatisfied."
    )


def build_packet(row: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Build a self-contained paired trajectory packet."""
    left_result = row["left_result"]
    right_result = row["right_result"]
    losing = (
        left_result
        if left_result["reward_partial"] < right_result["reward_partial"]
        else right_result
    )
    return {
        "task": row["task"],
        "title": metadata["title"],
        "category": metadata["category"],
        "language": metadata["language"],
        "difficulty": metadata["difficulty"],
        "rep": row["rep"],
        "selection_reasons": row["packet_reasons"],
        "left": left_result,
        "right": right_result,
        "left_patch": row["left_patch"],
        "right_patch": row["right_patch"],
        "left_failed_tests": row["left_failed_tests"],
        "right_failed_tests": row["right_failed_tests"],
        "left_successful_exact_reads": successful_exact_reads(row["left_path"]),
        "right_successful_exact_reads": successful_exact_reads(row["right_path"]),
        "left_stage_ledger": build_stage_ledger(row["left_path"], row["left_raw"]),
        "right_stage_ledger": build_stage_ledger(row["right_path"], row["right_raw"]),
        "left_tool_timeline": compact_tool_timeline(row["left_path"]),
        "right_tool_timeline": compact_tool_timeline(row["right_path"]),
        "first_consequential_divergence": first_consequential_divergence(
            row["left_patch"], row["right_patch"], left_result, right_result
        ),
        "primary_driver": primary_driver(losing),
        "confidence": "grading-backed; causal attribution to skills remains uncertain",
    }


def exact_mcnemar_p_value(gains: int, losses: int) -> float:
    """Compute the two-sided exact McNemar/binomial p-value for discordant pairs."""
    discordant = gains + losses
    smaller = min(gains, losses)
    tail = sum(math.comb(discordant, value) for value in range(smaller + 1))
    return min(1.0, 2 * tail / (2**discordant))


def paired_bootstrap_interval(deltas: list[int]) -> list[float]:
    """Return a deterministic percentile interval for paired solve-rate change."""
    randomizer = random.Random(0)
    samples = sorted(
        sum(randomizer.choice(deltas) for _ in deltas) / len(deltas)
        for _ in range(20_000)
    )
    return [samples[500], samples[19_499]]


def build_full113_analysis() -> dict[str, Any]:
    """Build the complete clean, contaminated, delivery, and packet ledgers."""
    tasks = read_tasks(SUBSET_PATH)
    task_set = set(tasks)
    tasks_36 = set(read_tasks(SUBSET_36_PATH))
    metadata = {task: task_metadata(task) for task in tasks}
    cells = load_result_cells(task_set)
    provenance = verify_result_provenance(cells)

    rows: list[dict[str, Any]] = []
    excluded_pairs: list[dict[str, Any]] = []
    raw_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for task in tasks:
        for rep in range(3):
            left_cell = cells[(LEFT_CONFIG, task, rep)]
            right_cell = cells[(RIGHT_CONFIG, task, rep)]
            raw_rows.append((left_cell["result"], right_cell["result"]))
            if (
                left_cell["disposition"] != "canonical"
                or right_cell["disposition"] != "canonical"
            ):
                excluded_pairs.append(
                    {
                        "task": task,
                        "rep": rep,
                        "left_disposition": left_cell["disposition"],
                        "right_disposition": right_cell["disposition"],
                        "left_reward_binary": left_cell["result"].get("reward_binary"),
                        "right_reward_binary": right_cell["result"].get(
                            "reward_binary"
                        ),
                        "left_oom_kills": (
                            left_cell["result"].get("subject_memory_events") or {}
                        ).get("oom_kill", 0),
                        "right_oom_kills": (
                            right_cell["result"].get("subject_memory_events") or {}
                        ).get("oom_kill", 0),
                    }
                )
                continue
            left_path = left_cell["path"]
            right_path = right_cell["path"]
            left_result = result_metrics(left_cell["result"])
            right_result = result_metrics(right_cell["result"])
            rows.append(
                {
                    "task": task,
                    "rep": rep,
                    "left_path": left_path,
                    "right_path": right_path,
                    "left_raw": left_cell["result"],
                    "right_raw": right_cell["result"],
                    "left_result": left_result,
                    "right_result": right_result,
                    "left_solved": left_result["reward_binary"] == 1,
                    "right_solved": right_result["reward_binary"] == 1,
                    "left_patch": patch_summary(left_path),
                    "right_patch": patch_summary(right_path),
                    "left_failed_tests": failed_verifier_tests(left_path),
                    "right_failed_tests": failed_verifier_tests(right_path),
                    "right_skill_reads": skill_reads(right_path),
                    "packet_reasons": packet_selection_reasons(
                        left_result, right_result
                    ),
                }
            )

    advertised = Counter()
    treatment_reads = Counter()
    baseline_leaks = Counter()
    for row in rows:
        for name, present in skill_advertisement(row["right_path"]).items():
            advertised[name] += present
        for name, present in row["right_skill_reads"].items():
            treatment_reads[name] += present
        for name, present in skill_reads(row["left_path"]).items():
            baseline_leaks[name] += present

    specialist_rows: list[dict[str, Any]] = [
        row
        for row in rows
        if any(row["right_skill_reads"][name] for name in SPECIALIST_NAMES)
    ]
    fuzz_target_rows: list[dict[str, Any]] = [
        row for row in specialist_rows if row["right_patch"]["fuzz_target"]
    ]
    property_test_rows: list[dict[str, Any]] = [
        row for row in specialist_rows if row["right_patch"]["property_test"]
    ]

    gains = sum(not row["left_solved"] and row["right_solved"] for row in rows)
    losses = sum(row["left_solved"] and not row["right_solved"] for row in rows)
    both = sum(row["left_solved"] and row["right_solved"] for row in rows)
    neither = len(rows) - gains - losses - both
    solve_deltas = [int(row["right_solved"]) - int(row["left_solved"]) for row in rows]
    partial_deltas = [
        row["right_result"]["reward_partial"] - row["left_result"]["reward_partial"]
        for row in rows
    ]

    aggregate_fields = (
        "total_tokens",
        "combined_cost_usd",
        "agent_wall_s",
        "tool_calls",
        "turns",
        "patch_bytes",
    )
    aggregates = {}
    for field in aggregate_fields:
        left = sum(row["left_result"][field] or 0 for row in rows)
        right = sum(row["right_result"][field] or 0 for row in rows)
        aggregates[field] = {
            "left": left,
            "right": right,
            "delta_percent": (right / left - 1) * 100,
        }

    def split_summary(split_rows: list[dict[str, Any]]) -> dict[str, Any]:
        split_gains = sum(
            not row["left_solved"] and row["right_solved"] for row in split_rows
        )
        split_losses = sum(
            row["left_solved"] and not row["right_solved"] for row in split_rows
        )
        return {
            "pairs": len(split_rows),
            "left_solves": sum(row["left_solved"] for row in split_rows),
            "right_solves": sum(row["right_solved"] for row in split_rows),
            "gains": split_gains,
            "losses": split_losses,
        }

    task_summaries: list[dict[str, Any]] = []
    for task in tasks:
        task_rows = [row for row in rows if row["task"] == task]
        summary = split_summary(task_rows)
        summary.update(metadata[task])
        summary["task"] = task
        summary["excluded_pairs"] = 3 - len(task_rows)
        summary["specialist_read_pairs"] = sum(
            any(row["right_skill_reads"][name] for name in SPECIALIST_NAMES)
            for row in task_rows
        )
        task_summaries.append(summary)

    language_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        language_rows[metadata[row["task"]]["language"]].append(row)
    language_summaries = {
        language: split_summary(group)
        for language, group in sorted(language_rows.items())
    }

    packets: list[dict[str, Any]] = []
    for row in rows:
        if not row["packet_reasons"]:
            continue
        packet = build_packet(row, metadata[row["task"]])
        packet["packet"] = f"packets/{row['task']}__rep{row['rep']}.json"
        packets.append(packet)

    clean_paths: dict[str, list[Path]] = {
        LEFT_CONFIG: [row["left_path"] for row in rows],
        RIGHT_CONFIG: [row["right_path"] for row in rows],
    }
    raw_left_solves = sum(left["reward_binary"] == 1 for left, _ in raw_rows)
    raw_right_solves = sum(right["reward_binary"] == 1 for _, right in raw_rows)
    return {
        "scope": {
            "left": LEFT_CONFIG,
            "right": RIGHT_CONFIG,
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
            "roles": "same-model config control; treatment adds testing, fuzzing, and property-based-testing skills",
            "tasks": len(tasks),
            "reps": 3,
            "planned_pairs": len(tasks) * 3,
            "valid_clean_pairs": len(rows),
            "excluded_pairs": len(excluded_pairs),
            "full_trajectories": len(cells),
            "valid_clean_trajectories": len(rows) * 2,
            "difficulty_note": "The task manifest does not assign difficulty labels.",
        },
        "provenance": provenance,
        "outcomes": {
            "left_solves": sum(row["left_solved"] for row in rows),
            "right_solves": sum(row["right_solved"] for row in rows),
            "solve_delta": sum(solve_deltas),
            "solve_rate_delta": statistics.mean(solve_deltas),
            "paired_bootstrap_95_percent": paired_bootstrap_interval(solve_deltas),
            "exact_mcnemar_p_value": exact_mcnemar_p_value(gains, losses),
            "gains": gains,
            "losses": losses,
            "both_solved": both,
            "neither_solved": neither,
            "mean_partial_delta": statistics.mean(partial_deltas),
            "median_partial_delta": statistics.median(partial_deltas),
            "raw_planned_left_solves": raw_left_solves,
            "raw_planned_right_solves": raw_right_solves,
            "raw_planned_note": "Includes OOM-contaminated and invalid-verifier cells; not an efficacy estimate.",
        },
        "splits": {
            "36_v2": split_summary([row for row in rows if row["task"] in tasks_36]),
            "added_77": split_summary(
                [row for row in rows if row["task"] not in tasks_36]
            ),
            "languages": language_summaries,
        },
        "delivery": {
            "advertised": dict(advertised),
            "treatment_reads": dict(treatment_reads),
            "baseline_skill_leaks": dict(baseline_leaks),
            "specialist_read_cells": len(specialist_rows),
            "fuzz_target_cells": len(fuzz_target_rows),
            "property_test_cells": len(property_test_rows),
            "specialist_association": split_summary(specialist_rows),
            "non_specialist_association": split_summary(
                [row for row in rows if row not in specialist_rows]
            ),
            "fuzz_target_rows": [
                {
                    "task": row["task"],
                    "rep": row["rep"],
                    "left_solved": row["left_solved"],
                    "right_solved": row["right_solved"],
                }
                for row in fuzz_target_rows
            ],
        },
        "behavior": {
            "left_test_patch_cells": sum(
                row["left_patch"]["test_patch"] for row in rows
            ),
            "right_test_patch_cells": sum(
                row["right_patch"]["test_patch"] for row in rows
            ),
            "left_empty_patch_cells": sum(
                not row["left_patch"]["changed_paths"] for row in rows
            ),
            "right_empty_patch_cells": sum(
                not row["right_patch"]["changed_paths"] for row in rows
            ),
            "aggregates": aggregates,
            "tool_errors": {
                LEFT_CONFIG: tool_error_audit(clean_paths[LEFT_CONFIG]),
                RIGHT_CONFIG: tool_error_audit(clean_paths[RIGHT_CONFIG]),
            },
        },
        "task_summaries": task_summaries,
        "excluded_pairs": excluded_pairs,
        "packet_rule": (
            "Select every valid pair with a binary solve flip, a negative-reward "
            "mismatch, or an absolute partial-reward delta of at least 0.05."
        ),
        "packet_count": len(packets),
        "packets": packets,
        "ledger": [
            {
                key: value
                for key, value in row.items()
                if key not in ("left_path", "right_path", "left_raw", "right_raw")
            }
            for row in rows
        ],
    }


def write_full113_analysis() -> dict[str, Any]:
    """Generate the JSON evidence artifact and return its in-memory value."""
    analysis = build_full113_analysis()
    ANALYSIS_PATH.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    return analysis


if __name__ == "__main__":
    result = write_full113_analysis()
    print(f"wrote {ANALYSIS_PATH}")
    print(f"valid pairs={result['scope']['valid_clean_pairs']}")
    print(f"packets={result['packet_count']}")
