#!/usr/bin/env python3
"""Build the frozen seven-rep ThinkingCap pi-check mid-run comparison."""

from __future__ import annotations

import html
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = (
    Path(os.environ.get("DEEP_SWE_BENCH_RESULTS_ROOT", REPOSITORY_ROOT / "results"))
    / "thinkingcap-qwen3.6-27b-awq-int4"
    / "high"
)
REPORT_ROOT = REPOSITORY_ROOT / "reports" / "thinkingcap-picheck-preflight-midrun-7cell"
SNAPSHOT_TIMESTAMP = "2026-08-05T02:26:46Z"
SNAPSHOT_RUN_PROGRESS = "7 of 36 completed; 2 active"

CONFIGS = (
    "baseline-thinkingcap-qwen36@1.1.0",
    "pi-check@1.4.0",
    "pi-check@1.5.0",
)
CONFIG_LABELS = {
    "baseline-thinkingcap-qwen36@1.1.0": "Stock baseline",
    "pi-check@1.4.0": "Final check",
    "pi-check@1.5.0": "Preflight + final",
}
SNAPSHOT_REPS = (
    ("obsidian-linter-link-format-conversion", 0),
    ("obsidian-linter-link-format-conversion", 1),
    ("obsidian-linter-link-format-conversion", 2),
    ("participle-grammar-conflict-analysis", 0),
    ("superjson-error-stack-serialization", 0),
    ("superjson-error-stack-serialization", 1),
    ("superjson-error-stack-serialization", 2),
)
TASK_LABELS = {
    "obsidian-linter-link-format-conversion": "Obsidian link conversion",
    "participle-grammar-conflict-analysis": "Participle grammar analysis",
    "superjson-error-stack-serialization": "SuperJSON error stacks",
}


def load_snapshot_results() -> dict[str, dict[tuple[str, int], dict[str, Any]]]:
    """Load and validate every frozen matched result."""
    loaded: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    for config in CONFIGS:
        config_results: dict[tuple[str, int], dict[str, Any]] = {}
        for task, rep in SNAPSHOT_REPS:
            result_path = RESULTS_ROOT / config / task / f"rep{rep}" / "result.json"
            result = json.loads(result_path.read_text())
            if (
                result["task"] != task
                or result["rep"] != rep
                or result["config"] != config
            ):
                raise ValueError(f"Result identity mismatch: {result_path}")
            if result.get("model") != "local-vllm/thinkingcap-qwen3.6-27b-awq-int4":
                raise ValueError(f"Model mismatch: {result_path}")
            if result.get("thinking_level") != "high":
                raise ValueError(f"Thinking mismatch: {result_path}")
            config_results[(task, rep)] = result
        loaded[config] = config_results
    return loaded


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate strict, grading, usage, and validity fields."""
    return {
        "reps": len(results),
        "strict": sum(int(result["reward_binary"]) for result in results),
        "partial_mean": statistics.mean(result["reward_partial"] for result in results),
        "partial_median": statistics.median(
            result["reward_partial"] for result in results
        ),
        "f2p_passed": sum(result["f2p_passed"] for result in results),
        "f2p_total": sum(result["f2p_total"] for result in results),
        "p2p_passed": sum(result["p2p_passed"] for result in results),
        "p2p_total": sum(result["p2p_total"] for result in results),
        "total_tokens": sum(result["total_tokens"] for result in results),
        "agent_wall_s": sum(result["agent_wall_s"] for result in results),
        "valid": sum(
            result.get("agent_exit") == 0 and result.get("verifier_exit") == 0
            for result in results
        ),
    }


def percent(numerator: float, denominator: float = 1.0) -> str:
    """Format a ratio as one-decimal percentage."""
    return f"{100 * numerator / denominator:.1f}%"


def signed_points(value: float) -> str:
    """Format a ratio delta as signed percentage points."""
    return f"{100 * value:+.2f} pp"


def millions(value: int) -> str:
    """Format a count in millions."""
    return f"{value / 1_000_000:.1f}M"


def hours(value: float) -> str:
    """Format seconds as hours."""
    return f"{value / 3600:.2f}h"


def score_bar(value: float) -> str:
    """Render a deterministic inline score bar."""
    width = max(0.0, min(100.0, 100 * value))
    return (
        '<span class="score"><span class="bar" style="width:'
        f'{width:.2f}%"></span><span>{percent(value)}</span></span>'
    )


def build_snapshot_document(
    loaded: dict[str, dict[tuple[str, int], dict[str, Any]]],
) -> dict[str, Any]:
    """Create the report's machine-readable frozen snapshot."""
    summaries = {
        config: aggregate([loaded[config][key] for key in SNAPSHOT_REPS])
        for config in CONFIGS
    }
    task_reps: dict[str, list[int]] = defaultdict(list)
    for task, rep in SNAPSHOT_REPS:
        task_reps[task].append(rep)
    tasks: dict[str, dict[str, Any]] = {}
    for task, reps in task_reps.items():
        tasks[task] = {
            config: aggregate([loaded[config][(task, rep)] for rep in reps])
            for config in CONFIGS
        }
    cells = []
    for task, rep in SNAPSHOT_REPS:
        row = {
            "task": task,
            "rep": rep,
            "configs": {config: loaded[config][(task, rep)] for config in CONFIGS},
        }
        current = loaded["pi-check@1.5.0"][(task, rep)]["reward_partial"]
        final_only = loaded["pi-check@1.4.0"][(task, rep)]["reward_partial"]
        baseline = loaded["baseline-thinkingcap-qwen36@1.1.0"][(task, rep)][
            "reward_partial"
        ]
        row["delta_vs_final"] = current - final_only
        row["delta_vs_baseline"] = current - baseline
        cells.append(row)
    return {
        "snapshotTimestamp": SNAPSHOT_TIMESTAMP,
        "runProgress": SNAPSHOT_RUN_PROGRESS,
        "model": "local-vllm/thinkingcap-qwen3.6-27b-awq-int4",
        "thinking": "high",
        "configs": list(CONFIGS),
        "snapshotReps": [list(key) for key in SNAPSHOT_REPS],
        "summaries": summaries,
        "tasks": tasks,
        "cells": cells,
    }


def render_report(document: dict[str, Any]) -> str:
    """Render the self-contained mid-run HTML report."""
    summaries = document["summaries"]
    baseline = summaries["baseline-thinkingcap-qwen36@1.1.0"]
    final_only = summaries["pi-check@1.4.0"]
    current = summaries["pi-check@1.5.0"]
    deltas_final = [cell["delta_vs_final"] for cell in document["cells"]]
    deltas_baseline = [cell["delta_vs_baseline"] for cell in document["cells"]]
    final_wins = sum(delta > 1e-12 for delta in deltas_final)
    final_losses = sum(delta < -1e-12 for delta in deltas_final)
    final_ties = len(deltas_final) - final_wins - final_losses

    summary_rows = []
    for config in CONFIGS:
        item = summaries[config]
        summary_rows.append(
            "<tr>"
            f"<th>{html.escape(CONFIG_LABELS[config])}<small>{html.escape(config)}</small></th>"
            f"<td>{item['strict']}/{item['reps']}</td>"
            f"<td>{score_bar(item['partial_mean'])}</td>"
            f"<td>{percent(item['partial_median'])}</td>"
            f"<td>{item['f2p_passed']}/{item['f2p_total']} <small>{percent(item['f2p_passed'], item['f2p_total'])}</small></td>"
            f"<td>{item['p2p_passed']}/{item['p2p_total']} <small>{percent(item['p2p_passed'], item['p2p_total'])}</small></td>"
            f"<td>{millions(item['total_tokens'])}</td>"
            f"<td>{hours(item['agent_wall_s'])}</td>"
            f"<td>{item['valid']}/{item['reps']}</td>"
            "</tr>"
        )

    task_verdicts = {
        "obsidian-linter-link-format-conversion": (
            "good",
            "Slight edge, near ceiling",
            "Preflight+final passes 168/180 feature tests, versus 165/180 for final-only and 167/180 for baseline; preservation is perfect for all three configs.",
        ),
        "participle-grammar-conflict-analysis": (
            "bad",
            "Large regression in rep 0",
            "Preflight+final passes 14/91 feature tests—the same as baseline—while final-only passes 87/91. The current verifier trace ends in recursive stack growth during TestAnalyzeRecursiveStructure.",
        ),
        "superjson-error-stack-serialization": (
            "caution",
            "Mixed; one rep collapses",
            "Preflight+final improves reps 0 and 1 over final-only, but rep 2 falls to 33/80 feature and 105/116 preservation tests. Across three reps it trails both historical controls.",
        ),
    }
    task_rows = []
    for task, task_label in TASK_LABELS.items():
        values = document["tasks"][task]
        style, verdict, detail = task_verdicts[task]
        current_task = values["pi-check@1.5.0"]
        task_rows.append(
            "<tr>"
            f"<th>{html.escape(task_label)}<small>{html.escape(task)} · {current_task['reps']} rep(s)</small></th>"
            f"<td>{percent(values['baseline-thinkingcap-qwen36@1.1.0']['partial_mean'])}</td>"
            f"<td>{percent(values['pi-check@1.4.0']['partial_mean'])}</td>"
            f"<td>{percent(current_task['partial_mean'])}</td>"
            f"<td>{current_task['f2p_passed']}/{current_task['f2p_total']}</td>"
            f'<td><span class="tag {style}">{html.escape(verdict)}</span><small>{html.escape(detail)}</small></td>'
            "</tr>"
        )

    cell_rows = []
    for cell in document["cells"]:
        by_config = cell["configs"]
        current_cell = by_config["pi-check@1.5.0"]
        delta = cell["delta_vs_final"]
        if delta > 0.01:
            tag = '<span class="tag good">gain</span>'
        elif delta < -0.01:
            tag = '<span class="tag bad">regression</span>'
        else:
            tag = '<span class="tag neutral">near tie</span>'
        delta_class = "positive" if delta > 0 else "negative" if delta < 0 else ""
        cell_rows.append(
            "<tr>"
            f"<th>{html.escape(TASK_LABELS[cell['task']])}<small>rep {cell['rep']}</small></th>"
            f"<td>{percent(by_config['baseline-thinkingcap-qwen36@1.1.0']['reward_partial'])}</td>"
            f"<td>{percent(by_config['pi-check@1.4.0']['reward_partial'])}</td>"
            f"<td>{percent(current_cell['reward_partial'])}</td>"
            f'<td class="{delta_class}">{signed_points(delta)}</td>'
            f"<td>{current_cell['f2p_passed']}/{current_cell['f2p_total']}</td>"
            f"<td>{current_cell['p2p_passed']}/{current_cell['p2p_total']}</td>"
            f"<td>{tag}</td>"
            "</tr>"
        )

    token_delta = current["total_tokens"] / final_only["total_tokens"] - 1
    wall_delta = current["agent_wall_s"] / final_only["agent_wall_s"] - 1
    baseline_token_delta = current["total_tokens"] / baseline["total_tokens"] - 1

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ThinkingCap pi-check preflight — seven-rep mid-run snapshot</title>
<link rel="icon" href="data:,">
<style>
:root{{--bg:#f4f1ea;--surface:#fffdf8;--ink:#172033;--muted:#667085;--line:#d8d3c8;--blue:#2856d8;--green:#157347;--red:#b42318;--amber:#a15c00;--shadow:0 18px 55px rgba(27,34,55,.10)}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}} main{{max-width:1260px;margin:auto;padding:34px 22px 70px}} h1,h2,h3,p{{margin-top:0}} h1{{font-size:clamp(2.35rem,6vw,5.5rem);line-height:.94;letter-spacing:-.055em;max-width:1050px;margin-bottom:25px}} h2{{font-size:1.55rem;letter-spacing:-.025em;margin:42px 0 14px}} .eyebrow{{text-transform:uppercase;letter-spacing:.15em;font-weight:800;color:var(--blue);font-size:.76rem}} .hero{{background:linear-gradient(135deg,#fffdf8 0%,#f0f4ff 100%);border:1px solid var(--line);border-radius:28px;padding:clamp(28px,5vw,64px);box-shadow:var(--shadow)}} .hero p{{font-size:1.1rem;max-width:850px;color:#3d475a}} .pills{{display:flex;gap:9px;flex-wrap:wrap}} .pill,.tag{{display:inline-block;border-radius:999px;font-weight:800;font-size:.76rem;padding:5px 10px}} .pill{{background:#edf1fa;color:#344054}} .pill.good,.tag.good{{background:#dff4e8;color:var(--green)}} .pill.bad,.tag.bad{{background:#fee4e2;color:var(--red)}} .pill.caution,.tag.caution{{background:#fff0d5;color:var(--amber)}} .pill.neutral,.tag.neutral{{background:#e9edf5;color:#475467}} .stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:18px 0}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:17px;padding:18px;min-height:125px}} .stat strong{{display:block;font-size:1.75rem;letter-spacing:-.045em}} .stat span{{display:block;color:var(--muted);font-size:.82rem;margin-top:7px}} .panel{{background:var(--surface);border:1px solid var(--line);border-radius:20px;overflow:hidden;box-shadow:0 7px 28px rgba(27,34,55,.055)}} .table-wrap{{overflow:auto}} table{{border-collapse:collapse;width:100%;min-width:920px}} th,td{{padding:13px 14px;border-bottom:1px solid #e8e4db;text-align:right;vertical-align:top}} thead th{{background:#f8f6f0;color:#586174;font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap}} tbody th{{text-align:left;min-width:245px}} th small,td small{{display:block;color:var(--muted);font-weight:500;font-size:.75rem;margin-top:3px}} tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}} .score{{display:inline-grid;grid-template-columns:76px 44px;gap:8px;align-items:center}} .score:before{{content:"";grid-column:1;grid-row:1;height:8px;border-radius:8px;background:#e4e8f1}} .score .bar{{grid-column:1;grid-row:1;height:8px;border-radius:8px;background:var(--blue);z-index:1}} .score span:last-child{{grid-column:2}} .positive{{color:var(--green);font-weight:800}} .negative{{color:var(--red);font-weight:800}} .callout{{border-left:5px solid var(--blue);background:#eef3ff;border-radius:5px 16px 16px 5px;padding:18px 21px;margin:18px 0}} .callout.caution{{border-color:var(--amber);background:#fff7e7}} .callout.bad{{border-color:var(--red);background:#fff0ef}} .callout strong{{display:block;margin-bottom:4px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:15px}} .card{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:20px}} .card h3{{margin-bottom:7px}} .card p:last-child{{margin-bottom:0}} code{{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;background:#ece9e1;padding:2px 5px;border-radius:5px;overflow-wrap:anywhere}} footer{{color:var(--muted);font-size:.8rem;margin-top:38px}} @media(max-width:900px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}}} @media(max-width:540px){{main{{padding:18px 12px 45px}}.hero{{padding:25px 20px;border-radius:20px}}.stats{{grid-template-columns:1fr}}}}
</style>
</head>
<body><main>
<section class="hero">
<p class="eyebrow">Provisional same-model config control · frozen {SNAPSHOT_TIMESTAMP}</p>
<h1>Preflight adds churn, not a clear early lift.</h1>
<p>ThinkingCap Qwen3.6-27B is the local subject; stock Pi, final-only pi-check, and preflight+final pi-check are same-model config controls. This snapshot compares only the seven completed task/rep identities available at the freeze point. The remaining 29 reps are not scored as failures.</p>
<div class="pills"><span class="pill caution">7 / 36 complete</span><span class="pill neutral">3 tasks represented</span><span class="pill bad">0 strict solves in every config</span><span class="pill good">preflight delivered 7 / 7</span><span class="pill caution">directional, not final</span></div>
</section>
<section class="stats">
<div class="stat"><strong>{percent(current["partial_mean"])}</strong><b>mean partial</b><span>vs {percent(final_only["partial_mean"])} final-only and {percent(baseline["partial_mean"])} baseline</span></div>
<div class="stat"><strong>{current["f2p_passed"]}/{current["f2p_total"]}</strong><b>feature tests</b><span>{percent(current["f2p_passed"], current["f2p_total"])}; final-only is {percent(final_only["f2p_passed"], final_only["f2p_total"])}</span></div>
<div class="stat"><strong>{current["p2p_passed"]}/{current["p2p_total"]}</strong><b>preservation tests</b><span>{percent(current["p2p_passed"], current["p2p_total"])}; little separation here</span></div>
<div class="stat"><strong>{final_wins}–{final_losses}</strong><b>partial-score pairs</b><span>{final_ties} ties vs final-only; two large losses dominate the mean</span></div>
<div class="stat"><strong>{millions(current["total_tokens"])}</strong><b>total tokens</b><span>{percent(token_delta)} more than final-only; {percent(baseline_token_delta)} more than stock</span></div>
</section>

<h2>Matched snapshot</h2>
<div class="panel table-wrap"><table>
<thead><tr><th>Config control</th><th>Strict</th><th>Mean partial</th><th>Median partial</th><th>Feature tests</th><th>Preservation</th><th>Tokens</th><th>Agent time</th><th>Valid</th></tr></thead>
<tbody>{"".join(summary_rows)}</tbody>
</table></div>
<div class="callout caution"><strong>Read the mean and churn together.</strong>Preflight+final wins {final_wins} of 7 partial-score pairs against final-only, but its mean delta is {signed_points(statistics.mean(deltas_final))}; the median delta is {signed_points(statistics.median(deltas_final))}. Against stock it is {sum(d > 1e-12 for d in deltas_baseline)} wins, {sum(d < -1e-12 for d in deltas_baseline)} losses, and {sum(abs(d) <= 1e-12 for d in deltas_baseline)} tie, with a {signed_points(statistics.mean(deltas_baseline))} mean delta.</div>

<h2>How it is doing by task</h2>
<div class="panel table-wrap"><table>
<thead><tr><th>Task</th><th>Stock partial</th><th>Final-only partial</th><th>Preflight+final</th><th>Current feature</th><th>Early read</th></tr></thead>
<tbody>{"".join(task_rows)}</tbody>
</table></div>

<h2>Complete task × rep denominator</h2>
<div class="panel table-wrap"><table>
<thead><tr><th>Task / rep</th><th>Stock partial</th><th>Final-only partial</th><th>Preflight+final</th><th>Δ vs final</th><th>Current feature</th><th>Current preservation</th><th>Pair</th></tr></thead>
<tbody>{"".join(cell_rows)}</tbody>
</table></div>

<h2>What the trajectories say so far</h2>
<div class="grid">
<div class="card"><h3>Reliable capability</h3><p>All seven current reps completed with agent and verifier exit 0. Every session contains the preflight block/steering evidence and the final <code>Re-audit</code> marker. The Obsidian task is consistently near ceiling, with 168/180 feature tests and perfect preservation across its three reps.</p></div>
<div class="card"><h3>Largest regression</h3><p>Participle rep 0 passes only 14/91 feature tests, exactly matching stock and far below final-only's 87/91. Its verifier trace shows recursive stack growth in <code>detectFirstFirstInNode</code> while running <code>TestAnalyzeRecursiveStructure</code>. This is observed model behavior, not an infrastructure exit.</p></div>
<div class="card"><h3>Mixed SuperJSON behavior</h3><p>Current reps 0 and 1 beat final-only by +5.61 and +8.16 points, reaching 72/80 and 75/80 feature tests. Rep 2 reverses that pattern at 33/80 feature and 105/116 preservation tests, with failures spanning stack annotations, class filtering, sanitization, and cause handling.</p></div>
<div class="card"><h3>Efficiency shape</h3><p>Preflight+final uses {percent(token_delta)} more total tokens than final-only on the same seven reps, while recorded agent time is {percent(abs(wall_delta))} lower. Both pi-check configs roughly double stock's accumulated tokens. The token accounting includes repeatedly re-sent context across turns.</p></div>
</div>

<h2>Interpretation and limits</h2>
<div class="callout bad"><strong>No evidence yet for a robust preflight benefit.</strong>The architecture checkpoint was delivered correctly, but the current partial mean and feature-test total trail final-only. The best reading is high outcome variance with one clear task-specific regression and one rep-specific collapse—not a settled claim that preflight is harmful.</div>
<div class="callout"><strong>What would change the verdict.</strong>Wait for all 36 reps. A credible positive result needs strict solves or repeated feature-test gains across later tasks without a matching rise in preservation regressions. If the completed comparison retains these large losses, inspect the first consequential decision after the preflight checkpoint on Participle and SuperJSON rep 2 before changing the extension.</div>
<div class="callout caution"><strong>Historical-control caveat.</strong>All cells use the same model, high thinking, task revision, and task-specific verifier identity, but the three configs were launched from different harness revisions. This is a matched historical comparison, not a perfectly concurrent same-revision A/B. Seven reps across three tasks are too few for a final config verdict.</div>

<h2>Evidence ledger</h2>
<div class="grid">
<div class="card"><h3>Direct session and harness evidence</h3><p>Current delivery: 7/7 valid exits; 7/7 sessions contain <code>Blocked</code>, <code>Pi-check</code>, and <code>Re-audit</code>; ThinkingCap provider-request captures are present. Config locks: stock <code>bc21a52e…</code>, final-only <code>249866de…</code>, preflight+final <code>2b720421…</code>.</p></div>
<div class="card"><h3>Patch and verifier evidence</h3><p>Scores, feature/preservation numerators, and task diagnostics come from each frozen <code>result.json</code>, <code>artifacts/model.patch</code>, and verifier CTRF/run logs. The report does not infer unfinished outcomes or include quarantined results.</p></div>
<div class="card"><h3>CodeGraph evidence</h3><p>CodeGraph was used only to orient the harness analysis surface; it identified <code>harness/analyze.py</code> and the result-provenance modules. Metric claims were then computed directly from result artifacts, not from the structural graph.</p></div>
<div class="card"><h3>Snapshot scope</h3><p>Frozen at {SNAPSHOT_TIMESTAMP}: {SNAPSHOT_RUN_PROGRESS}. Included tasks: Obsidian reps 0–2, Participle rep 0, and SuperJSON reps 0–2. Full denominator: 21 trajectories, forming 7 matched three-config rows.</p></div>
</div>
<footer>Generated from local canonical result artifacts. Local subject: ThinkingCap Qwen3.6-27B AWQ INT4 · thinking=high · subset=12_v2 · provisional mid-run analysis.</footer>
</main></body></html>"""


def main() -> None:
    """Write the frozen JSON snapshot and self-contained HTML report."""
    loaded = load_snapshot_results()
    document = build_snapshot_document(loaded)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    (REPORT_ROOT / "snapshot.json").write_text(json.dumps(document, indent=2) + "\n")
    (REPORT_ROOT / "index.html").write_text(render_report(document))
    print(REPORT_ROOT / "index.html")


if __name__ == "__main__":
    main()
