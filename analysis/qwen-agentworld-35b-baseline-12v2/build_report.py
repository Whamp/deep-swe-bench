#!/usr/bin/env python3
"""Build the Qwen-AgentWorld baseline 12_v2 result report."""

from __future__ import annotations

import argparse
import html
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

RUN_ID = "qwen-agentworld-35b-high-baseline-12v2-r3-w4"
CONFIG_IDENTITY = "baseline-qwen-agentworld-35b@1.0.0"
MODEL_LEAF = "qwen-agentworld-35b-a3b"
THINKING_LEVEL = "high"


def parse_report_arguments() -> argparse.Namespace:
    """Parse report paths without assuming one checkout owns the result tree."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("index.html"),
    )
    return parser.parse_args()


def load_qwen_agentworld_results(results_root: Path) -> list[dict[str, Any]]:
    """Load the 36 canonical Qwen-AgentWorld baseline result records."""
    config_root = results_root / MODEL_LEAF / THINKING_LEVEL / CONFIG_IDENTITY
    rows: list[dict[str, Any]] = []
    for result_path in sorted(config_root.glob("*/rep*/result.json")):
        row = json.loads(result_path.read_text())
        row["task"] = result_path.parents[1].name
        row["rep"] = int(result_path.parent.name.removeprefix("rep"))
        row["result_path"] = str(result_path)
        rows.append(row)
    if len(rows) != 36:
        raise ValueError(
            "Qwen-AgentWorld report input invalid: expected 36 result records; "
            f"found {len(rows)} under {config_root}"
        )
    return rows


def load_qwen_agentworld_tool_counts(results_root: Path) -> Counter[str]:
    """Count Pi tool calls from native session records for all 36 reps."""
    session_root = results_root / MODEL_LEAF / THINKING_LEVEL / CONFIG_IDENTITY
    tool_counts: Counter[str] = Counter()
    for session_path in session_root.glob("*/rep*/session/*.jsonl"):
        for line in session_path.read_text().splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "message":
                continue
            message = record.get("message", {})
            if message.get("role") != "assistant":
                continue
            for content in message.get("content", []):
                if isinstance(content, dict) and content.get("type") == "toolCall":
                    tool_counts[str(content.get("name"))] += 1
    return tool_counts


def find_qwen_agentworld_run_status(results_root: Path) -> dict[str, Any]:
    """Load the completed structured state for the approved launch plan."""
    matches = sorted((results_root / "_runs").glob(f"{RUN_ID}--*/status.json"))
    if len(matches) != 1:
        raise ValueError(
            "Qwen-AgentWorld run state invalid: expected one structured status; "
            f"found {len(matches)}"
        )
    return json.loads(matches[0].read_text())


def numeric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    """Return numeric result values while excluding nulls and strings."""
    return [float(row[key]) for row in rows if isinstance(row.get(key), int | float)]


def mean_result_value(rows: list[dict[str, Any]], key: str) -> float:
    """Return the arithmetic mean for one numeric result field."""
    values = numeric_values(rows, key)
    return statistics.mean(values) if values else 0.0


def build_task_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate strict, partial, reliability, and efficiency metrics by task."""
    metrics: list[dict[str, Any]] = []
    for task in sorted({str(row["task"]) for row in rows}):
        task_rows = [row for row in rows if row["task"] == task]
        partials = numeric_values(task_rows, "reward_partial")
        f2p_values = numeric_values(task_rows, "f2p")
        p2p_values = numeric_values(task_rows, "p2p")
        metrics.append(
            {
                "task": task,
                "partial_mean": statistics.mean(partials),
                "partial_min": min(partials),
                "partial_max": max(partials),
                "invalid": sum(row.get("reward_binary") == -1 for row in task_rows),
                "f2p_mean": statistics.mean(f2p_values) if f2p_values else None,
                "p2p_mean": statistics.mean(p2p_values) if p2p_values else None,
                "wall_mean": mean_result_value(task_rows, "agent_wall_s"),
                "tools_mean": mean_result_value(task_rows, "tool_calls"),
            }
        )
    return sorted(metrics, key=lambda row: (-row["partial_mean"], row["task"]))


def format_percent(value: float) -> str:
    """Format a zero-to-one metric as a one-decimal percentage."""
    return f"{value * 100:.1f}%"


def render_task_rows(task_metrics: list[dict[str, Any]]) -> str:
    """Render the per-task result table and deterministic score bars."""
    rendered: list[str] = []
    for metric in task_metrics:
        partial = float(metric["partial_mean"])
        f2p = metric["f2p_mean"]
        p2p = metric["p2p_mean"]
        invalid = int(metric["invalid"])
        if f2p is not None and float(f2p) >= 0.75:
            verdict = "feature close"
            verdict_class = "good"
        elif f2p is not None and float(f2p) >= 0.4:
            verdict = "mixed feature"
            verdict_class = "caution"
        else:
            verdict = "low feature"
            verdict_class = "bad"
        if invalid:
            verdict = f"{invalid} invalid"
            verdict_class = "bad"
        rendered.append(
            "<tr>"
            f"<td class='task'>{html.escape(str(metric['task']))}</td>"
            "<td><div class='meter'><span style='width:"
            f"{partial * 100:.3f}%'></span></div><strong>{partial:.3f}</strong></td>"
            f"<td class='num'>{format_percent(float(f2p)) if f2p is not None else '—'}</td>"
            f"<td class='num'>{format_percent(float(p2p)) if p2p is not None else '—'}</td>"
            f"<td class='num'>{float(metric['wall_mean']) / 60:.1f}m</td>"
            f"<td class='num'>{float(metric['tools_mean']):.1f}</td>"
            f"<td><span class='tag {verdict_class}'>{verdict}</span></td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_tool_bars(tool_counts: Counter[str]) -> str:
    """Render deterministic CSS bars for the native Pi tool mix."""
    maximum = max(tool_counts.values(), default=1)
    rows = []
    for name, count in tool_counts.most_common():
        rows.append(
            "<div class='tool-row'>"
            f"<strong>{html.escape(name)}</strong>"
            f"<div class='tool-track'><span style='width:{count / maximum * 100:.3f}%'></span></div>"
            f"<span class='num'>{count:,}</span>"
            "</div>"
        )
    return "\n".join(rows)


def render_qwen_agentworld_report(
    rows: list[dict[str, Any]],
    status: dict[str, Any],
    tool_counts: Counter[str],
) -> str:
    """Render one self-contained HTML report from canonical run evidence."""
    task_metrics = build_task_metrics(rows)
    valid_rows = [row for row in rows if row.get("reward_binary") != -1]
    solved = sum(row.get("reward_binary") == 1 for row in rows)
    agent_timeouts = sum(bool(row.get("agent_timed_out")) for row in rows)
    verifier_timeouts = sum(row.get("verifier_exit") == "timeout" for row in rows)
    weighted_f2p_passed = sum(int(row.get("f2p_passed") or 0) for row in rows)
    weighted_f2p_total = sum(int(row.get("f2p_total") or 0) for row in rows)
    weighted_p2p_passed = sum(int(row.get("p2p_passed") or 0) for row in rows)
    weighted_p2p_total = sum(int(row.get("p2p_total") or 0) for row in rows)
    mean_partial = mean_result_value(rows, "reward_partial")
    valid_partial = mean_result_value(valid_rows, "reward_partial")
    total_tokens = sum(int(row.get("total_tokens") or 0) for row in rows)
    output_tokens = sum(int(row.get("output_tokens") or 0) for row in rows)
    turns = sum(int(row.get("turns") or 0) for row in rows)
    tool_calls = sum(int(row.get("tool_calls") or 0) for row in rows)
    agent_hours = sum(float(row.get("agent_wall_s") or 0) for row in rows) / 3600
    perfect_p2p = sum(row.get("p2p") == 1 for row in valid_rows)
    task_rows = render_task_rows(task_metrics)
    tool_bars = render_tool_bars(tool_counts)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:," />
<title>Qwen-AgentWorld 35B baseline · 12_v2 result analysis</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#a86f00;--amber-soft:#fff4d8;--shadow:0 20px 55px rgba(14,30,62,.08);--radius:24px;--max:1240px}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),linear-gradient(180deg,#f9fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.5}} .wrap{{max-width:var(--max);margin:auto;padding:28px 20px 48px}} .hero,section{{background:rgba(255,255,255,.91);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}} .hero{{padding:clamp(24px,4vw,42px)}} .eyebrow{{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#1d3fb8;background:#eef3ff;padding:8px 12px;border-radius:999px;display:inline-block}} h1,h2{{letter-spacing:-.035em;line-height:1.08}} h1{{font-size:clamp(2.1rem,5vw,4.4rem);max-width:14ch;margin:14px 0}} h2{{margin:0;font-size:clamp(1.4rem,2.5vw,2rem)}} .subtitle,.muted{{color:var(--muted)}} .subtitle{{max-width:78ch;font-size:1.05rem}} .pillrow{{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}} .pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:7px 11px}} .pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}} .pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}} .pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}} .pill.neutral{{background:#eef3ff;color:#1d3fb8}} .stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin-top:25px}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;min-height:116px}} .stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}} .stat .value{{display:block;font-size:clamp(1.45rem,2.4vw,2.1rem);font-weight:900;margin-top:9px}} .stat .sub{{display:block;color:var(--muted);font-size:.86rem;margin-top:6px}} section{{padding:clamp(18px,3vw,28px);margin-top:20px}} .section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap;margin-bottom:18px}} .section-head p{{margin:6px 0 0;max-width:78ch;color:var(--muted)}} .callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin-top:14px}} .callout.bad{{border-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}} .callout.good{{border-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}} .grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .card{{border:1px solid var(--line);border-radius:18px;padding:18px;background:var(--surface)}} .card h3{{margin:0 0 8px}} .table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:18px}} table{{width:100%;border-collapse:collapse;min-width:990px}} th,td{{padding:11px 12px;border-bottom:1px solid #e7edf5;text-align:left;vertical-align:middle}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);background:#fbfcff}} td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}} td.task{{font-family:ui-monospace,monospace;font-size:.86rem;max-width:330px}} .meter{{display:inline-block;width:110px;height:12px;background:#edf2f7;border-radius:999px;overflow:hidden;margin-right:9px;vertical-align:middle}} .meter span{{display:block;height:100%;background:linear-gradient(90deg,#5a7cff,#335dff);border-radius:inherit}} .tool-list{{display:grid;gap:13px}} .tool-row{{display:grid;grid-template-columns:62px 1fr 62px;gap:12px;align-items:center}} .tool-track{{height:15px;border-radius:999px;background:#edf2f7;overflow:hidden}} .tool-track span{{display:block;height:100%;background:linear-gradient(90deg,#5a7cff,#1d3fb8)}} .foot{{color:var(--muted);font-size:.85rem;text-align:center;margin-top:24px}} code{{background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}} @media(max-width:850px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid-2{{grid-template-columns:1fr}}}}
</style>
</head>
<body><div class="wrap">
<header class="hero">
<span class="eyebrow">DeepSWE · 12_v2 · 36 reps · Pi 0.83.0</span>
<h1>High partial credit, weak feature completion.</h1>
<p class="subtitle">Qwen-AgentWorld 35B preserved existing behavior almost perfectly, but passed only 38.1% of weighted feature tests and solved no rep strictly. The 0.798 partial score is dominated by the much larger regression-test pool; two agent timeouts and one verifier timeout reduced it further.</p>
<div class="pillrow"><span class="pill bad">0 / 36 strict solves</span><span class="pill caution">3 invalid reps</span><span class="pill good">99.5% P2P weighted pass</span><span class="pill neutral">pi-check is a targeted next config</span></div>
<div class="stats">
<div class="stat"><span class="label">Strict reward</span><span class="value">{solved}/36</span><span class="sub">no F2P-perfect valid rep</span></div>
<div class="stat"><span class="label">Mean partial · all</span><span class="value">{mean_partial:.3f}</span><span class="sub">includes three zeroed invalid reps</span></div>
<div class="stat"><span class="label">Mean partial · valid</span><span class="value">{valid_partial:.3f}</span><span class="sub">33 normally graded reps</span></div>
<div class="stat"><span class="label">Weighted F2P / P2P</span><span class="value">{weighted_f2p_passed / weighted_f2p_total:.1%} / {weighted_p2p_passed / weighted_p2p_total:.1%}</span><span class="sub">feature gain vs regression safety</span></div>
<div class="stat"><span class="label">Cumulative tokens</span><span class="value">{total_tokens / 1_000_000:.1f}M</span><span class="sub">{output_tokens / 1_000_000:.2f}M output across turns</span></div>
</div>
</header>
<section><div class="section-head"><div><h2>Verdict</h2><p>The model is regression-safe but feature-incomplete under stock Pi.</p></div></div>
<div class="callout bad"><strong>Strict efficacy: failed.</strong> DeepSWE awards a binary solve only when every feature-to-pass test succeeds while pass-to-pass tests stay green. None of the 33 valid reps achieved perfect F2P. Partial reward looks high because P2P tests outnumber F2P tests by more than 25 to 1.</div>
<div class="callout good"><strong>Regression safety: strong.</strong> Valid patches passed {weighted_p2p_passed:,}/{weighted_p2p_total:,} weighted P2P tests ({weighted_p2p_passed / weighted_p2p_total:.1%}); {perfect_p2p}/{len(valid_rows)} valid reps were P2P-perfect. The model usually changed the right surface without breaking established behavior.</div>
<div class="callout"><strong>Next test: pi-check.</strong> A single fresh verification follow-up directly targets missed feature cases after the initial patch. The risk is runtime: this baseline already used {turns:,} turns and {tool_calls:,} tool calls, and two LangChain reps exhausted the one-hour agent timeout.</div>
</section>
<section><div class="section-head"><div><h2>Per-task outcomes</h2><p>Sorted by mean partial reward, but verdicts follow F2P completion. Partial includes invalid reps as zero; F2P/P2P omit reps without a verifier grade.</p></div></div><div class="table-wrap"><table><thead><tr><th>Task</th><th>Mean partial</th><th class="num">F2P mean</th><th class="num">P2P mean</th><th class="num">Mean wall</th><th class="num">Mean tools</th><th>Verdict</th></tr></thead><tbody>{task_rows}</tbody></table></div></section>
<div class="grid-2">
<section><div class="section-head"><div><h2>Execution reliability</h2><p>Three reps lacked a normal verifier grade.</p></div></div>
<div class="card"><h3>LangChain · reps 1 and 2</h3><p>Both agents hit 3,600.1 seconds before an <code>agent_end</code> event. Rep 0 scored 0.975 partial, so the task was solvable but unstable rather than uniformly out of reach.</p></div>
<div class="card" style="margin-top:12px"><h3>Mobly · rep 1</h3><p>The agent exited normally after 280 seconds, but the verifier timed out on its patch. This is a patch/verifier failure, not a model-request timeout; the other two reps scored 0.953 and 0.911 partial.</p></div>
<div class="callout"><strong>Run accounting:</strong> {status["counts"]["ok"]} normal outcomes, {status["counts"]["timeout"]} agent timeouts, {status["counts"]["failed"]} other failed outcome; {agent_timeouts} agent and {verifier_timeouts} total verifier timeouts.</div>
</section>
<section><div class="section-head"><div><h2>Tool mix</h2><p>{tool_calls:,} native tool calls across 36 reps, or {tool_calls / len(rows):.1f} per rep.</p></div></div><div class="tool-list">{tool_bars}</div><div class="callout"><strong>High iteration load:</strong> {turns:,} model completions and {agent_hours:.2f} aggregate agent-hours. Bash and read account for most activity; pi-check should be judged on added solves per added turn, not partial score alone.</div></section>
</div>
<section><div class="section-head"><div><h2>What partial reward hides</h2></div></div>
<div class="grid-2"><div class="card"><h3>Obsidian is a genuine feature near-miss</h3><p>Rep 2 preserved all 1,131 P2P tests and passed 52/60 F2P tests. The remaining failures clustered around nested or escaped Markdown labels, angle-bracket destinations, whitespace, and default heading display text—edge cases a focused re-audit could plausibly catch.</p></div><div class="card"><h3>Other 0.97+ partials are less complete</h3><p>SQL Formatter, Adaptix, and Dateutil averaged 0.98–0.99 partial, yet their mean F2P rates were 33.3%, 18.2%, and 47.8%. Their large P2P suites inflate partial reward. Pi-check must improve F2P, not merely preserve the already-green regression suite.</p></div></div>
</section>
<section><div class="section-head"><div><h2>Conclusion</h2></div></div>
<div class="callout bad"><strong>Do not call this baseline successful on DeepSWE.</strong> The official strict result is 0/36, not “about 80% solved.” Partial reward shows useful progress, not task completion.</div>
<div class="callout good"><strong>Do run the pi-check comparison.</strong> The config directly tests whether one independent verification pass converts regression-safe but feature-incomplete patches into strict solves. Judge it by F2P gains and solves, not partial reward alone. Preflight must prove the second request and preserve the Qwen request shape before fan-out.</div>
</section>
<div class="foot">Source: <code>results/{MODEL_LEAF}/{THINKING_LEVEL}/{CONFIG_IDENTITY}/</code> · run <code>{RUN_ID}</code> · launch plan <code>{rows[0]["launch_plan_identity"]}</code><br />Generated deterministically by <code>analysis/qwen-agentworld-35b-baseline-12v2/build_report.py</code>.</div>
</div></body></html>
"""


def main() -> None:
    """Build the report after validating the completed structured run state."""
    arguments = parse_report_arguments()
    rows = load_qwen_agentworld_results(arguments.results_root)
    status = find_qwen_agentworld_run_status(arguments.results_root)
    if status.get("state") != "completed" or status.get("stage") != "done":
        raise ValueError(
            "Qwen-AgentWorld report input invalid: structured run is not completed"
        )
    report = render_qwen_agentworld_report(
        rows,
        status,
        load_qwen_agentworld_tool_counts(arguments.results_root),
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(report)
    print(arguments.output)


if __name__ == "__main__":
    main()
