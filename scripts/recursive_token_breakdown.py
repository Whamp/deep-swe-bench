#!/usr/bin/env python3
"""Token/cost breakdowns for pi-recursive benchmark results.

Inputs are result.json files, cell directories, or config result leaves containing
``*/rep*/result.json``. The script reports executor tokens separately from
recursive child tokens, then compares combined totals against the first row.

Examples:
  scripts/recursive_token_breakdown.py \
    --result original=analysis/pi-recursive-smoke-backups/rep0.pre-audit-prompt-20260702-063314/result.json \
    --result audit=results/gpt-5.5/low/pi-recursive/superjson-error-stack-serialization/rep0/result.json

  scripts/recursive_token_breakdown.py \
    --result pi-recursive=results/gpt-5.5/low/pi-recursive \
    --subset 12_v2
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]


TOKEN_FIELDS = [
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "total_tokens",
    "cost_usd",
    "recursive_child_calls",
    "recursive_child_input_tokens",
    "recursive_child_output_tokens",
    "recursive_child_cache_read_tokens",
    "recursive_child_cache_write_tokens",
    "recursive_child_total_tokens",
    "recursive_child_cost_usd",
    "combined_total_tokens",
    "combined_cost_usd",
]


@dataclass
class Dataset:
    label: str
    rows: list[dict[str, Any]]


def num(row: dict[str, Any], key: str) -> float:
    value = row.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    return float(st.median(values)) if values else 0.0


def load_task_filter(subset: str | None, tasks: str | None) -> set[str] | None:
    if subset and tasks:
        raise SystemExit("pass only one of --subset / --tasks")
    if tasks:
        return {t.strip() for t in tasks.split(",") if t.strip()}
    if subset:
        path = REPO / "subsets" / f"{subset}.txt"
        if not path.exists():
            raise SystemExit(f"subset file not found: {path}")
        return {line.strip() for line in path.read_text().splitlines() if line.strip()}
    return None


def result_paths(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        raise SystemExit(f"path not found: {path}")
    direct = path / "result.json"
    if direct.exists():
        return [direct]
    paths = sorted(path.glob("*/rep*/result.json"))
    if not paths:
        raise SystemExit(f"no result.json files under: {path}")
    return paths


def load_rows(path: Path, task_filter: set[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in result_paths(path):
        try:
            row = json.loads(p.read_text())
        except Exception as exc:  # pragma: no cover - CLI error path
            raise SystemExit(f"failed to read {p}: {exc}") from exc
        task = row.get("task") or (p.parts[-3] if len(p.parts) >= 3 else None)
        if task_filter is not None and task not in task_filter:
            continue
        row["_path"] = str(p)
        rows.append(row)
    if not rows:
        raise SystemExit(f"no rows matched filter for: {path}")
    return rows


def parse_result_arg(value: str, task_filter: set[str] | None) -> Dataset:
    if "=" in value:
        label, raw_path = value.split("=", 1)
        label = label.strip()
    else:
        raw_path = value
        label = Path(value).name
    if not label:
        raise SystemExit(f"empty label in --result {value!r}")
    return Dataset(label=label, rows=load_rows(Path(raw_path), task_filter))


def summarize(ds: Dataset) -> dict[str, Any]:
    rows = ds.rows
    cells = len(rows)
    tasks = {str(row.get("task") or "") for row in rows if row.get("task")}
    solves = sum(1 for row in rows if row.get("reward_binary") == 1)
    partials = [num(row, "reward_partial") for row in rows]

    out: dict[str, Any] = {
        "label": ds.label,
        "cells": cells,
        "tasks": len(tasks) if tasks else None,
        "solves": solves,
        "solve_rate": solves / cells if cells else 0.0,
        "mean_partial": mean(partials),
    }
    for key in TOKEN_FIELDS:
        values = [num(row, key) for row in rows]
        out[f"sum_{key}"] = sum(values)
        out[f"mean_{key}"] = mean(values)
        out[f"median_{key}"] = median(values)

    # Some older records have combined totals but not combined output fields.
    out["mean_combined_output_tokens"] = out["mean_output_tokens"] + out["mean_recursive_child_output_tokens"]
    out["sum_combined_output_tokens"] = out["sum_output_tokens"] + out["sum_recursive_child_output_tokens"]
    out["mean_child_total_over_executor_total"] = (
        out["mean_recursive_child_total_tokens"] / out["mean_total_tokens"]
        if out["mean_total_tokens"]
        else 0.0
    )
    out["mean_child_output_over_executor_output"] = (
        out["mean_recursive_child_output_tokens"] / out["mean_output_tokens"]
        if out["mean_output_tokens"]
        else 0.0
    )
    return out


def with_baseline_multiples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return rows
    base = rows[0]
    for row in rows:
        for key in [
            "mean_total_tokens",
            "mean_output_tokens",
            "mean_recursive_child_total_tokens",
            "mean_recursive_child_output_tokens",
            "mean_combined_total_tokens",
            "mean_combined_output_tokens",
            "mean_combined_cost_usd",
        ]:
            b = base.get(key) or 0
            row[f"{key}_multiple"] = (row.get(key, 0) / b) if b else None
    return rows


def fmt_int(value: Any) -> str:
    return f"{float(value):,.0f}"


def fmt_float(value: Any, places: int = 3) -> str:
    return f"{float(value):.{places}f}"


def fmt_cost(value: Any) -> str:
    return f"${float(value):.3f}"


def fmt_multiple(value: Any) -> str:
    return "—" if value is None else f"{float(value):.2f}x"


def print_markdown(rows: list[dict[str, Any]]) -> None:
    headers = [
        "label",
        "cells",
        "solves",
        "partial",
        "exec out/cell",
        "exec total/cell",
        "child calls/cell",
        "child out/cell",
        "child total/cell",
        "child/exec total",
        "combined out/cell",
        "combined total/cell",
        "combined total ×base",
        "cost/cell",
        "cost ×base",
    ]
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        cells = row["cells"]
        values = [
            row["label"],
            str(cells),
            f"{row['solves']}/{cells}",
            fmt_float(row["mean_partial"], 3),
            fmt_int(row["mean_output_tokens"]),
            fmt_int(row["mean_total_tokens"]),
            fmt_float(row["mean_recursive_child_calls"], 2),
            fmt_int(row["mean_recursive_child_output_tokens"]),
            fmt_int(row["mean_recursive_child_total_tokens"]),
            fmt_multiple(row["mean_child_total_over_executor_total"]),
            fmt_int(row["mean_combined_output_tokens"]),
            fmt_int(row["mean_combined_total_tokens"]),
            fmt_multiple(row.get("mean_combined_total_tokens_multiple")),
            fmt_cost(row["mean_combined_cost_usd"]),
            fmt_multiple(row.get("mean_combined_cost_usd_multiple")),
        ]
        print("| " + " | ".join(values) + " |")

    if len(rows) >= 2:
        base = rows[0]
        print("\nDelta vs first row:")
        print("| label | exec out | child out | combined out | exec total | child total | combined total | cost |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|")
        for row in rows[1:]:
            values = [
                row["label"],
                fmt_int(row["mean_output_tokens"] - base["mean_output_tokens"]),
                fmt_int(row["mean_recursive_child_output_tokens"] - base["mean_recursive_child_output_tokens"]),
                fmt_int(row["mean_combined_output_tokens"] - base["mean_combined_output_tokens"]),
                fmt_int(row["mean_total_tokens"] - base["mean_total_tokens"]),
                fmt_int(row["mean_recursive_child_total_tokens"] - base["mean_recursive_child_total_tokens"]),
                fmt_int(row["mean_combined_total_tokens"] - base["mean_combined_total_tokens"]),
                fmt_cost(row["mean_combined_cost_usd"] - base["mean_combined_cost_usd"]),
            ]
            print("| " + " | ".join(values) + " |")


def print_csv(rows: list[dict[str, Any]]) -> None:
    fields = [
        "label", "cells", "tasks", "solves", "solve_rate", "mean_partial",
        "mean_output_tokens", "mean_total_tokens",
        "mean_recursive_child_calls", "mean_recursive_child_output_tokens",
        "mean_recursive_child_total_tokens", "mean_child_total_over_executor_total",
        "mean_combined_output_tokens", "mean_combined_total_tokens",
        "mean_combined_total_tokens_multiple", "mean_combined_cost_usd",
        "mean_combined_cost_usd_multiple",
    ]
    writer = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--result", action="append", required=True,
                    help="LABEL=path to result.json, cell dir, or config result leaf; repeatable")
    ap.add_argument("--subset", help="optional subset filter, e.g. 12_v2")
    ap.add_argument("--tasks", help="optional comma-separated task filter")
    ap.add_argument("--format", choices=["markdown", "csv", "json"], default="markdown")
    args = ap.parse_args()

    task_filter = load_task_filter(args.subset, args.tasks)
    rows = with_baseline_multiples([
        summarize(parse_result_arg(value, task_filter)) for value in args.result
    ])

    if args.format == "json":
        print(json.dumps(rows, indent=2, sort_keys=True))
    elif args.format == "csv":
        print_csv(rows)
    else:
        print_markdown(rows)


if __name__ == "__main__":
    main()
