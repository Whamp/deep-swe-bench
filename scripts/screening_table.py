#!/usr/bin/env python3
"""Generate compact screening tables for small DeepSWE config comparisons.

This is meant for early screens on small subsets (for example 12_v0), where one
bad cell can dominate raw means. The table keeps the high-signal metrics:
robust central quality, solve rate, tail risk, variance, and token cost.

Definitions:
  robust partial = average across tasks of each task's median partial reward
                   over included reps.
  solve rate     = average across tasks of each task's mean binary solve rate.
  token metrics  = task-level means/medians first, then aggregate across tasks,
                   so each task has equal weight even if reps are imbalanced.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "harness"))

from lib import model_leaf  # noqa: E402


METRICS = [
    ("robust_partial", "robust partial", "float"),
    ("solve_rate", "solve rate", "rate"),
    ("catastrophic_cells", "catastrophic cells <0.5", "int"),
    ("max_task_partial_std", "max task partial std", "float"),
    ("mean_combined_tokens", "mean combined tokens", "tokens"),
    ("median_combined_tokens", "median combined tokens", "tokens"),
    ("median_om_worker_tokens", "median OM worker tokens", "tokens"),
]


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def median(xs: list[float]) -> float:
    return float(st.median(xs)) if xs else 0.0


def stddev(xs: list[float]) -> float:
    return float(st.stdev(xs)) if len(xs) > 1 else 0.0


def load_task_filter(*, subset: str | None, tasks: str | None) -> set[str] | None:
    if subset and tasks:
        raise SystemExit("pass only one of --subset / --tasks")
    if tasks:
        return {t.strip() for t in tasks.split(",") if t.strip()}
    if subset:
        path = REPO / "subsets" / f"{subset}.txt"
        if not path.exists():
            raise SystemExit(f"subset file not found: {path}")
        return {t.strip() for t in path.read_text().splitlines() if t.strip()}
    return None


def load_results(model: str, thinking: str, config: str, task_filter: set[str] | None) -> dict[str, list[dict[str, Any]]]:
    root = REPO / "results" / model_leaf(model) / thinking / config
    if not root.exists():
        raise SystemExit(f"result config path not found: {root}")
    out: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(root.glob("*/rep*/result.json")):
        try:
            rec = json.loads(path.read_text())
        except Exception as exc:
            raise SystemExit(f"failed to read {path}: {exc}") from exc
        task = rec.get("task") or path.parts[-3]
        if task_filter is not None and task not in task_filter:
            continue
        out.setdefault(task, []).append(rec)
    for task in out:
        out[task].sort(key=lambda r: int(r.get("rep", 0)))
    return out


def included_tasks(results: dict[str, dict[str, list[dict[str, Any]]]], mode: str) -> list[str]:
    task_sets = [set(tasks) for tasks in results.values()]
    if not task_sets:
        return []
    if mode == "union":
        tasks = set().union(*task_sets)
    else:
        tasks = set.intersection(*task_sets)
    return sorted(tasks)


def align_reps(task_rows: dict[str, list[dict[str, Any]]], configs: list[str], paired_reps: bool) -> dict[str, list[dict[str, Any]]]:
    if not paired_reps:
        return task_rows
    rep_sets = []
    by_config_rep: dict[str, dict[int, dict[str, Any]]] = {}
    for config in configs:
        by_rep = {int(r.get("rep", 0)): r for r in task_rows.get(config, [])}
        by_config_rep[config] = by_rep
        rep_sets.append(set(by_rep))
    common_reps = set.intersection(*rep_sets) if rep_sets else set()
    return {config: [by_config_rep[config][rep] for rep in sorted(common_reps)] for config in configs}


def combined_tokens(rec: dict[str, Any]) -> float:
    value = rec.get("combined_total_tokens")
    if value is None:
        value = rec.get("total_tokens")
    return float(value or 0)


def summarize_config(config: str, rows_by_task: dict[str, list[dict[str, Any]]], tasks: list[str]) -> dict[str, Any]:
    partial_medians: list[float] = []
    solve_rates: list[float] = []
    partial_stds: list[float] = []
    combined_means: list[float] = []
    worker_means: list[float] = []
    catastrophic = 0
    cells = 0
    om_worker_usage_captured_cells = 0

    for task in tasks:
        rows = rows_by_task.get(task, [])
        if not rows:
            continue
        cells += len(rows)
        om_worker_usage_captured_cells += sum(1 for r in rows if "om_worker_total_tokens" in r)
        partials = [float(r.get("reward_partial") or 0.0) for r in rows]
        solves = [1.0 if r.get("reward_binary") == 1 else 0.0 for r in rows]
        combined = [combined_tokens(r) for r in rows]
        workers = [float(r.get("om_worker_total_tokens") or 0.0) for r in rows]

        partial_medians.append(median(partials))
        solve_rates.append(mean(solves))
        partial_stds.append(stddev(partials))
        combined_means.append(mean(combined))
        worker_means.append(mean(workers))
        catastrophic += sum(1 for x in partials if x < 0.5)

    return {
        "config": config,
        "tasks": len([t for t in tasks if rows_by_task.get(t)]),
        "cells": cells,
        "om_worker_usage_captured_cells": om_worker_usage_captured_cells,
        "om_worker_usage_missing_cells": max(0, cells - om_worker_usage_captured_cells),
        "robust_partial": mean(partial_medians),
        "solve_rate": mean(solve_rates),
        "catastrophic_cells": catastrophic,
        "max_task_partial_std": max(partial_stds) if partial_stds else 0.0,
        "mean_combined_tokens": mean(combined_means),
        "median_combined_tokens": median(combined_means),
        "median_om_worker_tokens": median(worker_means),
    }


def summarize_per_task(
    results: dict[str, dict[str, list[dict[str, Any]]]],
    configs: list[str],
    tasks: list[str],
    paired_reps: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for task in tasks:
        task_rows = {config: results[config].get(task, []) for config in configs}
        task_rows = align_reps(task_rows, configs, paired_reps)
        for config in configs:
            rows = task_rows.get(config, [])
            if not rows:
                continue
            partials = [float(r.get("reward_partial") or 0.0) for r in rows]
            solves = [1.0 if r.get("reward_binary") == 1 else 0.0 for r in rows]
            combined = [combined_tokens(r) for r in rows]
            workers = [float(r.get("om_worker_total_tokens") or 0.0) for r in rows]
            out.append({
                "task": task,
                "config": config,
                "reps": len(rows),
                "median_partial": median(partials),
                "solve_rate": mean(solves),
                "partial_std": stddev(partials),
                "catastrophic_cells": sum(1 for x in partials if x < 0.5),
                "mean_combined_tokens": mean(combined),
                "median_combined_tokens": median(combined),
                "mean_om_worker_tokens": mean(workers),
            })
    return out


def fmt_value(value: float | int, kind: str, *, signed: bool = False) -> str:
    sign = "+" if signed and float(value) > 0 else ""
    if kind == "int":
        return f"{sign}{int(value)}"
    if kind == "tokens":
        value = float(value)
        if abs(value) >= 1_000_000:
            return f"{sign}{value / 1_000_000:.2f}M"
        if abs(value) >= 1_000:
            return f"{sign}{value / 1_000:.0f}k"
        return f"{sign}{int(round(value))}"
    return f"{sign}{float(value):.3f}"


def worker_usage_warnings(summaries: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for row in summaries:
        config = row["config"]
        missing = int(row.get("om_worker_usage_missing_cells") or 0)
        cells = int(row.get("cells") or 0)
        if "observational-memory" in config and missing:
            warnings.append(
                f"{config}: OM worker usage fields missing on {missing}/{cells} cells; "
                "combined/worker token metrics may undercount extension cost for those cells."
            )
    return warnings


def emit_markdown(summaries: list[dict[str, Any]], per_task: list[dict[str, Any]], baseline: str, show_per_task: bool) -> None:
    by_config = {row["config"]: row for row in summaries}
    configs = [row["config"] for row in summaries]
    base = by_config[baseline]

    print("| metric | " + " | ".join(configs) + " | " + " | ".join(f"Δ {c}" for c in configs if c != baseline) + " |")
    print("|---" + "|---:" * (len(configs) + len(configs) - 1) + "|")
    for key, label, kind in METRICS:
        vals = [fmt_value(by_config[c][key], kind) for c in configs]
        deltas = [fmt_value(by_config[c][key] - base[key], kind, signed=True) for c in configs if c != baseline]
        print("| " + label + " | " + " | ".join(vals + deltas) + " |")

    print("\nDefinitions: robust partial = average across tasks of each task's median partial reward over reps. Combined tokens include main executor plus captured extension workers.")
    warnings = worker_usage_warnings(summaries)
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")
    print("\nCoverage:")
    print("| config | tasks | cells |")
    print("|---|---:|---:|")
    for row in summaries:
        print(f"| {row['config']} | {row['tasks']} | {row['cells']} |")

    if not show_per_task:
        return
    print("\n## Per-task details")
    print("| task | config | reps | median partial | solve rate | partial std | catastrophic | mean combined tokens | mean OM worker tokens |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in per_task:
        print(
            f"| {row['task']} | {row['config']} | {row['reps']} | "
            f"{row['median_partial']:.3f} | {row['solve_rate']:.3f} | {row['partial_std']:.3f} | "
            f"{row['catastrophic_cells']} | {fmt_value(row['mean_combined_tokens'], 'tokens')} | "
            f"{fmt_value(row['mean_om_worker_tokens'], 'tokens')} |"
        )


def emit_csv(summaries: list[dict[str, Any]], per_task: list[dict[str, Any]], show_per_task: bool) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=["config", "tasks", "cells", "om_worker_usage_captured_cells", "om_worker_usage_missing_cells"] + [key for key, _, _ in METRICS])
    writer.writeheader()
    for row in summaries:
        writer.writerow({key: row.get(key) for key in writer.fieldnames or []})
    if show_per_task:
        sys.stdout.write("\n")
        writer = csv.DictWriter(sys.stdout, fieldnames=list(per_task[0].keys()) if per_task else [])
        if per_task:
            writer.writeheader()
            writer.writerows(per_task)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="executor model id, e.g. openai-codex/gpt-5.5")
    ap.add_argument("--thinking", required=True, help="thinking level path segment")
    ap.add_argument("--configs", required=True, help="comma-separated configs; first is baseline unless --baseline is set")
    ap.add_argument("--baseline", help="config to use for delta columns; defaults to first --configs entry")
    ap.add_argument("--subset", help="optional subsets/<name>.txt filter, without .txt")
    ap.add_argument("--tasks", help="optional comma-separated task ids")
    ap.add_argument("--task-mode", choices=["common", "union"], default="common", help="default: common tasks across all configs")
    ap.add_argument("--paired-reps", action="store_true", help="for each task, restrict all configs to rep ids present in every config")
    ap.add_argument("--per-task", action="store_true", help="include long per-task detail table")
    ap.add_argument("--format", choices=["markdown", "csv", "json"], default="markdown")
    args = ap.parse_args()

    configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    if not configs:
        raise SystemExit("--configs is empty")
    baseline = args.baseline or configs[0]
    if baseline not in configs:
        raise SystemExit(f"baseline {baseline!r} is not in configs")

    task_filter = load_task_filter(subset=args.subset, tasks=args.tasks)
    raw_results = {config: load_results(args.model, args.thinking, config, task_filter) for config in configs}
    tasks = included_tasks(raw_results, args.task_mode)
    if not tasks:
        raise SystemExit("no overlapping tasks found for selected configs")

    # Optionally align rep ids task-by-task before summary. This is useful when a
    # partial run has uneven rep coverage.
    results: dict[str, dict[str, list[dict[str, Any]]]] = {config: {} for config in configs}
    for task in tasks:
        task_rows = {config: raw_results[config].get(task, []) for config in configs}
        task_rows = align_reps(task_rows, configs, args.paired_reps)
        for config in configs:
            if task_rows.get(config):
                results[config][task] = task_rows[config]

    tasks = included_tasks(results, args.task_mode)
    summaries = [summarize_config(config, results[config], tasks) for config in configs]
    per_task = summarize_per_task(results, configs, tasks, paired_reps=False)

    if args.format == "json":
        print(json.dumps({
            "model": args.model,
            "thinking": args.thinking,
            "configs": configs,
            "baseline": baseline,
            "task_mode": args.task_mode,
            "paired_reps": args.paired_reps,
            "tasks": tasks,
            "summaries": summaries,
            "warnings": worker_usage_warnings(summaries),
            "per_task": per_task if args.per_task else None,
            "definitions": {
                "robust_partial": "average across tasks of each task's median partial reward over reps",
                "solve_rate": "average across tasks of each task's mean reward_binary == 1 rate",
                "combined_tokens": "main executor plus captured extension worker tokens",
            },
        }, indent=2, sort_keys=True))
    elif args.format == "csv":
        emit_csv(summaries, per_task, args.per_task)
    else:
        emit_markdown(summaries, per_task, baseline, args.per_task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
