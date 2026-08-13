#!/usr/bin/env python3
"""Build the matched full-113 analysis for testing-skills 1.1.0 vs 1.2.0."""

from __future__ import annotations

import html
import importlib.util
import json
import math
import random
import re
import statistics
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
RESULTS = Path("/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low")
TASKS_ROOT = Path("/home/will/evals/deep-swe/tasks")
SUBSET = REPO / "subsets/113_v0.txt"
PILOT_SUBSET = REPO / "subsets/testing_skills_24_v0.txt"
OUT = REPO / "analysis/testing-skills-1.2.0-full113"
PACKETS = OUT / "packets"
REPORT = REPO / "reports/testing-skills-1.2-vs-1.1-full113"
REPORT_PACKETS = REPORT / "packets"
LEFT = "testing-skills@1.1.0"
RIGHT = "testing-skills@1.2.0"
CONFIGS = (LEFT, RIGHT)
LOCKS = {
    LEFT: "sha256:fc27e36bb3e113548a12c958abbc5a7a4b08f1059cb9261d330b8160dc8bcf54",
    RIGHT: "sha256:18aeac3ac63571b89844aa7f037eb6d4b7f21b983e6173f2fb0bf7b3593150f9",
}
PLAN_IDENTITIES = {
    "initial": "sha256:b72785bfa013565f980ddb8a92f9c44b8737ec34dee89b704403f51dee749e96",
    "resume": "sha256:bd70919645618f52ac446a18773ccc60a657d4737c10e49bd059947673503e71",
}
SKILLS = ("testing", "property-based-testing", "fuzzing")
VALIDATION = re.compile(
    r"\b(test|pytest|cargo test|go test|npm test|pnpm test|yarn test|vitest|jest|ruff|mypy|pyright|tsc|lint|check|build)\b",
    re.IGNORECASE,
)
TEST_PATH = re.compile(
    r"(^|/)(test|tests|spec)|[._-](test|tests|spec)\.", re.IGNORECASE
)
PROPERTY_PATTERN = re.compile(
    r"\b(@given|hypothesis\.given|fc\.assert|proptest!|quickcheck!|rapid\.Check|testing/quick)\b",
    re.IGNORECASE,
)
FUZZ_PATTERN = re.compile(
    r"\b(func\s+Fuzz\w*\s*\([^)]*\*testing\.F|cargo[_ -]?fuzz|libfuzzer|afl\+\+)\b",
    re.IGNORECASE,
)

spec = importlib.util.spec_from_file_location(
    "full113_helpers", REPO / "analysis/testing-skills-1.1.0/full113_analysis.py"
)
assert spec and spec.loader
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def selected_tasks(path: Path) -> list[str]:
    """Read one ordered task selector."""
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def task_metadata(task: str) -> dict[str, str]:
    """Read stable task labels used in the report."""
    document = tomllib.loads((TASKS_ROOT / task / "task.toml").read_text())
    metadata = document["metadata"]
    return {
        "title": metadata.get("display_title")
        or metadata.get("original_title")
        or task,
        "language": metadata.get("language", "unknown"),
        "category": metadata.get("category", "unknown"),
    }


def cell_path(config: str, task: str, rep: int) -> Path:
    """Return one canonical result-cell directory."""
    return RESULTS / config / task / f"rep{rep}"


def resource_flagged(result: dict[str, Any]) -> bool:
    """Report whether either subject or verifier recorded resource exhaustion."""
    subject = result.get("subject_memory_events") or {}
    verifier = result.get("verifier_memory_events") or {}
    return bool(
        result.get("agent_resource_exhausted")
        or result.get("verifier_resource_exhausted")
        or subject.get("oom_kill")
        or verifier.get("oom_kill")
    )


def load_cells(task_names: list[str]) -> dict[tuple[str, str, int], dict[str, Any]]:
    """Load and validate the complete 678-cell matched comparison."""
    cells: dict[tuple[str, str, int], dict[str, Any]] = {}
    for config in CONFIGS:
        for task in task_names:
            for rep in range(3):
                path = cell_path(config, task, rep)
                result_path = path / "result.json"
                if not result_path.is_file():
                    raise FileNotFoundError(f"missing result: {result_path}")
                result = json.loads(result_path.read_text())
                expected = {
                    "config": config,
                    "config_lock_identity": LOCKS[config],
                    "model": "openai-codex/gpt-5.6-sol",
                    "thinking_level": "low",
                    "subject_version": "pi@0.84.1",
                    "agent_exit": 0,
                    "agent_timed_out": False,
                }
                for field, value in expected.items():
                    if result.get(field) != value:
                        raise ValueError(
                            f"{config}/{task}/rep{rep}: {field}={result.get(field)!r}; expected={value!r}"
                        )
                verifier_exit = result.get("verifier_exit")
                allowed_exit = verifier_exit in {0, "skipped_empty_patch"} or (
                    config == RIGHT
                    and task == "kombu-virtual-queue-dead-lettering"
                    and rep == 2
                    and verifier_exit == "timeout"
                )
                if not allowed_exit:
                    raise ValueError(
                        f"unexpected verifier exit: {config}/{task}/rep{rep}={verifier_exit!r}"
                    )
                prompt = (path / "initial_context/system_prompt.txt").read_text(
                    errors="replace"
                )
                advertised = {
                    skill: f"<name>{skill}</name>" in prompt for skill in SKILLS
                }
                if not all(advertised.values()):
                    raise ValueError(
                        f"skill delivery missing: {config}/{task}/rep{rep}={advertised}"
                    )
                cells[(config, task, rep)] = {
                    "path": path,
                    "result": result,
                    "advertised": advertised,
                }
    if len(cells) != 678:
        raise ValueError(f"expected 678 trajectories, found {len(cells)}")
    return cells


def assistant_text(path: Path) -> str:
    """Join assistant text and thinking for mechanism marker searches."""
    chunks: list[str] = []
    for record in helpers.read_session_records(path):
        message = record.get("message", {})
        if message.get("role") != "assistant":
            continue
        for part in message.get("content", []):
            if isinstance(part, dict) and part.get("type") in {"text", "thinking"}:
                chunks.append(str(part.get("text", "")))
    return "\n".join(chunks)


def patch_excerpt(path: Path, limit: int = 120) -> str:
    """Return a bounded patch excerpt for one evidence packet."""
    lines = helpers.patch_text(path).splitlines()
    return "\n".join(lines[:limit]) + ("\n…" if len(lines) > limit else "")


def trajectory(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Extract routing, mutation, validation, patch, and termination evidence."""
    timeline = helpers.compact_tool_timeline(path)
    mutation_ordinals = [
        event["ordinal"]
        for event in timeline
        if event["tool"] in {"edit", "write"} and event["is_error"] is not True
    ]
    first_mutation = min(mutation_ordinals) if mutation_ordinals else None
    last_mutation = max(mutation_ordinals) if mutation_ordinals else None
    validations = [
        event
        for event in timeline
        if event["tool"] == "bash" and VALIDATION.search(event["summary"])
    ]
    final_validations = [
        event
        for event in validations
        if last_mutation is None or event["ordinal"] > last_mutation
    ]
    audits = [
        event
        for event in timeline
        if event["tool"] == "bash" and re.search(r"git (diff|status)", event["summary"])
    ]
    final_audits = [
        event
        for event in audits
        if last_mutation is None or event["ordinal"] > last_mutation
    ]
    patch = helpers.patch_summary(path)
    added = "\n".join(helpers.added_patch_lines(path))
    text = assistant_text(path)
    return {
        "skill_reads": helpers.skill_reads(path),
        "assistant_contract_card": bool(
            re.search(r"(?m)^\s*(Contract|Preservation|Primary search):", text)
        ),
        "first_mutation_ordinal": first_mutation,
        "last_mutation_ordinal": last_mutation,
        "successful_reads_before_first_mutation": sum(
            event["tool"] == "read"
            and event["is_error"] is False
            and (first_mutation is None or event["ordinal"] < first_mutation)
            for event in timeline
        ),
        "validation_commands": len(validations),
        "final_patch_validation_commands": len(final_validations),
        "final_patch_validation_tail": [
            event["summary"] for event in final_validations[-6:]
        ],
        "completion_audits_after_final_mutation": len(final_audits),
        "test_patch": any(
            TEST_PATH.search(changed) for changed in patch["changed_paths"]
        ),
        "property_test_patch": bool(PROPERTY_PATTERN.search(added)),
        "fuzz_target_patch": bool(FUZZ_PATTERN.search(added)),
        "patch": patch,
        "tool_calls": len(timeline),
        "tool_errors": sum(event["is_error"] is True for event in timeline),
        "successful_exact_reads": helpers.successful_exact_reads(path),
        "timeline": timeline,
        "termination": {
            "agent_exit": result.get("agent_exit"),
            "agent_timed_out": result.get("agent_timed_out"),
            "verifier_exit": result.get("verifier_exit"),
            "resource_flagged": resource_flagged(result),
        },
    }


def result_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """Select comparable result metrics for packet and ledger records."""
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
        "cost_usd",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_timed_out",
        "verifier_exit",
        "resource_policy",
    )
    metrics = {field: result.get(field) for field in fields}
    metrics["resource_flagged"] = resource_flagged(result)
    return metrics


def solved(result: dict[str, Any]) -> bool:
    """Treat only binary reward 1 as solved."""
    return result.get("reward_binary") == 1


def outcome_class(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Classify one matched binary outcome."""
    if not solved(left) and solved(right):
        return "gain"
    if solved(left) and not solved(right):
        return "loss"
    if solved(left) and solved(right):
        return "both"
    return "neither"


def task_flip_directions(
    cells: dict[tuple[str, str, int], dict[str, Any]], task: str
) -> set[str]:
    """Return gain/loss directions observed across a task's three reps."""
    return {
        outcome_class(
            cells[(LEFT, task, rep)]["result"],
            cells[(RIGHT, task, rep)]["result"],
        )
        for rep in range(3)
    } & {"gain", "loss"}


def driver_bucket(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    outcome: str,
    reciprocal_task: bool,
) -> str:
    """Assign a conservative grading-backed triage bucket to one selected pair."""
    if (
        left.get("verifier_exit") == "timeout"
        or right.get("verifier_exit") == "timeout"
    ):
        return "verifier timeout"
    if left.get("resource_flagged") or right.get("resource_flagged"):
        return "resource-sensitive"
    if reciprocal_task:
        return "likely variance"
    losing = left if outcome == "gain" else right
    if not losing.get("patch_bytes"):
        return "under-implementation"
    p2p_total = losing.get("p2p_total") or 0
    p2p_passed = losing.get("p2p_passed") or 0
    if p2p_total > p2p_passed:
        return "cross-scope regression"
    f2p_total = losing.get("f2p_total") or 0
    f2p_passed = losing.get("f2p_passed") or 0
    if f2p_total - f2p_passed > 3:
        return "under-implementation"
    if f2p_total > f2p_passed:
        return "missing invariant/guard"
    return "validation gap"


def mechanism_text(packet: dict[str, Any]) -> str:
    """Summarize the observable difference without claiming wording causality."""
    outcome = packet["outcome"]
    losing_side = "left" if outcome == "gain" else "right"
    winning_side = "right" if outcome == "gain" else "left"
    losing = packet[losing_side]
    winning = packet[winning_side]
    failed = packet[f"{losing_side}_failed_tests"]
    losing_paths = losing["trajectory"]["patch"]["changed_paths"]
    winning_paths = winning["trajectory"]["patch"]["changed_paths"]
    overlap = sorted(set(losing_paths) & set(winning_paths))
    failure = ", ".join(failed[:3]) if failed else "the remaining graded behavior"
    seam = ", ".join(overlap[:3]) if overlap else "different patch seams"
    bucket = packet["primary_driver"]
    if bucket == "verifier timeout":
        return "The 1.2 patch moved filesystem messages to the wrong transport directory, so the official no-ack consume test blocked in drain_events."
    if bucket == "resource-sensitive":
        return "At least one paired trajectory recorded an OOM event. The observed result remains intention-to-treat; the resource event is not assigned as the cause without a clean counterfactual."
    if bucket == "likely variance":
        return f"This task flipped in both directions across reps. Both sides reached {seam}, so no stable wording mechanism is assigned."
    if bucket == "cross-scope regression":
        return f"The losing patch failed preservation checks ({failure}); the winning patch retained them."
    if bucket == "under-implementation":
        return f"The losing patch left several requested checks unsatisfied ({failure}) around {seam}."
    if bucket == "missing invariant/guard":
        return f"The losing patch missed a bounded invariant ({failure}) around {seam}."
    return f"The losing trajectory did not expose the graded miss ({failure}) before stopping; the winning patch passed it."


def exact_mcnemar(gains: int, losses: int) -> float:
    """Return the exact two-sided McNemar p-value."""
    discordant = gains + losses
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(gains, losses) + 1))
    return min(1.0, 2 * tail / (2**discordant))


def paired_bootstrap_interval(
    deltas: list[int], *, samples: int = 20_000, seed: int = 20260813
) -> tuple[float, float]:
    """Return a deterministic percentile interval for solve-rate delta points."""
    rng = random.Random(seed)
    draws = []
    for _ in range(samples):
        draws.append(
            100 * sum(deltas[rng.randrange(len(deltas))] for _ in deltas) / len(deltas)
        )
    draws.sort()
    return draws[int(0.025 * samples)], draws[int(0.975 * samples) - 1]


def mean(values: list[float]) -> float:
    """Return a safe arithmetic mean."""
    return statistics.mean(values) if values else 0.0


def aggregate_config(
    config: str,
    keys: list[tuple[str, int]],
    cells: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate efficacy, cost, routing, and patch behavior for one config."""
    group = [cells[(config, task, rep)] for task, rep in keys]
    results = [item["result"] for item in group]
    trajectories = [item["trajectory"] for item in group]
    return {
        "cells": len(group),
        "solves": sum(solved(result) for result in results),
        "mean_partial": mean([float(result["reward_partial"]) for result in results]),
        "tokens": sum(int(result["total_tokens"]) for result in results),
        "cost": sum(float(result["cost_usd"]) for result in results),
        "wall_s": sum(float(result["agent_wall_s"]) for result in results),
        "turns": sum(int(result["turns"]) for result in results),
        "tool_calls": sum(int(result["tool_calls"]) for result in results),
        "patch_bytes": sum(int(result["patch_bytes"]) for result in results),
        "skill_reads": {
            skill: sum(bool(t["skill_reads"][skill]) for t in trajectories)
            for skill in SKILLS
        },
        "specialist_read_cells": sum(
            bool(t["skill_reads"]["property-based-testing"])
            or bool(t["skill_reads"]["fuzzing"])
            for t in trajectories
        ),
        "contract_card_mentions": sum(
            t["assistant_contract_card"] for t in trajectories
        ),
        "test_patch_cells": sum(t["test_patch"] for t in trajectories),
        "property_test_patch_cells": sum(
            t["property_test_patch"] for t in trajectories
        ),
        "fuzz_target_patch_cells": sum(t["fuzz_target_patch"] for t in trajectories),
        "final_patch_validation_cells": sum(
            t["final_patch_validation_commands"] > 0 for t in trajectories
        ),
        "resource_flagged_cells": sum(resource_flagged(result) for result in results),
        "verifier_timeouts": sum(
            result.get("verifier_exit") == "timeout" for result in results
        ),
    }


def comparison_summary(
    keys: list[tuple[str, int]],
    cells: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Compute matched solve, churn, partial, and statistical summaries."""
    rows = []
    for task, rep in keys:
        left = cells[(LEFT, task, rep)]["result"]
        right = cells[(RIGHT, task, rep)]["result"]
        rows.append((left, right, outcome_class(left, right)))
    gains = sum(outcome == "gain" for _, _, outcome in rows)
    losses = sum(outcome == "loss" for _, _, outcome in rows)
    deltas = [int(solved(right)) - int(solved(left)) for left, right, _ in rows]
    low, high = paired_bootstrap_interval(deltas)
    partial_deltas = [
        float(right["reward_partial"]) - float(left["reward_partial"])
        for left, right, _ in rows
    ]
    return {
        "pairs": len(rows),
        "left_solves": sum(solved(left) for left, _, _ in rows),
        "right_solves": sum(solved(right) for _, right, _ in rows),
        "gains": gains,
        "losses": losses,
        "both": sum(outcome == "both" for _, _, outcome in rows),
        "neither": sum(outcome == "neither" for _, _, outcome in rows),
        "solve_delta": gains - losses,
        "solve_rate_delta_points": 100 * sum(deltas) / len(deltas),
        "mcnemar_p": exact_mcnemar(gains, losses),
        "bootstrap_95_low_points": low,
        "bootstrap_95_high_points": high,
        "mean_partial_delta": mean(partial_deltas),
        "median_partial_delta": statistics.median(partial_deltas),
    }


def build() -> dict[str, Any]:
    """Build machine-readable comparison data and trajectory packets."""
    task_names = selected_tasks(SUBSET)
    if len(task_names) != 113 or len(set(task_names)) != 113:
        raise ValueError("full selector must contain 113 unique tasks")
    pilot_tasks = set(selected_tasks(PILOT_SUBSET))
    metadata = {task: task_metadata(task) for task in task_names}
    cells = load_cells(task_names)
    for item in cells.values():
        item["trajectory"] = trajectory(item["path"], item["result"])

    all_keys = [(task, rep) for task in task_names for rep in range(3)]
    pilot_keys = [key for key in all_keys if key[0] in pilot_tasks]
    holdout_keys = [key for key in all_keys if key[0] not in pilot_tasks]
    resource_clean_keys = [
        key
        for key in all_keys
        if not resource_flagged(cells[(LEFT, *key)]["result"])
        and not resource_flagged(cells[(RIGHT, *key)]["result"])
    ]
    cohorts = {
        "all": comparison_summary(all_keys, cells),
        "pilot": comparison_summary(pilot_keys, cells),
        "holdout": comparison_summary(holdout_keys, cells),
        "resource_clean": comparison_summary(resource_clean_keys, cells),
    }
    config_summary = {
        config: aggregate_config(config, all_keys, cells) for config in CONFIGS
    }

    packet_index = []
    ledger = []
    matrix = []
    PACKETS.mkdir(parents=True, exist_ok=True)
    REPORT_PACKETS.mkdir(parents=True, exist_ok=True)
    reciprocal_tasks = {
        task
        for task in task_names
        if task_flip_directions(cells, task) == {"gain", "loss"}
    }
    for task, rep in all_keys:
        left_cell = cells[(LEFT, task, rep)]
        right_cell = cells[(RIGHT, task, rep)]
        left_metrics = result_metrics(left_cell["result"])
        right_metrics = result_metrics(right_cell["result"])
        outcome = outcome_class(left_cell["result"], right_cell["result"])
        partial_delta = float(right_metrics["reward_partial"]) - float(
            left_metrics["reward_partial"]
        )
        reasons = []
        if outcome in {"gain", "loss"}:
            reasons.append("binary_solve_flip")
        if abs(partial_delta) >= 0.05:
            reasons.append("absolute_partial_delta_at_least_0.05")
        if left_metrics["verifier_exit"] != right_metrics["verifier_exit"]:
            reasons.append("verifier_exit_discordance")
        packet_name = f"{task}__rep{rep}.json"
        row = {
            "task": task,
            "rep": rep,
            "title": metadata[task]["title"],
            "language": metadata[task]["language"],
            "cohort": "pilot" if task in pilot_tasks else "holdout",
            "outcome": outcome,
            "partial_delta": partial_delta,
            "left": left_metrics,
            "right": right_metrics,
            "selection_reasons": reasons,
            "packet": f"packets/{packet_name}" if reasons else None,
        }
        ledger.append(row)
        matrix.append(
            {
                "task": task,
                "rep": rep,
                "language": metadata[task]["language"],
                "cohort": row["cohort"],
                "left_binary": left_metrics["reward_binary"],
                "right_binary": right_metrics["reward_binary"],
                "left_partial": left_metrics["reward_partial"],
                "right_partial": right_metrics["reward_partial"],
            }
        )
        if not reasons:
            continue
        bucket = driver_bucket(
            left_metrics,
            right_metrics,
            outcome=outcome,
            reciprocal_task=task in reciprocal_tasks,
        )
        packet = {
            **row,
            "category": metadata[task]["category"],
            "left": {
                "metrics": left_metrics,
                "trajectory": left_cell["trajectory"],
                "patch_excerpt": patch_excerpt(left_cell["path"]),
            },
            "right": {
                "metrics": right_metrics,
                "trajectory": right_cell["trajectory"],
                "patch_excerpt": patch_excerpt(right_cell["path"]),
            },
            "left_failed_tests": helpers.failed_verifier_tests(left_cell["path"]),
            "right_failed_tests": helpers.failed_verifier_tests(right_cell["path"]),
            "primary_driver": bucket,
            "first_consequential_divergence": (
                "The 1.2 patch introduced a deterministic filesystem-transport deadlock before grading completed."
                if bucket == "verifier timeout"
                else helpers.first_consequential_divergence(
                    left_cell["trajectory"]["patch"],
                    right_cell["trajectory"]["patch"],
                    left_metrics,
                    right_metrics,
                )
            ),
            "mechanism": "",
            "confidence": (
                "The bucket is a reproducible triage classification from grading, patch, "
                "resource, and reciprocal-rep evidence; it is not proof that wording caused the outcome."
            ),
        }
        packet["mechanism"] = mechanism_text(packet)
        text = json.dumps(packet, indent=2, sort_keys=True) + "\n"
        (PACKETS / packet_name).write_text(text)
        (REPORT_PACKETS / packet_name).write_text(text)
        packet_index.append(
            {
                "task": task,
                "rep": rep,
                "cohort": row["cohort"],
                "outcome": outcome,
                "driver": bucket,
                "mechanism": packet["mechanism"],
                "path": f"packets/{packet_name}",
            }
        )

    task_rows = []
    for task in task_names:
        left_solves = sum(
            solved(cells[(LEFT, task, rep)]["result"]) for rep in range(3)
        )
        right_solves = sum(
            solved(cells[(RIGHT, task, rep)]["result"]) for rep in range(3)
        )
        task_rows.append(
            {
                "task": task,
                "title": metadata[task]["title"],
                "language": metadata[task]["language"],
                "cohort": "pilot" if task in pilot_tasks else "holdout",
                "left_solves": left_solves,
                "right_solves": right_solves,
                "delta": right_solves - left_solves,
            }
        )

    language_rows = []
    for language in sorted({metadata[task]["language"] for task in task_names}):
        keys = [key for key in all_keys if metadata[key[0]]["language"] == language]
        language_rows.append({"language": language, **comparison_summary(keys, cells)})

    specialist_keys = [
        key
        for key in all_keys
        if cells[(RIGHT, *key)]["trajectory"]["skill_reads"]["property-based-testing"]
        or cells[(RIGHT, *key)]["trajectory"]["skill_reads"]["fuzzing"]
    ]
    specialist_summary = comparison_summary(specialist_keys, cells)
    specialist_summary["cells"] = len(specialist_keys)

    cost = {}
    for field, key in (
        ("cost", "cost"),
        ("tokens", "tokens"),
        ("wall_s", "wall_s"),
        ("tool_calls", "tool_calls"),
        ("turns", "turns"),
        ("patch_bytes", "patch_bytes"),
    ):
        left_value = config_summary[LEFT][key]
        right_value = config_summary[RIGHT][key]
        cost[field] = {
            "left": left_value,
            "right": right_value,
            "percent_delta": 100 * (right_value / left_value - 1),
        }

    return {
        "scope": {
            "question": "Does the cumulative contract-card and outer-surface redesign improve testing-skills@1.1.0 on the full 113-task corpus?",
            "roles": "Both sides are same-model config controls: GPT-5.6 Sol at low thinking under Pi 0.84.1.",
            "tasks": 113,
            "reps": 3,
            "matched_pairs": 339,
            "trajectories": 678,
            "pilot_pairs": len(pilot_keys),
            "holdout_pairs": len(holdout_keys),
        },
        "provenance": {
            "config_locks": LOCKS,
            "plan_identities": PLAN_IDENTITIES,
            "all_agent_exits_zero": True,
            "verifier_timeout": "testing-skills@1.2.0/kombu-virtual-queue-dead-lettering/rep2",
            "verifier_timeout_disposition": "Observed model failure: the saved patch deterministically blocks the official filesystem transport test; finalized without a repeated model call.",
            "delivery": "All three skills were advertised in all 678 trajectories.",
            "resource_flagged_pairs": len(all_keys) - len(resource_clean_keys),
        },
        "cohorts": cohorts,
        "config_summary": config_summary,
        "cost": cost,
        "specialist_summary": specialist_summary,
        "language_rows": language_rows,
        "task_rows": task_rows,
        "reciprocal_tasks": sorted(reciprocal_tasks),
        "packet_rule": "Every pair with a binary solve flip, verifier-exit discordance, or absolute partial-reward delta of at least 0.05.",
        "packet_count": len(packet_index),
        "flip_count": sum(
            packet["outcome"] in {"gain", "loss"} for packet in packet_index
        ),
        "driver_counts": dict(Counter(packet["driver"] for packet in packet_index)),
        "packets": packet_index,
        "matrix": matrix,
        "ledger": ledger,
        "decision": {
            "recommendation": "Do not promote testing-skills@1.2.0 as the new canonical package yet.",
            "reason": "The full score rose by 11 solves, but seven came from the outcome-informed pilot. The 267-pair holdout gained only four solves with 41 gains and 37 losses, while cost rose 8.8% and tokens 11.9% on that holdout.",
            "keep": "Keep contract cards and named outer-surface evidence as a promising experiment, especially for regressions such as textual-richlog-follow-state.",
            "next": "Split contract inventory from outer-surface wording and run a smaller randomized or predeclared A/B before changing the canonical skill package.",
        },
    }


def esc(value: Any) -> str:
    """Escape one report value."""
    return html.escape(str(value))


def outcome_pill(binary: float) -> str:
    """Render one compact binary-outcome marker."""
    return (
        '<span class="pill good">✓</span>'
        if binary == 1
        else '<span class="pill bad">×</span>'
    )


def render(data: dict[str, Any]) -> str:
    """Render the self-contained Tailnet HTML report."""
    all_summary = data["cohorts"]["all"]
    holdout = data["cohorts"]["holdout"]
    pilot = data["cohorts"]["pilot"]
    resource_clean = data["cohorts"]["resource_clean"]
    left_summary = data["config_summary"][LEFT]
    right_summary = data["config_summary"][RIGHT]
    cost = data["cost"]

    task_rows = "".join(
        f"<tr><td><code>{esc(row['task'])}</code></td><td>{esc(row['cohort'])}</td><td>{esc(row['language'])}</td>"
        f"<td>{row['left_solves']}/3</td><td>{row['right_solves']}/3</td>"
        f'<td><span class="tag {"good" if row["delta"] > 0 else "bad" if row["delta"] < 0 else "neutral"}">{row["delta"]:+d}</span></td></tr>'
        for row in sorted(
            data["task_rows"], key=lambda item: (-item["delta"], item["task"])
        )
    )
    language_rows = "".join(
        f"<tr><td>{esc(row['language'])}</td><td>{row['pairs']}</td><td>{row['left_solves']}</td><td>{row['right_solves']}</td>"
        f"<td>{row['solve_delta']:+d}</td><td>{row['gains']}</td><td>{row['losses']}</td></tr>"
        for row in data["language_rows"]
    )
    packet_rows = "".join(
        f"<tr><td><code>{esc(packet['task'])}</code> / rep{packet['rep']}</td><td>{esc(packet['cohort'])}</td>"
        f'<td><span class="tag {"good" if packet["outcome"] == "gain" else "bad" if packet["outcome"] == "loss" else "caution"}">{esc(packet["outcome"])}</span></td>'
        f'<td>{esc(packet["driver"])}</td><td>{esc(packet["mechanism"])}</td><td><a href="{esc(packet["path"])}">packet</a></td></tr>'
        for packet in data["packets"]
        if packet["outcome"] in {"gain", "loss"}
    )
    matrix_rows = "".join(
        f"<tr><td><code>{esc(row['task'])}</code></td><td>{row['rep']}</td><td>{esc(row['cohort'])}</td><td>{esc(row['language'])}</td>"
        f"<td>{outcome_pill(row['left_binary'])}<small>{row['left_partial']:.3f}</small></td>"
        f"<td>{outcome_pill(row['right_binary'])}<small>{row['right_partial']:.3f}</small></td></tr>"
        for row in data["matrix"]
    )
    max_solve = max(left_summary["solves"], right_summary["solves"])
    solve_bars = "".join(
        f'<div class="bar-row"><span>{esc(label)}</span><div class="bar-track"><div class="bar {"right" if label == "1.2.0" else ""}" style="width:{100 * solves / max_solve:.2f}%"></div></div><strong>{solves}/339</strong></div>'
        for label, solves in (
            ("1.1.0", left_summary["solves"]),
            ("1.2.0", right_summary["solves"]),
        )
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Testing skills 1.2 vs 1.1 · full 113</title><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#172033;--muted:#667085;--blue:#2563eb;--green:#16835b;--red:#c24141;--amber:#b7791f;--line:#dfe5ef}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}}main{{max-width:1500px;margin:auto;padding:32px}}.hero{{background:linear-gradient(135deg,#172554,#1d4ed8);color:white;border-radius:20px;padding:34px;margin-bottom:22px}}h1{{font-size:38px;line-height:1.06;margin:8px 0 12px}}h2{{margin-top:34px}}h3{{margin-top:24px}}.hero p{{max-width:980px;font-size:18px}}.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-weight:800;font-size:12px}}.pills{{display:flex;gap:8px;flex-wrap:wrap}}.pill,.tag{{display:inline-block;border-radius:999px;padding:3px 9px;font-weight:700;font-size:12px}}.pill.good,.tag.good{{background:#d8f4e8;color:#08714a}}.pill.bad,.tag.bad{{background:#fee2e2;color:#a32020}}.pill.caution,.tag.caution{{background:#fff0c2;color:#8a5a00}}.pill.neutral,.tag.neutral{{background:#e9eef8;color:#344054}}.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}.stat{{background:var(--surface);padding:18px;border:1px solid var(--line);border-radius:14px}}.stat span,.stat small{{display:block;color:var(--muted)}}.stat strong{{display:block;font-size:30px}}.callout{{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--blue);padding:18px 20px;border-radius:10px;margin:18px 0}}.callout.good{{border-left-color:var(--green)}}.callout.caution{{border-left-color:var(--amber)}}.callout.bad{{border-left-color:var(--red)}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.table-wrap{{overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#eef3fa;z-index:1;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}code{{font-size:12px}}a{{color:var(--blue)}}small{{display:block;color:var(--muted)}}.bar-card{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px}}.bar-row{{display:grid;grid-template-columns:60px 1fr 70px;gap:12px;align-items:center;margin:14px 0}}.bar-track{{height:16px;background:#e8edf5;border-radius:999px;overflow:hidden}}.bar{{height:100%;background:#64748b}}.bar.right{{background:var(--blue)}}@media(max-width:900px){{main{{padding:16px}}.stats{{grid-template-columns:1fr 1fr}}.grid{{grid-template-columns:1fr}}h1{{font-size:30px}}}}@media(max-width:520px){{.stats{{grid-template-columns:1fr}}}}
</style></head><body><main>
<section class="hero"><div class="eyebrow">113 tasks × 3 reps · same model · low thinking</div><h1>Promising score, weak holdout confirmation.</h1><p>Contract cards and outer-surface evidence raised the full score from <strong>142 to 153 solves</strong>. But seven of those eleven solves came from the outcome-informed pilot. On the 89-task holdout, the gain was only four solves amid 78 flips.</p><div class="pills"><span class="pill good">Full: +11 solves</span><span class="pill caution">Holdout: +4 solves</span><span class="pill bad">Do not promote yet</span><span class="pill neutral">678 trajectories</span></div></section>
<div class="stats"><div class="stat"><span>Full score</span><strong>142 → 153</strong><small>+3.24 percentage points</small></div><div class="stat"><span>Holdout score</span><strong>124 → 128</strong><small>+1.50 points across 267 pairs</small></div><div class="stat"><span>Full churn</span><strong>53 / 42</strong><small>gains / losses</small></div><div class="stat"><span>Cost</span><strong>+{cost["cost"]["percent_delta"]:.1f}%</strong><small>${cost["cost"]["left"]:.2f} → ${cost["cost"]["right"]:.2f}</small></div><div class="stat"><span>Specialist reads</span><strong>78 → 150</strong><small>cells reading PBT or fuzzing</small></div></div>
<div class="callout caution"><strong>Decision:</strong> do not replace <code>testing-skills@1.1.0</code> yet. Keep 1.2.0 as an experiment and split contract inventory from outer-surface wording. The full result is positive, but the predeclared holdout does not show a stable effect.</div>
<h2>Score and confirmation</h2><div class="grid"><div class="bar-card"><h3>Full 339-pair score</h3>{solve_bars}</div><div class="callout"><strong>Statistics:</strong> full exact McNemar p = {all_summary["mcnemar_p"]:.3f}. The paired-bootstrap 95% interval for the +{all_summary["solve_rate_delta_points"]:.2f}-point change is {all_summary["bootstrap_95_low_points"]:.2f} to {all_summary["bootstrap_95_high_points"]:.2f} points. The interval includes harm.</div></div>
<div class="table-wrap"><table><thead><tr><th>Cohort</th><th>Pairs</th><th>1.1 solves</th><th>1.2 solves</th><th>Δ</th><th>Gains</th><th>Losses</th><th>McNemar p</th><th>Bootstrap 95%</th></tr></thead><tbody>
<tr><td>Full</td><td>{all_summary["pairs"]}</td><td>{all_summary["left_solves"]}</td><td>{all_summary["right_solves"]}</td><td>{all_summary["solve_delta"]:+d}</td><td>{all_summary["gains"]}</td><td>{all_summary["losses"]}</td><td>{all_summary["mcnemar_p"]:.3f}</td><td>{all_summary["bootstrap_95_low_points"]:.2f} to {all_summary["bootstrap_95_high_points"]:.2f} pp</td></tr>
<tr><td>Outcome-informed pilot</td><td>{pilot["pairs"]}</td><td>{pilot["left_solves"]}</td><td>{pilot["right_solves"]}</td><td>{pilot["solve_delta"]:+d}</td><td>{pilot["gains"]}</td><td>{pilot["losses"]}</td><td>{pilot["mcnemar_p"]:.3f}</td><td>{pilot["bootstrap_95_low_points"]:.2f} to {pilot["bootstrap_95_high_points"]:.2f} pp</td></tr>
<tr><td><strong>89-task holdout</strong></td><td>{holdout["pairs"]}</td><td>{holdout["left_solves"]}</td><td>{holdout["right_solves"]}</td><td><strong>{holdout["solve_delta"]:+d}</strong></td><td>{holdout["gains"]}</td><td>{holdout["losses"]}</td><td>{holdout["mcnemar_p"]:.3f}</td><td>{holdout["bootstrap_95_low_points"]:.2f} to {holdout["bootstrap_95_high_points"]:.2f} pp</td></tr>
<tr><td>Resource-clean sensitivity</td><td>{resource_clean["pairs"]}</td><td>{resource_clean["left_solves"]}</td><td>{resource_clean["right_solves"]}</td><td>{resource_clean["solve_delta"]:+d}</td><td>{resource_clean["gains"]}</td><td>{resource_clean["losses"]}</td><td>{resource_clean["mcnemar_p"]:.3f}</td><td>{resource_clean["bootstrap_95_low_points"]:.2f} to {resource_clean["bootstrap_95_high_points"]:.2f} pp</td></tr>
</tbody></table></div>
<div class="callout"><strong>Resource sensitivity:</strong> thirteen pairs contain a resource-flagged cell. Excluding all thirteen leaves the same +11 solve delta (132 → 143), so resource events do not explain the result. The primary view remains intention-to-treat.</div>
<h2>Behavior changed more than score</h2><div class="table-wrap"><table><thead><tr><th>Config</th><th>Testing reads</th><th>PBT reads</th><th>Fuzz reads</th><th>Any specialist</th><th>Test patches</th><th>Property patches</th><th>Fuzz targets</th><th>Final-patch validation</th></tr></thead><tbody>
<tr><td><code>1.1.0</code></td><td>{left_summary["skill_reads"]["testing"]}</td><td>{left_summary["skill_reads"]["property-based-testing"]}</td><td>{left_summary["skill_reads"]["fuzzing"]}</td><td>{left_summary["specialist_read_cells"]}</td><td>{left_summary["test_patch_cells"]}</td><td>{left_summary["property_test_patch_cells"]}</td><td>{left_summary["fuzz_target_patch_cells"]}</td><td>{left_summary["final_patch_validation_cells"]}</td></tr>
<tr><td><code>1.2.0</code></td><td>{right_summary["skill_reads"]["testing"]}</td><td>{right_summary["skill_reads"]["property-based-testing"]}</td><td>{right_summary["skill_reads"]["fuzzing"]}</td><td>{right_summary["specialist_read_cells"]}</td><td>{right_summary["test_patch_cells"]}</td><td>{right_summary["property_test_patch_cells"]}</td><td>{right_summary["fuzz_target_patch_cells"]}</td><td>{right_summary["final_patch_validation_cells"]}</td></tr>
</tbody></table></div>
<div class="callout good"><strong>Routing improved:</strong> 1.2.0 nearly doubled specialist-reading cells from 78 to 150 and raised test-modifying patches from 253 to 282. The specialist-read cohort contributed +6 solves (69 → 75). But reading still did not produce any property-based test, and actual fuzz targets fell from seven to six.</div>
<h2>Cost and execution</h2><div class="table-wrap"><table><thead><tr><th>Measure</th><th>1.1.0</th><th>1.2.0</th><th>Change</th></tr></thead><tbody>
<tr><td>Tokens</td><td>{cost["tokens"]["left"]:,}</td><td>{cost["tokens"]["right"]:,}</td><td>{cost["tokens"]["percent_delta"]:+.1f}%</td></tr><tr><td>Cost</td><td>${cost["cost"]["left"]:.2f}</td><td>${cost["cost"]["right"]:.2f}</td><td>{cost["cost"]["percent_delta"]:+.1f}%</td></tr><tr><td>Agent wall time</td><td>{cost["wall_s"]["left"] / 3600:.1f} h</td><td>{cost["wall_s"]["right"] / 3600:.1f} h</td><td>{cost["wall_s"]["percent_delta"]:+.1f}%</td></tr><tr><td>Tool calls</td><td>{cost["tool_calls"]["left"]:,}</td><td>{cost["tool_calls"]["right"]:,}</td><td>{cost["tool_calls"]["percent_delta"]:+.1f}%</td></tr><tr><td>Patch bytes</td><td>{cost["patch_bytes"]["left"]:,}</td><td>{cost["patch_bytes"]["right"]:,}</td><td>{cost["patch_bytes"]["percent_delta"]:+.1f}%</td></tr></tbody></table></div>
<h2>Language split</h2><div class="table-wrap"><table><thead><tr><th>Language</th><th>Pairs</th><th>1.1 solves</th><th>1.2 solves</th><th>Δ</th><th>Gains</th><th>Losses</th></tr></thead><tbody>{language_rows}</tbody></table></div>
<div class="callout"><strong>Capability shape:</strong> Python gained 15 solves and Rust gained two; Go lost ten. TypeScript gained four and JavaScript was flat. This is not a uniform quality increase.</div>
<h2>Task-level movement</h2><div class="table-wrap"><table><thead><tr><th>Task</th><th>Cohort</th><th>Language</th><th>1.1</th><th>1.2</th><th>Δ</th></tr></thead><tbody>{task_rows}</tbody></table></div>
<div class="callout good"><strong>Outer-surface success:</strong> <code>textual-richlog-follow-state</code> improved from 0/3 to 2/3. The previous package consistently exercised the wrong string-level example; the redesigned contract language pushed two reps to the named RichLog observation.</div><div class="callout bad"><strong>Regression sentinel:</strong> <code>valibot-recursive-schema-composition</code> fell from 3/3 to 0/3. Several other prior strengths also regressed, including <code>dynamodb-toolbox-lazy-recursive-schemas</code> (3/3 → 1/3). Contract inventory did not prevent churn.</div>
<h2>Every solve flip ({data["flip_count"]})</h2><p>Packets include paired result metrics, session tool timelines, skill reads, changed files, patch excerpts, failed verifier tests, and the first consequential patch divergence. Driver labels are conservative triage buckets, not proof of wording causality.</p><div class="table-wrap"><table><thead><tr><th>Cell</th><th>Cohort</th><th>Direction</th><th>Driver</th><th>Observed mechanism</th><th>Evidence</th></tr></thead><tbody>{packet_rows}</tbody></table></div>
<h2>Complete task × rep table</h2><p>All 339 matched pairs appear below. Each marker shows binary outcome and partial reward.</p><div class="table-wrap"><table><thead><tr><th>Task</th><th>Rep</th><th>Cohort</th><th>Language</th><th>1.1.0</th><th>1.2.0</th></tr></thead><tbody>{matrix_rows}</tbody></table></div>
<h2>Conclusion</h2><div class="callout caution"><strong>Do not promote 1.2.0 yet.</strong> The full score is better and the resource-clean view agrees, but the independent holdout effect is small, noisy, and more expensive. Keep the ideas, not the release.</div><div class="callout"><strong>Next experiment:</strong> separate the contract inventory from the outer-surface requirement. Predeclare a smaller cross-language cohort with Go regression sentinels and Python gain sentinels. Require improvement on the holdout, not another outcome-selected aggregate.</div><div class="callout"><strong>Provenance:</strong> all 678 trajectories used GPT-5.6 Sol at low thinking under Pi 0.84.1. All agent exits were zero. Kombu 1.2 rep2 is an observed verifier timeout from a deterministic candidate deadlock, finalized from the saved patch without another model call. All three skills were advertised in every trajectory.</div>
</main></body></html>"""


def main() -> None:
    """Write reproducible JSON, packets, and self-contained HTML."""
    data = build()
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    (OUT / "full113-comparison.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n"
    )
    (REPORT / "index.html").write_text(render(data))
    print(
        json.dumps(
            {
                "pairs": data["scope"]["matched_pairs"],
                "solves": {
                    LEFT: data["config_summary"][LEFT]["solves"],
                    RIGHT: data["config_summary"][RIGHT]["solves"],
                },
                "holdout": data["cohorts"]["holdout"],
                "packets": data["packet_count"],
                "flips": data["flip_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
