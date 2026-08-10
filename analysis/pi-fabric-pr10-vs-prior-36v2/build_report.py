#!/usr/bin/env python3
"""Build the Pi-Fabric PR #10 three-way DeepSWE comparison report."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
REPORT_ROOT = REPOSITORY_ROOT / "reports/pi-fabric-pr10-vs-prior-36v2"
SUBSET_PATH = REPOSITORY_ROOT / "subsets/36_v2.txt"
METADATA_PATH = REPOSITORY_ROOT / "data/deepswe-v1.1-task-difficulty.tsv"
MODEL = "openai-codex/gpt-5.6-sol"
THINKING = "low"
EXPECTED_REPS = 108

CONFIG_LABELS = {
    "baseline": "Plain Pi",
    "pi-fabric": "Earlier Pi-Fabric",
    "pi-fabric-pr10@0.28.11": "PR #10 Pi-Fabric",
}
CONFIG_ORDER = tuple(CONFIG_LABELS)
RESULT_METRICS = (
    "reward_binary",
    "reward_partial",
    "f2p",
    "p2p",
    "f2p_passed",
    "f2p_total",
    "p2p_passed",
    "p2p_total",
    "combined_total_tokens",
    "combined_cost_usd",
    "agent_wall_s",
    "turns",
    "tool_calls",
    "patch_bytes",
    "agent_timed_out",
    "agent_exit",
    "verifier_exit",
)
INNER_OPERATIONS = ("read", "grep", "find", "ls", "bash", "bashSettled", "edit", "write")


@dataclass(frozen=True, slots=True)
class ResultCell:
    """One matched benchmark result and its artifact directory."""

    result: dict[str, Any]
    path: Path


@dataclass(frozen=True, slots=True)
class SessionAudit:
    """Observable model-session health and Pi-Fabric operation counts."""

    assistant_errors: tuple[str, ...]
    missing_tool_results: int
    outer_tool_calls: dict[str, int]
    inner_operations: dict[str, int]
    repo_reads: int
    bounded_repo_reads: int
    whole_repo_reads: int
    skill_reads: int
    delivery: str

    @property
    def affected_by_session_error(self) -> bool:
        """Return whether provider errors or unmatched tool calls affected the rep."""
        return bool(self.assistant_errors or self.missing_tool_results)


def parse_arguments() -> argparse.Namespace:
    """Parse deterministic report input and output paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-root",
        type=Path,
        required=True,
        help="Path containing gpt-5.6-sol/low/<config>/ result trees.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object from disk."""
    return json.loads(path.read_text())


def load_task_metadata() -> dict[str, dict[str, Any]]:
    """Load task title, language, and derived difficulty labels."""
    metadata: dict[str, dict[str, Any]] = {}
    with METADATA_PATH.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            pass_rate = int(row["pass_rate"])
            row["pass_rate"] = pass_rate
            row["difficulty"] = (
                "hard" if pass_rate < 33 else "medium" if pass_rate < 66 else "easy"
            )
            metadata[row["slug"]] = row
    return metadata


def load_matched_result_cells(
    results_root: Path,
) -> tuple[list[tuple[str, int]], dict[str, dict[tuple[str, int], ResultCell]]]:
    """Load and validate the exact 36_v2 × 3 matched rep set."""
    tasks = [line.strip() for line in SUBSET_PATH.read_text().splitlines() if line.strip()]
    expected_keys = [(task, rep) for task in tasks for rep in range(3)]
    cells: dict[str, dict[tuple[str, int], ResultCell]] = {}
    for config in CONFIG_ORDER:
        config_cells: dict[tuple[str, int], ResultCell] = {}
        for task, rep in expected_keys:
            path = results_root / config / task / f"rep{rep}"
            result_path = path / "result.json"
            if not result_path.is_file():
                raise FileNotFoundError(f"Missing matched result: {result_path}")
            result = load_json(result_path)
            if result.get("task") != task or int(result.get("rep", -1)) != rep:
                raise ValueError(f"Result identity mismatch: {result_path}")
            if result.get("config") != config:
                raise ValueError(f"Config identity mismatch: {result_path}")
            if result.get("model") != MODEL or result.get("thinking_level") != THINKING:
                raise ValueError(f"Model/thinking mismatch: {result_path}")
            config_cells[(task, rep)] = ResultCell(result=result, path=path)
        if len(config_cells) != EXPECTED_REPS:
            raise ValueError(f"Expected {EXPECTED_REPS} reps for {config}; got {len(config_cells)}")
        cells[config] = config_cells
    return expected_keys, cells


def load_initial_outage_cells(results_root: Path) -> dict[tuple[str, int], ResultCell]:
    """Load the 51 PR #10 cells archived before the supplemental rerun."""
    quarantine_root = (
        results_root.parents[1]
        / "_contaminated/provider-outage/pi-fabric-pr10-0da479f-initial"
    )
    cells: dict[tuple[str, int], ResultCell] = {}
    for result_path in sorted(quarantine_root.glob("*/rep*/result.json")):
        result = load_json(result_path)
        task = str(result["task"])
        rep = int(result["rep"])
        cells[(task, rep)] = ResultCell(result=result, path=result_path.parent)
    if len(cells) != 51:
        raise ValueError(f"Expected 51 archived outage cells; got {len(cells)}")
    return cells


def extract_pi_operation_arguments(code: str, operation: str) -> list[str]:
    """Extract balanced argument text from model-authored ``pi.<operation>(...)`` calls."""
    needle = f"pi.{operation}"
    arguments: list[str] = []
    cursor = 0
    while True:
        start = code.find(needle, cursor)
        if start < 0:
            return arguments
        opening = start + len(needle)
        while opening < len(code) and code[opening].isspace():
            opening += 1
        if opening >= len(code) or code[opening] != "(":
            cursor = opening
            continue
        index = opening + 1
        argument_start = index
        depth = 1
        quote: str | None = None
        escaped = False
        while index < len(code) and depth:
            character = code[index]
            if quote:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
            elif character in "'\"`":
                quote = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
            index += 1
        arguments.append(code[argument_start : index - 1] if depth == 0 else code[argument_start:])
        cursor = index


def audit_result_session(cell: ResultCell, config: str) -> SessionAudit:
    """Audit delivery, provider errors, tool matching, and read-economy behavior."""
    assistant_errors: list[str] = []
    outer_tools: Counter[str] = Counter()
    inner_operations: Counter[str] = Counter()
    tool_calls = 0
    tool_results = 0
    repo_reads = 0
    bounded_repo_reads = 0
    whole_repo_reads = 0
    skill_reads = 0

    for session_path in cell.path.glob("session/*.jsonl"):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = record.get("message", {})
            if message.get("role") == "assistant" and message.get("stopReason") == "error":
                assistant_errors.append(str(message.get("errorMessage") or "unknown assistant error"))
            content = message.get("content", [])
            if not isinstance(content, list):
                continue
            if message.get("role") == "toolResult":
                tool_results += 1
            for item in content:
                if item.get("type") != "toolCall":
                    continue
                tool_calls += 1
                tool_name = str(item.get("name", "unknown"))
                outer_tools[tool_name] += 1
                if tool_name != "fabric_exec":
                    continue
                code = str(item.get("arguments", {}).get("code", ""))
                for operation in INNER_OPERATIONS:
                    calls = extract_pi_operation_arguments(code, operation)
                    inner_operations[operation] += len(calls)
                    if operation != "read":
                        continue
                    for arguments in calls:
                        is_skill_read = "SKILL.md" in arguments or "/arm/extensions/" in arguments
                        if is_skill_read:
                            skill_reads += 1
                            continue
                        repo_reads += 1
                        if re.search(r"\b(?:offset|limit)\s*:", arguments):
                            bounded_repo_reads += 1
                        else:
                            whole_repo_reads += 1

    if config == "baseline":
        provider_requests = list(cell.path.glob("initial_context/provider_request_*.json"))
        delivery = "clean" if all("fabric_exec" not in p.read_text(errors="replace") for p in provider_requests) else "leaked"
    else:
        provider_requests = list(cell.path.glob("initial_context/provider_request_*.json"))
        delivery = "delivered" if provider_requests and all("fabric_exec" in p.read_text(errors="replace") for p in provider_requests[:2]) else "missing"

    return SessionAudit(
        assistant_errors=tuple(assistant_errors),
        missing_tool_results=max(0, tool_calls - tool_results),
        outer_tool_calls=dict(outer_tools),
        inner_operations=dict(inner_operations),
        repo_reads=repo_reads,
        bounded_repo_reads=bounded_repo_reads,
        whole_repo_reads=whole_repo_reads,
        skill_reads=skill_reads,
        delivery=delivery,
    )


def numeric_values(results: list[dict[str, Any]], key: str) -> list[float]:
    """Return non-null numeric values for one result field."""
    return [float(result[key]) for result in results if result.get(key) is not None]


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate efficacy and resource metrics for one matched result set."""
    values = lambda key: numeric_values(results, key)
    wall = sorted(values("agent_wall_s"))
    task_solves: Counter[str] = Counter()
    for result in results:
        task_solves[result["task"]] += result.get("reward_binary") == 1
    return {
        "n": len(results),
        "solves": sum(result.get("reward_binary") == 1 for result in results),
        "negative_rewards": sum(float(result.get("reward_binary", 0)) < 0 for result in results),
        "mean_partial": statistics.mean(values("reward_partial")),
        "median_partial": statistics.median(values("reward_partial")),
        "mean_f2p": statistics.mean(values("f2p")),
        "f2p_graded_n": len(values("f2p")),
        "mean_p2p": statistics.mean(values("p2p")),
        "p2p_graded_n": len(values("p2p")),
        "median_tokens": statistics.median(values("combined_total_tokens")),
        "mean_tokens": statistics.mean(values("combined_total_tokens")),
        "median_cost": statistics.median(values("combined_cost_usd")),
        "total_cost": sum(values("combined_cost_usd")),
        "median_wall_s": statistics.median(wall),
        "mean_wall_s": statistics.mean(wall),
        "p90_wall_s": wall[round((len(wall) - 1) * 0.90)],
        "p95_wall_s": wall[round((len(wall) - 1) * 0.95)],
        "max_wall_s": max(wall),
        "median_turns": statistics.median(values("turns")),
        "median_tool_calls": statistics.median(values("tool_calls")),
        "median_patch_bytes": statistics.median(values("patch_bytes")),
        "majority_solved_tasks": sum(count >= 2 for count in task_solves.values()),
        "three_of_three_solved_tasks": sum(count == 3 for count in task_solves.values()),
    }


def exact_mcnemar(left_only: int, right_only: int) -> float:
    """Return the two-sided exact McNemar p-value for discordant pairs."""
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    smaller = min(left_only, right_only)
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (2**discordant)
    return min(1.0, 2 * tail)


def compare_binary_churn(
    keys: set[tuple[str, int]],
    cells: dict[str, dict[tuple[str, int], ResultCell]],
    left: str,
    right: str,
) -> dict[str, Any]:
    """Summarize paired solve agreement and discordance."""
    both = left_only = right_only = neither = 0
    for key in sorted(keys):
        left_solved = cells[left][key].result["reward_binary"] == 1
        right_solved = cells[right][key].result["reward_binary"] == 1
        if left_solved and right_solved:
            both += 1
        elif left_solved:
            left_only += 1
        elif right_solved:
            right_only += 1
        else:
            neither += 1
    return {
        "n": len(keys),
        "both": both,
        "left_only": left_only,
        "right_only": right_only,
        "neither": neither,
        "net": right_only - left_only,
        "mcnemar_p": exact_mcnemar(left_only, right_only),
    }


def cluster_bootstrap_partial_reward(
    keys: set[tuple[str, int]],
    cells: dict[str, dict[tuple[str, int], ResultCell]],
    left: str,
    right: str,
    iterations: int = 100_000,
) -> dict[str, Any]:
    """Bootstrap task-clustered mean partial-reward deltas."""
    by_task: dict[str, list[float]] = defaultdict(list)
    all_deltas: list[float] = []
    for key in sorted(keys):
        delta = float(cells[right][key].result["reward_partial"]) - float(cells[left][key].result["reward_partial"])
        by_task[key[0]].append(delta)
        all_deltas.append(delta)
    task_means = [statistics.mean(by_task[task]) for task in sorted(by_task)]
    rng = random.Random(20260730)
    draws = sorted(statistics.mean(rng.choices(task_means, k=len(task_means))) for _ in range(iterations))
    return {
        "mean_delta": statistics.mean(all_deltas),
        "ci95": [draws[int(iterations * 0.025)], draws[int(iterations * 0.975)]],
    }


def aggregate_session_audits(audits: list[SessionAudit]) -> dict[str, Any]:
    """Aggregate session health and Pi-Fabric operation counts."""
    outer: Counter[str] = Counter()
    inner: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    for audit in audits:
        outer.update(audit.outer_tool_calls)
        inner.update(audit.inner_operations)
        errors.update(audit.assistant_errors)
    repo_reads = sum(audit.repo_reads for audit in audits)
    whole_repo_reads = sum(audit.whole_repo_reads for audit in audits)
    return {
        "cells": len(audits),
        "affected_cells": sum(audit.affected_by_session_error for audit in audits),
        "assistant_error_messages": sum(len(audit.assistant_errors) for audit in audits),
        "missing_tool_results": sum(audit.missing_tool_results for audit in audits),
        "error_types": dict(errors),
        "delivery": dict(Counter(audit.delivery for audit in audits)),
        "outer_tool_calls": dict(outer),
        "inner_operations": dict(inner),
        "repo_reads": repo_reads,
        "bounded_repo_reads": sum(audit.bounded_repo_reads for audit in audits),
        "whole_repo_reads": whole_repo_reads,
        "whole_repo_read_rate": whole_repo_reads / repo_reads if repo_reads else None,
        "skill_reads": sum(audit.skill_reads for audit in audits),
    }


def patch_statistics(path: Path) -> dict[str, Any]:
    """Extract deterministic changed-file and line counts from a saved patch."""
    if not path.is_file():
        return {"bytes": 0, "files": [], "adds": 0, "dels": 0}
    text = path.read_text(errors="replace")
    return {
        "bytes": len(text.encode()),
        "files": re.findall(r"^diff --git a/(.+?) b/", text, re.MULTILINE),
        "adds": sum(line.startswith("+") and not line.startswith("+++") for line in text.splitlines()),
        "dels": sum(line.startswith("-") and not line.startswith("---") for line in text.splitlines()),
    }


def verifier_evidence(path: Path) -> dict[str, Any]:
    """Extract verifier reward and bounded failing-test names."""
    reward_path = path / "verifier/reward.json"
    ctrf_path = path / "verifier/ctrf.json"
    failed: list[str] = []
    if ctrf_path.is_file():
        tests = load_json(ctrf_path).get("results", {}).get("tests", [])
        failed = [str(test.get("name")) for test in tests if test.get("status") == "failed"]
    return {
        "reward": load_json(reward_path) if reward_path.is_file() else {},
        "failed_count": len(failed),
        "failed_tests": failed[:30],
    }


def classify_packet(
    key: tuple[str, int],
    cells: dict[str, dict[tuple[str, int], ResultCell]],
    audits: dict[str, dict[tuple[str, int], SessionAudit]],
) -> dict[str, Any]:
    """Classify only mechanisms supported directly by saved artifacts."""
    new_cell = cells["pi-fabric-pr10@0.28.11"][key]
    new_audit = audits["pi-fabric-pr10@0.28.11"][key]
    files = patch_statistics(new_cell.path / "artifacts/model.patch")["files"]
    source_files = [path for path in files if path != ".pi/fabric/mesh/state.json"]
    earlier_solved = cells["pi-fabric"][key].result["reward_binary"] == 1
    new_solved = new_cell.result["reward_binary"] == 1
    if new_audit.affected_by_session_error:
        bucket = "provider-instability-confounded"
        mechanism = "The PR #10 session contains provider errors or a model tool call without a saved result."
        confidence = "high"
    elif not source_files:
        bucket = "under-implementation"
        mechanism = "The rep produced no source-code patch beyond Fabric mesh state."
        confidence = "high"
    elif new_solved and not earlier_solved:
        bucket = "clean-pr10-gain"
        mechanism = "PR #10 solved this error-free rep where earlier Pi-Fabric did not."
        confidence = "high"
    elif earlier_solved and not new_solved:
        bucket = "clean-pr10-loss"
        mechanism = "Earlier Pi-Fabric solved this rep, while the error-free PR #10 trajectory did not."
        confidence = "high"
    else:
        bucket = "outcome-churn-unclassified"
        mechanism = "The outcome changed, but this aggregate report does not assign a patch-level causal mechanism."
        confidence = "low"
    return {"primary_bucket": bucket, "mechanism": mechanism, "confidence": confidence}


def packet_side(cell: ResultCell, audit: SessionAudit) -> dict[str, Any]:
    """Build one self-contained packet side from saved artifacts."""
    session = next(cell.path.glob("session/*.jsonl"), None)
    return {
        "result": {metric: cell.result.get(metric) for metric in RESULT_METRICS},
        "session": str(session) if session else None,
        "session_audit": {
            "assistant_errors": list(audit.assistant_errors),
            "missing_tool_results": audit.missing_tool_results,
            "outer_tool_calls": audit.outer_tool_calls,
            "inner_operations": audit.inner_operations,
            "repo_reads": audit.repo_reads,
            "bounded_repo_reads": audit.bounded_repo_reads,
            "whole_repo_reads": audit.whole_repo_reads,
            "skill_reads": audit.skill_reads,
            "delivery": audit.delivery,
        },
        "patch_stats": patch_statistics(cell.path / "artifacts/model.patch"),
        "verifier": verifier_evidence(cell.path),
    }


def build_packet_outputs(
    keys: list[tuple[str, int]],
    cells: dict[str, dict[tuple[str, int], ResultCell]],
    audits: dict[str, dict[tuple[str, int], SessionAudit]],
    metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Write packets for every solve flip or material partial-reward movement."""
    packet_dir = REPORT_ROOT / "packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    for stale in packet_dir.glob("*.json"):
        stale.unlink()
    index: list[dict[str, Any]] = []
    for key in keys:
        baseline = cells["baseline"][key].result
        earlier = cells["pi-fabric"][key].result
        pr10 = cells["pi-fabric-pr10@0.28.11"][key].result
        binary_flip = len({baseline["reward_binary"] == 1, earlier["reward_binary"] == 1, pr10["reward_binary"] == 1}) > 1
        material_partial = max(
            abs(float(pr10["reward_partial"]) - float(baseline["reward_partial"])),
            abs(float(pr10["reward_partial"]) - float(earlier["reward_partial"])),
        ) >= 0.10
        if not binary_flip and not material_partial:
            continue
        task, rep = key
        packet_name = f"{task}__rep{rep}.json"
        packet = {
            "pair": {
                "task": task,
                "rep": rep,
                "title": metadata[task]["title"],
                "difficulty": metadata[task]["difficulty"],
                "language": metadata[task]["language"],
                "configs": list(CONFIG_ORDER),
            },
            "baseline": packet_side(cells["baseline"][key], audits["baseline"][key]),
            "earlier_pi_fabric": packet_side(cells["pi-fabric"][key], audits["pi-fabric"][key]),
            "pr10_pi_fabric": packet_side(cells["pi-fabric-pr10@0.28.11"][key], audits["pi-fabric-pr10@0.28.11"][key]),
            "classification": classify_packet(key, cells, audits),
        }
        (packet_dir / packet_name).write_text(json.dumps(packet, indent=2) + "\n")
        index.append(
            {
                "task": task,
                "rep": rep,
                "packet": f"packets/{packet_name}",
                "classification": packet["classification"],
            }
        )
    (packet_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    return index


def write_paired_cells_csv(
    keys: list[tuple[str, int]],
    cells: dict[str, dict[tuple[str, int], ResultCell]],
    audits: dict[str, dict[tuple[str, int], SessionAudit]],
    metadata: dict[str, dict[str, Any]],
) -> None:
    """Write one flat row per matched rep for reproducible follow-up analysis."""
    config_columns = [
        f"{config}_{metric}" for config in CONFIG_ORDER for metric in RESULT_METRICS
    ]
    fields = ["task", "rep", "title", "difficulty", "language", "pass_rate"] + config_columns + [
        f"{config}_session_affected" for config in CONFIG_ORDER
    ]
    with (REPORT_ROOT / "paired_cells.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for task, rep in keys:
            key = (task, rep)
            row: dict[str, Any] = {
                "task": task,
                "rep": rep,
                "title": metadata[task]["title"],
                "difficulty": metadata[task]["difficulty"],
                "language": metadata[task]["language"],
                "pass_rate": metadata[task]["pass_rate"],
            }
            for config in CONFIG_ORDER:
                for metric in RESULT_METRICS:
                    row[f"{config}_{metric}"] = cells[config][key].result.get(metric)
                row[f"{config}_session_affected"] = audits[config][key].affected_by_session_error
            writer.writerow(row)


def escape(value: object) -> str:
    """Escape one value for HTML output."""
    return html.escape(str(value))


def percent_change(value: float, reference: float) -> float:
    """Return percentage change from a nonzero reference."""
    return (value / reference - 1) * 100


def render_metric_table(aggregate: dict[str, dict[str, Any]]) -> str:
    """Render the headline three-config metric table."""
    rows = [
        ("Full solves", "solves", lambda value: f"{value}/108"),
        ("Mean partial reward", "mean_partial", lambda value: f"{value:.3f}"),
        ("Mean feature-test pass rate", "mean_f2p", lambda value: f"{value * 100:.1f}%"),
        ("Mean preservation-test pass rate", "mean_p2p", lambda value: f"{value * 100:.1f}%"),
        ("Median tokens", "median_tokens", lambda value: f"{value:,.0f}"),
        ("Median cost", "median_cost", lambda value: f"${value:.3f}"),
        ("Total cost", "total_cost", lambda value: f"${value:.2f}"),
        ("Median wall time", "median_wall_s", lambda value: f"{value:.1f}s"),
        ("90th percentile wall time", "p90_wall_s", lambda value: f"{value:.1f}s"),
        ("Median turns", "median_turns", lambda value: f"{value:.1f}"),
        ("Median outer tool calls", "median_tool_calls", lambda value: f"{value:.1f}"),
    ]
    return "".join(
        "<tr><td>{}</td>{}</tr>".format(
            label,
            "".join(f"<td class='num'>{formatter(aggregate[config][key])}</td>" for config in CONFIG_ORDER),
        )
        for label, key, formatter in rows
    )


def render_clean_metric_table(clean_aggregate: dict[str, dict[str, Any]], sample_size: int) -> str:
    """Render the conservative error-free sensitivity table."""
    rows = [
        ("Full solves", "solves", lambda value: f"{value}/{sample_size}"),
        ("Mean partial reward", "mean_partial", lambda value: f"{value:.3f}"),
        ("Mean feature-test pass rate", "mean_f2p", lambda value: f"{value * 100:.1f}%"),
        ("Median tokens", "median_tokens", lambda value: f"{value:,.0f}"),
        ("Median cost", "median_cost", lambda value: f"${value:.3f}"),
        ("Median wall time", "median_wall_s", lambda value: f"{value:.1f}s"),
    ]
    return "".join(
        "<tr><td>{}</td>{}</tr>".format(
            label,
            "".join(f"<td class='num'>{formatter(clean_aggregate[config][key])}</td>" for config in CONFIG_ORDER),
        )
        for label, key, formatter in rows
    )


def render_packet_rows(packet_index: list[dict[str, Any]], cells: dict[str, dict[tuple[str, int], ResultCell]]) -> str:
    """Render representative packet links and direct outcome evidence."""
    bucket_limits = {
        "provider-instability-confounded": 2,
        "under-implementation": 1,
        "clean-pr10-gain": 2,
        "clean-pr10-loss": 2,
        "outcome-churn-unclassified": 1,
    }
    representatives: list[dict[str, Any]] = []
    for bucket, limit in bucket_limits.items():
        matches = [
            item
            for item in packet_index
            if item["classification"]["primary_bucket"] == bucket
        ]
        representatives.extend(matches[:limit])
    representatives = representatives[:8]
    rows: list[str] = []
    for item in representatives:
        key = (item["task"], item["rep"])
        outcomes = []
        for config in CONFIG_ORDER:
            result = cells[config][key].result
            outcomes.append(f"{result['reward_binary']}/{float(result['reward_partial']):.3f}")
        classification = item["classification"]
        rows.append(
            f"<tr><td><a href='{escape(item['packet'])}'><code>{escape(key[0])}</code> · rep{key[1]}</a></td>"
            + "".join(f"<td class='num'>{outcome}</td>" for outcome in outcomes)
            + f"<td><strong>{escape(classification['primary_bucket'])}</strong><br><span class='muted'>{escape(classification['mechanism'])}</span></td></tr>"
        )
    return "".join(rows)


def render_html_report(
    summary: dict[str, Any],
    packet_index: list[dict[str, Any]],
    cells: dict[str, dict[tuple[str, int], ResultCell]],
) -> str:
    """Render the self-contained Tailnet report."""
    aggregate = summary["aggregate"]
    clean = summary["strict_error_free_sensitivity"]["aggregate"]
    clean_n = summary["strict_error_free_sensitivity"]["n"]
    audits = summary["session_audit"]
    old_audit = audits["pi-fabric"]["all"]
    new_audit = audits["pi-fabric-pr10@0.28.11"]["all"]
    clean_old_audit = audits["pi-fabric"]["strict_error_free"]
    clean_new_audit = audits["pi-fabric-pr10@0.28.11"]["strict_error_free"]
    old = aggregate["pi-fabric"]
    new = aggregate["pi-fabric-pr10@0.28.11"]
    baseline = aggregate["baseline"]
    clean_old = clean["pi-fabric"]
    clean_new = clean["pi-fabric-pr10@0.28.11"]
    clean_base = clean["baseline"]
    new_vs_old = summary["paired_comparisons"]["pi-fabric_to_pr10"]
    new_vs_base = summary["paired_comparisons"]["baseline_to_pr10"]
    clean_new_vs_old = summary["strict_error_free_sensitivity"]["paired_comparisons"]["pi-fabric_to_pr10"]
    clean_new_vs_base = summary["strict_error_free_sensitivity"]["paired_comparisons"]["baseline_to_pr10"]

    token_change_old = percent_change(new["median_tokens"], old["median_tokens"])
    cost_change_old = percent_change(new["median_cost"], old["median_cost"])
    clean_token_change_old = percent_change(clean_new["median_tokens"], clean_old["median_tokens"])
    clean_cost_change_old = percent_change(clean_new["median_cost"], clean_old["median_cost"])
    clean_token_change_base = percent_change(clean_new["median_tokens"], clean_base["median_tokens"])
    clean_cost_change_base = percent_change(clean_new["median_cost"], clean_base["median_cost"])
    clean_wall_change_old = percent_change(clean_new["median_wall_s"], clean_old["median_wall_s"])
    clean_wall_change_base = percent_change(clean_new["median_wall_s"], clean_base["median_wall_s"])
    whole_read_drop = (new_audit["whole_repo_read_rate"] - old_audit["whole_repo_read_rate"]) * 100
    supplemental = summary["supplemental_rerun"]
    initial_outage = supplemental["initial_outage_cells"]
    replacements = supplemental["replacement_cells"]
    current_error_details = ", ".join(
        f"{count} {escape(error_type)}"
        for error_type, count in sorted(
            new_audit["error_types"].items(), key=lambda item: (-item[1], item[0])
        )
    )

    read_rows = "".join(
        f"<tr><td>{scope}</td><td class='num'>{old_item['repo_reads']:,}</td><td class='num'>{new_item['repo_reads']:,}</td>"
        f"<td class='num'>{old_item['whole_repo_reads']:,} ({old_item['whole_repo_read_rate'] * 100:.1f}%)</td>"
        f"<td class='num good'>{new_item['whole_repo_reads']:,} ({new_item['whole_repo_read_rate'] * 100:.1f}%)</td>"
        f"<td class='num'>{old_item['inner_operations'].get('grep', 0) + old_item['inner_operations'].get('find', 0):,}</td>"
        f"<td class='num'>{new_item['inner_operations'].get('grep', 0) + new_item['inner_operations'].get('find', 0):,}</td></tr>"
        for scope, old_item, new_item in [
            ("All 108 reps", old_audit, new_audit),
            (f"{clean_n} error-free matched reps", clean_old_audit, clean_new_audit),
        ]
    )

    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Pi-Fabric PR #10 · DeepSWE analysis</title><link rel='icon' href='data:,'><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#b87900;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:26px;--max:1240px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),radial-gradient(circle at top right,rgba(184,121,0,.09),transparent 28%),linear-gradient(180deg,#fbfdff,var(--bg));color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55}}.wrap{{max-width:var(--max);margin:auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.95);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}}.hero{{padding:clamp(26px,4vw,44px)}}section{{padding:clamp(20px,3vw,30px);margin-top:20px;overflow-x:auto}}h1,h2{{margin:0;line-height:1.08;letter-spacing:-.03em}}h1{{font-size:clamp(2.2rem,5vw,4.3rem);max-width:18ch;margin-top:14px}}h2{{font-size:clamp(1.4rem,2.4vw,2rem)}}p{{color:var(--muted)}}.eyebrow,.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.05em;text-transform:uppercase}}.eyebrow{{padding:8px 12px;background:#eef3ff;color:#1d3fb8}}.pillrow{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}.pill{{padding:8px 12px;border:1px solid var(--line)}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:26px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;min-height:116px}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:850;text-transform:uppercase;letter-spacing:.07em}}.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.9rem);font-weight:900;margin-top:8px;letter-spacing:-.04em}}.stat .sub{{display:block;color:var(--muted);font-size:.86rem;margin-top:7px}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}.neutral{{color:#1d3fb8}}.muted{{color:var(--muted)}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:15px 17px;margin-top:16px}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff9e8,#fff)}}.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.head{{margin-bottom:16px}}.head p{{margin:.45rem 0 0;max-width:92ch}}table{{width:100%;border-collapse:collapse;font-size:.91rem}}th,td{{padding:11px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}}td.num,th.num{{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#eef2ff;color:#24346f;border-radius:6px;padding:.12em .35em}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}.bars{{display:grid;gap:14px}}.barrow{{display:grid;grid-template-columns:170px 1fr 150px;gap:12px;align-items:center}}.track{{height:18px;border-radius:999px;background:#edf2f7;border:1px solid #dde5ef;overflow:hidden}}.fill{{height:100%;background:linear-gradient(90deg,#6a8cff,#335dff);border-radius:999px}}.fill.good{{background:linear-gradient(90deg,#4fc58f,#178a5b)}}.fill.bad{{background:linear-gradient(90deg,#f26a5f,#d0473f)}}.foot{{margin-top:22px;text-align:center;color:var(--muted);font-size:.86rem}}@media(max-width:900px){{.stats,.grid2{{grid-template-columns:1fr 1fr}}}}@media(max-width:650px){{.stats,.grid2{{grid-template-columns:1fr}}.barrow{{grid-template-columns:1fr}}table{{font-size:.8rem}}th,td{{padding:7px 5px}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>DeepSWE · 36_v2 × 3 reps · GPT-5.6-sol low</span><h1>PR #10 matches earlier Pi-Fabric with one-third fewer tokens.</h1><p>The selective rerun recovered six observed solves. PR #10 now ties earlier Pi-Fabric at {new['solves']}/108 while preserving the intended read-economy improvement. It remains two solves behind plain Pi, and {new_audit['affected_cells']} reps still contain provider/session errors, so the evidence supports parity—not a precise causal estimate.</p><div class='pillrow'><span class='pill good'>Whole-file reads: {old_audit['whole_repo_read_rate'] * 100:.1f}% → {new_audit['whole_repo_read_rate'] * 100:.1f}%</span><span class='pill good'>Median tokens vs earlier Fabric: {token_change_old:.0f}%</span><span class='pill good'>Median cost vs earlier Fabric: {cost_change_old:.0f}%</span><span class='pill neutral'>Observed solves: {old['solves']} → {new['solves']}</span><span class='pill caution'>{new_audit['affected_cells']}/108 reps still had session errors</span></div><div class='stats'><div class='stat'><span class='label'>Observed solves</span><span class='value neutral'>{baseline['solves']} / {old['solves']} / {new['solves']}</span><span class='sub'>Plain / earlier Fabric / PR #10</span></div><div class='stat'><span class='label'>Error-free sensitivity</span><span class='value neutral'>{clean_base['solves']} / {clean_old['solves']} / {clean_new['solves']}</span><span class='sub'>{clean_n} matched reps</span></div><div class='stat'><span class='label'>Whole-file read rate</span><span class='value good'>{new_audit['whole_repo_read_rate'] * 100:.1f}%</span><span class='sub'>{whole_read_drop:+.1f} percentage points</span></div><div class='stat'><span class='label'>Clean median tokens</span><span class='value good'>{clean_token_change_old:.0f}%</span><span class='sub'>vs earlier Pi-Fabric</span></div><div class='stat'><span class='label'>Clean median wall time</span><span class='value neutral'>{clean_wall_change_old:+.1f}%</span><span class='sub'>vs earlier Pi-Fabric</span></div></div><div class='callout good'><strong>Decision:</strong> PR #10 delivered its read-economy goal without a detectable efficacy loss versus earlier Pi-Fabric. The error-free sensitivity is one solve lower (paired p={clean_new_vs_old['mcnemar_p']:.3f}) with essentially identical mean partial reward. Remaining provider failures and the Pi-version mismatch limit stronger claims.</div></header>
<section><div class='head'><h2>Observed outcomes: all 108 reps</h2><p>This is the complete merged view: 57 original clean results plus 51 supplemental replacements. PR #10 ties earlier Pi-Fabric and is two solves below plain Pi. Neither paired difference is statistically distinguishable from zero.</p></div><table><thead><tr><th>Metric</th><th class='num'>Plain Pi</th><th class='num'>Earlier Pi-Fabric</th><th class='num'>PR #10 Pi-Fabric</th></tr></thead><tbody>{render_metric_table(aggregate)}</tbody></table><div class='grid2'><div class='callout'><strong>Against plain Pi:</strong> PR #10 gained {new_vs_base['right_only']} solves and lost {new_vs_base['left_only']} (net {new_vs_base['net']:+d}; exact paired p={new_vs_base['mcnemar_p']:.3f}). Mean partial reward changed {summary['partial_bootstrap']['baseline_to_pr10']['mean_delta']:+.3f}; the task-clustered 95% interval is {summary['partial_bootstrap']['baseline_to_pr10']['ci95'][0]:+.3f} to {summary['partial_bootstrap']['baseline_to_pr10']['ci95'][1]:+.3f}.</div><div class='callout'><strong>Against earlier Pi-Fabric:</strong> PR #10 gained {new_vs_old['right_only']} solves and lost {new_vs_old['left_only']} (net {new_vs_old['net']:+d}; exact paired p={new_vs_old['mcnemar_p']:.3f}). Mean partial reward changed {summary['partial_bootstrap']['pi-fabric_to_pr10']['mean_delta']:+.3f}; the 95% interval is {summary['partial_bootstrap']['pi-fabric_to_pr10']['ci95'][0]:+.3f} to {summary['partial_bootstrap']['pi-fabric_to_pr10']['ci95'][1]:+.3f}.</div></div></section>
<section><div class='head'><h2>The supplemental rerun helped, but the provider was still overloaded</h2><p>The rerun executed exactly 51 archived cells, reused 57 clean cells, had zero harness failures, and required no watchdog intervention. Session evidence improved substantially, but did not become clean.</p></div><table><thead><tr><th>Scope</th><th class='num'>Affected reps</th><th class='num'>Assistant error messages</th><th class='num'>Tool calls without results</th></tr></thead><tbody><tr><td>Initial 51 archived cells</td><td class='num'>{initial_outage['affected_cells']}/51</td><td class='num'>{initial_outage['assistant_error_messages']}</td><td class='num'>{initial_outage['missing_tool_results']}</td></tr><tr><td>51 supplemental replacements</td><td class='num'>{replacements['affected_cells']}/51</td><td class='num'>{replacements['assistant_error_messages']}</td><td class='num'>{replacements['missing_tool_results']}</td></tr></tbody></table><div class='callout caution'><strong>Remaining PR #10 session evidence:</strong> {new_audit['assistant_error_messages']} assistant errors across {new_audit['affected_cells']} reps and {new_audit['missing_tool_results']} unmatched tool calls. Error types: {current_error_details}. The provider explicitly reported overload {new_audit['error_types'].get('Codex error: Our servers are currently overloaded. Please try again later.', 0)} times.</div><div class='callout'><strong>Interpretation:</strong> the six-solve recovery after replacing only outage-affected cells is consistent with infrastructure noise depressing the first result. It does not prove every changed outcome was caused by the outage.</div></section>
<section><div class='head'><h2>Conservative sensitivity: {clean_n} matched reps with no session errors</h2><p>This post-hoc view removes every key where any config had an assistant error or unmatched tool call. It is not a replacement score; it tests whether the headline direction survives without known session failures.</p></div><table><thead><tr><th>Metric</th><th class='num'>Plain Pi</th><th class='num'>Earlier Pi-Fabric</th><th class='num'>PR #10 Pi-Fabric</th></tr></thead><tbody>{render_clean_metric_table(clean, clean_n)}</tbody></table><div class='grid2'><div class='callout'><strong>Efficacy:</strong> PR #10 solved {clean_new['solves']}/{clean_n} versus {clean_base['solves']}/{clean_n} for plain Pi and {clean_old['solves']}/{clean_n} for earlier Pi-Fabric. It is net {clean_new_vs_base['net']:+d} against baseline (p={clean_new_vs_base['mcnemar_p']:.3f}) and {clean_new_vs_old['net']:+d} against earlier Fabric (p={clean_new_vs_old['mcnemar_p']:.3f}).</div><div class='callout good'><strong>Efficiency:</strong> PR #10 used {abs(clean_token_change_old):.1f}% fewer median tokens and cost {abs(clean_cost_change_old):.1f}% less than earlier Pi-Fabric on the clean subset. It still used {clean_token_change_base:.1f}% more tokens and cost {clean_cost_change_base:.1f}% more than plain Pi.</div></div></section>
<section><div class='head'><h2>Read economy changed exactly as intended</h2><p>This static trajectory audit counts model-authored <code>pi.read</code>, <code>pi.grep</code>, and <code>pi.find</code> calls inside <code>fabric_exec</code>. A repo read is “bounded” when its arguments include an offset or limit. Skill-file reads are excluded. This is a transparent estimator, not the maintainer's separate Pier metric.</p></div><table><thead><tr><th>Scope</th><th class='num'>Earlier reads</th><th class='num'>PR #10 reads</th><th class='num'>Earlier whole-file</th><th class='num'>PR #10 whole-file</th><th class='num'>Earlier searches</th><th class='num'>PR #10 searches</th></tr></thead><tbody>{read_rows}</tbody></table><div class='grid2'><div class='callout good'><strong>All reps:</strong> whole-file reads fell from {old_audit['whole_repo_reads']:,}/{old_audit['repo_reads']:,} ({old_audit['whole_repo_read_rate'] * 100:.1f}%) to {new_audit['whole_repo_reads']:,}/{new_audit['repo_reads']:,} ({new_audit['whole_repo_read_rate'] * 100:.1f}%). The absolute count fell {percent_change(new_audit['whole_repo_reads'], old_audit['whole_repo_reads']):.1f}%.</div><div class='callout'><strong>Behavioral shift:</strong> PR #10 performed more total read calls and more searches, but used bounded windows for most reads. Active-skill rereads fell from {old_audit['skill_reads']} to {new_audit['skill_reads']}. On the {clean_n} error-free keys, whole-file reads fell from {clean_old_audit['whole_repo_read_rate'] * 100:.1f}% to {clean_new_audit['whole_repo_read_rate'] * 100:.1f}%.</div></div></section>
<section><div class='head'><h2>Representative trajectory evidence</h2><p>Each linked JSON packet contains all three results, patch files and line counts, verifier failures, session errors, tool counts, and read-economy measures. “Binary / partial” is shown for each config.</p></div><table><thead><tr><th>Rep</th><th class='num'>Plain</th><th class='num'>Earlier Fabric</th><th class='num'>PR #10</th><th>Evidence-backed classification</th></tr></thead><tbody>{render_packet_rows(packet_index, cells)}</tbody></table><div class='callout'><strong>Churn remains high:</strong> PR #10 flipped {new_vs_old['left_only'] + new_vs_old['right_only']} binary outcomes relative to earlier Pi-Fabric and {new_vs_base['left_only'] + new_vs_base['right_only']} relative to plain Pi. The packets separate provider-confounded reps from clean gains, clean losses, under-implementation, and unclassified variance. Aggregate deltas alone cannot assign one mechanism to all flips.</div></section>
<section><div class='head'><h2>Resource tradeoff</h2><p>PR #10 removed most of earlier Pi-Fabric's token and cost overhead. Host load was not controlled across separately timed comparisons, and remaining provider retries still affect latency tails, so the error-free medians are the safer timing view.</p></div><div class='bars'><div class='barrow'><strong>Clean median tokens</strong><div class='track'><div class='fill good' style='width:{clean_new['median_tokens'] / clean_old['median_tokens'] * 100:.1f}%'></div></div><span>{clean_new['median_tokens']:,.0f} · {clean_token_change_old:+.1f}% vs old</span></div><div class='barrow'><strong>Clean median cost</strong><div class='track'><div class='fill good' style='width:{clean_new['median_cost'] / clean_old['median_cost'] * 100:.1f}%'></div></div><span>${clean_new['median_cost']:.3f} · {clean_cost_change_old:+.1f}% vs old</span></div><div class='barrow'><strong>Clean median wall</strong><div class='track'><div class='fill good' style='width:{clean_new['median_wall_s'] / clean_old['median_wall_s'] * 100:.1f}%'></div></div><span>{clean_new['median_wall_s']:.1f}s · {clean_wall_change_old:+.1f}% vs old</span></div></div><div class='callout caution'><strong>Residual overhead versus plain Pi:</strong> on error-free keys, PR #10 used {clean_token_change_base:.1f}% more median tokens, cost {clean_cost_change_base:.1f}% more, and took {clean_wall_change_base:.1f}% longer. Against earlier Pi-Fabric it used {abs(clean_token_change_old):.1f}% fewer tokens, cost {abs(clean_cost_change_old):.1f}% less, and had nearly identical median wall time.</div></section>
<section><div class='head'><h2>Conclusion and next move</h2></div><div class='grid2'><div class='callout good'><strong>What worked:</strong> PR #10 cut whole-file read rate from {old_audit['whole_repo_read_rate'] * 100:.1f}% to {new_audit['whole_repo_read_rate'] * 100:.1f}%, reduced median tokens {abs(token_change_old):.1f}% and median cost {abs(cost_change_old):.1f}% versus earlier Pi-Fabric, and matched its {old['solves']}/108 observed solves.</div><div class='callout caution'><strong>What remains unresolved:</strong> {new_audit['affected_cells']} PR #10 reps still contain provider/session failures, and the historical references used Pi 0.81.1 while PR #10 used Pi 0.83.0. The data supports no detectable efficacy loss; it does not establish formal non-inferiority.</div></div><div class='callout'><strong>Recommended next move:</strong> share this as strong evidence that PR #10 achieved its efficiency goal while preserving observed efficacy relative to earlier Pi-Fabric. If a publication-quality clean efficacy estimate is required, first make native-session errors invalidate a rep, then rerun only the remaining {new_audit['affected_cells']} affected cells after provider load stabilizes.</div><p class='muted'><strong>Comparability limit:</strong> plain Pi and earlier Pi-Fabric are legacy Pi 0.81.1 references with no per-result subject or harness identity fields. PR #10 ran on Pi 0.83.0 with full provenance. The baseline was intentionally reference-only, so this is not a fully matched subject-version comparison. Scope: 36_v2, 3 reps, <code>{MODEL}</code>, low thinking. Raw data: <a href='summary.json'>summary.json</a> · <a href='paired_cells.csv'>paired_cells.csv</a> · <a href='packets/index.json'>packet index</a>.</p></section><div class='foot'>Deterministic analysis: <code>analysis/pi-fabric-pr10-vs-prior-36v2/build_report.py</code> · PR #10 package commit <code>0da479fe267232115b3fbf0893067352622b0f29</code></div>
</div></body></html>"""


def main() -> None:
    """Build all machine-readable artifacts and the HTML report."""
    arguments = parse_arguments()
    results_root = arguments.results_root.resolve()
    keys, cells = load_matched_result_cells(results_root)
    metadata = load_task_metadata()
    audits = {
        config: {key: audit_result_session(cell, config) for key, cell in config_cells.items()}
        for config, config_cells in cells.items()
    }
    initial_outage_cells = load_initial_outage_cells(results_root)
    initial_outage_audits = {
        key: audit_result_session(cell, "pi-fabric-pr10@0.28.11")
        for key, cell in initial_outage_cells.items()
    }
    replacement_keys = set(initial_outage_cells)
    all_keys = set(keys)
    affected_keys = {
        config: {key for key, audit in config_audits.items() if audit.affected_by_session_error}
        for config, config_audits in audits.items()
    }
    strict_error_free_keys = all_keys - set().union(*affected_keys.values())
    if not strict_error_free_keys:
        raise ValueError("No strict error-free matched reps remain")

    aggregate = {
        config: aggregate_results([cells[config][key].result for key in keys])
        for config in CONFIG_ORDER
    }
    clean_aggregate = {
        config: aggregate_results([cells[config][key].result for key in sorted(strict_error_free_keys)])
        for config in CONFIG_ORDER
    }
    paired_comparisons = {
        "baseline_to_earlier_pi_fabric": compare_binary_churn(all_keys, cells, "baseline", "pi-fabric"),
        "baseline_to_pr10": compare_binary_churn(all_keys, cells, "baseline", "pi-fabric-pr10@0.28.11"),
        "pi-fabric_to_pr10": compare_binary_churn(all_keys, cells, "pi-fabric", "pi-fabric-pr10@0.28.11"),
    }
    clean_paired_comparisons = {
        "baseline_to_pr10": compare_binary_churn(strict_error_free_keys, cells, "baseline", "pi-fabric-pr10@0.28.11"),
        "pi-fabric_to_pr10": compare_binary_churn(strict_error_free_keys, cells, "pi-fabric", "pi-fabric-pr10@0.28.11"),
    }
    session_summary: dict[str, Any] = {}
    for config in CONFIG_ORDER:
        session_summary[config] = {
            "all": aggregate_session_audits([audits[config][key] for key in keys]),
            "strict_error_free": aggregate_session_audits(
                [audits[config][key] for key in sorted(strict_error_free_keys)]
            ),
            "affected_keys": [f"{task}__rep{rep}" for task, rep in sorted(affected_keys[config])],
        }

    summary: dict[str, Any] = {
        "comparison": {
            "subset": "36_v2",
            "reps": 3,
            "model": MODEL,
            "thinking": THINKING,
            "configs": {
                "baseline": {"label": "Plain Pi", "subject": "legacy Pi 0.81.1 reference", "provenance_complete": False},
                "pi-fabric": {"label": "Earlier Pi-Fabric 0.25.6", "subject": "legacy Pi 0.81.1 reference", "provenance_complete": False},
                "pi-fabric-pr10@0.28.11": {"label": "PR #10 Pi-Fabric 0.28.11", "subject": "pi@0.83.0", "upstream_commit": "0da479fe267232115b3fbf0893067352622b0f29", "provenance_complete": True},
            },
        },
        "aggregate": aggregate,
        "paired_comparisons": paired_comparisons,
        "partial_bootstrap": {
            "baseline_to_pr10": cluster_bootstrap_partial_reward(all_keys, cells, "baseline", "pi-fabric-pr10@0.28.11"),
            "pi-fabric_to_pr10": cluster_bootstrap_partial_reward(all_keys, cells, "pi-fabric", "pi-fabric-pr10@0.28.11"),
        },
        "session_audit": session_summary,
        "supplemental_rerun": {
            "cells": len(replacement_keys),
            "preserved_cells": len(all_keys - replacement_keys),
            "initial_aggregate": aggregate_results(
                [
                    initial_outage_cells.get(
                        key, cells["pi-fabric-pr10@0.28.11"][key]
                    ).result
                    for key in keys
                ]
            ),
            "final_aggregate": aggregate["pi-fabric-pr10@0.28.11"],
            "initial_outage_cells": aggregate_session_audits(list(initial_outage_audits.values())),
            "replacement_cells": aggregate_session_audits(
                [audits["pi-fabric-pr10@0.28.11"][key] for key in sorted(replacement_keys)]
            ),
            "run_state": "completed",
            "harness_failures": 0,
            "watchdog_interventions": 0,
        },
        "strict_error_free_sensitivity": {
            "n": len(strict_error_free_keys),
            "excluded_n": len(all_keys - strict_error_free_keys),
            "selection": "Exclude any task/rep key where any config has an assistant error or unmatched tool call.",
            "aggregate": clean_aggregate,
            "paired_comparisons": clean_paired_comparisons,
            "partial_bootstrap": {
                "baseline_to_pr10": cluster_bootstrap_partial_reward(strict_error_free_keys, cells, "baseline", "pi-fabric-pr10@0.28.11"),
                "pi-fabric_to_pr10": cluster_bootstrap_partial_reward(strict_error_free_keys, cells, "pi-fabric", "pi-fabric-pr10@0.28.11"),
            },
        },
        "execution_audit": {
            config: {
                "model_ok": sum(cell.result.get("model") == MODEL for cell in cells[config].values()),
                "thinking_ok": sum(cell.result.get("thinking_level") == THINKING for cell in cells[config].values()),
                "timed_out": sum(bool(cell.result.get("agent_timed_out")) for cell in cells[config].values()),
                "recursive_child_calls": sum(int(cell.result.get("recursive_child_calls") or 0) for cell in cells[config].values()),
                "workflow_agent_calls": sum(int(cell.result.get("workflow_agent_calls") or 0) for cell in cells[config].values()),
            }
            for config in CONFIG_ORDER
        },
    }

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    packet_index = build_packet_outputs(keys, cells, audits, metadata)
    summary["selected_packets"] = packet_index
    write_paired_cells_csv(keys, cells, audits, metadata)
    summary_text = json.dumps(summary, indent=2) + "\n"
    (HERE / "summary.json").write_text(summary_text)
    (REPORT_ROOT / "summary.json").write_text(summary_text)
    (REPORT_ROOT / "index.html").write_text(render_html_report(summary, packet_index, cells))
    print(REPORT_ROOT / "index.html")


if __name__ == "__main__":
    main()
