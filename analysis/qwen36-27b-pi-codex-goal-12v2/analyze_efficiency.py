#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = ROOT / "results/Qwen3.6-27B-AWQ-BF16-INT4/high"
CONFIGS = {
    "baseline": "baseline-qwen36-27b",
    "contract_checkpoint": "qwen36-27b-contract-checkpoints",
    "create_goal": "qwen36-27b-pi-codex-goal",
}
SUBSET = ROOT / "subsets/12_v2.txt"
DIFFICULTY = ROOT / "data/deepswe-v1.1-task-difficulty.tsv"
OUT = Path(__file__).with_name("efficiency.json")
METRICS = [
    "reward_binary", "reward_partial", "total_tokens", "input_tokens",
    "cache_read_tokens", "output_tokens", "cost_usd", "agent_wall_s",
    "turns", "tool_calls", "patch_bytes", "patch_files", "patch_added_lines",
    "patch_deleted_lines",
]


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def patch_stats(path: Path) -> dict[str, int]:
    text = path.read_text(errors="replace") if path.exists() else ""
    added = deleted = 0
    files: set[str] = set()
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            files.add(line[6:])
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            deleted += 1
    return {"patch_files": len(files), "patch_added_lines": added, "patch_deleted_lines": deleted}


def session_stats(cell: Path) -> dict[str, Any]:
    tool_counts: Counter[str] = Counter()
    goal_events: Counter[str] = Counter()
    usage_events = 0
    max_goal_tokens = 0
    max_active_seconds = 0
    goal_status = None
    for path in cell.glob("session/*.jsonl"):
        for raw in path.open(errors="replace"):
            event = json.loads(raw)
            if event.get("type") == "message":
                message = event.get("message", {})
                if message.get("role") == "assistant":
                    for part in message.get("content", []):
                        if part.get("type") == "toolCall":
                            tool_counts[part.get("name", "unknown")] += 1
            if event.get("type") == "custom" and event.get("customType") == "pi-codex-goal":
                data = event.get("data", {})
                kind = str(data.get("kind", "unknown"))
                goal_events[kind] += 1
                if kind == "usage":
                    usage_events += 1
                    usage = data.get("usage", {})
                    max_goal_tokens = max(max_goal_tokens, int(usage.get("tokensUsed", 0) or 0))
                    max_active_seconds = max(max_active_seconds, int(usage.get("activeSeconds", 0) or 0))
                    goal_status = data.get("status", goal_status)
                elif kind == "set":
                    goal_status = data.get("goal", {}).get("status", goal_status)
    return {
        "tool_counts": dict(sorted(tool_counts.items())),
        "goal_tool_calls": sum(tool_counts[k] for k in ("create_goal", "get_goal", "update_goal")),
        "create_goal_calls": tool_counts["create_goal"],
        "get_goal_calls": tool_counts["get_goal"],
        "update_goal_calls": tool_counts["update_goal"],
        "goal_custom_events": dict(sorted(goal_events.items())),
        "goal_usage_events": usage_events,
        "goal_reported_tokens_max": max_goal_tokens,
        "goal_active_seconds_max": max_active_seconds,
        "goal_final_status": goal_status,
    }


def summarize(cells: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {m: sum(float(c[m]) for c in cells) for m in METRICS}
    medians = {m: median([float(c[m]) for c in cells]) for m in METRICS}
    return {
        "cells": len(cells),
        "solves": sum(c["reward_binary"] == 1 for c in cells),
        "solve_rate": sum(c["reward_binary"] == 1 for c in cells) / len(cells),
        "partial_total": totals["reward_partial"],
        "partial_mean": totals["reward_partial"] / len(cells),
        "near_solves_unsolved": {
            "ge_0.90": sum(c["reward_binary"] != 1 and c["reward_partial"] >= .90 for c in cells),
            "ge_0.95": sum(c["reward_binary"] != 1 and c["reward_partial"] >= .95 for c in cells),
        },
        "partial_attainment_including_solves": {
            "ge_0.90": sum(c["reward_partial"] >= .90 for c in cells),
            "ge_0.95": sum(c["reward_partial"] >= .95 for c in cells),
        },
        "timeouts": sum(bool(c["agent_timed_out"]) for c in cells),
        "reward_minus_one": sum(c["reward_binary"] == -1 or c["reward_partial"] == -1 for c in cells),
        "totals": totals,
        "medians": medians,
        "goal_activity_totals": {
            k: sum(int(c[k]) for c in cells)
            for k in ["goal_tool_calls", "create_goal_calls", "get_goal_calls", "update_goal_calls", "goal_usage_events", "goal_reported_tokens_max", "goal_active_seconds_max"]
        },
        "goal_activity_medians": {
            k: median([float(c[k]) for c in cells])
            for k in ["goal_tool_calls", "create_goal_calls", "get_goal_calls", "update_goal_calls", "goal_usage_events", "goal_reported_tokens_max", "goal_active_seconds_max"]
        },
        "goal_status_counts": dict(Counter(str(c["goal_final_status"]) for c in cells)),
    }


def delta(right: dict[str, Any], left: dict[str, Any]) -> dict[str, Any]:
    return {
        "solve_delta": right["solves"] - left["solves"],
        "partial_total_delta": right["partial_total"] - left["partial_total"],
        "partial_mean_delta": right["partial_mean"] - left["partial_mean"],
        "near_solve_delta": {k: right["near_solves_unsolved"][k] - left["near_solves_unsolved"][k] for k in right["near_solves_unsolved"]},
        "partial_attainment_delta": {k: right["partial_attainment_including_solves"][k] - left["partial_attainment_including_solves"][k] for k in right["partial_attainment_including_solves"]},
        "timeout_delta": right["timeouts"] - left["timeouts"],
        "totals": {m: right["totals"][m] - left["totals"][m] for m in METRICS},
        "medians": {m: right["medians"][m] - left["medians"][m] for m in METRICS},
        "total_percent": {
            m: ((right["totals"][m] / left["totals"][m] - 1) * 100) if left["totals"][m] else None
            for m in METRICS
        },
    }


def aggregate_frontier(summaries: dict[str, dict[str, Any]], value: str, cost: str) -> list[str]:
    names = list(summaries)
    frontier = []
    for name in names:
        v = summaries[name][value] if value in summaries[name] else summaries[name]["totals"][value]
        c = summaries[name]["totals"][cost]
        dominated = False
        for other in names:
            if other == name:
                continue
            ov = summaries[other][value] if value in summaries[other] else summaries[other]["totals"][value]
            oc = summaries[other]["totals"][cost]
            if ov >= v and oc <= c and (ov > v or oc < c):
                dominated = True
                break
        if not dominated:
            frontier.append(name)
    return frontier


def main() -> None:
    tasks = [x.strip() for x in SUBSET.read_text().splitlines() if x.strip()]
    with DIFFICULTY.open() as f:
        difficulty = {row["slug"]: row for row in csv.DictReader(f, delimiter="\t")}
    cells: dict[str, list[dict[str, Any]]] = {}
    keyed: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    for label, dirname in CONFIGS.items():
        rows = []
        for task in tasks:
            for rep in range(3):
                cell = RESULT_ROOT / dirname / task / f"rep{rep}"
                result_path = cell / "result.json"
                if not result_path.exists():
                    raise FileNotFoundError(result_path)
                row = json.loads(result_path.read_text())
                row.update(patch_stats(cell / "artifacts/model.patch"))
                row.update(session_stats(cell))
                row["difficulty_pass_rate"] = float(difficulty[task]["pass_rate"])
                row["title"] = difficulty[task]["title"]
                row["repository"] = difficulty[task]["repository"]
                rows.append(row)
        cells[label] = rows
        keyed[label] = {(r["task"], int(r["rep"])): r for r in rows}
    expected = {(task, rep) for task in tasks for rep in range(3)}
    assert all(set(v) == expected for v in keyed.values())
    summaries = {name: summarize(rows) for name, rows in cells.items()}
    comparisons = {
        "create_goal_vs_baseline": delta(summaries["create_goal"], summaries["baseline"]),
        "create_goal_vs_contract_checkpoint": delta(summaries["create_goal"], summaries["contract_checkpoint"]),
        "contract_checkpoint_vs_baseline": delta(summaries["contract_checkpoint"], summaries["baseline"]),
    }
    paired = []
    for task, rep in sorted(expected):
        entry: dict[str, Any] = {"task": task, "rep": rep, "difficulty_pass_rate": keyed["baseline"][(task, rep)]["difficulty_pass_rate"]}
        for name in CONFIGS:
            r = keyed[name][(task, rep)]
            entry[name] = {k: r[k] for k in ["reward_binary", "reward_partial", "total_tokens", "input_tokens", "cache_read_tokens", "output_tokens", "cost_usd", "agent_wall_s", "turns", "tool_calls", "patch_bytes", "patch_files", "patch_added_lines", "patch_deleted_lines", "agent_timed_out", "agent_exit", "goal_tool_calls", "goal_usage_events", "goal_reported_tokens_max", "goal_active_seconds_max", "goal_final_status"]}
        paired.append(entry)
    flips = {
        "create_goal_only_vs_baseline": [f"{p['task']}/rep{p['rep']}" for p in paired if p["create_goal"]["reward_binary"] == 1 and p["baseline"]["reward_binary"] == 0],
        "baseline_only_vs_create_goal": [f"{p['task']}/rep{p['rep']}" for p in paired if p["baseline"]["reward_binary"] == 1 and p["create_goal"]["reward_binary"] == 0],
        "create_goal_only_vs_contract_checkpoint": [f"{p['task']}/rep{p['rep']}" for p in paired if p["create_goal"]["reward_binary"] == 1 and p["contract_checkpoint"]["reward_binary"] == 0],
        "contract_checkpoint_only_vs_create_goal": [f"{p['task']}/rep{p['rep']}" for p in paired if p["contract_checkpoint"]["reward_binary"] == 1 and p["create_goal"]["reward_binary"] == 0],
    }
    frontier = {}
    for value in ["solves", "partial_total"]:
        frontier[value] = {cost: aggregate_frontier(summaries, value, cost) for cost in ["total_tokens", "output_tokens", "agent_wall_s", "turns", "tool_calls"]}
    output = {
        "schema_version": 1,
        "comparison": {"model": "local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4", "thinking": "high", "subset": "12_v2", "reps": [0, 1, 2], "cells_per_config": 36, "configs": CONFIGS, "timeout_policy": "Count timeout and reward=-1 as observed config outcomes absent concrete infrastructure evidence.", "excluded": ["results/_contaminated"], "wall_field": "agent_wall_s", "cost_note": "Local-vLLM result cost_usd is zero for every cell; tokens and wall time are the informative cost axes."},
        "summaries": summaries,
        "comparisons": comparisons,
        "solve_flips": flips,
        "aggregate_pareto_frontiers": frontier,
        "verdict": {
            "solve_gain": "Create-goal produced the comparison's only solve (go-critic-doc-link-checker/rep1), versus zero for both alternatives.",
            "efficiency_vs_baseline": "The solve came with 7,172,649 fewer total tokens (-2.71%) but 28,578 more output tokens (+1.79%), 1,271.5 more agent-wall seconds (+2.04%), 209 more turns (+5.93%), and 279 more tool calls (+7.19%). Aggregate partial reward fell 0.2381, so this is a real solve gain but not a broad quality gain.",
            "efficiency_vs_contract_checkpoint": "Create-goal added one solve and 1.4022 partial-reward points while using 7,534.8 fewer agent-wall seconds (-10.58%) and a 150,399-byte smaller aggregate patch (-9.09%), but used 15,821,793 more total tokens (+6.54%), 82,355 more output tokens (+5.33%), 387 more turns (+11.56%), and 414 more tool calls (+11.05%).",
            "goal_overhead": "Every create-goal cell called create_goal once; 31/36 called update_goal and ended complete, four ended active, and one budgetLimited. Goal tools added 74 calls, while 3,510 custom usage events recorded continuation activity. These events are instrumentation heartbeats, not model turns or extra LLM calls.",
            "frontier": "Create-goal expands the solve-cost frontier on every informative resource axis because it is the only config with a solve. It also adds a nondominated partial-reward point on total/input-token cost, but not on output tokens, wall time, turns, or tool calls; baseline dominates it on those partial-cost axes. Monetary cost is uninformative because all local-vLLM cells report $0.",
            "overall": "Qualified efficiency win: create-goal buys one unique solve and beats baseline on total-token cost, but the gain is isolated, aggregate partial reward is slightly lower than baseline, high-threshold partial attainment does not improve, and interaction/output/wall overhead rises. It is a solve-frontier expansion, not a general efficiency-frontier shift.",
        },
        "paired_cells": paired,
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
