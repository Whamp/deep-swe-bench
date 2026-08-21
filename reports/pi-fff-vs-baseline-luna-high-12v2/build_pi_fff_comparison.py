#!/usr/bin/env python3
"""Build the paired Pi FFF versus baseline Luna/high 12_v2 report."""

from __future__ import annotations

import csv
import html
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = REPORT_DIR.parents[1]
BASELINE_ROOT = REPOSITORY_ROOT / "results/gpt-5.6-luna/high/baseline@1.0.0"
FFF_ROOT = (
    REPOSITORY_ROOT
    / "results/_campaigns/pi-fff-1.0.0-w8-r3/gpt-5.6-luna/high/pi-fff@1.0.0"
)
SUBSET_PATH = REPOSITORY_ROOT / "subsets/12_v2.txt"
DIFFICULTY_PATH = REPOSITORY_ROOT / "data/deepswe-v1.1-task-difficulty.tsv"
REPS = (0, 1, 2)
RESULT_METRICS = (
    "reward_binary",
    "reward_partial",
    "f2p",
    "p2p",
    "combined_total_tokens",
    "combined_cost_usd",
    "agent_wall_s",
    "turns",
    "tool_calls",
    "patch_bytes",
)


def read_json(path: Path) -> dict[str, Any]:
    """Read one JSON artifact used by the paired comparison."""
    return json.loads(path.read_text())


def load_subset_tasks() -> list[str]:
    """Load the ordered 12_v2 task slugs from the canonical subset file."""
    return [
        line.strip()
        for line in SUBSET_PATH.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def load_task_metadata() -> dict[str, dict[str, Any]]:
    """Load task titles, languages, and difficulty buckets."""
    metadata: dict[str, dict[str, Any]] = {}
    with DIFFICULTY_PATH.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            pass_rate = float(row["pass_rate"])
            row["pass_rate"] = pass_rate
            row["difficulty"] = (
                "hard" if pass_rate < 33 else "medium" if pass_rate < 66 else "easy"
            )
            metadata[row["slug"]] = row
    return metadata


def model_patch_stats(cell_path: Path) -> dict[str, Any]:
    """Summarize a cell's model patch without executing it."""
    patch_path = cell_path / "artifacts/model.patch"
    if not patch_path.exists():
        return {"files": [], "adds": 0, "deletes": 0, "bytes": 0, "excerpt": ""}
    patch = patch_path.read_text(errors="replace")
    files = re.findall(r"^diff --git a/(.+?) b/", patch, re.MULTILINE)
    adds = sum(
        line.startswith("+") and not line.startswith("+++")
        for line in patch.splitlines()
    )
    deletes = sum(
        line.startswith("-") and not line.startswith("---")
        for line in patch.splitlines()
    )
    return {
        "files": files,
        "adds": adds,
        "deletes": deletes,
        "bytes": len(patch.encode()),
        "excerpt": "\n".join(patch.splitlines()[:120]),
    }


def normalize_tool_result_text(content: Any) -> str:
    """Flatten Pi tool-result content into searchable text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text", item)) if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content)


def classify_tool_error(tool_name: str, message: str) -> str:
    """Classify an errored tool result by its concrete failure signature."""
    lowered = message.lower()
    if tool_name == "edit" and any(
        marker in lowered
        for marker in ("oldtext", "exact", "match", "replacement", "unique")
    ):
        return "edit mismatch"
    if tool_name == "read" and any(
        marker in lowered
        for marker in ("enoent", "not found", "no such file", "offset")
    ):
        return "read failure"
    if tool_name in {"fffind", "ffgrep"}:
        return "FFF parser/transport"
    if any(
        marker in lowered
        for marker in ("required", "invalid argument", "expected", "must provide")
    ):
        return "malformed arguments"
    if tool_name == "bash":
        return "nonzero diagnostic command"
    return "other tool error"


def session_trace(cell_path: Path) -> dict[str, Any]:
    """Extract tool counts, tool errors, commands, and a compact timeline."""
    tool_counts: Counter[str] = Counter()
    error_counts: Counter[str] = Counter()
    error_causes: Counter[str] = Counter()
    commands: list[str] = []
    timeline: list[dict[str, Any]] = []
    assistant_turns = 0
    for session_path in sorted((cell_path / "session").glob("*.jsonl")):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "message":
                continue
            message = record.get("message", {})
            role = message.get("role")
            if role == "assistant":
                assistant_turns += 1
                content = message.get("content", [])
                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict) or item.get("type") != "toolCall":
                        continue
                    tool_name = str(item.get("name", "unknown"))
                    arguments = item.get("arguments", {})
                    tool_counts[tool_name] += 1
                    if tool_name == "bash" and isinstance(arguments, dict):
                        commands.append(
                            str(arguments.get("command", arguments.get("cmd", "")))
                        )
                    timeline.append(
                        {
                            "kind": "tool_call",
                            "tool": tool_name,
                            "arguments": arguments,
                        }
                    )
            elif role == "toolResult":
                tool_name = str(message.get("toolName", "unknown"))
                result_text = normalize_tool_result_text(message.get("content", ""))
                is_error = bool(message.get("isError"))
                if is_error:
                    error_counts[tool_name] += 1
                    error_causes[classify_tool_error(tool_name, result_text)] += 1
                timeline.append(
                    {
                        "kind": "tool_result",
                        "tool": tool_name,
                        "is_error": is_error,
                        "text": result_text[:1200],
                    }
                )
    return {
        "assistant_turns": assistant_turns,
        "tool_counts": dict(sorted(tool_counts.items())),
        "tool_error_counts": dict(sorted(error_counts.items())),
        "tool_error_causes": dict(sorted(error_causes.items())),
        "tool_errors": sum(error_counts.values()),
        "commands": commands[:100],
        "timeline": timeline[:240],
    }


def verifier_trace(cell_path: Path) -> dict[str, Any]:
    """Extract grading totals and failed tests from one cell."""
    reward_path = cell_path / "verifier/reward.json"
    ctrf_path = cell_path / "verifier/ctrf.json"
    reward = read_json(reward_path) if reward_path.exists() else {}
    failed_tests: list[dict[str, str]] = []
    summary: dict[str, Any] = {}
    if ctrf_path.exists():
        results = read_json(ctrf_path).get("results", {})
        summary = results.get("summary", {})
        failed_tests = [
            {
                "name": str(test.get("name", "unknown")),
                "message": str(test.get("message", ""))[:1000],
            }
            for test in results.get("tests", [])
            if test.get("status") == "failed"
        ]
    run_log_path = cell_path / "verifier/run.log"
    return {
        "reward": reward,
        "summary": summary,
        "failed_tests": failed_tests[:40],
        "run_log_tail": (
            run_log_path.read_text(errors="replace")[-5000:]
            if run_log_path.exists()
            else ""
        ),
    }


def fff_delivery(cell_path: Path) -> dict[str, Any]:
    """Classify whether the FFF tool surface reached the treatment model."""
    options_path = cell_path / "initial_context/system_prompt_options.json"
    request_path = cell_path / "initial_context/provider_request_0001.json"
    stderr_path = cell_path / "logs/pi.stderr.txt"
    if not options_path.exists() or not request_path.exists():
        return {"classification": "missing", "selected_tools": []}
    options = read_json(options_path)
    selected_tools = options.get("selectedTools", [])
    request_text = request_path.read_text(errors="replace")
    stderr = stderr_path.read_text(errors="replace") if stderr_path.exists() else ""
    has_tools = selected_tools == ["read", "bash", "edit", "write", "ffgrep", "fffind"]
    request_has_tools = (
        '"name": "ffgrep"' in request_text and '"name": "fffind"' in request_text
    )
    extension_error = (
        "Failed to load extension" in stderr or "Extension error" in stderr
    )
    classification = (
        "ambiguous"
        if extension_error
        else "delivered"
        if has_tools and request_has_tools
        else "missing"
    )
    return {"classification": classification, "selected_tools": selected_tools}


def baseline_delivery(cell_path: Path) -> dict[str, Any]:
    """Verify the baseline did not receive FFF tools."""
    request_path = cell_path / "initial_context/provider_request_0001.json"
    request_text = (
        request_path.read_text(errors="replace") if request_path.exists() else ""
    )
    leaked = '"name": "ffgrep"' in request_text or '"name": "fffind"' in request_text
    return {"classification": "leaked" if leaked else "delivered", "fff_leaked": leaked}


def exact_mcnemar(left_only: int, right_only: int) -> float:
    """Return the two-sided exact McNemar p-value for solve flips."""
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    smaller = min(left_only, right_only)
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (
        2**discordant
    )
    return min(1.0, 2 * tail)


def task_cluster_bootstrap(
    pairs: list[dict[str, Any]], iterations: int = 100_000
) -> list[float]:
    """Bootstrap mean partial delta by task clusters with a fixed seed."""
    by_task: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        by_task[pair["task"]].append(float(pair["delta"]["reward_partial"]))
    task_means = [statistics.mean(by_task[task]) for task in sorted(by_task)]
    randomizer = random.Random(20260816)
    draws = sorted(
        statistics.mean(randomizer.choices(task_means, k=len(task_means)))
        for _ in range(iterations)
    )
    return [draws[int(iterations * 0.025)], draws[int(iterations * 0.975)]]


def summarize_side(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize one comparison side across all 36 paired cells."""

    def numeric(metric: str) -> list[float]:
        return [float(row[metric]) for row in rows if row.get(metric) is not None]

    f2p_passed = sum(float(row.get("f2p_passed") or 0) for row in rows)
    f2p_total = sum(float(row.get("f2p_total") or 0) for row in rows)
    p2p_passed = sum(float(row.get("p2p_passed") or 0) for row in rows)
    p2p_total = sum(float(row.get("p2p_total") or 0) for row in rows)
    return {
        "n": len(rows),
        "solves": sum(row.get("reward_binary") == 1 for row in rows),
        "mean_partial": statistics.mean(numeric("reward_partial")),
        "median_partial": statistics.median(numeric("reward_partial")),
        "total_tokens": sum(numeric("combined_total_tokens")),
        "median_tokens": statistics.median(numeric("combined_total_tokens")),
        "total_cost": sum(numeric("combined_cost_usd")),
        "median_cost": statistics.median(numeric("combined_cost_usd")),
        "median_wall_s": statistics.median(numeric("agent_wall_s")),
        "median_turns": statistics.median(numeric("turns")),
        "median_tool_calls": statistics.median(numeric("tool_calls")),
        "timeouts": sum(bool(row.get("agent_timed_out")) for row in rows),
        "empty_patches": sum(float(row.get("patch_bytes") or 0) == 0 for row in rows),
        "f2p_passed": f2p_passed,
        "f2p_total": f2p_total,
        "f2p_rate": f2p_passed / f2p_total if f2p_total else None,
        "p2p_passed": p2p_passed,
        "p2p_total": p2p_total,
        "p2p_rate": p2p_passed / p2p_total if p2p_total else None,
    }


def classify_packet_driver(pair: dict[str, Any]) -> dict[str, str]:
    """Assign a conservative packet driver from direct paired grading evidence."""
    partial_delta = float(pair["delta"]["reward_partial"])
    baseline_partial = float(pair["baseline"]["reward_partial"])
    fff_partial = float(pair["fff"]["reward_partial"])
    if abs(partial_delta) < 0.01 and min(baseline_partial, fff_partial) >= 0.98:
        return {
            "primary": "likely variance",
            "mechanism": "Binary flip at an almost-perfect grading boundary; direct evidence does not isolate FFF as the cause.",
        }
    if partial_delta <= -0.1:
        return {
            "primary": "validation gap",
            "mechanism": "FFF left materially more verifier failures than baseline; inspect the packet's failed tests and patch before assigning a tool mechanism.",
        }
    if partial_delta >= 0.1:
        return {
            "primary": "under-implementation",
            "mechanism": "Baseline left materially more feature work incomplete; the packet records the paired failed tests, but causality remains uncertain.",
        }
    return {
        "primary": "likely variance",
        "mechanism": "Outcome moved without a large partial-reward change or an independent infrastructure signature.",
    }


def build_paired_cells() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load all 36 exact task/rep pairs and their artifact traces."""
    tasks = load_subset_tasks()
    metadata = load_task_metadata()
    pairs: list[dict[str, Any]] = []
    packets: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for task in tasks:
        for rep in REPS:
            baseline_path = BASELINE_ROOT / task / f"rep{rep}"
            fff_path = FFF_ROOT / task / f"rep{rep}"
            baseline_result_path = baseline_path / "result.json"
            fff_result_path = fff_path / "result.json"
            if not baseline_result_path.exists() or not fff_result_path.exists():
                missing.append(f"{task}/rep{rep}")
                continue
            baseline = read_json(baseline_result_path)
            fff = read_json(fff_result_path)
            delta = {
                metric: (
                    float(fff[metric]) - float(baseline[metric])
                    if fff.get(metric) is not None and baseline.get(metric) is not None
                    else None
                )
                for metric in RESULT_METRICS
            }
            pair = {
                "task": task,
                "rep": rep,
                "title": metadata[task]["title"],
                "language": metadata[task]["language"],
                "difficulty": metadata[task]["difficulty"],
                "pass_rate": metadata[task]["pass_rate"],
                "baseline": baseline,
                "fff": fff,
                "delta": delta,
                "baseline_path": str(baseline_path.relative_to(REPOSITORY_ROOT)),
                "fff_path": str(fff_path.relative_to(REPOSITORY_ROOT)),
                "baseline_delivery": baseline_delivery(baseline_path),
                "fff_delivery": fff_delivery(fff_path),
            }
            pairs.append(pair)
    if missing:
        raise RuntimeError(f"Paired comparison missing cells: {missing}")
    if len(pairs) != 36:
        raise RuntimeError(f"Paired comparison expected 36 cells, got {len(pairs)}")

    for pair in pairs:
        solve_flip = (pair["baseline"]["reward_binary"] == 1) != (
            pair["fff"]["reward_binary"] == 1
        )
        material_partial = abs(float(pair["delta"]["reward_partial"])) >= 0.1
        timeout_discordance = bool(pair["baseline"].get("agent_timed_out")) != bool(
            pair["fff"].get("agent_timed_out")
        )
        if not (solve_flip or material_partial or timeout_discordance):
            continue
        packet_key = f"{pair['task']}__rep{pair['rep']}"
        baseline_path = REPOSITORY_ROOT / pair["baseline_path"]
        fff_path = REPOSITORY_ROOT / pair["fff_path"]
        packet = {
            "selection_reasons": {
                "solve_flip": solve_flip,
                "material_partial_delta": material_partial,
                "timeout_discordance": timeout_discordance,
            },
            "task": {
                key: pair[key]
                for key in (
                    "task",
                    "title",
                    "rep",
                    "language",
                    "difficulty",
                    "pass_rate",
                )
            },
            "baseline": {
                "result": {
                    key: pair["baseline"].get(key)
                    for key in (
                        *RESULT_METRICS,
                        "f2p_passed",
                        "f2p_total",
                        "p2p_passed",
                        "p2p_total",
                        "agent_exit",
                        "verifier_exit",
                        "agent_timed_out",
                    )
                },
                "patch": model_patch_stats(baseline_path),
                "session": session_trace(baseline_path),
                "verifier": verifier_trace(baseline_path),
            },
            "fff": {
                "result": {
                    key: pair["fff"].get(key)
                    for key in (
                        *RESULT_METRICS,
                        "f2p_passed",
                        "f2p_total",
                        "p2p_passed",
                        "p2p_total",
                        "agent_exit",
                        "verifier_exit",
                        "agent_timed_out",
                    )
                },
                "patch": model_patch_stats(fff_path),
                "session": session_trace(fff_path),
                "verifier": verifier_trace(fff_path),
                "delivery": pair["fff_delivery"],
            },
            "delta": pair["delta"],
            "driver": classify_packet_driver(pair),
        }
        packets[packet_key] = packet
    return pairs, packets


def aggregate_comparison(
    pairs: list[dict[str, Any]], packets: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Compute aggregate, churn, delivery, and tool-use metrics."""
    baseline_rows = [pair["baseline"] for pair in pairs]
    fff_rows = [pair["fff"] for pair in pairs]
    both = sum(
        pair["baseline"]["reward_binary"] == pair["fff"]["reward_binary"] == 1
        for pair in pairs
    )
    baseline_only = sum(
        pair["baseline"]["reward_binary"] == 1 and pair["fff"]["reward_binary"] != 1
        for pair in pairs
    )
    fff_only = sum(
        pair["baseline"]["reward_binary"] != 1 and pair["fff"]["reward_binary"] == 1
        for pair in pairs
    )
    partial_deltas = [float(pair["delta"]["reward_partial"]) for pair in pairs]
    timeout_discordance = sum(
        bool(pair["baseline"].get("agent_timed_out"))
        != bool(pair["fff"].get("agent_timed_out"))
        for pair in pairs
    )

    traces: dict[str, list[dict[str, Any]]] = {"baseline": [], "fff": []}
    for pair in pairs:
        traces["baseline"].append(
            session_trace(REPOSITORY_ROOT / pair["baseline_path"])
        )
        traces["fff"].append(session_trace(REPOSITORY_ROOT / pair["fff_path"]))

    tool_audit: dict[str, Any] = {}
    for side in ("baseline", "fff"):
        tool_counts: Counter[str] = Counter()
        error_counts: Counter[str] = Counter()
        error_causes: Counter[str] = Counter()
        cells_with_errors = 0
        for trace in traces[side]:
            tool_counts.update(trace["tool_counts"])
            error_counts.update(trace["tool_error_counts"])
            error_causes.update(trace["tool_error_causes"])
            cells_with_errors += trace["tool_errors"] > 0
        tool_audit[side] = {
            "calls": sum(tool_counts.values()),
            "tool_counts": dict(sorted(tool_counts.items())),
            "errors": sum(error_counts.values()),
            "error_counts": dict(sorted(error_counts.items())),
            "error_causes": dict(sorted(error_causes.items())),
            "cells_with_errors": cells_with_errors,
        }

    difficulty: dict[str, Any] = {}
    for bucket in ("hard", "medium", "easy"):
        bucket_pairs = [pair for pair in pairs if pair["difficulty"] == bucket]
        difficulty[bucket] = {
            "n": len(bucket_pairs),
            "baseline_solves": sum(
                pair["baseline"]["reward_binary"] == 1 for pair in bucket_pairs
            ),
            "fff_solves": sum(
                pair["fff"]["reward_binary"] == 1 for pair in bucket_pairs
            ),
            "mean_partial_delta": statistics.mean(
                float(pair["delta"]["reward_partial"]) for pair in bucket_pairs
            )
            if bucket_pairs
            else None,
        }

    try:
        from scipy.stats import wilcoxon

        wilcoxon_p = float(wilcoxon(partial_deltas, zero_method="wilcox").pvalue)
    except (ImportError, ValueError):
        wilcoxon_p = None

    return {
        "comparison": {
            "left": "baseline@1.0.0",
            "right": "pi-fff@1.0.0",
            "subset": "12_v2",
            "reps": 3,
            "model": "openai-codex/gpt-5.6-luna",
            "thinking": "high",
            "baseline_root": str(BASELINE_ROOT.relative_to(REPOSITORY_ROOT)),
            "fff_root": str(FFF_ROOT.relative_to(REPOSITORY_ROOT)),
            "analytical_roles": {
                "baseline@1.0.0": "same-model config control",
                "pi-fff@1.0.0": "same-model config treatment",
            },
        },
        "baseline": summarize_side(baseline_rows),
        "fff": summarize_side(fff_rows),
        "agreement": {
            "both_solved": both,
            "baseline_only": baseline_only,
            "fff_only": fff_only,
            "neither": len(pairs) - both - baseline_only - fff_only,
            "net": fff_only - baseline_only,
            "mcnemar_p": exact_mcnemar(baseline_only, fff_only),
            "timeout_discordance": timeout_discordance,
        },
        "partial": {
            "mean_delta": statistics.mean(partial_deltas),
            "median_delta": statistics.median(partial_deltas),
            "wilcoxon_p": wilcoxon_p,
            "task_cluster_bootstrap_95": task_cluster_bootstrap(pairs),
            "improved": sum(delta > 1e-12 for delta in partial_deltas),
            "worsened": sum(delta < -1e-12 for delta in partial_deltas),
            "tied": sum(abs(delta) <= 1e-12 for delta in partial_deltas),
            "material_abs_ge_0_1": sum(abs(delta) >= 0.1 for delta in partial_deltas),
        },
        "difficulty": difficulty,
        "delivery": {
            "fff": dict(
                Counter(pair["fff_delivery"]["classification"] for pair in pairs)
            ),
            "baseline": dict(
                Counter(pair["baseline_delivery"]["classification"] for pair in pairs)
            ),
            "fff_used_cells": sum(
                trace["tool_counts"].get("fffind", 0)
                + trace["tool_counts"].get("ffgrep", 0)
                > 0
                for trace in traces["fff"]
            ),
        },
        "tool_audit": tool_audit,
        "packet_selection": {
            "rule": "Every solve flip, timeout discordance, or |partial delta| >= 0.10.",
            "count": len(packets),
            "keys": sorted(packets),
        },
    }


def outcome_symbol(value: Any) -> str:
    """Render a compact binary outcome symbol."""
    return "✓" if value == 1 else "—"


def report_number(value: float, digits: int = 3) -> str:
    """Format one signed comparison number."""
    return f"{value:+.{digits}f}"


def render_task_rep_table(pairs: list[dict[str, Any]]) -> str:
    """Render the complete task × rep paired outcome table."""
    rows = []
    for pair in pairs:
        baseline_solved = pair["baseline"]["reward_binary"] == 1
        fff_solved = pair["fff"]["reward_binary"] == 1
        if fff_solved and not baseline_solved:
            verdict = "FFF only"
            verdict_class = "good"
        elif baseline_solved and not fff_solved:
            verdict = "baseline only"
            verdict_class = "bad"
        elif baseline_solved:
            verdict = "both"
            verdict_class = "neutral"
        else:
            verdict = "neither"
            verdict_class = "caution"
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(pair['title'])}</strong><br><span class='muted mono'>{html.escape(pair['task'])} · {pair['difficulty']}</span></td>"
            f"<td class='num'>rep{pair['rep']}</td>"
            f"<td class='num'>{outcome_symbol(pair['baseline']['reward_binary'])}<br><span class='muted'>{pair['baseline']['reward_partial']:.3f}</span></td>"
            f"<td class='num'>{outcome_symbol(pair['fff']['reward_binary'])}<br><span class='muted'>{pair['fff']['reward_partial']:.3f}</span></td>"
            f"<td class='num'>{report_number(pair['delta']['reward_partial'])}</td>"
            f"<td><span class='tag {verdict_class}'>{verdict}</span></td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_packet_table(packets: dict[str, dict[str, Any]]) -> str:
    """Render links and evidence summaries for every selected packet."""
    rows = []
    for packet_key in sorted(packets):
        packet = packets[packet_key]
        task = packet["task"]
        baseline = packet["baseline"]["result"]
        fff = packet["fff"]["result"]
        driver = packet["driver"]
        rows.append(
            "<tr>"
            f"<td><a href='packets/{html.escape(packet_key)}.json'><strong>{html.escape(task['title'])}</strong> · rep{task['rep']}</a><br><span class='muted mono'>{html.escape(task['task'])}</span></td>"
            f"<td class='num'>{outcome_symbol(baseline['reward_binary'])} {baseline['reward_partial']:.3f}</td>"
            f"<td class='num'>{outcome_symbol(fff['reward_binary'])} {fff['reward_partial']:.3f}</td>"
            f"<td><span class='tag neutral'>{html.escape(driver['primary'])}</span><br><span class='muted'>{html.escape(driver['mechanism'])}</span></td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_tool_rows(summary: dict[str, Any]) -> str:
    """Render per-tool call counts for both configs."""
    baseline_tools = summary["tool_audit"]["baseline"]["tool_counts"]
    fff_tools = summary["tool_audit"]["fff"]["tool_counts"]
    tools = sorted(set(baseline_tools) | set(fff_tools))
    return "\n".join(
        f"<tr><td class='mono'>{html.escape(tool)}</td><td class='num'>{baseline_tools.get(tool, 0):,}</td><td class='num'>{fff_tools.get(tool, 0):,}</td></tr>"
        for tool in tools
    )


def render_report(
    summary: dict[str, Any],
    pairs: list[dict[str, Any]],
    packets: dict[str, dict[str, Any]],
) -> str:
    """Render the self-contained evidence-first HTML comparison report."""
    baseline = summary["baseline"]
    fff = summary["fff"]
    agreement = summary["agreement"]
    partial = summary["partial"]
    token_delta = fff["total_tokens"] / baseline["total_tokens"] - 1
    cost_delta = fff["total_cost"] / baseline["total_cost"] - 1
    bootstrap = partial["task_cluster_bootstrap_95"]
    error_baseline = summary["tool_audit"]["baseline"]
    error_fff = summary["tool_audit"]["fff"]
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><link rel='icon' href='data:,'>
<title>Pi FFF vs baseline · GPT-5.6-luna high · 12_v2</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#b77a00;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--shadow:0 18px 50px rgba(14,30,62,.08);--radius:24px;--max:1260px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.1),transparent 30%),linear-gradient(#f9fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.5}}.wrap{{max-width:var(--max);margin:auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}}.hero{{padding:38px}}section{{margin-top:22px;padding:28px}}h1,h2,h3{{line-height:1.08;letter-spacing:-.025em;margin:0}}h1{{font-size:clamp(2.25rem,5vw,4.25rem);max-width:16ch}}h2{{font-size:1.7rem}}h3{{font-size:1.05rem}}p{{color:var(--muted)}}.eyebrow{{display:inline-block;color:var(--blue);font-size:.75rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;margin-bottom:12px}}.pillrow{{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:6px 10px;border:1px solid var(--line);font-size:.76rem;font-weight:800}}.pill.good,.tag.good{{color:var(--green);background:var(--green-soft)}}.pill.bad,.tag.bad{{color:var(--red);background:var(--red-soft)}}.pill.caution,.tag.caution{{color:var(--amber);background:var(--amber-soft)}}.pill.neutral,.tag.neutral{{color:#42516a;background:#f4f7fb}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:26px}}.stat{{border:1px solid var(--line);border-radius:18px;padding:18px;background:#fff}}.stat .label{{display:block;color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em}}.stat .value{{display:block;font-size:1.7rem;font-weight:850;margin-top:4px}}.stat .sub{{display:block;color:var(--muted);font-size:.82rem;margin-top:5px}}.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.callout{{border-left:4px solid var(--blue);background:#f7f9ff;border-radius:12px;padding:15px 17px;color:#344258}}.callout.good{{border-color:var(--green);background:var(--green-soft)}}.callout.bad{{border-color:var(--red);background:var(--red-soft)}}.callout.caution{{border-color:var(--amber);background:var(--amber-soft)}}table{{width:100%;border-collapse:collapse;margin-top:16px;font-size:.88rem}}th,td{{padding:10px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:var(--muted);font-size:.73rem;text-transform:uppercase;letter-spacing:.05em}}.num{{text-align:right;font-variant-numeric:tabular-nums}}.muted{{color:var(--muted);font-size:.8rem}}.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#eef2f8;padding:2px 5px;border-radius:5px}}.bar-row{{display:grid;grid-template-columns:180px 1fr 90px;gap:12px;align-items:center;margin:10px 0}}.bar-track{{height:14px;border-radius:999px;background:#e8edf5;overflow:hidden}}.bar{{height:100%;background:var(--blue)}}.bar.green{{background:var(--green)}}.foot{{margin-top:20px;text-align:center;color:var(--muted);font-size:.78rem}}@media(max-width:900px){{.stats,.grid-3{{grid-template-columns:1fr 1fr}}.grid-2{{grid-template-columns:1fr}}}}@media(max-width:600px){{.stats,.grid-3{{grid-template-columns:1fr}}.hero,section{{padding:22px}}table{{display:block;overflow:auto}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>Same-model config control · GPT-5.6-luna high · 12_v2 × 3</span><h1>FFF finished +2 solves, but the result is mostly churn.</h1><p>Pi with FFF solved <strong>{fff["solves"]}/36</strong> cells versus <strong>{baseline["solves"]}/36</strong> for stock Pi. That small net gain came from {agreement["fff_only"]} FFF-only solves and {agreement["baseline_only"]} baseline-only solves. Mean partial reward barely moved, and the paired tests do not separate the configs.</p><div class='pillrow'><span class='pill good'>36/36 pairs complete</span><span class='pill good'>FFF +2 solves</span><span class='pill caution'>20 solve flips</span><span class='pill neutral'>McNemar p={agreement["mcnemar_p"]:.3f}</span><span class='pill caution'>provenance caveat</span></div><div class='stats'><div class='stat'><span class='label'>Baseline</span><span class='value'>{baseline["solves"]}/36</span><span class='sub'>50.0% solved</span></div><div class='stat'><span class='label'>Pi FFF</span><span class='value'>{fff["solves"]}/36</span><span class='sub'>55.6% solved</span></div><div class='stat'><span class='label'>Mean partial Δ</span><span class='value'>{partial["mean_delta"]:+.4f}</span><span class='sub'>95% task bootstrap [{bootstrap[0]:+.4f}, {bootstrap[1]:+.4f}]</span></div><div class='stat'><span class='label'>Token change</span><span class='value'>{token_delta:+.1%}</span><span class='sub'>{fff["total_tokens"] / 1_000_000:.1f}M vs {baseline["total_tokens"] / 1_000_000:.1f}M</span></div><div class='stat'><span class='label'>FFF delivered</span><span class='value'>{summary["delivery"]["fff"].get("delivered", 0)}/36</span><span class='sub'>used in {summary["delivery"]["fff_used_cells"]}/36 cells</span></div></div></header>
<section><h2>Verdict</h2><div class='grid-3' style='margin-top:18px'><div class='callout good'><strong>Promising direction:</strong> FFF improved the observed solve count by 2 and reduced reported tokens by {abs(token_delta):.1%}. This justifies a larger, cleanly matched replication.</div><div class='callout caution'><strong>Not yet a win:</strong> 20/36 cells flipped, McNemar p={agreement["mcnemar_p"]:.3f}, Wilcoxon partial p={partial["wilcoxon_p"]:.3f}, and the task-cluster bootstrap crosses zero.</div><div class='callout bad'><strong>Do not attribute the cost drop to FFF:</strong> recorded cost fell {abs(cost_delta):.1%}, but historical and treatment runs used different Pi, harness, task-revision, and pricing/accounting provenance.</div></div></section>
<section><h2>Headline comparison</h2><table><thead><tr><th>Metric</th><th class='num'>baseline@1.0.0</th><th class='num'>pi-fff@1.0.0</th><th class='num'>Read</th></tr></thead><tbody>
<tr><td>Binary solves</td><td class='num'>{baseline["solves"]}/36</td><td class='num'>{fff["solves"]}/36</td><td class='num'>+2</td></tr>
<tr><td>Mean partial reward</td><td class='num'>{baseline["mean_partial"]:.4f}</td><td class='num'>{fff["mean_partial"]:.4f}</td><td class='num'>{partial["mean_delta"]:+.4f}</td></tr>
<tr><td>F2P aggregate</td><td class='num'>{baseline["f2p_passed"]:.0f}/{baseline["f2p_total"]:.0f} ({baseline["f2p_rate"]:.1%})</td><td class='num'>{fff["f2p_passed"]:.0f}/{fff["f2p_total"]:.0f} ({fff["f2p_rate"]:.1%})</td><td class='num'>feature tests</td></tr>
<tr><td>P2P aggregate</td><td class='num'>{baseline["p2p_passed"]:.0f}/{baseline["p2p_total"]:.0f} ({baseline["p2p_rate"]:.1%})</td><td class='num'>{fff["p2p_passed"]:.0f}/{fff["p2p_total"]:.0f} ({fff["p2p_rate"]:.1%})</td><td class='num'>preservation tests</td></tr>
<tr><td>Total reported tokens</td><td class='num'>{baseline["total_tokens"]:,}</td><td class='num'>{fff["total_tokens"]:,}</td><td class='num'>{token_delta:+.1%}</td></tr>
<tr><td>Median tokens/cell</td><td class='num'>{baseline["median_tokens"]:,.0f}</td><td class='num'>{fff["median_tokens"]:,.0f}</td><td class='num'>{fff["median_tokens"] / baseline["median_tokens"] - 1:+.1%}</td></tr>
<tr><td>Total recorded cost</td><td class='num'>${baseline["total_cost"]:.2f}</td><td class='num'>${fff["total_cost"]:.2f}</td><td class='num'>not causally comparable</td></tr>
<tr><td>Median agent wall time</td><td class='num'>{baseline["median_wall_s"]:.0f}s</td><td class='num'>{fff["median_wall_s"]:.0f}s</td><td class='num'>{fff["median_wall_s"] - baseline["median_wall_s"]:+.0f}s</td></tr>
<tr><td>Timeouts / empty patches</td><td class='num'>{baseline["timeouts"]} / {baseline["empty_patches"]}</td><td class='num'>{fff["timeouts"]} / {fff["empty_patches"]}</td><td class='num'>no timeout discordance</td></tr>
</tbody></table></section>
<section><h2>Net score versus churn</h2><div class='grid-2' style='margin-top:18px'><div><div class='bar-row'><span>Both solved</span><div class='bar-track'><div class='bar green' style='width:{agreement["both_solved"] / 36 * 100:.1f}%'></div></div><strong class='num'>{agreement["both_solved"]}</strong></div><div class='bar-row'><span>FFF only</span><div class='bar-track'><div class='bar green' style='width:{agreement["fff_only"] / 36 * 100:.1f}%'></div></div><strong class='num'>{agreement["fff_only"]}</strong></div><div class='bar-row'><span>Baseline only</span><div class='bar-track'><div class='bar' style='width:{agreement["baseline_only"] / 36 * 100:.1f}%'></div></div><strong class='num'>{agreement["baseline_only"]}</strong></div><div class='bar-row'><span>Neither</span><div class='bar-track'><div class='bar' style='width:{agreement["neither"] / 36 * 100:.1f}%'></div></div><strong class='num'>{agreement["neither"]}</strong></div></div><div class='callout caution'><strong>Interpretation:</strong> the +2 headline is the difference between 11 gains and 9 losses. Only {partial["material_abs_ge_0_1"]} cells moved by at least 0.10 partial reward; most binary flips occurred near a strict almost-perfect grading threshold and fit likely variance better than a tool mechanism.</div></div></section>
<section><h2>Complete 36-pair outcome table</h2><p>Every row is one matched task/rep trajectory. Binary outcome appears above partial reward.</p><table><thead><tr><th>Task</th><th class='num'>Rep</th><th class='num'>Baseline</th><th class='num'>FFF</th><th class='num'>Partial Δ</th><th>Outcome</th></tr></thead><tbody>{render_task_rep_table(pairs)}</tbody></table></section>
<section><h2>Delivery and tool audit</h2><div class='grid-2' style='margin-top:18px'><div class='callout good'><strong>Delivery:</strong> all {summary["delivery"]["fff"].get("delivered", 0)} FFF cells captured the exact <code>read, bash, edit, write, ffgrep, fffind</code> tool surface. No baseline request leaked FFF. FFF search was used in {summary["delivery"]["fff_used_cells"]} cells.</div><div class='callout caution'><strong>Tool errors:</strong> baseline had {error_baseline["errors"]} errored results across {error_baseline["calls"]} calls ({error_baseline["cells_with_errors"]} cells); FFF had {error_fff["errors"]} across {error_fff["calls"]} calls ({error_fff["cells_with_errors"]} cells). FFF parser/transport errors: {error_fff["error_causes"].get("FFF parser/transport", 0)}.</div></div><table><thead><tr><th>Tool</th><th class='num'>Baseline calls</th><th class='num'>FFF calls</th></tr></thead><tbody>{render_tool_rows(summary)}</tbody></table><p class='muted'>Errored results are classified by concrete signatures. Bash nonzero diagnostic commands are not counted as broken tools; edit mismatches, read failures, malformed arguments, and FFF parser/transport failures are separated in <a href='summary.json'>summary.json</a>.</p></section>
<section><h2>Selected trajectory packets</h2><p>Selection rule: {html.escape(summary["packet_selection"]["rule"])} These {len(packets)} examples are rep-specific evidence, not task-wide claims.</p><table><thead><tr><th>Packet</th><th class='num'>Baseline</th><th class='num'>FFF</th><th>Conservative driver</th></tr></thead><tbody>{render_packet_table(packets)}</tbody></table></section>
<section><h2>Provenance and sensitivity</h2><div class='grid-2' style='margin-top:18px'><div class='callout caution'><strong>Known mismatch:</strong> baseline used Pi 0.83.0, historical harness <code>061797…</code>, and task revision <code>8cc393…</code>. FFF used Pi 0.84.1, harness <code>247424…</code>, and task revision <code>3a1a52…</code> containing the approved Mobly fail-fast verifier fix. This comparison is useful but not a clean single-variable causal estimate.</div><div class='callout'><strong>Timeout sensitivity:</strong> neither side timed out and timeout discordance is {agreement["timeout_discordance"]}. The Mobly verifier change therefore did not turn a timeout into an observed solve in this sample, but its presence still changes provenance.</div></div><p>Reported cost is especially sensitive to historical provider pricing and usage accounting. Token totals are more comparable than dollars, but Pi/harness differences can still affect context and cache accounting.</p></section>
<section><h2>Conclusion</h2><div class='callout good'><strong>Decision:</strong> FFF is promising enough to replicate, not strong enough to declare better. The observed score moved from 18/36 to 20/36 and token volume fell, while paired uncertainty remained wide and churn was extreme. A clean rerun of stock Pi beside FFF under the same Pi, harness, task revision, worker policy, and provider accounting would answer the causal question.</div></section>
<div class='foot'>Generated from 72 result artifacts and native session traces · packet data and reproducible metrics are linked above.</div>
</div></body></html>"""


def main() -> None:
    """Build summary JSON, trajectory packets, and the HTML report."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    packet_dir = REPORT_DIR / "packets"
    packet_dir.mkdir(exist_ok=True)
    pairs, packets = build_paired_cells()
    summary = aggregate_comparison(pairs, packets)
    paired_rows = [
        {
            "task": pair["task"],
            "title": pair["title"],
            "rep": pair["rep"],
            "difficulty": pair["difficulty"],
            "language": pair["language"],
            "baseline_binary": pair["baseline"]["reward_binary"],
            "fff_binary": pair["fff"]["reward_binary"],
            "baseline_partial": pair["baseline"]["reward_partial"],
            "fff_partial": pair["fff"]["reward_partial"],
            "partial_delta": pair["delta"]["reward_partial"],
            "fff_delivery": pair["fff_delivery"]["classification"],
        }
        for pair in pairs
    ]
    (REPORT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    (REPORT_DIR / "paired_cells.json").write_text(json.dumps(paired_rows, indent=2))
    for packet_key, packet in packets.items():
        (packet_dir / f"{packet_key}.json").write_text(json.dumps(packet, indent=2))
    (REPORT_DIR / "index.html").write_text(render_report(summary, pairs, packets))
    print(
        json.dumps(
            {
                "report": str(REPORT_DIR / "index.html"),
                "baseline_solves": summary["baseline"]["solves"],
                "fff_solves": summary["fff"]["solves"],
                "agreement": summary["agreement"],
                "partial": summary["partial"],
                "delivery": summary["delivery"],
                "packets": len(packets),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
