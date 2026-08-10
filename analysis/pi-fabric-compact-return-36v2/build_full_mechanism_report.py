#!/usr/bin/env python3
"""Explain the mechanism behind Pi Fabric compact-return behavior on 36v2."""

from __future__ import annotations

import argparse
import html
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASELINE = "baseline"
CONTROL = "pi-fabric-output-telemetry@1.0.0"
TREATMENT = "pi-fabric-compact-return@1.0.0"
CONFIGS = (CONTROL, TREATMENT)
TELEMETRY_KIND = "pi-fabric.output-telemetry.v1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def visible_text_chars(message: dict[str, Any]) -> int:
    return sum(
        len(str(item.get("text", "")))
        for item in message.get("content") or []
        if isinstance(item, dict) and item.get("type") == "text"
    )


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    return ordered[round((len(ordered) - 1) * fraction)]


def exact_integer_sign_flip_pvalue(differences: list[int]) -> float:
    """Compute an exact two-sided sign-flip p-value for integer differences."""
    distribution: Counter[int] = Counter({0: 1})
    for difference in differences:
        updated: Counter[int] = Counter()
        for total, count in distribution.items():
            updated[total + difference] += count
            updated[total - difference] += count
        distribution = updated
    observed = abs(sum(differences))
    extreme = sum(count for total, count in distribution.items() if abs(total) >= observed)
    return extreme / (2 ** len(differences))


def monte_carlo_sign_flip_pvalue(
    differences: list[float], *, seed: int = 20260728, draws: int = 200_000
) -> float:
    """Estimate a two-sided task-level sign-flip p-value deterministically."""
    observed = abs(statistics.mean(differences))
    generator = random.Random(seed)
    extreme = sum(
        abs(
            statistics.mean(
                difference * (1 if generator.getrandbits(1) else -1)
                for difference in differences
            )
        )
        >= observed
        for _ in range(draws)
    )
    return (extreme + 1) / (draws + 1)


def correlation(left: list[float], right: list[float]) -> float:
    left_mean = statistics.mean(left)
    right_mean = statistics.mean(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((x - left_mean) ** 2 for x in left)
        * sum((y - right_mean) ** 2 for y in right)
    )
    return numerator / denominator if denominator else 0.0


def load_run(result_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result = load_json(result_path)
    session_paths = list((result_path.parent / "session").glob("*.jsonl"))
    if len(session_paths) != 1:
        raise ValueError(f"Expected one session for {result_path.parent}")

    calls_by_id: dict[str, dict[str, Any]] = {}
    call_order: list[str] = []
    executed_calls: list[dict[str, Any]] = []
    preexecution_validation_failures = 0
    for raw_line in session_paths[0].read_text(errors="replace").splitlines():
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "message":
            continue
        message = record.get("message") or {}
        if message.get("role") == "assistant":
            for item in message.get("content") or []:
                if not (
                    isinstance(item, dict)
                    and item.get("type") == "toolCall"
                    and item.get("name") == "fabric_exec"
                ):
                    continue
                arguments = item.get("arguments") or {}
                call_id = str(item.get("id"))
                code = str(arguments.get("code", ""))
                calls_by_id[call_id] = {
                    "id": call_id,
                    "ordinal": len(call_order),
                    "code_chars": len(code),
                    "promise_all": "Promise.all" in code,
                    "control_flow": bool(
                        re.search(r"\b(?:if|for|while|switch|try|catch)\b", code)
                    ),
                    "selector": bool(
                        re.search(
                            r"\.(?:slice|filter|map|match|split|substring|trim)\s*\(",
                            code,
                        )
                    ),
                    "display_name": str(
                        (arguments.get("display") or {}).get("name", "")
                    ),
                }
                call_order.append(call_id)
        if not (
            message.get("role") == "toolResult"
            and message.get("toolName") == "fabric_exec"
        ):
            continue
        details = message.get("details") or {}
        telemetry = details.get("telemetry")
        if not (
            isinstance(telemetry, dict)
            and telemetry.get("kind") == TELEMETRY_KIND
        ):
            result_text = "".join(
                str(item.get("text", ""))
                for item in message.get("content") or []
                if isinstance(item, dict) and item.get("type") == "text"
            )
            if (
                message.get("isError")
                and not details
                and result_text.startswith('Validation failed for tool "fabric_exec"')
            ):
                preexecution_validation_failures += 1
                continue
            raise ValueError(f"Missing telemetry in {session_paths[0]}")
        call_id = str(message.get("toolCallId"))
        call = dict(
            calls_by_id.get(
                call_id,
                {
                    "id": call_id,
                    "ordinal": len(executed_calls),
                    "code_chars": 0,
                    "promise_all": False,
                    "control_flow": False,
                    "selector": False,
                    "display_name": "",
                },
            )
        )
        operations = [
            operation
            for operation in ((details.get("trace") or {}).get("operations") or [])
            if isinstance(operation, dict)
        ]
        nested_chars = int(telemetry["nestedSandboxResultChars"])
        formatted_chars = int(telemetry["formattedValueChars"])
        call.update(
            {
                "operations": operations,
                "refs": [str(operation.get("ref", "")) for operation in operations],
                "nested_chars": nested_chars,
                "formatted_chars": formatted_chars,
                "visible_chars": visible_text_chars(message),
                "net_reduction_chars": nested_chars - formatted_chars,
                "selection_ratio": (
                    formatted_chars / nested_chars if nested_chars else None
                ),
                "is_error": bool(message.get("isError")),
                "nested_truncations": int(telemetry["nestedTruncatedResults"]),
                "outer_truncated": int(
                    telemetry["rawOutputChars"] > telemetry["returnedTextChars"]
                ),
            }
        )
        executed_calls.append(call)

    prior_reads: dict[str, list[tuple[int, int | None]]] = defaultdict(list)
    for call in executed_calls:
        call["whole_file_reads"] = 0
        call["exact_rereads"] = 0
        for operation in call["operations"]:
            if operation.get("ref") != "pi.read":
                continue
            arguments = operation.get("args") or {}
            path = arguments.get("path")
            if not isinstance(path, str):
                continue
            signature = (int(arguments.get("offset", 1)), arguments.get("limit"))
            if arguments.get("limit") is None:
                call["whole_file_reads"] += 1
            if signature in prior_reads[path]:
                call["exact_rereads"] += 1
            prior_reads[path].append(signature)

    result["_issued_fabric_calls"] = len(call_order)
    result["_preexecution_validation_failures"] = preexecution_validation_failures
    return result, executed_calls


def load_all(results_root: Path) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    for config in CONFIGS:
        runs: list[dict[str, Any]] = []
        calls: list[dict[str, Any]] = []
        result_paths = sorted(
            (results_root / "gpt-5.6-sol" / "low" / config).glob(
                "*/rep*/result.json"
            )
        )
        if len(result_paths) != 108:
            raise ValueError(f"Expected 108 results for {config}, found {len(result_paths)}")
        for result_path in result_paths:
            result, run_calls = load_run(result_path)
            runs.append(result)
            for call in run_calls:
                call.update(task=result["task"], rep=result["rep"])
            calls.extend(run_calls)
        data[config] = {"runs": runs, "calls": calls}
    return data


def aggregate(config_data: dict[str, Any]) -> dict[str, Any]:
    runs = config_data["runs"]
    calls = config_data["calls"]
    operation_counts = Counter(ref for call in calls for ref in call["refs"])
    nested = sum(call["nested_chars"] for call in calls)
    formatted = sum(call["formatted_chars"] for call in calls)
    visible = sum(call["visible_chars"] for call in calls)
    ratios = [
        call["selection_ratio"]
        for call in calls
        if call["selection_ratio"] is not None
    ]
    return {
        "runs": len(runs),
        "solves": sum(int(run["reward_binary"] == 1) for run in runs),
        "mean_partial_reward": statistics.mean(
            float(run["reward_partial"]) for run in runs
        ),
        "calls": len(calls),
        "issued_calls": sum(int(run["_issued_fabric_calls"]) for run in runs),
        "preexecution_validation_failures": sum(
            int(run["_preexecution_validation_failures"]) for run in runs
        ),
        "turns": sum(int(run["turns"]) for run in runs),
        "wall_seconds": sum(float(run["agent_wall_s"]) for run in runs),
        "input_tokens": sum(int(run["input_tokens"]) for run in runs),
        "cache_read_tokens": sum(int(run["cache_read_tokens"]) for run in runs),
        "output_tokens": sum(int(run["output_tokens"]) for run in runs),
        "total_tokens": sum(int(run["combined_total_tokens"]) for run in runs),
        "cost_usd": sum(float(run["combined_cost_usd"]) for run in runs),
        "code_chars": sum(call["code_chars"] for call in calls),
        "code_chars_per_call": sum(call["code_chars"] for call in calls) / len(calls),
        "code_chars_p90": percentile([call["code_chars"] for call in calls], 0.9),
        "promise_all_calls": sum(call["promise_all"] for call in calls),
        "control_flow_calls": sum(call["control_flow"] for call in calls),
        "selector_calls": sum(call["selector"] for call in calls),
        "nested_chars": nested,
        "formatted_chars": formatted,
        "visible_chars": visible,
        "selection_ratio": formatted / nested,
        "median_call_selection_ratio": statistics.median(ratios),
        "net_reduction_chars": nested - formatted,
        "large_nested_calls": sum(call["nested_chars"] > 50_000 for call in calls),
        "large_visible_calls": sum(call["visible_chars"] > 50_000 for call in calls),
        "nested_truncations": sum(call["nested_truncations"] for call in calls),
        "outer_truncated_calls": sum(call["outer_truncated"] for call in calls),
        "error_results": sum(call["is_error"] for call in calls),
        "operation_counts": dict(operation_counts),
        "whole_file_reads": sum(call["whole_file_reads"] for call in calls),
        "exact_rereads": sum(call["exact_rereads"] for call in calls),
    }


def relative_change(control: float, treatment: float) -> float:
    return treatment / control - 1 if control else 0.0


def paired_run_deltas(data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[tuple[str, int], tuple[dict[str, Any], list[dict[str, Any]]]]] = {}
    for config in CONFIGS:
        runs = {(str(run["task"]), int(run["rep"])): run for run in data[config]["runs"]}
        calls = defaultdict(list)
        for call in data[config]["calls"]:
            calls[(str(call["task"]), int(call["rep"]))].append(call)
        by_key[config] = {key: (run, calls[key]) for key, run in runs.items()}

    rows: list[dict[str, Any]] = []
    for key in sorted(by_key[CONTROL]):
        control_run, control_calls = by_key[CONTROL][key]
        treatment_run, treatment_calls = by_key[TREATMENT][key]
        rows.append(
            {
                "task": key[0],
                "rep": key[1],
                "token_delta": int(treatment_run["combined_total_tokens"])
                - int(control_run["combined_total_tokens"]),
                "cache_delta": int(treatment_run["cache_read_tokens"])
                - int(control_run["cache_read_tokens"]),
                "input_delta": int(treatment_run["input_tokens"])
                - int(control_run["input_tokens"]),
                "output_delta": int(treatment_run["output_tokens"])
                - int(control_run["output_tokens"]),
                "call_delta": len(treatment_calls) - len(control_calls),
                "visible_delta": sum(call["visible_chars"] for call in treatment_calls)
                - sum(call["visible_chars"] for call in control_calls),
                "nested_delta": sum(call["nested_chars"] for call in treatment_calls)
                - sum(call["nested_chars"] for call in control_calls),
                "code_delta": sum(call["code_chars"] for call in treatment_calls)
                - sum(call["code_chars"] for call in control_calls),
                "reread_delta": sum(call["exact_rereads"] for call in treatment_calls)
                - sum(call["exact_rereads"] for call in control_calls),
            }
        )
    return rows


def load_baseline(results_root: Path) -> tuple[dict[str, Any], dict[tuple[str, int], dict[str, Any]]]:
    result_paths = sorted(
        (results_root / "gpt-5.6-sol" / "low" / BASELINE).glob("*/rep*/result.json")
    )
    if len(result_paths) != 108:
        raise ValueError(f"Expected 108 baseline results, found {len(result_paths)}")
    runs = [load_json(path) for path in result_paths]
    by_key = {(str(run["task"]), int(run["rep"])): run for run in runs}
    return (
        {
            "runs": len(runs),
            "solves": sum(int(run["reward_binary"] == 1) for run in runs),
            "mean_partial_reward": statistics.mean(
                float(run["reward_partial"]) for run in runs
            ),
            "total_tokens": sum(int(run["combined_total_tokens"]) for run in runs),
            "cost_usd": sum(float(run["combined_cost_usd"]) for run in runs),
            "wall_seconds": sum(float(run["agent_wall_s"]) for run in runs),
            "turns": sum(int(run["turns"]) for run in runs),
            "tool_calls": sum(int(run["tool_calls"]) for run in runs),
            "cache_read_tokens": sum(int(run["cache_read_tokens"]) for run in runs),
        },
        by_key,
    )


def case_study(
    data: dict[str, dict[str, Any]], task: str, rep: int
) -> dict[str, Any]:
    output: dict[str, Any] = {"task": task, "rep": rep}
    for config in CONFIGS:
        run = next(
            run
            for run in data[config]["runs"]
            if run["task"] == task and int(run["rep"]) == rep
        )
        calls = [
            call
            for call in data[config]["calls"]
            if call["task"] == task and int(call["rep"]) == rep
        ]
        output[config] = {
            "tokens": int(run["combined_total_tokens"]),
            "cache_tokens": int(run["cache_read_tokens"]),
            "calls": len(calls),
            "nested_chars": sum(call["nested_chars"] for call in calls),
            "visible_chars": sum(call["visible_chars"] for call in calls),
            "exact_rereads": sum(call["exact_rereads"] for call in calls),
            "selector_calls": sum(call["selector"] for call in calls),
        }
    return output


def build_summary(results_root: Path) -> dict[str, Any]:
    data = load_all(results_root)
    control = aggregate(data[CONTROL])
    treatment = aggregate(data[TREATMENT])
    baseline, baseline_runs = load_baseline(results_root)
    deltas = paired_run_deltas(data)
    token_deltas = [float(row["token_delta"]) for row in deltas]
    correlations = {
        field: correlation(
            [float(row[field]) for row in deltas],
            token_deltas,
        )
        for field in (
            "cache_delta",
            "input_delta",
            "output_delta",
            "call_delta",
            "visible_delta",
            "nested_delta",
            "code_delta",
            "reread_delta",
        )
    }
    regression = max(deltas, key=lambda row: row["token_delta"])
    win = min(deltas, key=lambda row: row["token_delta"])
    control_runs = {
        (str(run["task"]), int(run["rep"])): run for run in data[CONTROL]["runs"]
    }
    treatment_runs = {
        (str(run["task"]), int(run["rep"])): run
        for run in data[TREATMENT]["runs"]
    }
    control_only = treatment_only = 0
    for key, control_run in control_runs.items():
        control_solved = int(control_run["reward_binary"]) == 1
        treatment_solved = int(treatment_runs[key]["reward_binary"]) == 1
        control_only += int(control_solved and not treatment_solved)
        treatment_only += int(treatment_solved and not control_solved)
    discordant = control_only + treatment_only
    smaller_discordant = min(control_only, treatment_only)
    mcnemar_pvalue = min(
        1.0,
        2
        * sum(math.comb(discordant, index) for index in range(smaller_discordant + 1))
        / (2**discordant),
    )
    task_partial_differences: list[float] = []
    task_solve_differences: list[int] = []
    for task in sorted({key[0] for key in control_runs}):
        task_partial_differences.append(
            statistics.mean(
                float(treatment_runs[(task, rep)]["reward_partial"])
                - float(control_runs[(task, rep)]["reward_partial"])
                for rep in range(3)
            )
        )
        task_solve_differences.append(
            sum(
                int(treatment_runs[(task, rep)]["reward_binary"] == 1)
                - int(control_runs[(task, rep)]["reward_binary"] == 1)
                for rep in range(3)
            )
        )
    baseline_only = compact_only = 0
    baseline_partial_differences: list[float] = []
    baseline_solve_differences: list[int] = []
    for key, baseline_run in baseline_runs.items():
        baseline_solved = int(baseline_run["reward_binary"]) == 1
        compact_solved = int(treatment_runs[key]["reward_binary"]) == 1
        baseline_only += int(baseline_solved and not compact_solved)
        compact_only += int(compact_solved and not baseline_solved)
    baseline_discordant = baseline_only + compact_only
    baseline_smaller = min(baseline_only, compact_only)
    baseline_mcnemar_pvalue = min(
        1.0,
        2
        * sum(
            math.comb(baseline_discordant, index)
            for index in range(baseline_smaller + 1)
        )
        / (2**baseline_discordant),
    )
    for task in sorted({key[0] for key in baseline_runs}):
        baseline_partial_differences.append(
            statistics.mean(
                float(treatment_runs[(task, rep)]["reward_partial"])
                - float(baseline_runs[(task, rep)]["reward_partial"])
                for rep in range(3)
            )
        )
        baseline_solve_differences.append(
            sum(
                int(treatment_runs[(task, rep)]["reward_binary"] == 1)
                - int(baseline_runs[(task, rep)]["reward_binary"] == 1)
                for rep in range(3)
            )
        )
    return {
        "results_root": str(results_root),
        "baseline": baseline,
        "control": control,
        "treatment": treatment,
        "baseline_changes": {
            "solves_absolute": treatment["solves"] - baseline["solves"],
            "partial_absolute": treatment["mean_partial_reward"]
            - baseline["mean_partial_reward"],
            "total_tokens": relative_change(
                baseline["total_tokens"], treatment["total_tokens"]
            ),
            "cost_usd": relative_change(baseline["cost_usd"], treatment["cost_usd"]),
            "wall_seconds": relative_change(
                baseline["wall_seconds"], treatment["wall_seconds"]
            ),
        },
        "baseline_paired_quality": {
            "baseline_only_solves": baseline_only,
            "compact_only_solves": compact_only,
            "discordant_solve_cells": baseline_discordant,
            "exact_mcnemar_pvalue": baseline_mcnemar_pvalue,
            "task_sign_flip_partial_pvalue": monte_carlo_sign_flip_pvalue(
                baseline_partial_differences, seed=20260730
            ),
            "task_sign_flip_solve_pvalue": exact_integer_sign_flip_pvalue(
                baseline_solve_differences
            ),
        },
        "changes": {
            field: relative_change(control[field], treatment[field])
            for field in (
                "calls",
                "turns",
                "input_tokens",
                "cache_read_tokens",
                "output_tokens",
                "total_tokens",
                "cost_usd",
                "code_chars",
                "code_chars_per_call",
                "nested_chars",
                "formatted_chars",
                "visible_chars",
                "selection_ratio",
                "net_reduction_chars",
                "whole_file_reads",
                "exact_rereads",
                "promise_all_calls",
                "selector_calls",
                "error_results",
            )
        },
        "token_delta_components": {
            "input": treatment["input_tokens"] - control["input_tokens"],
            "cache_read": treatment["cache_read_tokens"]
            - control["cache_read_tokens"],
            "output": treatment["output_tokens"] - control["output_tokens"],
            "total": treatment["total_tokens"] - control["total_tokens"],
        },
        "correlations_with_token_delta": correlations,
        "paired_quality": {
            "control_only_solves": control_only,
            "treatment_only_solves": treatment_only,
            "discordant_solve_cells": discordant,
            "exact_mcnemar_pvalue": mcnemar_pvalue,
            "task_sign_flip_partial_pvalue": monte_carlo_sign_flip_pvalue(
                task_partial_differences
            ),
            "task_sign_flip_solve_pvalue": exact_integer_sign_flip_pvalue(
                task_solve_differences
            ),
        },
        "regression_case": case_study(
            data, str(regression["task"]), int(regression["rep"])
        ),
        "win_case": case_study(data, str(win["task"]), int(win["rep"])),
        "largest_regressions": sorted(
            deltas, key=lambda row: row["token_delta"], reverse=True
        )[:5],
        "largest_wins": sorted(deltas, key=lambda row: row["token_delta"])[:5],
    }


def fmt_int(value: float) -> str:
    return f"{value:,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value * 100:+.1f}%"


def esc(value: Any) -> str:
    return html.escape(str(value))


def comparison_row(
    label: str,
    control: float,
    treatment: float,
    *,
    formatter=fmt_int,
) -> str:
    change = relative_change(control, treatment)
    verdict = "bad" if change > 0.01 else "good" if change < -0.01 else "neutral"
    return (
        f"<tr><th>{esc(label)}</th><td>{formatter(control)}</td>"
        f"<td>{formatter(treatment)}</td><td><span class='tag {verdict}'>"
        f"{fmt_pct(change)}</span></td></tr>"
    )


def render_case(summary: dict[str, Any], key: str, title: str) -> str:
    case = summary[key]
    left = case[CONTROL]
    right = case[TREATMENT]
    return f"""
    <article class="case">
      <h3>{esc(title)}</h3>
      <p><code>{esc(case['task'])}/rep{case['rep']}</code></p>
      <table><thead><tr><th>Measure</th><th>Control</th><th>Compact</th><th>Change</th></tr></thead><tbody>
      {comparison_row('Tokens', left['tokens'], right['tokens'])}
      {comparison_row('Cache-read tokens', left['cache_tokens'], right['cache_tokens'])}
      {comparison_row('Fabric calls', left['calls'], right['calls'])}
      {comparison_row('Nested result chars', left['nested_chars'], right['nested_chars'])}
      {comparison_row('Visible result chars', left['visible_chars'], right['visible_chars'])}
      {comparison_row('Exact rereads', left['exact_rereads'], right['exact_rereads'])}
      </tbody></table>
    </article>"""


def render(summary: dict[str, Any]) -> str:
    baseline = summary["baseline"]
    baseline_changes = summary["baseline_changes"]
    baseline_quality = summary["baseline_paired_quality"]
    left = summary["control"]
    right = summary["treatment"]
    changes = summary["changes"]
    token_parts = summary["token_delta_components"]
    quality = summary["paired_quality"]
    regression = summary["regression_case"]
    regression_left = regression[CONTROL]
    regression_right = regression[TREATMENT]
    win = summary["win_case"]
    win_left = win[CONTROL]
    win_right = win[TREATMENT]
    operation_rows = "".join(
        comparison_row(
            ref,
            left["operation_counts"].get(ref, 0),
            right["operation_counts"].get(ref, 0),
        )
        for ref in ("pi.read", "pi.grep", "pi.bash", "pi.edit", "pi.write")
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>Pi Fabric compact-return · full 36v2 mechanism</title>
<style>
:root{{--bg:#f5f7fb;--surface:#fff;--ink:#172033;--muted:#5c667a;--blue:#2357d8;--green:#087f5b;--red:#c92a2a;--amber:#b46a00;--line:#dce2ee}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}} main{{max-width:1100px;margin:auto;padding:28px 20px 64px}} .hero{{background:linear-gradient(135deg,#172a5a,#275cc9);color:white;padding:34px;border-radius:20px;box-shadow:0 14px 36px #172a5a22}} .hero h1{{font-size:clamp(2rem,5vw,3.8rem);line-height:1.02;margin:.25rem 0 1rem;max-width:900px}} .hero p{{max-width:850px;font-size:1.12rem}} .eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-weight:800;font-size:.76rem;color:#bdd0ff}} .pills{{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}} .pill,.tag{{display:inline-block;border-radius:999px;padding:.25rem .65rem;font-weight:750;font-size:.84rem}} .pill{{background:#ffffff20;border:1px solid #ffffff44}} .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}} .stat,.card,.case,.callout{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px}} .stat strong{{font-size:1.75rem;display:block}} .stat span{{color:var(--muted)}} h2{{margin-top:36px;font-size:1.65rem}} h3{{margin-bottom:.25rem}} table{{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden}} th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:right}} th:first-child,td:first-child{{text-align:left}} thead th{{background:#eef2f9}} .tag.bad{{background:#ffe3e3;color:var(--red)}} .tag.good{{background:#dff7ed;color:var(--green)}} .tag.neutral{{background:#edf1f7;color:var(--muted)}} .pipeline{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}} .stage{{background:var(--surface);border:1px solid var(--line);border-top:5px solid var(--blue);border-radius:12px;padding:15px}} .stage strong{{display:block;font-size:1.35rem}} .stage small{{color:var(--muted)}} .callout{{border-left:6px solid var(--amber);margin:18px 0}} .callout.good{{border-left-color:var(--green)}} .cases{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} code{{font-size:.9em;background:#edf1f7;padding:.1em .3em;border-radius:4px}} ul{{padding-left:1.3rem}} @media(max-width:760px){{.pipeline,.cases{{grid-template-columns:1fr}} table{{font-size:.88rem}} th,td{{padding:8px 6px}}}}
</style></head><body><main>
<section class="hero"><div class="eyebrow">Pi Fabric · compact-return telemetry · full 36v2</div><h1>Better than stock Fabric. Not yet better than vanilla Pi.</h1><p>Compact-return is the stronger Fabric variant, but vanilla Pi is the fair decision baseline. Against vanilla Pi on the same GPT-5.6 Sol low tasks, compact-return gained only two full solves while using 51% more tokens and costing 38% more.</p><div class="pills"><span class="pill">36 tasks × 3 repetitions</span><span class="pill">GPT-5.6 Sol · low</span><span class="pill">Vanilla Pi is the decision baseline</span></div></section>
<section class="stats"><div class="stat"><strong>{baseline['solves']} → {right['solves']}</strong><span>full solves vs vanilla Pi</span></div><div class="stat"><strong>{fmt_pct(baseline_changes['total_tokens'])}</strong><span>tokens vs vanilla Pi</span></div><div class="stat"><strong>{fmt_pct(baseline_changes['cost_usd'])}</strong><span>cost vs vanilla Pi</span></div><div class="stat"><strong>{fmt_pct(baseline_changes['wall_seconds'])}</strong><span>wall time vs vanilla Pi</span></div></section>
<h2>The fair comparison: vanilla Pi</h2><table><thead><tr><th>Measure</th><th>Vanilla Pi</th><th>Compact-return</th><th>Change</th></tr></thead><tbody>
<tr><th>Full solves</th><td>{baseline['solves']}</td><td>{right['solves']}</td><td><span class="tag good">+{baseline_changes['solves_absolute']}</span></td></tr>
<tr><th>Mean partial reward</th><td>{baseline['mean_partial_reward']:.4f}</td><td>{right['mean_partial_reward']:.4f}</td><td><span class="tag good">+{baseline_changes['partial_absolute']:.4f}</span></td></tr>
{comparison_row('Total tokens', baseline['total_tokens'], right['total_tokens'])}
{comparison_row('Total cost', baseline['cost_usd'], right['cost_usd'], formatter=lambda x:f'${x:,.2f}')}
{comparison_row('Agent wall time', baseline['wall_seconds'], right['wall_seconds'], formatter=lambda x:f'{x/3600:.2f} h')}
</tbody></table>
<p>Compact-return had 16 compact-only solves and 14 baseline-only solves. That +2 net solve difference is not reliable in the paired sample (McNemar p={baseline_quality['exact_mcnemar_pvalue']:.3f}; task-level solve p={baseline_quality['task_sign_flip_solve_pvalue']:.3f}). The partial-reward difference is also uncertain (task-level p={baseline_quality['task_sign_flip_partial_pvalue']:.3f}). The baseline is historical and does not record the newer harness revision field, so this is the intended same-model, same-task, same-repetition comparison rather than a same-launch randomized run.</p>
<section class="callout"><strong>Decision:</strong> on point estimates, both configurations are technically non-dominated: compact-return is slightly higher quality, while vanilla Pi is much cheaper and faster. With the quality difference unproven, vanilla Pi remains the practical default. Compact-return remains the best Fabric variant and a useful research lead.</section>
<h2>The mechanism comparison inside Fabric</h2><div class="pipeline">
<div class="stage"><small>1 · Nested tools</small><strong>{fmt_pct(changes['nested_chars'])}</strong><p>Tool results generated inside QuickJS were nearly unchanged: {fmt_int(left['nested_chars'])} → {fmt_int(right['nested_chars'])} characters.</p></div>
<div class="stage"><small>2 · Sandbox bound</small><strong>0 truncations</strong><p>Raw and sandbox-delivered values were identical in this sample. The nested-result ceiling did no work.</p></div>
<div class="stage"><small>3 · Model-authored return</small><strong>{left['selection_ratio']*100:.1f}% → {right['selection_ratio']*100:.1f}%</strong><p>The model selected a smaller fraction of what it fetched. Net hidden text increased from {fmt_int(left['net_reduction_chars'])} to {fmt_int(right['net_reduction_chars'])} chars.</p></div>
<div class="stage"><small>4 · Visible result</small><strong>{fmt_pct(changes['visible_chars'])}</strong><p>Visible Fabric output fell from {fmt_int(left['visible_chars'])} to {fmt_int(right['visible_chars'])} characters.</p></div></div>
<section class="callout good"><strong>What succeeded:</strong> compact-return changed model behavior at the intended selection seam. Selector-bearing programs rose {left['selector_calls']} → {right['selector_calls']}; the weighted selected-output ratio fell {left['selection_ratio']*100:.1f}% → {right['selection_ratio']*100:.1f}%; and visible output fell 4.8%.</section>
<section class="callout"><strong>Why that did not save tokens:</strong> the model returned {fmt_int(left['visible_chars']-right['visible_chars'])} fewer visible characters but made {right['calls']-left['calls']} more Fabric calls and {right['turns']-left['turns']} more turns. Replaying the accumulated transcript across those extra cycles outweighed the output reduction.</section>
<h2>How the model changed its use of Fabric</h2><table><thead><tr><th>Behavior</th><th>Control</th><th>Compact</th><th>Change</th></tr></thead><tbody>
{comparison_row('Fabric calls', left['calls'], right['calls'])}
{comparison_row('Turns', left['turns'], right['turns'])}
{comparison_row('TypeScript argument chars', left['code_chars'], right['code_chars'])}
{comparison_row('TypeScript chars per call', left['code_chars_per_call'], right['code_chars_per_call'], formatter=lambda x:f'{x:,.1f}')}
{comparison_row('Promise.all programs', left['promise_all_calls'], right['promise_all_calls'])}
{comparison_row('Selector-bearing programs', left['selector_calls'], right['selector_calls'])}
{comparison_row('Whole-file reads', left['whole_file_reads'], right['whole_file_reads'])}
{comparison_row('Exact cross-call rereads', left['exact_rereads'], right['exact_rereads'])}
{comparison_row('Fabric error results', left['error_results'], right['error_results'])}
</tbody></table>
<p>The compact prompt explicitly encouraged one-program composition, yet observed <code>Promise.all</code> programs fell by half while selector-heavy programs rose 75%. The model used JavaScript more often to trim or inspect values, but not to keep the overall reasoning loop inside one Fabric call.</p>
<h3>Nested operation mix</h3><table><thead><tr><th>Operation</th><th>Control</th><th>Compact</th><th>Change</th></tr></thead><tbody>{operation_rows}</tbody></table>
<p>Reads and searches both fell, while write operations increased. Whole-file reads were {left['whole_file_reads']/left['operation_counts']['pi.read']*100:.1f}% of control reads and {right['whole_file_reads']/right['operation_counts']['pi.read']*100:.1f}% under compact-return. Exact rereads were nearly flat in absolute count ({left['exact_rereads']} → {right['exact_rereads']}). The full sample does not support the exploratory 12v2 claim that extra broad reading was the main cause.</p>
<h2>Where the token increase came from</h2><div class="stats"><div class="stat"><strong>{fmt_int(token_parts['cache_read'])}</strong><span>additional cache-read tokens</span></div><div class="stat"><strong>{fmt_int(token_parts['input'])}</strong><span>input-token change</span></div><div class="stat"><strong>{fmt_int(token_parts['output'])}</strong><span>output-token change</span></div><div class="stat"><strong>{fmt_int(token_parts['total'])}</strong><span>total-token change</span></div></div>
<p>Cache reads account for more than the net increase because direct input tokens fell. Across the {left['runs']} paired cells, cache-token delta correlates <strong>r={summary['correlations_with_token_delta']['cache_delta']:.3f}</strong> with total-token delta; call delta is <strong>r={summary['correlations_with_token_delta']['call_delta']:.3f}</strong>, visible-result delta <strong>r={summary['correlations_with_token_delta']['visible_delta']:.3f}</strong>, and exact-reread delta <strong>r={summary['correlations_with_token_delta']['reread_delta']:.3f}</strong>.</p>
<section class="callout"><strong>Mechanism:</strong> hidden intermediate results do not themselves enter the provider transcript. But every additional outer call adds TypeScript arguments and a visible result, then the next completion rereads the accumulated conversation. Compact-return improved the local return boundary while adding outer cycles.</section>
<h2>Within Fabric, quality moved in the promising direction</h2><div class="stats"><div class="stat"><strong>{left['solves']} → {right['solves']}</strong><span>full solves (+9)</span></div><div class="stat"><strong>{left['mean_partial_reward']:.4f} → {right['mean_partial_reward']:.4f}</strong><span>mean partial reward</span></div><div class="stat"><strong>{quality['treatment_only_solves']} vs {quality['control_only_solves']}</strong><span>compact-only vs control-only solves</span></div><div class="stat"><strong>p={quality['exact_mcnemar_pvalue']:.3f}</strong><span>paired-cell exact solve test</span></div></div>
<p>Compact-return produced nine more full solves: +8.3 percentage points, or +19.6% relative. Mean partial reward improved only 0.00125 because both configs were already near 0.98. The direction is encouraging, but uncertainty remains: paired-cell McNemar p={quality['exact_mcnemar_pvalue']:.3f}; task-level sign-flip p={quality['task_sign_flip_solve_pvalue']:.3f} for solves and p={quality['task_sign_flip_partial_pvalue']:.3f} for partial reward.</p>
<h2>Matched trajectories show both directions</h2><div class="cases">{render_case(summary,'regression_case','Regression: filtering without convergence')}{render_case(summary,'win_case','Win: fewer calls and less evidence')}</div>
<p>In the largest regression, <code>{esc(regression['task'])}/rep{regression['rep']}</code>, compact-return made {regression_right['calls']-regression_left['calls']} more calls and added {fmt_int(regression_right['cache_tokens']-regression_left['cache_tokens'])} cache-read tokens. In the largest win, <code>{esc(win['task'])}/rep{win['rep']}</code>, it made {win_left['calls']-win_right['calls']} fewer calls and saved {fmt_int(win_left['cache_tokens']-win_right['cache_tokens'])} cache-read tokens. The differentiator remained outer-call convergence, not merely one return's size.</p>
<h2>What this says about Pi Fabric</h2><ul><li><strong>Fabric can compress tool evidence.</strong> The treatment returned 4.8% less visible tool text from almost the same nested-result volume.</li><li><strong>The sandbox is not an LLM.</strong> It can filter, branch, and aggregate structurally, but semantic coding decisions still require outer model turns. Asking for compact output does not automatically consolidate those decisions.</li><li><strong>The persistent cost mechanism is outer-call replay.</strong> Cache reads added 2.72M tokens even while direct input and visible Fabric output fell.</li><li><strong>The instruction split behavior.</strong> Selector use rose sharply, but <code>Promise.all</code> use halved and outer calls increased. The model followed the compact-return request better than the one-program-composition request.</li></ul>
<section class="callout good"><strong>Fabric-only bottom line:</strong> compact-return achieved its immediate objective and improved on stock Fabric for almost no added dollar cost. Against vanilla Pi, however, the quality gain is too uncertain to justify 38% more cost today. The next experiment should preserve evidence filtering while restoring one-program batching and outer-call convergence.</section>
<h2>Evidence boundaries</h2><ul><li>This is the completed 36-task decision sample with three repetitions per task and config.</li><li>Telemetry measures serialized result sizes, selection, and returned text—not semantic usefulness of each byte.</li><li>No nested result hit the configured nested-result truncation path in this sample.</li><li>Visible output is read from native Pi sessions because telemetry snapshots can precede later error/media replacement text.</li><li>Each config had exactly {left['preexecution_validation_failures']} schema-validation failures before Fabric execution; these are counted as issued calls but correctly have no execution telemetry.</li><li>Correlations localize the mechanism but do not prove mediation. The controlled intervention changed only the compact-return guidance; normal model sampling still introduces run-to-run variation.</li></ul>
</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    summary = build_summary(arguments.results_root)
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    (arguments.output_dir / "mechanism-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    (arguments.output_dir / "index.html").write_text(render(summary))
    print(json.dumps({"status": "ok", "output": str(arguments.output_dir)}))


if __name__ == "__main__":
    main()
