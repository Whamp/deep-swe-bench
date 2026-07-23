#!/usr/bin/env python3
"""Build the completed Qwen3.6-27B 12-task × 3-rep evidence ledger."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

RESULT_ROOT = Path(
    "results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b"
)
OUT_DIR = Path("analysis/qwen36-27b-support-deep-dive")


def load_json(path: Path) -> dict[str, object]:
    """Load one JSON object."""
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def number(value: object) -> float:
    """Return a numeric JSON field as a float."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"expected number, got {value!r}")
    return float(value)


def integer(value: object) -> int:
    """Return an integral JSON field as an integer."""
    result = number(value)
    if not result.is_integer():
        raise ValueError(f"expected integer, got {value!r}")
    return int(result)


def patch_stats(path: Path) -> tuple[int, int, int]:
    """Count changed files and added/deleted lines in a unified diff."""
    files: set[str] = set()
    added = 0
    deleted = 0
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("+++ b/"):
            files.add(line[6:])
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            deleted += 1
    return len(files), added, deleted


def build_cells() -> list[dict[str, object]]:
    """Build normalized rows for every persisted benchmark cell."""
    rows: list[dict[str, object]] = []
    for result_path in sorted(RESULT_ROOT.glob("*/rep*/result.json")):
        result = load_json(result_path)
        patch_path = result_path.parent / "artifacts" / "model.patch"
        files, added, deleted = patch_stats(patch_path)
        f2p_total = result.get("f2p_total")
        f2p_passed = result.get("f2p_passed")
        p2p_total = result.get("p2p_total")
        p2p_passed = result.get("p2p_passed")
        scored = all(
            value is not None
            for value in (f2p_total, f2p_passed, p2p_total, p2p_passed)
        )
        rows.append(
            {
                "task": str(result["task"]),
                "rep": integer(result["rep"]),
                "reward_binary": integer(result["reward_binary"]),
                "reward_partial": number(result["reward_partial"]),
                "scored": scored,
                "f2p_passed": integer(f2p_passed) if scored else None,
                "f2p_total": integer(f2p_total) if scored else None,
                "p2p_passed": integer(p2p_passed) if scored else None,
                "p2p_total": integer(p2p_total) if scored else None,
                "patch_bytes": integer(result["patch_bytes"]),
                "patch_files": files,
                "patch_added": added,
                "patch_deleted": deleted,
                "turns": integer(result["turns"]),
                "tool_calls": integer(result["tool_calls"]),
                "total_tokens": integer(result["total_tokens"]),
                "agent_wall_s": number(result["agent_wall_s"]),
                "agent_timed_out": result["agent_timed_out"] is True,
                "verifier_timed_out": result["verifier_exit"] == "timeout",
            }
        )
    return rows


def ratio(passed: object, total: object) -> float:
    """Compute a passed/total ratio from normalized row fields."""
    denominator = integer(total)
    return integer(passed) / denominator if denominator else 0.0


def aggregate(rows: list[dict[str, object]]) -> dict[str, object]:
    """Compute run-level and task-level metrics."""
    scored = [row for row in rows if row["scored"] is True]
    f2p_passed = sum(integer(row["f2p_passed"]) for row in scored)
    f2p_total = sum(integer(row["f2p_total"]) for row in scored)
    p2p_passed = sum(integer(row["p2p_passed"]) for row in scored)
    p2p_total = sum(integer(row["p2p_total"]) for row in scored)
    by_task: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_task[str(row["task"])].append(row)
    return {
        "cells": len(rows),
        "tasks": len(by_task),
        "solves": sum(integer(row["reward_binary"]) == 1 for row in rows),
        "empty_patches": sum(integer(row["patch_bytes"]) == 0 for row in rows),
        "reward_minus_1": sum(
            integer(row["reward_binary"]) == -1 for row in rows
        ),
        "agent_timeouts": sum(row["agent_timed_out"] is True for row in rows),
        "verifier_timeouts": sum(
            row["verifier_timed_out"] is True for row in rows
        ),
        "scored_cells": len(scored),
        "mean_partial": mean(number(row["reward_partial"]) for row in rows),
        "f2p": {
            "passed": f2p_passed,
            "total": f2p_total,
            "micro": f2p_passed / f2p_total,
            "macro": mean(
                ratio(row["f2p_passed"], row["f2p_total"])
                for row in scored
            ),
        },
        "p2p": {
            "passed": p2p_passed,
            "total": p2p_total,
            "micro": p2p_passed / p2p_total,
            "macro": mean(
                ratio(row["p2p_passed"], row["p2p_total"])
                for row in scored
            ),
            "perfect_cells": sum(
                row["p2p_passed"] == row["p2p_total"] for row in scored
            ),
        },
        "strict_near_misses": sum(
            ratio(row["f2p_passed"], row["f2p_total"]) >= 0.9
            and row["p2p_passed"] == row["p2p_total"]
            for row in scored
        ),
        "median_tokens": median(integer(row["total_tokens"]) for row in rows),
        "median_turns": median(integer(row["turns"]) for row in rows),
        "median_tool_calls": median(
            integer(row["tool_calls"]) for row in rows
        ),
        "patch": {
            "added": sum(integer(row["patch_added"]) for row in rows),
            "deleted": sum(integer(row["patch_deleted"]) for row in rows),
            "median_added": median(
                integer(row["patch_added"]) for row in rows
            ),
            "median_files": median(
                integer(row["patch_files"]) for row in rows
            ),
        },
        "tasks_summary": task_summary(by_task),
    }


def task_summary(
    by_task: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    """Aggregate outcomes for each task."""
    summaries: list[dict[str, object]] = []
    for task, rows in sorted(by_task.items()):
        scored = [row for row in rows if row["scored"] is True]
        summaries.append(
            {
                "task": task,
                "scored_reps": len(scored),
                "reward_minus_1": sum(
                    integer(row["reward_binary"]) == -1 for row in rows
                ),
                "f2p_passed": sum(
                    integer(row["f2p_passed"]) for row in scored
                ),
                "f2p_total": sum(integer(row["f2p_total"]) for row in scored),
                "p2p_passed": sum(
                    integer(row["p2p_passed"]) for row in scored
                ),
                "p2p_total": sum(integer(row["p2p_total"]) for row in scored),
                "partial_by_rep": [
                    number(row["reward_partial"]) for row in rows
                ],
            }
        )
    return summaries


def write_outputs(rows: list[dict[str, object]]) -> None:
    """Write the normalized ledger and aggregate summary."""
    summary = aggregate(rows)
    (OUT_DIR / "full36_metrics.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    with (OUT_DIR / "full36_cells.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(summary, indent=2))


def main() -> None:
    """Build and persist the full-run evidence."""
    rows = build_cells()
    if len(rows) != 36 or len({row["task"] for row in rows}) != 12:
        raise RuntimeError("expected exactly 12 tasks × 3 repetitions")
    write_outputs(rows)


if __name__ == "__main__":
    main()
