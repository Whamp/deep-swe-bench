#!/usr/bin/env python3
"""Render the DeepSWE agentic inference profile as Markdown and self-contained HTML."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "profile.json"


def number(value: float) -> str:
    """Format a count without implying more than whole-token precision."""
    return f"{value:,.0f}"


def pct(value: float) -> str:
    """Format a fraction as a one-decimal percentage."""
    return f"{value:.1%}"


def rounded(value: float, quantum: int) -> int:
    """Round a measured token count to a practical benchmark quantum."""
    return max(quantum, round(value / quantum) * quantum)


def trajectory_recipe(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a balanced 41-request recipe from normalized trajectory stages."""
    recipe = [
        {
            "label": "Cold start",
            "requests": 1,
            "depth": 0,
            "pp": 2048,
            "tg": 64,
            "basis": "first-turn medians",
        }
    ]
    for stage in profile["trajectory_progression"]["normalized_stages"]:
        recipe.append(
            {
                "label": f"Stage {stage['stage']} · {stage['trajectory_fraction']}",
                "requests": 8,
                "depth": rounded(stage["cache_friendly_depth"]["mean"], 256),
                "pp": rounded(stage["cache_friendly_pp"]["mean"], 256),
                "tg": rounded(stage["output"]["mean"], 32),
                "basis": "mean of per-trajectory stage medians",
            }
        )
    return recipe


def render_markdown(profile: dict[str, Any], recipe: list[dict[str, Any]]) -> str:
    """Render the evidence and recommendation in a plain-text review format."""
    corpus = profile["corpus"]
    requests = profile["request_weighted"]["all"]
    trajectories = profile["trajectory_weighted"]
    progression = profile["trajectory_progression"]
    lines = [
        "# DeepSWE agentic inference workload profile",
        "",
        "## Verdict",
        "",
        "A single average request is not a faithful coding-agent benchmark. The corpus starts near 2k prompt tokens, reaches a median 45k context by turn 40, and ends at a median 41k context. The recommended benchmark is therefore a 41-request progression: one cold request, then eight requests in each of five normalized conversation stages.",
        "",
        "## Denominator and method",
        "",
        f"- {corpus['trajectories_with_sessions']:,} canonical root trajectories across {corpus['unique_tasks']} tasks",
        f"- {corpus['assistant_requests']:,} nonzero assistant requests",
        f"- {corpus['cache_reported_trajectories']:,} trajectories with direct cache usage; {corpus['cache_estimated_trajectories']:,} with cache-friendly shape estimated from context growth",
        f"- {corpus['missing_root_sessions']} result cells lacked a root session and were excluded",
        "- Excluded every underscore-prefixed result tree, including `_contaminated/` and `_archives/`",
        "- Mapping: `depth = cacheRead`, `pp = input + cacheWrite`, `context = depth + pp`, `tg = output`",
        "",
        "## Request-weighted distribution",
        "",
        "| Metric | Mean | Mean below p99 | p25 | p50 | p75 | p90 | p99 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, label in (
        ("cache_friendly_depth", "Cached depth"),
        ("cache_friendly_pp", "New prompt / pp"),
        ("output", "Generated / tg"),
        ("context", "Total input context"),
    ):
        row = requests[key]
        lines.append(
            f"| {label} | {number(row['mean'])} | {number(row['mean_below_p99'])} | {number(row['p25'])} | {number(row['p50'])} | {number(row['p75'])} | {number(row['p90'])} | {number(row['p99'])} |"
        )
    lines.extend(
        [
            "",
            f"The median trajectory has {number(trajectories['turns']['p50'])} requests, reaches {number(trajectories['max_context']['p50'])} tokens, and generates {number(trajectories['total_output']['p50'])} tokens in total. Context shrank on {progression['context_shrink_transitions']:,} of {progression['total_follow_up_transitions']:,} follow-up transitions ({pct(progression['context_shrink_transitions'] / progression['total_follow_up_transitions'])}), usually because of compaction or reset.",
            "",
            "## Recommended 41-request trajectory",
            "",
            "Run each row separately; llama-benchy takes a Cartesian product when several values are passed together.",
            "",
            "| Phase | Repetitions | `--depth` | `--pp` | `--tg` |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in recipe:
        lines.append(
            f"| {row['label']} | {row['requests']} | {row['depth']:,} | {row['pp']:,} | {row['tg']:,} |"
        )
    lines.extend(
        [
            "",
            "Use `--enable-prefix-caching` for the five staged rows. The cold row uses depth 0. These generated-token counts represent balanced per-trajectory stage averages, not fixed completion caps observed in production; `--exact-tg` is appropriate only when you intentionally want fixed-length throughput comparability.",
            "",
            "## Absolute progression",
            "",
            "| Turn | Trajectories reaching turn | Median context | Median depth | Median pp | Median tg |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in progression["absolute_turn_checkpoints"]:
        lines.append(
            f"| {row['turn']} | {row['trajectories']:,} ({pct(row['trajectory_share'])}) | {number(row['context']['p50'])} | {number(row['cache_friendly_depth']['p50'])} | {number(row['cache_friendly_pp']['p50'])} | {number(row['output']['p50'])} |"
        )
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- This is the empirical result corpus, not a balanced sample of configs or models. GPT-5.5 contributes 4,831 of 9,236 trajectories.",
            "- Request weighting describes serving demand but overweights long trajectories. The normalized recipe first gives every trajectory equal weight within each stage.",
            "- Cache shape is derived for APIs that report no cache tokens. Context totals and output tokens remain provider-reported; only the depth/pp split is estimated.",
            "- A static llama-benchy request measures a slice of the trajectory. It does not reproduce persistent KV residency, compaction, scheduler contention, or tool latency across a live 41-turn session.",
            "",
            "## Reproduction",
            "",
            "```bash",
            "python3 analysis/agentic-inference-profile/build_profile.py",
            "python3 analysis/agentic-inference-profile/render_report.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def table_rows(rows: list[str]) -> str:
    """Join already escaped HTML table rows."""
    return "\n".join(rows)


def render_html(profile: dict[str, Any], recipe: list[dict[str, Any]]) -> str:
    """Render a self-contained report matching the project report design system."""
    corpus = profile["corpus"]
    request = profile["request_weighted"]["all"]
    trajectory = profile["trajectory_weighted"]
    progression = profile["trajectory_progression"]
    request_rows = []
    for key, label in (
        ("cache_friendly_depth", "Cached depth"),
        ("cache_friendly_pp", "New prompt / pp"),
        ("output", "Generated / tg"),
        ("context", "Total context"),
    ):
        row = request[key]
        request_rows.append(
            f"<tr><td><strong>{html.escape(label)}</strong></td><td class='num'>{number(row['mean'])}</td><td class='num'>{number(row['mean_below_p99'])}</td><td class='num'>{number(row['p25'])}</td><td class='num'>{number(row['p50'])}</td><td class='num'>{number(row['p75'])}</td><td class='num'>{number(row['p90'])}</td><td class='num'>{number(row['p99'])}</td></tr>"
        )
    recipe_rows = [
        f"<tr><td><strong>{html.escape(row['label'])}</strong></td><td class='num'>{row['requests']}</td><td class='num'>{row['depth']:,}</td><td class='num'>{row['pp']:,}</td><td class='num'>{row['tg']:,}</td><td><span class='tag {'neutral' if row['depth'] == 0 else 'good'}'>{'cold' if row['depth'] == 0 else 'cached'}</span></td></tr>"
        for row in recipe
    ]
    checkpoint_rows = [
        f"<tr><td><strong>{row['turn']}</strong></td><td class='num'>{row['trajectories']:,} <span class='muted'>({pct(row['trajectory_share'])})</span></td><td class='num'>{number(row['context']['p50'])}</td><td class='num'>{number(row['cache_friendly_depth']['p50'])}</td><td class='num'>{number(row['cache_friendly_pp']['p50'])}</td><td class='num'>{number(row['output']['p50'])}</td></tr>"
        for row in progression["absolute_turn_checkpoints"]
    ]
    band_rows = [
        f"<tr><td><strong>{html.escape(row['label'].replace('-plus', '+').replace('-', '–'))}</strong></td><td class='num'>{pct(row['share'])}</td><td class='num'>{number(row['context']['p50'])}</td><td class='num'>{number(row['cache_friendly_depth']['p50'])}</td><td class='num'>{number(row['cache_friendly_pp']['p50'])}</td><td class='num'>{number(row['output']['p50'])}</td></tr>"
        for row in profile["context_bands"]
    ]
    shrink_share = (
        progression["context_shrink_transitions"]
        / progression["total_follow_up_transitions"]
    )
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><link rel='icon' href='data:,'>
<title>DeepSWE agentic inference workload</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--shadow:0 20px 55px rgba(14,30,62,.08)}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),linear-gradient(#f9fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.55}}.wrap{{max-width:1180px;margin:auto;padding:28px 20px 48px}}.hero,section{{background:rgba(255,255,255,.93);border:1px solid var(--line);border-radius:26px;box-shadow:var(--shadow)}}.hero{{padding:38px}}.eyebrow{{display:inline-block;padding:7px 11px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}}h1,h2{{line-height:1.08;letter-spacing:-.03em}}h1{{font-size:clamp(2rem,5vw,3.8rem);max-width:17ch;margin:14px 0}}h2{{margin:0;font-size:clamp(1.4rem,3vw,2rem)}}p{{color:var(--muted)}}.pillrow{{display:flex;gap:9px;flex-wrap:wrap}}.pill,.tag{{display:inline-flex;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}}.pill.good,.tag.good{{background:#e7f7ef;color:var(--green)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.pill.caution{{background:#fff4d8;color:var(--amber)}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin-top:24px}}.stat{{border:1px solid var(--line);border-radius:18px;padding:16px;background:#fff}}.label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}}.value{{display:block;font-size:1.8rem;font-weight:900;margin-top:6px}}section{{padding:26px;margin-top:20px}}.section-head{{margin-bottom:16px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px 11px;border-bottom:1px solid var(--line);text-align:left}}th{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}.num{{text-align:right;font-variant-numeric:tabular-nums}}.muted{{color:var(--muted)}}code{{background:#eef2ff;padding:.12em .35em;border-radius:6px}}.callout{{border-left:5px solid var(--blue);background:#f5f7ff;padding:14px 16px;border-radius:13px;margin-top:15px}}.callout.good{{border-left-color:var(--green);background:#f2fbf6}}.callout.caution{{border-left-color:var(--amber);background:#fffbef}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}.foot{{color:var(--muted);text-align:center;font-size:.86rem;margin-top:24px}}@media(max-width:820px){{.stats,.grid{{grid-template-columns:1fr 1fr}}section{{overflow-x:auto}}table{{min-width:680px}}}}@media(max-width:560px){{.stats,.grid{{grid-template-columns:1fr}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>DeepSWE · local inference workload</span><h1>Benchmark the conversation, not one average request</h1><p>The typical coding-agent session starts around 2k tokens, grows through dozens of cached follow-ups, and ends near 41k context. One static depth hides the workload. Use a 41-request progression.</p><div class='pillrow'><span class='pill good'>9,236 trajectories</span><span class='pill neutral'>481,152 requests</span><span class='pill caution'>113 tasks · config-heavy corpus</span></div><div class='stats'><div class='stat'><span class='label'>Median trajectory</span><span class='value'>{number(trajectory["turns"]["p50"])} turns</span></div><div class='stat'><span class='label'>Median max context</span><span class='value'>{number(trajectory["max_context"]["p50"])}</span></div><div class='stat'><span class='label'>Median total output</span><span class='value'>{number(trajectory["total_output"]["p50"])}</span></div><div class='stat'><span class='label'>Context shrink transitions</span><span class='value'>{pct(shrink_share)}</span></div></div></header>
<section><div class='section-head'><h2>Recommended typical trajectory</h2><p>One cold request plus eight requests from each normalized conversation stage gives 41 requests, matching the corpus median. Values are rounded from balanced stage averages.</p></div><table><thead><tr><th>Phase</th><th class='num'>Requests</th><th class='num'>Depth</th><th class='num'>PP</th><th class='num'>TG</th><th>Mode</th></tr></thead><tbody>{table_rows(recipe_rows)}</tbody></table><div class='callout good'><strong>Run rows separately.</strong> llama-benchy forms a Cartesian product when multiple depth, pp, and tg values are supplied together. Enable prefix caching for staged rows; use depth 0 for cold start.</div></section>
<section><div class='section-head'><h2>What “average” means here</h2><p>Request weighting models server demand and therefore overweights long trajectories. The below-p99 mean is a safer single-number capacity estimate; medians describe ordinary latency.</p></div><table><thead><tr><th>Metric</th><th class='num'>Mean</th><th class='num'>Mean below p99</th><th class='num'>p25</th><th class='num'>p50</th><th class='num'>p75</th><th class='num'>p90</th><th class='num'>p99</th></tr></thead><tbody>{table_rows(request_rows)}</tbody></table><div class='callout caution'><strong>If you insist on one request:</strong> use approximately <code>--depth 46080 --pp 3072 --tg 320</code> for mean load, or <code>--depth 32768 --pp 1024 --tg 128</code> for median-like latency. Neither reproduces depth growth.</div></section>
<div class='grid'><section><div class='section-head'><h2>Absolute turn progression</h2><p>Late checkpoints include only trajectories that reached that turn; the survivor share stays visible.</p></div><table><thead><tr><th>Turn</th><th class='num'>Trajectories</th><th class='num'>Context</th><th class='num'>Depth</th><th class='num'>PP</th><th class='num'>TG</th></tr></thead><tbody>{table_rows(checkpoint_rows)}</tbody></table></section><section><div class='section-head'><h2>Serving-demand context mix</h2><p>Request-weighted bands are useful for sweep weighting and KV-capacity planning.</p></div><table><thead><tr><th>Context band</th><th class='num'>Share</th><th class='num'>Context</th><th class='num'>Depth</th><th class='num'>PP</th><th class='num'>TG</th></tr></thead><tbody>{table_rows(band_rows)}</tbody></table></section></div>
<section><div class='section-head'><h2>Method and limits</h2></div><div class='callout'><strong>Direct mapping:</strong> depth = <code>cacheRead</code>; pp = <code>input + cacheWrite</code>; tg = <code>output</code>. {corpus["cache_reported_trajectories"]:,} trajectories report cache usage directly. For {corpus["cache_estimated_trajectories"]:,} traces without cache metadata, the extractor derives reusable depth from sequential context growth and treats context shrink as a cold prefill.</div><div class='callout caution'><strong>Corpus bias:</strong> these are all canonical available trajectories, not a model/config-balanced sample. GPT-5.5 alone contributes 4,831 of 9,236 trajectories. Underscore trees—including contaminated and archive copies—are excluded.</div><div class='callout'><strong>Remaining fidelity gap:</strong> static llama-benchy calls sample trajectory slices. They do not reproduce persistent KV residency, compaction behavior, tool latency, or scheduler contention across a live multi-turn agent session.</div></section>
<div class='foot'><code>analysis/agentic-inference-profile/profile.json</code> · generated by <code>build_profile.py</code> and <code>render_report.py</code></div></div></body></html>"""


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    recipe = trajectory_recipe(profile)
    (ROOT / "report.md").write_text(render_markdown(profile, recipe), encoding="utf-8")
    (ROOT / "index.html").write_text(render_html(profile, recipe), encoding="utf-8")
    print(f"wrote {ROOT / 'report.md'}")
    print(f"wrote {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
