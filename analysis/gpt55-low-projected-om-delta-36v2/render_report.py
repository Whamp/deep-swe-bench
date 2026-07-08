#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "summary.json").read_text())
S = DATA["summaries"]
P = DATA["pairs"]
LABELS = DATA["labels"]
TARGET = DATA["target_config"]


def fmt_int(x):
    return f"{int(round(x)):,}"


def fmt_m(x, digits=2):
    return f"{x/1_000_000:.{digits}f}M"


def fmt_money(x, digits=2):
    return f"${x:,.{digits}f}"


def fmt_pct(x, digits=1):
    return f"{100*x:.{digits}f}%"


def fmt_float(x, digits=3):
    return f"{x:.{digits}f}"


def pval(x):
    if x is None:
        return "—"
    return f"p={x:.3f}"


def cls_delta(x, higher=True):
    if abs(x) < 1e-12:
        return "neutral"
    good = x > 0 if higher else x < 0
    return "good" if good else "bad"


def sign(x, digits=3, money=False, integer=False):
    if integer:
        s = f"{int(round(abs(x))):,}"
    elif money:
        s = fmt_money(abs(x), 3)
    else:
        s = f"{abs(x):.{digits}f}"
    return ("+" if x >= 0 else "−") + s


def tr(cells, cls=""):
    return f"<tr class='{cls}'>" + "".join(cells) + "</tr>"


def td(x, cls=""):
    return f"<td class='{cls}'>{x}</td>"


def th(x, cls=""):
    return f"<th class='{cls}'>{x}</th>"


def tag(text, kind="neutral"):
    return f"<span class='tag {kind}'>{html.escape(text)}</span>"


def pill(text, kind="neutral"):
    return f"<span class='pill {kind}'>{html.escape(text)}</span>"


def config_rows():
    rows=[]
    for c in DATA["configs"]:
        m=S[c]
        kind = "target" if c == TARGET else ""
        rows.append(tr([
            td(html.escape(LABELS[c])),
            td(f"{m['solves']}/108", "num"),
            td(fmt_float(m["mean_partial"], 4), "num"),
            td(fmt_money(m["median_combined_cost"], 3), "num"),
            td(fmt_money(m["total_combined_cost"], 2), "num"),
            td(fmt_m(m["median_combined_tokens"]), "num"),
            td(f"{m['om_worker_calls']:,}", "num"),
            td(str(m.get("projection_delta_messages") or "—"), "num"),
            td(tag("target", "good") if c==TARGET else ""),
        ], kind))
    return "\n".join(rows)


def pair_rows():
    keys=[
        "delta_vs_baseline",
        "delta_vs_recall_placebo",
        "delta_vs_stock_om",
        "delta_vs_projected_v1",
    ]
    rows=[]
    for k in keys:
        p=P[k]
        rows.append(tr([
            td(f"{html.escape(p['other_label'])} vs {html.escape(p['base_label'])}"),
            td(sign(p["solve_delta"], integer=True), f"num {cls_delta(p['solve_delta'])}"),
            td(sign(p["mean_delta_partial"], 4), f"num {cls_delta(p['mean_delta_partial'])}"),
            td(sign(p["median_delta_combined_cost_usd"], money=True), f"num {cls_delta(p['median_delta_combined_cost_usd'], higher=False)}"),
            td(sign(p["median_delta_combined_total_tokens"], integer=True), f"num {cls_delta(p['median_delta_combined_total_tokens'], higher=False)}"),
            td(f"{p['improved_cells']} / {p['worsened_cells']} / {p['tied_cells']}", "num"),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", "num"),
        ]))
    return "\n".join(rows)


def difficulty_rows(pair_key):
    p=P[pair_key]
    rows=[]
    for bucket in ["hard", "medium", "easy"]:
        d=p["difficulty"].get(bucket)
        rows.append(tr([
            td(bucket.title()),
            td(str(d["n"]), "num"),
            td(f"{d['base_solves']} → {d['other_solves']}", "num"),
            td(sign(d["solve_delta"], integer=True), f"num {cls_delta(d['solve_delta'])}"),
            td(sign(d["mean_delta_partial"], 4), f"num {cls_delta(d['mean_delta_partial'])}"),
            td(sign(d["median_delta_cost"], money=True), f"num {cls_delta(d['median_delta_cost'], higher=False)}"),
        ]))
    return "\n".join(rows)


def mover_rows(pair_key, which="top_wins", n=8):
    rows=[]
    for x in P[pair_key][which][:n]:
        delta=x["delta_partial"]
        rows.append(tr([
            td(f"<strong>{html.escape(x['title'])}</strong><br><span class='muted t-mono'>{html.escape(x['task'])} · rep{x['rep']} · {x['difficulty']}</span>"),
            td(f"{x['base_partial']:.3f} → {x['other_partial']:.3f}", "num"),
            td(sign(delta, 3), f"num {cls_delta(delta)}"),
            td(("✓" if x["base_solved"] else "—") + " → " + ("✓" if x["other_solved"] else "—"), "num"),
            td(sign(x["delta_cost"], money=True), f"num {cls_delta(x['delta_cost'], higher=False)}"),
        ]))
    return "\n".join(rows)


def bar(label, value, maxv, color="blue", sub=""):
    w = 0 if maxv == 0 else max(1, min(100, value / maxv * 100))
    return f"<div class='bar-row'><div class='bar-label'>{html.escape(label)}</div><div><div class='bar-track'><div class='bar-fill {color}' style='width:{w:.2f}%'></div></div><div class='vals'><span>{fmt_int(value)}</span><span>{html.escape(sub)}</span></div></div></div>"


def projection_bars():
    v1=S["projected-om-gpt54mini-low"]
    d=S[TARGET]
    max_chars=max(v1["projection_injected_chars_total"], d["projection_injected_chars_total"])
    max_rows=max(v1["projection_injected_rows"], d["projection_injected_rows"])
    return "".join([
        bar("v1 repeated summaries", v1["projection_injected_chars_total"], max_chars, "red", "chars injected"),
        bar("delta custom messages", d["projection_injected_chars_total"], max_chars, "green", "chars injected"),
        bar("v1 injected requests", v1["projection_injected_rows"], max_rows, "red", "requests"),
        bar("delta messages", d["projection_injected_rows"], max_rows, "green", "custom_message entries"),
    ])


def f2p_rows():
    rows=[]
    for c in DATA["configs"]:
        m=S[c]
        rows.append(tr([
            td(html.escape(LABELS[c])),
            td(f"{m['f2p_passed']:,}/{m['f2p_total']:,}", "num"),
            td(fmt_pct(m["f2p_rate"], 2), "num"),
            td(f"{m['p2p_passed']:,}/{m['p2p_total']:,}", "num"),
            td(fmt_pct(m["p2p_rate"], 3), "num"),
            td(str(m["partial_lt_09"]), "num"),
            td(str(m["partial_ge_099"]), "num"),
        ], "target" if c==TARGET else ""))
    return "\n".join(rows)


base=S["baseline"]
stock=S["observational-memory-gpt54mini-low"]
v1=S["projected-om-gpt54mini-low"]
delta=S[TARGET]

html_doc = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8' />
<meta name='viewport' content='width=device-width, initial-scale=1' />
<title>Projected OM delta · GPT-5.5 low · DeepSWE report</title>
<style>
:root {{
  --bg:#f4f7fb; --surface:#ffffff; --surface-2:#f8fafc; --ink:#102033; --muted:#607086;
  --line:#d9e1ec; --blue:#335dff; --blue-2:#1d3fb8; --green:#178a5b; --green-soft:#e7f7ef;
  --red:#d0473f; --red-soft:#fdeceb; --amber:#c58a00; --amber-soft:#fff4d8;
  --shadow:0 24px 60px rgba(14,30,62,.08); --shadow-sm:0 10px 30px rgba(14,30,62,.06);
  --radius-xl:28px; --radius-lg:20px; --radius-md:14px; --max:1260px;
}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
a{{color:var(--blue);text-decoration:none}} a:hover{{text-decoration:underline}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.93em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}}
.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}
.hero,section{{background:rgba(255,255,255,.9);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}
.hero{{padding:clamp(24px,4vw,42px);overflow:hidden;position:relative}}
.hero::after{{content:"";position:absolute;inset:auto -10% -30% auto;width:440px;height:440px;background:radial-gradient(circle,rgba(23,138,91,.14),transparent 70%);pointer-events:none}}
.eyebrow{{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}
h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.05}} h1{{font-size:clamp(2rem,4.4vw,3.8rem);margin-top:14px;max-width:18ch}} h2{{font-size:clamp(1.35rem,2.2vw,2rem)}}
.subtitle{{max-width:82ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.08rem);margin:14px 0 0}}
.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}} .pill{{display:inline-flex;align-items:center;gap:8px;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line);color:#31415d}} .pill.good{{background:var(--green-soft);color:var(--green);border-color:rgba(23,138,91,.16)}} .pill.bad{{background:var(--red-soft);color:var(--red);border-color:rgba(208,71,63,.16)}} .pill.caution{{background:var(--amber-soft);color:var(--amber);border-color:rgba(197,138,0,.16)}} .pill.neutral{{background:#eef3ff;color:var(--blue-2);border-color:rgba(51,93,255,.16)}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:26px}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:16px;min-height:118px;box-shadow:var(--shadow-sm)}} .stat .label{{display:block;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}} .stat .value{{display:block;font-size:clamp(1.25rem,2vw,1.9rem);font-weight:900;letter-spacing:-.04em}} .stat .sub{{display:block;margin-top:8px;font-size:.9rem;color:var(--muted);font-weight:600}}
.up,.goodtxt{{color:var(--green)}} .down,.badtxt{{color:var(--red)}} .warn{{color:var(--amber)}} .neut{{color:var(--blue-2)}}
section{{margin-top:20px;padding:clamp(18px,3vw,28px)}} .section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}} .section-head p{{margin:6px 0 0;color:var(--muted);max-width:78ch}}
table{{width:100%;border-collapse:collapse;font-size:.94rem;min-width:0}} th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:800}} td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} tbody tr:hover{{background:var(--surface-2)}} tr.target{{background:#f4fbf7}}
.t-mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}} .muted{{color:var(--muted)}}
.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;color:#22314d;margin-top:14px}} .callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}} .callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}} .callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}} .callout strong{{color:var(--blue-2)}}
.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}
.mini{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;text-align:center;box-shadow:var(--shadow-sm)}} .mini .big{{display:block;font-size:2rem;font-weight:900;letter-spacing:-.04em}} .mini .cap{{display:block;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;margin-top:6px}}
.tag{{display:inline-flex;padding:4px 10px;border-radius:999px;font-size:.78rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase}} .tag.good{{background:var(--green-soft);color:var(--green)}} .tag.bad{{background:var(--red-soft);color:var(--red)}} .tag.neutral{{background:#eef3ff;color:var(--blue-2)}} .tag.caution{{background:var(--amber-soft);color:var(--amber)}}
.bar-list{{display:grid;gap:14px;margin-top:8px}} .bar-row{{display:grid;grid-template-columns:170px 1fr;gap:14px;align-items:center}} .bar-label{{font-weight:800;color:#22314d;font-size:14px}} .bar-track{{position:relative;height:18px;border-radius:999px;background:#edf2f7;overflow:hidden;border:1px solid #dde5ef}} .bar-fill{{position:absolute;inset:0 auto 0 0;border-radius:inherit}} .bar-fill.blue{{background:linear-gradient(90deg,#6f8cff,#244de0)}} .bar-fill.green{{background:linear-gradient(90deg,#45bf81,#178a5b)}} .bar-fill.red{{background:linear-gradient(90deg,#f1786f,#d0473f)}} .vals{{display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);font-weight:700;font-variant-numeric:tabular-nums;margin-top:4px}}
.foot{{margin-top:26px;color:var(--muted);font-size:.86rem;text-align:center}}
@media (max-width:900px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.grid-2,.grid-3{{grid-template-columns:1fr}}table{{font-size:.84rem}}th,td{{padding:8px 7px}}.bar-row{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class='wrap'>
<header class='hero'>
  <span class='eyebrow'>DeepSWE · GPT-5.5 low · 36_v2 × 3 reps</span>
  <h1>Projected OM delta is cleaner, but not a clear Pareto win.</h1>
  <p class='subtitle'>This run tested <strong>projected-om-delta-gpt54mini-low</strong>: GPT‑5.5 low executor, GPT‑5.4‑mini low memory workers, and a cache-safe delta projection path that appends net-new memory as hidden custom messages instead of rewriting provider instructions. It fixes the projection mechanics problem, but the quality lift is still noisy and the cost overhead remains real.</p>
  <div class='pillrow'>
    {pill('108/108 result cells', 'good')}
    {pill('0 reward=-1 / 0 empty patches', 'good')}
    {pill('+5 solves vs clean baseline', 'neutral')}
    {pill('not statistically decisive', 'caution')}
    {pill('94.8% fewer injected chars vs v1', 'good')}
  </div>
  <div class='stats'>
    <div class='stat'><span class='label'>Delta solves</span><span class='value'>{delta['solves']}/108</span><span class='sub neut'>baseline {base['solves']}, stock OM {stock['solves']}, v1 {v1['solves']}</span></div>
    <div class='stat'><span class='label'>Mean partial</span><span class='value'>{fmt_float(delta['mean_partial'], 4)}</span><span class='sub neut'>{sign(P['delta_vs_baseline']['mean_delta_partial'],4)} vs clean baseline</span></div>
    <div class='stat'><span class='label'>Median combined cost</span><span class='value'>{fmt_money(delta['median_combined_cost'], 2)}</span><span class='sub down'>{sign(P['delta_vs_baseline']['median_delta_combined_cost_usd'], money=True)} vs baseline</span></div>
    <div class='stat'><span class='label'>Projection messages</span><span class='value'>{fmt_int(delta['projection_delta_messages'])}</span><span class='sub goodtxt'>custom_message deltas; no provider rewrite</span></div>
    <div class='stat'><span class='label'>Worker overhead</span><span class='value'>{fmt_money(delta['om_worker_cost'], 2)}</span><span class='sub'>{fmt_m(delta['om_worker_tokens'])} worker tokens</span></div>
  </div>
</header>

<section>
  <div class='section-head'><div><h2>Verdict</h2><p>Separate the engineering result from the benchmark result.</p></div></div>
  <div class='grid-2'>
    <div class='callout good'><strong>Engineering result:</strong> delta projection is the right shape. It created executor-visible <code>om.delta_projection</code> custom messages in 104/108 cells, used zero provider-payload rewrites, and cut repeated projection text from 9.48M chars in v1 to 0.49M chars.</div>
    <div class='callout caution'><strong>Efficacy result:</strong> raw solves improved to 33/108, but paired tests do not clear a reliable bar. Versus clean baseline: +5 solves, mean partial +0.0063, McNemar {pval(P['delta_vs_baseline']['mcnemar_p'])}, Wilcoxon {pval(P['delta_vs_baseline']['wilcoxon_partial_p'])}. Treat as promising/noisy, not proven.</div>
  </div>
  <div class='callout bad'><strong>Important caveat:</strong> this config still inherits the neutral OM orchestration sentence. That means clean-baseline comparisons include recall/prompt-surface and prompt-text differences. The cleanest causal read is inside the ladder: recall placebo → stock workers → projected memory variants.</div>
</section>

<section>
  <div class='section-head'><div><h2>Headline table</h2><p>All rows are exactly 36_v2 × 3 reps (108 cells). Combined cost/tokens include OM worker usage where present.</p></div></div>
  <table><thead><tr>{th('Config')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Total cost','num')}{th('Median tokens','num')}{th('OM worker calls','num')}{th('Projection msgs','num')}{th('')}</tr></thead><tbody>{config_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Paired deltas</h2><p>The main positive result is solve count; the main negative result is cost. Statistical tests remain weak at 3 reps.</p></div></div>
  <table><thead><tr>{th('Comparison')}{th('Δ solves','num')}{th('Δ mean partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('cells + / − / =','num')}{th('tests','num')}</tr></thead><tbody>{pair_rows()}</tbody></table>
  <div class='callout'><strong>Read:</strong> delta projection beats stock OM by +6 solves and beats v1 by +1 solve while costing {fmt_money(S[TARGET]['total_combined_cost'] - S['projected-om-gpt54mini-low']['total_combined_cost'], 2)} less in total than v1. But the paired solve p-values are not persuasive, and the clean-baseline cost premium is {fmt_money(S[TARGET]['total_combined_cost'] - S['baseline']['total_combined_cost'], 2)} over 108 cells.</div>
</section>

<section>
  <div class='section-head'><div><h2>Projection mechanics audit</h2><p>This is the strongest result: the new delta path did what it was designed to do.</p></div></div>
  <div class='grid-3'>
    <div class='mini'><span class='big goodtxt'>{delta['projection_cells_with_injection']}/108</span><span class='cap'>cells with delta memory</span></div>
    <div class='mini'><span class='big goodtxt'>{fmt_int(delta['projection_observations'])}</span><span class='cap'>observations injected</span></div>
    <div class='mini'><span class='big goodtxt'>{fmt_int(delta['projection_reflections'])}</span><span class='cap'>reflections injected</span></div>
  </div>
  <div class='bar-list'>{projection_bars()}</div>
  <table style='margin-top:16px'><thead><tr>{th('Projection path')}{th('cells w/ injection','num')}{th('injected rows/messages','num')}{th('total injected chars','num')}{th('median chars/cell','num')}{th('first injection median','num')}{th('payloadShape markers','num')}{th('stock compactions','num')}</tr></thead><tbody>
    <tr><td>v1 provider-instructions rewrite</td><td class='num'>{v1['projection_cells_with_injection']}/108</td><td class='num'>{fmt_int(v1['projection_injected_rows'])}</td><td class='num'>{fmt_int(v1['projection_injected_chars_total'])}</td><td class='num'>{fmt_int(v1['projection_injected_chars_median_cell'])}</td><td class='num'>{v1['projection_first_injection_median']:.0f}</td><td class='num'>{v1['payload_shape_mentions']}</td><td class='num'>{v1['compaction_entries']}</td></tr>
    <tr class='target'><td><strong>delta custom_message path</strong></td><td class='num'>{delta['projection_cells_with_injection']}/108</td><td class='num'>{fmt_int(delta['projection_delta_messages'])}</td><td class='num'>{fmt_int(delta['projection_injected_chars_total'])}</td><td class='num'>{fmt_int(delta['projection_injected_chars_median_cell'])}</td><td class='num'>{delta['projection_first_injection_median']:.0f}</td><td class='num'>{delta['payload_shape_mentions']}</td><td class='num'>{delta['compaction_entries']}</td></tr>
  </tbody></table>
  <div class='callout good'><strong>Mechanically clean:</strong> 0 <code>payloadShape</code> entries, 0 compaction entries, 357 session <code>custom_message</code> entries with <code>customType='om.delta_projection'</code>. This proves executor-visible memory came through the new append-only path, not the old provider-instruction rewrite or stock compaction.</div>
</section>

<div class='grid-2'>
<section>
  <div class='section-head'><div><h2>Difficulty split vs clean baseline</h2><p>Raw solve gains came from medium and hard tasks, not easy tasks.</p></div></div>
  <table><thead><tr>{th('bucket')}{th('n','num')}{th('solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('median Δ cost','num')}</tr></thead><tbody>{difficulty_rows('delta_vs_baseline')}</tbody></table>
</section>
<section>
  <div class='section-head'><div><h2>Difficulty split vs stock OM</h2><p>Projection helped hard/medium solves but lost easy solves relative to stock workers.</p></div></div>
  <table><thead><tr>{th('bucket')}{th('n','num')}{th('solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('median Δ cost','num')}</tr></thead><tbody>{difficulty_rows('delta_vs_stock_om')}</tbody></table>
</section>
</div>

<section>
  <div class='section-head'><div><h2>f2p / p2p health</h2><p>Delta has the best aggregate f2p rate and avoids v1's p2p damage. This supports the claim that v1's repeated instruction rewriting was a bad projection shape.</p></div></div>
  <table><thead><tr>{th('Config')}{th('f2p','num')}{th('f2p rate','num')}{th('p2p','num')}{th('p2p rate','num')}{th('partial < .90','num')}{th('partial ≥ .99','num')}</tr></thead><tbody>{f2p_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Largest movers vs stock OM</h2><p>This isolates the projected-memory content effect over background workers and recall-tool scaffold.</p></div></div>
  <div class='grid-2'>
    <div><h3>Biggest wins</h3><table><thead><tr>{th('Task')}{th('partial','num')}{th('Δ','num')}{th('solve','num')}{th('Δ cost','num')}</tr></thead><tbody>{mover_rows('delta_vs_stock_om','top_wins')}</tbody></table></div>
    <div><h3>Biggest losses</h3><table><thead><tr>{th('Task')}{th('partial','num')}{th('Δ','num')}{th('solve','num')}{th('Δ cost','num')}</tr></thead><tbody>{mover_rows('delta_vs_stock_om','top_losses')}</tbody></table></div>
  </div>
  <div class='callout caution'><strong>Pattern:</strong> wins and losses are threshold-sensitive and sometimes bimodal on the same task family (<code>participle</code>, <code>tengo</code>, <code>go-critic</code>). That is why the solve count moved but the partial-reward statistics stayed noisy.</div>
</section>

<section>
  <div class='section-head'><div><h2>Run health and interpretation</h2></div></div>
  <div class='grid-3'>
    <div class='mini'><span class='big goodtxt'>108/108</span><span class='cap'>result cells present</span></div>
    <div class='mini'><span class='big goodtxt'>0</span><span class='cap'>reward −1 / empty patches</span></div>
    <div class='mini'><span class='big warn'>1</span><span class='cap'>agent timeout, valid patch</span></div>
  </div>
  <div class='callout'><strong>Timeout note:</strong> <code>sql-formatter-bigquery-pipe-formatting rep0</code> hit the agent timeout but produced a valid patch and verifier partial {S[TARGET]['mean_partial'] and '0.999826'}. It is included as a normal scored cell because the patch verified and reward was not −1.</div>
  <div class='callout bad'><strong>Do not overclaim:</strong> this is not evidence that stock pi-observational-memory works in single-shot DeepSWE. Stock compaction still fired 0 times here. The tested memory-content path is the experimental delta projection extension.</div>
</section>

<section>
  <div class='section-head'><div><h2>What I would do next</h2></div></div>
  <div class='callout good'><strong>Keep delta projection as the candidate implementation shape.</strong> It is much more cache-safe than v1 and avoids provider-specific instruction rewriting.</div>
  <div class='callout caution'><strong>Do not promote a public efficacy claim yet.</strong> The right next benchmark is a prompt-clean isolation ladder with the inherited neutral OM sentence removed from every OM config, then either more reps on 36_v2 or a 113-task single-rep diagnostic depending on budget.</div>
  <div class='callout'><strong>Optimization target:</strong> reduce worker/projection overhead. Median combined cost is still {fmt_money(delta['median_combined_cost'],2)} vs clean baseline {fmt_money(base['median_combined_cost'],2)}; the solve gain is not yet strong enough to justify that cost on the Pareto frontier.</div>
</section>

<div class='foot'>
  Generated from <code>analysis/gpt55-low-projected-om-delta-36v2/summary.json</code> · run <code>gpt55-low-projected-om-delta-36v2-r3-w24</code><br />
  Result filter: <code>results/gpt-5.5/low/&lt;config&gt;/&lt;36_v2 task&gt;/rep0..2/result.json</code> · no broad result globs.
</div>
</div>
</body>
</html>
"""

(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html")
