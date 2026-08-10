#!/usr/bin/env python3
"""Build the self-contained ThinkingCap Qwen3.6 12_v2 run report."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
ANALYSIS_PATH = REPORT_DIR / "analysis.json"
RESULT_ROOT = Path(
    "/home/will/evals/deep-swe-bench/results/"
    "thinkingcap-qwen3.6-27b-awq-int4/high/"
    "baseline-thinkingcap-qwen36@1.1.0"
)


def escape(value: object) -> str:
    """Escape one value for safe HTML rendering."""
    return html.escape(str(value), quote=True)


def format_integer(value: float) -> str:
    """Format an integer metric with thousands separators."""
    return f"{value:,.0f}"


def format_compact(value: float) -> str:
    """Format token and byte totals in compact decimal units."""
    number = float(value)
    for suffix, divisor in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if abs(number) >= divisor:
            return f"{number / divisor:.2f}{suffix}"
    return f"{number:.0f}"


def format_percent(value: float | None, digits: int = 1) -> str:
    """Format a zero-to-one ratio as a percentage."""
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def format_duration(seconds: float) -> str:
    """Format seconds as a compact human duration."""
    total = round(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def load_current_cells() -> list[dict[str, Any]]:
    """Load all canonical result records for the completed config."""
    cells = [
        json.loads(path.read_text()) for path in RESULT_ROOT.glob("*/rep*/result.json")
    ]
    return sorted(cells, key=lambda row: (row["task"], int(row["rep"])))


def result_tag(cell: dict[str, Any]) -> str:
    """Render one observed cell outcome tag."""
    if cell["reward_binary"] == 1:
        return '<span class="tag good">solved</span>'
    if cell["reward_binary"] < 0:
        return '<span class="tag bad">invalid</span>'
    return '<span class="tag neutral">unsolved</span>'


def task_verdict(task: dict[str, Any]) -> str:
    """Classify one task's repeat-level outcome."""
    if task["solves"]:
        return '<span class="tag good">one solve</span>'
    if task["invalid"] >= 2:
        return '<span class="tag bad">unstable</span>'
    if task["invalid"]:
        return '<span class="tag caution">one invalid</span>'
    if task["mean_partial"] >= 0.98:
        return '<span class="tag caution">near miss</span>'
    return '<span class="tag neutral">unsolved</span>'


def render_task_rows(tasks: list[dict[str, Any]]) -> str:
    """Render the task-level score and efficiency table."""
    rows = []
    for task in sorted(tasks, key=lambda row: row["mean_partial"], reverse=True):
        rows.append(
            "<tr>"
            f"<td><strong>{escape(task['task'])}</strong><br><span class='muted'>{escape(task['language'])}</span></td>"
            f"<td class='num'>{task['solves']}/3</td>"
            f"<td class='num'>{task['invalid']}</td>"
            f"<td class='num'>{task['mean_partial']:.3f}</td>"
            f"<td class='num'>{format_percent(task['mean_f2p'])}</td>"
            f"<td class='num'>{format_percent(task['mean_p2p'])}</td>"
            f"<td class='num'>{format_compact(task['median_tokens'])}</td>"
            f"<td class='num'>{format_duration(task['median_wall_s'])}</td>"
            f"<td>{task_verdict(task)}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_task_bars(tasks: list[dict[str, Any]]) -> str:
    """Render deterministic CSS bars for mean partial reward by task."""
    rows = []
    for task in sorted(tasks, key=lambda row: row["mean_partial"], reverse=True):
        score = task["mean_partial"]
        color = (
            "var(--green)"
            if score >= 0.98
            else "var(--blue)"
            if score >= 0.8
            else "var(--amber)"
            if score >= 0.5
            else "var(--red)"
        )
        rows.append(
            "<div class='bar-row'>"
            f"<div class='bar-label'>{escape(task['task'])}</div>"
            "<div class='bar-track'>"
            f"<div class='bar-fill' style='width:{score * 100:.2f}%;background:{color}'></div>"
            "</div>"
            f"<div class='bar-value'>{score:.3f}</div>"
            "</div>"
        )
    return "".join(rows)


def render_cell_rows(cells: list[dict[str, Any]]) -> str:
    """Render every canonical task/rep cell."""
    rows = []
    for cell in cells:
        rows.append(
            "<tr>"
            f"<td>{escape(cell['task'])}</td>"
            f"<td class='num'>{cell['rep']}</td>"
            f"<td>{result_tag(cell)}</td>"
            f"<td class='num'>{cell['reward_partial']:.3f}</td>"
            f"<td class='num'>{format_percent(cell.get('f2p'))}</td>"
            f"<td class='num'>{format_percent(cell.get('p2p'))}</td>"
            f"<td class='num'>{format_compact(cell['total_tokens'])}</td>"
            f"<td class='num'>{cell['turns']}</td>"
            f"<td class='num'>{cell['tool_calls']}</td>"
            f"<td class='num'>{format_duration(cell['agent_wall_s'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_paired_rows(pairs: list[dict[str, Any]]) -> str:
    """Render the most material historical paired-cell movements."""
    material = [row for row in pairs if abs(row["delta_partial"]) > 0.05]
    rows = []
    for row in sorted(material, key=lambda item: item["delta_partial"], reverse=True):
        delta = row["delta_partial"]
        delta_class = "up" if delta > 0 else "down"
        rows.append(
            "<tr>"
            f"<td>{escape(row['task'])}</td>"
            f"<td class='num'>{row['rep']}</td>"
            f"<td class='num'>{row['old_partial']:.3f}</td>"
            f"<td class='num'>{row['current_partial']:.3f}</td>"
            f"<td class='num {delta_class}'>{delta:+.3f}</td>"
            f"<td class='num'>{format_compact(row['old_tokens'])}</td>"
            f"<td class='num'>{format_compact(row['current_tokens'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def build_report() -> str:
    """Build the complete HTML report from canonical result artifacts."""
    analysis = json.loads(ANALYSIS_PATH.read_text())
    current = analysis["current"]
    historical = analysis["historical"]
    overlap = analysis["historical_overlap"]
    reliability = analysis["session_reliability"]
    delivery = analysis["request_delivery"]
    cells = load_current_cells()
    invalid_rows = "".join(
        "<tr>"
        f"<td>{escape(row['task'])}</td><td class='num'>{row['rep']}</td>"
        f"<td>{escape(row['agent_exit'])}</td><td>{escape(row['verifier_exit'])}</td>"
        f"<td class='num'>{row['turns']}</td><td class='num'>{row['tool_calls']}</td>"
        f"<td class='num'>{format_duration(row['wall_s'])}</td>"
        "</tr>"
        for row in analysis["invalid_cells"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ThinkingCap Qwen3.6 27B AWQ · 12_v2 run analysis</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23335dff%22/><text x=%2250%22 y=%2264%22 text-anchor=%22middle%22 font-size=%2242%22 fill=%22white%22>TC</text></svg>" />
<style>
:root {{
  --bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;
  --line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;
  --red:#d0473f;--red-soft:#fdeceb;--amber:#b77d00;--amber-soft:#fff4d8;
  --shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);
  --radius-xl:28px;--radius-lg:20px;--max:1280px;
}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px;overflow-wrap:anywhere}}
.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}.hero,section{{background:rgba(255,255,255,.9);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}
.hero{{padding:clamp(24px,4vw,42px);overflow:hidden;position:relative}}.hero::after{{content:"";position:absolute;inset:auto -10% -35% auto;width:430px;height:430px;background:radial-gradient(circle,rgba(51,93,255,.14),transparent 70%);pointer-events:none}}
.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}
h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2.1rem,4.8vw,4.3rem);margin-top:14px;max-width:15ch}}h2{{font-size:clamp(1.45rem,2.5vw,2.1rem)}}h3{{font-size:1.12rem;margin-bottom:8px}}
.subtitle{{max-width:82ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.09rem);margin:15px 0 0}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}.pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line)}}
.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:var(--blue-2)}}
.stats{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:13px;margin-top:25px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:15px;min-height:116px;box-shadow:var(--shadow-sm)}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:9px}}.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.95rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;margin-top:8px;font-size:.86rem;color:var(--muted);font-weight:600}}
section{{margin-top:20px;padding:clamp(18px,3vw,29px)}}.section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}}.section-head p{{margin:7px 0 0;color:var(--muted);max-width:82ch}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.panel{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-sm)}}
.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:15px 17px;color:#22314d;margin-top:14px}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff9e8,#fff)}}
.callout strong{{color:var(--blue-2)}}.tag{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:.75rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}}.up{{color:var(--green);font-weight:800}}.down{{color:var(--red);font-weight:800}}.muted{{color:var(--muted);font-size:.86em}}
.table-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:14px}}table{{width:100%;border-collapse:collapse;font-size:.91rem}}th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:800;background:var(--surface-2);position:sticky;top:0}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}tbody tr:hover{{background:var(--surface-2)}}tbody tr:last-child td{{border-bottom:0}}
.bar-list{{display:grid;gap:12px}}.bar-row{{display:grid;grid-template-columns:minmax(220px,1.3fr) 2fr 54px;gap:12px;align-items:center}}.bar-label{{font-size:.86rem;font-weight:750;overflow-wrap:anywhere}}.bar-track{{height:16px;border-radius:999px;background:#edf2f7;overflow:hidden;border:1px solid #dde5ef}}.bar-fill{{height:100%;border-radius:inherit}}.bar-value{{text-align:right;font-variant-numeric:tabular-nums;font-weight:850}}
.kv{{display:grid;grid-template-columns:minmax(180px,.8fr) 2fr;gap:0}}.kv div{{padding:9px 0;border-bottom:1px solid var(--line)}}.kv .k{{color:var(--muted);font-weight:750}}details{{border:1px solid var(--line);border-radius:14px;background:var(--surface);padding:13px 15px;margin-top:12px}}summary{{cursor:pointer;font-weight:850;color:#263b66}}.artifact{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.8rem;color:var(--muted);overflow-wrap:anywhere}}
.foot{{margin-top:24px;color:var(--muted);font-size:.84rem;text-align:center}}@media(max-width:980px){{.stats{{grid-template-columns:repeat(3,minmax(0,1fr))}}.grid-2{{grid-template-columns:1fr}}}}@media(max-width:650px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.bar-row{{grid-template-columns:1fr 70px}}.bar-track{{grid-column:1/-1;grid-row:2}}.kv{{grid-template-columns:1fr}}}}
</style>
</head>
<body><div class="wrap">
<header class="hero">
  <span class="eyebrow">DeepSWE · 12_v2 · 36 cells · Pi 0.83.0</span>
  <h1>Tool calling works. Strict task quality does not.</h1>
  <p class="subtitle">ThinkingCap Qwen3.6 27B AWQ INT4 completed the full three-rep subset on server60:8081. The new contract fixed the old run's tool-call and empty-patch collapse. It still solved only one cell: preservation was almost perfect, but feature tests failed often.</p>
  <div class="pillrow"><span class="pill good">Run complete · 36/36</span><span class="pill good">0 malformed tool calls</span><span class="pill caution">1 strict solve</span><span class="pill bad">3 invalid cells</span><span class="pill neutral">98,304 cap not binding</span></div>
  <div class="stats">
    <div class="stat"><span class="label">Strict solves</span><span class="value">1 / 36</span><span class="sub">{format_percent(current["solve_rate_all"])} observed</span></div>
    <div class="stat"><span class="label">Mean partial</span><span class="value">{current["mean_partial_all"]:.3f}</span><span class="sub">{current["mean_partial_valid"]:.3f} on valid cells</span></div>
    <div class="stat"><span class="label">Feature tests · micro</span><span class="value">{format_percent(current["f2p_micro"])}</span><span class="sub">main quality bottleneck</span></div>
    <div class="stat"><span class="label">Preservation · micro</span><span class="value">{format_percent(current["p2p_micro"], 2)}</span><span class="sub">near-perfect regression safety</span></div>
    <div class="stat"><span class="label">Invalid cells</span><span class="value">3</span><span class="sub">1 agent + 2 verifier outcomes</span></div>
    <div class="stat"><span class="label">Elapsed</span><span class="value">6h 47m</span><span class="sub">2 workers · local compute</span></div>
  </div>
</header>

<section>
  <div class="section-head"><div><h2>Executive verdict</h2><p>Separate transport reliability from benchmark efficacy.</p></div></div>
  <div class="grid-2">
    <div class="callout good"><strong>Keep the server/client contract.</strong> All 72 captured requests carried the exact model, <code>max_tokens=98304</code>, thinking enabled, thinking preserved, and no hard thinking budget. Every one of 3,189 assistant turns preserved the <code>reasoning</code> signature. The sessions contain 3,518 well-formed tool calls and no raw XML tool-call leakage.</div>
    <div class="callout bad"><strong>Do not read transport success as model success.</strong> Only <code>sql-formatter rep1</code> passed every feature and preservation test. Across valid cells, preservation reached {format_percent(current["p2p_micro"], 2)} while feature tests reached {format_percent(current["f2p_micro"])}. The model usually changed the right code without completing the full contract.</div>
  </div>
  <div class="callout caution"><strong>Timeout sensitivity:</strong> observed strict score is 1/36 ({format_percent(current["solve_rate_all"])}). Excluding invalid cells gives 1/33 ({format_percent(current["solve_rate_valid"])}). The impossible best case—counting all three invalid cells as solves—is 4/36 (11.1%). The efficacy verdict stays weak across that range.</div>
</section>

<section>
  <div class="section-head"><div><h2>Run integrity and delivered behavior</h2><p>The canonical run finished, the preflight passed, and every requested task/rep has a result.</p></div></div>
  <div class="grid-2">
    <div class="panel"><div class="kv">
      <div class="k">Plan</div><div><code>sha256:908f2284…fb4dc</code></div>
      <div class="k">Config lock</div><div><code>sha256:bc21a52e…a2792</code></div>
      <div class="k">Terminal state</div><div><span class="tag good">completed</span> · stage <code>done</code></div>
      <div class="k">Preflight</div><div>1/1 passed; smoke-covered batch cell reused</div>
      <div class="k">Batch accounting</div><div>36/36 done · 32 ok · 2 failed · 1 timeout · 1 preflight-covered skip</div>
      <div class="k">Model</div><div><code>local-vllm/thinkingcap-qwen3.6-27b-awq-int4</code></div>
      <div class="k">Endpoint</div><div><code>http://100.92.238.117:8081/v1</code></div>
    </div></div>
    <div class="panel"><div class="kv">
      <div class="k">Captured requests</div><div>{delivery["captured"]} / {delivery["captured"]} exact contract matches</div>
      <div class="k">Thinking blocks</div><div>{format_integer(reliability["thinking_blocks"])} / {format_integer(reliability["assistant_messages"])}, all signature <code>reasoning</code></div>
      <div class="k">Tool calls</div><div>{format_integer(reliability["tool_call_blocks"])} well-formed; {format_integer(reliability["tool_results"])} results</div>
      <div class="k">Malformed / raw leak</div><div>0 / 0</div>
      <div class="k">Length stops</div><div>0; max response {format_integer(reliability["max_single_completion_tokens"])} tokens</div>
      <div class="k">Largest prompt</div><div>{format_integer(reliability["max_single_prompt_tokens"])} / 262,144 context tokens</div>
      <div class="k">Final stop messages</div><div>35; the agent-timeout cell ended during one in-flight tool call</div>
    </div></div>
  </div>
  <div class="callout"><strong>The 98,304-token cap did not affect this run.</strong> The largest single completion used {format_integer(reliability["max_single_completion_tokens"])} tokens ({reliability["max_single_completion_tokens"] / 98304 * 100:.1f}% of the cap), and no response stopped for length. The cap removed a risk ceiling; it did not drive the observed score.</div>
</section>

<section>
  <div class="section-head"><div><h2>Task scorecard</h2><p>Partial reward exposes near misses that the strict solve count hides. F2P is feature-to-pass; P2P is preservation-to-pass.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Solves</th><th class="num">Invalid</th><th class="num">Mean partial</th><th class="num">Mean F2P</th><th class="num">Mean P2P</th><th class="num">Median tokens</th><th class="num">Median wall</th><th>Verdict</th></tr></thead><tbody>{render_task_rows(analysis["current_tasks"])}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Mean partial reward by task</h2><p>Six tasks exceeded 0.92 mean partial, yet only one cell earned a strict solve. High partial scores mainly reflect preserved existing behavior plus incomplete feature coverage.</p></div></div>
  <div class="bar-list">{render_task_bars(analysis["current_tasks"])}</div>
</section>

<section>
  <div class="section-head"><div><h2>Invalid outcomes</h2><p>All three produced non-empty patches. None shows a provider parser failure or output-cap truncation.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Agent exit</th><th>Verifier exit</th><th class="num">Turns</th><th class="num">Tools</th><th class="num">Agent wall</th></tr></thead><tbody>{invalid_rows}</tbody></table></div>
  <details open><summary>langchain-request-coalescing · rep0 · resource exhaustion</summary><p>The agent hit the 3,600-second wall while debugging concurrent state sharing. It ended on a <code>bash</code> call with a 44.5KB patch. The verifier then began against the incomplete patch and also timed out. Primary driver: <strong>resource exhaustion after an unresolved concurrency design</strong>.</p><div class="artifact">{escape(RESULT_ROOT / "langchain-request-coalescing/rep0")}</div></details>
  <details open><summary>langchain-request-coalescing · rep1 · incomplete concurrency semantics</summary><p>The agent finished normally, but four of 50 feature tests failed. Joiners received <code>None</code> instead of completed values, clear did not cancel sync or async waiters, and teardown spent 300 seconds joining threads. Primary driver: <strong>missing concurrency invariants</strong>; the verifier timeout followed a patch-induced teardown hang.</p><div class="artifact">{escape(RESULT_ROOT / "langchain-request-coalescing/rep1/verifier/new.log")}</div></details>
  <details open><summary>mobly-grouped-test-barriers · rep1 · ambiguous verifier timeout</summary><p>The agent finished and produced a 46.7KB patch after 65 turns. The verifier emitted no result log before timing out. Two sibling reps graded normally, while the historical deployment timed out on all three Mobly reps. Disposition: <strong>observed invalid, mechanism ambiguous</strong>; the artifacts do not justify calling it pure infrastructure or pure patch behavior.</p><div class="artifact">{escape(RESULT_ROOT / "mobly-grouped-test-barriers/rep1")}</div></details>
</section>

<section>
  <div class="section-head"><div><h2>Historical port-30000 baseline</h2><p>Directional context only. This is not an isolated output-cap experiment: the endpoint, served model identity, checkpoint/deployment, vLLM path, tool contract, output ceiling, and thinking budget changed. The old unversioned baseline also has only 35 result files.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Historical baseline</th><th class="num">Current 1.1.0</th><th>Read</th></tr></thead><tbody>
    <tr><td>Cells</td><td class="num">35</td><td class="num">36</td><td><span class="tag caution">old missing one</span></td></tr>
    <tr><td>Strict solves</td><td class="num">{historical["solves"]}</td><td class="num">{current["solves"]}</td><td><span class="tag neutral">net tied</span></td></tr>
    <tr><td>Invalid outcomes</td><td class="num">{historical["invalid"]}</td><td class="num">{current["invalid"]}</td><td><span class="tag good">16 → 3</span></td></tr>
    <tr><td>Empty patches</td><td class="num">{historical["empty_patches"]}</td><td class="num">{current["empty_patches"]}</td><td><span class="tag good">13 → 0</span></td></tr>
    <tr><td>Mean partial · all</td><td class="num">{historical["mean_partial_all"]:.3f}</td><td class="num">{current["mean_partial_all"]:.3f}</td><td><span class="tag good">+{current["mean_partial_all"] - historical["mean_partial_all"]:.3f}</span></td></tr>
    <tr><td>Mean partial · valid only</td><td class="num">{historical["mean_partial_valid"]:.3f}</td><td class="num">{current["mean_partial_valid"]:.3f}</td><td><span class="tag neutral">essentially tied</span></td></tr>
    <tr><td>Median tokens / cell</td><td class="num">{format_compact(historical["median_total_tokens"])}</td><td class="num">{format_compact(current["median_total_tokens"])}</td><td>higher because runs now continue</td></tr>
    <tr><td>Median agent wall</td><td class="num">{format_duration(historical["wall_median_s"])}</td><td class="num">{format_duration(current["wall_median_s"])}</td><td><span class="tag good">41% lower</span></td></tr>
  </tbody></table></div>
  <div class="callout good"><strong>The gain is reliability, not conditional patch quality.</strong> Invalid outcomes fell from 16/35 to 3/36 and empty patches from 13 to zero. But valid-only mean partial stayed flat: {historical["mean_partial_valid"]:.3f} historically versus {current["mean_partial_valid"]:.3f} now.</div>
  <div class="grid-2">
    <div class="panel"><h3>Matched-cell churn · 35 pairs</h3><div class="kv">
      <div class="k">Current-only solves</div><div>{overlap["current_only_solves"]}</div><div class="k">Historical-only solves</div><div>{overlap["old_only_solves"]}</div>
      <div class="k">Both solved</div><div>{overlap["both_solved"]}</div><div class="k">Partial wins &gt; 0.05</div><div>{overlap["partial_wins_gt_005"]}</div>
      <div class="k">Partial losses &lt; −0.05</div><div>{overlap["partial_losses_lt_minus_005"]}</div><div class="k">Within ±0.05</div><div>{overlap["partial_ties_within_005"]}</div>
      <div class="k">Mean paired partial delta</div><div class="up">+{overlap["mean_partial_delta"]:.3f}</div><div class="k">Median paired delta</div><div>+{overlap["median_partial_delta"]:.3f}</div>
    </div></div>
    <div class="panel"><h3>Comparison boundary</h3><p>The old baseline used <code>bottlecapai/ThinkingCap-Qwen3.6-27B</code> on port 30000, an 81,920 output setting, and a 32,768 hard thinking budget. The current run used the AWQ INT4 checkpoint on port 8081, vLLM 0.25.1, a 98,304 output setting, and no hard thinking budget. Treat every delta as a bundle, not a causal estimate.</p><p class="muted">Missing historical pair: <code>obsidian-linter-link-format-conversion/rep2</code>.</p></div>
  </div>
  <details open id="packet-sql"><summary>Solve flip packet · current-only · sql-formatter rep1</summary><p><strong>Historical:</strong> one assistant completion, zero tool calls, no patch, reward −1. The server reported 131,072 output tokens before the trajectory stopped. <strong>Current:</strong> 84 turns, 98 tool calls, 17.5KB patch, 26/26 F2P and 5,709/5,709 P2P tests, strict reward 1. Earliest divergence: the current route parsed the first tool call and entered the repository; the old route never did.</p><p>Driver: <strong>protocol/interface delivery</strong>. This is strong evidence that the new contract fixed a historical execution failure, but not evidence that the 98,304 cap alone caused the gain.</p></details>
  <details open id="packet-claude"><summary>Solve flip packet · historical-only · recursive delegation rep0</summary><p>Both trajectories had nearly identical scale: historical 42 turns / 50 tools; current 43 turns / 51 tools. Historical passed 7/7 feature tests. Current passed 0/7 while preserving 31/31 existing tests. Failures covered circular blocking, propagated child errors, specified-agent execution, empty child output, unknown agents, empty instructions, and multi-level delegation.</p><p>Driver: <strong>wrong seam or under-implementation</strong>, not transport. The current model executed normally and preserved the codebase, but its patch missed the required recursive-delegation contract.</p></details>
  <div class="table-wrap" style="margin-top:16px"><table><thead><tr><th>Material paired cell</th><th class="num">Rep</th><th class="num">Old partial</th><th class="num">Current partial</th><th class="num">Delta</th><th class="num">Old tokens</th><th class="num">Current tokens</th></tr></thead><tbody>{render_paired_rows(analysis["paired_cells"])}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Resource profile</h2><p>Native session usage sums every repeated prompt across turns; these totals are accounting volume, not unique context text.</p></div></div>
  <div class="stats">
    <div class="stat"><span class="label">Total tokens</span><span class="value">{format_compact(current["total_tokens"])}</span><span class="sub">{format_compact(current["input_tokens"])} input</span></div>
    <div class="stat"><span class="label">Output tokens</span><span class="value">{format_compact(current["output_tokens"])}</span><span class="sub">0 cache-read tokens reported</span></div>
    <div class="stat"><span class="label">Median / cell</span><span class="value">{format_compact(current["median_total_tokens"])}</span><span class="sub">P90 {format_compact(current["p90_total_tokens"])}</span></div>
    <div class="stat"><span class="label">Turns</span><span class="value">{format_integer(current["turns"])}</span><span class="sub">{format_integer(current["tool_calls"])} tool calls</span></div>
    <div class="stat"><span class="label">Agent wall sum</span><span class="value">{format_duration(current["wall_sum_s"])}</span><span class="sub">two-way concurrency</span></div>
    <div class="stat"><span class="label">Patch volume</span><span class="value">{format_compact(current["patch_bytes"])}</span><span class="sub">includes one 2.10MB outlier</span></div>
  </div>
  <div class="callout caution"><strong>Input dominates accounting.</strong> Repeated full-context prompts produced {format_compact(current["input_tokens"])} input tokens versus {format_compact(current["output_tokens"])} output tokens. Prefix caching was enabled server-side, but Pi's native usage records reported zero cache-read tokens, so this report cannot quantify physical cache savings.</div>
</section>

<section>
  <div class="section-head"><div><h2>All 36 observed cells</h2><p>Primary intention-to-treat outcomes. Invalid cells remain in the denominator with partial reward zero.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Outcome</th><th class="num">Partial</th><th class="num">F2P</th><th class="num">P2P</th><th class="num">Tokens</th><th class="num">Turns</th><th class="num">Tools</th><th class="num">Wall</th></tr></thead><tbody>{render_cell_rows(cells)}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Decision</h2></div></div>
  <div class="callout good"><strong>Operational verdict: keep.</strong> The port-8081 configuration delivered thinking, reasoning replay, streaming tool calls, and multi-turn execution without malformed calls, raw XML leakage, or output truncation.</div>
  <div class="callout bad"><strong>Benchmark verdict: weak.</strong> One solve in 36 cells is not competitive. The model preserved existing behavior but routinely missed feature requirements; strict efficacy did not improve over the historical baseline despite a large reliability gain.</div>
  <div class="callout"><strong>Next test, if wanted:</strong> change model capability or agent behavior, not the output cap. This run never approached 98,304 tokens in one completion. Any follow-up should target feature-contract representation, completion audits, and concurrency invariants while keeping this proven provider contract fixed.</div>
</section>

<div class="foot">Generated from canonical <code>result.json</code>, native <code>session/*.jsonl</code>, provider captures, verifier artifacts, and structured run state. <a href="analysis.json">Download the metric dataset</a>.<br><code>baseline-thinkingcap-qwen36@1.1.0</code> · plan <code>sha256:908f2284…fb4dc</code> · run completed 2026-08-03 12:08:35Z</div>
</div></body></html>"""


def main() -> None:
    """Write the deterministic self-contained report page."""
    output = REPORT_DIR / "index.html"
    output.write_text(build_report())
    print(output)


if __name__ == "__main__":
    main()
