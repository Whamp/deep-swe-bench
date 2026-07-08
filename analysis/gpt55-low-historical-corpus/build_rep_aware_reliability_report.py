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
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "analysis/gpt55-low-historical-corpus"
REPORT_DIR = ROOT / "reports/gpt55-low-rep-aware-reliability"
LOW_ROOT = ROOT / "results/gpt-5.5/low"

OUT_JSON = ANALYSIS_DIR / "rep_aware_prompt_reliability.json"
OUT_TRANSITIONS_CSV = ANALYSIS_DIR / "rep_aware_transition_matrices.csv"
OUT_DECOMP_CSV = ANALYSIS_DIR / "rep_aware_decomposition.csv"
OUT_UNCERTAINTY_CSV = ANALYSIS_DIR / "rep_aware_task_bootstrap_uncertainty.csv"
OUT_RERUN_CSV = ANALYSIS_DIR / "rep_aware_rerun_economics.csv"
OUT_TASKS_CSV = ANALYSIS_DIR / "rep_aware_task_profiles.csv"
OUT_PILOT_CSV = ANALYSIS_DIR / "rep_aware_pilot_subset_12.csv"
OUT_HTML = REPORT_DIR / "index.html"

PROMPT_CONFIGS = [
    "baseline",
    "baseline-neutral-orchestration-only",
    "baseline-preamble-only",
    "baseline-preamble-orchestration",
    "baseline-wf-only",
    "baseline-preamble-orchestration-wf",
]
PROMPT_ONLY_CONFIGS = [config for config in PROMPT_CONFIGS if config != "baseline"]
CONFIG_LABELS = {
    "baseline": "Clean low",
    "baseline-neutral-orchestration-only": "Neutral orchestration",
    "baseline-preamble-only": "Engineer preamble",
    "baseline-preamble-orchestration": "Preamble + neutral orchestration",
    "baseline-wf-only": "Workflow checklist",
    "baseline-preamble-orchestration-wf": "Preamble + workflow checklist",
}

BOOTSTRAP_REPS = 5000
BOOTSTRAP_SEED = 20260709
PILOT_SEED = 20260710
PILOT_SIZES = [6, 9, 12, 18]
PRIMARY_PILOT_SIZE = 12

MANIFESTS = [
    "results/_runs/gpt55-low-clean-baseline-36v2-r3-w24/manifest.json",
    "results/_runs/gpt55-low-prompt-ablation-36v2-r3-w24-v2/manifest.json",
]

ROLLUP_KEYS = [
    "new_reach",
    "reliability_improvement",
    "robust_improvement",
    "unchanged",
    "variance_lottery_ticket_change",
    "regression",
]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def money(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.{digits}f}"


def pct(value: float | None, digits: int = 1) -> str:
    return "—" if value is None else f"{value * 100:.{digits}f}%"


def solved(row: dict[str, Any]) -> int:
    return 1 if row.get("reward_binary") == 1 else 0


def invalid_reward(row: dict[str, Any]) -> bool:
    return row.get("reward_binary") not in (0, 1, False, True)


def result_cost(row: dict[str, Any]) -> float:
    return float(row.get("combined_cost_usd", row.get("cost_usd", 0.0)) or 0.0)


def result_tokens(row: dict[str, Any]) -> int:
    return int(row.get("combined_total_tokens", row.get("total_tokens", 0)) or 0)


def percentile(values: list[float], p: float) -> float:
    xs = sorted(values)
    if not xs:
        return float("nan")
    if len(xs) == 1:
        return xs[0]
    idx = (len(xs) - 1) * p
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return xs[lo]
    weight = idx - lo
    return xs[lo] * (1 - weight) + xs[hi] * weight


def cell_key(result_path: Path) -> tuple[str, str]:
    return result_path.parts[-3], result_path.parts[-2]


def read_config_rows(config: str) -> dict[str, dict[str, dict[str, Any]]]:
    by_task: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for result_path in sorted((LOW_ROOT / config).glob("*/rep*/result.json")):
        task, rep = cell_key(result_path)
        row = load_json(result_path)
        row["_result_path"] = str(result_path.relative_to(ROOT))
        row["_task"] = task
        row["_rep"] = rep
        by_task[task][rep] = row
    return {task: dict(reps) for task, reps in by_task.items()}


def common_complete_tasks(rows_by_config: dict[str, dict[str, dict[str, dict[str, Any]]]]) -> list[str]:
    task_sets = [set(rows_by_config[config]) for config in PROMPT_CONFIGS]
    tasks = sorted(set.intersection(*task_sets))
    complete = []
    for task in tasks:
        ok = True
        for config in PROMPT_CONFIGS:
            reps = rows_by_config[config][task]
            if sorted(reps) != ["rep0", "rep1", "rep2"]:
                ok = False
                break
        if ok:
            complete.append(task)
    return complete


def task_language(task: str, rows_by_config: dict[str, dict[str, dict[str, dict[str, Any]]]]) -> str:
    counts = Counter(str(row.get("language") or "unknown") for row in rows_by_config["baseline"][task].values())
    return counts.most_common(1)[0][0] if counts else "unknown"


def task_category(task: str, rows_by_config: dict[str, dict[str, dict[str, dict[str, Any]]]]) -> str:
    counts = Counter(str(row.get("category") or "unknown") for row in rows_by_config["baseline"][task].values())
    return counts.most_common(1)[0][0] if counts else "unknown"


def config_task_summary(config: str, task: str, rows_by_config: dict[str, dict[str, dict[str, dict[str, Any]]]]) -> dict[str, Any]:
    reps = rows_by_config[config][task]
    rep_rows = [reps[f"rep{i}"] for i in range(3)]
    k = sum(solved(row) for row in rep_rows)
    invalid = sum(1 for row in rep_rows if invalid_reward(row))
    costs = [result_cost(row) for row in rep_rows]
    tokens = [result_tokens(row) for row in rep_rows]
    return {
        "config": config,
        "task": task,
        "k": k,
        "n": 3,
        "p_hat": k / 3,
        "solved_reps": [f"rep{i}" for i, row in enumerate(rep_rows) if solved(row)],
        "invalid_reward_reps": [f"rep{i}" for i, row in enumerate(rep_rows) if invalid_reward(row)],
        "invalid_reward_count": invalid,
        "total_cost_usd": sum(costs),
        "mean_attempt_cost_usd": mean(costs),
        "median_attempt_cost_usd": median(costs),
        "total_tokens": sum(tokens),
        "mean_attempt_tokens": mean(tokens),
        "result_paths": [row["_result_path"] for row in rep_rows],
    }


def build_task_summaries(tasks: list[str], rows_by_config: dict[str, dict[str, dict[str, dict[str, Any]]]]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        config: {task: config_task_summary(config, task, rows_by_config) for task in tasks}
        for config in PROMPT_CONFIGS
    }


def exclusive_transition_label(clean_k: int, prompt_k: int) -> str:
    if prompt_k > clean_k:
        if clean_k == 0 and prompt_k == 1:
            return "new_reach_lottery_ticket"
        if clean_k == 0 and prompt_k >= 2:
            return "new_reach_robust"
        if prompt_k == 3 and clean_k in (1, 2):
            return "reliability_improvement_to_stable"
        return "reliability_improvement"
    if prompt_k < clean_k:
        if prompt_k == 0:
            return "regression_to_zero"
        if clean_k == 3 and prompt_k in (1, 2):
            return "regression_to_flaky"
        return "regression"
    if prompt_k == 0:
        return "unchanged_zero"
    if prompt_k == 3:
        return "unchanged_stable"
    return "unchanged_flaky"


def rollup_flags(clean_k: int, prompt_k: int) -> dict[str, bool]:
    prompt_flaky = prompt_k in (1, 2)
    clean_flaky = clean_k in (1, 2)
    return {
        "new_reach": clean_k == 0 and prompt_k > 0,
        "reliability_improvement": clean_k > 0 and prompt_k > clean_k,
        "robust_improvement": prompt_k - clean_k >= 2,
        "unchanged": prompt_k == clean_k,
        "variance_lottery_ticket_change": (clean_k == 0 and prompt_k == 1) or (prompt_flaky != clean_flaky),
        "regression": prompt_k < clean_k,
    }


def transition_matrices(tasks: list[str], summaries: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    matrices: dict[str, Any] = {}
    clean = summaries["baseline"]
    for config in PROMPT_ONLY_CONFIGS:
        matrix = {str(i): {str(j): {"count": 0, "tasks": []} for j in range(4)} for i in range(4)}
        exclusive_counts = Counter()
        rollups = Counter()
        rows = []
        for task in tasks:
            clean_k = clean[task]["k"]
            prompt_k = summaries[config][task]["k"]
            matrix[str(clean_k)][str(prompt_k)]["count"] += 1
            matrix[str(clean_k)][str(prompt_k)]["tasks"].append(task)
            exclusive = exclusive_transition_label(clean_k, prompt_k)
            exclusive_counts[exclusive] += 1
            flags = rollup_flags(clean_k, prompt_k)
            for key, value in flags.items():
                if value:
                    rollups[key] += 1
            rows.append({
                "task": task,
                "clean_k": clean_k,
                "prompt_k": prompt_k,
                "delta_k": prompt_k - clean_k,
                "exclusive_label": exclusive,
                "rollup_flags": [key for key, value in flags.items() if value],
            })
        matrices[config] = {
            "config": config,
            "label": CONFIG_LABELS[config],
            "matrix": matrix,
            "exclusive_counts": dict(exclusive_counts.most_common()),
            "rollup_counts": {key: rollups[key] for key in ROLLUP_KEYS},
            "task_transitions": rows,
            "delta_attempt_solves": sum(row["delta_k"] for row in rows),
            "delta_any_success_tasks": sum((row["prompt_k"] > 0) - (row["clean_k"] > 0) for row in rows),
            "delta_stable_success_tasks": sum((row["prompt_k"] == 3) - (row["clean_k"] == 3) for row in rows),
            "delta_flaky_tasks": sum((row["prompt_k"] in (1, 2)) - (row["clean_k"] in (1, 2)) for row in rows),
        }
    return matrices


def config_summary(config: str, tasks: list[str], summaries: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    rows = [summaries[config][task] for task in tasks]
    k_counts = Counter(row["k"] for row in rows)
    total_k = sum(row["k"] for row in rows)
    any_success = sum(1 for row in rows if row["k"] > 0)
    stable_success = sum(1 for row in rows if row["k"] == 3)
    flaky = sum(1 for row in rows if row["k"] in (1, 2))
    return {
        "config": config,
        "label": CONFIG_LABELS[config],
        "tasks": len(tasks),
        "attempt_cells": len(tasks) * 3,
        "attempt_solves": total_k,
        "attempt_solve_rate": total_k / (len(tasks) * 3),
        "any_success_tasks": any_success,
        "any_success_task_rate": any_success / len(tasks),
        "stable_3_of_3_tasks": stable_success,
        "stable_3_of_3_task_rate": stable_success / len(tasks),
        "flaky_1_or_2_of_3_tasks": flaky,
        "flaky_1_or_2_of_3_task_rate": flaky / len(tasks),
        "k_distribution": {str(k): k_counts[k] for k in range(4)},
        "invalid_reward_reps": sum(row["invalid_reward_count"] for row in rows),
        "total_cost_usd": round(sum(row["total_cost_usd"] for row in rows), 6),
        "mean_attempt_cost_usd": mean(row["mean_attempt_cost_usd"] for row in rows),
        "median_attempt_cost_usd": median(row["median_attempt_cost_usd"] for row in rows),
        "total_tokens": sum(row["total_tokens"] for row in rows),
        "sample_result_paths": [path for row in rows[:2] for path in row["result_paths"]],
    }


def effect_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": "workflow_vs_clean",
            "label": "Workflow checklist vs clean",
            "terms": [(1.0, "baseline-wf-only"), (-1.0, "baseline")],
            "meaning": "Concrete checklist effect over three-rep task distributions.",
        },
        {
            "id": "preamble_vs_clean",
            "label": "Engineer preamble vs clean",
            "terms": [(1.0, "baseline-preamble-only"), (-1.0, "baseline")],
            "meaning": "Generic engineer preamble effect over three-rep task distributions.",
        },
        {
            "id": "neutral_vs_clean",
            "label": "Neutral orchestration vs clean",
            "terms": [(1.0, "baseline-neutral-orchestration-only"), (-1.0, "baseline")],
            "meaning": "Supposedly neutral top-of-context instruction effect.",
        },
        {
            "id": "preamble_plus_workflow_vs_workflow",
            "label": "Adding preamble to workflow",
            "terms": [(1.0, "baseline-preamble-orchestration-wf"), (-1.0, "baseline-wf-only")],
            "meaning": "Whether the generic preamble helps or interferes when the checklist is already present.",
        },
        {
            "id": "workflow_given_preamble",
            "label": "Adding workflow to preamble",
            "terms": [(1.0, "baseline-preamble-orchestration-wf"), (-1.0, "baseline-preamble-only")],
            "meaning": "Whether the checklist helps when the generic preamble is already present.",
        },
        {
            "id": "preamble_workflow_interaction",
            "label": "Preamble × workflow interaction",
            "terms": [(1.0, "baseline-preamble-orchestration-wf"), (-1.0, "baseline-preamble-only"), (-1.0, "baseline-wf-only"), (1.0, "baseline")],
            "meaning": "Negative values mean the checklist and generic preamble combine worse than their separate effects imply.",
        },
        {
            "id": "preamble_neutral_interaction",
            "label": "Preamble × neutral interaction",
            "terms": [(1.0, "baseline-preamble-orchestration"), (-1.0, "baseline-preamble-only"), (-1.0, "baseline-neutral-orchestration-only"), (1.0, "baseline")],
            "meaning": "How neutral orchestration changes when layered with the preamble.",
        },
    ]


def eval_terms(terms: list[tuple[float, str]], sample_tasks: list[str], summaries: dict[str, dict[str, dict[str, Any]]], metric: str) -> float:
    value = 0.0
    for weight, config in terms:
        for task in sample_tasks:
            k = summaries[config][task]["k"]
            if metric == "attempt_solves_per_108":
                value += weight * k
            elif metric == "any_success_tasks_per_36":
                value += weight * (1 if k > 0 else 0)
            elif metric == "stable_3_of_3_tasks_per_36":
                value += weight * (1 if k == 3 else 0)
            elif metric == "flaky_1_or_2_tasks_per_36":
                value += weight * (1 if k in (1, 2) else 0)
            else:
                raise ValueError(metric)
    # Bootstrap samples always contain 36 task draws, so these are already per-108 or per-36 units.
    return value


def task_bootstrap_uncertainty(tasks: list[str], summaries: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    outputs = []
    metrics = ["attempt_solves_per_108", "any_success_tasks_per_36", "stable_3_of_3_tasks_per_36", "flaky_1_or_2_tasks_per_36"]
    for spec in effect_specs():
        signature = "|".join(f"{weight}:{config}" for weight, config in spec["terms"])
        stable_offset = sum((idx + 1) * ord(ch) for idx, ch in enumerate(signature)) % 100000
        rng = random.Random(BOOTSTRAP_SEED + stable_offset)
        samples_by_metric = {metric: [] for metric in metrics}
        for _ in range(BOOTSTRAP_REPS):
            sample_tasks = [rng.choice(tasks) for _ in tasks]
            for metric in metrics:
                samples_by_metric[metric].append(eval_terms(spec["terms"], sample_tasks, summaries, metric))
        point_by_metric = {metric: eval_terms(spec["terms"], tasks, summaries, metric) for metric in metrics}
        result = {
            "id": spec["id"],
            "label": spec["label"],
            "meaning": spec["meaning"],
            "terms": spec["terms"],
            "bootstrap_reps": BOOTSTRAP_REPS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "metrics": {},
        }
        for metric in metrics:
            values = samples_by_metric[metric]
            result["metrics"][metric] = {
                "point": point_by_metric[metric],
                "mean": mean(values),
                "ci95_low": percentile(values, 0.025),
                "ci95_high": percentile(values, 0.975),
                "probability_positive": sum(1 for value in values if value > 0) / len(values),
                "probability_negative": sum(1 for value in values if value < 0) / len(values),
            }
        outputs.append(result)
    return outputs


def rerun_economics(tasks: list[str], summaries: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for config in PROMPT_CONFIGS:
        for attempts in (1, 2, 3):
            expected_solved_tasks = 0.0
            expected_stop_cost = 0.0
            fixed_cost = 0.0
            average_prob = 0.0
            for task in tasks:
                row = summaries[config][task]
                p = row["p_hat"]
                prob_any = 1 - (1 - p) ** attempts
                expected_attempts_until_success_or_cap = sum((1 - p) ** i for i in range(attempts))
                mean_attempt_cost = row["mean_attempt_cost_usd"]
                expected_solved_tasks += prob_any
                average_prob += prob_any
                expected_stop_cost += mean_attempt_cost * expected_attempts_until_success_or_cap
                fixed_cost += mean_attempt_cost * attempts
            observed_three_rep_any = sum(1 for task in tasks if summaries[config][task]["k"] > 0)
            rows.append({
                "config": config,
                "label": CONFIG_LABELS[config],
                "attempt_cap": attempts,
                "tasks": len(tasks),
                "expected_solved_tasks": expected_solved_tasks,
                "mean_probability_at_least_one_success": average_prob / len(tasks),
                "expected_stop_on_success_cost_usd": expected_stop_cost,
                "fixed_attempt_cost_usd": fixed_cost,
                "stop_on_success_cost_per_expected_solved_task_usd": expected_stop_cost / expected_solved_tasks if expected_solved_tasks else None,
                "fixed_attempt_cost_per_expected_solved_task_usd": fixed_cost / expected_solved_tasks if expected_solved_tasks else None,
                "observed_any_success_tasks_in_existing_3_reps": observed_three_rep_any if attempts == 3 else None,
                "method": "per-task p_hat=k/3; probability at least one success after m attempts is 1-(1-p_hat)^m; stop-on-success cost uses expected attempts sum((1-p_hat)^i).",
            })
    return rows


def task_profiles(tasks: list[str], summaries: dict[str, dict[str, dict[str, Any]]], matrices: dict[str, Any], rows_by_config: dict[str, dict[str, dict[str, dict[str, Any]]]]) -> list[dict[str, Any]]:
    by_config_label = {config: {entry["task"]: entry for entry in matrices[config]["task_transitions"]} for config in PROMPT_ONLY_CONFIGS}
    rows = []
    for task in tasks:
        clean_k = summaries["baseline"][task]["k"]
        k_by_config = {config: summaries[config][task]["k"] for config in PROMPT_CONFIGS}
        best_k = max(k_by_config.values())
        best_configs = [config for config, k in k_by_config.items() if k == best_k]
        worst_k = min(k_by_config.values())
        labels = []
        if clean_k == 0:
            labels.append("clean_zero")
        elif clean_k == 3:
            labels.append("clean_stable")
        else:
            labels.append("clean_flaky")
        if any(k_by_config[config] > clean_k for config in PROMPT_ONLY_CONFIGS):
            labels.append("some_prompt_improves")
        if any(k_by_config[config] < clean_k for config in PROMPT_ONLY_CONFIGS):
            labels.append("some_prompt_regresses")
        if k_by_config["baseline-wf-only"] > clean_k:
            labels.append("workflow_improves")
        if k_by_config["baseline-preamble-only"] > clean_k:
            labels.append("preamble_improves")
        if k_by_config["baseline-wf-only"] > k_by_config["baseline-preamble-orchestration-wf"]:
            labels.append("preamble_hurts_workflow")
        if k_by_config["baseline-wf-only"] < k_by_config["baseline-preamble-orchestration-wf"]:
            labels.append("preamble_helps_workflow")
        if all(k == clean_k for k in k_by_config.values()):
            labels.append("all_rows_same_as_clean")
        if worst_k == 0 and best_k == 3:
            labels.append("full_range_across_prompts")
        row = {
            "task": task,
            "language": task_language(task, rows_by_config),
            "category": task_category(task, rows_by_config),
            "clean_k": clean_k,
            "k_by_config": k_by_config,
            "best_configs": best_configs,
            "labels": labels,
            "workflow_transition_label": by_config_label["baseline-wf-only"][task]["exclusive_label"],
            "preamble_transition_label": by_config_label["baseline-preamble-only"][task]["exclusive_label"],
            "workflow_vs_clean_delta": k_by_config["baseline-wf-only"] - clean_k,
            "preamble_vs_clean_delta": k_by_config["baseline-preamble-only"] - clean_k,
            "preamble_workflow_interaction_k": (k_by_config["baseline-preamble-orchestration-wf"] - k_by_config["baseline-preamble-only"]) - (k_by_config["baseline-wf-only"] - clean_k),
            "total_prompt_range": best_k - worst_k,
            "mean_attempt_cost_clean": summaries["baseline"][task]["mean_attempt_cost_usd"],
        }
        rows.append(row)
    return rows


def vector_for_tasks(selected_tasks: list[str], matrices: dict[str, Any], profiles_by_task: dict[str, dict[str, Any]]) -> dict[str, float]:
    n = len(selected_tasks)
    vector: dict[str, float] = {}
    if n == 0:
        return vector
    for config in PROMPT_CONFIGS:
        for k in range(4):
            vector[f"kdist:{config}:{k}"] = sum(1 for task in selected_tasks if profiles_by_task[task]["k_by_config"][config] == k) / n
        vector[f"any:{config}"] = sum(1 for task in selected_tasks if profiles_by_task[task]["k_by_config"][config] > 0) / n
        vector[f"stable:{config}"] = sum(1 for task in selected_tasks if profiles_by_task[task]["k_by_config"][config] == 3) / n
        vector[f"flaky:{config}"] = sum(1 for task in selected_tasks if profiles_by_task[task]["k_by_config"][config] in (1, 2)) / n
    for config in PROMPT_ONLY_CONFIGS:
        for clean_k in range(4):
            for prompt_k in range(4):
                vector[f"transition:{config}:{clean_k}->{prompt_k}"] = sum(
                    1 for task in selected_tasks
                    if profiles_by_task[task]["clean_k"] == clean_k and profiles_by_task[task]["k_by_config"][config] == prompt_k
                ) / n
        for key in ROLLUP_KEYS:
            vector[f"rollup:{config}:{key}"] = sum(
                1 for task in selected_tasks
                if key in by_rollup_flags(profiles_by_task[task]["clean_k"], profiles_by_task[task]["k_by_config"][config])
            ) / n
    languages = Counter(profiles_by_task[task]["language"] for task in selected_tasks)
    labels = Counter(label for task in selected_tasks for label in profiles_by_task[task]["labels"])
    for language, count in languages.items():
        vector[f"language:{language}"] = count / n
    for label, count in labels.items():
        vector[f"profile_label:{label}"] = count / n
    return vector


def by_rollup_flags(clean_k: int, prompt_k: int) -> list[str]:
    flags = rollup_flags(clean_k, prompt_k)
    return [key for key, value in flags.items() if value]


def subset_score(candidate_tasks: list[str], full_vector: dict[str, float], profiles_by_task: dict[str, dict[str, Any]]) -> float:
    vector = vector_for_tasks(candidate_tasks, {}, profiles_by_task)
    keys = set(full_vector) | set(vector)
    score = 0.0
    for key in keys:
        weight = 1.0
        if key.startswith("transition:"):
            weight = 6.0
        elif key.startswith("rollup:"):
            weight = 5.0
        elif key.startswith("kdist:"):
            weight = 4.0
        elif key.startswith("any:") or key.startswith("stable:") or key.startswith("flaky:"):
            weight = 3.0
        elif key.startswith("language:"):
            weight = 1.5
        elif key.startswith("profile_label:"):
            weight = 1.0
        score += weight * abs(vector.get(key, 0.0) - full_vector.get(key, 0.0))
    # Preserve the headline ordering if possible: workflow k total >= preamble k total and workflow > preamble+workflow.
    def total_k(config: str) -> int:
        return sum(profiles_by_task[task]["k_by_config"][config] for task in candidate_tasks)
    if total_k("baseline-wf-only") < total_k("baseline-preamble-only"):
        score += 5.0
    if total_k("baseline-wf-only") <= total_k("baseline-preamble-orchestration-wf"):
        score += 4.0
    return score


def optimize_subset(size: int, profiles: list[dict[str, Any]], full_vector: dict[str, float]) -> dict[str, Any]:
    rng = random.Random(PILOT_SEED + size)
    tasks = sorted(row["task"] for row in profiles)
    profiles_by_task = {row["task"]: row for row in profiles}
    current: list[str] = []
    remaining = set(tasks)
    while len(current) < size:
        best_next = min(remaining, key=lambda task: subset_score(sorted(current + [task]), full_vector, profiles_by_task))
        current.append(best_next)
        remaining.remove(best_next)
    best_tasks = sorted(current)
    best_score = subset_score(best_tasks, full_vector, profiles_by_task)
    restarts = 120 if size <= 12 else 80
    for _ in range(restarts):
        current = sorted(rng.sample(tasks, size))
        improved = True
        while improved:
            improved = False
            current_set = set(current)
            outsiders = [task for task in tasks if task not in current_set]
            local_score = subset_score(current, full_vector, profiles_by_task)
            local_best = current
            for old in current:
                for new in outsiders:
                    candidate = sorted((current_set - {old}) | {new})
                    score = subset_score(candidate, full_vector, profiles_by_task)
                    if score + 1e-12 < local_score:
                        local_score = score
                        local_best = candidate
            if local_best != current:
                current = local_best
                improved = True
        score = subset_score(current, full_vector, profiles_by_task)
        if score < best_score:
            best_score = score
            best_tasks = current
    vector = vector_for_tasks(best_tasks, {}, profiles_by_task)
    return {
        "size": size,
        "score": round(best_score, 6),
        "tasks": best_tasks,
        "metrics": vector,
    }


def pilot_selection(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    profiles_by_task = {row["task"]: row for row in profiles}
    all_tasks = sorted(profiles_by_task)
    full_vector = vector_for_tasks(all_tasks, {}, profiles_by_task)
    selections = [optimize_subset(size, profiles, full_vector) for size in PILOT_SIZES]
    primary = next(row for row in selections if row["size"] == PRIMARY_PILOT_SIZE)
    return {
        "method": "Deterministic local search minimizes weighted distance to the full 36-task vector of k/3 distributions, transition matrices vs clean, decomposition rollups, any/stable/flaky task rates, language mix, and profile labels.",
        "seed": PILOT_SEED,
        "full_vector": full_vector,
        "selections": selections,
        "primary_size": PRIMARY_PILOT_SIZE,
        "primary": primary,
        "primary_task_profiles": [profiles_by_task[task] for task in primary["tasks"]],
    }


def write_csvs(data: dict[str, Any]) -> None:
    with OUT_TRANSITIONS_CSV.open("w", newline="") as f:
        fields = ["config", "clean_k", "prompt_k", "count", "tasks"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for config, entry in data["transition_matrices"].items():
            for clean_k in range(4):
                for prompt_k in range(4):
                    cell = entry["matrix"][str(clean_k)][str(prompt_k)]
                    writer.writerow({
                        "config": config,
                        "clean_k": clean_k,
                        "prompt_k": prompt_k,
                        "count": cell["count"],
                        "tasks": ";".join(cell["tasks"]),
                    })
    with OUT_DECOMP_CSV.open("w", newline="") as f:
        fields = ["config", "rollup", "count"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for config, entry in data["transition_matrices"].items():
            for key, count in entry["rollup_counts"].items():
                writer.writerow({"config": config, "rollup": key, "count": count})
    with OUT_UNCERTAINTY_CSV.open("w", newline="") as f:
        fields = ["effect_id", "metric", "point", "mean", "ci95_low", "ci95_high", "probability_positive", "probability_negative"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for effect in data["task_bootstrap_uncertainty"]:
            for metric, values in effect["metrics"].items():
                writer.writerow({"effect_id": effect["id"], "metric": metric, **values})
    with OUT_RERUN_CSV.open("w", newline="") as f:
        fields = ["config", "attempt_cap", "expected_solved_tasks", "mean_probability_at_least_one_success", "expected_stop_on_success_cost_usd", "fixed_attempt_cost_usd", "stop_on_success_cost_per_expected_solved_task_usd", "fixed_attempt_cost_per_expected_solved_task_usd", "observed_any_success_tasks_in_existing_3_reps"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in data["rerun_economics"]:
            writer.writerow({field: row[field] for field in fields})
    with OUT_TASKS_CSV.open("w", newline="") as f:
        fields = ["task", "language", "category", "clean_k", "neutral_k", "preamble_k", "preamble_neutral_k", "workflow_k", "preamble_workflow_k", "workflow_transition_label", "preamble_transition_label", "workflow_vs_clean_delta", "preamble_vs_clean_delta", "preamble_workflow_interaction_k", "labels"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in data["task_profiles"]:
            writer.writerow({
                "task": row["task"],
                "language": row["language"],
                "category": row["category"],
                "clean_k": row["clean_k"],
                "neutral_k": row["k_by_config"]["baseline-neutral-orchestration-only"],
                "preamble_k": row["k_by_config"]["baseline-preamble-only"],
                "preamble_neutral_k": row["k_by_config"]["baseline-preamble-orchestration"],
                "workflow_k": row["k_by_config"]["baseline-wf-only"],
                "preamble_workflow_k": row["k_by_config"]["baseline-preamble-orchestration-wf"],
                "workflow_transition_label": row["workflow_transition_label"],
                "preamble_transition_label": row["preamble_transition_label"],
                "workflow_vs_clean_delta": row["workflow_vs_clean_delta"],
                "preamble_vs_clean_delta": row["preamble_vs_clean_delta"],
                "preamble_workflow_interaction_k": row["preamble_workflow_interaction_k"],
                "labels": ";".join(row["labels"]),
            })
    with OUT_PILOT_CSV.open("w", newline="") as f:
        fields = ["task", "language", "clean_k", "workflow_k", "preamble_k", "preamble_workflow_k", "labels"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in data["pilot_selection"]["primary_task_profiles"]:
            writer.writerow({
                "task": row["task"],
                "language": row["language"],
                "clean_k": row["clean_k"],
                "workflow_k": row["k_by_config"]["baseline-wf-only"],
                "preamble_k": row["k_by_config"]["baseline-preamble-only"],
                "preamble_workflow_k": row["k_by_config"]["baseline-preamble-orchestration-wf"],
                "labels": ";".join(row["labels"]),
            })


def heatmap_table(config: str, entry: dict[str, Any]) -> str:
    rows = []
    for clean_k in range(4):
        tds = [f'<th>{clean_k}/3 clean</th>']
        for prompt_k in range(4):
            count = entry["matrix"][str(clean_k)][str(prompt_k)]["count"]
            klass = "neutral"
            if prompt_k > clean_k:
                klass = "good"
            elif prompt_k < clean_k:
                klass = "bad"
            tds.append(f'<td><span class="tag {klass}">{count}</span></td>')
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return f'''<div class="mini"><h3>{e(entry['label'])}</h3><table class="matrix"><thead><tr><th></th><th>0/3 prompt</th><th>1/3 prompt</th><th>2/3 prompt</th><th>3/3 prompt</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''


def decomp_table(matrices: dict[str, Any]) -> str:
    rows = []
    for config, entry in matrices.items():
        r = entry["rollup_counts"]
        rows.append(f'''<tr><td><code>{e(config)}</code><div class="muted">{e(entry['label'])}</div></td><td>{entry['delta_attempt_solves']:+d}</td><td>{entry['delta_any_success_tasks']:+d}</td><td>{entry['delta_stable_success_tasks']:+d}</td><td>{r['new_reach']}</td><td>{r['reliability_improvement']}</td><td>{r['robust_improvement']}</td><td>{r['variance_lottery_ticket_change']}</td><td>{r['regression']}</td></tr>''')
    return "".join(rows)


def uncertainty_table(uncertainty: list[dict[str, Any]]) -> str:
    rows = []
    for effect in uncertainty:
        attempt = effect["metrics"]["attempt_solves_per_108"]
        reach = effect["metrics"]["any_success_tasks_per_36"]
        stable = effect["metrics"]["stable_3_of_3_tasks_per_36"]
        klass = "good" if attempt["point"] > 0 else ("bad" if attempt["point"] < 0 else "neutral")
        rows.append(f'''<tr><td><b>{e(effect['label'])}</b><div class="muted">{e(effect['meaning'])}</div></td><td><span class="tag {klass}">{attempt['point']:+.1f}</span></td><td>{attempt['ci95_low']:+.1f} to {attempt['ci95_high']:+.1f}</td><td>{reach['point']:+.1f} ({reach['ci95_low']:+.1f} to {reach['ci95_high']:+.1f})</td><td>{stable['point']:+.1f} ({stable['ci95_low']:+.1f} to {stable['ci95_high']:+.1f})</td><td>{attempt['probability_positive']:.2f}</td></tr>''')
    return "".join(rows)


def rerun_table(rows: list[dict[str, Any]]) -> str:
    html_rows = []
    for row in rows:
        if row["attempt_cap"] not in (1, 2, 3):
            continue
        html_rows.append(f'''<tr><td><code>{e(row['config'])}</code><div class="muted">{e(row['label'])}</div></td><td>{row['attempt_cap']}</td><td>{row['expected_solved_tasks']:.1f}</td><td>{pct(row['mean_probability_at_least_one_success'])}</td><td>{money(row['expected_stop_on_success_cost_usd'])}</td><td>{money(row['stop_on_success_cost_per_expected_solved_task_usd'])}</td><td>{money(row['fixed_attempt_cost_usd'])}</td><td>{row['observed_any_success_tasks_in_existing_3_reps'] if row['observed_any_success_tasks_in_existing_3_reps'] is not None else '—'}</td></tr>''')
    return "".join(html_rows)


def config_summary_table(config_summaries: list[dict[str, Any]]) -> str:
    rows = []
    for row in config_summaries:
        rows.append(f'''<tr><td><code>{e(row['config'])}</code><div class="muted">{e(row['label'])}</div></td><td>{row['attempt_solves']}/108</td><td>{row['any_success_tasks']}/36</td><td>{row['stable_3_of_3_tasks']}/36</td><td>{row['flaky_1_or_2_of_3_tasks']}/36</td><td>{row['k_distribution']}</td><td>{row['invalid_reward_reps']}</td></tr>''')
    return "".join(rows)


def task_profile_table(profiles: list[dict[str, Any]], limit: int = 18) -> str:
    selected = sorted(profiles, key=lambda row: (-row["total_prompt_range"], row["preamble_workflow_interaction_k"], row["task"]))[:limit]
    rows = []
    for row in selected:
        k = row["k_by_config"]
        rows.append(f'''<tr><td><code>{e(row['task'])}</code><div class="muted">{e(row['language'])}</div></td><td>{row['clean_k']}</td><td>{k['baseline-wf-only']}</td><td>{k['baseline-preamble-only']}</td><td>{k['baseline-preamble-orchestration-wf']}</td><td>{row['preamble_workflow_interaction_k']:+d}</td><td>{', '.join(e(label) for label in row['labels'][:5])}</td></tr>''')
    return "".join(rows)


def pilot_metric_table(pilot: dict[str, Any]) -> str:
    full = pilot["full_vector"]
    primary = pilot["primary"]["metrics"]
    keys = [
        ("kdist:baseline:0", "Clean 0/3 tasks"),
        ("kdist:baseline:3", "Clean 3/3 tasks"),
        ("rollup:baseline-wf-only:new_reach", "Workflow new reach"),
        ("rollup:baseline-wf-only:regression", "Workflow regressions"),
        ("rollup:baseline-wf-only:variance_lottery_ticket_change", "Workflow variance/lottery changes"),
        ("rollup:baseline-preamble-orchestration-wf:regression", "Preamble+workflow regressions"),
    ]
    rows = []
    for key, label in keys:
        rows.append(f'''<tr><td>{e(label)}</td><td>{pct(full.get(key, 0.0))}</td><td>{pct(primary.get(key, 0.0))}</td><td>{(primary.get(key, 0.0) - full.get(key, 0.0)) * 100:+.1f} pp</td></tr>''')
    return "".join(rows)


def pilot_table(pilot: dict[str, Any]) -> str:
    rows = []
    for row in pilot["primary_task_profiles"]:
        k = row["k_by_config"]
        rows.append(f'''<tr><td><code>{e(row['task'])}</code></td><td>{e(row['language'])}</td><td>{row['clean_k']}</td><td>{k['baseline-wf-only']}</td><td>{k['baseline-preamble-only']}</td><td>{k['baseline-preamble-orchestration-wf']}</td><td>{', '.join(e(label) for label in row['labels'][:4])}</td></tr>''')
    return "".join(rows)


def render_html(data: dict[str, Any]) -> str:
    matrices = data["transition_matrices"]
    config_summaries = data["config_summaries"]
    by_config = {row["config"]: row for row in config_summaries}
    uncertainty = data["task_bootstrap_uncertainty"]
    pilot = data["pilot_selection"]
    workflow = matrices["baseline-wf-only"]
    combo = matrices["baseline-preamble-orchestration-wf"]
    interaction = next(row for row in uncertainty if row["id"] == "preamble_workflow_interaction")["metrics"]["attempt_solves_per_108"]
    manifest_items = "".join(f'<li><code>{e(path)}</code></li>' for path in data["inputs"]["manifests"])
    outputs = "".join(f'<li><code>{e(path)}</code></li>' for path in data["outputs"].values())
    heatmaps = "".join(heatmap_table(config, entry) for config, entry in matrices.items())
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GPT-5.5 low rep-aware prompt reliability</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 8% 0%,#173c54,#07111f 45%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}main{{max-width:1400px;margin:0 auto;padding:36px 22px 66px}}.hero,.card,.callout,.mini{{background:rgba(15,29,49,.91);border:1px solid var(--line);border-radius:24px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.25)}}.hero{{padding:34px;background:linear-gradient(135deg,rgba(52,211,153,.18),rgba(15,29,49,.94) 43%,rgba(96,165,250,.11))}}.kicker{{color:var(--green);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:900}}h1{{font-size:clamp(34px,5.8vw,72px);line-height:.92;letter-spacing:-.06em;margin:12px 0 16px}}h2{{margin:34px 0 12px;font-size:27px;letter-spacing:-.02em}}h3{{margin:0 0 10px}}p,li{{color:#dbe7fb;max-width:1080px}}.pills{{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:850;border:1px solid var(--line);background:#0b1728;color:var(--muted);white-space:nowrap;margin:1px}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:32px;line-height:1;letter-spacing:-.04em}}.stat span,.muted,.src{{color:var(--muted);font-size:12px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.heatmaps{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68);margin-bottom:22px}}th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}.matrix th,.matrix td{{text-align:center}}.matrix th:first-child{{text-align:right}}code,pre{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px}}code{{padding:1px 5px;font-size:12px}}pre{{white-space:pre-wrap;padding:12px;overflow:auto}}.section-note{{color:#dbe7fb;border-left:4px solid var(--blue);padding-left:14px}}@media(max-width:980px){{.stats,.grid,.heatmaps{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">Rep-aware reliability · GPT-5.5 low · prompt-shaped configs</div><h1>Use the three reps as signal, not just 108 cells.</h1><p>Each task/config is treated as a mini distribution: 0/3, 1/3, 2/3, or 3/3 solved. The report separates new reach, reliability, regressions, uncertainty by task, and rerun economics. No new benchmark ablations were launched and no prompt files were written.</p><div class="pills"><span class="pill good">k/3 transition matrices</span><span class="pill neutral">task-bootstrap uncertainty</span><span class="pill neutral">rerun economics</span><span class="pill caution">rep indices are not assumed matched seeds</span></div><p class="src">Inputs: direct <code>result.json</code> files under <code>{e(data['inputs']['low_result_root'])}</code>; solve rule is <code>reward_binary == 1</code>.</p></section>
<div class="stats"><div class="stat"><b>{workflow['delta_attempt_solves']:+d}</b><span>workflow attempt-solve delta vs clean /108</span></div><div class="stat"><b>{workflow['delta_any_success_tasks']:+d}</b><span>workflow tasks with ≥1 success vs clean /36</span></div><div class="stat"><b>{interaction['point']:+.0f}</b><span>preamble×workflow interaction, attempt solves /108</span></div><div class="stat"><b>{pilot['primary_size']}</b><span>rep-aware representative pilot tasks</span></div></div>
<section class="callout good"><h2>Verdict</h2><p>The three reps change the story. <b>Workflow checklist</b> is still the best prompt-only row by attempt solves ({by_config['baseline-wf-only']['attempt_solves']}/108), but it is better described as changing task reliability/reach: {workflow['rollup_counts']['new_reach']} new-reach tasks, {workflow['rollup_counts']['reliability_improvement']} reliability improvements, and {workflow['rollup_counts']['regression']} regressions versus clean. The preamble+workflow row is not just four solves lower; its task-bootstrap interaction is {interaction['point']:+.0f} attempt solves per 108 with 95% CI {interaction['ci95_low']:+.0f} to {interaction['ci95_high']:+.0f}.</p></section>
<h2>Config k/3 summaries</h2><table><thead><tr><th>Config</th><th>Attempt solves</th><th>Any-success tasks</th><th>Stable 3/3 tasks</th><th>Flaky 1/3 or 2/3 tasks</th><th>k distribution</th><th>Invalid rewards</th></tr></thead><tbody>{config_summary_table(config_summaries)}</tbody></table>
<h2>k/3 transition matrices vs clean low</h2><p class="section-note">Rows are clean low k/3; columns are the prompt row k/3. Green cells moved up, red cells moved down. Counts are tasks, not individual reps.</p><div class="heatmaps">{heatmaps}</div>
<h2>Reliability / new-reach / regression decomposition</h2><table><thead><tr><th>Config</th><th>Attempt solve Δ</th><th>Any-success task Δ</th><th>Stable 3/3 task Δ</th><th>New reach</th><th>Reliability improvement</th><th>Robust improvement</th><th>Variance / lottery change</th><th>Regression</th></tr></thead><tbody>{decomp_table(matrices)}</tbody></table>
<h2>Task-bootstrap uncertainty</h2><p class="section-note">Bootstrap samples resample the 36 tasks with replacement ({BOOTSTRAP_REPS:,} reps). This avoids treating 108 attempts as independent for task-level claims.</p><table><thead><tr><th>Effect</th><th>Attempt solve Δ /108</th><th>95% CI</th><th>Any-success task Δ /36</th><th>Stable 3/3 task Δ /36</th><th>P(positive)</th></tr></thead><tbody>{uncertainty_table(uncertainty)}</tbody></table>
<h2>Rerun economics: 1, 2, and 3 attempts</h2><p class="section-note">For each task/config, estimate p=k/3. Probability of at least one success after m attempts is 1−(1−p)^m. Main cost column assumes stop-on-success; fixed-attempt cost is also shown.</p><table><thead><tr><th>Config</th><th>Attempt cap</th><th>Expected solved tasks</th><th>Mean P(≥1 success)</th><th>Expected stop-on-success cost</th><th>Cost / expected solved task</th><th>Fixed-attempt cost</th><th>Observed any success in 3 reps</th></tr></thead><tbody>{rerun_table(data['rerun_economics'])}</tbody></table>
<h2>Task profiles with the widest prompt variation</h2><table><thead><tr><th>Task</th><th>Clean k</th><th>Workflow k</th><th>Preamble k</th><th>Preamble+workflow k</th><th>Interaction k</th><th>Labels</th></tr></thead><tbody>{task_profile_table(data['task_profiles'])}</tbody></table>
<h2>Updated representative pilot subset preserving transition patterns</h2><p class="section-note">The primary 12-task subset is selected to preserve k distributions, transition matrices, decomposition rollups, any/stable/flaky task rates, language mix, and profile labels.</p><div class="grid"><section class="card"><h3>Full set vs pilot transition features</h3><table><thead><tr><th>Feature</th><th>Full 36 tasks</th><th>Primary 12 tasks</th><th>Difference</th></tr></thead><tbody>{pilot_metric_table(pilot)}</tbody></table></section><section class="card"><h3>Alternative subset sizes</h3><table><thead><tr><th>Size</th><th>Score</th><th>Tasks</th></tr></thead><tbody>{''.join(f'<tr><td>{sel["size"]}</td><td>{sel["score"]:.3f}</td><td>{len(sel["tasks"])}</td></tr>' for sel in pilot['selections'])}</tbody></table></section></div><table><thead><tr><th>Task</th><th>Language</th><th>Clean k</th><th>Workflow k</th><th>Preamble k</th><th>Preamble+workflow k</th><th>Labels</th></tr></thead><tbody>{pilot_table(pilot)}</tbody></table>
<section class="callout caution"><h2>Interpretation caveats</h2><ul><li>Rep indices across configs are paired by task but are <b>not</b> treated as matched random seeds; the unit of uncertainty is the task.</li><li>OMP/tool-surface rows, behavioral wrappers, and <code>results/_contaminated/</code> are excluded from prompt-only conclusions.</li><li>Rerun economics use p̂=k/3, which is useful for decision modeling but still a noisy estimate for each task.</li></ul></section>
<section class="callout"><h2>Evidence and generated artifacts</h2><p>Source manifests:</p><ul>{manifest_items}</ul><p>Generated outputs:</p><ul>{outputs}</ul><p>Every numeric table is generated from direct <code>result.json</code> cells; sample paths are stored in the JSON under config summaries.</p></section>
</main></body></html>'''


def build() -> dict[str, Any]:
    rows_by_config = {config: read_config_rows(config) for config in PROMPT_CONFIGS}
    tasks = common_complete_tasks(rows_by_config)
    if len(tasks) != 36:
        raise RuntimeError(f"expected 36 complete tasks, got {len(tasks)}")
    summaries = build_task_summaries(tasks, rows_by_config)
    matrices = transition_matrices(tasks, summaries)
    config_summaries = [config_summary(config, tasks, summaries) for config in PROMPT_CONFIGS]
    uncertainty = task_bootstrap_uncertainty(tasks, summaries)
    economics = rerun_economics(tasks, summaries)
    profiles = task_profiles(tasks, summaries, matrices, rows_by_config)
    pilot = pilot_selection(profiles)
    data = {
        "inputs": {
            "low_result_root": str(LOW_ROOT.relative_to(ROOT)),
            "prompt_configs": PROMPT_CONFIGS,
            "complete_tasks": len(tasks),
            "reps_per_task": 3,
            "attempt_cells": len(tasks) * 3,
            "manifests": [path for path in MANIFESTS if (ROOT / path).exists()],
        },
        "outputs": {
            "json": str(OUT_JSON.relative_to(ROOT)),
            "transition_matrices_csv": str(OUT_TRANSITIONS_CSV.relative_to(ROOT)),
            "decomposition_csv": str(OUT_DECOMP_CSV.relative_to(ROOT)),
            "uncertainty_csv": str(OUT_UNCERTAINTY_CSV.relative_to(ROOT)),
            "rerun_economics_csv": str(OUT_RERUN_CSV.relative_to(ROOT)),
            "task_profiles_csv": str(OUT_TASKS_CSV.relative_to(ROOT)),
            "pilot_subset_csv": str(OUT_PILOT_CSV.relative_to(ROOT)),
            "html": str(OUT_HTML.relative_to(ROOT)),
        },
        "method_notes": {
            "solve_rule": "Only reward_binary == 1 counts as solved; invalid/negative rewards are tracked separately and otherwise counted unsolved.",
            "rep_pairing_caveat": "Task/config summaries use the three existing reps, but rep0/rep1/rep2 across configs are not assumed to be matched random seeds.",
            "uncertainty_rule": "Task-bootstrap resamples the 36 tasks with replacement; 108 attempts are not treated as independent for task-level uncertainty.",
            "rerun_rule": "Rerun economics estimate per-task success probability as p_hat=k/3 and report stop-on-success plus fixed-attempt cost.",
            "scope": "Prompt-only GPT-5.5 low configs; no OMP/tool-surface rows, behavioral wrappers, new ablations, prompt files, or results/_contaminated artifacts are used.",
        },
        "config_summaries": config_summaries,
        "transition_matrices": matrices,
        "task_bootstrap_uncertainty": uncertainty,
        "rerun_economics": economics,
        "task_profiles": profiles,
        "pilot_selection": pilot,
    }
    return data


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = build()
    OUT_JSON.write_text(json.dumps(data, indent=2))
    write_csvs(data)
    OUT_HTML.write_text(render_html(data))
    for path in [OUT_JSON, OUT_TRANSITIONS_CSV, OUT_DECOMP_CSV, OUT_UNCERTAINTY_CSV, OUT_RERUN_CSV, OUT_TASKS_CSV, OUT_PILOT_CSV, OUT_HTML]:
        print("wrote", path.relative_to(ROOT), path.stat().st_size)


if __name__ == "__main__":
    main()
