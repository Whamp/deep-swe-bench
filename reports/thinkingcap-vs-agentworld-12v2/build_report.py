#!/usr/bin/env python3
"""Render the ThinkingCap versus Qwen-AgentWorld paired comparison report."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

REPORT_ROOT = Path(__file__).resolve().parent
ANALYSIS_PATH = REPORT_ROOT / "analysis.json"


def escape(value: object) -> str:
    """Escape one value for safe HTML rendering."""
    return html.escape(str(value), quote=True)


def format_integer(value: float) -> str:
    """Format a numeric count with thousands separators."""
    return f"{value:,.0f}"


def format_compact(value: float) -> str:
    """Format large counts with compact decimal units."""
    for suffix, divisor in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if abs(value) >= divisor:
            return f"{value / divisor:.2f}{suffix}"
    return f"{value:.0f}"


def format_percent(value: float | None, digits: int = 1) -> str:
    """Format a zero-to-one ratio as a percentage."""
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def format_points(value: float, digits: int = 1) -> str:
    """Format a zero-to-one delta as percentage points."""
    return f"{value * 100:+.{digits}f} pp"


def format_duration(seconds: float) -> str:
    """Format seconds as a compact duration."""
    total = round(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def result_tag(result: dict[str, Any]) -> str:
    """Render one observed benchmark outcome."""
    if result["reward_binary"] == 1:
        return '<span class="tag good">solved</span>'
    if result["reward_binary"] < 0:
        return '<span class="tag bad">invalid</span>'
    return '<span class="tag neutral">unsolved</span>'


def render_task_rows(analysis: dict[str, Any]) -> str:
    """Render the task-level paired scorecard."""
    agentworld = {row["task"]: row for row in analysis["tasks"]["agentworld"]}
    thinkingcap = {row["task"]: row for row in analysis["tasks"]["thinkingcap"]}
    rows = []
    for task, delta in sorted(
        analysis["paired"]["task_deltas"].items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        left = agentworld[task]
        right = thinkingcap[task]
        delta_class = "up" if delta > 0 else "down" if delta < 0 else ""
        winner = (
            '<span class="tag good">ThinkingCap</span>'
            if delta > 0
            else '<span class="tag caution">AgentWorld</span>'
            if delta < 0
            else '<span class="tag neutral">tie</span>'
        )
        rows.append(
            "<tr>"
            f"<td><strong>{escape(task)}</strong><br><span class='muted'>{escape(left['language'])}</span></td>"
            f"<td class='num'>{left['mean_partial']:.3f}</td>"
            f"<td class='num'>{right['mean_partial']:.3f}</td>"
            f"<td class='num {delta_class}'>{delta:+.3f}</td>"
            f"<td class='num'>{format_percent(left['f2p_micro'])}</td>"
            f"<td class='num'>{format_percent(right['f2p_micro'])}</td>"
            f"<td class='num'>{left['solves']}–{right['solves']}</td>"
            f"<td class='num'>{left['invalid']}–{right['invalid']}</td>"
            f"<td>{winner}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_task_delta_bars(analysis: dict[str, Any]) -> str:
    """Render deterministic centered bars for task-level partial deltas."""
    task_metadata = analysis["tasks"]["metadata"]
    maximum = max(abs(value) for value in analysis["paired"]["task_deltas"].values())
    rows = []
    for task, delta in sorted(
        analysis["paired"]["task_deltas"].items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        width = abs(delta) / maximum * 48
        if delta > 0:
            bar = (
                f"<div class='delta-bar tc' style='left:50%;width:{width:.2f}%'></div>"
            )
        elif delta < 0:
            bar = (
                f"<div class='delta-bar aw' style='right:50%;width:{width:.2f}%'></div>"
            )
        else:
            bar = ""
        rows.append(
            "<div class='delta-row'>"
            f"<div class='delta-label'>{escape(task)}<span>{escape(task_metadata[task]['language'])}</span></div>"
            f"<div class='delta-track'><i></i>{bar}</div>"
            f"<div class='delta-value {'up' if delta > 0 else 'down' if delta < 0 else ''}'>{delta:+.3f}</div>"
            "</div>"
        )
    return "".join(rows)


def render_language_rows(analysis: dict[str, Any]) -> str:
    """Render language-level quality and speed metrics."""
    agentworld = {row["language"]: row for row in analysis["languages"]["agentworld"]}
    thinkingcap = {row["language"]: row for row in analysis["languages"]["thinkingcap"]}
    rows = []
    for language in ("Go", "Python", "Typescript"):
        left = agentworld[language]
        right = thinkingcap[language]
        delta = right["mean_partial"] - left["mean_partial"]
        rows.append(
            "<tr>"
            f"<td><strong>{escape(language)}</strong></td>"
            f"<td class='num'>{left['mean_partial']:.3f}</td>"
            f"<td class='num'>{right['mean_partial']:.3f}</td>"
            f"<td class='num up'>{delta:+.3f}</td>"
            f"<td class='num'>{format_percent(left['f2p_micro'])}</td>"
            f"<td class='num'>{format_percent(right['f2p_micro'])}</td>"
            f"<td class='num'>{format_duration(left['median_wall_s'])}</td>"
            f"<td class='num'>{format_duration(right['median_wall_s'])}</td>"
            f"<td class='num'>{format_compact(left['median_tokens'])}</td>"
            f"<td class='num'>{format_compact(right['median_tokens'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_pair_rows(analysis: dict[str, Any]) -> str:
    """Render all 36 matched task and rep outcomes."""
    rows = []
    for pair in analysis["pairs"]:
        left = pair["agentworld"]
        right = pair["thinkingcap"]
        delta = pair["delta_thinkingcap_minus_agentworld"]
        delta_class = "up" if delta > 0 else "down" if delta < 0 else ""
        rows.append(
            "<tr>"
            f"<td>{escape(pair['task'])}</td>"
            f"<td class='num'>{pair['rep']}</td>"
            f"<td>{result_tag(left)}</td>"
            f"<td class='num'>{left['reward_partial']:.3f}</td>"
            f"<td>{result_tag(right)}</td>"
            f"<td class='num'>{right['reward_partial']:.3f}</td>"
            f"<td class='num {delta_class}'>{delta:+.3f}</td>"
            f"<td class='num'>{format_compact(left['total_tokens'])}</td>"
            f"<td class='num'>{format_compact(right['total_tokens'])}</td>"
            f"<td class='num'>{format_duration(left['agent_wall_s'])}</td>"
            f"<td class='num'>{format_duration(right['agent_wall_s'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_packet_cards(analysis: dict[str, Any]) -> str:
    """Render the evidence-backed trajectory packet summaries."""
    pair_lookup = {(row["task"], row["rep"]): row for row in analysis["pairs"]}
    cards = []
    for packet in analysis["packet_index"]:
        pair = pair_lookup[(packet["task"], packet["rep"])]
        classification = packet["classification"]
        left = pair["agentworld"]
        right = pair["thinkingcap"]
        winner_class = "tc" if classification["winner"] == "ThinkingCap" else "aw"
        cards.append(
            f"<article class='packet {winner_class}'>"
            "<div class='packet-head'>"
            f"<div><span class='tag {'good' if winner_class == 'tc' else 'caution'}'>{escape(classification['winner'])} packet win</span>"
            f"<h3>{escape(pair['title'])} · rep {pair['rep']}</h3></div>"
            f"<div class='packet-delta'>{pair['delta_thinkingcap_minus_agentworld']:+.3f}</div>"
            "</div>"
            f"<p><strong>{escape(classification['primary_bucket'])}:</strong> {escape(classification['mechanism'])}</p>"
            "<div class='packet-metrics'>"
            f"<span>Partial <b>{left['reward_partial']:.3f} → {right['reward_partial']:.3f}</b></span>"
            f"<span>F2P <b>{left['f2p_passed']}/{left['f2p_total']} → {right['f2p_passed']}/{right['f2p_total']}</b></span>"
            f"<span>Wall <b>{format_duration(left['agent_wall_s'])} → {format_duration(right['agent_wall_s'])}</b></span>"
            "</div>"
            f"<p class='hypothesis'><strong>Process hypothesis:</strong> {escape(classification['guidance_implication'])}</p>"
            f"<p class='packet-links'><a href='{escape(packet['markdown'])}'>Readable packet</a> · <a href='{escape(packet['json'])}'>Packet JSON</a></p>"
            "</article>"
        )
    return "".join(cards)


def build_report() -> str:
    """Build the complete self-contained HTML comparison."""
    analysis = json.loads(ANALYSIS_PATH.read_text())
    agentworld = analysis["aggregate"]["agentworld"]
    thinkingcap = analysis["aggregate"]["thinkingcap"]
    paired = analysis["paired"]
    aw_delivery = analysis["delivery"]["agentworld"]
    tc_delivery = analysis["delivery"]["thinkingcap"]
    aw_run = analysis["runs"]["agentworld"]
    tc_run = analysis["runs"]["thinkingcap"]
    f2p_delta = thinkingcap["f2p_micro"] - agentworld["f2p_micro"]
    p2p_delta = thinkingcap["p2p_micro"] - agentworld["p2p_micro"]
    token_reduction = 1 - thinkingcap["total_tokens"] / agentworld["total_tokens"]
    wall_advantage = 1 - agentworld["wall_median_s"] / thinkingcap["wall_median_s"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ThinkingCap vs Qwen-AgentWorld · 12_v2 paired comparison</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23335dff%22/><text x=%2250%22 y=%2264%22 text-anchor=%22middle%22 font-size=%2236%22 fill=%22white%22>VS</text></svg>" />
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#b77d00;--amber-soft:#fff4d8;--purple:#7754d8;--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);--radius-xl:28px;--radius-lg:20px;--max:1320px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),radial-gradient(circle at top right,rgba(183,125,0,.08),transparent 25%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.91em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px;overflow-wrap:anywhere}}.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}.hero,section{{background:rgba(255,255,255,.9);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}.hero{{padding:clamp(24px,4vw,42px);overflow:hidden;position:relative}}.hero::after{{content:"";position:absolute;inset:auto -9% -45% auto;width:500px;height:500px;background:radial-gradient(circle,rgba(51,93,255,.13),transparent 70%);pointer-events:none}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2.05rem,4.7vw,4.2rem);margin-top:14px;max-width:17ch}}h2{{font-size:clamp(1.45rem,2.5vw,2.1rem)}}h3{{font-size:1.12rem;margin-bottom:8px}}.subtitle{{max-width:87ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.09rem);margin:15px 0 0}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}.pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line)}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:var(--blue-2)}}.stats{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:13px;margin-top:25px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:15px;min-height:118px;box-shadow:var(--shadow-sm)}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:9px}}.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.95rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;margin-top:8px;font-size:.85rem;color:var(--muted);font-weight:600}}section{{margin-top:20px;padding:clamp(18px,3vw,29px)}}.section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}}.section-head p{{margin:7px 0 0;color:var(--muted);max-width:88ch}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}.panel{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-sm)}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:15px 17px;color:#22314d;margin-top:14px}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff9e8,#fff)}}.callout strong{{color:var(--blue-2)}}.tag{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:.73rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}}.up{{color:var(--green);font-weight:800}}.down{{color:var(--amber);font-weight:800}}.muted{{color:var(--muted);font-size:.86em}}.table-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:14px}}table{{width:100%;border-collapse:collapse;font-size:.89rem}}th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:800;background:var(--surface-2);position:sticky;top:0}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}tbody tr:hover{{background:var(--surface-2)}}tbody tr:last-child td{{border-bottom:0}}.kv{{display:grid;grid-template-columns:minmax(180px,.8fr) 2fr;gap:0}}.kv div{{padding:9px 0;border-bottom:1px solid var(--line)}}.kv .k{{color:var(--muted);font-weight:750}}.delta-list{{display:grid;gap:11px}}.delta-row{{display:grid;grid-template-columns:minmax(230px,1.3fr) 2fr 60px;gap:12px;align-items:center}}.delta-label{{font-size:.85rem;font-weight:750;overflow-wrap:anywhere}}.delta-label span{{display:block;color:var(--muted);font-size:.76rem}}.delta-track{{height:19px;border-radius:999px;background:#edf2f7;position:relative;overflow:hidden;border:1px solid #dde5ef}}.delta-track i{{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#8796aa;z-index:2}}.delta-bar{{position:absolute;top:0;bottom:0}}.delta-bar.tc{{background:var(--green)}}.delta-bar.aw{{background:var(--amber)}}.delta-value{{text-align:right;font-variant-numeric:tabular-nums;font-weight:850}}.legend{{display:flex;gap:16px;flex-wrap:wrap;color:var(--muted);font-size:.85rem}}.legend span::before{{content:"";display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}}.legend .tc::before{{background:var(--green)}}.legend .aw::before{{background:var(--amber)}}.packets{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}}.packet{{background:var(--surface);border:1px solid var(--line);border-top:5px solid var(--green);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-sm)}}.packet.aw{{border-top-color:var(--amber)}}.packet-head{{display:flex;align-items:start;justify-content:space-between;gap:14px}}.packet h3{{margin-top:9px}}.packet-delta{{font-size:1.35rem;font-weight:900;font-variant-numeric:tabular-nums}}.packet p{{font-size:.9rem}}.packet-metrics{{display:flex;gap:8px;flex-wrap:wrap}}.packet-metrics span{{background:var(--surface-2);border:1px solid var(--line);border-radius:9px;padding:6px 8px;font-size:.79rem;color:var(--muted)}}.hypothesis{{border-left:3px solid var(--blue);padding-left:10px;color:#33445f}}.packet-links{{margin-bottom:0;font-weight:750}}.flow{{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:center}}.model-card{{border:1px solid var(--line);border-radius:16px;padding:16px;background:var(--surface)}}.model-card h3{{font-size:1.25rem}}.versus{{font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;font-weight:900;color:var(--muted)}}details{{border:1px solid var(--line);border-radius:14px;background:var(--surface);padding:13px 15px;margin-top:12px}}summary{{cursor:pointer;font-weight:850;color:#263b66}}.foot{{margin-top:24px;color:var(--muted);font-size:.84rem;text-align:center}}@media(max-width:1000px){{.stats{{grid-template-columns:repeat(3,minmax(0,1fr))}}.grid-3{{grid-template-columns:1fr}}}}@media(max-width:820px){{.grid-2,.packets{{grid-template-columns:1fr}}.flow{{grid-template-columns:1fr}}.versus{{text-align:center}}}}@media(max-width:650px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.delta-row{{grid-template-columns:1fr 62px}}.delta-track{{grid-column:1/-1;grid-row:2}}.kv{{grid-template-columns:1fr}}}}
</style>
</head>
<body><div class="wrap">
<header class="hero">
  <span class="eyebrow">Paired model comparison · 12_v2 · 36 reps each · Pi 0.83.0</span>
  <h1>ThinkingCap wins quality. AgentWorld wins speed.</h1>
  <p class="subtitle">On the same 12 tasks and three reps, ThinkingCap produced the only strict solve, passed 348 more feature tests, and used 12.8% fewer accounted tokens. Qwen-AgentWorld finished a median rep 42.3% faster. Both delivered reliable reasoning and tool calls; the quality gap comes from implementation behavior, not parser failure.</p>
  <div class="pillrow"><span class="pill good">ThinkingCap · 1 strict solve</span><span class="pill caution">AgentWorld · 42% faster median</span><span class="pill good">ThinkingCap · +23.2 pp F2P</span><span class="pill neutral">3 invalid each</span><span class="pill neutral">0 malformed calls</span></div>
  <div class="stats">
    <div class="stat"><span class="label">Strict solves · AW → TC</span><span class="value">0 → 1</span><span class="sub">one discordant solved rep</span></div>
    <div class="stat"><span class="label">Mean partial · AW → TC</span><span class="value">.798 → .820</span><span class="sub">+{paired["mean_partial_delta"]:.3f} paired</span></div>
    <div class="stat"><span class="label">Feature tests · micro</span><span class="value">38.1% → 61.3%</span><span class="sub">{format_points(f2p_delta)} ThinkingCap</span></div>
    <div class="stat"><span class="label">Preservation · micro</span><span class="value">99.50% → 99.93%</span><span class="sub">{format_points(p2p_delta, 2)} ThinkingCap</span></div>
    <div class="stat"><span class="label">Median wall · AW → TC</span><span class="value">9:55 → 17:12</span><span class="sub">AgentWorld {wall_advantage * 100:.1f}% faster</span></div>
    <div class="stat"><span class="label">Total tokens · AW → TC</span><span class="value">242M → 211M</span><span class="sub">ThinkingCap {token_reduction * 100:.1f}% fewer</span></div>
  </div>
</header>

<section>
  <div class="section-head"><div><h2>Executive verdict</h2><p>The evidence supports different winners for quality and latency.</p></div></div>
  <div class="grid-3">
    <div class="callout good"><strong>Quality: ThinkingCap.</strong> It leads partial reward on 25/36 paired reps and 10/12 tasks, passes 918/1,498 feature tests versus 570/1,498, and owns the only strict solve. Its valid-only mean partial is {thinkingcap["mean_partial_valid"]:.3f} versus {agentworld["mean_partial_valid"]:.3f}.</div>
    <div class="callout caution"><strong>Speed: AgentWorld.</strong> Median agent wall is {format_duration(agentworld["wall_median_s"])} versus {format_duration(thinkingcap["wall_median_s"])}. AgentWorld uses 13.2% more turns and 14.7% more accounted tokens, but its sparse-MoE deployment returns those turns much faster.</div>
    <div class="callout"><strong>Reliability: tied.</strong> Both have three invalid outcomes, 72/72 exact provider captures, one thinking block per assistant message, no malformed tool calls, no raw tool-call leakage, and no length stops.</div>
  </div>
  <div class="callout caution"><strong>Confidence boundary:</strong> the observed mean partial gain is +{paired["mean_partial_delta"]:.3f}, but the task-clustered bootstrap 95% interval is {paired["bootstrap_95"]["lower_95"]:+.3f} to {paired["bootstrap_95"]["upper_95"]:+.3f}. It crosses zero. The direction is broad—10 task wins—but 12 tasks and one strict solve do not establish a decisive population-level advantage.</div>
</section>

<section>
  <div class="section-head"><div><h2>What is controlled—and what is not</h2><p>This is a paired model/config-bundle comparison, not a causal estimate of model weights alone.</p></div></div>
  <div class="flow">
    <div class="model-card"><span class="tag caution">Left</span><h3>Qwen-AgentWorld 35B-A3B</h3><p>Qwen3.5 MoE · 35B total / 3B active · AWQ INT4<br><code>server60:8080</code> · temperature 0.6 · 65,536 output ceiling · 4 workers</p></div>
    <div class="versus">versus</div>
    <div class="model-card"><span class="tag good">Right</span><h3>ThinkingCap Qwen3.6 27B</h3><p>Qwen3.6 dense fine-tune · 27B · AWQ INT4<br><code>server60:8081</code> · temperature 1.0 · 98,304 output ceiling · 2 workers</p></div>
  </div>
  <div class="callout"><strong>Shared:</strong> stock Pi with no config-authored prompt text, Pi 0.83.0, thinking high, 262,144 context, vLLM 0.25.1, TP2, FP8 KV cache, Qwen3 reasoning parser, qwen3_coder tool parser, thinking preservation, no hard thinking budget, identical tasks/reps, and identical harness/task/verifier identities.</div>
  <div class="callout caution"><strong>Different:</strong> checkpoint, dense versus sparse-MoE architecture, endpoint/GPU allocation, temperature, output ceiling, and launch concurrency. Neither output ceiling bound behavior—the largest completion was {format_integer(aw_delivery["session"]["max_single_completion"]["tokens"])} tokens for AgentWorld and {format_integer(tc_delivery["session"]["max_single_completion"]["tokens"])} for ThinkingCap—so cap size does not explain the score gap.</div>
</section>

<section>
  <div class="section-head"><div><h2>Primary outcome table</h2><p>Intention-to-treat keeps invalid reps in the denominator with partial reward zero. Valid-only values are secondary.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">AgentWorld</th><th class="num">ThinkingCap</th><th class="num">TC − AW</th><th>Verdict</th></tr></thead><tbody>
    <tr><td>Strict solves</td><td class="num">{agentworld["solves"]} / 36</td><td class="num">{thinkingcap["solves"]} / 36</td><td class="num up">+1</td><td><span class="tag good">ThinkingCap</span></td></tr>
    <tr><td>Invalid outcomes</td><td class="num">{agentworld["invalid"]}</td><td class="num">{thinkingcap["invalid"]}</td><td class="num">0</td><td><span class="tag neutral">tie</span></td></tr>
    <tr><td>Mean partial · all reps</td><td class="num">{agentworld["mean_partial_all"]:.3f}</td><td class="num">{thinkingcap["mean_partial_all"]:.3f}</td><td class="num up">+{paired["mean_partial_delta"]:.3f}</td><td><span class="tag good">ThinkingCap</span></td></tr>
    <tr><td>Mean partial · valid only</td><td class="num">{agentworld["mean_partial_valid"]:.3f}</td><td class="num">{thinkingcap["mean_partial_valid"]:.3f}</td><td class="num up">+{thinkingcap["mean_partial_valid"] - agentworld["mean_partial_valid"]:.3f}</td><td><span class="tag good">ThinkingCap</span></td></tr>
    <tr><td>Feature tests · micro</td><td class="num">{format_integer(agentworld["f2p_passed"])} / {format_integer(agentworld["f2p_total"])} · {format_percent(agentworld["f2p_micro"])}</td><td class="num">{format_integer(thinkingcap["f2p_passed"])} / {format_integer(thinkingcap["f2p_total"])} · {format_percent(thinkingcap["f2p_micro"])}</td><td class="num up">{format_points(f2p_delta)}</td><td><span class="tag good">ThinkingCap</span></td></tr>
    <tr><td>Preservation tests · micro</td><td class="num">{format_integer(agentworld["p2p_passed"])} / {format_integer(agentworld["p2p_total"])} · {format_percent(agentworld["p2p_micro"], 2)}</td><td class="num">{format_integer(thinkingcap["p2p_passed"])} / {format_integer(thinkingcap["p2p_total"])} · {format_percent(thinkingcap["p2p_micro"], 2)}</td><td class="num up">{format_points(p2p_delta, 2)}</td><td><span class="tag good">ThinkingCap</span></td></tr>
    <tr><td>Median agent wall</td><td class="num">{format_duration(agentworld["wall_median_s"])}</td><td class="num">{format_duration(thinkingcap["wall_median_s"])}</td><td class="num down">+{format_duration(thinkingcap["wall_median_s"] - agentworld["wall_median_s"])}</td><td><span class="tag caution">AgentWorld</span></td></tr>
    <tr><td>Total accounted tokens</td><td class="num">{format_compact(agentworld["total_tokens"])}</td><td class="num">{format_compact(thinkingcap["total_tokens"])}</td><td class="num up">−{format_compact(agentworld["total_tokens"] - thinkingcap["total_tokens"])}</td><td><span class="tag good">ThinkingCap</span></td></tr>
  </tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Paired churn</h2><p>Net score hides the consistency and timeout swaps underneath it.</p></div></div>
  <div class="stats">
    <div class="stat"><span class="label">Partial wins · TC</span><span class="value">{paired["thinkingcap_partial_wins"]}</span><span class="sub">of 36 paired reps</span></div>
    <div class="stat"><span class="label">Partial wins · AW</span><span class="value">{paired["agentworld_partial_wins"]}</span><span class="sub">6 exact ties</span></div>
    <div class="stat"><span class="label">Material wins · TC</span><span class="value">{paired["thinkingcap_material_wins_gt_005"]}</span><span class="sub">delta &gt; +0.05</span></div>
    <div class="stat"><span class="label">Material wins · AW</span><span class="value">{paired["agentworld_material_wins_gt_005"]}</span><span class="sub">delta &lt; −0.05</span></div>
    <div class="stat"><span class="label">Task wins · TC</span><span class="value">{paired["thinkingcap_task_wins"]} / 12</span><span class="sub">AgentWorld 1 · one tie</span></div>
    <div class="stat"><span class="label">Both-valid delta</span><span class="value">+{paired["both_valid_mean_partial_delta"]:.3f}</span><span class="sub">32 pairs; 24 TC wins</span></div>
  </div>
  <div class="callout"><strong>Timeout sensitivity:</strong> two pairs were invalid on both sides. AgentWorld alone timed out on <code>langchain rep2</code>; ThinkingCap alone timed out on <code>langchain rep0</code>. Those opposite 0.975 swings cancel at task level, leaving LangChain tied at 0.325. Excluding every pair invalid on either side, ThinkingCap still leads mean partial by +{paired["both_valid_mean_partial_delta"]:.3f} across 32 pairs.</div>
</section>

<section>
  <div class="section-head"><div><h2>Task-level partial delta</h2><p>Positive values favor ThinkingCap; negative values favor AgentWorld.</p></div><div class="legend"><span class="tc">ThinkingCap</span><span class="aw">AgentWorld</span></div></div>
  <div class="delta-list">{render_task_delta_bars(analysis)}</div>
</section>

<section>
  <div class="section-head"><div><h2>Task scorecard</h2><p>ThinkingCap's largest task gains are SuperJSON and Tengo. AgentWorld's only task-level quality win is GoReleaser.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">AW partial</th><th class="num">TC partial</th><th class="num">Delta</th><th class="num">AW F2P</th><th class="num">TC F2P</th><th class="num">Solves AW–TC</th><th class="num">Invalid AW–TC</th><th>Winner</th></tr></thead><tbody>{render_task_rows(analysis)}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Language split</h2><p>ThinkingCap's quality edge appears in all three languages; AgentWorld's speed edge does too.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Language</th><th class="num">AW partial</th><th class="num">TC partial</th><th class="num">Delta</th><th class="num">AW F2P</th><th class="num">TC F2P</th><th class="num">AW median wall</th><th class="num">TC median wall</th><th class="num">AW median tokens</th><th class="num">TC median tokens</th></tr></thead><tbody>{render_language_rows(analysis)}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Trajectory style and delivery</h2><p>Both provider contracts worked. The models spent their successful trajectories differently.</p></div></div>
  <div class="grid-2">
    <div class="panel"><h3>Qwen-AgentWorld</h3><div class="kv">
      <div class="k">Assistant turns</div><div>{format_integer(aw_delivery["session"]["assistant_messages"])}</div>
      <div class="k">Tool calls</div><div>{format_integer(aw_delivery["session"]["tool_call_blocks"])}</div>
      <div class="k">Tool mix</div><div>{format_integer(aw_delivery["session"]["tool_names"]["read"])} read · {format_integer(aw_delivery["session"]["tool_names"]["edit"])} edit · {format_integer(aw_delivery["session"]["tool_names"]["bash"])} bash</div>
      <div class="k">Tool-result errors</div><div>{format_integer(aw_delivery["session"]["tool_result_errors"])} / {format_integer(aw_delivery["session"]["tool_results"])}</div>
      <div class="k">Median patch</div><div>{format_compact(agentworld["median_patch_bytes"])}</div>
      <div class="k">Max completion</div><div>{format_integer(aw_delivery["session"]["max_single_completion"]["tokens"])} / 65,536</div>
      <div class="k">Provider delivery</div><div>72/72 exact · 0 malformed · 0 length stops</div>
    </div></div>
    <div class="panel"><h3>ThinkingCap</h3><div class="kv">
      <div class="k">Assistant turns</div><div>{format_integer(tc_delivery["session"]["assistant_messages"])}</div>
      <div class="k">Tool calls</div><div>{format_integer(tc_delivery["session"]["tool_call_blocks"])}</div>
      <div class="k">Tool mix</div><div>{format_integer(tc_delivery["session"]["tool_names"]["read"])} read · {format_integer(tc_delivery["session"]["tool_names"]["edit"])} edit · {format_integer(tc_delivery["session"]["tool_names"]["bash"])} bash</div>
      <div class="k">Tool-result errors</div><div>{format_integer(tc_delivery["session"]["tool_result_errors"])} / {format_integer(tc_delivery["session"]["tool_results"])}</div>
      <div class="k">Median patch</div><div>{format_compact(thinkingcap["median_patch_bytes"])}</div>
      <div class="k">Max completion</div><div>{format_integer(tc_delivery["session"]["max_single_completion"]["tokens"])} / 98,304</div>
      <div class="k">Provider delivery</div><div>72/72 exact · 0 malformed · 0 length stops</div>
    </div></div>
  </div>
  <div class="callout"><strong>Observed style difference:</strong> AgentWorld used 33% more <code>read</code> calls and 24% fewer <code>edit</code> calls, with 421 more assistant turns but only 84 more tool calls. ThinkingCap produced a 36.4KB median patch versus 22.2KB for AgentWorld. These are trajectory descriptors, not proof of why one model scored better.</div>
  <div class="callout caution"><strong>Patch-total caveat:</strong> ThinkingCap's total patch bytes include a 2.10MB generated-file outlier on <code>participle rep2</code>. Use medians, not total bytes, for the typical patch comparison.</div>
</section>

<section>
  <div class="section-head"><div><h2>Seven trajectory packets</h2><p>Selection was fixed before interpretation: every strict solve flip, invalid-outcome discordance, or |partial delta| above 0.10.</p></div></div>
  <div class="packets">{render_packet_cards(analysis)}</div>
</section>

<section>
  <div class="section-head"><div><h2>Resource and throughput profile</h2><p>Native session usage sums repeated full prompts across turns. Run elapsed time is not apples-to-apples because AgentWorld used four workers and ThinkingCap two.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">AgentWorld</th><th class="num">ThinkingCap</th><th>Read</th></tr></thead><tbody>
    <tr><td>Run elapsed</td><td class="num">{format_duration(aw_run["elapsed_s"])}</td><td class="num">{format_duration(tc_run["elapsed_s"])}</td><td>4 workers versus 2; do not attribute directly to model speed</td></tr>
    <tr><td>Agent wall sum</td><td class="num">{format_duration(agentworld["wall_sum_s"])}</td><td class="num">{format_duration(thinkingcap["wall_sum_s"])}</td><td>AgentWorld 32.8% lower, despite two agent timeouts versus one</td></tr>
    <tr><td>Median / P90 wall</td><td class="num">{format_duration(agentworld["wall_median_s"])} / {format_duration(agentworld["wall_p90_s"])}</td><td class="num">{format_duration(thinkingcap["wall_median_s"])} / {format_duration(thinkingcap["wall_p90_s"])}</td><td>AgentWorld faster across the distribution</td></tr>
    <tr><td>Input tokens</td><td class="num">{format_compact(agentworld["input_tokens"])}</td><td class="num">{format_compact(thinkingcap["input_tokens"])}</td><td>AgentWorld +14.7%</td></tr>
    <tr><td>Output tokens</td><td class="num">{format_compact(agentworld["output_tokens"])}</td><td class="num">{format_compact(thinkingcap["output_tokens"])}</td><td>AgentWorld +10.7%</td></tr>
    <tr><td>Median / P90 total tokens</td><td class="num">{format_compact(agentworld["median_total_tokens"])} / {format_compact(agentworld["p90_total_tokens"])}</td><td class="num">{format_compact(thinkingcap["median_total_tokens"])} / {format_compact(thinkingcap["p90_total_tokens"])}</td><td>P90 nearly equal; AgentWorld median 8.3% higher</td></tr>
    <tr><td>Turns / tool calls</td><td class="num">{format_integer(agentworld["turns"])} / {format_integer(agentworld["tool_calls"])}</td><td class="num">{format_integer(thinkingcap["turns"])} / {format_integer(thinkingcap["tool_calls"])}</td><td>AgentWorld more turns; tool-call totals close</td></tr>
  </tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>All 36 matched reps</h2><p>Delta is ThinkingCap minus AgentWorld. Invalid outcomes remain at partial zero.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>AW outcome</th><th class="num">AW partial</th><th>TC outcome</th><th class="num">TC partial</th><th class="num">Delta</th><th class="num">AW tokens</th><th class="num">TC tokens</th><th class="num">AW wall</th><th class="num">TC wall</th></tr></thead><tbody>{render_pair_rows(analysis)}</tbody></table></div>
</section>

<section>
  <div class="section-head"><div><h2>Decision</h2></div></div>
  <div class="callout good"><strong>Choose ThinkingCap when correctness matters more than latency.</strong> It has the only strict solve, a +23.2-point feature-test advantage, stronger preservation, fewer accounted tokens, and a broad 10-of-12 task direction.</div>
  <div class="callout caution"><strong>Choose AgentWorld when iteration latency dominates.</strong> It cuts median agent wall from 17:12 to 9:55 and wins GoReleaser by choosing a better attempt-auditing seam, but its feature coverage is much weaker overall.</div>
  <div class="callout"><strong>Do not tune the output ceiling next.</strong> Neither model approached its cap. The highest-value follow-up is a larger paired subset or targeted reruns of SuperJSON, Tengo, GoReleaser, and SQL formatter while holding sampling and concurrency fixed. That would test whether the observed implementation-pattern differences persist.</div>
</section>

<div class="foot">Derived from canonical <code>result.json</code>, native sessions, provider captures, patches, CTRF/verifier artifacts, and structured run state. <a href="analysis.json">Download the complete metric dataset</a>.<br>Positive deltas favor ThinkingCap. Packet classifications separate direct evidence from process hypotheses.</div>
</div></body></html>"""


def main() -> None:
    """Write the deterministic comparison report page."""
    output_path = REPORT_ROOT / "index.html"
    output_path.write_text(build_report())
    print(output_path)


if __name__ == "__main__":
    main()
