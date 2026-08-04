#!/usr/bin/env python3
"""Render the ThinkingCap pi-check and AgentWorld comparison report."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

REPORT_ROOT = Path(__file__).resolve().parent
ANALYSIS_PATH = REPORT_ROOT / "analysis.json"
OUTPUT_PATH = REPORT_ROOT / "index.html"

CONFIG_ORDER = [
    "thinkingcap_baseline",
    "thinkingcap_pi_check",
    "agentworld_baseline",
    "agentworld_pi_check",
]


def escape(value: Any) -> str:
    """Escape one value for safe HTML output."""
    return html.escape(str(value), quote=True)


def format_percent(value: float, digits: int = 1) -> str:
    """Format a zero-to-one ratio as a percentage."""
    return f"{value * 100:.{digits}f}%"


def format_delta(value: float, digits: int = 3) -> str:
    """Format a signed decimal change."""
    return f"{value:+.{digits}f}"


def format_compact(value: float) -> str:
    """Format large counts in compact human-readable units."""
    absolute = abs(float(value))
    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def format_duration(seconds: float) -> str:
    """Format seconds as hours or minutes."""
    if seconds >= 3_600:
        return f"{seconds / 3_600:.1f}h"
    if seconds >= 60:
        return f"{seconds / 60:.1f}m"
    return f"{seconds:.1f}s"


def status_tag(status: str) -> str:
    """Render one benchmark status as a colored tag."""
    class_name = {
        "solved": "good",
        "graded": "neutral",
        "agent timeout": "bad",
        "verifier timeout": "bad",
        "invalid": "bad",
    }.get(status, "neutral")
    return f"<span class='tag {class_name}'>{escape(status)}</span>"


def delta_class(value: float, threshold: float = 0.001) -> str:
    """Choose a CSS class for a signed metric change."""
    if value > threshold:
        return "up"
    if value < -threshold:
        return "down"
    return "flat"


def render_aggregate_table(analysis: dict[str, Any]) -> str:
    """Render the four-config aggregate comparison table."""
    rows: list[str] = []
    for config_name in CONFIG_ORDER:
        config = analysis["configs"][config_name]
        aggregate = config["aggregate"]
        rows.append(
            "<tr>"
            f"<td><strong>{escape(config['label'])}</strong><br><span class='muted'>{escape(config['config'])}</span></td>"
            f"<td class='num'>{aggregate['solves']}/36</td>"
            f"<td class='num'>{aggregate['valid']}/36</td>"
            f"<td class='num'>{aggregate['mean_partial_all']:.3f}</td>"
            f"<td class='num'>{format_percent(aggregate['f2p_micro'])}</td>"
            f"<td class='num'>{format_percent(aggregate['p2p_micro'], 2)}</td>"
            f"<td class='num'>{format_compact(aggregate['total_tokens'])}</td>"
            f"<td class='num'>{format_duration(aggregate['wall_sum_s'])}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_within_model_table(analysis: dict[str, Any]) -> str:
    """Render the paired treatment change for ThinkingCap and AgentWorld."""
    rows: list[str] = []
    for label, pair_name, base_name, check_name in [
        (
            "ThinkingCap",
            "thinkingcap_treatment",
            "thinkingcap_baseline",
            "thinkingcap_pi_check",
        ),
        (
            "AgentWorld",
            "agentworld_treatment",
            "agentworld_baseline",
            "agentworld_pi_check",
        ),
    ]:
        pair = analysis["pairs"][pair_name]
        base = analysis["configs"][base_name]["aggregate"]
        check = analysis["configs"][check_name]["aggregate"]
        rows.append(
            "<tr>"
            f"<td><strong>{label}</strong></td>"
            f"<td class='num'>{base['invalid']} → {check['invalid']}</td>"
            f"<td class='num'>{base['solves']} → {check['solves']}</td>"
            f"<td class='num {delta_class(pair['mean_partial_delta_all'])}'>{format_delta(pair['mean_partial_delta_all'])}</td>"
            f"<td class='num {delta_class(pair['common_valid_mean_partial_delta'])}'>{format_delta(pair['common_valid_mean_partial_delta'])}</td>"
            f"<td class='num'>{pair['wins_over_0_05']} / {pair['losses_below_minus_0_05']} / {pair['ties_within_0_05']}</td>"
            f"<td class='num'>{(pair['token_ratio'] - 1) * 100:+.1f}%</td>"
            f"<td class='num'>{(pair['wall_ratio'] - 1) * 100:+.1f}%</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_common_grade_table(analysis: dict[str, Any]) -> str:
    """Render feature and preservation scores on attempts graded in both configs."""
    rows: list[str] = []
    for label, pair_name in [
        ("ThinkingCap", "thinkingcap_treatment"),
        ("AgentWorld", "agentworld_treatment"),
    ]:
        pair = analysis["pairs"][pair_name]
        rows.append(
            "<tr>"
            f"<td><strong>{label}</strong></td>"
            f"<td class='num'>{pair['common_valid_pairs']}</td>"
            f"<td class='num'>{format_percent(pair['left_common_f2p_micro'])}</td>"
            f"<td class='num'>{format_percent(pair['right_common_f2p_micro'])}</td>"
            f"<td class='num'>{format_percent(pair['left_common_p2p_micro'], 2)}</td>"
            f"<td class='num'>{format_percent(pair['right_common_p2p_micro'], 2)}</td>"
            f"<td class='num'>{pair['left_common_mean_partial']:.3f}</td>"
            f"<td class='num'>{pair['right_common_mean_partial']:.3f}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_delivery_rows(analysis: dict[str, Any]) -> str:
    """Render treatment delivery and post-check work for both local models."""
    rows: list[str] = []
    for config_name in ["thinkingcap_pi_check", "agentworld_pi_check"]:
        config = analysis["configs"][config_name]
        delivery = config["delivery"]
        aggregate = config["aggregate"]
        rows.append(
            "<tr>"
            f"<td><strong>{escape(config['label'])}</strong></td>"
            f"<td class='num'>{delivery['delivered_cells']}/36</td>"
            f"<td class='num'>{delivery['cells_with_post_check_mutation']}/36</td>"
            f"<td class='num'>{delivery['post_check_mutation_calls']}</td>"
            f"<td class='num'>{format_compact(delivery['post_check_tokens'])}</td>"
            f"<td class='num'>{format_percent(delivery['post_check_token_share'])}</td>"
            f"<td class='num'>{delivery['total_tool_errors']}/{aggregate['tool_calls']}</td>"
            f"<td class='num'>{delivery['malformed_tool_calls']}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_tool_error_rows(analysis: dict[str, Any]) -> str:
    """Render tool-result errors by cause for both pi-check configs."""
    causes = sorted(
        {
            cause
            for name in ["thinkingcap_pi_check", "agentworld_pi_check"]
            for cause in analysis["configs"][name]["delivery"]["tool_error_causes"]
        }
    )
    rows: list[str] = []
    for cause in causes:
        thinkingcap = analysis["configs"]["thinkingcap_pi_check"]["delivery"][
            "tool_error_causes"
        ].get(cause, 0)
        agentworld = analysis["configs"]["agentworld_pi_check"]["delivery"][
            "tool_error_causes"
        ].get(cause, 0)
        rows.append(
            "<tr>"
            f"<td>{escape(cause)}</td>"
            f"<td class='num'>{thinkingcap}</td>"
            f"<td class='num'>{agentworld}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_task_rows(analysis: dict[str, Any]) -> str:
    """Render task-level partial scores and within-model treatment changes."""
    rows: list[str] = []
    for row in analysis["task_rows"]:
        tc_base = row["thinkingcap_baseline"]["mean_partial"]
        tc_check = row["thinkingcap_pi_check"]["mean_partial"]
        aw_base = row["agentworld_baseline"]["mean_partial"]
        aw_check = row["agentworld_pi_check"]["mean_partial"]
        tc_delta = tc_check - tc_base
        aw_delta = aw_check - aw_base
        rows.append(
            "<tr>"
            f"<td class='task'><strong>{escape(row['task'])}</strong><br><span class='muted'>{escape(row['language'])}</span></td>"
            f"<td class='num'>{tc_base:.3f}</td>"
            f"<td class='num'>{tc_check:.3f}</td>"
            f"<td class='num {delta_class(tc_delta)}'>{format_delta(tc_delta)}</td>"
            f"<td class='num'>{row['thinkingcap_baseline']['invalid']} → {row['thinkingcap_pi_check']['invalid']}</td>"
            f"<td class='num'>{aw_base:.3f}</td>"
            f"<td class='num'>{aw_check:.3f}</td>"
            f"<td class='num {delta_class(aw_delta)}'>{format_delta(aw_delta)}</td>"
            f"<td class='num'>{row['agentworld_baseline']['invalid']} → {row['agentworld_pi_check']['invalid']}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_language_rows(analysis: dict[str, Any]) -> str:
    """Render language-level partial scores for all four configs."""
    rows: list[str] = []
    for row in analysis["language_rows"]:
        rows.append(
            "<tr>"
            f"<td><strong>{escape(row['language'])}</strong></td>"
            f"<td class='num'>{row['thinkingcap_baseline']['mean_partial']:.3f}</td>"
            f"<td class='num'>{row['thinkingcap_pi_check']['mean_partial']:.3f}</td>"
            f"<td class='num'>{row['agentworld_baseline']['mean_partial']:.3f}</td>"
            f"<td class='num'>{row['agentworld_pi_check']['mean_partial']:.3f}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_packet_cards(analysis: dict[str, Any]) -> str:
    """Render the selected ThinkingCap trajectory packets."""
    cards: list[str] = []
    for packet in analysis["packets"]:
        classification = packet["classification"]
        baseline = packet["baseline"]
        treatment = packet["treatment"]
        cards.append(
            "<article class='packet-card'>"
            f"<span class='tag {('good' if packet['partial_delta'] > 0.05 else 'bad' if packet['partial_delta'] < -0.05 else 'caution')}'>{escape(classification['effect'])}</span>"
            f"<h3>{escape(packet['title'])} · rep {packet['rep']}</h3>"
            f"<p class='mono'>{escape(packet['task'])}</p>"
            f"<p><strong>Baseline:</strong> {status_tag(baseline['status'])} {baseline['metrics']['reward_partial']:.3f} partial · "
            f"<strong>combined:</strong> {status_tag(treatment['status'])} {treatment['metrics']['reward_partial']:.3f} partial.</p>"
            f"<p>{escape(classification['mechanism'])}</p>"
            f"<p class='muted'><strong>Lesson:</strong> {escape(classification['lesson'])}</p>"
            f"<p><a href='packets/{escape(packet['packet_key'])}.md'>Readable packet</a> · "
            f"<a href='packets/{escape(packet['packet_key'])}.json'>JSON evidence</a></p>"
            "</article>"
        )
    return "\n".join(cards)


def render_full_cell_rows(analysis: dict[str, Any]) -> str:
    """Render all 36 matched attempts across the four configs."""
    rows: list[str] = []
    for row in analysis["full_cell_rows"]:
        cells = row["configs"]

        def result_cell(config_name: str, row_cells: dict[str, Any] = cells) -> str:
            value = row_cells[config_name]
            f2p = "—" if value["f2p"] is None else format_percent(value["f2p"], 0)
            return (
                f"{status_tag(value['status'])}<br>"
                f"<span class='score'>{value['reward_partial']:.3f}</span> · "
                f"<span class='muted'>F {f2p}</span>"
            )

        packet_link = (
            f"<a href='packets/{escape(row['packet_key'])}.md'>packet</a>"
            if row["packet_key"]
            else "—"
        )
        rows.append(
            "<tr>"
            f"<td class='task'>{escape(row['task'])}</td>"
            f"<td class='num'>{row['rep']}</td>"
            f"<td>{result_cell('thinkingcap_baseline')}</td>"
            f"<td>{result_cell('thinkingcap_pi_check')}</td>"
            f"<td>{result_cell('agentworld_baseline')}</td>"
            f"<td>{result_cell('agentworld_pi_check')}</td>"
            f"<td>{packet_link}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_config_rows(analysis: dict[str, Any]) -> str:
    """Render the config and serving differences that limit causal claims."""
    rows: list[str] = []
    for config_name in CONFIG_ORDER:
        config = analysis["configs"][config_name]
        rows.append(
            "<tr>"
            f"<td><strong>{escape(config['label'])}</strong></td>"
            f"<td>{escape(config['checkpoint'])}</td>"
            f"<td>{escape(config['endpoint'])}</td>"
            f"<td class='num'>{config['temperature']}</td>"
            f"<td class='num'>{config['max_tokens']:,}</td>"
            f"<td class='num'>{config['workers']}</td>"
            f"<td>{'pi-check + 360s Bash default' if 'pi_check' in config_name else 'none'}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def build_report(analysis: dict[str, Any]) -> str:
    """Build the self-contained HTML report."""
    tc_base = analysis["configs"]["thinkingcap_baseline"]["aggregate"]
    tc_check = analysis["configs"]["thinkingcap_pi_check"]["aggregate"]
    aw_base = analysis["configs"]["agentworld_baseline"]["aggregate"]
    aw_check = analysis["configs"]["agentworld_pi_check"]["aggregate"]
    tc_pair = analysis["pairs"]["thinkingcap_treatment"]
    aw_pair = analysis["pairs"]["agentworld_treatment"]
    model_pair = analysis["pairs"]["pi_check_models"]
    tc_delivery = analysis["configs"]["thinkingcap_pi_check"]["delivery"]
    conclusion = analysis["conclusions"]

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,">
<title>ThinkingCap pi-check vs baseline and AgentWorld · 12_v2</title>
<style>
:root{{--bg:#f3f6fb;--surface:#fff;--surface-2:#f8fafc;--ink:#122033;--muted:#617087;--line:#d9e2ee;--blue:#315ee8;--blue-soft:#edf2ff;--green:#148258;--green-soft:#e8f7ef;--red:#c7463e;--red-soft:#fdeceb;--amber:#9a6900;--amber-soft:#fff3d5;--shadow:0 20px 60px rgba(15,35,65,.08);--radius:24px;--max:1420px}}
*{{box-sizing:border-box}}html{{background:var(--bg)}}body{{margin:0;color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;line-height:1.5;background:radial-gradient(circle at top left,rgba(49,94,232,.12),transparent 28%),linear-gradient(180deg,#fafcff,var(--bg))}}a{{color:#244fcf;font-weight:750;text-decoration:none}}a:hover{{text-decoration:underline}}.wrap{{max-width:var(--max);margin:auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.95);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}}.hero{{padding:clamp(24px,4vw,46px);overflow:hidden}}.eyebrow{{display:inline-block;padding:8px 12px;border-radius:999px;background:var(--blue-soft);color:#2348af;font-size:12px;font-weight:850;text-transform:uppercase;letter-spacing:.08em}}h1,h2,h3{{line-height:1.1;letter-spacing:-.03em}}h1{{font-size:clamp(2.15rem,5vw,4.5rem);max-width:18ch;margin:16px 0}}h2{{font-size:clamp(1.45rem,2.8vw,2.1rem);margin:0}}h3{{margin:8px 0 10px}}.subtitle{{font-size:1.08rem;max-width:90ch;color:var(--muted)}}.pillrow{{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}}.pill,.tag{{display:inline-flex;align-items:center;border-radius:999px;font-size:11px;font-weight:850;text-transform:uppercase;letter-spacing:.045em;padding:7px 10px}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:var(--blue-soft);color:#2348af}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin-top:26px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;min-height:122px;min-width:0}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:850;text-transform:uppercase;letter-spacing:.07em}}.stat .value{{display:block;font-size:clamp(1.35rem,2.4vw,2.05rem);font-weight:900;margin-top:9px}}.stat .sub{{display:block;color:var(--muted);font-size:.84rem;margin-top:6px}}section{{padding:clamp(19px,3vw,30px);margin-top:20px;min-width:0}}.section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap;margin-bottom:18px}}.section-head p{{margin:7px 0 0;max-width:90ch;color:var(--muted)}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f2f6ff,#fff);border-radius:14px;padding:15px 17px;margin-top:14px}}.callout.good{{border-color:var(--green);background:linear-gradient(90deg,#f0faf5,#fff)}}.callout.bad{{border-color:var(--red);background:linear-gradient(90deg,#fff4f3,#fff)}}.callout.caution{{border-color:var(--amber);background:linear-gradient(90deg,#fff8e7,#fff)}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:17px;min-width:0}}.grid-2>*{{min-width:0}}.card,.packet-card{{border:1px solid var(--line);border-radius:18px;padding:18px;background:var(--surface);min-width:0}}.packet-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.table-wrap{{overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:16px}}table{{border-collapse:collapse;width:100%;min-width:900px}}th,td{{padding:10px 11px;border-bottom:1px solid #e7edf5;text-align:left;vertical-align:top}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.055em;color:var(--muted);background:#fbfcff;position:sticky;top:0;z-index:1}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}td.task{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.81rem;max-width:310px;overflow-wrap:anywhere}}.mono{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.82rem;color:var(--muted);overflow-wrap:anywhere}}.muted{{color:var(--muted)}}.score{{font-variant-numeric:tabular-nums;font-weight:800}}.up{{color:var(--green);font-weight:850}}.down{{color:var(--red);font-weight:850}}.flat{{color:var(--muted);font-weight:750}}code{{background:#edf2ff;color:#283d78;border-radius:6px;padding:.1em .35em}}.foot{{color:var(--muted);font-size:.84rem;text-align:center;margin:24px 0 0;overflow-wrap:anywhere}}@media(max-width:980px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.grid-2,.packet-grid{{grid-template-columns:1fr}}}}@media(max-width:520px){{.wrap{{padding:12px 8px 36px}}.hero,section{{border-radius:18px}}.stats{{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}}.stat{{padding:13px}}}}
</style></head><body><div class="wrap">
<header class="hero">
<span class="eyebrow">144 complete trajectories · 12 tasks · 3 reps · high thinking</span>
<h1>Pi-check gave ThinkingCap fewer failed runs, not better finished runs.</h1>
<p class="subtitle">The combined pi-check and 360-second Bash timeout setup reduced ThinkingCap's invalid outcomes from {tc_base["invalid"]} to {tc_check["invalid"]} and raised its all-attempt average from {tc_base["mean_partial_all"]:.3f} to {tc_check["mean_partial_all"]:.3f}. But on the {tc_pair["common_valid_pairs"]} attempts that finished normally in both runs, quality was unchanged: {tc_pair["left_common_mean_partial"]:.3f} to {tc_pair["right_common_mean_partial"]:.3f}. The price was {((tc_pair["token_ratio"] - 1) * 100):.1f}% more tokens, and strict solves moved from {tc_base["solves"]} to {tc_check["solves"]}.</p>
<div class="pillrow"><span class="pill good">ThinkingCap invalids {tc_base["invalid"]} → {tc_check["invalid"]}</span><span class="pill neutral">finished quality {tc_pair["left_common_mean_partial"]:.3f} → {tc_pair["right_common_mean_partial"]:.3f}</span><span class="pill caution">tokens +{(tc_pair["token_ratio"] - 1) * 100:.1f}%</span><span class="pill bad">strict solves {tc_base["solves"]} → {tc_check["solves"]}</span><span class="pill neutral">treatment delivered 36/36</span></div>
<div class="stats">
<div class="stat"><span class="label">All attempts</span><span class="value">{tc_base["mean_partial_all"]:.3f} → {tc_check["mean_partial_all"]:.3f}</span><span class="sub">gain comes from fewer invalid outcomes</span></div>
<div class="stat"><span class="label">Both finished</span><span class="value">{format_delta(tc_pair["common_valid_mean_partial_delta"])}</span><span class="sub">mean partial change across {tc_pair["common_valid_pairs"]} attempts</span></div>
<div class="stat"><span class="label">Feature tests</span><span class="value">{format_percent(tc_pair["left_common_f2p_micro"])} → {format_percent(tc_pair["right_common_f2p_micro"])}</span><span class="sub">same {tc_pair["left_common_f2p_total"]:,} tests per side</span></div>
<div class="stat"><span class="label">Token use</span><span class="value">{format_compact(tc_base["total_tokens"])} → {format_compact(tc_check["total_tokens"])}</span><span class="sub">{format_compact(tc_delivery["post_check_tokens"])} tokens after re-audit began</span></div>
<div class="stat"><span class="label">AgentWorld</span><span class="value">{aw_base["mean_partial_all"]:.3f} → {aw_check["mean_partial_all"]:.3f}</span><span class="sub">same combined setup did not improve reliability</span></div>
</div></header>

<section><div class="section-head"><div><h2>Plain-English answer</h2><p>What changed, what did not, and what this run can support.</p></div></div>
<div class="callout good"><strong>ThinkingCap became more likely to finish with a grade.</strong> Three baseline failures became graded attempts; one different attempt became invalid. That net reliability gain explains the higher all-attempt average.</div>
<div class="callout"><strong>When both runs finished normally, ThinkingCap's average quality stayed the same.</strong> Mean partial moved by {format_delta(tc_pair["common_valid_mean_partial_delta"])}. Feature-test coverage rose, but preservation slipped on some attempts and no strict solve survived.</div>
<div class="callout caution"><strong>This was expensive.</strong> ThinkingCap used {format_compact(tc_check["total_tokens"] - tc_base["total_tokens"])} more tokens and {format_duration(tc_check["wall_sum_s"] - tc_base["wall_sum_s"])} more summed agent time. The final re-audit alone consumed {format_compact(tc_delivery["post_check_tokens"])} tokens.</div>
<div class="callout bad"><strong>Do not call this a clean pi-check result.</strong> The config changed pi-check and the Bash timeout default together, and every cell was a fresh model run. The evidence shows what the combined setup did; it does not tell us which mechanism caused each change.</div>
</section>

<section><div class="section-head"><div><h2>All four completed runs</h2><p>Strict solve means every feature and preservation test passed. “Valid” means the verifier produced a usable grade.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Run</th><th class="num">Strict</th><th class="num">Valid</th><th class="num">Mean partial</th><th class="num">Feature tests</th><th class="num">Preservation</th><th class="num">Tokens</th><th class="num">Agent time</th></tr></thead><tbody>{render_aggregate_table(analysis)}</tbody></table></div>
</section>

<section><div class="section-head"><div><h2>What the combined setup changed within each model</h2><p>“Both-finished change” excludes attempts where either side failed to produce a grade. Wins and losses use a 0.05 partial-score threshold.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Model</th><th class="num">Invalid</th><th class="num">Strict</th><th class="num">All-attempt change</th><th class="num">Both-finished change</th><th class="num">Wins / losses / ties</th><th class="num">Tokens</th><th class="num">Agent time</th></tr></thead><tbody>{render_within_model_table(analysis)}</tbody></table></div>
<div class="callout"><strong>ThinkingCap:</strong> {tc_pair["left_only_invalid"]} invalid baseline attempts were recovered, while {tc_pair["right_only_invalid"]} new invalid appeared. Across stable finished attempts, the mean changed by only {format_delta(tc_pair["common_valid_mean_partial_delta"])}.</div>
<div class="callout caution"><strong>AgentWorld:</strong> {aw_pair["left_only_invalid"]} invalid baseline attempts were recovered, but {aw_pair["right_only_invalid"]} new invalids appeared. Its all-attempt average fell {abs(aw_pair["mean_partial_delta_all"]):.3f} while token use rose {(aw_pair["token_ratio"] - 1) * 100:.1f}%.</div>
</section>

<section><div class="section-head"><div><h2>Feature work improved more than final task completion</h2><p>These rows use only attempts graded in both the baseline and combined runs. Feature tests measure the requested behavior; preservation tests measure existing behavior.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Model</th><th class="num">Matched attempts</th><th class="num">Base feature</th><th class="num">Check feature</th><th class="num">Base preservation</th><th class="num">Check preservation</th><th class="num">Base partial</th><th class="num">Check partial</th></tr></thead><tbody>{render_common_grade_table(analysis)}</tbody></table></div>
<div class="callout"><strong>Why no strict solve?</strong> Pi-check often found or tested more behavior, but the remaining misses were broad: concurrency cleanup, hidden edge cases, and preservation regressions. More feature tests passing did not make every required test pass in one attempt.</div>
</section>

<section><div class="section-head"><div><h2>ThinkingCap versus AgentWorld under the combined setup</h2><p>This is a local-model contrast, not a controlled checkpoint test. Both received pi-check and the Bash timeout guard, but their model, server, sampling, and output settings differ.</p></div></div>
<div class="grid-2">
<div class="card"><h3>ThinkingCap</h3><p><strong>{tc_check["valid"]}/36 valid</strong> · {tc_check["mean_partial_all"]:.3f} mean partial · {format_percent(tc_check["f2p_micro"])} feature tests · {format_compact(tc_check["total_tokens"])} tokens.</p></div>
<div class="card"><h3>AgentWorld</h3><p><strong>{aw_check["valid"]}/36 valid</strong> · {aw_check["mean_partial_all"]:.3f} mean partial · {format_percent(aw_check["f2p_micro"])} feature tests · {format_compact(aw_check["total_tokens"])} tokens.</p></div>
</div>
<div class="callout good"><strong>On this subset, ThinkingCap handled the combined setup better.</strong> It had {model_pair["wins_over_0_05"]} material paired wins, {model_pair["losses_below_minus_0_05"]} material losses, and used only {(model_pair["token_ratio"] - 1) * 100:.1f}% more tokens than AgentWorld. Among {model_pair["common_valid_pairs"]} attempts both models graded, ThinkingCap averaged {format_delta(model_pair["common_valid_mean_partial_delta"])} higher partial.</div>
<div class="callout caution"><strong>Do not read this as a pure fine-tune ranking.</strong> ThinkingCap is a 27B dense checkpoint on port 8081 with temperature 1.0 and a 98,304-token output ceiling. AgentWorld is a 35B-A3B mixture-of-experts checkpoint on port 8080 with temperature 0.6 and a 65,536-token ceiling.</div>
</section>

<section><div class="section-head"><div><h2>What pi-check actually did</h2><p>Both treatments reached all 36 attempts. A mutation means an edit or write tool call after the “Re-audit every requirement” message.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Run</th><th class="num">Delivered</th><th class="num">Cells changed after check</th><th class="num">Mutation calls</th><th class="num">Post-check tokens</th><th class="num">Share of run</th><th class="num">Tool errors / calls</th><th class="num">Malformed calls</th></tr></thead><tbody>{render_delivery_rows(analysis)}</tbody></table></div>
<div class="callout"><strong>ThinkingCap acted more often:</strong> it changed files after re-audit in {tc_delivery["cells_with_post_check_mutation"]} of 36 attempts, compared with {analysis["configs"]["agentworld_pi_check"]["delivery"]["cells_with_post_check_mutation"]} for AgentWorld. Activity did not reliably become a correct repair: several packets show extra tests or edits followed by the same hidden failures.</div>
<h3>Recorded tool-result errors</h3>
<p class="muted">Most Bash errors were normal failing tests or diagnostic commands, not broken tool transport. Both models produced zero malformed tool calls.</p>
<div class="table-wrap"><table><thead><tr><th>Cause</th><th class="num">ThinkingCap</th><th class="num">AgentWorld</th></tr></thead><tbody>{render_tool_error_rows(analysis)}</tbody></table></div>
</section>

<section><div class="section-head"><div><h2>Where scores moved</h2><p>Task means average three reps. Large gains on LangChain mainly reflect recovered invalid attempts; large Mobly movement reflects failure churn in both directions.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">TC base</th><th class="num">TC check</th><th class="num">TC change</th><th class="num">TC invalid</th><th class="num">AW base</th><th class="num">AW check</th><th class="num">AW change</th><th class="num">AW invalid</th></tr></thead><tbody>{render_task_rows(analysis)}</tbody></table></div>
<h3>Language view</h3>
<div class="table-wrap"><table><thead><tr><th>Language</th><th class="num">TC base</th><th class="num">TC check</th><th class="num">AW base</th><th class="num">AW check</th></tr></thead><tbody>{render_language_rows(analysis)}</tbody></table></div>
</section>

<section><div class="section-head"><div><h2>Nine ThinkingCap attempts worth reading</h2><p>{escape(analysis["comparison"]["packet_rule"])} Each packet includes result metrics, changed files, failed tests, final claims, and post-check edits.</p></div></div>
<div class="packet-grid">{render_packet_cards(analysis)}</div>
</section>

<section><div class="section-head"><div><h2>Complete 36-attempt table</h2><p>Every task and rep appears before any filtering. Each cell shows status, partial score, and feature-test rate.</p></div></div>
<div class="table-wrap"><table style="min-width:1450px"><thead><tr><th>Task</th><th class="num">Rep</th><th>ThinkingCap baseline</th><th>ThinkingCap check</th><th>AgentWorld baseline</th><th>AgentWorld check</th><th>Evidence</th></tr></thead><tbody>{render_full_cell_rows(analysis)}</tbody></table></div>
</section>

<section><div class="section-head"><div><h2>What differs between these runs</h2><p>Within each model, the provider contract stayed fixed. Across models, several serving and model settings differ.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Run</th><th>Checkpoint</th><th>Endpoint</th><th class="num">Temperature</th><th class="num">Max output</th><th class="num">Workers</th><th>Added support</th></tr></thead><tbody>{render_config_rows(analysis)}</tbody></table></div>
<div class="callout caution"><strong>Causal limit:</strong> {escape(analysis["comparison"]["causal_limit"])}</div>
</section>

<section><div class="section-head"><div><h2>Decision</h2><p>What the evidence supports doing next.</p></div></div>
<div class="callout good"><strong>Keep investigating bounded Bash commands.</strong> The combined ThinkingCap run recovered three invalid attempts, including two LangChain attempts, and neither model showed tool-parser failures.</div>
<div class="callout caution"><strong>Do not treat pi-check as an efficiency win.</strong> ThinkingCap used 67.8% more tokens; AgentWorld used 45.0% more. Neither pi-check run produced a strict solve.</div>
<div class="callout"><strong>Run two controls:</strong> ThinkingCap with timeout only, then ThinkingCap with pi-check only. Keep the same server, tasks, reps, and worker count. That will tell us whether the reliability gain came from bounded commands, the final re-audit, or ordinary run variance.</div>
<div class="callout"><strong>Best current reading:</strong> {escape(conclusion["thinkingcap"])} {escape(conclusion["agentworld"])}</div>
</section>

<p class="foot">Generated from immutable result, session, provider-request, timeout-trace, patch, and verifier artifacts. Source data: <a href="analysis.json">analysis.json</a>. Previous baseline-only model comparison: <a href="../thinkingcap-vs-agentworld-12v2/">ThinkingCap vs AgentWorld baseline report</a>.</p>
</div></body></html>"""


def main() -> None:
    """Load the extracted comparison and render the HTML page."""
    analysis = json.loads(ANALYSIS_PATH.read_text())
    document = build_report(analysis)
    OUTPUT_PATH.write_text(document)
    print(f"ThinkingCap pi-check report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
