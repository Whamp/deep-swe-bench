"""Render the self-contained GPT-5.6 Luna all-thinking comparison report."""

from __future__ import annotations

import html
from datetime import UTC, datetime
from typing import Any

LEFT_CONFIG = "baseline@1.0.0"
RIGHT_CONFIG = "pi-check@1.0.1"
LEVELS = ("low", "high", "max")


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def percentage_points(value: float) -> str:
    return f"{value * 100:+.1f} pp"


def ratio_change(right: float, left: float) -> float:
    return right / left - 1 if left else 0.0


def verdict_class(delta: float, *, higher_is_better: bool = True) -> str:
    if delta == 0:
        return "neutral"
    favorable = delta > 0 if higher_is_better else delta < 0
    return "good" if favorable else "bad"


def render_level_metric_rows(level_summary: dict[str, Any]) -> str:
    left = level_summary["configs"][LEFT_CONFIG]
    right = level_summary["configs"][RIGHT_CONFIG]
    rows = [
        (
            "Binary solves",
            f"{left['solves']}/36 · {percent(left['solves'] / 36)}",
            f"{right['solves']}/36 · {percent(right['solves'] / 36)}",
            percentage_points(level_summary["solve_rate_delta"]),
            verdict_class(level_summary["solve_delta"]),
        ),
        (
            "Mean partial reward",
            percent(left["partial_mean"]),
            percent(right["partial_mean"]),
            percentage_points(right["partial_mean"] - left["partial_mean"]),
            verdict_class(right["partial_mean"] - left["partial_mean"]),
        ),
        (
            "F2P passed / total",
            f"{left['f2p_passed']:,}/{left['f2p_total']:,}",
            f"{right['f2p_passed']:,}/{right['f2p_total']:,}",
            "different denominators"
            if left["f2p_total"] != right["f2p_total"]
            else f"{right['f2p_passed'] - left['f2p_passed']:+,}",
            "caution" if left["f2p_total"] != right["f2p_total"] else "neutral",
        ),
        (
            "P2P passed / total",
            f"{left['p2p_passed']:,}/{left['p2p_total']:,}",
            f"{right['p2p_passed']:,}/{right['p2p_total']:,}",
            "different denominators"
            if left["p2p_total"] != right["p2p_total"]
            else f"{right['p2p_passed'] - left['p2p_passed']:+,}",
            "caution" if left["p2p_total"] != right["p2p_total"] else "neutral",
        ),
        (
            "Total tokens",
            f"{left['tokens_total'] / 1e6:.1f}M",
            f"{right['tokens_total'] / 1e6:.1f}M",
            f"{ratio_change(right['tokens_total'], left['tokens_total']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Total recorded cost",
            f"${left['cost_total']:.2f}",
            f"${right['cost_total']:.2f}",
            f"{ratio_change(right['cost_total'], left['cost_total']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Mean wall time",
            f"{left['wall_mean']:.1f}s",
            f"{right['wall_mean']:.1f}s",
            f"{ratio_change(right['wall_mean'], left['wall_mean']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Mean turns / tool calls",
            f"{left['turns_mean']:.1f} / {left['tool_calls_mean']:.1f}",
            f"{right['turns_mean']:.1f} / {right['tool_calls_mean']:.1f}",
            f"turns {ratio_change(right['turns_mean'], left['turns_mean']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Verifier timeouts / negative rewards",
            f"{left['verifier_timeouts']} / {left['negative_rewards']}",
            f"{right['verifier_timeouts']} / {right['negative_rewards']}",
            "risk" if right["negative_rewards"] > left["negative_rewards"] else "none",
            "bad"
            if right["negative_rewards"] > left["negative_rewards"]
            else "neutral",
        ),
    ]
    return "".join(
        f'<tr><td>{html.escape(name)}</td><td class="num">{left_value}</td>'
        f'<td class="num">{right_value}</td><td class="num"><span class="tag {tag}">{delta}</span></td></tr>'
        for name, left_value, right_value, delta, tag in rows
    )


def render_agreement_cards(level_summary: dict[str, Any]) -> str:
    agreement = level_summary["agreement"]
    return f"""
<div class="grid4">
  <div class="mini"><strong>{agreement["both"]}</strong><span>both solved</span></div>
  <div class="mini"><strong>{agreement["baseline_only"]}</strong><span>baseline only</span></div>
  <div class="mini"><strong>{agreement["pi_check_only"]}</strong><span>pi-check only</span></div>
  <div class="mini"><strong>{agreement["neither"]}</strong><span>neither solved</span></div>
</div>"""


def render_flip_rows(
    level: str, level_summary: dict[str, Any], packet_index: list[dict[str, Any]]
) -> str:
    packet_lookup = {
        (packet["level"], packet["task"], packet["rep"]): packet
        for packet in packet_index
    }
    rows: list[str] = []
    for flip in level_summary["flips"]:
        packet = packet_lookup[(level, flip["task"], flip["rep"])]
        classification = packet["classification"]
        tag = "good" if flip["direction"] == "pi-check-only" else "bad"
        rows.append(
            f"<tr><td><strong>{html.escape(flip['task'])}</strong></td>"
            f'<td class="num">{flip["rep"]}</td>'
            f'<td><span class="tag {tag}">{html.escape(flip["direction"])}</span></td>'
            f'<td class="num">{flip["left_partial"]:.3f}</td>'
            f'<td class="num">{flip["right_partial"]:.3f}</td>'
            f"<td>{html.escape(classification['primary_bucket'])}</td>"
            f"<td>{html.escape(classification['mechanism'])}</td>"
            f'<td><a href="{html.escape(packet["markdown"])}">packet</a></td></tr>'
        )
    return "".join(rows)


def render_task_matrix(summary: dict[str, Any]) -> str:
    task_rows_by_level = {
        level: {row["task"]: row for row in summary["levels"][level]["task_rows"]}
        for level in LEVELS
    }
    tasks = [row["task"] for row in summary["levels"]["low"]["task_rows"]]
    tasks.sort()
    rows: list[str] = []
    for task in tasks:
        low = task_rows_by_level["low"][task]
        cells = []
        for level in LEVELS:
            row = task_rows_by_level[level][task]
            delta = row["delta"]
            tag = verdict_class(delta)
            cells.append(
                f'<td class="num">{row["left_solves"]} → {row["right_solves"]} '
                f'<span class="tag {tag}">{delta:+d}</span></td>'
            )
        rows.append(
            f"<tr><td><strong>{html.escape(task)}</strong><br>"
            f'<span class="muted">{html.escape(low["title"])} · {html.escape(low["language"])}</span></td>'
            + "".join(cells)
            + "</tr>"
        )
    return "".join(rows)


def render_thinking_transition_rows(summary: dict[str, Any]) -> str:
    rows: list[str] = []
    for config in (LEFT_CONFIG, RIGHT_CONFIG):
        for transition_name in ("low_to_high", "high_to_max"):
            transition = summary["thinking_transitions"][config][transition_name]
            from_level = transition["from_level"]
            to_level = transition["to_level"]
            from_metrics = summary["levels"][from_level]["configs"][config]
            to_metrics = summary["levels"][to_level]["configs"][config]
            incremental_cost = to_metrics["cost_total"] - from_metrics["cost_total"]
            incremental_tokens = (
                to_metrics["tokens_total"] - from_metrics["tokens_total"]
            )
            solve_delta = transition["solve_delta"]
            cost_per_incremental_solve = (
                f"${incremental_cost / solve_delta:.2f}" if solve_delta > 0 else "n/a"
            )
            ci = transition["task_cluster_bootstrap_ci"]
            rows.append(
                f"<tr><td>{html.escape(config)}</td><td>{from_level} → {to_level}</td>"
                f'<td class="num">{transition["from_solves"]} → {transition["to_solves"]} '
                f'<span class="tag good">{solve_delta:+d}</span></td>'
                f'<td class="num">{transition["agreement"]["discordant"]}</td>'
                f'<td class="num">{transition["mcnemar_p"]:.4f}</td>'
                f'<td class="num">{percentage_points(ci[0])} to {percentage_points(ci[1])}</td>'
                f'<td class="num">{incremental_tokens / 1e6:+.1f}M</td>'
                f'<td class="num">${incremental_cost:+.2f}</td>'
                f'<td class="num">{cost_per_incremental_solve}</td></tr>'
            )
    return "".join(rows)


def render_level_section(
    level: str, summary: dict[str, Any], packet_index: list[dict[str, Any]]
) -> str:
    level_summary = summary["levels"][level]
    agreement = level_summary["agreement"]
    ci = level_summary["task_cluster_bootstrap_ci"]
    level_labels = {"low": "Low", "high": "High", "max": "Max"}
    observations = {
        "low": (
            "Partial credit improves, but binary performance falls and pi-check introduces the only two negative rewards in the comparison. "
            "Removing the one verifier-timeout pair produces a 1–1 solve tie, not a win."
        ),
        "high": (
            "This is the only level with a positive net solve delta, but 14 discordant pairs produce eight gains and six losses. "
            "Two flips had no post-check edit, so they cannot be attributed to follow-up mutation."
        ),
        "max": (
            "The solve count is an exact tie. Three wins and three losses cancel, while pi-check lowers mean partial reward and raises every resource measure. "
            "Recursive delegation alone contributes one gain and two losses."
        ),
    }
    return f"""
<section id="{level}"><h2>{level_labels[level]} thinking</h2>
<p class="section-lede">36 matched pairs · solve delta {level_summary["solve_delta"]:+d} · exact McNemar p={level_summary["mcnemar_p"]:.3f} · task-cluster 95% CI {percentage_points(ci[0])} to {percentage_points(ci[1])}.</p>
<div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{render_level_metric_rows(level_summary)}</tbody></table></div>
<h3>Solve agreement</h3>{render_agreement_cards(level_summary)}
<div class="callout {"badline" if level == "low" else "warn"}"><strong>Read:</strong> {observations[level]}</div>
<details open><summary>{agreement["discordant"]} solve flips</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Direction</th><th class="num">Base partial</th><th class="num">Check partial</th><th>Driver</th><th>Evidence</th><th></th></tr></thead><tbody>{render_flip_rows(level, level_summary, packet_index)}</tbody></table></div></details>
</section>"""


def render_all_thinking_report(
    summary: dict[str, Any], packet_index: list[dict[str, Any]]
) -> str:
    all_levels = summary["all_levels"]
    pooled_left = all_levels["configs"][LEFT_CONFIG]
    pooled_right = all_levels["configs"][RIGHT_CONFIG]
    pooled_ci = all_levels["task_cluster_bootstrap_ci"]
    high = summary["levels"]["high"]
    max_level = summary["levels"]["max"]
    max_left = max_level["configs"][LEFT_CONFIG]
    max_right = max_level["configs"][RIGHT_CONFIG]
    packet_counts = {
        level: sum(packet["level"] == level for packet in packet_index)
        for level in LEVELS
    }
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    style = """
:root{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#c58a00;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--max:1260px}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff,var(--bg));color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}.wrap{max-width:var(--max);margin:auto;padding:28px 20px 56px}.hero,section{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}.hero{padding:clamp(26px,4vw,44px)}.eyebrow{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1,h2,h3{line-height:1.08;letter-spacing:-.035em}h1{font-size:clamp(2.4rem,5vw,4.8rem);max-width:14ch;margin:14px 0}h2{font-size:1.85rem;margin:0 0 6px}h3{margin-top:24px}.lede,.section-lede{max-width:82ch;color:var(--muted)}.pills{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}.pill,.tag{display:inline-flex;padding:6px 10px;border-radius:999px;font-weight:800;font-size:12px}.pill{padding:8px 12px;text-transform:uppercase;letter-spacing:.04em}.good{background:var(--green-soft);color:var(--green)}.bad{background:var(--red-soft);color:var(--red)}.caution{background:var(--amber-soft);color:#8a6100}.neutral{background:#eef3ff;color:var(--blue-2)}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:13px;margin-top:22px}.stat{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:17px}.stat strong{display:block;font-size:1.65rem;letter-spacing:-.04em}.stat span{display:block;color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase}section{margin-top:20px;padding:clamp(20px,3vw,30px)}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.mini{border:1px solid var(--line);border-radius:17px;padding:16px;text-align:center}.mini strong{display:block;font-size:2rem}.mini span{font-size:11px;text-transform:uppercase;color:var(--muted);font-weight:800}.callout{border-left:5px solid var(--blue);background:#f5f7ff;padding:15px 17px;border-radius:13px;margin-top:15px}.callout.goodline{border-color:var(--green);background:var(--green-soft)}.callout.badline{border-color:var(--red);background:var(--red-soft)}.callout.warn{border-color:var(--amber);background:var(--amber-soft)}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.table-wrap{overflow:auto}.muted{color:var(--muted)}code{background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:5px}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}details{border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin-top:12px}summary{cursor:pointer;font-weight:800}footer{text-align:center;color:var(--muted);padding:26px;font-size:13px}@media(max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}.grid2,.grid3{grid-template-columns:1fr}.grid4{grid-template-columns:repeat(2,1fr)}}@media(max-width:540px){.stats,.grid4{grid-template-columns:1fr}.hero,section{padding:20px}}
"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>GPT-5.6 Luna · all thinking levels · pi-check</title><style>{style}</style></head>
<body><div class="wrap">
<header class="hero"><span class="eyebrow">DeepSWE · GPT-5.6 Luna · low / high / max · 12_v2 · 3 reps</span>
<h1>Thinking wins. pi-check mostly churns.</h1>
<p class="lede">Across 108 matched task/rep/level pairs, pi-check moves from {pooled_left["solves"]} to {pooled_right["solves"]} solves—one net solve—while using 37% more tokens and costing 32% more. Low loses one solve, high gains two, and max ties. The stronger and more consistent intervention is reasoning effort: both configs improve sharply from low to high and again from high to max.</p>
<div class="pills"><span class="pill neutral">Pooled: +1 / 108</span><span class="pill bad">Tokens: +37%</span><span class="pill bad">Cost: +32%</span><span class="pill caution">23 pooled solve flips</span><span class="pill good">Delivery: 108 / 108</span></div>
<div class="stats"><div class="stat"><strong>{pooled_left["solves"]} → {pooled_right["solves"]}</strong><span>All-level solves · 108</span></div><div class="stat"><strong>2 → 1</strong><span>Low solves</span></div><div class="stat"><strong>18 → 20</strong><span>High solves</span></div><div class="stat"><strong>25 → 25</strong><span>Max solves</span></div><div class="stat"><strong>{len(packet_index)}</strong><span>Evidence packets</span></div></div></header>

<section><h2>Executive verdict</h2><div class="grid3">
<div class="callout badline"><strong>Low: reject.</strong> −1 solve, +97% tokens, +91% cost, and the only two negative outcomes.</div>
<div class="callout warn"><strong>High: promising but unproven.</strong> +2 solves, but 14 flips, McNemar p={high["mcnemar_p"]:.3f}, and +37% cost.</div>
<div class="callout badline"><strong>Max: no benefit.</strong> 25–25 tie, lower pi-check partial reward, +34% tokens, and +27% cost.</div>
</div><div class="callout"><strong>Recommendation:</strong> use high as Luna’s efficiency knee when cost matters; use max only when the additional five-to-seven observed solves justify roughly triple high-level token use. Do not add pi-check based on this subset: its pooled +1 solve is overwhelmed by cost and bidirectional churn.</div></section>

<section><h2>All-level pi-check effect</h2><p class="section-lede">Descriptive pool of 108 within-level matched pairs. It is not a substitute for the per-level estimates; repeated tasks are handled with a task-cluster bootstrap.</p>
<div class="grid4"><div class="mini"><strong>{all_levels["agreement"]["both"]}</strong><span>both solved</span></div><div class="mini"><strong>{all_levels["agreement"]["baseline_only"]}</strong><span>baseline only</span></div><div class="mini"><strong>{all_levels["agreement"]["pi_check_only"]}</strong><span>pi-check only</span></div><div class="mini"><strong>{all_levels["agreement"]["neither"]}</strong><span>neither solved</span></div></div>
<div class="callout warn"><strong>No reliable aggregate lift.</strong> Solve rate moves {percent(pooled_left["solves"] / 108)} → {percent(pooled_right["solves"] / 108)} ({percentage_points(all_levels["solve_rate_delta"])}); exact McNemar p={all_levels["mcnemar_p"]:.3f}; task-cluster 95% CI {percentage_points(pooled_ci[0])} to {percentage_points(pooled_ci[1])}. Tokens move {pooled_left["tokens_total"] / 1e6:.1f}M → {pooled_right["tokens_total"] / 1e6:.1f}M and recorded cost ${pooled_left["cost_total"]:.2f} → ${pooled_right["cost_total"]:.2f}.</div></section>

<section><h2>The thinking ladder</h2><p class="section-lede">Same 12 tasks and reps, paired within each config. Incremental cost per solve is descriptive, not a claim that thinking alone caused each flip.</p>
<div class="table-wrap"><table><thead><tr><th>Config</th><th>Step</th><th class="num">Solves</th><th class="num">Discordant</th><th class="num">McNemar p</th><th class="num">Task-cluster 95% CI</th><th class="num">Δ tokens</th><th class="num">Δ cost</th><th class="num">Δ cost / added solve</th></tr></thead><tbody>{render_thinking_transition_rows(summary)}</tbody></table></div>
<div class="callout goodline"><strong>Reasoning effort dominates.</strong> Baseline climbs 2 → 18 → 25 solves; pi-check climbs 1 → 20 → 25. The high-to-max step adds seven baseline solves and five pi-check solves, but costs another ${max_left["cost_total"] - high["configs"][LEFT_CONFIG]["cost_total"]:.2f} and ${max_right["cost_total"] - high["configs"][RIGHT_CONFIG]["cost_total"]:.2f}, respectively.</div></section>

{render_level_section("low", summary, packet_index)}
{render_level_section("high", summary, packet_index)}
{render_level_section("max", summary, packet_index)}

<section><h2>Task matrix</h2><p class="section-lede">Each cell shows baseline solves → pi-check solves across three reps, followed by the pi-check delta.</p><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Low</th><th class="num">High</th><th class="num">Max</th></tr></thead><tbody>{render_task_matrix(summary)}</tbody></table></div></section>

<section><h2>Mechanisms across 33 evidence packets</h2><div class="grid2"><div class="callout goodline"><strong>Where follow-up helped:</strong> retry and Retry-After coverage, recursive-delegation branches, alias collision and missing-field behavior, stack-processing order, grammar analysis, barrier preservation, and closure import retention.</div><div class="callout badline"><strong>Where follow-up hurt:</strong> recursive delegation remains the largest unstable seam; additional losses came from VCALENDAR scope, request-coalescing call counts, exact link formatting, stack option preservation, and one low-level verifier timeout.</div></div><p class="muted">Packet triggers: {packet_counts["low"]} low, {packet_counts["high"]} high, {packet_counts["max"]} max. Trigger rule is binary/negative/timeout discordance or an absolute partial, F2P, or P2P delta of at least 0.25. Every flip links to its Markdown and JSON packet.</p></section>

<section><h2>Delivery, integrity, and provenance</h2><div class="grid2"><div class="callout goodline"><strong>Delivery passed.</strong> Baseline has zero check prompts in 108/108 sessions; pi-check has exactly one <code>Re-audit</code> prompt in 108/108. All 432 captured provider requests match <code>gpt-5.6-luna</code> and their requested thinking level.</div><div class="callout"><strong>Controlled surface.</strong> Every result uses Pi 0.83.0 and Codex OAuth. The config difference is the vendored pi-check extension plus <code>--check</code>; no config-authored preamble or orchestration prompt was added.</div></div>
<div class="callout warn"><strong>Recovery provenance is explicit.</strong> Low uses one original plan identity. High contains 56 original-plan results plus 16 compatible auth-recovery results. The initial max plan failed preflight with zero usage and contributed no final result; all 72 canonical max results come from the successful recovery plan <code>sha256:38bc68…</code>. Quarantined results are excluded.</div></section>

<section><h2>Conclusion</h2><div class="callout badline"><strong>pi-check does not earn a Luna recommendation.</strong> Its level-specific effects are −1, +2, and 0 solves; pooled, that is +1/108 with 23 bidirectional flips, p={all_levels["mcnemar_p"]:.3f}, +37% tokens, and +32% recorded cost.</div><div class="callout goodline"><strong>Thinking level does earn a recommendation.</strong> High is the practical efficiency knee in this subset. Max achieves the highest observed solve count, but its incremental gains are expensive and should be reserved for quality-first workloads.</div><div class="callout"><strong>Best next experiment:</strong> test a non-mutating or preservation-gated check at high thinking on a wider subset. The current follow-up finds real last-mile defects, but its broad edit latitude creates enough counter-regressions to erase most of the benefit.</div></section>

<footer>Generated {generated} from 216 canonical result files · <a href="summary.json">summary JSON</a> · <a href="packets/packet_index.json">33 trajectory packets</a> · GPT-5.6 Luna · 12_v2 · reps 0–2</footer>
</div></body></html>"""
