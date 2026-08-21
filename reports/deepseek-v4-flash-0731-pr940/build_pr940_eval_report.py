#!/usr/bin/env python3
"""Build the PR 940 DeepSeek V4 Flash 0731 evaluation report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
REPO_ROOT = REPORT_DIR.parents[1]
RESULTS_ROOT = REPO_ROOT / "results"
TASK_COUNT = 12

API_RESULT_ROOT = (
    RESULTS_ROOT
    / "deepseek-v4-flash-0731/max/baseline-openrouter-deepseek-v4-flash-0731@1.0.0"
)
LOCAL_LOW_RESULT_ROOT = (
    RESULTS_ROOT
    / "deepseek-v4-flash-0731-q8-fast-prefill/low/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0"
)
LOCAL_MAX_RESULT_ROOT = (
    RESULTS_ROOT
    / "deepseek-v4-flash-0731-q8-fast-prefill/max/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0"
)

API_STATUS_PATH = (
    RESULTS_ROOT
    / "_runs/openrouter-dsv4f0731-max-12v2-r3-w12--44426a8110ec43b3bf451fb32ccf8c92a0aa7ef9746151d495d9ec274bb34c99/status.json"
)
LOCAL_LOW_STATUS_PATH = (
    RESULTS_ROOT
    / "_runs/llamacpp-dsv4f0731-iq2xxs-low-12v2-r1-w1--1a2d2f151960b5da19fdb8c9e321379c77816aa59a8497045127addddf135953/status.json"
)
LOCAL_MAX_STATUS_PATH = (
    RESULTS_ROOT
    / "_runs/llamacpp-dsv4f0731-iq2xxs-max-12v2-r1-w1-3h--f6903264dffcb9ebce20a17edbcdad68903e8b471ca57d08afe071dd39df9ce1/status.json"
)

COMPARISON_SPECS = [
    {
        "key": "api_max",
        "label": "DeepSeek V4 Flash 0731 API",
        "role": "OpenRouter API",
        "result_root": API_RESULT_ROOT,
        "status_path": API_STATUS_PATH,
        "workers": 12,
        "canonical": True,
    },
    {
        "key": "local_low",
        "label": "DeepSeek V4 Flash 0731 IQ2_XXS",
        "role": "Local llama.cpp run · low reasoning",
        "result_root": LOCAL_LOW_RESULT_ROOT,
        "status_path": LOCAL_LOW_STATUS_PATH,
        "workers": 1,
        "canonical": True,
    },
    {
        "key": "local_max",
        "label": "DeepSeek V4 Flash 0731 IQ2_XXS",
        "role": "Local llama.cpp run · max reasoning",
        "result_root": LOCAL_MAX_RESULT_ROOT,
        "status_path": LOCAL_MAX_STATUS_PATH,
        "workers": 1,
        "canonical": True,
    },
    {
        "key": "qwen36",
        "label": "Qwen3.6 27B AWQ",
        "role": "Older local-model result",
        "result_root": RESULTS_ROOT
        / "Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b",
        "status_path": None,
        "workers": None,
        "canonical": False,
    },
    {
        "key": "thinkingcap",
        "label": "ThinkingCap Qwen3.6 27B",
        "role": "Older local-model result",
        "result_root": RESULTS_ROOT
        / "thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0",
        "status_path": RESULTS_ROOT
        / "_runs/thinkingcap-qwen36-high-baseline-12v2-r3-w2--f7e37b79a65eca1f42896fff9c5800cf968988791cbf9cd61845b48607bc9f5c/status.json",
        "workers": 2,
        "canonical": True,
    },
    {
        "key": "agentworld",
        "label": "Qwen AgentWorld 35B A3B",
        "role": "Older local-model result",
        "result_root": RESULTS_ROOT
        / "qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0",
        "status_path": RESULTS_ROOT
        / "_runs/qwen-agentworld-35b-high-baseline-12v2-r3-w4--baf0b1a25d28c42ca27e320876e7946b8d4168eea03d9e952b23c56603c1ae40/status.json",
        "workers": 4,
        "canonical": True,
    },
    {
        "key": "gemma4",
        "label": "Gemma 4 31B",
        "role": "Older local-model result",
        "result_root": RESULTS_ROOT / "gemma-4-31b/high/baseline-gemma4-31b@1.0.0",
        "status_path": RESULTS_ROOT
        / "_runs/gemma4-31b-high-12v2-r3-w2--62f5bb098c6f4fd8f8fbb8c059ed5241eff31cd4ded716ce041aeb2847beb4f1/status.json",
        "workers": 2,
        "canonical": True,
    },
]

REASONING_DELIVERY_EVIDENCE = [
    {
        "subject": "DeepSeek V4 Flash 0731 API",
        "reasoning": "max",
        "request_marker": 'reasoning={"effort":"max"}; provider.quantizations=["fp8"]; allow_fallbacks=false',
        "path": "results/deepseek-v4-flash-0731/max/baseline-openrouter-deepseek-v4-flash-0731@1.0.0/adaptix-name-mapping-aliases/rep0/initial_context/provider_request_0001.json",
    },
    {
        "subject": "Local IQ2_XXS + Q8 KV",
        "reasoning": "low",
        "request_marker": 'chat_template_kwargs={"enable_thinking":true,"reasoning_effort":"low"}',
        "path": "results/deepseek-v4-flash-0731-q8-fast-prefill/low/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0/adaptix-name-mapping-aliases/rep0/initial_context/provider_request_0001.json",
    },
    {
        "subject": "Local IQ2_XXS + Q8 KV",
        "reasoning": "max",
        "request_marker": 'chat_template_kwargs={"enable_thinking":true,"reasoning_effort":"max"}',
        "path": "results/deepseek-v4-flash-0731-q8-fast-prefill/max/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0/dateutil-rfc5545-timezone-interop/rep0/initial_context/provider_request_0001.json",
    },
]

BENCHLOCAL_EVIDENCE = [
    {
        "label": "DeepSeek IQ2_XXS fork",
        "mode": "thinking low",
        "score": 121,
        "total": 150,
        "source": "https://github.com/noonghunna/club-3090/pull/940",
        "note": "Exact PR profile",
    },
    {
        "label": "DeepSeek IQ2_XXS fork",
        "mode": "thinking max",
        "score": 123,
        "total": 150,
        "source": "https://github.com/noonghunna/club-3090/pull/940",
        "note": "Exact PR profile; four of 226 responses reached the 65,536-token cap",
    },
    {
        "label": "DeepSeek IQ2_XXS stock b10200",
        "mode": "thinking low",
        "score": 122,
        "total": 150,
        "source": "https://github.com/noonghunna/club-3090/pull/940",
        "note": "Same weights and Q8 cache",
    },
    {
        "label": "ThinkingCap Qwen3.6 27B",
        "mode": "thinking on",
        "score": 120,
        "total": 150,
        "source": "https://github.com/noonghunna/club-3090/blob/master/models/thinkingcap-27b/README.md",
        "note": "Published club-3090 8-pack",
    },
    {
        "label": "Qwen3.6 27B fast tier",
        "mode": "published tier score",
        "score": 109,
        "total": 150,
        "source": "https://github.com/noonghunna/club-3090/blob/master/models/thinkingcap-27b/README.md",
        "note": "README comparison; mode is not stated there",
    },
    {
        "label": "Qwen AgentWorld 35B BF16 baseline",
        "mode": "thinking on",
        "score": 125,
        "total": 150,
        "source": "https://github.com/noonghunna/club-3090/blob/master/models/qwen-agentworld-35b-a3b/vllm/compose/dual/cyankiwi-awq-int4/fp8.yml",
        "note": "BF16 baseline, not the exact AWQ DeepSWE subject; exact AWQ quick gate was 29/30",
    },
]


@dataclass
class ComparisonMetrics:
    key: str
    label: str
    role: str
    model: str
    thinking: str
    subject_version: str
    result_root: str
    completed_cells: int
    completed_tasks: int
    planned_tasks: int
    reps: int
    status_state: str | None
    status_stage: str | None
    status_counts: dict[str, Any] | None
    normalized_solves: float
    solve_denominator: int
    positive_trajectories: int
    negative_trajectories: int
    unique_tasks_solved: int
    rep_solve_counts: list[int]
    partial_mean: float | None
    f2p_mean: float | None
    f2p_n: int
    p2p_mean: float | None
    p2p_n: int
    net_tokens_per_12: float
    agent_hours_per_12: float
    mean_cell_minutes: float
    timeouts: int
    calendar_hours: float | None
    workers: int | None
    canonical: bool
    task_revisions: list[str]
    complete: bool


def read_json(path: Path) -> dict[str, Any]:
    """Read one JSON object from a benchmark artifact."""
    return json.loads(path.read_text())


def parse_utc_timestamp(value: str) -> datetime:
    """Parse a benchmark UTC timestamp ending in Z."""
    return datetime.fromisoformat(value)


def validate_reasoning_delivery_evidence() -> None:
    """Require captured provider requests to contain the reported reasoning levels."""
    for evidence in REASONING_DELIVERY_EVIDENCE:
        request = read_json(REPO_ROOT / evidence["path"])
        if evidence["subject"].endswith("API"):
            delivered_reasoning = request["reasoning"]["effort"]
        else:
            delivered_reasoning = request["chat_template_kwargs"]["reasoning_effort"]
        if delivered_reasoning != evidence["reasoning"]:
            raise RuntimeError(
                "PR 940 reasoning delivery mismatch: "
                f"expected {evidence['reasoning']} at {evidence['path']}, "
                f"found {delivered_reasoning}"
            )


def discover_comparison_tasks() -> list[str]:
    """Use the completed dated API baseline to define the canonical 12_v2 tasks."""
    tasks = sorted(
        task_dir.name
        for task_dir in API_RESULT_ROOT.iterdir()
        if task_dir.is_dir() and any(task_dir.glob("rep*/result.json"))
    )
    if len(tasks) != TASK_COUNT:
        raise RuntimeError(
            f"PR 940 report expected {TASK_COUNT} API tasks, found {len(tasks)}"
        )
    return tasks


def collect_result_rows(result_root: Path, tasks: list[str]) -> list[dict[str, Any]]:
    """Collect result rows restricted to the canonical 12_v2 task set."""
    rows: list[dict[str, Any]] = []
    for task in tasks:
        for result_path in sorted((result_root / task).glob("rep*/result.json")):
            result = read_json(result_path)
            rows.append(
                {
                    "task": task,
                    "rep": result_path.parent.name,
                    "path": str(result_path.relative_to(REPO_ROOT)),
                    "result": result,
                }
            )
    return rows


def optional_mean(values: list[float]) -> float | None:
    """Return the arithmetic mean when at least one value exists."""
    return mean(values) if values else None


def collect_status_metadata(
    status_path: Path | None,
) -> tuple[dict[str, Any] | None, float | None]:
    """Read structured run state and derive calendar elapsed hours."""
    if status_path is None or not status_path.exists():
        return None, None
    status = read_json(status_path)
    started_at = status.get("started_at")
    updated_at = status.get("updated_at")
    calendar_hours = None
    if started_at and updated_at:
        calendar_hours = (
            parse_utc_timestamp(updated_at) - parse_utc_timestamp(started_at)
        ).total_seconds() / 3600
    return status, calendar_hours


def build_comparison_metrics(
    spec: dict[str, Any], tasks: list[str]
) -> tuple[ComparisonMetrics, list[dict[str, Any]]]:
    """Normalize one repeated benchmark config to a 12-task analytical pass."""
    rows = collect_result_rows(spec["result_root"], tasks)
    if not rows:
        raise RuntimeError(f"PR 940 report found no results for {spec['label']}")

    reps = sorted({row["rep"] for row in rows})
    rep_count = len(reps)
    results = [row["result"] for row in rows]
    positive_rows = [
        row for row in rows if float(row["result"].get("reward_binary") or 0) == 1
    ]
    negative_rows = [
        row for row in rows if float(row["result"].get("reward_binary") or 0) < 0
    ]
    f2p_values = [
        float(result["f2p"]) for result in results if result.get("f2p") is not None
    ]
    p2p_values = [
        float(result["p2p"]) for result in results if result.get("p2p") is not None
    ]
    partial_values = [
        float(result["reward_partial"])
        for result in results
        if result.get("reward_partial") is not None
    ]
    status, calendar_hours = collect_status_metadata(spec["status_path"])
    completed_tasks = len({row["task"] for row in rows})
    complete = completed_tasks == TASK_COUNT and len(rows) == TASK_COUNT * rep_count

    metrics = ComparisonMetrics(
        key=spec["key"],
        label=spec["label"],
        role=spec["role"],
        model=next(iter({str(result.get("model")) for result in results})),
        thinking=next(iter({str(result.get("thinking_level")) for result in results})),
        subject_version=next(
            iter({str(result.get("subject_version")) for result in results})
        ),
        result_root=str(spec["result_root"].relative_to(REPO_ROOT)),
        completed_cells=len(rows),
        completed_tasks=completed_tasks,
        planned_tasks=TASK_COUNT,
        reps=rep_count,
        status_state=status.get("state") if status else None,
        status_stage=status.get("stage") if status else None,
        status_counts=status.get("counts") if status else None,
        normalized_solves=len(positive_rows) / rep_count,
        solve_denominator=TASK_COUNT,
        positive_trajectories=len(positive_rows),
        negative_trajectories=len(negative_rows),
        unique_tasks_solved=len({row["task"] for row in positive_rows}),
        rep_solve_counts=[
            sum(1 for row in positive_rows if row["rep"] == rep) for rep in reps
        ],
        partial_mean=optional_mean(partial_values),
        f2p_mean=optional_mean(f2p_values),
        f2p_n=len(f2p_values),
        p2p_mean=optional_mean(p2p_values),
        p2p_n=len(p2p_values),
        net_tokens_per_12=sum(
            int(result.get("input_tokens") or 0) + int(result.get("output_tokens") or 0)
            for result in results
        )
        / rep_count,
        agent_hours_per_12=sum(
            float(result.get("agent_wall_s") or 0) for result in results
        )
        / rep_count
        / 3600,
        mean_cell_minutes=mean(
            float(result.get("agent_wall_s") or 0) for result in results
        )
        / 60,
        timeouts=sum(bool(result.get("agent_timed_out")) for result in results),
        calendar_hours=calendar_hours,
        workers=spec["workers"],
        canonical=spec["canonical"],
        task_revisions=sorted({str(result.get("task_revision")) for result in results}),
        complete=complete,
    )
    return metrics, rows


def format_decimal(value: float | None, digits: int = 3) -> str:
    """Format an optional decimal for report tables."""
    return "—" if value is None else f"{value:.{digits}f}"


def format_percent(value: float | None) -> str:
    """Format an optional score as a percentage."""
    return "—" if value is None else f"{value:.1%}"


def format_hours(value: float | None) -> str:
    """Format optional hours as a compact duration."""
    if value is None:
        return "—"
    total_minutes = round(value * 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes:02d}m"


def build_task_matrix(
    tasks: list[str], rows_by_key: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Build complete task-by-config solve counts for the report denominator."""
    matrix = []
    for task in tasks:
        task_row: dict[str, Any] = {"task": task}
        for key, rows in rows_by_key.items():
            matching = [row for row in rows if row["task"] == task]
            task_row[key] = {
                "positive": sum(
                    float(row["result"].get("reward_binary") or 0) == 1
                    for row in matching
                ),
                "negative": sum(
                    float(row["result"].get("reward_binary") or 0) < 0
                    for row in matching
                ),
                "cells": len(matching),
            }
        matrix.append(task_row)
    return matrix


def render_metric_row(metrics: ComparisonMetrics) -> str:
    """Render one normalized DeepSWE comparison table row."""
    solve_text = (
        f"{metrics.normalized_solves:.1f} / {TASK_COUNT}"
        if metrics.complete
        else f"{metrics.positive_trajectories} / {metrics.completed_tasks} provisional"
    )
    rep_text = ", ".join(str(value) for value in metrics.rep_solve_counts)
    status = (
        "complete"
        if metrics.complete
        else f"{metrics.completed_tasks}/{TASK_COUNT} tasks"
    )
    canonical_note = (
        "" if metrics.canonical else '<span class="pill caution">older result</span>'
    )
    return f"""
      <tr>
        <td><strong>{escape(metrics.label)}</strong><br><span class="muted">{escape(metrics.role)} · {escape(metrics.model)}</span>{canonical_note}</td>
        <td><span class="pill neutral">{escape(metrics.thinking)}</span></td>
        <td>{metrics.reps}</td>
        <td><strong>{solve_text}</strong><br><span class="muted">solves by pass: {escape(rep_text)}</span></td>
        <td>{format_percent(metrics.f2p_mean)} <span class="muted">{metrics.f2p_n} graded</span></td>
        <td>{format_percent(metrics.p2p_mean)} <span class="muted">{metrics.p2p_n} graded</span></td>
        <td>{format_decimal(metrics.partial_mean)}</td>
        <td>{metrics.net_tokens_per_12 / 1_000_000:.2f}M</td>
        <td>{format_hours(metrics.agent_hours_per_12)}</td>
        <td>{metrics.mean_cell_minutes:.1f}m</td>
        <td>{escape(status)}</td>
      </tr>"""


def render_task_matrix_row(task_row: dict[str, Any], keys: list[str]) -> str:
    """Render one complete-denominator task matrix row."""
    cells = []
    for key in keys:
        value = task_row[key]
        text = f"{value['positive']}/{value['cells']}"
        class_name = "good-cell" if value["positive"] else "bad-cell"
        if value["cells"] == 0:
            text = "pending"
            class_name = "pending-cell"
        cells.append(f'<td class="{class_name}">{text}</td>')
    return f"<tr><td>{escape(task_row['task'])}</td>{''.join(cells)}</tr>"


def render_reasoning_delivery_row(row: dict[str, Any]) -> str:
    """Render one captured reasoning-request marker."""
    return f"""
      <tr>
        <td>{escape(row["subject"])}</td>
        <td><span class="pill neutral">{escape(row["reasoning"])}</span></td>
        <td><code>{escape(row["request_marker"])}</code></td>
        <td><span class="muted">{escape(row["path"])}</span></td>
      </tr>"""


def render_benchlocal_row(row: dict[str, Any]) -> str:
    """Render one sourced benchlocal quality score."""
    percent = row["score"] / row["total"] * 100
    return f"""
      <tr>
        <td>{escape(row["label"])}</td>
        <td>{escape(row["mode"])}</td>
        <td><strong>{row["score"]} / {row["total"]}</strong> ({percent:.1f}%)</td>
        <td>{escape(row["note"])}</td>
        <td><a href="{escape(row["source"])}">source</a></td>
      </tr>"""


def render_pr_update_draft(metrics_by_key: dict[str, ComparisonMetrics]) -> str:
    """Render the plain-language PR update."""
    api = metrics_by_key["api_max"]
    local_low = metrics_by_key["local_low"]
    local_max = metrics_by_key["local_max"]
    max_status = (
        f"{local_max.normalized_solves:.1f}/12"
        if local_max.complete
        else f"{local_max.positive_trajectories}/{local_max.completed_tasks} so far"
    )
    low_speed_ratio = local_low.mean_cell_minutes / api.mean_cell_minutes
    max_speed_ratio = local_max.mean_cell_minutes / api.mean_cell_minutes
    max_token_ratio = local_max.net_tokens_per_12 / api.net_tokens_per_12
    max_token_text = (
        f"{local_max.net_tokens_per_12 / 1_000_000:.2f}M"
        if local_max.complete
        else f"{local_max.net_tokens_per_12 / 1_000_000:.2f}M across {local_max.completed_tasks} finished tasks"
    )
    max_agent_time_text = (
        format_hours(local_max.agent_hours_per_12)
        if local_max.complete
        else f"{format_hours(local_max.agent_hours_per_12)} across {local_max.completed_tasks} finished tasks"
    )
    if local_max.complete:
        opening = f"""The local IQ2_XXS model solved **{local_max.normalized_solves:.0f} of 12 coding tasks** at max reasoning. The API averaged **{api.normalized_solves:.1f} of 12** at the same reasoning level across three passes.

The local result is inside the API's observed range of 5–6 solves and slightly above its average. That is strong evidence that the quantized model kept its coding ability, but one local pass is not enough to prove parity."""
        max_speed_note = f"The local max pass took {format_hours(local_max.calendar_hours)} from start to finish, including the unrelated host-memory pause. The tasks themselves used {format_hours(local_max.agent_hours_per_12)}, or {local_max.mean_cell_minutes:.1f} minutes each—{max_speed_ratio:.1f}× slower than the API. It used {max_token_ratio:.2f}× as many non-cached tokens. One task timed out."
        takeaway = "The PR's quality claim holds up: the patched server scored almost exactly like stock on benchlocal, and the local 2-bit model matched the API's coding-task range at max reasoning. The remaining cost is speed and verbosity, not an obvious loss of capability. I would still avoid claiming proven parity because the local result has one pass while the API has three."
    else:
        opening = f"""The local IQ2_XXS model solved **5 of 12 coding tasks** at low reasoning. The API averaged **{api.normalized_solves:.1f} of 12** at max reasoning across three passes.

This is a strong local result, but not proof of API parity. The local model ran once and used a lower reasoning level."""
        max_speed_note = "The local max pass is still running. Its wall-clock time includes a pause caused by an unrelated process exhausting host memory, so the final comparison should use task time instead of total elapsed time."
        takeaway = "The PR's narrow quality claim holds up: the patched server scored almost exactly like stock on benchlocal, and the local 2-bit model solved real repository tasks. I would not claim API parity yet. The local low result is one pass at a different reasoning level, and the max run is unfinished."
    return f"""## DeepSWE results for local DeepSeek V4 Flash 0731

{opening}

### How I counted the API result

Each pass uses the same 12 tasks. The API ran three passes and produced {api.positive_trajectories} full solves, so the average is {api.positive_trajectories} ÷ 3 = **{api.normalized_solves:.1f} solves per 12-task pass**. The three passes solved {", ".join(str(value) for value in api.rep_solve_counts)} tasks. One other API result had a negative reward; I list it separately instead of subtracting it from the solve count.

| Run | Reasoning | Passes | Full solves per 12 tasks | Feature tests passed | Existing tests kept passing | Average score | Tokens per pass | Agent time per pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| API | `max` | 3 | **{api.normalized_solves:.1f}/12** | {format_percent(api.f2p_mean)} | {format_percent(api.p2p_mean)} | {api.partial_mean:.3f} | {api.net_tokens_per_12 / 1_000_000:.2f}M | {format_hours(api.agent_hours_per_12)} |
| Local IQ2_XXS | `low` | 1 | **{local_low.normalized_solves:.0f}/12** | {format_percent(local_low.f2p_mean)} | {format_percent(local_low.p2p_mean)} | {local_low.partial_mean:.3f} | {local_low.net_tokens_per_12 / 1_000_000:.2f}M | {format_hours(local_low.agent_hours_per_12)} |
| Local IQ2_XXS | `max` | 1 | **{max_status}** | {format_percent(local_max.f2p_mean)} | {format_percent(local_max.p2p_mean)} | {local_max.partial_mean:.3f} | {max_token_text} | {max_agent_time_text} |

“Feature tests passed” measures whether the model implemented the requested change. “Existing tests kept passing” measures whether it broke working code. Token totals exclude cached input.

### Setup and speed

- All three runs used Pi `0.84.0`.
- The API used max reasoning, DeepSeek's FP8 endpoint, and no fallback provider.
- The local runs used low and max reasoning as shown above.
- The API finished 36 attempts in {format_hours(api.calendar_hours)} with 12 workers. Its average task took {api.mean_cell_minutes:.1f} minutes.
- The local low pass used one worker. It took {format_hours(local_low.calendar_hours)}, or {local_low.mean_cell_minutes:.1f} minutes per task—{low_speed_ratio:.1f}× slower than the API.
- {max_speed_note}

### Compared with other local models

These runs use the same 12 tasks. The older models ran three passes each; local DeepSeek ran once.

| Local model | Reasoning | Passes | Full solves per 12 tasks | Feature tests passed | Existing tests kept passing |
|---|---|---:|---:|---:|---:|
| DeepSeek IQ2_XXS | `max` | 1 | **{local_max.normalized_solves:.1f}/12** | {format_percent(local_max.f2p_mean)} | {format_percent(local_max.p2p_mean)} |
| DeepSeek IQ2_XXS | `low` | 1 | **{local_low.normalized_solves:.1f}/12** | {format_percent(local_low.f2p_mean)} | {format_percent(local_low.p2p_mean)} |
| Qwen3.6 27B AWQ | `high` | 3 | **{metrics_by_key["qwen36"].normalized_solves:.1f}/12** | {format_percent(metrics_by_key["qwen36"].f2p_mean)} | {format_percent(metrics_by_key["qwen36"].p2p_mean)} |
| ThinkingCap Qwen3.6 27B | `high` | 3 | **{metrics_by_key["thinkingcap"].normalized_solves:.1f}/12** | {format_percent(metrics_by_key["thinkingcap"].f2p_mean)} | {format_percent(metrics_by_key["thinkingcap"].p2p_mean)} |
| Qwen AgentWorld 35B A3B | `high` | 3 | **{metrics_by_key["agentworld"].normalized_solves:.1f}/12** | {format_percent(metrics_by_key["agentworld"].f2p_mean)} | {format_percent(metrics_by_key["agentworld"].p2p_mean)} |
| Gemma 4 31B | `high` | 3 | **{metrics_by_key["gemma4"].normalized_solves:.1f}/12** | {format_percent(metrics_by_key["gemma4"].f2p_mean)} | {format_percent(metrics_by_key["gemma4"].p2p_mean)} |

ThinkingCap solved one of its 36 attempts, which works out to 0.3 solves per 12-task pass. Qwen3.6, AgentWorld, and Gemma had no full solves. Qwen3.6's older result does not record the current task revision, so treat that row as a rough comparison.

### What benchlocal tells us

The patched DeepSeek server scored 121/150 at low reasoning and 123/150 at max. Stock `b10200` scored 122/150 at low. That is good evidence that the server changes did not damage the model.

The published benchlocal scores for these strong local models sit in a narrow range: Qwen3.6 has 109/150, ThinkingCap has 120/150, and the AgentWorld BF16 reference has 125/150. DeepSWE separates them much more sharply. This suggests benchlocal is becoming saturated as a model-ranking test. It is still useful as a quick check that a server works correctly.

Gemma 4 has no published full 8-pack score, so I left it out of that comparison. The exact AgentWorld AWQ profile has only a 29/30 quick check; 125/150 comes from its BF16 reference.

### Takeaway

{takeaway}
"""


def render_html_report(
    metrics: list[ComparisonMetrics],
    task_matrix: list[dict[str, Any]],
) -> str:
    """Render the self-contained PR 940 evaluation report."""
    metrics_by_key = {item.key: item for item in metrics}
    api = metrics_by_key["api_max"]
    local_low = metrics_by_key["local_low"]
    local_max = metrics_by_key["local_max"]
    comparison_keys = [item.key for item in metrics]
    max_verdict = (
        f"{local_max.normalized_solves:.1f}/12 final"
        if local_max.complete
        else f"{local_max.positive_trajectories}/{local_max.completed_tasks} provisional"
    )
    if local_max.complete:
        hero_title = f"The local 2-bit model solved {local_max.normalized_solves:.0f} of 12 coding tasks."
        hero_copy = f"The API averaged {api.normalized_solves:.1f} solves on the same tasks at max reasoning. The local result is inside the API's observed 5–6 solve range, but it comes from one pass instead of three."
        speed_copy = f"The local max model took {local_max.mean_cell_minutes / api.mean_cell_minutes:.1f}× longer per task than the API and used {local_max.net_tokens_per_12 / api.net_tokens_per_12:.2f}× as many non-cached tokens. It finished in {format_hours(local_max.calendar_hours)} elapsed, including a pause caused by an unrelated process exhausting host memory; the tasks themselves used {format_hours(local_max.agent_hours_per_12)}."
        task_copy = "Each cell shows solves / attempts. All runs are complete."
        bottom_copy = "The patched server scored almost exactly like stock on benchlocal, and the local 2-bit model landed inside the API's coding-task range at max reasoning. That supports the PR's quality claim. The main remaining costs are speed and token use. One local pass is not enough to prove parity with a three-pass API average."
    else:
        hero_title = "The local 2-bit model solved 5 of 12 coding tasks."
        hero_copy = f"The API averaged {api.normalized_solves:.1f} solves on the same 12 tasks. The low-reasoning local result is promising; the max-reasoning pass is still running."
        speed_copy = f"The local low model took {local_low.mean_cell_minutes / api.mean_cell_minutes:.1f}× longer per task than the API. Do not compare only total elapsed time: the API ran 12 tasks at once, while the local server handled one."
        task_copy = "Each cell shows solves / attempts. The unfinished local max pass shows pending tasks."
        bottom_copy = "The patched server scored almost exactly like stock on benchlocal, and the local 2-bit model solved real repository tasks. That supports the PR's quality claim, but the max-reasoning comparison is not finished."
    task_headers = "".join(
        f"<th>{escape(metrics_by_key[key].label)}<br><span class='muted'>{escape(metrics_by_key[key].thinking)}</span></th>"
        for key in comparison_keys
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="icon" href="data:,">
  <title>DeepSeek V4 Flash 0731 benchmark results</title>
  <style>
    :root {{ --bg:#f4f6fa; --surface:#fff; --ink:#172033; --muted:#647087; --blue:#275efe; --green:#18794e; --red:#c53b3b; --amber:#a66000; --line:#dfe4ec; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif; }}
    main {{ max-width:1480px; margin:auto; padding:32px 24px 72px; }}
    .hero {{ color:white; background:linear-gradient(135deg,#101a35,#254fc9); border-radius:24px; padding:36px; box-shadow:0 18px 50px #19327533; }}
    .hero h1 {{ margin:8px 0 10px; font-size:clamp(30px,5vw,56px); line-height:1.03; max-width:1000px; }}
    .eyebrow {{ text-transform:uppercase; letter-spacing:.14em; font-weight:800; opacity:.8; }}
    .hero p {{ max-width:900px; font-size:18px; }}
    .pills {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; }}
    .pill {{ display:inline-block; border-radius:999px; padding:4px 9px; font-size:12px; font-weight:750; vertical-align:middle; margin:2px 0; }}
    .pill.good {{ color:#d9ffed; background:#1e7c57; }} .pill.bad {{ color:#ffe4e4; background:#a82e38; }} .pill.caution {{ color:#6b3a00; background:#ffe0a3; margin-left:6px; }} .pill.neutral {{ color:#17337d; background:#dfe8ff; }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; margin:20px 0; }}
    .stat,.panel {{ background:var(--surface); border:1px solid var(--line); border-radius:18px; box-shadow:0 8px 24px #15234b0c; }}
    .stat {{ padding:20px; }} .stat b {{ display:block; font-size:30px; color:var(--blue); }} .stat span {{ color:var(--muted); }}
    .panel {{ padding:24px; margin-top:18px; overflow:hidden; }} h2 {{ font-size:26px; margin:0 0 12px; }} h3 {{ margin-top:24px; }}
    .callout {{ border-left:5px solid var(--blue); background:#edf2ff; padding:16px 18px; border-radius:10px; margin:18px 0; }}
    .callout.caution {{ border-color:var(--amber); background:#fff5df; }}
    .table-wrap {{ overflow:auto; }} table {{ width:100%; border-collapse:collapse; min-width:1100px; }} th,td {{ padding:11px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} th {{ position:sticky; top:0; background:#f7f9fc; font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:#536079; }}
    .muted {{ color:var(--muted); font-size:12px; }} .good-cell {{ color:var(--green); font-weight:800; }} .bad-cell {{ color:var(--muted); }} .pending-cell {{ color:var(--amber); font-style:italic; }}
    .bar {{ height:10px; background:#e7ebf2; border-radius:999px; overflow:hidden; min-width:130px; }} .bar > i {{ display:block; height:100%; background:var(--blue); }}
    a {{ color:var(--blue); }} code {{ background:#eef1f6; padding:2px 5px; border-radius:5px; }}
    @media (max-width:700px) {{ main {{ padding:16px 12px 48px; }} .hero {{ padding:25px 20px; }} .panel {{ padding:18px 14px; }} }}
  </style>
</head>
<body><main>
  <section class="hero">
    <div class="eyebrow">PR 940 · DeepSeek V4 Flash 0731</div>
    <h1>{escape(hero_title)}</h1>
    <p>{escape(hero_copy)}</p>
    <div class="pills"><span class="pill good">API average: {api.normalized_solves:.1f} / 12</span><span class="pill good">Local low: 5 / 12</span><span class="pill caution">Local max: {escape(max_verdict)}</span><span class="pill neutral">Cached input excluded</span></div>
  </section>

  <section class="stats">
    <div class="stat"><b>{" · ".join(str(value) for value in api.rep_solve_counts)}</b><span>Tasks solved in each API pass</span></div>
    <div class="stat"><b>{local_max.f2p_mean:.1%}</b><span>Feature tests passed by local max</span></div>
    <div class="stat"><b>{api.f2p_mean:.1%}</b><span>Feature tests passed by API max</span></div>
    <div class="stat"><b>{local_max.mean_cell_minutes:.1f}m</b><span>Average local-max time per task</span></div>
  </section>

  <section class="panel">
    <h2>Main results</h2>
    <div class="callout"><strong>How the API average works:</strong> it solved {api.positive_trajectories} attempts across three passes of the same 12 tasks. {api.positive_trajectories} ÷ 3 = <strong>{api.normalized_solves:.1f} solves per pass</strong>. One other API attempt had a negative reward; it is not counted as a solve.</div>
    <div class="table-wrap"><table>
      <thead><tr><th>Run</th><th>Reasoning</th><th>Passes</th><th>Full solves</th><th>Feature tests passed</th><th>Existing tests kept passing</th><th>Average score</th><th>Tokens / pass</th><th>Agent time / pass</th><th>Time / task</th><th>Status</th></tr></thead>
      <tbody>{"".join(render_metric_row(item) for item in metrics)}</tbody>
    </table></div>
    <p>“Feature tests passed” shows how much of the requested change worked. “Existing tests kept passing” shows whether the model broke code that already worked. Token totals exclude cached input.</p>
  </section>

  <section class="panel">
    <h2>Speed</h2>
    <div class="stats">
      <div class="stat"><b>{api.mean_cell_minutes:.1f}m</b><span>Average API time per task</span></div>
      <div class="stat"><b>{local_max.mean_cell_minutes:.1f}m</b><span>Average local-max time per task</span></div>
      <div class="stat"><b>{api.net_tokens_per_12 / 1_000_000:.2f}M</b><span>API tokens per 12 tasks</span></div>
      <div class="stat"><b>{local_max.net_tokens_per_12 / 1_000_000:.2f}M</b><span>Local-max tokens per 12 tasks</span></div>
    </div>
    <p>{escape(speed_copy)}</p>
  </section>

  <section class="panel">
    <h2>Results by task</h2>
    <p>{escape(task_copy)}</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Task</th>{task_headers}</tr></thead>
      <tbody>{"".join(render_task_matrix_row(row, comparison_keys) for row in task_matrix)}</tbody>
    </table></div>
  </section>

  <section class="panel">
    <h2>What the smaller benchlocal test tells us</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Model</th><th>Mode</th><th>Published score</th><th>Notes</th><th>Source</th></tr></thead>
      <tbody>{"".join(render_benchlocal_row(row) for row in BENCHLOCAL_EVIDENCE)}</tbody>
    </table></div>
    <div class="callout caution">The published benchlocal scores bunch together between 109/150 and 125/150. DeepSWE separates the models much more sharply: local DeepSeek max solved {local_max.normalized_solves:.0f}/12 tasks, ThinkingCap solved one attempt across three passes, and Qwen3.6, AgentWorld, and Gemma had no full solves. This suggests benchlocal is becoming saturated as a ranking test. It is still useful for checking that a server works correctly.</div>
    <p class="muted">Gemma 4 has no published full 8-pack score. AgentWorld's 125/150 comes from its BF16 reference; the exact AWQ profile has only a 29/30 quick check.</p>
  </section>

  <section class="panel">
    <h2>Bottom line</h2>
    <p>{escape(bottom_copy)}</p>
    <p><a href="pr-update-draft.md">Read the draft PR update</a> · <a href="comparison.json">Download the numbers</a></p>
    <h3>Technical proof of reasoning settings</h3>
    <p>The captured requests below confirm that the API used max reasoning and the local server received the requested low and max settings.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Run</th><th>Reasoning</th><th>Request field</th><th>Artifact</th></tr></thead>
      <tbody>{"".join(render_reasoning_delivery_row(row) for row in REASONING_DELIVERY_EVIDENCE)}</tbody>
    </table></div>
  </section>
</main></body></html>"""


def main() -> None:
    """Build JSON, HTML, and PR-ready Markdown from current artifacts."""
    validate_reasoning_delivery_evidence()
    tasks = discover_comparison_tasks()
    metrics: list[ComparisonMetrics] = []
    rows_by_key: dict[str, list[dict[str, Any]]] = {}
    for spec in COMPARISON_SPECS:
        comparison_metrics, rows = build_comparison_metrics(spec, tasks)
        metrics.append(comparison_metrics)
        rows_by_key[comparison_metrics.key] = rows

    metrics_by_key = {item.key: item for item in metrics}
    task_matrix = build_task_matrix(tasks, rows_by_key)
    payload = {
        "schema_version": 1,
        "task_count": TASK_COUNT,
        "tasks": tasks,
        "solve_normalization": "positive trajectories divided by repetition count; denominator remains 12 unique tasks",
        "comparisons": [asdict(item) for item in metrics],
        "task_matrix": task_matrix,
        "benchlocal_evidence": BENCHLOCAL_EVIDENCE,
        "reasoning_delivery_evidence": REASONING_DELIVERY_EVIDENCE,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "comparison.json").write_text(json.dumps(payload, indent=2) + "\n")
    (REPORT_DIR / "pr-update-draft.md").write_text(
        render_pr_update_draft(metrics_by_key)
    )
    (REPORT_DIR / "index.html").write_text(render_html_report(metrics, task_matrix))
    print(
        f"Built PR 940 report with {metrics_by_key['local_max'].completed_tasks}/12 local max tasks"
    )


if __name__ == "__main__":
    main()
