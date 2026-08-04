#!/usr/bin/env python3
"""Build the self-contained ThinkingCap 36_v2 run analysis report."""

from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
ANALYSIS_PATH = REPORT_DIR / "analysis.json"


def escape(value: object) -> str:
    """Escape one value for safe HTML rendering."""
    return html.escape(str(value), quote=True)


def format_percent(value: float | None, digits: int = 1) -> str:
    """Format a zero-to-one ratio as a percentage."""
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def format_delta(value: float, digits: int = 3) -> str:
    """Format a signed numeric delta."""
    return f"{value:+.{digits}f}"


def format_compact(value: float | None) -> str:
    """Format a count using compact decimal units."""
    if value is None:
        return "—"
    number = float(value)
    for suffix, divisor in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if abs(number) >= divisor:
            return f"{number / divisor:.2f}{suffix}"
    return f"{number:.0f}"


def format_duration(seconds: float | None) -> str:
    """Format seconds as a compact human duration."""
    if seconds is None:
        return "—"
    total = round(float(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def outcome_tag(outcome: str) -> str:
    """Render an observed cell outcome tag."""
    css_class = {"solved": "good", "invalid": "bad", "unsolved": "neutral"}[outcome]
    return f'<span class="tag {css_class}">{escape(outcome)}</span>'


def delta_class(value: float) -> str:
    """Return the visual class for a signed delta."""
    if value > 0.0005:
        return "up"
    if value < -0.0005:
        return "down"
    return "flat"


def render_task_rows(tasks: list[dict[str, Any]]) -> str:
    """Render task-level score, validity, and efficiency comparisons."""
    rows = []
    for task in sorted(tasks, key=lambda row: row["delta_partial"], reverse=True):
        delta = float(task["delta_partial"])
        rows.append(
            "<tr>"
            f"<td><strong>{escape(task['task'])}</strong></td>"
            f"<td class='num'>{task['base_solves']}/3</td>"
            f"<td class='num'>{task['thinkingcap_solves']}/3</td>"
            f"<td class='num'>{task['base_invalid']}</td>"
            f"<td class='num'>{task['thinkingcap_invalid']}</td>"
            f"<td class='num'>{task['base_mean_partial']:.3f}</td>"
            f"<td class='num'>{task['thinkingcap_mean_partial']:.3f}</td>"
            f"<td class='num {delta_class(delta)}'>{format_delta(delta)}</td>"
            f"<td class='num'>{format_compact(task['base_median_tokens'])}</td>"
            f"<td class='num'>{format_compact(task['thinkingcap_median_tokens'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_task_delta_bars(tasks: list[dict[str, Any]]) -> str:
    """Render deterministic diverging task-level partial-delta bars."""
    max_delta = max(abs(float(task["delta_partial"])) for task in tasks)
    rows = []
    for task in sorted(tasks, key=lambda row: row["delta_partial"], reverse=True):
        delta = float(task["delta_partial"])
        width = abs(delta) / max_delta * 48 if max_delta else 0
        side_class = "positive" if delta >= 0 else "negative"
        rows.append(
            "<div class='delta-row'>"
            f"<div class='delta-label'>{escape(task['task'])}</div>"
            "<div class='delta-track'><div class='delta-zero'></div>"
            f"<div class='delta-bar {side_class}' style='width:{width:.2f}%'></div></div>"
            f"<div class='delta-value {delta_class(delta)}'>{format_delta(delta)}</div>"
            "</div>"
        )
    return "".join(rows)


def render_language_rows(languages: list[dict[str, Any]]) -> str:
    """Render language-level capability-shape comparisons."""
    rows = []
    for language in languages:
        delta = float(language["delta_partial"])
        rows.append(
            "<tr>"
            f"<td><strong>{escape(language['language'])}</strong></td>"
            f"<td class='num'>{language['cells']}</td>"
            f"<td class='num'>{language['base_mean_partial']:.3f}</td>"
            f"<td class='num'>{language['thinkingcap_mean_partial']:.3f}</td>"
            f"<td class='num {delta_class(delta)}'>{format_delta(delta)}</td>"
            f"<td class='num'>{language['base_invalid']}</td>"
            f"<td class='num'>{language['thinkingcap_invalid']}</td>"
            f"<td class='num'>{format_compact(language['base_median_tokens'])}</td>"
            f"<td class='num'>{format_compact(language['thinkingcap_median_tokens'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_all_cell_rows(cells: list[dict[str, Any]]) -> str:
    """Render every matched task and rep before filtered packet examples."""
    rows = []
    for row in sorted(cells, key=lambda item: (item["task"], item["rep"])):
        delta = float(row["delta_partial"])
        rows.append(
            "<tr>"
            f"<td>{escape(row['task'])}<br><span class='muted'>{escape(row['language'])}</span></td>"
            f"<td class='num'>{row['rep']}</td>"
            f"<td>{outcome_tag(row['base']['outcome'])}</td>"
            f"<td class='num'>{float(row['base']['reward_partial'] or 0):.3f}</td>"
            f"<td class='num'>{format_percent(row['base']['f2p'])}</td>"
            f"<td>{outcome_tag(row['thinkingcap']['outcome'])}</td>"
            f"<td class='num'>{float(row['thinkingcap']['reward_partial'] or 0):.3f}</td>"
            f"<td class='num'>{format_percent(row['thinkingcap']['f2p'])}</td>"
            f"<td class='num {delta_class(delta)}'>{format_delta(delta)}</td>"
            f"<td class='num'>{format_compact(row['base']['total_tokens'])}</td>"
            f"<td class='num'>{format_compact(row['thinkingcap']['total_tokens'])}</td>"
            f"<td class='num'>{format_duration(row['base']['agent_wall_s'])}</td>"
            f"<td class='num'>{format_duration(row['thinkingcap']['agent_wall_s'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_substrate_rows(substrate: dict[str, Any]) -> str:
    """Render the deployment and provenance confound ledger."""
    rows = []
    for row in substrate["differences"]:
        role = (
            '<span class="tag caution">intended contrast</span>'
            if row["intentional"]
            else '<span class="tag bad">confound</span>'
        )
        rows.append(
            "<tr>"
            f"<td><strong>{escape(row['surface'])}</strong></td>"
            f"<td>{escape(row['base'])}</td>"
            f"<td>{escape(row['thinkingcap'])}</td>"
            f"<td>{role}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_tool_rows(base: dict[str, Any], thinkingcap: dict[str, Any]) -> str:
    """Render tool-result error numerators and denominators by tool."""
    rows = []
    tools = sorted(set(base["tool_results"]) | set(thinkingcap["tool_results"]))
    for tool in tools:
        base_results = int(base["tool_results"].get(tool, 0))
        base_errors = int(base["tool_errors"].get(tool, 0))
        tc_results = int(thinkingcap["tool_results"].get(tool, 0))
        tc_errors = int(thinkingcap["tool_errors"].get(tool, 0))
        rows.append(
            "<tr>"
            f"<td><code>{escape(tool)}</code></td>"
            f"<td class='num'>{base_errors} / {base_results}</td>"
            f"<td class='num'>{format_percent(base_errors / base_results if base_results else None)}</td>"
            f"<td class='num'>{tc_errors} / {tc_results}</td>"
            f"<td class='num'>{format_percent(tc_errors / tc_results if tc_results else None)}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_error_cause_rows(base: dict[str, Any], thinkingcap: dict[str, Any]) -> str:
    """Render interpreted tool-result error causes."""
    causes = sorted(
        set(base["tool_error_causes"]) | set(thinkingcap["tool_error_causes"])
    )
    return "".join(
        "<tr>"
        f"<td>{escape(cause.replace('_', ' '))}</td>"
        f"<td class='num'>{base['tool_error_causes'].get(cause, 0)}</td>"
        f"<td class='num'>{thinkingcap['tool_error_causes'].get(cause, 0)}</td>"
        "</tr>"
        for cause in causes
    )


def render_invalid_rows(cells: list[dict[str, Any]]) -> str:
    """Render the union of invalid cells and their paired outcomes."""
    invalid_union = [
        row
        for row in cells
        if row["base"]["outcome"] == "invalid"
        or row["thinkingcap"]["outcome"] == "invalid"
    ]
    rows = []
    for row in invalid_union:
        rows.append(
            "<tr>"
            f"<td>{escape(row['task'])}</td>"
            f"<td class='num'>{row['rep']}</td>"
            f"<td>{outcome_tag(row['base']['outcome'])}<br><span class='muted'>agent={escape(row['base']['agent_exit'])}; verifier={escape(row['base']['verifier_exit'])}; {format_duration(row['base']['agent_wall_s'])}</span></td>"
            f"<td>{outcome_tag(row['thinkingcap']['outcome'])}<br><span class='muted'>agent={escape(row['thinkingcap']['agent_exit'])}; verifier={escape(row['thinkingcap']['verifier_exit'])}; {format_duration(row['thinkingcap']['agent_wall_s'])}</span></td>"
            f"<td class='num {delta_class(float(row['delta_partial']))}'>{format_delta(float(row['delta_partial']))}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_packet_rows(packets: list[dict[str, Any]]) -> str:
    """Render selected trajectory packets and evidence-backed classifications."""
    rows = []
    for packet in sorted(
        packets, key=lambda row: abs(row["delta"]["partial"]), reverse=True
    ):
        classification = packet["classification"]
        packet_id = packet["packet_id"]
        delta = float(packet["delta"]["partial"])
        rows.append(
            "<tr>"
            f"<td><strong>{escape(packet['pair']['task'])}</strong><br><span class='muted'>rep {packet['pair']['rep']} · {escape(packet['pair']['language'])}</span></td>"
            f"<td class='num {delta_class(delta)}'>{format_delta(delta)}</td>"
            f"<td>{escape(', '.join(packet['pair']['triggers']))}</td>"
            f"<td><span class='tag neutral'>{escape(classification['primary_bucket'])}</span><br><span class='muted'>{escape(classification.get('secondary_bucket') or '')}</span></td>"
            f"<td>{escape(classification['mechanism'])}</td>"
            f"<td><a href='packets/{escape(packet_id)}.md'>packet</a> · <a href='packets/{escape(packet_id)}.json'>JSON</a></td>"
            "</tr>"
        )
    return "".join(rows)


def render_bucket_rows(packets: list[dict[str, Any]]) -> str:
    """Render primary driver counts within the selected packet cohort."""
    counts = Counter(packet["classification"]["primary_bucket"] for packet in packets)
    return "".join(
        "<tr>"
        f"<td>{escape(bucket)}</td><td class='num'>{count}</td>"
        f"<td class='num'>{format_percent(count / len(packets))}</td>"
        "</tr>"
        for bucket, count in counts.most_common()
    )


def render_scaffold_rows(ledger: list[dict[str, Any]]) -> str:
    """Render checkable support hypotheses and minimal experiments."""
    return "".join(
        "<tr>"
        f"<td><strong>{escape(row['observed_weakness'])}</strong><br><span class='muted'>{escape(row['failure_layer'])}</span></td>"
        f"<td>{escape(row['candidate_support'])}<br><span class='muted'>{escape(row['expected_mechanism'])}</span></td>"
        f"<td>{escape(row['minimal_experiment'])}</td>"
        f"<td>{escape(row['success_criterion'])}</td>"
        f"<td>{escape(row['non_targets'])}<br><span class='muted'>Risk: {escape(row['risk'])}</span></td>"
        "</tr>"
        for row in ledger
    )


def build_report() -> str:
    """Build the complete HTML report from extracted paired artifacts."""
    analysis = json.loads(ANALYSIS_PATH.read_text())
    base = analysis["base"]
    thinkingcap = analysis["thinkingcap"]
    paired = analysis["paired_statistics"]
    delivery_base = analysis["delivery"]["base"]
    delivery_tc = analysis["delivery"]["thinkingcap"]
    packets = analysis["packets"]
    run_audit = analysis["thinkingcap_run_audit"]
    watchdog = run_audit["watchdog"]
    solve_ci_low, solve_ci_high = thinkingcap["solve_rate_wilson_95_ci"]
    token_reduction = 1 - thinkingcap["total_tokens"] / base["total_tokens"]
    wall_reduction = 1 - thinkingcap["wall_sum_s"] / base["wall_sum_s"]
    turn_reduction = 1 - thinkingcap["turns"] / base["turns"]
    tool_reduction = 1 - thinkingcap["tool_calls"] / base["tool_calls"]
    ci_low, ci_high = paired["task_cluster_bootstrap_95_ci"]
    base_tool_errors = sum(delivery_base["tool_errors"].values())
    base_tool_results = sum(delivery_base["tool_results"].values())
    tc_tool_errors = sum(delivery_tc["tool_errors"].values())
    tc_tool_results = sum(delivery_tc["tool_results"].values())
    completion_claims = sum(
        packet["classification"] is not None
        and json.loads(
            (REPORT_DIR / "packets" / f"{packet['packet_id']}.json").read_text()
        )["thinkingcap"]["stage_ledger"]["completion_audit"]["claimed_completion"]
        for packet in packets
    )
    completion_claims_not_solved = sum(
        json.loads(
            (REPORT_DIR / "packets" / f"{packet['packet_id']}.json").read_text()
        )["thinkingcap"]["stage_ledger"]["completion_audit"]["claimed_completion"]
        and next(
            row
            for row in analysis["paired_cells"]
            if row["task"] == packet["pair"]["task"]
            and row["rep"] == packet["pair"]["rep"]
        )["thinkingcap"]["outcome"]
        != "solved"
        for packet in packets
    )

    shared_items = "".join(
        f"<li>{escape(item)}</li>"
        for item in analysis["substrate_comparability"]["shared"]
    )
    negative_items = "".join(
        f"<li>{escape(item)}</li>" for item in analysis["negative_evidence"]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ThinkingCap Qwen3.6 27B · 36_v2 run analysis</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23335dff%22/><text x=%2250%22 y=%2264%22 text-anchor=%22middle%22 font-size=%2238%22 fill=%22white%22>TC</text></svg>" />
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#b77d00;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);--radius-xl:28px;--radius-lg:20px;--max:1440px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.91em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px;overflow-wrap:anywhere}}.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}.hero,section{{background:rgba(255,255,255,.91);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}.hero{{padding:clamp(24px,4vw,44px);overflow:hidden;position:relative}}.hero::after{{content:"";position:absolute;inset:auto -8% -45% auto;width:470px;height:470px;background:radial-gradient(circle,rgba(51,93,255,.15),transparent 70%);pointer-events:none}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2rem,4.7vw,4.25rem);margin-top:14px;max-width:16ch}}h2{{font-size:clamp(1.45rem,2.5vw,2.1rem)}}h3{{font-size:1.12rem;margin-bottom:8px}}.subtitle{{max-width:88ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.1rem);margin:15px 0 0}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}.pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line)}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:var(--blue-2)}}.stats{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:13px;margin-top:25px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:15px;min-height:118px;box-shadow:var(--shadow-sm)}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:9px}}.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.9rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;margin-top:8px;font-size:.84rem;color:var(--muted);font-weight:600}}section{{margin-top:20px;padding:clamp(18px,3vw,30px)}}.section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}}.section-head p{{margin:7px 0 0;color:var(--muted);max-width:90ch}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;min-width:0}}.grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;min-width:0}}.grid-2>*,.grid-3>*{{min-width:0}}.panel{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-sm);min-width:0}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:15px 17px;color:#22314d;margin-top:14px}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff9e8,#fff)}}.callout strong{{color:var(--blue-2)}}.tag{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:.73rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}}.up{{color:var(--green);font-weight:850}}.down{{color:var(--red);font-weight:850}}.flat{{color:var(--muted);font-weight:750}}.muted{{color:var(--muted);font-size:.86em}}.table-wrap{{overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:14px}}table{{width:100%;border-collapse:collapse;font-size:.88rem}}th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:800;background:var(--surface-2);position:sticky;top:0}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}tbody tr:hover{{background:var(--surface-2)}}tbody tr:last-child td{{border-bottom:0}}ul.clean{{margin:0;padding-left:20px}}ul.clean li{{margin:7px 0}}.delta-list{{display:grid;gap:10px}}.delta-row{{display:grid;grid-template-columns:minmax(250px,1.3fr) 2fr 60px;gap:10px;align-items:center}}.delta-label{{font-size:.84rem;font-weight:750;overflow-wrap:anywhere}}.delta-track{{height:16px;background:#edf2f7;border-radius:999px;position:relative;overflow:hidden;border:1px solid #dde5ef}}.delta-zero{{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#93a1b6;z-index:2}}.delta-bar{{position:absolute;top:0;bottom:0}}.delta-bar.positive{{left:50%;background:var(--green)}}.delta-bar.negative{{right:50%;background:var(--red)}}.delta-value{{text-align:right;font-variant-numeric:tabular-nums}}.artifact{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.79rem;color:var(--muted);overflow-wrap:anywhere}}details{{border:1px solid var(--line);border-radius:14px;background:var(--surface);padding:13px 15px;margin-top:12px}}summary{{cursor:pointer;font-weight:850;color:#263b66}}.foot{{margin-top:24px;color:var(--muted);font-size:.84rem;text-align:center}}@media(max-width:1100px){{.stats{{grid-template-columns:repeat(3,minmax(0,1fr))}}.grid-3{{grid-template-columns:1fr}}}}@media(max-width:850px){{.grid-2{{grid-template-columns:1fr}}}}@media(max-width:650px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.delta-row{{grid-template-columns:1fr 58px}}.delta-track{{grid-column:1/-1;grid-row:2}}.wrap{{padding:14px 8px 30px}}section,.hero{{border-radius:20px}}}}
</style>
</head>
<body><div class="wrap">
<header class="hero">
  <span class="eyebrow">ThinkingCap baseline · 36_v2 · 108 reps · high thinking</span>
  <h1>Same finished-rep quality, 21% fewer tokens.</h1>
  <p class="subtitle">ThinkingCap Qwen3.6 27B produced 3 strict solves, 104 valid grades, 67.6% feature-test micro, and 99.93% preservation-test micro across 36 tasks × 3 reps. Against the matched but confounded stock-Qwen + pi-codex-goal contrast, common-valid mean partial was effectively unchanged while ThinkingCap used materially fewer tokens and agent time.</p>
  <div class="pillrow"><span class="pill good">3 / 108 strict solves</span><span class="pill good">104 / 108 valid</span><span class="pill good">{format_percent(token_reduction)} fewer tokens</span><span class="pill good">{format_percent(wall_reduction)} less agent wall</span><span class="pill good">0 malformed calls</span><span class="pill caution">4 invalid reps</span></div>
  <div class="stats">
    <div class="stat"><span class="label">Strict solve rate</span><span class="value">{format_percent(thinkingcap["solve_rate"])}</span><span class="sub">95% Wilson {format_percent(solve_ci_low)}–{format_percent(solve_ci_high)}</span></div>
    <div class="stat"><span class="label">Mean partial</span><span class="value">{thinkingcap["mean_partial_all"]:.3f}</span><span class="sub">valid-only {thinkingcap["mean_partial_valid"]:.3f}</span></div>
    <div class="stat"><span class="label">Feature tests</span><span class="value">{format_percent(thinkingcap["f2p_micro"])}</span><span class="sub">{thinkingcap["f2p_passed"]:,} / {thinkingcap["f2p_total"]:,}</span></div>
    <div class="stat"><span class="label">Preservation</span><span class="value">{format_percent(thinkingcap["p2p_micro"], 2)}</span><span class="sub">{thinkingcap["p2p_passed"]:,} / {thinkingcap["p2p_total"]:,}</span></div>
    <div class="stat"><span class="label">Total tokens</span><span class="value">{format_compact(thinkingcap["total_tokens"])}</span><span class="sub">median {format_compact(thinkingcap["median_total_tokens"])} / rep</span></div>
    <div class="stat"><span class="label">Agent wall sum</span><span class="value">{format_duration(thinkingcap["wall_sum_s"])}</span><span class="sub">median {format_duration(thinkingcap["wall_median_s"])}</span></div>
  </div>
</header>

<section>
  <div class="section-head"><div><h2>Executive reading</h2><p>What ThinkingCap demonstrated, where it broke, and what the next config can test.</p></div></div>
  <div class="grid-2">
    <div class="callout good"><strong>The efficiency objective held.</strong> Relative to stock Qwen + pi-codex-goal on the same 108 addresses, ThinkingCap used {format_percent(token_reduction)} fewer total tokens, {format_percent(wall_reduction)} less summed agent time, {format_percent(turn_reduction)} fewer turns, and {format_percent(tool_reduction)} fewer tool calls.</div>
    <div class="callout good"><strong>Finished-rep quality held.</strong> Across {paired["common_valid_pairs"]} pairs graded on both sides, mean partial moved only {format_delta(paired["mean_delta_partial_common_valid"])}. The 36-task clustered interval for the all-rep delta spans zero: {format_delta(ci_low)} to {format_delta(ci_high)}.</div>
    <div class="callout bad"><strong>Strict completion stayed rare.</strong> Only 3 of 108 reps solved. ThinkingCap preserved existing behavior almost perfectly, but feature-test micro stopped at {format_percent(thinkingcap["f2p_micro"])}; near-perfect partial scores often hid several required feature failures.</div>
    <div class="callout caution"><strong>The next run is a combined intervention.</strong> The proven <code>pi-check@1.4.0</code> config adds an unchanged final re-audit and a 360-second default for Bash calls without numeric timeouts. It can test completion and reliability together, but not isolate which mechanism caused any movement.</div>
  </div>
  <div class="callout"><strong>Completion-audit signal:</strong> {completion_claims} of the 15 selected ThinkingCap trajectories claimed completion; {completion_claims_not_solved} of those still ended unsolved or invalid. That is the clearest process-level target for pi-check.</div>
</section>

<section>
  <div class="section-head"><div><h2>Run integrity and provenance</h2><p>The analysis includes all approved exact reuses and all new 36_v2 executions; quarantined results are excluded.</p></div></div>
  <div class="grid-3">
    <div class="panel"><h3>Immutable launch</h3><p><strong>Plan:</strong> <code>{escape(run_audit["plan_identity"])}</code></p><p><strong>Config lock:</strong> <code>{escape(run_audit["config_lock_identity"])}</code></p><p><strong>Config:</strong> <code>baseline-thinkingcap-qwen36@1.1.0</code></p></div>
    <div class="panel"><h3>Nested-subset reuse</h3><p><strong>{run_audit["exact_reused_entries"]}</strong> exact 12_v2 result files were hash-pinned and reused.</p><p><strong>{run_audit["new_execution_entries"]}</strong> reps were executed for the 24 added tasks.</p><p class="muted">The two provenance groups are explicit because selection-wide task and planner hashes differ.</p></div>
    <div class="panel"><h3>Terminal state</h3><p><strong>108 / 108</strong> batch entries accounted for.</p><p><strong>69</strong> new-result executions reported ok; <strong>2</strong> run-timeouts; <strong>37</strong> skips include exact reuse and the preflight-covered entry.</p><p><strong>No empty patches.</strong></p></div>
  </div>
  <div class="callout caution"><strong>Memory pressure was observed, not hidden.</strong> The 12 GiB watchdog saw {watchdog["alert_events"]} alert-only events in {watchdog["alert_containers"]} ThinkingCap container and made {watchdog["interventions"]} interventions. Meriyah rep2 peaked at {watchdog["peak_container_gib"]:.2f} GiB during Vitest fan-out because no single killable process exceeded the 6 GiB action threshold.</div>
  <details><summary>Provenance groups</summary><p class="artifact">36 reused reps: prior 12_v2 task/harness/plan identities. 72 new reps: task <code>{escape(run_audit["task_revision"])}</code>, harness <code>{escape(run_audit["harness_revision"])}</code>, plan <code>{escape(run_audit["plan_identity"])}</code>. The reuse manifest audit proved the selected 12 task files, images, verifiers, config lock, model, and thinking were unchanged.</p></details>
</section>

<section>
  <div class="section-head"><div><h2>Contextual stock-Qwen contrast</h2><p>ThinkingCap is the local subject. Stock Qwen + pi-codex-goal is a local contrast, not a config control or frontier reference.</p></div></div>
  <div class="grid-2">
    <div class="panel"><h3>Shared execution surface</h3><ul class="clean">{shared_items}</ul></div>
    <div class="panel"><h3>Interpretation limit</h3><p>{escape(analysis["contextual_contrast_limit"])}</p><p><span class="tag caution">stock ambiguous</span> {escape(analysis["delivery_classification"]["base_qwen_reason"])}</p><p><span class="tag good">ThinkingCap delivered</span> {escape(analysis["delivery_classification"]["thinkingcap_reason"])}</p></div>
  </div>
  <div class="table-wrap" style="margin-top:16px"><table><thead><tr><th>Surface</th><th>Stock Qwen + goal</th><th>ThinkingCap baseline</th><th>Role</th></tr></thead><tbody>{render_substrate_rows(analysis["substrate_comparability"])}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Aggregate capability and efficiency</h2><p>Strict solves are threshold-sensitive; common-valid partial and test denominators show the broader profile.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Stock Qwen + goal</th><th class="num">ThinkingCap baseline</th><th>Reading</th></tr></thead><tbody>
    <tr><td>Strict solves</td><td class="num">{base["solves"]} / 108</td><td class="num">{thinkingcap["solves"]} / 108</td><td>Eight one-sided solve flips; no pair solved on both sides</td></tr>
    <tr><td>Valid / invalid</td><td class="num">{base["valid"]} / {base["invalid"]}</td><td class="num">{thinkingcap["valid"]} / {thinkingcap["invalid"]}</td><td>ThinkingCap graded two more reps</td></tr>
    <tr><td>Mean partial · all reps</td><td class="num">{base["mean_partial_all"]:.3f}</td><td class="num">{thinkingcap["mean_partial_all"]:.3f}</td><td class="{delta_class(paired["mean_delta_partial_all"])}">{format_delta(paired["mean_delta_partial_all"])}</td></tr>
    <tr><td>Mean partial · valid reps</td><td class="num">{base["mean_partial_valid"]:.3f}</td><td class="num">{thinkingcap["mean_partial_valid"]:.3f}</td><td>Different valid cohorts</td></tr>
    <tr><td>Mean partial · {paired["common_valid_pairs"]} common-valid pairs</td><td class="num">—</td><td class="num">—</td><td class="{delta_class(paired["mean_delta_partial_common_valid"])}">{format_delta(paired["mean_delta_partial_common_valid"])}</td></tr>
    <tr><td>F2P micro · common-valid</td><td class="num">{format_percent(paired["common_valid_base_f2p_micro"])}</td><td class="num">{format_percent(paired["common_valid_thinkingcap_f2p_micro"])}</td><td>ThinkingCap −{format_percent(paired["common_valid_base_f2p_micro"] - paired["common_valid_thinkingcap_f2p_micro"])}</td></tr>
    <tr><td>P2P micro · common-valid</td><td class="num">{format_percent(paired["common_valid_base_p2p_micro"], 2)}</td><td class="num">{format_percent(paired["common_valid_thinkingcap_p2p_micro"], 2)}</td><td>Both near 100%</td></tr>
    <tr><td>Total / output tokens</td><td class="num">{format_compact(base["total_tokens"])} / {format_compact(base["output_tokens"])}</td><td class="num">{format_compact(thinkingcap["total_tokens"])} / {format_compact(thinkingcap["output_tokens"])}</td><td class="up">−{format_percent(token_reduction)} total</td></tr>
    <tr><td>Median rep tokens</td><td class="num">{format_compact(base["median_total_tokens"])}</td><td class="num">{format_compact(thinkingcap["median_total_tokens"])}</td><td class="up">−{format_percent(1 - thinkingcap["median_total_tokens"] / base["median_total_tokens"])}</td></tr>
    <tr><td>Summed / median wall</td><td class="num">{format_duration(base["wall_sum_s"])} / {format_duration(base["wall_median_s"])}</td><td class="num">{format_duration(thinkingcap["wall_sum_s"])} / {format_duration(thinkingcap["wall_median_s"])}</td><td class="up">−{format_percent(wall_reduction)} summed wall</td></tr>
    <tr><td>Turns / tool calls</td><td class="num">{base["turns"]:,} / {base["tool_calls"]:,}</td><td class="num">{thinkingcap["turns"]:,} / {thinkingcap["tool_calls"]:,}</td><td>Shorter ThinkingCap trajectories</td></tr>
  </tbody></table></div>
  <div class="callout"><strong>Matched churn:</strong> {paired["wins_gt_005"]} ThinkingCap wins above +0.05, {paired["losses_lt_neg_005"]} losses below −0.05, and {paired["ties_within_005"]} ties within ±0.05. The seeded 100,000-sample task sign-flip permutation gives p={paired["task_sign_flip_monte_carlo_p"]:.3f}; the 20,000-sample task bootstrap interval is [{format_delta(ci_low)}, {format_delta(ci_high)}].</div>
</section>

<section>
  <div class="section-head"><div><h2>Task and language profile</h2><p>TypeScript was strongest; Go exposed the most repeatable invariant gaps; Python carried all four invalid reps.</p></div></div>
  <div class="grid-2">
    <div class="panel"><h3>Task mean partial delta vs contextual contrast</h3><div class="delta-list">{render_task_delta_bars(analysis["task_splits"])}</div></div>
    <div class="panel"><h3>Language split</h3><div class="table-wrap"><table><thead><tr><th>Language</th><th class="num">Reps</th><th class="num">Q+goal</th><th class="num">TC</th><th class="num">Δ</th><th class="num">Q invalid</th><th class="num">TC invalid</th><th class="num">Q med tok</th><th class="num">TC med tok</th></tr></thead><tbody>{render_language_rows(analysis["language_splits"])}</tbody></table></div></div>
  </div>
  <div class="table-wrap" style="margin-top:16px"><table><thead><tr><th>Task</th><th class="num">Q solves</th><th class="num">TC solves</th><th class="num">Q invalid</th><th class="num">TC invalid</th><th class="num">Q partial</th><th class="num">TC partial</th><th class="num">Δ</th><th class="num">Q med tok</th><th class="num">TC med tok</th></tr></thead><tbody>{render_task_rows(analysis["task_splits"])}</tbody></table></div>
  <div class="callout bad"><strong>Weakest recurring task families:</strong> Go worktree merge conflicts averaged 0.544 partial, GoReleaser retry auditing 0.586, Wazero snapshots 0.650, and recursive grammar analysis 0.680. The recurring mechanisms are incomplete conflict/retry state matrices, protocol drift, and missing cycle guards.</div>
</section>

<section>
  <div class="section-head"><div><h2>Complete 108-rep denominator</h2><p>All 216 local-model trajectories and all 108 matched task/rep addresses appear here before the filtered 15-packet cohort. Positive delta means higher ThinkingCap partial reward.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Q+goal outcome</th><th class="num">Q partial</th><th class="num">Q F2P</th><th>TC outcome</th><th class="num">TC partial</th><th class="num">TC F2P</th><th class="num">Δ partial</th><th class="num">Q tokens</th><th class="num">TC tokens</th><th class="num">Q wall</th><th class="num">TC wall</th></tr></thead><tbody>{render_all_cell_rows(analysis["paired_cells"])}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Execution substrate and tool behavior</h2><p>Delivery was clean enough to interpret model behavior; normal failing commands remain separate from parser or transport failures.</p></div></div>
  <div class="grid-3">
    <div class="panel"><h3>Thinking and requests</h3><p><strong>{delivery_tc["assistant_turns"]:,}</strong> assistant turns and <strong>{delivery_tc["thinking_blocks"]:,}</strong> thinking blocks.</p><p><strong>{delivery_tc["provider_request_count"]}</strong> captured requests; every request sent model, <code>max_tokens=98304</code>, thinking, preservation, and sampling pins.</p><p class="muted">One valid tool-call turn contained no thinking block; it was not malformed.</p></div>
    <div class="panel"><h3>No parser or limit collapse</h3><p>Malformed tool calls: <strong>{delivery_tc["malformed_tool_calls"]}</strong>.</p><p>Raw tool-call text leaks: <strong>{delivery_tc["raw_tool_call_text_leaks"]}</strong>.</p><p>Length-stop reps: <strong>{delivery_tc["cells_with_length_stop"]}</strong>.</p><p>Maximum completion: <strong>{delivery_tc["max_completion_tokens"]:,}</strong> tokens against 98,304.</p></div>
    <div class="panel"><h3>Exploration and validation</h3><p>Unique exact-file reads summed by rep: <strong>{delivery_tc["exact_file_reads_total_unique_by_cell"]}</strong>.</p><p>Pre-mutation reads: <strong>{delivery_tc["pre_mutation_reads_total_unique_by_cell"]}</strong>.</p><p>Detected validation commands: <strong>{delivery_tc["validation_commands"]:,}</strong>.</p></div>
  </div>
  <div class="grid-2" style="margin-top:16px">
    <div class="panel"><h3>Tool-result errors by tool</h3><p class="muted">ThinkingCap: {tc_tool_errors}/{tc_tool_results} ({format_percent(tc_tool_errors / tc_tool_results)}). Stock+goal context: {base_tool_errors}/{base_tool_results} ({format_percent(base_tool_errors / base_tool_results)}).</p><div class="table-wrap"><table><thead><tr><th>Tool</th><th class="num">Q errors/results</th><th class="num">Q rate</th><th class="num">TC errors/results</th><th class="num">TC rate</th></tr></thead><tbody>{render_tool_rows(delivery_base, delivery_tc)}</tbody></table></div></div>
    <div class="panel"><h3>Error causes</h3><div class="table-wrap"><table><thead><tr><th>Cause</th><th class="num">Stock+goal</th><th class="num">ThinkingCap</th></tr></thead><tbody>{render_error_cause_rows(delivery_base, delivery_tc)}</tbody></table></div><p class="muted">ThinkingCap’s 940 error results comprise 378 nonzero validation commands, 124 diagnostics, 258 other shell failures, 138 edit mismatches, 11 other edit errors, and 31 read failures—not tool-parser collapse.</p></div>
  </div>
</section>

<section>
  <div class="section-head"><div><h2>Invalid outcomes</h2><p>Seven matched pairs had an invalid side; ThinkingCap’s four invalid reps are primary here.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Stock+goal</th><th>ThinkingCap</th><th class="num">Δ partial</th></tr></thead><tbody>{render_invalid_rows(analysis["paired_cells"])}</tbody></table></div>
  <div class="grid-2" style="margin-top:16px">
    <div class="callout bad"><strong>Agent-budget exhaustion:</strong> HTTPX rep2 and LangChain rep0 hit 3,600 seconds before any detected validation. Their final messages still described implementation work, so these are clear execution-control failures.</div>
    <div class="callout bad"><strong>Implementation-linked teardown:</strong> LangChain rep1 exited normally but leaked executor threads and failed join/cancel semantics; the verifier waited 300 seconds. Mobly rep1 also timed out after agent exit, but lacks an independent signature and remains partly unresolved.</div>
  </div>
</section>

<section>
  <div class="section-head"><div><h2>Selected trajectory packets</h2><p>Fifteen rep-specific packets cover every ThinkingCap solve, every invalid rep, a valid agent timeout, patch and memory outliers, and representative low or unstable valid outcomes. They are examples from 15 reps, not task-wide claims.</p></div></div>
  <div class="grid-2">
    <div class="panel"><h3>Primary drivers</h3><div class="table-wrap"><table><thead><tr><th>Bucket</th><th class="num">Packets</th><th class="num">Share</th></tr></thead><tbody>{render_bucket_rows(packets)}</tbody></table></div></div>
    <div class="panel"><h3>Keep vs prevent</h3><p><span class="tag good">Keep</span> end-to-end owner-module mapping, cross-layer syntax integration, and full regression validation.</p><p><span class="tag bad">Prevent</span> offline dependency drift, helper-only integration, unguarded recursion, waiter leaks, self-authored-test overfitting, and unbounded validation loops.</p></div>
  </div>
  <div class="table-wrap" style="margin-top:16px"><table><thead><tr><th>Rep</th><th class="num">Δ partial</th><th>Trigger</th><th>Driver</th><th>Mechanism</th><th>Evidence</th></tr></thead><tbody>{render_packet_rows(packets)}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Concrete mechanisms</h2><p>Direct patch and verifier evidence behind the most useful success and failure patterns.</p></div></div>
  <div class="grid-2">
    <div class="callout good"><strong>SQL formatter rep1 · complete cross-layer integration.</strong> ThinkingCap connected lexer, grammar, AST, parser post-processing, formatter behavior, and tests; it passed 26/26 feature and 5,709/5,709 preservation tests.</div>
    <div class="callout good"><strong>True Myth rep0 · systematic owner-module coverage.</strong> The trajectory mapped combinators across Maybe, Result, Task, and toolbelt, mirrored them in tests, and passed all 96 feature plus 561 preservation checks.</div>
    <div class="callout bad"><strong>FD rep2 · avoidable offline dependency failure.</strong> The patch added <code>rand</code>; the clean verifier could not resolve crates.io, so all 152 tests were missing. Rep1 solved the same task without that failure.</div>
    <div class="callout bad"><strong>Wazero rep1 · self-consistent but wrong public protocol.</strong> The trajectory wrote 1,593 changed lines and 44 passing local tests, then passed 0/78 benchmark feature tests. Its parallel snapshot abstraction did not match real module/runtime contracts.</div>
    <div class="callout bad"><strong>Participle rep2 · missing recursion guard.</strong> Recursive grammar traversal exceeded a 1 GB goroutine stack and fatally overflowed. The 2.1 MB patch and 23 validations did not expose the core cycle invariant.</div>
    <div class="callout caution"><strong>Meriyah rep2 · quality near the threshold, resource use far outside it.</strong> Partial reached 0.9995, but eight preservation tests regressed and Vitest fan-out peaked at 39.33 GiB. This is a test-control and contextual-keyword preservation target.</div>
  </div>
</section>

<section>
  <div class="section-head"><div><h2>Scaffoldability ledger</h2><p>Each proposal names a mechanism, non-targets, risk, minimal same-model experiment, and a stop condition.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Observed weakness</th><th>Candidate support and mechanism</th><th>Minimal experiment</th><th>Success criterion</th><th>Non-targets and risk</th></tr></thead><tbody>{render_scaffold_rows(analysis["scaffoldability_ledger"])}</tbody></table></div>
  <div class="callout caution"><strong>Next config:</strong> reuse the released <code>pi-check@1.4.0</code> behavior unchanged. It already owns the exact re-audit prompt and ThinkingCap Bash-timeout hook; no new config-authored wording is needed. A later timeout-only or pi-check-only control is required for attribution.</div>
</section>

<section>
  <div class="section-head"><div><h2>What not to change</h2><p>Negative evidence rules out unsupported interventions.</p></div></div>
  <ul class="clean">{negative_items}</ul>
</section>

<section>
  <div class="section-head"><div><h2>Conclusion</h2><p>ThinkingCap’s 36_v2 capability profile and the next decision.</p></div></div>
  <div class="callout good"><strong>Reliable result:</strong> ThinkingCap preserved finished-rep average quality while reducing token traffic by {format_percent(token_reduction)} and summed agent time by {format_percent(wall_reduction)} in the contextual matched view.</div>
  <div class="callout bad"><strong>Reliable limit:</strong> strict completion stayed at 3/108. Repeated failures came from incomplete state matrices, interface drift, recursion/lifecycle guards, offline dependency assumptions, and completion claims unsupported by clean verification.</div>
  <div class="callout"><strong>Next move:</strong> run the proven pi-check + timeout config across the same 36_v2 addresses. Count strict solves, common-valid F2P, invalid churn, post-check mutations, timeout recovery, token overhead, and recurrence of the 15 packet mechanisms. If the combined treatment moves outcomes, isolate its two mechanisms next.</div>
  <details><summary>Artifact roots and reproducibility</summary><p class="artifact">Stock+goal results: {escape(analysis["comparison"]["base_result_root"])}<br>ThinkingCap results: {escape(analysis["comparison"]["thinkingcap_result_root"])}<br>Dataset: {escape(ANALYSIS_PATH)}<br>Packets: {escape(REPORT_DIR / "packets")}<br>Extractor: {escape(REPORT_DIR / "build_analysis.py")}<br>Builder: {escape(REPORT_DIR / "build_report.py")}</p></details>
</section>

<p class="foot">DeepSWE 36_v2 · 36 tasks · 3 reps · high thinking · local compute · completed 2026-08-04</p>
</div></body></html>"""


def main() -> None:
    """Write the deterministic self-contained ThinkingCap run report."""
    report_path = REPORT_DIR / "index.html"
    report_path.write_text(build_report())
    print(f"ThinkingCap 36_v2 report written to {report_path}")


if __name__ == "__main__":
    main()
