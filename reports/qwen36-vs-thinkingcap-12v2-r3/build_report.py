#!/usr/bin/env python3
"""Build the self-contained stock-Qwen versus ThinkingCap comparison report."""

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
    token_reduction = 1 - thinkingcap["total_tokens"] / base["total_tokens"]
    wall_reduction = 1 - thinkingcap["wall_sum_s"] / base["wall_sum_s"]
    turn_reduction = 1 - thinkingcap["turns"] / base["turns"]
    tool_reduction = 1 - thinkingcap["tool_calls"] / base["tool_calls"]
    ci_low, ci_high = paired["task_cluster_bootstrap_95_ci"]
    base_tool_errors = sum(delivery_base["tool_errors"].values())
    base_tool_results = sum(delivery_base["tool_results"].values())
    tc_tool_errors = sum(delivery_tc["tool_errors"].values())
    tc_tool_results = sum(delivery_tc["tool_results"].values())
    tc_patch_outlier = max(
        int(row["thinkingcap"]["patch_bytes"] or 0) for row in analysis["paired_cells"]
    )
    adjusted_tc_patch_bytes = thinkingcap["patch_bytes"] - tc_patch_outlier
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
<title>Qwen3.6 27B vs ThinkingCap · local capability-shape comparison</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23335dff%22/><text x=%2250%22 y=%2264%22 text-anchor=%22middle%22 font-size=%2238%22 fill=%22white%22>Q↔T</text></svg>" />
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#b77d00;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);--radius-xl:28px;--radius-lg:20px;--max:1440px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.91em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px;overflow-wrap:anywhere}}.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}.hero,section{{background:rgba(255,255,255,.91);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}.hero{{padding:clamp(24px,4vw,44px);overflow:hidden;position:relative}}.hero::after{{content:"";position:absolute;inset:auto -8% -45% auto;width:470px;height:470px;background:radial-gradient(circle,rgba(51,93,255,.15),transparent 70%);pointer-events:none}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2rem,4.7vw,4.25rem);margin-top:14px;max-width:16ch}}h2{{font-size:clamp(1.45rem,2.5vw,2.1rem)}}h3{{font-size:1.12rem;margin-bottom:8px}}.subtitle{{max-width:88ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.1rem);margin:15px 0 0}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}.pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line)}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:var(--blue-2)}}.stats{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:13px;margin-top:25px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:15px;min-height:118px;box-shadow:var(--shadow-sm)}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:9px}}.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.9rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;margin-top:8px;font-size:.84rem;color:var(--muted);font-weight:600}}section{{margin-top:20px;padding:clamp(18px,3vw,30px)}}.section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}}.section-head p{{margin:7px 0 0;color:var(--muted);max-width:90ch}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;min-width:0}}.grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;min-width:0}}.grid-2>*,.grid-3>*{{min-width:0}}.panel{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-sm);min-width:0}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:15px 17px;color:#22314d;margin-top:14px}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff9e8,#fff)}}.callout strong{{color:var(--blue-2)}}.tag{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:.73rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}}.up{{color:var(--green);font-weight:850}}.down{{color:var(--red);font-weight:850}}.flat{{color:var(--muted);font-weight:750}}.muted{{color:var(--muted);font-size:.86em}}.table-wrap{{overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:14px}}table{{width:100%;border-collapse:collapse;font-size:.88rem}}th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:800;background:var(--surface-2);position:sticky;top:0}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}tbody tr:hover{{background:var(--surface-2)}}tbody tr:last-child td{{border-bottom:0}}ul.clean{{margin:0;padding-left:20px}}ul.clean li{{margin:7px 0}}.delta-list{{display:grid;gap:10px}}.delta-row{{display:grid;grid-template-columns:minmax(250px,1.3fr) 2fr 60px;gap:10px;align-items:center}}.delta-label{{font-size:.84rem;font-weight:750;overflow-wrap:anywhere}}.delta-track{{height:16px;background:#edf2f7;border-radius:999px;position:relative;overflow:hidden;border:1px solid #dde5ef}}.delta-zero{{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#93a1b6;z-index:2}}.delta-bar{{position:absolute;top:0;bottom:0}}.delta-bar.positive{{left:50%;background:var(--green)}}.delta-bar.negative{{right:50%;background:var(--red)}}.delta-value{{text-align:right;font-variant-numeric:tabular-nums}}.artifact{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.79rem;color:var(--muted);overflow-wrap:anywhere}}details{{border:1px solid var(--line);border-radius:14px;background:var(--surface);padding:13px 15px;margin-top:12px}}summary{{cursor:pointer;font-weight:850;color:#263b66}}.foot{{margin-top:24px;color:var(--muted);font-size:.84rem;text-align:center}}@media(max-width:1100px){{.stats{{grid-template-columns:repeat(3,minmax(0,1fr))}}.grid-3{{grid-template-columns:1fr}}}}@media(max-width:850px){{.grid-2{{grid-template-columns:1fr}}}}@media(max-width:650px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.delta-row{{grid-template-columns:1fr 58px}}.delta-track{{grid-column:1/-1;grid-row:2}}.wrap{{padding:14px 8px 30px}}section,.hero{{border-radius:20px}}}}
</style>
</head>
<body><div class="wrap">
<header class="hero">
  <span class="eyebrow">Local capability contrast · 12_v2 · 72 trajectories · 36 matched pairs</span>
  <h1>The fine-tune changes execution more than correctness.</h1>
  <p class="subtitle">ThinkingCap Qwen3.6 27B uses materially fewer tokens and less agent wall time than its stock Qwen3.6-27B base contrast. It does not show a broad task-quality lift on this subset: the mean partial gain is small, common-valid feature coverage falls, and one strict solve sits beside substantial Go regressions and timeout churn.</p>
  <div class="pillrow"><span class="pill good">1 solve vs 0</span><span class="pill good">{format_percent(token_reduction)} fewer tokens</span><span class="pill good">{format_percent(wall_reduction)} less agent wall</span><span class="pill neutral">27 / 36 paired ties</span><span class="pill good">0 malformed tool calls</span><span class="pill caution">causal attribution limited</span></div>
  <div class="stats">
    <div class="stat"><span class="label">Strict solves</span><span class="value">1 vs 0</span><span class="sub">ThinkingCap vs stock Qwen</span></div>
    <div class="stat"><span class="label">All-cell Δ partial</span><span class="value">{format_delta(paired["mean_delta_partial_all"])}</span><span class="sub">95% task CI {format_delta(ci_low)} to {format_delta(ci_high)}</span></div>
    <div class="stat"><span class="label">Common-valid Δ</span><span class="value">{format_delta(paired["mean_delta_partial_common_valid"])}</span><span class="sub">31 pairs valid on both sides</span></div>
    <div class="stat"><span class="label">Common-valid F2P</span><span class="value">{format_percent(paired["common_valid_thinkingcap_f2p_micro"])}</span><span class="sub">stock Qwen {format_percent(paired["common_valid_base_f2p_micro"])}</span></div>
    <div class="stat"><span class="label">Total tokens</span><span class="value">{format_compact(thinkingcap["total_tokens"])}</span><span class="sub">stock Qwen {format_compact(base["total_tokens"])}</span></div>
    <div class="stat"><span class="label">Agent wall sum</span><span class="value">{format_duration(thinkingcap["wall_sum_s"])}</span><span class="sub">stock Qwen {format_duration(base["wall_sum_s"])}</span></div>
  </div>
</header>

<section>
  <div class="section-head"><div><h2>Executive reading</h2><p>What the matched trajectories support—and what they do not.</p></div></div>
  <div class="grid-2">
    <div class="callout good"><strong>ThinkingCap converges faster.</strong> It used {format_percent(token_reduction)} fewer total tokens, {format_percent(wall_reduction)} less summed agent time, {format_percent(turn_reduction)} fewer turns, and {format_percent(tool_reduction)} fewer tool calls. It completed <code>langchain rep2</code> and <code>mobly rep0</code> where stock Qwen exhausted 5,400 seconds.</div>
    <div class="callout caution"><strong>The quality lift is not broad.</strong> Mean partial moved from {base["mean_partial_all"]:.3f} to {thinkingcap["mean_partial_all"]:.3f}, but the task-cluster interval spans zero and common-valid partial moved {format_delta(paired["mean_delta_partial_common_valid"])}. On the 31 common-valid pairs, F2P fell from {format_percent(paired["common_valid_base_f2p_micro"])} to {format_percent(paired["common_valid_thinkingcap_f2p_micro"])}.</div>
    <div class="callout good"><strong>Better seam choices created real wins.</strong> ThinkingCap solved <code>sql-formatter rep1</code> by adding parser post-processing for nested <code>GROUP BY</code> and pipe <code>AS</code>. It avoided stock Qwen's shared-walker regression in <code>go-critic rep1</code> and integrated SuperJSON at the authoritative Error transformer seam.</div>
    <div class="callout bad"><strong>Recursive state remains the clearest weakness.</strong> ThinkingCap stack-overflowed on recursive grammar analysis, overflowed on circular Error causes, and failed to release coalescing waiters. Those are concrete cycle, depth, identity, and lifecycle invariants—not serving failures.</div>
  </div>
  <div class="callout caution"><strong>Completion audit opportunity:</strong> in the predeclared 11-packet cohort, ThinkingCap made {completion_claims} completion claims; {completion_claims_not_solved} still ended unsolved or invalid. The in-progress <code>pi-check@1.4.0</code> plus Bash-timeout run is a useful same-model combined treatment, but it cannot isolate the audit from the timeout hook.</div>
</section>

<section>
  <div class="section-head"><div><h2>Comparison lock and causal limits</h2><p>ThinkingCap is the local subject; stock Qwen3.6-27B is the local contrast. There is no frontier reference. The intended weight change is mixed with deployment and provenance differences.</p></div></div>
  <div class="grid-2">
    <div class="panel"><h3>Shared execution surface</h3><ul class="clean">{shared_items}</ul></div>
    <div class="panel"><h3>Delivery classification</h3><p><span class="tag caution">stock ambiguous</span> {escape(analysis["delivery_classification"]["base_qwen_reason"])}</p><p><span class="tag good">ThinkingCap delivered</span> {escape(analysis["delivery_classification"]["thinkingcap_reason"])}</p><p class="muted">All {paired["common_valid_pairs"]} common-valid pairs use identical F2P/P2P denominators. That supports grading comparability where both sides finished, but it does not recover the stock run's missing immutable task revision.</p></div>
  </div>
  <div class="table-wrap" style="margin-top:16px"><table><thead><tr><th>Surface</th><th>Stock Qwen</th><th>ThinkingCap</th><th>Role</th></tr></thead><tbody>{render_substrate_rows(analysis["substrate_comparability"])}</tbody></table></div>
  <div class="callout caution"><strong>Interpretation rule:</strong> efficiency and observed outcome differences are real for these artifacts. Fine-tune causality is suggestive, not isolated, because runtime, timeout, output-request, Pi provenance, and checkpoint packaging also changed.</div>
</section>

<section>
  <div class="section-head"><div><h2>Aggregate capability shape</h2><p>Strict outcomes, valid-only grading, and resource use tell different parts of the story.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Stock Qwen</th><th class="num">ThinkingCap</th><th>Reading</th></tr></thead><tbody>
    <tr><td>Strict solves</td><td class="num">{base["solves"]} / 36</td><td class="num">{thinkingcap["solves"]} / 36</td><td>One ThinkingCap-only solve</td></tr>
    <tr><td>Valid / invalid</td><td class="num">{base["valid"]} / {base["invalid"]}</td><td class="num">{thinkingcap["valid"]} / {thinkingcap["invalid"]}</td><td>Three one-sided invalid flips; two shared invalid pairs</td></tr>
    <tr><td>Mean partial · all cells</td><td class="num">{base["mean_partial_all"]:.3f}</td><td class="num">{thinkingcap["mean_partial_all"]:.3f}</td><td class="{delta_class(paired["mean_delta_partial_all"])}">{format_delta(paired["mean_delta_partial_all"])}</td></tr>
    <tr><td>Mean partial · valid cells</td><td class="num">{base["mean_partial_valid"]:.3f}</td><td class="num">{thinkingcap["mean_partial_valid"]:.3f}</td><td>Different valid cohorts; use common-valid row below</td></tr>
    <tr><td>Mean partial · 31 common-valid pairs</td><td class="num">—</td><td class="num">—</td><td class="{delta_class(paired["mean_delta_partial_common_valid"])}">{format_delta(paired["mean_delta_partial_common_valid"])}</td></tr>
    <tr><td>F2P micro · 31 common-valid pairs</td><td class="num">{format_percent(paired["common_valid_base_f2p_micro"])}</td><td class="num">{format_percent(paired["common_valid_thinkingcap_f2p_micro"])}</td><td class="down">{format_delta(paired["common_valid_thinkingcap_f2p_micro"] - paired["common_valid_base_f2p_micro"], 3)}</td></tr>
    <tr><td>P2P micro · 31 common-valid pairs</td><td class="num">{format_percent(paired["common_valid_base_p2p_micro"], 2)}</td><td class="num">{format_percent(paired["common_valid_thinkingcap_p2p_micro"], 2)}</td><td>Both preserve existing behavior almost perfectly</td></tr>
    <tr><td>Total / output tokens</td><td class="num">{format_compact(base["total_tokens"])} / {format_compact(base["output_tokens"])}</td><td class="num">{format_compact(thinkingcap["total_tokens"])} / {format_compact(thinkingcap["output_tokens"])}</td><td class="up">−{format_percent(token_reduction)} total</td></tr>
    <tr><td>Median cell tokens</td><td class="num">{format_compact(base["median_total_tokens"])}</td><td class="num">{format_compact(thinkingcap["median_total_tokens"])}</td><td class="up">lower for ThinkingCap</td></tr>
    <tr><td>Summed / median agent wall</td><td class="num">{format_duration(base["wall_sum_s"])} / {format_duration(base["wall_median_s"])}</td><td class="num">{format_duration(thinkingcap["wall_sum_s"])} / {format_duration(thinkingcap["wall_median_s"])}</td><td class="up">−{format_percent(wall_reduction)} summed wall</td></tr>
    <tr><td>Turns / tool calls</td><td class="num">{base["turns"]:,} / {base["tool_calls"]:,}</td><td class="num">{thinkingcap["turns"]:,} / {thinkingcap["tool_calls"]:,}</td><td>Shorter ThinkingCap trajectories</td></tr>
    <tr><td>Median patch bytes</td><td class="num">{format_compact(base["median_patch_bytes"])}</td><td class="num">{format_compact(thinkingcap["median_patch_bytes"])}</td><td>ThinkingCap total is distorted by one {format_compact(tc_patch_outlier)} binary patch</td></tr>
  </tbody></table></div>
  <div class="callout"><strong>Churn:</strong> {paired["wins_gt_005"]} ThinkingCap wins above +0.05, {paired["losses_lt_neg_005"]} losses below −0.05, and {paired["ties_within_005"]} ties within ±0.05. Exact task-level sign-flip p={paired["task_sign_flip_exact_p"]:.3f}; deterministic 20,000-sample task bootstrap CI [{format_delta(ci_low)}, {format_delta(ci_high)}]. These are directional summaries over 12 tasks, not population guarantees.</div>
</section>

<section>
  <div class="section-head"><div><h2>Task and language profile</h2><p>Python's apparent gain is timeout-sensitive. Go contains the clearest fine-tune regressions. TypeScript contains the only strict solve and the most consistent efficiency improvement.</p></div></div>
  <div class="grid-2">
    <div class="panel"><h3>Task mean partial delta</h3><div class="delta-list">{render_task_delta_bars(analysis["task_splits"])}</div></div>
    <div class="panel"><h3>Language split</h3><div class="table-wrap"><table><thead><tr><th>Language</th><th class="num">Cells</th><th class="num">Qwen</th><th class="num">TC</th><th class="num">Δ</th><th class="num">Q invalid</th><th class="num">TC invalid</th><th class="num">Q med tok</th><th class="num">TC med tok</th></tr></thead><tbody>{render_language_rows(analysis["language_splits"])}</tbody></table></div></div>
  </div>
  <div class="table-wrap" style="margin-top:16px"><table><thead><tr><th>Task</th><th class="num">Q solves</th><th class="num">TC solves</th><th class="num">Q invalid</th><th class="num">TC invalid</th><th class="num">Q partial</th><th class="num">TC partial</th><th class="num">Δ</th><th class="num">Q med tok</th><th class="num">TC med tok</th></tr></thead><tbody>{render_task_rows(analysis["task_splits"])}</tbody></table></div>
  <div class="callout caution"><strong>Do not read the +0.078 Python delta as broad Python capability.</strong> It is dominated by <code>mobly rep0</code> and <code>langchain rep2</code> changing from stock-Qwen timeouts to valid ThinkingCap patches, offset by <code>langchain rep1</code> moving the other way.</div>
</section>

<section>
  <div class="section-head"><div><h2>Complete paired denominator</h2><p>All 72 trajectories and all 36 matched pairs appear here before the filtered 11-packet cohort. Positive delta means higher ThinkingCap partial reward.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Q outcome</th><th class="num">Q partial</th><th class="num">Q F2P</th><th>TC outcome</th><th class="num">TC partial</th><th class="num">TC F2P</th><th class="num">Δ partial</th><th class="num">Q tokens</th><th class="num">TC tokens</th><th class="num">Q wall</th><th class="num">TC wall</th></tr></thead><tbody>{render_all_cell_rows(analysis["paired_cells"])}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Execution substrate and tool behavior</h2><p>Both models used reasoning and tools reliably. Error results are mostly useful test and diagnostic feedback, not parser failure.</p></div></div>
  <div class="grid-3">
    <div class="panel"><h3>Reasoning and requests</h3><p><strong>Stock Qwen:</strong> {delivery_base["assistant_turns"]:,} assistant turns, {delivery_base["thinking_blocks"]:,} thinking blocks, {delivery_base["provider_request_count"]} captured requests.</p><p><strong>ThinkingCap:</strong> {delivery_tc["assistant_turns"]:,} assistant turns, {delivery_tc["thinking_blocks"]:,} thinking blocks, {delivery_tc["provider_request_count"]} captured requests.</p><p class="muted">Every thinking block on both sides used signature <code>reasoning</code>.</p></div>
    <div class="panel"><h3>Limits did not bind</h3><p>Length-stop cells: <strong>{delivery_base["cells_with_length_stop"]} vs {delivery_tc["cells_with_length_stop"]}</strong>.</p><p>Maximum completion: <strong>{delivery_base["max_completion_tokens"]:,} vs {delivery_tc["max_completion_tokens"]:,}</strong> tokens.</p><p>Maximum prompt: <strong>{delivery_base["max_prompt_tokens"]:,} vs {delivery_tc["max_prompt_tokens"]:,}</strong>.</p></div>
    <div class="panel"><h3>Exploration and validation</h3><p>Unique exact-file reads summed by cell: <strong>{delivery_base["exact_file_reads_total_unique_by_cell"]} vs {delivery_tc["exact_file_reads_total_unique_by_cell"]}</strong>.</p><p>Pre-mutation reads: <strong>{delivery_base["pre_mutation_reads_total_unique_by_cell"]} vs {delivery_tc["pre_mutation_reads_total_unique_by_cell"]}</strong>.</p><p>Detected validation commands: <strong>{delivery_base["validation_commands"]} vs {delivery_tc["validation_commands"]}</strong>.</p></div>
  </div>
  <div class="grid-2" style="margin-top:16px">
    <div class="panel"><h3>Tool-result errors by tool</h3><p class="muted">Stock: {base_tool_errors}/{base_tool_results} ({format_percent(base_tool_errors / base_tool_results)}). ThinkingCap: {tc_tool_errors}/{tc_tool_results} ({format_percent(tc_tool_errors / tc_tool_results)}).</p><div class="table-wrap"><table><thead><tr><th>Tool</th><th class="num">Q errors/results</th><th class="num">Q rate</th><th class="num">TC errors/results</th><th class="num">TC rate</th></tr></thead><tbody>{render_tool_rows(delivery_base, delivery_tc)}</tbody></table></div></div>
    <div class="panel"><h3>Error causes</h3><div class="table-wrap"><table><thead><tr><th>Cause</th><th class="num">Stock Qwen</th><th class="num">ThinkingCap</th></tr></thead><tbody>{render_error_cause_rows(delivery_base, delivery_tc)}</tbody></table></div><p class="muted">Both sides recorded 159 nonzero validation commands. ThinkingCap reduced edit mismatches from 53 to 46. Neither side emitted malformed tool calls or assistant-record parse errors.</p></div>
  </div>
  <div class="callout good"><strong>Serving conclusion:</strong> the tool and reasoning substrate is healthy enough to interpret the trajectories. The stock request's absent <code>max_tokens</code> is a provenance ambiguity, but zero length stops and ~11.6K maximum completions argue that it did not drive the observed cells.</div>
</section>

<section>
  <div class="section-head"><div><h2>Invalid-outcome churn</h2><p>Five pairs had at least one invalid side. Two were invalid on both sides; three flipped validity.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Stock Qwen</th><th>ThinkingCap</th><th class="num">Δ partial</th></tr></thead><tbody>{render_invalid_rows(analysis["paired_cells"])}</tbody></table></div>
  <div class="grid-2" style="margin-top:16px">
    <div class="callout good"><strong>ThinkingCap recoveries:</strong> <code>langchain rep2</code> reached 0.975 partial and <code>mobly rep0</code> reached 0.961 after stock Qwen exhausted 5,400 seconds. These are execution-control wins, though neither patch solved its task.</div>
    <div class="callout bad"><strong>ThinkingCap regression:</strong> <code>langchain rep1</code> changed from 0.986 partial to invalid. The verifier found result/cancellation failures and waited 300 seconds for leaked executor threads. That timeout is implementation-linked, not an independent infrastructure outage.</div>
  </div>
</section>

<section>
  <div class="section-head"><div><h2>Selected trajectory packets</h2><p>Predeclared triggers: every solve flip, one-sided invalid, |Δpartial| ≥ 0.20, |ΔF2P| ≥ 0.25, |ΔP2P| ≥ 0.05, or patch &gt; 200 KB. Eleven rep-specific packets qualified; they are examples from 11 cells, not task-wide claims.</p></div></div>
  <div class="grid-2">
    <div class="panel"><h3>Primary drivers in packet cohort</h3><div class="table-wrap"><table><thead><tr><th>Bucket</th><th class="num">Packets</th><th class="num">Share</th></tr></thead><tbody>{render_bucket_rows(packets)}</tbody></table></div></div>
    <div class="panel"><h3>Keep vs prevent</h3><p><span class="tag good">Keep</span> narrow extension seams, parser post-processing where required, and early end-to-end slices.</p><p><span class="tag bad">Prevent</span> unguarded recursion, waiter leaks, helper-only integration, and completion claims without full-surface evidence.</p><p><span class="tag caution">Mixed</span> faster completion can rescue validity while still leaving large feature gaps.</p></div>
  </div>
  <div class="table-wrap" style="margin-top:16px"><table><thead><tr><th>Cell</th><th class="num">Δ partial</th><th>Trigger</th><th>Driver</th><th>Mechanism</th><th>Evidence</th></tr></thead><tbody>{render_packet_rows(packets)}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Five concrete mechanisms</h2><p>Direct patch/verifier evidence behind the most useful wins and losses.</p></div></div>
  <div class="grid-2">
    <div class="callout good"><strong>SQL formatter rep1 · better parser seam.</strong> ThinkingCap added <code>createParser.ts</code> post-processing for nested <code>GROUP BY</code> and pipe <code>AS</code>, passed 26/26 feature tests and 5,709/5,709 preservation tests, and finished 34% faster. Stock Qwen left five formatter/parser edge cases.</div>
    <div class="callout good"><strong>SuperJSON rep2 · better integration, incomplete recursion.</strong> ThinkingCap moved F2P from 25.0% to 82.5% by wiring mode-specific Error behavior into the transformer. It still stack-overflowed on circular causes and rehydrated causes as plain objects, dropping four preservation tests.</div>
    <div class="callout bad"><strong>GoReleaser rep2 · helper never reached the real call.</strong> ThinkingCap implemented <code>executeHTTPRequestWithResponse</code> but left <code>doSingleUpload</code> calling the old helper. Retryable responses lost their status context; 27/29 feature tests failed and attempt records stayed empty.</div>
    <div class="callout bad"><strong>Participle rep0 · one missing cycle guard masked 77 tests.</strong> Recursive grammar traversal repeated through <code>analyze_engine.go:168–206</code> until Go exceeded a 1 GB goroutine stack. Stock Qwen passed 88/91 feature tests on the same cell.</div>
    <div class="callout bad"><strong>LangChain rep1 · lifecycle bug became verifier timeout.</strong> Join returned <code>None</code>, clear did not cancel waiters, and pytest spent 300.10 seconds waiting for executor threads. The invalid result belongs to the patch's concurrency semantics, not generic verifier instability.</div>
    <div class="callout caution"><strong>Patch-size total needs correction.</strong> ThinkingCap's raw patch total is {format_compact(thinkingcap["patch_bytes"])}, but {format_compact(tc_patch_outlier)} comes from a generated <code>verify</code> binary in Participle rep2. Excluding it gives {format_compact(adjusted_tc_patch_bytes)} versus stock Qwen's {format_compact(base["patch_bytes"])}; median ThinkingCap patch size is smaller.</div>
  </div>
</section>

<section>
  <div class="section-head"><div><h2>Scaffoldability ledger</h2><p>Each proposal names a mechanism, non-targets, risk, minimal same-model experiment, and a stop condition. These are hypotheses, not proven treatment effects.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Observed weakness</th><th>Candidate support and mechanism</th><th>Minimal experiment</th><th>Success criterion</th><th>Non-targets and risk</th></tr></thead><tbody>{render_scaffold_rows(analysis["scaffoldability_ledger"])}</tbody></table></div>
  <div class="callout caution"><strong>Prompt-integrity constraint:</strong> any new config-authored audit wording requires approval of the exact text before implementation. The existing pi-check plus timeout treatment can be analyzed as-is when its current run completes; attribution requires a later single-mechanism control.</div>
</section>

<section>
  <div class="section-head"><div><h2>What not to change</h2><p>Negative evidence rules out several tempting but unsupported interventions.</p></div></div>
  <ul class="clean">{negative_items}</ul>
</section>

<section>
  <div class="section-head"><div><h2>Conclusion</h2><p>Capability shape, not a winner declaration.</p></div></div>
  <div class="callout good"><strong>Reliable gain:</strong> ThinkingCap reaches usable patches with substantially less local compute time and token traffic. It also shows isolated better seam selection in SQL formatting, checker traversal, and Error serialization.</div>
  <div class="callout bad"><strong>Reliable limit:</strong> the fine-tune does not consistently improve feature completeness. It is weaker on the two Go tasks with the largest model-quality movement, and recursive/lifecycle invariants recur across languages.</div>
  <div class="callout"><strong>Next decision:</strong> let the matched pi-check plus timeout run finish, then test whether the combined treatment improves strict solves or common-valid F2P without erasing ThinkingCap's efficiency advantage. If it moves the result, isolate pi-check from the timeout hook; if it does not move the recursion/lifecycle packets, target those invariants directly.</div>
  <details><summary>Artifact roots and reproducibility</summary><p class="artifact">Stock results: {escape(analysis["comparison"]["base_result_root"])}<br>ThinkingCap results: {escape(analysis["comparison"]["thinkingcap_result_root"])}<br>Dataset: {escape(ANALYSIS_PATH)}<br>Packets: {escape(REPORT_DIR / "packets")}<br>Extractor: {escape(REPORT_DIR / "extract_comparison.py")}</p></details>
</section>

<p class="foot">DeepSWE 12_v2 · 12 tasks · 3 reps · high thinking · local compute · observed artifacts through 2026-08-03</p>
</div></body></html>"""


def main() -> None:
    """Write the deterministic self-contained comparison report."""
    report_path = REPORT_DIR / "index.html"
    report_path.write_text(build_report())
    print(f"Qwen comparison report written to {report_path}")


if __name__ == "__main__":
    main()
