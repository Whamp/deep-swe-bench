#!/usr/bin/env python3
"""Build the Qwen-AgentWorld baseline 36_v2 capability report."""

from __future__ import annotations

import argparse
import html
import json
import statistics
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

RUN_ID = "qwen-agentworld-35b-high-baseline-36v2-r3-w4"
CONFIG_IDENTITY = "baseline-qwen-agentworld-35b@1.0.0"
MODEL_LEAF = "qwen-agentworld-35b-a3b"
THINKING_LEVEL = "high"
EXPECTED_RESULTS = 108
BASELINE_PLAN_IDENTITY = (
    "sha256:5b869d3306171a738a4218378977182a232e3e784faafe51571fe80376fa38e3"
)
PI_CHECK_CONFIG = "pi-check@1.3.0"
PI_CHECK_PLAN_IDENTITY = (
    "sha256:319268e4178d267ef3048cecb7e15095b035df9223dc101882b85bc3d3c303fc"
)


def parse_report_arguments() -> argparse.Namespace:
    """Parse canonical result, task, repository, and output locations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--tasks-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("index.html"),
    )
    return parser.parse_args()


def load_subset_tasks(repository_root: Path, subset: str) -> list[str]:
    """Load one named subset in its stable display order."""
    return (repository_root / "subsets" / f"{subset}.txt").read_text().split()


def load_qwen_agentworld_results(
    results_root: Path,
    subset_tasks: list[str],
) -> list[dict[str, Any]]:
    """Load and validate all 108 Qwen-AgentWorld baseline result records."""
    config_root = results_root / MODEL_LEAF / THINKING_LEVEL / CONFIG_IDENTITY
    rows: list[dict[str, Any]] = []
    for result_path in sorted(config_root.glob("*/rep*/result.json")):
        row = json.loads(result_path.read_text())
        row["task"] = result_path.parents[1].name
        row["rep"] = int(result_path.parent.name.removeprefix("rep"))
        row["artifact_root"] = str(result_path.parent)
        rows.append(row)
    expected_cells = {(task, rep) for task in subset_tasks for rep in range(3)}
    actual_cells = {(str(row["task"]), int(row["rep"])) for row in rows}
    if len(rows) != EXPECTED_RESULTS or actual_cells != expected_cells:
        raise ValueError(
            "Qwen-AgentWorld 36_v2 report input invalid: expected the complete "
            f"36-task × 3-rep corpus; found {len(rows)} records"
        )
    return rows


def find_completed_run_status(results_root: Path) -> dict[str, Any]:
    """Load the one completed structured state for the approved 36_v2 run."""
    matches = sorted((results_root / "_runs").glob(f"{RUN_ID}--*/status.json"))
    if len(matches) != 1:
        raise ValueError(
            "Qwen-AgentWorld 36_v2 run state invalid: expected one status file; "
            f"found {len(matches)}"
        )
    status = json.loads(matches[0].read_text())
    if status.get("state") != "completed" or status.get("stage") != "done":
        raise ValueError("Qwen-AgentWorld 36_v2 run state is not completed")
    return status


def numeric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    """Return available numeric values for one result field."""
    return [float(row[key]) for row in rows if isinstance(row.get(key), int | float)]


def mean_value(rows: list[dict[str, Any]], key: str) -> float:
    """Return the arithmetic mean for one result field."""
    values = numeric_values(rows, key)
    return statistics.mean(values) if values else 0.0


def is_invalid(row: dict[str, Any]) -> bool:
    """Identify a rep without a normal strict grade."""
    return row.get("reward_binary") == -1


def weighted_grade(
    rows: list[dict[str, Any]],
    prefix: str,
) -> tuple[int, int, float | None]:
    """Return passed, total, and ratio for F2P or P2P tests."""
    passed = sum(int(row.get(f"{prefix}_passed") or 0) for row in rows)
    total = sum(int(row.get(f"{prefix}_total") or 0) for row in rows)
    return passed, total, passed / total if total else None


def aggregate_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate strict, feature, preservation, validity, and cost evidence."""
    valid_rows = [row for row in rows if not is_invalid(row)]
    f2p = weighted_grade(valid_rows, "f2p")
    p2p = weighted_grade(valid_rows, "p2p")
    return {
        "reps": len(rows),
        "tasks": len({str(row["task"]) for row in rows}),
        "solves": sum(row.get("reward_binary") == 1 for row in rows),
        "invalid": len(rows) - len(valid_rows),
        "agent_timeouts": sum(bool(row.get("agent_timed_out")) for row in rows),
        "verifier_timeouts": sum(row.get("verifier_exit") == "timeout" for row in rows),
        "partial_all": mean_value(rows, "reward_partial"),
        "partial_valid": mean_value(valid_rows, "reward_partial"),
        "f2p": f2p,
        "p2p": p2p,
        "f2p_perfect": sum(row.get("f2p") == 1 for row in valid_rows),
        "p2p_perfect": sum(row.get("p2p") == 1 for row in valid_rows),
        "tokens": sum(int(row.get("total_tokens") or 0) for row in rows),
        "output_tokens": sum(int(row.get("output_tokens") or 0) for row in rows),
        "turns": sum(int(row.get("turns") or 0) for row in rows),
        "tool_calls": sum(int(row.get("tool_calls") or 0) for row in rows),
        "wall_hours": sum(float(row.get("agent_wall_s") or 0) for row in rows) / 3600,
        "wall_mean": mean_value(rows, "agent_wall_s"),
        "wall_median": statistics.median(numeric_values(rows, "agent_wall_s")),
    }


def load_task_metadata(tasks_root: Path, task: str) -> dict[str, str]:
    """Load stable task title, language, and category."""
    document = tomllib.loads((tasks_root / task / "task.toml").read_text())
    metadata = document["metadata"]
    return {
        "title": str(
            metadata.get("display_title") or metadata.get("original_title") or task
        ),
        "language": str(metadata.get("language") or "unknown"),
        "category": str(metadata.get("category") or "unknown"),
    }


def build_task_metrics(
    rows: list[dict[str, Any]],
    tasks_root: Path,
    subset_tasks: list[str],
    reused_tasks: set[str],
) -> list[dict[str, Any]]:
    """Build complete per-task and per-rep evidence in subset order."""
    metrics: list[dict[str, Any]] = []
    for task in subset_tasks:
        task_rows = sorted(
            [row for row in rows if row["task"] == task],
            key=lambda row: int(row["rep"]),
        )
        valid_rows = [row for row in task_rows if not is_invalid(row)]
        f2p = weighted_grade(valid_rows, "f2p")
        p2p = weighted_grade(valid_rows, "p2p")
        f2p_values = numeric_values(valid_rows, "f2p")
        metrics.append(
            {
                "task": task,
                **load_task_metadata(tasks_root, task),
                "cohort": "reused 12_v2" if task in reused_tasks else "new in 36_v2",
                "rows": task_rows,
                "solves": sum(row.get("reward_binary") == 1 for row in task_rows),
                "invalid": len(task_rows) - len(valid_rows),
                "partial": mean_value(task_rows, "reward_partial"),
                "f2p": f2p,
                "p2p": p2p,
                "f2p_min": min(f2p_values) if f2p_values else None,
                "f2p_max": max(f2p_values) if f2p_values else None,
                "wall": mean_value(task_rows, "agent_wall_s"),
                "tokens": mean_value(task_rows, "total_tokens"),
                "tools": mean_value(task_rows, "tool_calls"),
            }
        )
    return metrics


def message_text(message: dict[str, Any]) -> str:
    """Flatten Pi text content for tool-error classification."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text", "")) for item in content if isinstance(item, dict)
        )
    return ""


def load_session_records(artifact_root: Path) -> list[dict[str, Any]]:
    """Load one rep's native Pi session records."""
    records: list[dict[str, Any]] = []
    for session_path in sorted((artifact_root / "session").glob("*.jsonl")):
        records.extend(
            json.loads(line)
            for line in session_path.read_text().splitlines()
            if line.strip()
        )
    return records


def audit_execution_substrate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit provider shape, thinking, RPC, tools, errors, and terminal hangs."""
    provider_ok = 0
    session_ok = 0
    rpc_prompt = 0
    rpc_quiescent = 0
    request_counts: list[int] = []
    calls: Counter[str] = Counter()
    results: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    causes: Counter[str] = Counter()
    stop_reasons: Counter[str] = Counter()
    maximum_output = 0
    unmatched: list[dict[str, Any]] = []
    for row in rows:
        artifact_root = Path(str(row["artifact_root"]))
        request_paths = sorted(
            (artifact_root / "initial_context").glob("provider_request_*.json")
        )
        request_counts.append(len(request_paths))
        if request_paths:
            request = json.loads(request_paths[0].read_text())
            if (
                request.get("model") == "qwen-agentworld-35b-a3b"
                and request.get("max_tokens") == 65536
                and request.get("temperature") == 0.6
                and request.get("top_p") == 0.95
                and request.get("top_k") == 20
                and request.get("min_p") == 0
                and request.get("repetition_penalty") == 1
                and request.get("chat_template_kwargs")
                == {"enable_thinking": True, "preserve_thinking": True}
                and request.get("reasoning_effort") is None
            ):
                provider_ok += 1
        records = load_session_records(artifact_root)
        if any(
            record.get("type") == "model_change"
            and record.get("provider") == "local-vllm"
            and record.get("modelId") == "qwen-agentworld-35b-a3b"
            for record in records
        ) and any(
            record.get("type") == "thinking_level_change"
            and record.get("thinkingLevel") == "high"
            for record in records
        ):
            session_ok += 1
        rpc_path = artifact_root / "logs" / "pi-rpc-runner.jsonl"
        rpc_records = (
            [
                json.loads(line)
                for line in rpc_path.read_text().splitlines()
                if line.strip()
            ]
            if rpc_path.exists()
            else []
        )
        rpc_events = {record.get("event") for record in rpc_records}
        rpc_prompt += "prompt_sent" in rpc_events
        rpc_quiescent += "quiescent" in rpc_events
        tool_calls_by_id: dict[str, dict[str, Any]] = {}
        tool_result_ids: set[str] = set()
        for record in records:
            if record.get("type") != "message":
                continue
            message = record.get("message", {})
            if message.get("role") == "assistant":
                stop_reasons[str(message.get("stopReason"))] += 1
                usage = message.get("usage") or {}
                output = usage.get("output") or usage.get("outputTokens") or 0
                if isinstance(output, int | float):
                    maximum_output = max(maximum_output, int(output))
                for item in message.get("content", []):
                    if not isinstance(item, dict) or item.get("type") != "toolCall":
                        continue
                    tool = str(item.get("name"))
                    calls[tool] += 1
                    tool_calls_by_id[str(item.get("id"))] = item
            elif message.get("role") == "toolResult":
                tool = str(message.get("toolName"))
                results[tool] += 1
                tool_result_ids.add(str(message.get("toolCallId")))
                if not message.get("isError"):
                    continue
                errors[tool] += 1
                text = message_text(message).lower()
                if tool == "bash":
                    causes["shell nonzero / diagnostic"] += 1
                elif tool == "edit" and text.startswith("validation failed for tool"):
                    causes["malformed edit arguments"] += 1
                elif tool == "edit" and (
                    "could not find" in text or "old text must match" in text
                ):
                    causes["edit target mismatch"] += 1
                elif tool == "edit":
                    causes["edit no-op / other"] += 1
                elif tool == "read" and (
                    "enoent" in text or "no such file" in text or "not found" in text
                ):
                    causes["read missing file"] += 1
                elif tool == "read" and ("offset" in text or "range" in text):
                    causes["read range error"] += 1
                else:
                    causes[f"{tool} other"] += 1
        for call_id, call in tool_calls_by_id.items():
            if call_id in tool_result_ids:
                continue
            raw_arguments = call.get("arguments")
            arguments = raw_arguments if isinstance(raw_arguments, dict) else {}
            unmatched.append(
                {
                    "task": row["task"],
                    "rep": row["rep"],
                    "tool": call.get("name"),
                    "has_numeric_timeout": isinstance(
                        arguments.get("timeout"), int | float
                    ),
                    "command": str(arguments.get("command") or ""),
                }
            )
    return {
        "provider_ok": provider_ok,
        "session_ok": session_ok,
        "rpc_prompt": rpc_prompt,
        "rpc_quiescent": rpc_quiescent,
        "request_min": min(request_counts),
        "request_max": max(request_counts),
        "calls": calls,
        "results": results,
        "errors": errors,
        "causes": causes,
        "stop_reasons": stop_reasons,
        "maximum_output": maximum_output,
        "unmatched": unmatched,
    }


def load_watchdog_evidence(repository_root: Path) -> dict[str, Any]:
    """Summarize alert-only container memory evidence outside result artifacts."""
    log_path = (
        repository_root
        / "runs/container-memory-watchdog"
        / RUN_ID
        / "manual-interventions.ndjson"
    )
    records = [
        json.loads(line) for line in log_path.read_text().splitlines() if line.strip()
    ]
    alerts = [
        record for record in records if record.get("event") == "over_cap_alert_only"
    ]
    interventions = [
        record
        for record in records
        if record.get("event") not in {"watchdog_start", "over_cap_alert_only"}
    ]
    return {
        "alerts": len(alerts),
        "peak_bytes": max(
            (int(record["container_mem_bytes"]) for record in alerts), default=0
        ),
        "containers": sorted({str(record.get("container")) for record in alerts}),
        "interventions": interventions,
    }


def format_percent(value: float | None) -> str:
    """Format a ratio as a one-decimal percentage."""
    return "—" if value is None else f"{value:.1%}"


def rep_cell(row: dict[str, Any]) -> str:
    """Render one rep's strict state and feature-test ratio."""
    if is_invalid(row):
        return "<span class='tag bad'>invalid</span>"
    f2p = row.get("f2p")
    ratio = format_percent(float(f2p)) if isinstance(f2p, int | float) else "—"
    if row.get("reward_binary") == 1:
        return f"<span class='tag good'>solve · {ratio}</span>"
    if row.get("agent_timed_out"):
        return f"<span class='tag caution'>graded timeout · {ratio}</span>"
    return f"<span class='tag neutral'>nonsolve · {ratio}</span>"


def task_verdict(metric: dict[str, Any]) -> tuple[str, str]:
    """Classify one task from strict, feature, preservation, and validity evidence."""
    if metric["solves"]:
        return "solved once", "good"
    p2p_ratio = metric["p2p"][2]
    f2p_ratio = metric["f2p"][2]
    if p2p_ratio is not None and p2p_ratio < 0.8:
        return "regression loss", "bad"
    if metric["invalid"]:
        return f"{metric['invalid']} invalid", "bad"
    if f2p_ratio is not None and f2p_ratio >= 0.7:
        return "feature near-miss", "caution"
    if f2p_ratio is not None and f2p_ratio >= 0.4:
        return "mixed feature", "caution"
    return "low feature", "bad"


def render_task_rows(metrics: list[dict[str, Any]]) -> str:
    """Render the complete 36-task × 3-rep outcome table."""
    rendered: list[str] = []
    for metric in metrics:
        verdict, verdict_class = task_verdict(metric)
        f2p_ratio = metric["f2p"][2]
        p2p_ratio = metric["p2p"][2]
        f2p_span = (
            "—"
            if metric["f2p_min"] is None
            else f"{format_percent(metric['f2p_min'])}–{format_percent(metric['f2p_max'])}"
        )
        rendered.append(
            "<tr>"
            f"<td class='task'><strong>{html.escape(metric['task'])}</strong>"
            f"<span>{html.escape(metric['language'])} · {html.escape(metric['cohort'])}</span></td>"
            + "".join(f"<td>{rep_cell(row)}</td>" for row in metric["rows"])
            + f"<td class='num'>{format_percent(f2p_ratio)}</td>"
            f"<td class='num'>{format_percent(p2p_ratio)}</td>"
            f"<td class='num'>{f2p_span}</td>"
            f"<td class='num'>{metric['partial']:.3f}</td>"
            f"<td class='num'>{metric['wall'] / 60:.1f}m</td>"
            f"<td><span class='tag {verdict_class}'>{verdict}</span></td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_invalid_rows(rows: list[dict[str, Any]]) -> str:
    """Render invalid outcomes and the separately graded SCC timeout."""
    affected = [row for row in rows if is_invalid(row) or row.get("agent_timed_out")]
    rendered = []
    for row in sorted(affected, key=lambda item: (str(item["task"]), int(item["rep"]))):
        outcome = "invalid" if is_invalid(row) else "graded nonsolve"
        rendered.append(
            "<tr>"
            f"<td class='task'>{html.escape(str(row['task']))}</td>"
            f"<td class='num'>{row['rep']}</td>"
            f"<td>{outcome}</td>"
            f"<td>{html.escape(str(row.get('agent_exit')))}</td>"
            f"<td>{html.escape(str(row.get('verifier_exit')))}</td>"
            f"<td class='num'>{float(row.get('agent_wall_s') or 0) / 60:.1f}m</td>"
            f"<td class='num'>{format_percent(float(row['f2p'])) if isinstance(row.get('f2p'), int | float) else '—'}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_instability_rows(metrics: list[dict[str, Any]]) -> str:
    """Render the ten widest feature-test spans across three reps."""
    ranked = sorted(
        metrics,
        key=lambda metric: (
            -(float(metric["f2p_max"] or 0) - float(metric["f2p_min"] or 0))
        ),
    )[:10]
    return "\n".join(
        "<tr>"
        f"<td class='task'>{html.escape(metric['task'])}</td>"
        f"<td class='num'>{format_percent(metric['f2p_min'])}</td>"
        f"<td class='num'>{format_percent(metric['f2p_max'])}</td>"
        f"<td class='num'>{format_percent(float(metric['f2p_max'] or 0) - float(metric['f2p_min'] or 0))}</td>"
        f"<td class='num'>{format_percent(metric['p2p'][2])}</td>"
        "</tr>"
        for metric in ranked
    )


def render_tool_rows(substrate: dict[str, Any]) -> str:
    """Render tool-result counts and concrete error rates."""
    return "\n".join(
        "<tr>"
        f"<td>{html.escape(tool)}</td>"
        f"<td class='num'>{count:,}</td>"
        f"<td class='num'>{int(substrate['errors'].get(tool, 0)):,}</td>"
        f"<td class='num'>{int(substrate['errors'].get(tool, 0)) / count:.1%}</td>"
        "</tr>"
        for tool, count in substrate["results"].most_common()
    )


def render_report(
    rows: list[dict[str, Any]],
    status: dict[str, Any],
    metrics: list[dict[str, Any]],
    reused_rows: list[dict[str, Any]],
    new_rows: list[dict[str, Any]],
    substrate: dict[str, Any],
    watchdog: dict[str, Any],
) -> str:
    """Render one self-contained HTML capability and scaffold report."""
    overall = aggregate_results(rows)
    reused = aggregate_results(reused_rows)
    new = aggregate_results(new_rows)
    valid_count = len(rows) - overall["invalid"]
    all_f2p = overall["f2p"]
    all_p2p = overall["p2p"]
    malformed_edits = int(substrate["causes"].get("malformed edit arguments", 0))
    edit_results = int(substrate["results"].get("edit", 0))
    timeout_unmatched = [
        item
        for item in substrate["unmatched"]
        if item["tool"] == "bash" and not item["has_numeric_timeout"]
    ]
    task_rows = render_task_rows(metrics)
    invalid_rows = render_invalid_rows(rows)
    instability_rows = render_instability_rows(metrics)
    tool_rows = render_tool_rows(substrate)
    stop_reasons = substrate["stop_reasons"]
    revision_counts = Counter(str(row.get("task_revision")) for row in rows)
    launch_counts = Counter(str(row.get("launch_plan_identity")) for row in rows)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:," /><title>Qwen-AgentWorld baseline · 36_v2 full analysis</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#a86f00;--amber-soft:#fff4d8;--shadow:0 20px 55px rgba(14,30,62,.08);--radius:24px;--max:1380px}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),linear-gradient(180deg,#f9fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.5}} .wrap{{max-width:var(--max);margin:auto;padding:28px 20px 48px}} .hero,section{{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}} .hero{{padding:clamp(24px,4vw,42px)}} .eyebrow{{font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase;color:#1d3fb8;background:#eef3ff;padding:8px 12px;border-radius:999px;display:inline-block}} h1,h2{{letter-spacing:-.035em;line-height:1.08}} h1{{font-size:clamp(2.1rem,5vw,4.3rem);max-width:17ch;margin:14px 0}} h2{{margin:0;font-size:clamp(1.4rem,2.5vw,2rem)}} h3{{margin:0 0 8px}} .subtitle,.muted{{color:var(--muted)}} .subtitle{{max-width:88ch;font-size:1.05rem}} .pillrow{{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}} .pill,.tag{{display:inline-flex;align-items:center;border-radius:999px;font-weight:800;white-space:nowrap}} .pill{{padding:8px 11px;font-size:.86rem}} .tag{{padding:5px 8px;font-size:.74rem}} .good{{background:var(--green-soft);color:var(--green)}} .bad{{background:var(--red-soft);color:var(--red)}} .caution{{background:var(--amber-soft);color:var(--amber)}} .neutral{{background:#eef3ff;color:#1d3fb8}} .stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin-top:25px}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;min-height:118px}} .stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:850;text-transform:uppercase;letter-spacing:.07em}} .stat .value{{display:block;font-size:clamp(1.35rem,2.3vw,2rem);font-weight:900;margin-top:9px}} .stat .sub{{display:block;color:var(--muted);font-size:.84rem;margin-top:6px}} section{{padding:clamp(18px,3vw,28px);margin-top:20px}} .section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap;margin-bottom:18px}} .section-head p{{margin:6px 0 0;max-width:90ch;color:var(--muted)}} .callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin-top:14px}} .callout.bad{{border-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}} .callout.good{{border-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}} .callout.caution{{border-color:var(--amber);background:linear-gradient(90deg,#fff8e7,#fff)}} .grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}} .grid-2>*,.grid-3>*{{min-width:0}} .card{{border:1px solid var(--line);border-radius:18px;padding:18px;background:var(--surface)}} .table-wrap{{max-width:100%;overflow:auto;border:1px solid var(--line);border-radius:18px}} table{{width:100%;border-collapse:collapse;min-width:980px}} .full-table{{min-width:1370px}} th,td{{padding:10px 11px;border-bottom:1px solid #e7edf5;text-align:left;vertical-align:middle}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);background:#fbfcff;position:sticky;top:0}} td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}} td.task{{font-family:ui-monospace,monospace;font-size:.81rem;max-width:330px}} td.task span{{display:block;color:var(--muted);font-family:Inter,system-ui,sans-serif;font-size:.72rem;margin-top:4px}} code{{background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px;overflow-wrap:anywhere}} .foot{{color:var(--muted);font-size:.84rem;text-align:center;margin-top:24px}} ul{{padding-left:20px}} @media(max-width:900px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid-2,.grid-3{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<header class="hero"><span class="eyebrow">Local subject · 36_v2 · 108 reps · Pi 0.83.0 · high thinking</span>
<h1>One strict solve; useful feature work, brittle completion.</h1>
<p class="subtitle">Qwen-AgentWorld solved 1/108 reps. Across the 104 normally graded reps it passed {all_f2p[0]:,}/{all_f2p[1]:,} weighted feature tests ({format_percent(all_f2p[2])}) and {all_p2p[0]:,}/{all_p2p[1]:,} preservation tests ({format_percent(all_p2p[2])}). It can find and implement substantial parts of real features, but rarely closes every requirement and varies sharply across repeated attempts.</p>
<div class="pillrow"><span class="pill good">1 / 108 strict solve</span><span class="pill caution">{format_percent(all_f2p[2])} weighted F2P</span><span class="pill good">{format_percent(all_p2p[2])} weighted P2P</span><span class="pill bad">{overall["invalid"]} invalid grades</span><span class="pill neutral">{overall["tokens"] / 1_000_000:.1f}M tokens</span></div>
<div class="stats"><div class="stat"><span class="label">Strict reward</span><span class="value">{overall["solves"]}/108</span><span class="sub">Wazero rep0 only</span></div><div class="stat"><span class="label">Feature tests</span><span class="value">{format_percent(all_f2p[2])}</span><span class="sub">{overall["f2p_perfect"]}/{valid_count} valid reps perfect</span></div><div class="stat"><span class="label">Preservation tests</span><span class="value">{format_percent(all_p2p[2])}</span><span class="sub">{overall["p2p_perfect"]}/{valid_count} valid reps perfect</span></div><div class="stat"><span class="label">Mean partial</span><span class="value">{overall["partial_all"]:.3f}</span><span class="sub">{overall["partial_valid"]:.3f} on valid reps</span></div><div class="stat"><span class="label">Execution</span><span class="value">{overall["wall_hours"]:.1f}h</span><span class="sub">{overall["turns"]:,} turns · {overall["tool_calls"]:,} tools</span></div></div></header>

<section><div class="section-head"><div><h2>How to read this result</h2><p>This is a capability profile for one local model, not a model ranking or a causal scaffold comparison.</p></div></div><div class="grid-3"><div class="card"><h3>Local subject</h3><p>Qwen-AgentWorld-35B-A3B under stock Pi is the subject whose reliable abilities and support needs are being mapped.</p></div><div class="card"><h3>No frontier reference</h3><p>No matched frontier trajectories are analyzed here. The report makes no claim about the size or cause of a frontier-model gap.</p></div><div class="card"><h3>One config only</h3><p>Scaffold recommendations are hypotheses grounded in failures. Effects require the prepared same-model <code>{PI_CHECK_CONFIG}</code> comparison.</p></div></div>
<div class="callout"><strong>Complete denominator:</strong> 108 full task×rep trajectories across 36 unique tasks. Every task appears in the table below before selected examples. The 36 reused <code>12_v2</code> reps retain their original task-set revision and plan identity; the 72 new reps carry the expanded <code>36_v2</code> revision. That is intentional nested-subset provenance, not missing data.</div></section>

<section><div class="section-head"><div><h2>Execution substrate</h2><p>The intended model, request shape, and high-thinking state reached every rep.</p></div></div><div class="grid-2"><div class="card"><h3>Delivery checks</h3><ul><li>Provider request shape: {substrate["provider_ok"]}/108.</li><li>Model + high-thinking session markers: {substrate["session_ok"]}/108.</li><li>RPC prompt delivery: {substrate["rpc_prompt"]}/108.</li><li>RPC quiescence: {substrate["rpc_quiescent"]}/108; the four missing events are exactly the four agent timeouts.</li><li>Captured provider requests: {substrate["request_min"]}–{substrate["request_max"]} per rep.</li></ul></div><div class="card"><h3>Pinned request</h3><ul><li><code>enable_thinking=true</code> and <code>preserve_thinking=true</code>.</li><li><code>max_tokens=65536</code>; sampling 0.6 / 0.95 / 20 / 0 / 1.</li><li>No <code>reasoning_effort</code> field.</li><li>No length stops among {sum(stop_reasons.values()):,} completions; largest single completion was {substrate["maximum_output"]:,} output tokens.</li></ul></div></div>
<div class="callout good"><strong>Interpretation:</strong> parser, provider routing, thinking delivery, and output ceiling do not explain the low strict score. The model had functioning tools and ample output headroom.</div></section>

<section><div class="section-head"><div><h2>Complete 36-task × 3-rep outcomes</h2><p>Rep cells show strict state and per-rep F2P. Task F2P/P2P are weighted by the test counts in valid grades; partial includes invalid reps as zero.</p></div></div><div class="table-wrap"><table class="full-table"><thead><tr><th>Task</th><th>Rep 0</th><th>Rep 1</th><th>Rep 2</th><th class="num">Weighted F2P</th><th class="num">Weighted P2P</th><th class="num">F2P span</th><th class="num">Mean partial</th><th class="num">Mean wall</th><th>Verdict</th></tr></thead><tbody>{task_rows}</tbody></table></div></section>

<section><div class="section-head"><div><h2>Corpus expansion</h2><p>The wider subset added one solve and exposed more feature coverage, preservation failures, and one new invalid rep.</p></div></div><div class="table-wrap"><table><thead><tr><th>Cohort</th><th class="num">Tasks</th><th class="num">Reps</th><th class="num">Solves</th><th class="num">Invalid</th><th class="num">Weighted F2P</th><th class="num">Weighted P2P</th><th class="num">Tokens</th></tr></thead><tbody><tr><td>Reused 12_v2</td><td class="num">{reused["tasks"]}</td><td class="num">{reused["reps"]}</td><td class="num">{reused["solves"]}</td><td class="num">{reused["invalid"]}</td><td class="num">{format_percent(reused["f2p"][2])}</td><td class="num">{format_percent(reused["p2p"][2])}</td><td class="num">{reused["tokens"] / 1_000_000:.1f}M</td></tr><tr><td>New 24 tasks</td><td class="num">{new["tasks"]}</td><td class="num">{new["reps"]}</td><td class="num">{new["solves"]}</td><td class="num">{new["invalid"]}</td><td class="num">{format_percent(new["f2p"][2])}</td><td class="num">{format_percent(new["p2p"][2])}</td><td class="num">{new["tokens"] / 1_000_000:.1f}M</td></tr><tr><td><strong>Full 36_v2</strong></td><td class="num">36</td><td class="num">108</td><td class="num">{overall["solves"]}</td><td class="num">{overall["invalid"]}</td><td class="num">{format_percent(all_f2p[2])}</td><td class="num">{format_percent(all_p2p[2])}</td><td class="num">{overall["tokens"] / 1_000_000:.1f}M</td></tr></tbody></table></div>
<div class="callout"><strong>Do not read the cohort difference as improvement.</strong> These are different task sets, not matched configs. The new 24 tasks happened to carry a higher weighted F2P rate and lower P2P rate than the reused 12.</div></section>

<section><div class="section-head"><div><h2>What works reliably</h2><p>Start with demonstrated capabilities before failure analysis.</p></div></div><div class="grid-3"><div class="card"><h3>One complete implementation</h3><p><code>wazero-multi-module-snapshots</code> rep0 passed every feature and preservation test. Across all three reps, Wazero reached 207/234 F2P ({207 / 234:.1%}) and 6/6 P2P.</p></div><div class="card"><h3>Stable near-misses</h3><p>PSD Tools and Yjs each passed 74.1% weighted F2P with perfect P2P in all three reps. Obsidian reached 72.8% F2P and 100% P2P across 3,393 preservation tests.</p></div><div class="card"><h3>Scope control is often good</h3><p>{overall["p2p_perfect"]}/{valid_count} valid reps were P2P-perfect. The model frequently found the relevant surface and preserved existing behavior even when feature coverage remained incomplete.</p></div></div></section>

<section><div class="section-head"><div><h2>Where capability breaks</h2><p>Strict completion, preservation outliers, and rep-to-rep variance are separate failure modes.</p></div></div><div class="grid-3"><div class="card"><h3>Requirements remain unfinished</h3><p>Only {overall["f2p_perfect"]}/{valid_count} valid reps passed every feature test. Tengo destructuring and recursive delegation passed 0% F2P across all three reps despite mostly or fully preserved P2P.</p></div><div class="card"><h3>Some patches break the base</h3><p><code>fd-deterministic-multi-key-sorting</code> scored 0/129 F2P and 0/327 P2P. FastAPI preserved only 33.3% weighted P2P. The overall 97.7% P2P rate hides these concentrated regressions.</p></div><div class="card"><h3>Variance is large</h3><p>SCC ranged from 0% to 83.9% F2P, Koota from 0% to 69.8%, and HTTPX from 26.2% to 82.0%. A single rep is not a stable estimate for these tasks.</p></div></div>
<div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>Most variable task</th><th class="num">Min F2P</th><th class="num">Max F2P</th><th class="num">Span</th><th class="num">Weighted P2P</th></tr></thead><tbody>{instability_rows}</tbody></table></div></section>

<section><div class="section-head"><div><h2>Reliability and termination</h2><p>Four reps lacked a normal grade; a fifth timed out but still produced a gradable patch.</p></div></div><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Outcome</th><th>Agent exit</th><th>Verifier exit</th><th class="num">Wall</th><th class="num">F2P</th></tr></thead><tbody>{invalid_rows}</tbody></table></div>
<div class="callout good"><strong>Bounded Bash execution directly targets the observed hangs.</strong> All four agent timeouts ended on an unmatched Bash call with no numeric timeout: LangChain reps 1–2, Pest rep1, and SCC rep0. The existing Qwen timeout extension defaults only those missing values to 360 seconds.</div><div class="callout caution"><strong>SCC is an accounting edge case, not a strict solve.</strong> Its agent timed out at 3,600 seconds, but the verifier graded the saved patch at 0% F2P and 98.3% P2P. Structured run state correctly counted it as a timeout outcome while the corpus retained the grade.</div></section>

<section><div class="section-head"><div><h2>Tool behavior and efficiency</h2><p>Shell failures mostly represent diagnostic feedback; edit failures expose a more specific schema-adherence weakness.</p></div></div><div class="grid-2"><div><div class="table-wrap"><table><thead><tr><th>Tool</th><th class="num">Results</th><th class="num">Errors</th><th class="num">Error rate</th></tr></thead><tbody>{tool_rows}</tbody></table></div></div><div class="card"><h3>Concrete causes</h3><ul><li>{int(substrate["causes"].get("shell nonzero / diagnostic", 0)):,} Bash errors were normal nonzero or diagnostic command feedback.</li><li>{malformed_edits:,}/{edit_results:,} edit results ({malformed_edits / edit_results:.1%}) were malformed arguments.</li><li>{int(substrate["causes"].get("edit target mismatch", 0)):,} edits missed stale or nonmatching text.</li><li>{len(substrate["unmatched"])} tool calls had no result; all were the terminal unbounded Bash calls above.</li></ul></div></div>
<div class="callout"><strong>Cost profile:</strong> {overall["tokens"] / 1_000_000:.1f}M tokens, {overall["output_tokens"] / 1_000_000:.2f}M output tokens, {overall["turns"]:,} completions, {overall["tool_calls"]:,} tool calls, and {overall["wall_hours"]:.1f} aggregate agent-hours. Median wall time was {overall["wall_median"] / 60:.1f} minutes.</div></section>

<section><div class="section-head"><div><h2>Host memory evidence</h2><p>The host-side watchdog stayed outside official result artifacts and made no intervention.</p></div></div><div class="callout caution"><strong>Meriyah stressed container memory.</strong> The watchdog logged {watchdog["alerts"]} alert-only samples across reps 1 and 2, peaking at {watchdog["peak_bytes"] / 1024**3:.1f} GiB. It declined to kill because the largest killable process stayed below the 6 GiB safety floor. No official result was mutated.</div><div class="callout good"><strong>Interventions: {len(watchdog["interventions"])}.</strong> This is a host-safety signal, not evidence of model capability or task failure; all three Meriyah reps graded normally.</div></section>

<section><div class="section-head"><div><h2>Scaffoldability ledger</h2><p>Each proposal follows a trajectory-linked failure; unsupported changes are ruled out.</p></div></div><div class="table-wrap"><table><thead><tr><th>Failure</th><th>Evidence</th><th>Smallest scaffold</th><th>Confidence</th></tr></thead><tbody><tr><td>Terminal tool hangs</td><td>{len(timeout_unmatched)}/4 agent timeouts ended on unbounded Bash</td><td>Default only missing Bash timeouts to 360s</td><td><span class="tag good">high</span></td></tr><tr><td>Incomplete feature coverage</td><td>43.5% weighted F2P; 1/104 valid reps perfect</td><td>One bounded independent requirement re-audit</td><td><span class="tag caution">moderate</span></td></tr><tr><td>Malformed edit calls</td><td>{malformed_edits}/{edit_results} edit results failed argument validation</td><td>Tool-call repair or clearer edit schema feedback</td><td><span class="tag good">high</span></td></tr><tr><td>High task variance</td><td>SCC, Koota, HTTPX, SQL, and Updo span >50 F2P points</td><td>Keep three reps; judge paired churn, not means alone</td><td><span class="tag good">high</span></td></tr><tr><td>Output ceiling</td><td>No length stops; max completion {substrate["maximum_output"]:,} vs 65,536 cap</td><td>Do not raise the output ceiling</td><td><span class="tag bad">reject</span></td></tr></tbody></table></div>
<div class="callout"><strong>Pi-check scope:</strong> the prior 12-task Qwen comparison showed mixed mechanism evidence: the timeout recovered two hangs, while re-audit effort did not reliably become repair and produced new verifier-timeout regressions. Extending the same combined config to 36_v2 tests breadth; it does not isolate timeout from re-audit.</div></section>

<section><div class="section-head"><div><h2>Prepared next comparison</h2><p>No duplicate config release was created because the existing locked release already contains exactly the requested behavior.</p></div></div><div class="grid-2"><div class="card"><h3><code>{PI_CHECK_CONFIG}</code></h3><ul><li>One pi-check re-audit via <code>--check</code>.</li><li>Missing Bash timeout defaults to 360 seconds; explicit model timeouts remain unchanged.</li><li>Same Qwen provider, thinking preservation, sampling, and 65,536-token ceiling.</li><li>No new system preamble or orchestration text.</li></ul></div><div class="card"><h3>36_v2 launch shape</h3><ul><li>108 treatment cells in the comparison view.</li><li>36 completed 12_v2 treatment reps reused read-only.</li><li>72 new treatment attempts across the added 24 tasks.</li><li>Baseline is reference-only and creates no run cells.</li><li>New preflight: actionlint rep0.</li></ul></div></div><div class="callout good"><strong>Model-free plan compiled:</strong> <code>{PI_CHECK_PLAN_IDENTITY}</code>. It selects only <code>{PI_CHECK_CONFIG}</code>, references <code>{CONFIG_IDENTITY}</code>, and has not been approved or executed.</div></section>

<section><div class="section-head"><div><h2>Conclusion</h2></div></div><div class="callout bad"><strong>Primary limitation: completion, not access.</strong> Qwen-AgentWorld navigates, edits, validates, and often preserves existing behavior, but converts that work into a strict solve in only 1/108 reps.</div><div class="callout good"><strong>Best-supported next step:</strong> run the prepared combined pi-check + timeout comparison on the 24 added tasks, preserving the three-rep design. Judge it by strict solves, paired F2P, verifier-timeout churn, malformed edit calls, and added tokens—not partial reward alone.</div><div class="callout"><strong>Keep uncertainty explicit:</strong> the combined config cannot attribute gains separately to timeout control and re-audit. If the 36_v2 result is promising, the next clean mechanism comparison should split timeout-only from timeout-plus-check.</div></section>

<div class="foot">Source: <code>results/{MODEL_LEAF}/{THINKING_LEVEL}/{CONFIG_IDENTITY}/</code> · run <code>{RUN_ID}</code> · plans {dict(launch_counts)} · task revisions {dict(revision_counts)}<br />Structured run: {status["counts"]["ok"]} ok, {status["counts"]["timeout"]} timeout, {status["counts"]["failed"]} failed, {status["counts"]["batch_skipped"]} skipped · generated deterministically by <code>analysis/qwen-agentworld-35b-baseline-36v2/build_report.py</code>.</div>
</div></body></html>"""


def main() -> None:
    """Build the report after validating canonical result and run evidence."""
    arguments = parse_report_arguments()
    subset_tasks = load_subset_tasks(arguments.repository_root, "36_v2")
    reused_tasks = set(load_subset_tasks(arguments.repository_root, "12_v2"))
    rows = load_qwen_agentworld_results(arguments.results_root, subset_tasks)
    status = find_completed_run_status(arguments.results_root)
    if rows[0].get("config") != CONFIG_IDENTITY:
        raise ValueError("Qwen-AgentWorld report config identity mismatch")
    launch_identities = {str(row.get("launch_plan_identity")) for row in rows}
    if BASELINE_PLAN_IDENTITY not in launch_identities or len(launch_identities) != 2:
        raise ValueError("Qwen-AgentWorld report launch provenance mismatch")
    metrics = build_task_metrics(rows, arguments.tasks_root, subset_tasks, reused_tasks)
    reused_rows = [row for row in rows if row["task"] in reused_tasks]
    new_rows = [row for row in rows if row["task"] not in reused_tasks]
    substrate = audit_execution_substrate(rows)
    if (
        substrate["provider_ok"] != EXPECTED_RESULTS
        or substrate["session_ok"] != EXPECTED_RESULTS
    ):
        raise ValueError("Qwen-AgentWorld report delivery audit failed")
    report = render_report(
        rows,
        status,
        metrics,
        reused_rows,
        new_rows,
        substrate,
        load_watchdog_evidence(arguments.repository_root),
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(report)
    print(arguments.output)


if __name__ == "__main__":
    main()
