#!/usr/bin/env python3
"""Render the local-model versus frontier trajectory analysis."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

REPORT_ROOT = Path(__file__).resolve().parent
ANALYSIS_PATH = REPORT_ROOT / "analysis.json"
FEEDBACK_ANALYSIS_PATH = REPORT_ROOT / "feedback-uptake/analysis-v2.json"
MODEL_LABELS = {
    "frontier": "GPT-5.6 SOL",
    "agentworld": "AgentWorld",
    "thinkingcap": "ThinkingCap",
}


def escape(value: object) -> str:
    """Escape one value for safe HTML rendering."""
    return html.escape(str(value), quote=True)


def format_number(value: float | None, digits: int = 1) -> str:
    """Format one optional number."""
    if value is None:
        return "—"
    return f"{value:,.{digits}f}"


def format_percent(value: float | None, digits: int = 0) -> str:
    """Format one optional zero-to-one ratio as a percentage."""
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def outcome_tag(result: dict[str, Any]) -> str:
    """Render one benchmark outcome tag."""
    reward = result["reward_binary"]
    if reward == 1:
        return '<span class="tag good">solved</span>'
    if reward is not None and reward < 0:
        return '<span class="tag bad">invalid</span>'
    return '<span class="tag neutral">unsolved</span>'


def short_outcome(reward: int | None) -> str:
    """Render one compact repetition outcome."""
    if reward == 1:
        return '<span class="rep good">S</span>'
    if reward is not None and reward < 0:
        return '<span class="rep bad">I</span>'
    return '<span class="rep neutral">U</span>'


def render_outcome_rows(analysis: dict[str, Any]) -> str:
    """Render all three repetitions for every task and model."""
    rows = []
    for row in analysis["outcomes_by_task"]:
        cells = []
        for model_key in ("frontier", "agentworld", "thinkingcap"):
            outcomes = row["outcomes"][model_key]
            cells.append(
                "<td><div class='rep-set'>"
                + "".join(
                    f"<span><small>r{rep}</small>{short_outcome(reward)}</span>"
                    for rep, reward in enumerate(outcomes)
                )
                + "</div></td>"
            )
        rows.append(
            "<tr>"
            f"<td><strong>{escape(row['task'])}</strong></td>"
            + "".join(cells)
            + "</tr>"
        )
    return "".join(rows)


def tool_fraction(summary: dict[str, Any], tool: str) -> str:
    """Format failures and rate for one tool's recorded results."""
    row = summary["by_tool"][tool]
    return f"{row['errors']}/{row['total']} <span class='muted'>({format_percent(row['error_rate'], 1)})</span>"


def render_tool_result_rows(analysis: dict[str, Any]) -> str:
    """Render full-run tool-result failures without conflating them with parser errors."""
    rows = []
    for model_key in ("frontier", "agentworld", "thinkingcap"):
        summary = analysis["tool_results"][model_key]
        rows.append(
            "<tr>"
            f"<td><strong>{MODEL_LABELS[model_key]}</strong></td>"
            f"<td class='num'>{summary['errors']}/{summary['total']} <span class='muted'>({format_percent(summary['error_rate'], 1)})</span></td>"
            f"<td class='num'>{tool_fraction(summary, 'bash')}</td>"
            f"<td class='num'>{tool_fraction(summary, 'edit')}</td>"
            f"<td class='num'>{tool_fraction(summary, 'read')}</td>"
            f"<td class='num'>{summary['error_categories'].get('malformed edit arguments', 0)}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_file_focus_bar(summary: dict[str, Any]) -> str:
    """Render a deterministic stacked bar for file-category focus."""
    shares = summary["file_category_shares"]
    segments = []
    for category in ("source", "test", "docs", "config", "other"):
        width = shares[category] * 100
        if width <= 0:
            continue
        segments.append(
            f"<span class='seg {category}' style='width:{width:.4f}%' "
            f"title='{escape(category)} {width:.1f}%'></span>"
        )
    return "<div class='focus-bar'>" + "".join(segments) + "</div>"


def render_coverage_rows(analysis: dict[str, Any]) -> str:
    """Render aligned frontier-gap cohort metrics."""
    rows = []
    for local_key in ("agentworld", "thinkingcap"):
        cohort = analysis["gap_cohorts"][local_key]
        local = cohort["local"]
        frontier = cohort["frontier"]
        unique_local = sum(local["file_category_counts"].values())
        unique_frontier = sum(frontier["file_category_counts"].values())
        repeat_local = local["total_successful_explicit_reads"] / unique_local
        repeat_frontier = frontier["total_successful_explicit_reads"] / unique_frontier
        rows.append(
            "<tr>"
            f"<td><strong>{MODEL_LABELS[local_key]}</strong><br><span class='muted'>{cohort['pairs']} exact frontier-solved failures</span></td>"
            f"<td class='num'>{format_number(local['median_content_files'])}</td>"
            f"<td class='num'>{format_number(frontier['median_content_files'])}</td>"
            f"<td class='num'>{format_percent(cohort['median_frontier_file_recall'])}</td>"
            f"<td class='num'>{format_number(local['median_pre_mutation_files'])}</td>"
            f"<td class='num'>{format_number(frontier['median_pre_mutation_files'])}</td>"
            f"<td class='num'>{repeat_local:.2f}×</td>"
            f"<td class='num'>{repeat_frontier:.2f}×</td>"
            f"<td class='num'>{cohort['local_reads_fewer_files']} / {cohort['pairs']}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_focus_panels(analysis: dict[str, Any]) -> str:
    """Render file-category focus panels for each aligned local cohort."""
    panels = []
    for local_key in ("agentworld", "thinkingcap"):
        cohort = analysis["gap_cohorts"][local_key]
        rows = []
        for side, label in (
            ("local", MODEL_LABELS[local_key]),
            ("frontier", "GPT-5.6 SOL"),
        ):
            summary = cohort[side]
            counts = summary["file_category_counts"]
            rows.append(
                "<div class='focus-row'>"
                f"<div><strong>{escape(label)}</strong><span>{sum(counts.values())} cell-file observations</span></div>"
                f"{render_file_focus_bar(summary)}"
                "<div class='focus-counts'>"
                f"<span>source {counts['source']}</span><span>tests {counts['test']}</span>"
                f"<span>docs {counts['docs']}</span><span>config {counts['config']}</span>"
                "</div></div>"
            )
        panels.append(
            "<article class='panel'>"
            f"<h3>{MODEL_LABELS[local_key]} failure cohort</h3>"
            f"<p class='muted'>{cohort['pairs']} task/rep cells where GPT-5.6 solved and {MODEL_LABELS[local_key]} did not.</p>"
            + "".join(rows)
            + "</article>"
        )
    return "".join(panels)


def render_timing_rows(analysis: dict[str, Any]) -> str:
    """Render first-mutation and validation timing comparisons."""
    rows = []
    for local_key in ("agentworld", "thinkingcap"):
        cohort = analysis["gap_cohorts"][local_key]
        local = cohort["local"]
        frontier = cohort["frontier"]
        rows.append(
            "<tr>"
            f"<td><strong>{MODEL_LABELS[local_key]}</strong></td>"
            f"<td class='num'>{format_number(local['median_first_mutation_event'])}</td>"
            f"<td class='num'>{format_number(frontier['median_first_mutation_event'])}</td>"
            f"<td class='num'>{format_number(local['median_first_validation_event'])}</td>"
            f"<td class='num'>{format_number(frontier['median_first_validation_event'])}</td>"
            f"<td class='num'>{local['total_validation_commands']}</td>"
            f"<td class='num'>{frontier['total_validation_commands']}</td>"
            f"<td class='num'>{local['cells_without_validation']}</td>"
            f"<td class='num'>{local['cells_changing_tests']} / {cohort['pairs']}</td>"
            f"<td class='num'>{frontier['cells_changing_tests']} / {cohort['pairs']}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_feedback_uptake_rows(feedback: dict[str, Any]) -> str:
    """Render unseen feedback candidates with explicit event-level denominators."""
    rows = []
    for model_key in ("frontier", "agentworld", "thinkingcap"):
        summary = feedback["models"][model_key]
        density = feedback["candidate_density"][model_key]
        outcomes = summary["window_outcome_counts"]
        rows.append(
            "<tr>"
            f"<td><strong>{MODEL_LABELS[model_key]}</strong></td>"
            f"<td class='num'>{summary['candidate_units']}</td>"
            f"<td class='num'>{density['candidate_units_per_100_tool_calls']:.1f}</td>"
            f"<td class='num'>{summary['negative_feedback']}</td>"
            f"<td class='num'>{outcomes.get('recovered', 0)} <span class='muted'>({format_percent(summary['recovery_rate'], 1)})</span></td>"
            f"<td class='num'>{outcomes.get('progressed', 0)}</td>"
            f"<td class='num'>{outcomes.get('not_recovered', 0)} <span class='muted'>({format_percent(summary['not_recovered_rate'], 1)})</span></td>"
            f"<td class='num'>{format_percent(summary['relevant_change_rate'], 1)}</td>"
            f"<td class='num'>{format_percent(summary['post_change_validation_rate'], 1)}</td>"
            f"<td class='num'>{summary['schema_invalid_tool_arguments']}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_decision_cards(analysis: dict[str, Any]) -> str:
    """Render selected task packets with concrete decision divergence evidence."""
    cards = []
    for packet in analysis["selected_packets"]:
        divergence = packet["decision_divergence"]
        models = packet["models"]
        stem = f"{packet['task']}__rep{packet['rep']}"
        is_control = divergence["stage"] == "local success control"
        card_class = "control" if is_control else ""
        model_stats = []
        for model_key in ("frontier", "agentworld", "thinkingcap"):
            model = models[model_key]
            result = model["result"]
            trace = model["trace"]
            f2p = (
                f"{result['f2p_passed']}/{result['f2p_total']}"
                if result["f2p_total"] is not None
                else "not graded"
            )
            model_stats.append(
                "<div class='model-stat'>"
                f"<span>{MODEL_LABELS[model_key]}</span>{outcome_tag(result)}"
                f"<b>{f2p} F2P</b>"
                f"<small>{trace['content_read_count']} files · {trace['pre_mutation_count']} before mutation · {len(trace['validation_commands'])} validations</small>"
                "</div>"
            )
        frontier_only_aw = models["agentworld"]["frontier_coverage"][
            "frontier_only_paths"
        ][:5]
        frontier_only_tc = models["thinkingcap"]["frontier_coverage"][
            "frontier_only_paths"
        ][:5]
        cards.append(
            f"<article class='decision-card {card_class}'>"
            "<div class='decision-head'>"
            f"<div><span class='tag {'good' if is_control else 'caution'}'>{escape(divergence['stage'])}</span>"
            f"<h3>{escape(packet['metadata']['title'])} · rep {packet['rep']}</h3></div>"
            f"<span class='language'>{escape(packet['metadata']['language'])}</span>"
            "</div>"
            f"<p><strong>Frontier:</strong> {escape(divergence['frontier_behavior'])}</p>"
            f"<p><strong>AgentWorld divergence:</strong> {escape(divergence['agentworld_divergence'])}</p>"
            f"<p><strong>ThinkingCap divergence:</strong> {escape(divergence['thinkingcap_divergence'])}</p>"
            "<div class='model-stats'>" + "".join(model_stats) + "</div>"
            "<details><summary>Frontier-read files absent from each local trajectory</summary>"
            f"<p><strong>AgentWorld:</strong> {escape(', '.join(frontier_only_aw) or 'none')}</p>"
            f"<p><strong>ThinkingCap:</strong> {escape(', '.join(frontier_only_tc) or 'none')}</p>"
            "</details>"
            f"<p class='packet-links'><a href='packets/{escape(stem)}.md'>Readable packet</a> · <a href='packets/{escape(stem)}.json'>Packet JSON</a></p>"
            "</article>"
        )
    return "".join(cards)


def render_task_rows(analysis: dict[str, Any]) -> str:
    """Render task-level file-coverage and feature-gap summaries."""
    agentworld = {
        row["task"]: row for row in analysis["task_gap_summaries"]["agentworld"]
    }
    thinkingcap = {
        row["task"]: row for row in analysis["task_gap_summaries"]["thinkingcap"]
    }
    rows = []
    for task in sorted(set(agentworld) | set(thinkingcap)):
        aw = agentworld.get(task)
        tc = thinkingcap.get(task)

        def cell(row: dict[str, Any] | None, key: str, *, percent: bool = False) -> str:
            if row is None:
                return "—"
            value = row[key]
            return format_percent(value) if percent else format_number(value)

        rows.append(
            "<tr>"
            f"<td><strong>{escape(task)}</strong><br><span class='muted'>{escape(analysis['task_metadata'][task]['language'])}</span></td>"
            f"<td class='num'>{aw['pairs'] if aw else 0}</td>"
            f"<td class='num'>{cell(aw, 'local_mean_content_files')}</td>"
            f"<td class='num'>{cell(aw, 'frontier_mean_content_files')}</td>"
            f"<td class='num'>{cell(aw, 'mean_frontier_file_recall', percent=True)}</td>"
            f"<td class='num'>{cell(aw, 'local_mean_f2p', percent=True)}</td>"
            f"<td class='num'>{tc['pairs'] if tc else 0}</td>"
            f"<td class='num'>{cell(tc, 'local_mean_content_files')}</td>"
            f"<td class='num'>{cell(tc, 'frontier_mean_content_files')}</td>"
            f"<td class='num'>{cell(tc, 'mean_frontier_file_recall', percent=True)}</td>"
            f"<td class='num'>{cell(tc, 'local_mean_f2p', percent=True)}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_scaffold_cards(analysis: dict[str, Any]) -> str:
    """Render evidence-backed scaffold experiments."""
    cards = []
    for index, row in enumerate(analysis["scaffoldability_ledger"], start=1):
        cards.append(
            "<article class='scaffold-card'>"
            f"<div class='scaffold-number'>{index}</div>"
            f"<div><h3>{escape(row['candidate_support'])}</h3>"
            f"<p><strong>Observed weakness:</strong> {escape(row['weakness'])}</p>"
            f"<p><strong>Evidence:</strong> {escape(row['evidence'])}</p>"
            f"<p><strong>Mechanism:</strong> {escape(row['expected_mechanism'])}</p>"
            f"<p><strong>Minimal A/B:</strong> {escape(row['minimal_experiment'])}</p>"
            f"<details><summary>Limits, risk, and success criterion</summary>"
            f"<p><strong>Non-targets:</strong> {escape(row['non_targets'])}</p>"
            f"<p><strong>Risk:</strong> {escape(row['risk'])}</p>"
            f"<p><strong>Success:</strong> {escape(row['success_criterion'])}</p>"
            "</details></div></article>"
        )
    return "".join(cards)


def render_gap_pair_rows(analysis: dict[str, Any]) -> str:
    """Render every exact frontier-solved/local-failed pair."""
    rows = []
    for local_key in ("agentworld", "thinkingcap"):
        for pair in analysis["gap_pairs"][local_key]:
            local = pair["local_result"]
            frontier = pair["frontier_result"]
            coverage = pair["coverage"]
            f2p = (
                format_percent(local["f2p"])
                if local["f2p"] is not None
                else "not graded"
            )
            rows.append(
                "<tr>"
                f"<td>{MODEL_LABELS[local_key]}</td>"
                f"<td>{escape(pair['task'])}</td>"
                f"<td class='num'>{pair['rep']}</td>"
                f"<td>{outcome_tag(local)}</td>"
                f"<td class='num'>{f2p}</td>"
                f"<td class='num'>{local['reward_partial']:.3f}</td>"
                f"<td class='num'>{coverage['local_content_files']}</td>"
                f"<td class='num'>{coverage['frontier_content_files']}</td>"
                f"<td class='num'>{format_percent(coverage['frontier_file_recall'])}</td>"
                f"<td class='num'>{coverage['local_pre_mutation_files']}</td>"
                f"<td class='num'>{coverage['frontier_pre_mutation_files']}</td>"
                f"<td class='num'>{frontier['f2p_passed']}/{frontier['f2p_total']}</td>"
                "</tr>"
            )
    return "".join(rows)


def build_report() -> str:
    """Build the complete self-contained frontier-gap report."""
    analysis = json.loads(ANALYSIS_PATH.read_text())
    feedback = json.loads(FEEDBACK_ANALYSIS_PATH.read_text())
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Local-model trajectory gaps against GPT-5.6 SOL</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23335dff%22/><text x=%2250%22 y=%2264%22 text-anchor=%22middle%22 font-size=%2238%22 fill=%22white%22>Δ</text></svg>"/>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#b77d00;--amber-soft:#fff4d8;--purple:#7754d8;--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);--radius-xl:28px;--radius-lg:20px;--max:1320px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 25%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.91em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px;overflow-wrap:anywhere}}.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}.hero,section{{background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}.hero{{padding:clamp(24px,4vw,42px);overflow:hidden;position:relative}}.hero::after{{content:"";position:absolute;inset:auto -9% -45% auto;width:500px;height:500px;background:radial-gradient(circle,rgba(51,93,255,.13),transparent 70%);pointer-events:none}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2.05rem,4.7vw,4.2rem);margin-top:14px;max-width:18ch}}h2{{font-size:clamp(1.45rem,2.5vw,2.1rem)}}h3{{font-size:1.12rem;margin-bottom:8px}}.subtitle{{max-width:88ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.09rem);margin:15px 0 0}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}.pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line)}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:var(--blue-2)}}.stats{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:13px;margin-top:25px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:15px;min-height:118px;box-shadow:var(--shadow-sm)}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:9px}}.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.95rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;margin-top:8px;font-size:.85rem;color:var(--muted);font-weight:600}}section{{margin-top:20px;padding:clamp(18px,3vw,29px)}}.section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}}.section-head p{{margin:7px 0 0;color:var(--muted);max-width:90ch}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}.panel{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-sm)}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:15px 17px;color:#22314d;margin-top:14px}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff9e8,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout strong{{color:var(--blue-2)}}.tag{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:.72rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}}.rep-set{{display:flex;gap:10px;align-items:center;min-width:180px}}.rep-set>span{{display:flex;align-items:center;gap:4px}}.rep-set small{{color:var(--muted);font-size:.68rem}}.rep{{width:25px;height:25px;display:inline-grid;place-items:center;border-radius:7px;font-size:.73rem;font-weight:900}}.rep.good{{background:var(--green-soft);color:var(--green)}}.rep.bad{{background:var(--red-soft);color:var(--red)}}.rep.neutral{{background:#eef3ff;color:var(--blue-2)}}.muted{{color:var(--muted);font-size:.86em}}.table-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:14px}}table{{width:100%;border-collapse:collapse;font-size:.87rem}}th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:800;background:var(--surface-2);position:sticky;top:0}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}tbody tr:hover{{background:var(--surface-2)}}tbody tr:last-child td{{border-bottom:0}}.focus-row{{display:grid;grid-template-columns:150px 1fr;gap:10px 14px;align-items:center;margin-top:14px}}.focus-row>div:first-child span{{display:block;color:var(--muted);font-size:.76rem}}.focus-bar{{height:20px;border-radius:999px;overflow:hidden;background:#edf2f7;display:flex;border:1px solid #dbe4ef}}.seg.source{{background:var(--blue)}}.seg.test{{background:var(--green)}}.seg.docs{{background:var(--amber)}}.seg.config{{background:var(--purple)}}.seg.other{{background:#8fa0b5}}.focus-counts{{grid-column:2;display:flex;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:.75rem}}.legend{{display:flex;gap:14px;flex-wrap:wrap;color:var(--muted);font-size:.82rem}}.legend span::before{{content:"";display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px}}.legend .source::before{{background:var(--blue)}}.legend .test::before{{background:var(--green)}}.legend .docs::before{{background:var(--amber)}}.legend .config::before{{background:var(--purple)}}.pattern{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-sm)}}.pattern .number{{font-size:2rem;font-weight:900;color:var(--blue);line-height:1;margin-bottom:12px}}.pattern p{{margin-bottom:0;color:#34445d}}.decision-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px;min-width:0}}.decision-card{{border:1px solid var(--line);border-top:5px solid var(--amber);border-radius:var(--radius-lg);background:var(--surface);padding:18px;box-shadow:var(--shadow-sm);min-width:0}}.decision-card.control{{border-top-color:var(--green)}}.decision-head{{display:flex;align-items:start;justify-content:space-between;gap:12px}}.decision-head h3{{margin-top:9px}}.language{{font-size:.75rem;color:var(--muted);font-weight:800;text-transform:uppercase}}.decision-card p{{font-size:.9rem}}.model-stats{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:14px 0}}.model-stat{{border:1px solid var(--line);background:var(--surface-2);border-radius:12px;padding:10px;display:flex;flex-direction:column;align-items:flex-start;gap:5px}}.model-stat span:first-child{{font-size:.73rem;color:var(--muted);font-weight:800;text-transform:uppercase}}.model-stat b{{font-size:.9rem}}.model-stat small{{color:var(--muted);line-height:1.35}}details{{border:1px solid var(--line);border-radius:12px;background:var(--surface-2);padding:11px 13px;margin-top:10px}}summary{{cursor:pointer;font-weight:800;color:#263b66}}.packet-links{{margin-bottom:0;font-weight:750}}.scaffold-list{{display:grid;gap:14px}}.scaffold-card{{display:grid;grid-template-columns:48px 1fr;gap:14px;border:1px solid var(--line);border-radius:var(--radius-lg);background:var(--surface);padding:17px;box-shadow:var(--shadow-sm)}}.scaffold-number{{width:42px;height:42px;display:grid;place-items:center;border-radius:13px;background:#eef3ff;color:var(--blue);font-size:1.2rem;font-weight:900}}.scaffold-card p{{margin:7px 0;font-size:.91rem}}.foot{{margin-top:24px;color:var(--muted);font-size:.84rem;text-align:center}}@media(max-width:1050px){{.stats{{grid-template-columns:repeat(3,minmax(0,1fr))}}.grid-3{{grid-template-columns:1fr}}}}@media(max-width:850px){{.grid-2,.decision-grid{{grid-template-columns:1fr}}.model-stats{{grid-template-columns:1fr}}}}@media(max-width:650px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.focus-row{{grid-template-columns:1fr}}.focus-counts{{grid-column:1}}.scaffold-card{{grid-template-columns:1fr}}.decision-card{{overflow:hidden}}.decision-head{{flex-wrap:wrap}}}}
</style></head><body><div class="wrap">
<header class="hero">
<span class="eyebrow">12 tasks · 3 repetitions · 3 models · 108 trajectories</span>
<h1>The local gap opens before validation.</h1>
<p class="subtitle">Every model ran every task three times. The aggregate comparison uses all 36 trajectories per model. GPT‑5.6 SOL usually builds a broader repository model before editing; AgentWorld repeatedly rereads a narrower surface; ThinkingCap explores more broadly but commits to an architecture earlier. A separate 108-trajectory feedback audit shows that the locals usually react to negative results, but less often close the issue before moving on.</p>
<div class="pillrow"><span class="pill caution">AgentWorld · 43% frontier-file overlap</span><span class="pill caution">ThinkingCap · 61% overlap</span><span class="pill neutral">Frontier · 24/36 solved</span><span class="pill neutral">47 model/rep gap comparisons</span><span class="pill neutral">1,165 unseen feedback cases</span><span class="pill neutral">Nine detailed examples</span></div>
<div class="stats">
<div class="stat"><span class="label">AgentWorld median files</span><span class="value">11.5 vs 16.5</span><span class="sub">local vs aligned frontier</span></div>
<div class="stat"><span class="label">ThinkingCap median files</span><span class="value">14 vs 16</span><span class="sub">local vs aligned frontier</span></div>
<div class="stat"><span class="label">Before first mutation · AW</span><span class="value">9 vs 14.5</span><span class="sub">exact content-read files</span></div>
<div class="stat"><span class="label">Before first mutation · TC</span><span class="value">11 vs 14</span><span class="sub">exact content-read files</span></div>
<div class="stat"><span class="label">First validation · AW</span><span class="value">59 vs 32</span><span class="sub">median tool-event position</span></div>
<div class="stat"><span class="label">First validation · TC</span><span class="value">48.5 vs 31.5</span><span class="sub">median tool-event position</span></div>
</div></header>

<section><div class="section-head"><div><h2>Capability diagnosis</h2><p>The two local models diverge from the frontier reference in different ways.</p></div></div>
<div class="grid-3">
<div class="callout caution"><strong>AgentWorld loses breadth through repetition.</strong> It made 808 read calls across 24 failures but covered only 276 task-local unique file observations. The aligned frontier made 530 calls across 439 observations. AgentWorld changed tests in 3/24 cells; the frontier did so in 23/24.</div>
<div class="callout caution"><strong>ThinkingCap loses flexibility after choosing a design.</strong> It changed tests in 22/23 cells and ran 349 validation commands versus the frontier's 202, yet began mutation after fewer files and validated much later. More testing could not recover omitted seams.</div>
<div class="callout"><strong>Common failure: local mechanics replace end-to-end contracts.</strong> Retry without audit persistence, serialization without deserialization, barriers without lifecycle records, and callable execution without runtime rebinding recur across languages.</div>
</div>
<div class="callout good"><strong>Local success control:</strong> ThinkingCap solved SQL formatter rep1 after reading 21 files before mutation—including tokenizer engine, parser creation, layout, dialect, and BigQuery keyword seams. File breadth is not sufficient, but the control shows that a complete architecture model can move this local model to a strict solve.</div>
</section>

<section><div class="section-head"><div><h2>What was compared</h2><p>Each letter below is one complete benchmark trajectory. Repetitions are shown separately: <strong>S</strong> = strict solve, <strong>U</strong> = graded but unsolved, and <strong>I</strong> = invalid or timed out.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th>GPT-5.6 SOL · reps 0/1/2</th><th>AgentWorld · reps 0/1/2</th><th>ThinkingCap · reps 0/1/2</th></tr></thead><tbody>{render_outcome_rows(analysis)}</tbody></table></div>
<div class="callout"><strong>Why the report says 47 comparisons:</strong> GPT‑5.6 solved 24 of its 36 task/repetition cells. AgentWorld failed all 24 matching cells. ThinkingCap failed 23 and solved one. That produces 24 + 23 = 47 local-versus-frontier failure comparisons. It does not mean only 47 trajectories existed; the full experiment contains 108.</div>
</section>

<section><div class="section-head"><div><h2>File overlap before interpretation</h2><p>Coverage counts successful exact files opened through <code>read</code> or named as exact shell content targets. Listings and glob searches are discovery, not comprehension.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Local subject</th><th class="num">Local median files</th><th class="num">Frontier median</th><th class="num">Frontier recall</th><th class="num">Local pre-mutation</th><th class="num">Frontier pre-mutation</th><th class="num">Local reads / unique</th><th class="num">Frontier reads / unique</th><th class="num">Local read fewer</th></tr></thead><tbody>{render_coverage_rows(analysis)}</tbody></table></div>
<div class="callout"><strong>What “frontier-file recall” means:</strong> for one matching task and repetition, take the exact files GPT‑5.6 opened and ask what fraction the local model also opened. If GPT‑5.6 opened 20 files and the local model opened 8 of those same files, the overlap is 40%. The reported 43% and 61% are the middle values across the 24 AgentWorld and 23 ThinkingCap failure comparisons. This is behavioral overlap—not proof that every frontier-read file was necessary or that opening a file means understanding it.</div>
<div class="callout"><strong>Interpretation:</strong> AgentWorld's problem is not low tool activity; it reads more often but revisits a smaller set. ThinkingCap is closer to frontier breadth, so its remaining gap is more often the decision made from those files.</div>
</section>

<section><div class="section-head"><div><h2>What each model reads</h2><p>Counts sum unique file categories within each cell; the same filename in different tasks remains a separate observation.</p></div><div class="legend"><span class="source">source</span><span class="test">tests</span><span class="docs">docs</span><span class="config">config/build</span></div></div>
<div class="grid-2">{render_focus_panels(analysis)}</div>
<div class="callout caution"><strong>Documentation is conditional evidence, not a universal prescription.</strong> Frontier trajectories read 33 documentation files in each aligned cohort, often on public API/config tasks such as Adaptix and GoReleaser. AgentWorld read none; ThinkingCap read one. The intervention should ask for docs/schema surfaces when the task changes public behavior, not force README reading on every task.</div>
</section>

<section><div class="section-head"><div><h2>Decision timing</h2><p>Tool-event positions are comparable within exact task/rep pairs but are not wall-clock measurements.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Local subject</th><th class="num">Local first mutation</th><th class="num">Frontier first mutation</th><th class="num">Local first validation</th><th class="num">Frontier first validation</th><th class="num">Local validations</th><th class="num">Frontier validations</th><th class="num">No local validation</th><th class="num">Local changed tests</th><th class="num">Frontier changed tests</th></tr></thead><tbody>{render_timing_rows(analysis)}</tbody></table></div>
<div class="callout"><strong>ThinkingCap's counterintuitive result matters:</strong> it ran 73% more validation commands than its aligned frontier trajectories. The deficit is not “run more tests.” It needs an earlier discriminating test that can invalidate the architecture before dozens of edits make that architecture expensive to abandon.</div>
</section>

<section><div class="section-head"><div><h2>What the tool errors actually are</h2><p>This audit uses all 36 trajectories per model. A recorded tool error means the tool returned an error status; it does not automatically mean the tool API or model server malfunctioned.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Model</th><th class="num">All error results</th><th class="num">Shell command errors</th><th class="num">Edit errors</th><th class="num">Read errors</th><th class="num">Malformed edit calls</th></tr></thead><tbody>{render_tool_result_rows(analysis)}</tbody></table></div>
<div class="grid-3">
<div class="callout"><strong>GPT‑5.6 has tool errors too.</strong> It recorded 223 error results out of 2,507 (8.9%). Its shell-command error rate was actually the highest: 205/1,184. These are commonly failing tests, builds, probes, searches with no match, or an attempted git commit without configured identity.</div>
<div class="callout caution"><strong>AgentWorld has a genuine edit-call problem.</strong> All 107 malformed calls targeted <code>edit</code>: 81 put the file path inside each edit instead of at the top level, 23 sent the edits array as a JSON string, and 3 omitted the top-level path. Its edit error rate was 24.1%, versus 3.1% for GPT‑5.6.</div>
<div class="callout caution"><strong>ThinkingCap shows the same problem less often.</strong> It made 19 malformed edit calls: 10 nested the path, 6 stringified the edits array, and 3 omitted the path. Another 28 edits failed because the old text no longer matched the file—a normal stale-edit problem rather than bad tool syntax.</div>
</div>
<div class="callout good"><strong>What is and is not broken:</strong> the server successfully parsed these calls and there were no raw tool-call leaks. The malformed calls are valid JSON with the wrong <code>edit</code> schema. A conservative adapter could repair the two unambiguous shapes, but that would only save wasted turns; it would not fix the larger repository-understanding failures.</div>
</section>

<section><div class="section-head"><div><h2>What happens after negative feedback</h2><p>A deterministic detector found 1,237 bounded candidate windows across all 108 trajectories. The 72 cases used to develop or test the rubric are excluded below. Luna‑xhigh—selected only after two passing accuracy runs and a passing repeatability check—classified the remaining 1,165 unseen cases. These are flagged events, not independent task episodes.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Model</th><th class="num">Unseen candidates</th><th class="num">Flagged / 100 calls</th><th class="num">Visible negative</th><th class="num">Recovered</th><th class="num">Progressed</th><th class="num">Not recovered</th><th class="num">Relevant change</th><th class="num">Validated after change</th><th class="num">Bad tool arguments</th></tr></thead><tbody>{render_feedback_uptake_rows(feedback)}</tbody></table></div>
<div class="grid-2">
<div class="callout good"><strong>The local models usually react.</strong> Among visible negative events, {format_percent(feedback["models"]["agentworld"]["progress_or_recovery_rate"], 1)} of AgentWorld cases and {format_percent(feedback["models"]["thinkingcap"]["progress_or_recovery_rate"], 1)} of ThinkingCap cases either progressed or recovered. “The locals ignore tool feedback” is not supported.</div>
<div class="callout caution"><strong>They close fewer loops.</strong> Event-level recovery was {format_percent(feedback["models"]["frontier"]["recovery_rate"], 1)} for GPT‑5.6, {format_percent(feedback["models"]["agentworld"]["recovery_rate"], 1)} for AgentWorld, and {format_percent(feedback["models"]["thinkingcap"]["recovery_rate"], 1)} for ThinkingCap. Equal-weighted trajectory medians were {format_percent(feedback["models"]["frontier"]["trajectory_median_recovery_rate"], 1)}, {format_percent(feedback["models"]["agentworld"]["trajectory_median_recovery_rate"], 1)}, and {format_percent(feedback["models"]["thinkingcap"]["trajectory_median_recovery_rate"], 1)}.</div>
<div class="callout"><strong>ThinkingCap does test after changing code.</strong> Among events with a relevant change, post-change validation appeared in {format_percent(feedback["models"]["thinkingcap"]["post_change_validation_rate"], 1)} of ThinkingCap cases versus {format_percent(feedback["models"]["frontier"]["post_change_validation_rate"], 1)} for GPT‑5.6. AgentWorld was lower at {format_percent(feedback["models"]["agentworld"]["post_change_validation_rate"], 1)}. This reinforces the earlier result: generic “run more tests” guidance is not the main ThinkingCap intervention.</div>
<div class="callout caution"><strong>AgentWorld absorbs tool-shape mistakes, but pays for them.</strong> The unseen corpus contains {feedback["models"]["agentworld"]["schema_invalid_tool_arguments"]} AgentWorld schema-invalid calls: {feedback["models"]["agentworld"]["schema_invalid_outcome_counts"].get("recovered", 0)} recovered, {feedback["models"]["agentworld"]["schema_invalid_outcome_counts"].get("progressed", 0)} progressed, and {feedback["models"]["agentworld"]["schema_invalid_outcome_counts"].get("not_recovered", 0)} did not recover. ThinkingCap had {feedback["models"]["thinkingcap"]["schema_invalid_tool_arguments"]} such cases.</div>
</div>
<div class="callout caution"><strong>Interpretation limit:</strong> candidate windows can overlap, and models encounter different mixes of failures. The “flagged per 100 calls” column uses all detector candidates; semantic rates use only the 1,165 unseen annotations. These numbers describe feedback handling, not solve probability or a causal model comparison. <a href="feedback-uptake/analysis-v2.json">Download the feedback dataset</a>.</div>
</section>

<section><div class="section-head"><div><h2>Recurring task-analysis patterns</h2><p>These patterns combine the 47-pair aggregate with direct evidence from the nine packets below.</p></div></div>
<div class="grid-3">
<article class="pattern"><div class="number">01</div><h3>Requirements become a checklist, not a dependency model</h3><p>Local reasoning often restates every requirement accurately, then implements each near the first plausible file. Frontier trajectories trace producers, consumers, persistence, round trips, and error attribution before choosing seams.</p></article>
<article class="pattern"><div class="number">02</div><h3>Search activity substitutes for file coverage</h3><p>Both locals issue more search and discovery commands than the frontier. AgentWorld especially revisits the same source files, while frontier trajectories convert search into a broader set of exact reads across tests, config, and docs.</p></article>
<article class="pattern"><div class="number">03</div><h3>Architecture freezes before feedback</h3><p>Local validation begins 16–27 tool events later than the aligned frontier median. By then new modules, public types, and control flow already encode the initial interpretation.</p></article>
<article class="pattern"><div class="number">04</div><h3>Self-authored tests mirror the chosen design</h3><p>ThinkingCap changes tests as often as the frontier, yet misses hidden requirement families. Its tests often prove its implementation's happy path rather than challenge round trips, lifecycle isolation, persistence, or conflicting inputs.</p></article>
<article class="pattern"><div class="number">05</div><h3>Completion audits trust green visible tests</h3><p>Local final summaries repeatedly claim completion or “all tests pass” while entire prompt-derived feature families fail. The missing step is coverage evidence per requirement, not access to hidden tests.</p></article>
<article class="pattern"><div class="number">06</div><h3>Near-frontier coverage can still choose the wrong abstraction</h3><p>Claude delegation and Mobly show similar file counts across models, but local patches choose standalone or monolithic modules while the frontier integrates the existing orchestration and lifecycle owners.</p></article>
</div></section>

<section><div class="section-head"><div><h2>Where decisions begin to fail</h2><p>These are nine detailed examples chosen from the 108 trajectories: eight failing task/repetition cells spanning TypeScript, Python, and Go, plus SQL formatter rep1 as a local-success counterexample. They illustrate mechanisms; the all-repetition table above and 47-row cohort below provide the aggregate evidence.</p></div></div>
<div class="decision-grid">{render_decision_cards(analysis)}</div></section>

<section><div class="section-head"><div><h2>Task-level coverage and feature gaps</h2><p>Each side includes only exact cells where GPT-5.6 solved and that local subject did not. Frontier F2P is therefore 100% by construction.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">AW pairs</th><th class="num">AW files</th><th class="num">Frontier files</th><th class="num">AW recall</th><th class="num">AW F2P</th><th class="num">TC pairs</th><th class="num">TC files</th><th class="num">Frontier files</th><th class="num">TC recall</th><th class="num">TC F2P</th></tr></thead><tbody>{render_task_rows(analysis)}</tbody></table></div></section>

<section><div class="section-head"><div><h2>Experiments worth trying</h2><p>These are intervention hypotheses, not claims that scaffolding can erase the model-capability gap. The sixth experiment addresses malformed edit calls separately from reasoning quality.</p></div></div><div class="scaffold-list">{render_scaffold_cards(analysis)}</div>
<div class="callout caution"><strong>Benchmark integrity:</strong> every proposed A/B must use only the task prompt and normal repository surface. Frontier paths, reference patches, hidden test names, and packet classifications are analysis evidence—not inputs to the intervention.</div></section>

<section><div class="section-head"><div><h2>What not to change</h2></div></div>
<div class="grid-3">
<div class="callout bad"><strong>Do not raise output ceilings.</strong> Prior delivery analysis found no length stops and completions far below either local model's cap. The divergence occurs in task modeling and execution control.</div>
<div class="callout bad"><strong>Do not add blanket time.</strong> ThinkingCap already performs long, validation-heavy trajectories. Extend or redirect only when progress signals justify it.</div>
<div class="callout bad"><strong>Do not force indiscriminate file counts.</strong> Similar coverage still produced wrong seams on delegation and Mobly. Coverage must end in an explicit dependency and invariant model.</div>
</div></section>

<section><div class="section-head"><div><h2>All 47 frontier-solved local failures</h2><p>These rows are the aggregate cohort behind the coverage findings. GPT-5.6 passed every listed cell's feature tests.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Local subject</th><th>Task</th><th class="num">Rep</th><th>Outcome</th><th class="num">Local F2P</th><th class="num">Partial</th><th class="num">Local files</th><th class="num">Frontier files</th><th class="num">Recall</th><th class="num">Local pre-mutation</th><th class="num">Frontier pre-mutation</th><th class="num">Frontier F2P</th></tr></thead><tbody>{render_gap_pair_rows(analysis)}</tbody></table></div></section>

<section><div class="section-head"><div><h2>Provenance and limits</h2></div></div>
<div class="callout"><strong>Reference role:</strong> GPT-5.6 SOL high is a capability reference, not an expected peer. The stock-Pi 36_v2 run supplies all 36 matching trajectories and solves 24. Both local subjects supply all 36 trajectories.</div>
<div class="callout caution"><strong>Artifact compatibility:</strong> user prompts match exactly and every completed verifier surface has matching F2P/P2P denominators. The frontier run predates embedded harness, task, verifier, and Pi-version identities, so compatibility is evidenced but not cryptographically sealed. System-prompt differences are limited to later Pi environment-variable documentation.</div>
<div class="callout"><strong>Measurement limit:</strong> file coverage records successful exact content targets. It cannot prove comprehension, and shell parsing can undercount dynamic paths. Decision classifications combine those metrics with patches, validation commands, final summaries, and verifier failures.</div>
<div class="callout"><strong>Feedback-label calibration:</strong> the first clarified rubric round remained blocked. One predeclared repair round then used new worked examples and a fresh held-out sample that excluded every earlier test case. Luna‑xhigh passed at 15/24 and 14/24 exact units, with 18/24 repeatability; GLM‑5.2 max did not pass. All 72 development or held-out cases across the three calibration sets are excluded from the 1,165-event semantic analysis.</div></section>

<div class="foot">Derived from canonical result artifacts, Pi session JSONL, model patches, initial-context captures, task metadata, and CTRF verifier output. <a href="analysis.json">Download the analysis dataset</a>. Packet links provide per-cell evidence.</div>
</div></body></html>"""


def main() -> None:
    """Write the deterministic HTML report."""
    output_path = REPORT_ROOT / "index.html"
    output_path.write_text(build_report())
    print(output_path)


if __name__ == "__main__":
    main()
