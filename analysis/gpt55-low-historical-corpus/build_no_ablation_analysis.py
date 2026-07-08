#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "analysis/gpt55-low-historical-corpus"
REPORT_DIR = ROOT / "reports/gpt55-low-no-ablation-analysis"
OUT_JSON = ANALYSIS_DIR / "no_ablation_prompt_analysis.json"
OUT_EFFECTS_CSV = ANALYSIS_DIR / "no_ablation_prompt_factorial_effects.csv"
OUT_PROFILES_CSV = ANALYSIS_DIR / "no_ablation_task_profiles.csv"
OUT_PILOT_CSV = ANALYSIS_DIR / "no_ablation_pilot_subset_12.csv"
OUT_HTML = REPORT_DIR / "index.html"
LOW_ROOT = ROOT / "results/gpt-5.5/low"
MEDIUM_ROOT = ROOT / "results/gpt-5.5/medium"

PROMPT_CONFIGS = [
    "baseline",
    "baseline-neutral-orchestration-only",
    "baseline-preamble-only",
    "baseline-preamble-orchestration",
    "baseline-wf-only",
    "baseline-preamble-orchestration-wf",
]
MEDIUM_CONFIG = "baseline"

CONFIG_LABELS = {
    "baseline": "Clean low",
    "baseline-neutral-orchestration-only": "Neutral orchestration",
    "baseline-preamble-only": "Engineer preamble",
    "baseline-preamble-orchestration": "Preamble + neutral orchestration",
    "baseline-wf-only": "Workflow checklist",
    "baseline-preamble-orchestration-wf": "Preamble + workflow checklist",
    "medium:baseline": "Clean medium",
}

FACTORS = {
    "baseline": {"preamble": 0, "workflow": 0, "neutral": 0},
    "baseline-neutral-orchestration-only": {"preamble": 0, "workflow": 0, "neutral": 1},
    "baseline-preamble-only": {"preamble": 1, "workflow": 0, "neutral": 0},
    "baseline-preamble-orchestration": {"preamble": 1, "workflow": 0, "neutral": 1},
    "baseline-wf-only": {"preamble": 0, "workflow": 1, "neutral": 0},
    "baseline-preamble-orchestration-wf": {"preamble": 1, "workflow": 1, "neutral": 0},
}

MANIFESTS = [
    "results/_runs/gpt55-low-clean-baseline-36v2-r3-w24/manifest.json",
    "results/_runs/gpt55-low-prompt-ablation-36v2-r3-w24-v2/manifest.json",
    "results/_runs/gpt55-medium-clean-baseline-36v2-r3-w24/manifest.json",
]

BOOTSTRAP_SEED = 20260707
BOOTSTRAP_REPS = 5000
PILOT_SEED = 20260708
PRIMARY_PILOT_SIZE = 12
PILOT_SIZES = [6, 9, 12, 18]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def solved(row: dict[str, Any]) -> int:
    return 1 if row.get("reward_binary") == 1 else 0


def is_invalid_reward(row: dict[str, Any]) -> bool:
    value = row.get("reward_binary")
    return value not in (0, 1, False, True)


def cost(row: dict[str, Any]) -> float:
    return float(row.get("combined_cost_usd", row.get("cost_usd", 0.0)) or 0.0)


def tokens(row: dict[str, Any]) -> int:
    return int(row.get("combined_total_tokens", row.get("total_tokens", 0)) or 0)


def money(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.{digits}f}"


def pp(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value * 100:+.{digits}f} pp"


def fmt_num(value: float | int, digits: int = 2) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.{digits}f}"


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    idx = (len(xs) - 1) * p
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return xs[lo]
    weight = idx - lo
    return xs[lo] * (1 - weight) + xs[hi] * weight


def cell_key_from_path(result_path: Path) -> str:
    return f"{result_path.parts[-3]}/{result_path.parts[-2]}"


def task_from_cell(cell: str) -> str:
    return cell.split("/", 1)[0]


def rep_from_cell(cell: str) -> str:
    return cell.rsplit("/", 1)[1]


def read_config_cells(root: Path, config: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for result_path in sorted((root / config).glob("*/rep*/result.json")):
        try:
            row = load_json(result_path)
        except Exception:
            continue
        key = cell_key_from_path(result_path)
        row["_result_path"] = str(result_path.relative_to(ROOT))
        row["_task"] = task_from_cell(key)
        row["_rep"] = rep_from_cell(key)
        out[key] = row
    return out


def common_cells(cells_by_config: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
    sets = [set(cells) for cells in cells_by_config.values()]
    return sorted(set.intersection(*sets))


def task_cells(cells: Iterable[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for cell in cells:
        out[task_from_cell(cell)].append(cell)
    return {task: sorted(values) for task, values in sorted(out.items())}


def aggregate_config(config: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    rows = [data[config][cell] for cell in cells]
    solves = sum(solved(row) for row in rows)
    total_cost = sum(cost(row) for row in rows)
    total_tokens = sum(tokens(row) for row in rows)
    invalid = sum(1 for row in rows if is_invalid_reward(row))
    return {
        "config": config,
        "label": CONFIG_LABELS.get(config, config),
        "cells": len(rows),
        "tasks": len({task_from_cell(cell) for cell in cells}),
        "solves": solves,
        "solve_rate": solves / len(rows) if rows else 0.0,
        "total_cost_usd": round(total_cost, 6),
        "median_cost_usd": round(median([cost(row) for row in rows]), 6) if rows else 0.0,
        "total_tokens": total_tokens,
        "median_tokens": median([tokens(row) for row in rows]) if rows else 0,
        "mean_partial": mean([float(row.get("reward_partial") or 0.0) for row in rows]) if rows else 0.0,
        "invalid_reward_cells": invalid,
        "system_preamble_chars": int(median([int(row.get("system_preamble_chars") or 0) for row in rows])) if rows else 0,
        "orchestration_chars": int(median([int(row.get("orchestration_chars") or 0) for row in rows])) if rows else 0,
        "sample_result_paths": [row["_result_path"] for row in rows[:3]],
    }


def solve_count(config: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> int:
    return sum(solved(data[config][cell]) for cell in cells)


def cost_sum(config: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> float:
    return sum(cost(data[config][cell]) for cell in cells)


def contrast_value(config_a: str, config_b: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> float:
    return (solve_count(config_b, cells, data) - solve_count(config_a, cells, data)) / len(cells)


def contrast_cost(config_a: str, config_b: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> float:
    return cost_sum(config_b, cells, data) - cost_sum(config_a, cells, data)


def pair_counts(config_a: str, config_b: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> dict[str, int]:
    both = a_only = b_only = neither = 0
    for cell in cells:
        a = solved(data[config_a][cell])
        b = solved(data[config_b][cell])
        both += int(a and b)
        a_only += int(a and not b)
        b_only += int(b and not a)
        neither += int(not a and not b)
    return {"both": both, "a_only": a_only, "b_only": b_only, "neither": neither}


def build_contrast_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": "workflow_main_without_preamble",
            "label": "Workflow checklist effect without preamble",
            "formula": "workflow - clean",
            "terms": [(1.0, "baseline-wf-only"), (-1.0, "baseline")],
            "interpretation": "Concrete ordered workflow relative to clean low.",
        },
        {
            "id": "preamble_main_without_workflow",
            "label": "Engineer preamble effect without workflow",
            "formula": "preamble - clean",
            "terms": [(1.0, "baseline-preamble-only"), (-1.0, "baseline")],
            "interpretation": "Generic engineer preamble relative to clean low.",
        },
        {
            "id": "neutral_main_without_preamble",
            "label": "Neutral orchestration effect without preamble",
            "formula": "neutral - clean",
            "terms": [(1.0, "baseline-neutral-orchestration-only"), (-1.0, "baseline")],
            "interpretation": "The supposedly neutral top-of-context instruction relative to clean low.",
        },
        {
            "id": "workflow_effect_with_preamble",
            "label": "Workflow effect when preamble is already present",
            "formula": "preamble+workflow - preamble",
            "terms": [(1.0, "baseline-preamble-orchestration-wf"), (-1.0, "baseline-preamble-only")],
            "interpretation": "Whether adding checklist to the preamble improves the preamble row.",
        },
        {
            "id": "preamble_effect_with_workflow",
            "label": "Preamble effect when workflow is already present",
            "formula": "preamble+workflow - workflow",
            "terms": [(1.0, "baseline-preamble-orchestration-wf"), (-1.0, "baseline-wf-only")],
            "interpretation": "Whether adding the generic engineer preamble to the checklist helps or hurts.",
        },
        {
            "id": "preamble_workflow_interaction",
            "label": "Preamble × workflow interaction",
            "formula": "(preamble+workflow - preamble) - (workflow - clean)",
            "terms": [(1.0, "baseline-preamble-orchestration-wf"), (-1.0, "baseline-preamble-only"), (-1.0, "baseline-wf-only"), (1.0, "baseline")],
            "interpretation": "Negative values mean the checklist and generic preamble combine worse than their separate gains suggest.",
        },
        {
            "id": "neutral_effect_with_preamble",
            "label": "Neutral orchestration effect with preamble",
            "formula": "preamble+neutral - preamble",
            "terms": [(1.0, "baseline-preamble-orchestration"), (-1.0, "baseline-preamble-only")],
            "interpretation": "Whether adding neutral orchestration changes the preamble row.",
        },
        {
            "id": "preamble_neutral_interaction",
            "label": "Preamble × neutral orchestration interaction",
            "formula": "(preamble+neutral - preamble) - (neutral - clean)",
            "terms": [(1.0, "baseline-preamble-orchestration"), (-1.0, "baseline-preamble-only"), (-1.0, "baseline-neutral-orchestration-only"), (1.0, "baseline")],
            "interpretation": "Negative values mean neutral orchestration looks less helpful when layered onto the preamble.",
        },
        {
            "id": "workflow_vs_preamble",
            "label": "Workflow checklist vs engineer preamble",
            "formula": "workflow - preamble",
            "terms": [(1.0, "baseline-wf-only"), (-1.0, "baseline-preamble-only")],
            "interpretation": "Direct prompt-only head-to-head on exact cells.",
        },
    ]


def eval_terms(terms: list[tuple[float, str]], cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> float:
    if not cells:
        return 0.0
    value = 0.0
    for weight, config in terms:
        value += weight * solve_count(config, cells, data) / len(cells)
    return value


def eval_cost_terms(terms: list[tuple[float, str]], cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> float:
    value = 0.0
    for weight, config in terms:
        value += weight * cost_sum(config, cells, data)
    return value


def bootstrap_contrast(terms: list[tuple[float, str]], tasks_to_cells: dict[str, list[str]], data: dict[str, dict[str, dict[str, Any]]], reps: int = BOOTSTRAP_REPS) -> dict[str, float]:
    signature = "|".join(f"{weight}:{config}" for weight, config in terms)
    stable_offset = sum((idx + 1) * ord(ch) for idx, ch in enumerate(signature)) % 100000
    rng = random.Random(BOOTSTRAP_SEED + stable_offset)
    tasks = sorted(tasks_to_cells)
    samples: list[float] = []
    for _ in range(reps):
        sampled_tasks = [rng.choice(tasks) for _ in tasks]
        cells = [cell for task in sampled_tasks for cell in tasks_to_cells[task]]
        samples.append(eval_terms(terms, cells, data))
    return {
        "reps": reps,
        "seed": BOOTSTRAP_SEED,
        "mean_rate_delta": mean(samples),
        "ci95_low_rate_delta": percentile(samples, 0.025),
        "ci95_high_rate_delta": percentile(samples, 0.975),
        "mean_solves_per_108": mean(samples) * 108,
        "ci95_low_solves_per_108": percentile(samples, 0.025) * 108,
        "ci95_high_solves_per_108": percentile(samples, 0.975) * 108,
    }


def build_effects(cells: list[str], tasks_to_cells: dict[str, list[str]], data: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    effects = []
    for spec in build_contrast_specs():
        rate = eval_terms(spec["terms"], cells, data)
        cost_delta = eval_cost_terms(spec["terms"], cells, data)
        boot = bootstrap_contrast(spec["terms"], tasks_to_cells, data)
        row = {
            **spec,
            "cells": len(cells),
            "tasks": len(tasks_to_cells),
            "rate_delta": rate,
            "solves_per_108": rate * 108,
            "cost_delta_usd": round(cost_delta, 6),
            "cost_per_net_solve_usd": round(cost_delta / (rate * len(cells)), 6) if rate > 0 else None,
            "bootstrap": boot,
        }
        effects.append(row)
    return effects


def language_for_task(task: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> str:
    counts = Counter()
    for cell in cells:
        value = data["baseline"][cell].get("language") or "unknown"
        counts[str(value)] += 1
    return counts.most_common(1)[0][0] if counts else "unknown"


def category_for_task(task: str, cells: list[str], data: dict[str, dict[str, dict[str, Any]]]) -> str:
    counts = Counter()
    for cell in cells:
        value = data["baseline"][cell].get("category") or "unknown"
        counts[str(value)] += 1
    return counts.most_common(1)[0][0] if counts else "unknown"


def task_feature_rows(tasks_to_cells: dict[str, list[str]], data: dict[str, dict[str, dict[str, Any]]], medium_data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for task, cells in tasks_to_cells.items():
        counts = {config: solve_count(config, cells, data) for config in PROMPT_CONFIGS}
        costs = {config: cost_sum(config, cells, data) for config in PROMPT_CONFIGS}
        medium_counts = sum(solved(medium_data[cell]) for cell in cells if cell in medium_data)
        clean = counts["baseline"]
        workflow = counts["baseline-wf-only"]
        preamble = counts["baseline-preamble-only"]
        combo = counts["baseline-preamble-orchestration-wf"]
        neutral = counts["baseline-neutral-orchestration-only"]
        preamble_neutral = counts["baseline-preamble-orchestration"]
        prompt_counts = {config: counts[config] for config in PROMPT_CONFIGS if config != "baseline"}
        max_prompt = max(prompt_counts.values())
        best_prompt_candidates = [config for config, value in prompt_counts.items() if value == max_prompt]
        if clean >= max_prompt:
            gate = "clean_or_no_prompt"
        else:
            best_prompt_candidates.sort(key=lambda cfg: (costs[cfg], cfg))
            gate = best_prompt_candidates[0]
        max_all = max(counts.values())
        best_all = [config for config, value in counts.items() if value == max_all]
        labels = []
        if max_all == 0:
            labels.append("all_prompt_rows_hard")
        if clean == 3:
            labels.append("clean_already_3_of_3")
        if workflow > clean:
            labels.append("workflow_gain")
        if preamble > clean:
            labels.append("preamble_gain")
        if neutral > clean:
            labels.append("neutral_gain")
        if preamble_neutral > preamble:
            labels.append("neutral_helps_preamble")
        if preamble_neutral < preamble:
            labels.append("neutral_hurts_preamble")
        if workflow > combo:
            labels.append("preamble_interferes_with_workflow")
        if combo > workflow:
            labels.append("preamble_helps_workflow")
        if workflow == max_all and len(best_all) == 1 and workflow > clean:
            labels.append("workflow_unique_best")
        if preamble == max_all and len(best_all) == 1 and preamble > clean:
            labels.append("preamble_unique_best")
        if medium_counts > clean:
            labels.append("medium_gap_positive")
        if not labels:
            labels.append("mixed_or_no_clear_prompt_signal")
        f2p_totals = [int(data["baseline"][cell].get("f2p_total") or 0) for cell in cells]
        p2p_totals = [int(data["baseline"][cell].get("p2p_total") or 0) for cell in cells]
        clean_cost = cost_sum("baseline", cells, data)
        clean_turns = sum(int(data["baseline"][cell].get("turns") or 0) for cell in cells)
        rows.append({
            "task": task,
            "cells": len(cells),
            "language": language_for_task(task, cells, data),
            "category": category_for_task(task, cells, data),
            "clean_solves": clean,
            "medium_solves": medium_counts,
            "workflow_solves": workflow,
            "preamble_solves": preamble,
            "neutral_solves": neutral,
            "preamble_neutral_solves": preamble_neutral,
            "preamble_workflow_solves": combo,
            "workflow_delta": workflow - clean,
            "preamble_delta": preamble - clean,
            "neutral_delta": neutral - clean,
            "preamble_neutral_delta": preamble_neutral - clean,
            "preamble_workflow_delta": combo - clean,
            "workflow_vs_preamble": workflow - preamble,
            "workflow_vs_preamble_workflow": workflow - combo,
            "preamble_workflow_interaction": (combo - preamble) - (workflow - clean),
            "preamble_neutral_interaction": (preamble_neutral - preamble) - (neutral - clean),
            "medium_delta": medium_counts - clean,
            "best_all_configs": best_all,
            "gate_recommendation": gate,
            "profile_labels": labels,
            "baseline_f2p_total_median": median(f2p_totals) if f2p_totals else 0,
            "baseline_p2p_total_median": median(p2p_totals) if p2p_totals else 0,
            "baseline_test_total_median": median([a + b for a, b in zip(f2p_totals, p2p_totals)]) if f2p_totals else 0,
            "baseline_cost_usd": round(clean_cost, 6),
            "baseline_turns": clean_turns,
        })
    return rows


def bin_by_quantiles(rows: list[dict[str, Any]], field: str, labels: tuple[str, str, str] = ("low", "mid", "high")) -> dict[str, str]:
    values = sorted(float(row[field]) for row in rows)
    if not values:
        return {}
    q1 = percentile(values, 1 / 3)
    q2 = percentile(values, 2 / 3)
    out = {}
    for row in rows:
        value = float(row[field])
        if value <= q1:
            out[row["task"]] = labels[0]
        elif value <= q2:
            out[row["task"]] = labels[1]
        else:
            out[row["task"]] = labels[2]
    return out


def summarize_group(name: str, value: str, tasks: list[str], tasks_to_cells: dict[str, list[str]], data: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    cells = [cell for task in tasks for cell in tasks_to_cells[task]]
    solves = {config: solve_count(config, cells, data) for config in PROMPT_CONFIGS}
    costs = {config: cost_sum(config, cells, data) for config in PROMPT_CONFIGS}
    clean = solves["baseline"]
    best_configs = sorted(PROMPT_CONFIGS, key=lambda cfg: (-solves[cfg], costs[cfg], cfg))
    best = best_configs[0]
    return {
        "group": name,
        "value": value,
        "tasks": len(tasks),
        "cells": len(cells),
        "best_config": best,
        "best_label": CONFIG_LABELS[best],
        "best_solves": solves[best],
        "clean_solves": clean,
        "best_delta_vs_clean": solves[best] - clean,
        "workflow_delta_vs_clean": solves["baseline-wf-only"] - clean,
        "preamble_delta_vs_clean": solves["baseline-preamble-only"] - clean,
        "combo_delta_vs_clean": solves["baseline-preamble-orchestration-wf"] - clean,
        "neutral_delta_vs_clean": solves["baseline-neutral-orchestration-only"] - clean,
        "cost_delta_best_vs_clean": round(costs[best] - costs["baseline"], 6),
        "confidence": "higher" if len(tasks) >= 6 and solves[best] - clean >= 2 else ("exploratory" if len(tasks) >= 3 else "thin"),
    }


def build_candidate_gates(task_rows: list[dict[str, Any]], tasks_to_cells: dict[str, list[str]], data: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    by_task = {row["task"]: row for row in task_rows}
    test_bins = bin_by_quantiles(task_rows, "baseline_test_total_median", ("small_test_surface", "mid_test_surface", "large_test_surface"))
    cost_bins = bin_by_quantiles(task_rows, "baseline_cost_usd", ("low_clean_cost", "mid_clean_cost", "high_clean_cost"))
    turn_bins = bin_by_quantiles(task_rows, "baseline_turns", ("low_clean_turns", "mid_clean_turns", "high_clean_turns"))
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in task_rows:
        task = row["task"]
        groups[("clean_solve_count", str(row["clean_solves"]))].append(task)
        groups[("language", row["language"])].append(task)
        groups[("category", row["category"])].append(task)
        groups[("test_surface", test_bins[task])].append(task)
        groups[("clean_cost", cost_bins[task])].append(task)
        groups[("clean_turns", turn_bins[task])].append(task)
        for label in row["profile_labels"]:
            groups[("profile_label", label)].append(task)
    summaries = []
    for (name, value), tasks in sorted(groups.items()):
        summaries.append(summarize_group(name, value, sorted(tasks), tasks_to_cells, data))
    candidate_rules = [row for row in summaries if row["tasks"] >= 3 and row["best_delta_vs_clean"] != 0]
    candidate_rules.sort(key=lambda row: (row["confidence"] != "higher", -abs(row["best_delta_vs_clean"]), -row["tasks"], row["group"], row["value"]))
    label_counts = Counter(label for row in task_rows for label in row["profile_labels"])
    gate_counts = Counter(row["gate_recommendation"] for row in task_rows)
    return {
        "bin_assignments": {
            "test_surface": test_bins,
            "clean_cost": cost_bins,
            "clean_turns": turn_bins,
        },
        "profile_label_counts": dict(label_counts.most_common()),
        "gate_recommendation_counts": dict(gate_counts.most_common()),
        "group_summaries": summaries,
        "candidate_rules": candidate_rules[:24],
        "caveat": "Candidate gates are post-hoc descriptive rules over the existing 36 tasks; they should guide future validation, not be treated as an already validated router.",
    }


def metric_vector(tasks: list[str], task_rows_by_task: dict[str, dict[str, Any]]) -> dict[str, float]:
    if not tasks:
        return {}
    cells = 3 * len(tasks)
    totals = Counter()
    languages = Counter()
    labels = Counter()
    categories = Counter()
    for task in tasks:
        row = task_rows_by_task[task]
        languages[row["language"]] += 1
        categories[row["category"]] += 1
        for label in row["profile_labels"]:
            labels[label] += 1
        for key in [
            "clean_solves",
            "medium_solves",
            "workflow_solves",
            "preamble_solves",
            "neutral_solves",
            "preamble_neutral_solves",
            "preamble_workflow_solves",
        ]:
            totals[key] += row[key]
    out = {
        "tasks": float(len(tasks)),
        "cells": float(cells),
        "clean_rate": totals["clean_solves"] / cells,
        "medium_rate": totals["medium_solves"] / cells,
        "medium_gap_rate": (totals["medium_solves"] - totals["clean_solves"]) / cells,
        "workflow_delta_rate": (totals["workflow_solves"] - totals["clean_solves"]) / cells,
        "preamble_delta_rate": (totals["preamble_solves"] - totals["clean_solves"]) / cells,
        "neutral_delta_rate": (totals["neutral_solves"] - totals["clean_solves"]) / cells,
        "preamble_workflow_delta_rate": (totals["preamble_workflow_solves"] - totals["clean_solves"]) / cells,
        "workflow_vs_preamble_rate": (totals["workflow_solves"] - totals["preamble_solves"]) / cells,
        "workflow_vs_combo_rate": (totals["workflow_solves"] - totals["preamble_workflow_solves"]) / cells,
    }
    for lang, count in languages.items():
        out[f"language:{lang}"] = count / len(tasks)
    for cat, count in categories.items():
        out[f"category:{cat}"] = count / len(tasks)
    for label, count in labels.items():
        out[f"profile:{label}"] = count / len(tasks)
    return out


def subset_score(tasks: list[str], full_vector: dict[str, float], task_rows_by_task: dict[str, dict[str, Any]]) -> float:
    vec = metric_vector(tasks, task_rows_by_task)
    weights = {
        "clean_rate": 6.0,
        "medium_rate": 5.0,
        "medium_gap_rate": 6.0,
        "workflow_delta_rate": 8.0,
        "preamble_delta_rate": 6.0,
        "workflow_vs_preamble_rate": 8.0,
        "workflow_vs_combo_rate": 7.0,
        "neutral_delta_rate": 3.0,
        "preamble_workflow_delta_rate": 4.0,
    }
    score = 0.0
    for key, weight in weights.items():
        score += weight * abs(vec.get(key, 0.0) - full_vector.get(key, 0.0))
    all_keys = set(full_vector) | set(vec)
    for key in all_keys:
        if key.startswith("language:"):
            score += 1.5 * abs(vec.get(key, 0.0) - full_vector.get(key, 0.0))
        elif key.startswith("profile:"):
            score += 0.8 * abs(vec.get(key, 0.0) - full_vector.get(key, 0.0))
        elif key.startswith("category:"):
            score += 0.6 * abs(vec.get(key, 0.0) - full_vector.get(key, 0.0))
    # Preserve headline ranking where possible: medium > workflow >= preamble > clean and workflow > combo.
    if vec.get("medium_gap_rate", 0) <= 0:
        score += 4.0
    if vec.get("workflow_delta_rate", 0) < vec.get("preamble_delta_rate", 0):
        score += 2.5
    if vec.get("workflow_vs_combo_rate", 0) <= 0:
        score += 1.5
    return score


def optimize_subset(size: int, task_rows: list[dict[str, Any]], full_vector: dict[str, float]) -> dict[str, Any]:
    rng = random.Random(PILOT_SEED + size)
    tasks = sorted(row["task"] for row in task_rows)
    by_task = {row["task"]: row for row in task_rows}
    best_tasks: list[str] | None = None
    best_score = float("inf")
    # Greedy seed.
    current: list[str] = []
    remaining = set(tasks)
    while len(current) < size:
        candidates = sorted(remaining, key=lambda t: subset_score(current + [t], full_vector, by_task))
        current.append(candidates[0])
        remaining.remove(candidates[0])
    best_tasks = sorted(current)
    best_score = subset_score(best_tasks, full_vector, by_task)
    # Random restarts plus local swaps.
    restarts = 1800 if size <= 12 else 1200
    for _ in range(restarts):
        current = sorted(rng.sample(tasks, size))
        improved = True
        while improved:
            improved = False
            current_set = set(current)
            outsiders = [task for task in tasks if task not in current_set]
            local_best = subset_score(current, full_vector, by_task)
            local_choice = None
            for old in current:
                for new in outsiders:
                    candidate = sorted((current_set - {old}) | {new})
                    s = subset_score(candidate, full_vector, by_task)
                    if s + 1e-12 < local_best:
                        local_best = s
                        local_choice = candidate
            if local_choice is not None:
                current = local_choice
                improved = True
        s = subset_score(current, full_vector, by_task)
        if s < best_score:
            best_score = s
            best_tasks = current
    assert best_tasks is not None
    return {
        "size": size,
        "score": round(best_score, 6),
        "tasks": best_tasks,
        "metrics": metric_vector(best_tasks, by_task),
    }


def build_pilot_selection(task_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_task = {row["task"]: row for row in task_rows}
    all_tasks = sorted(by_task)
    full_vector = metric_vector(all_tasks, by_task)
    selections = [optimize_subset(size, task_rows, full_vector) for size in PILOT_SIZES]
    primary = next(sel for sel in selections if sel["size"] == PRIMARY_PILOT_SIZE)
    return {
        "method": "Deterministic local-search subset selection minimizes distance to the full 36-task metric vector: clean low rate, clean medium rate and gap, prompt deltas/rankings, workflow-vs-combo discordance, language/category/profile distribution.",
        "seed": PILOT_SEED,
        "full_metrics": full_vector,
        "selections": selections,
        "primary_size": PRIMARY_PILOT_SIZE,
        "primary": primary,
        "primary_task_rows": [by_task[task] for task in primary["tasks"]],
    }


def write_csvs(effects: list[dict[str, Any]], task_rows: list[dict[str, Any]], pilot: dict[str, Any]) -> None:
    with OUT_EFFECTS_CSV.open("w", newline="") as f:
        fields = ["id", "label", "formula", "solves_per_108", "rate_delta", "ci95_low_solves_per_108", "ci95_high_solves_per_108", "cost_delta_usd", "cost_per_net_solve_usd", "interpretation"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for effect in effects:
            writer.writerow({
                "id": effect["id"],
                "label": effect["label"],
                "formula": effect["formula"],
                "solves_per_108": round(effect["solves_per_108"], 6),
                "rate_delta": round(effect["rate_delta"], 9),
                "ci95_low_solves_per_108": round(effect["bootstrap"]["ci95_low_solves_per_108"], 6),
                "ci95_high_solves_per_108": round(effect["bootstrap"]["ci95_high_solves_per_108"], 6),
                "cost_delta_usd": effect["cost_delta_usd"],
                "cost_per_net_solve_usd": effect["cost_per_net_solve_usd"],
                "interpretation": effect["interpretation"],
            })
    with OUT_PROFILES_CSV.open("w", newline="") as f:
        fields = ["task", "language", "category", "clean_solves", "medium_solves", "workflow_solves", "preamble_solves", "neutral_solves", "preamble_neutral_solves", "preamble_workflow_solves", "workflow_delta", "preamble_delta", "workflow_vs_preamble", "workflow_vs_preamble_workflow", "preamble_workflow_interaction", "gate_recommendation", "profile_labels"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in task_rows:
            writer.writerow({**{k: row[k] for k in fields if k != "profile_labels"}, "profile_labels": ";".join(row["profile_labels"])})
    with OUT_PILOT_CSV.open("w", newline="") as f:
        fields = ["task", "language", "category", "clean_solves", "medium_solves", "workflow_solves", "preamble_solves", "preamble_workflow_solves", "workflow_delta", "preamble_delta", "gate_recommendation", "profile_labels"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in pilot["primary_task_rows"]:
            writer.writerow({**{k: row[k] for k in fields if k != "profile_labels"}, "profile_labels": ";".join(row["profile_labels"])})


def bar_svg(effects: list[dict[str, Any]]) -> str:
    rows = effects[:]
    width = 860
    row_h = 34
    left = 300
    mid = 470
    max_abs = max(abs(row["bootstrap"]["ci95_low_solves_per_108"]) for row in rows)
    max_abs = max(max_abs, max(abs(row["bootstrap"]["ci95_high_solves_per_108"]) for row in rows), 1)
    scale = 330 / max_abs
    height = 36 + row_h * len(rows)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Bootstrap contrast chart">']
    parts.append(f'<line x1="{mid}" x2="{mid}" y1="18" y2="{height-10}" stroke="#54708f" stroke-width="1"/>')
    for i, row in enumerate(rows):
        y = 30 + i * row_h
        val = row["solves_per_108"]
        lo = row["bootstrap"]["ci95_low_solves_per_108"]
        hi = row["bootstrap"]["ci95_high_solves_per_108"]
        x0 = mid + min(0, val) * scale
        w = abs(val) * scale
        color = "#34d399" if val >= 0 else "#fb7185"
        ci_x1 = mid + lo * scale
        ci_x2 = mid + hi * scale
        parts.append(f'<text x="12" y="{y+5}" fill="#dbeafe" font-size="12">{e(row["label"])}</text>')
        parts.append(f'<line x1="{ci_x1:.1f}" x2="{ci_x2:.1f}" y1="{y}" y2="{y}" stroke="#9fb0c9" stroke-width="2"/>')
        parts.append(f'<rect x="{x0:.1f}" y="{y-8}" width="{max(w,1):.1f}" height="16" fill="{color}" opacity="0.82" rx="4"/>')
        parts.append(f'<text x="{mid + val * scale + (8 if val >= 0 else -8):.1f}" y="{y+5}" text-anchor="{"start" if val >= 0 else "end"}" fill="#eef5ff" font-size="12">{val:+.1f}</text>')
    parts.append('</svg>')
    return "".join(parts)


def stat_card(value: str, label: str) -> str:
    return f'<div class="stat"><b>{e(value)}</b><span>{e(label)}</span></div>'


def effects_table(effects: list[dict[str, Any]]) -> str:
    rows = []
    for effect in effects:
        boot = effect["bootstrap"]
        klass = "good" if effect["solves_per_108"] > 0 else ("bad" if effect["solves_per_108"] < 0 else "neutral")
        rows.append(f'''<tr><td><b>{e(effect['label'])}</b><div class="muted"><code>{e(effect['formula'])}</code></div></td><td><span class="tag {klass}">{effect['solves_per_108']:+.1f} solves / 108</span></td><td>{boot['ci95_low_solves_per_108']:+.1f} to {boot['ci95_high_solves_per_108']:+.1f}</td><td>{money(effect['cost_delta_usd'])}</td><td>{money(effect['cost_per_net_solve_usd']) if effect['cost_per_net_solve_usd'] is not None else '—'}</td><td>{e(effect['interpretation'])}</td></tr>''')
    return "".join(rows)


def profile_table(task_rows: list[dict[str, Any]], limit: int = 18) -> str:
    ordered = sorted(task_rows, key=lambda row: (-abs(row["preamble_workflow_interaction"]), -abs(row["workflow_delta"]), row["task"]))[:limit]
    rows = []
    for row in ordered:
        rows.append(f'''<tr><td><code>{e(row['task'])}</code><div class="muted">{e(row['language'])} · {e(row['category'])}</div></td><td>{row['clean_solves']} / {row['workflow_solves']} / {row['preamble_solves']} / {row['preamble_workflow_solves']}</td><td>{row['workflow_delta']:+d}</td><td>{row['preamble_delta']:+d}</td><td>{row['preamble_workflow_interaction']:+d}</td><td><span class="tag neutral">{e(CONFIG_LABELS.get(row['gate_recommendation'], row['gate_recommendation']))}</span></td><td>{', '.join(e(x) for x in row['profile_labels'][:4])}</td></tr>''')
    return "".join(rows)


def gate_table(gates: dict[str, Any]) -> str:
    rows = []
    for row in gates["candidate_rules"][:16]:
        klass = "good" if row["best_delta_vs_clean"] > 0 else "bad"
        rows.append(f'''<tr><td><b>{e(row['group'])}</b><div class="muted">{e(row['value'])}</div></td><td>{row['tasks']} tasks / {row['cells']} cells</td><td><span class="tag {klass}">{e(row['best_label'])}</span></td><td>{row['best_solves']} vs {row['clean_solves']} clean</td><td>{row['best_delta_vs_clean']:+d}</td><td>{row['workflow_delta_vs_clean']:+d}</td><td>{row['preamble_delta_vs_clean']:+d}</td><td>{money(row['cost_delta_best_vs_clean'])}</td><td>{e(row['confidence'])}</td></tr>''')
    return "".join(rows)


def pilot_table(pilot: dict[str, Any]) -> str:
    rows = []
    for row in pilot["primary_task_rows"]:
        rows.append(f'''<tr><td><code>{e(row['task'])}</code></td><td>{e(row['language'])}</td><td>{row['clean_solves']}</td><td>{row['medium_solves']}</td><td>{row['workflow_solves']}</td><td>{row['preamble_solves']}</td><td>{row['preamble_workflow_solves']}</td><td>{e(CONFIG_LABELS.get(row['gate_recommendation'], row['gate_recommendation']))}</td></tr>''')
    return "".join(rows)


def pilot_metric_table(pilot: dict[str, Any]) -> str:
    keys = [
        ("clean_rate", "Clean low solve rate"),
        ("medium_rate", "Clean medium solve rate"),
        ("medium_gap_rate", "Medium gap"),
        ("workflow_delta_rate", "Workflow delta"),
        ("preamble_delta_rate", "Preamble delta"),
        ("workflow_vs_preamble_rate", "Workflow vs preamble"),
        ("workflow_vs_combo_rate", "Workflow vs preamble+workflow"),
    ]
    full = pilot["full_metrics"]
    primary = pilot["primary"]["metrics"]
    rows = []
    for key, label in keys:
        rows.append(f'''<tr><td>{e(label)}</td><td>{full.get(key, 0)*100:.1f}%</td><td>{primary.get(key, 0)*100:.1f}%</td><td>{(primary.get(key, 0)-full.get(key, 0))*100:+.1f} pp</td></tr>''')
    return "".join(rows)


def render_html(data: dict[str, Any]) -> str:
    summaries = {row["config"]: row for row in data["config_summaries"]}
    effects = data["factorial_effects"]
    gates = data["conditional_gate"]
    pilot = data["pilot_selection"]
    workflow = next(row for row in effects if row["id"] == "workflow_main_without_preamble")
    interaction = next(row for row in effects if row["id"] == "preamble_workflow_interaction")
    primary = pilot["primary"]
    chart = bar_svg(effects)
    profile_counts = " ".join(f'<span class="tag neutral">{e(k)} · {v}</span>' for k, v in list(gates["profile_label_counts"].items())[:10])
    manifest_list = "".join(f'<li><code>{e(path)}</code></li>' for path in data["inputs"]["manifests"])
    output_list = "".join(f'<li><code>{e(path)}</code></li>' for path in data["outputs"].values())
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GPT-5.5 low no-ablation prompt analysis</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 8% 0%,#173c54,#07111f 45%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}main{{max-width:1360px;margin:0 auto;padding:36px 22px 66px}}.hero,.card,.callout{{background:rgba(15,29,49,.91);border:1px solid var(--line);border-radius:24px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.25)}}.hero{{padding:34px;background:linear-gradient(135deg,rgba(52,211,153,.18),rgba(15,29,49,.94) 43%,rgba(96,165,250,.11))}}.kicker{{color:var(--green);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:900}}h1{{font-size:clamp(34px,5.8vw,72px);line-height:.92;letter-spacing:-.06em;margin:12px 0 16px}}h2{{margin:34px 0 12px;font-size:27px;letter-spacing:-.02em}}h3{{margin:18px 0 8px}}p,li{{color:#dbe7fb;max-width:1080px}}.pills{{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:850;border:1px solid var(--line);background:#0b1728;color:var(--muted);white-space:nowrap;margin:1px}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:32px;line-height:1;letter-spacing:-.04em}}.stat span,.muted,.src{{color:var(--muted);font-size:12px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68);margin-bottom:22px}}th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}code,pre{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px}}code{{padding:1px 5px;font-size:12px}}pre{{white-space:pre-wrap;padding:12px;overflow:auto}}svg{{width:100%;height:auto;background:rgba(9,18,32,.45);border:1px solid var(--line);border-radius:18px;padding:10px}}.section-note{{color:#dbe7fb;border-left:4px solid var(--blue);padding-left:14px}}@media(max-width:900px){{.stats,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">No-new-ablation analysis · GPT-5.5 low · prompt-shaped configs</div><h1>Existing cells already isolate the next prompt questions.</h1><p>This report applies Kaggle-style lessons after the deeper audit: use paired cells, hard-negative prompt neighbors, post-hoc gates, and validation-subset matching. No benchmark ablations were launched and no config prompt files were written.</p><div class="pills"><span class="pill good">factorial contrasts + task bootstrap</span><span class="pill neutral">response profiles + conditional gates</span><span class="pill neutral">representative 12-task pilot subset</span><span class="pill caution">prompt-only claims only</span></div><p class="src">Primary inputs: <code>results/gpt-5.5/low/</code>, <code>results/gpt-5.5/medium/baseline/</code>, existing prompt audit JSON, and manifests listed below.</p></section>
<div class="stats">{stat_card(f'{summaries['baseline-wf-only']['solves'] - summaries['baseline']['solves']:+d}', 'workflow checklist solves vs clean low')}{stat_card(f'{summaries['baseline-preamble-only']['solves'] - summaries['baseline']['solves']:+d}', 'engineer preamble solves vs clean low')}{stat_card(f'{interaction['solves_per_108']:+.1f}', 'preamble × workflow interaction, solves / 108')}{stat_card(f'{primary['size']}', 'tasks in recommended pilot subset')}</div>
<section class="callout good"><h2>Verdict</h2><p>The useful no-ablation signal is an <b>interaction</b>, not a new cluster: the workflow checklist adds {workflow['solves_per_108']:+.1f} solves per 108 without the preamble, but the preamble×workflow contrast is {interaction['solves_per_108']:+.1f} solves per 108. That supports testing checklist structure later, but the current work here is to quantify the pattern, identify where it happens, and choose a cheaper representative pilot subset.</p></section>
<h2>Prompt factorial + interaction bootstrap</h2><p class="section-note">Contrasts are paired on the same 108 task/rep cells and bootstrapped by resampling the 36 tasks with replacement ({BOOTSTRAP_REPS:,} reps, deterministic seed). Because the design lacks workflow+neutral and preamble+workflow+neutral cells, workflow×neutral terms are explicitly not estimated.</p>{chart}<table><thead><tr><th>Effect</th><th>Point estimate</th><th>Task-bootstrap 95% CI</th><th>Cost contrast</th><th>Cost/net solve</th><th>Meaning</th></tr></thead><tbody>{effects_table(effects)}</tbody></table>
<div class="grid"><section class="card"><h2>Prompt row summaries</h2><table><thead><tr><th>Config</th><th>Solves</th><th>Cost</th><th>Invalid rewards</th><th>Prompt chars</th></tr></thead><tbody>{''.join(f'<tr><td><code>{e(row["config"])}</code><div class="muted">{e(row["label"])}</div></td><td>{row["solves"]}/{row["cells"]}</td><td>{money(row["total_cost_usd"])}</td><td>{row["invalid_reward_cells"]}</td><td>preamble {row["system_preamble_chars"]}, orchestration {row["orchestration_chars"]}</td></tr>' for row in data['config_summaries'])}</tbody></table></section><section class="callout caution"><h2>Identifiability caveat</h2><p>This is an incomplete factorial. The report estimates the contrasts the historical runs support: workflow without preamble, preamble without workflow, neutral without preamble, preamble×workflow, and preamble×neutral. It does not infer unrun cells.</p></section></div>
<h2>Task response profiles and conditional gates</h2><p class="section-note">These gates are descriptive, post-hoc, and intended to prioritize future validation. They do not prove a deployable router.</p><div class="card"><h3>Profile label distribution</h3><p>{profile_counts}</p></div><table><thead><tr><th>Candidate condition</th><th>Coverage</th><th>Best row</th><th>Best vs clean</th><th>Δ solves</th><th>Workflow Δ</th><th>Preamble Δ</th><th>Cost Δ</th><th>Confidence</th></tr></thead><tbody>{gate_table(gates)}</tbody></table>
<h3>Highest-interaction task profiles</h3><table><thead><tr><th>Task</th><th>Clean / workflow / preamble / preamble+workflow solves</th><th>Workflow Δ</th><th>Preamble Δ</th><th>Interaction</th><th>Gate recommendation</th><th>Labels</th></tr></thead><tbody>{profile_table(data['task_profiles'])}</tbody></table>
<h2>Representative pilot subset selection</h2><p class="section-note">The primary subset has {primary['size']} tasks. It was selected by deterministic local search to preserve the full-set clean-low rate, clean-medium gap, workflow-vs-preamble ranking, workflow-vs-combo discordance, language/category mix, and response-profile mix.</p><div class="grid"><section class="card"><h3>Full set vs primary pilot metrics</h3><table><thead><tr><th>Metric</th><th>Full 36 tasks</th><th>Primary 12 tasks</th><th>Difference</th></tr></thead><tbody>{pilot_metric_table(pilot)}</tbody></table></section><section class="card"><h3>Alternate subset sizes</h3><table><thead><tr><th>Size</th><th>Score</th><th>Clean rate</th><th>Workflow Δ</th><th>Preamble Δ</th></tr></thead><tbody>{''.join(f'<tr><td>{sel["size"]}</td><td>{sel["score"]:.3f}</td><td>{sel["metrics"].get("clean_rate",0)*100:.1f}%</td><td>{sel["metrics"].get("workflow_delta_rate",0)*100:+.1f} pp</td><td>{sel["metrics"].get("preamble_delta_rate",0)*100:+.1f} pp</td></tr>' for sel in pilot['selections'])}</tbody></table></section></div><table><thead><tr><th>Task</th><th>Language</th><th>Clean</th><th>Medium</th><th>Workflow</th><th>Preamble</th><th>Preamble+workflow</th><th>Gate</th></tr></thead><tbody>{pilot_table(pilot)}</tbody></table>
<section class="callout neutral"><h2>Kaggle techniques transferred</h2><ul><li><b>Hard negatives:</b> semantically close prompt rows with divergent outcomes become targeted contrasts, especially workflow vs preamble+workflow.</li><li><b>Cluster-conditioned wins/losses:</b> profiles and gates summarize where each prompt shape helps or hurts rather than trusting aggregate solve deltas.</li><li><b>Validation matching:</b> the pilot subset is chosen to match full-set outcome structure before spending on future ablations.</li><li><b>Metric parity:</b> all solves use <code>reward_binary == 1</code>, exact task/rep overlap, and combined cost fields.</li></ul></section>
<section class="callout"><h2>Evidence and generated artifacts</h2><p>Manifests / run sources:</p><ul>{manifest_list}</ul><p>Generated outputs:</p><ul>{output_list}</ul><p>Sample result paths are stored in the JSON under each config summary. Behavioral wrappers, OMP/tool-surface configs, and contaminated results are not used for prompt-only conclusions.</p></section>
</main></body></html>'''


def build() -> dict[str, Any]:
    cells_by_config = {config: read_config_cells(LOW_ROOT, config) for config in PROMPT_CONFIGS}
    medium_cells = read_config_cells(MEDIUM_ROOT, MEDIUM_CONFIG)
    cells = common_cells(cells_by_config)
    medium_overlap = sorted(set(cells) & set(medium_cells))
    if len(cells) != 108:
        raise RuntimeError(f"expected 108 common low prompt cells, got {len(cells)}")
    if len(medium_overlap) != 108:
        raise RuntimeError(f"expected 108 medium overlap cells, got {len(medium_overlap)}")
    tasks_to_cells = task_cells(cells)
    config_summaries = [aggregate_config(config, cells, cells_by_config) for config in PROMPT_CONFIGS]
    medium_summary = aggregate_config(MEDIUM_CONFIG, medium_overlap, {MEDIUM_CONFIG: medium_cells})
    medium_summary["config"] = "medium:baseline"
    medium_summary["label"] = CONFIG_LABELS["medium:baseline"]
    effects = build_effects(cells, tasks_to_cells, cells_by_config)
    profiles = task_feature_rows(tasks_to_cells, cells_by_config, medium_cells)
    gates = build_candidate_gates(profiles, tasks_to_cells, cells_by_config)
    pilot = build_pilot_selection(profiles)
    pairwise = {
        "workflow_vs_clean": pair_counts("baseline", "baseline-wf-only", cells, cells_by_config),
        "preamble_vs_clean": pair_counts("baseline", "baseline-preamble-only", cells, cells_by_config),
        "workflow_vs_preamble_workflow": pair_counts("baseline-preamble-orchestration-wf", "baseline-wf-only", cells, cells_by_config),
        "medium_vs_clean_low": {
            "both": sum(1 for cell in cells if solved(cells_by_config["baseline"][cell]) and solved(medium_cells[cell])),
            "low_only": sum(1 for cell in cells if solved(cells_by_config["baseline"][cell]) and not solved(medium_cells[cell])),
            "medium_only": sum(1 for cell in cells if not solved(cells_by_config["baseline"][cell]) and solved(medium_cells[cell])),
            "neither": sum(1 for cell in cells if not solved(cells_by_config["baseline"][cell]) and not solved(medium_cells[cell])),
        },
    }
    data = {
        "inputs": {
            "low_result_root": str(LOW_ROOT.relative_to(ROOT)),
            "medium_result_root": str((MEDIUM_ROOT / MEDIUM_CONFIG).relative_to(ROOT)),
            "common_low_cells": len(cells),
            "common_tasks": len(tasks_to_cells),
            "prompt_configs": PROMPT_CONFIGS,
            "manifests": [path for path in MANIFESTS if (ROOT / path).exists()],
            "existing_context_artifacts": [
                "analysis/gpt55-low-historical-corpus/prompt_discordant_audit.json",
                "analysis/gpt55-low-historical-corpus/prompt_shaped_neighbor_divergence.json",
                "analysis/gpt55-low-historical-corpus/kaggle_plugin_prompt_lessons.json",
            ],
        },
        "outputs": {
            "json": str(OUT_JSON.relative_to(ROOT)),
            "effects_csv": str(OUT_EFFECTS_CSV.relative_to(ROOT)),
            "task_profiles_csv": str(OUT_PROFILES_CSV.relative_to(ROOT)),
            "pilot_subset_csv": str(OUT_PILOT_CSV.relative_to(ROOT)),
            "html": str(OUT_HTML.relative_to(ROOT)),
        },
        "method_notes": {
            "solve_rule": "A cell is solved only when reward_binary == 1; negative or invalid reward values are counted as unsolved and tracked as invalid_reward_cells.",
            "cost_rule": "Use combined_cost_usd and combined_total_tokens when present; fall back to cost_usd and total_tokens.",
            "pairing_rule": "All prompt-only contrasts use exact task/rep cells in the 108-cell intersection across the six clean-Pi prompt configs.",
            "excluded_scope": "No OMP/tool-surface rows, behavioral wrappers, or results/_contaminated artifacts are used for prompt-only conclusions.",
            "bootstrap_rule": f"Bootstrap resamples the 36 tasks with replacement for {BOOTSTRAP_REPS} deterministic reps.",
        },
        "factors": FACTORS,
        "config_summaries": config_summaries + [medium_summary],
        "factorial_effects": effects,
        "pairwise": pairwise,
        "task_profiles": profiles,
        "conditional_gate": gates,
        "pilot_selection": pilot,
    }
    return data


def main() -> None:
    data = build()
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_csvs(data["factorial_effects"], data["task_profiles"], data["pilot_selection"])
    OUT_JSON.write_text(json.dumps(data, indent=2))
    OUT_HTML.write_text(render_html(data))
    print("wrote", OUT_JSON.relative_to(ROOT), OUT_JSON.stat().st_size)
    print("wrote", OUT_EFFECTS_CSV.relative_to(ROOT), OUT_EFFECTS_CSV.stat().st_size)
    print("wrote", OUT_PROFILES_CSV.relative_to(ROOT), OUT_PROFILES_CSV.stat().st_size)
    print("wrote", OUT_PILOT_CSV.relative_to(ROOT), OUT_PILOT_CSV.stat().st_size)
    print("wrote", OUT_HTML.relative_to(ROOT), OUT_HTML.stat().st_size)


if __name__ == "__main__":
    main()
