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

KEY_CONFIGS = [
    "baseline",
    "recall-placebo-gpt54mini-low",
    "observational-memory-gpt54mini-low",
    "projected-om-gpt54mini-low",
    "projected-om-delta-gpt54mini-low",
    TARGET,
]

FRONTIER_ROWS = [
    {"label": "Clean stock Pi", "config": "baseline", "solves": S["baseline"]["solves"], "mean_partial": S["baseline"]["mean_partial"], "median_cost": S["baseline"]["median_combined_cost"], "median_tokens": S["baseline"]["median_combined_tokens"], "verdict": "frontier anchor", "kind": "good"},
    {"label": "Workflow-only prompt scaffold", "config": "baseline-wf-only", "solves": 35, "mean_partial": 0.9704, "median_cost": 0.9563, "median_tokens": 729401, "verdict": "dominates target", "kind": "bad"},
    {"label": "Projected OM delta, no orchestration", "config": TARGET, "solves": S[TARGET]["solves"], "mean_partial": S[TARGET]["mean_partial"], "median_cost": S[TARGET]["median_combined_cost"], "median_tokens": S[TARGET]["median_combined_tokens"], "verdict": "not frontier-changing", "kind": "caution"},
    {"label": "Pi codex-goal", "config": "pi-codex-goal", "solves": 48, "mean_partial": 0.9735, "median_cost": 1.972, "median_tokens": 1732978, "verdict": "higher solve tier", "kind": "neutral"},
]


def fmt_int(x):
    return f"{int(round(x)):,}"


def fmt_money(x, digits=2):
    return f"${x:,.{digits}f}"


def fmt_m(x, digits=2):
    return f"{x / 1_000_000:.{digits}f}M"


def fmt_pct(x, digits=1):
    return f"{100 * x:.{digits}f}%"


def fmt_float(x, digits=4):
    return f"{x:.{digits}f}"


def sign(x, digits=4, money=False, integer=False):
    if integer:
        body = f"{int(round(abs(x))):,}"
    elif money:
        body = fmt_money(abs(x), 3)
    else:
        body = f"{abs(x):.{digits}f}"
    return ("+" if x >= 0 else "−") + body


def pval(x):
    return "—" if x is None else f"p={x:.3f}"


def cls_delta(x, higher=True):
    if abs(x) < 1e-12:
        return "neutral"
    good = x > 0 if higher else x < 0
    return "good" if good else "bad"


def pill(text, kind="neutral"):
    return f"<span class='pill {kind}'>{html.escape(text)}</span>"


def tag(text, kind="neutral"):
    return f"<span class='tag {kind}'>{html.escape(text)}</span>"


def tr(cells, cls=""):
    return f"<tr class='{cls}'>" + "".join(cells) + "</tr>"


def td(x, cls=""):
    return f"<td class='{cls}'>{x}</td>"


def th(x, cls=""):
    return f"<th class='{cls}'>{x}</th>"


def config_table():
    rows = []
    for c in KEY_CONFIGS:
        m = S[c]
        rows.append(tr([
            td(html.escape(LABELS[c])),
            td(f"{m['solves']}/108", "num"),
            td(fmt_float(m["mean_partial"]), "num"),
            td(fmt_money(m["median_combined_cost"], 3), "num"),
            td(fmt_money(m["total_combined_cost"], 2), "num"),
            td(fmt_int(m["median_combined_tokens"]), "num"),
            td(fmt_int(m["om_worker_calls"]), "num"),
            td(fmt_int(m.get("projection_delta_messages") or 0), "num"),
            td(tag("target", "good") if c == TARGET else ""),
        ], "target" if c == TARGET else ""))
    return "\n".join(rows)


def pair_table():
    keys = [
        "delta_vs_baseline",
        "delta_vs_recall_placebo",
        "delta_vs_stock_om",
        "delta_vs_projected_v1",
        "delta_vs_delta_neutral_sentence",
    ]
    names = {
        "delta_vs_baseline": "vs clean baseline",
        "delta_vs_recall_placebo": "vs recall placebo",
        "delta_vs_stock_om": "vs stock OM workers",
        "delta_vs_projected_v1": "vs projected OM v1",
        "delta_vs_delta_neutral_sentence": "vs delta + neutral sentence",
    }
    rows = []
    for k in keys:
        p = P[k]
        rows.append(tr([
            td(f"<strong>{names[k]}</strong><br><span class='muted'>{html.escape(p['other_label'])} compared with {html.escape(p['base_label'])}</span>"),
            td(sign(p["solve_delta"], integer=True), f"num {cls_delta(p['solve_delta'])}"),
            td(sign(p["mean_delta_partial"], 4), f"num {cls_delta(p['mean_delta_partial'])}"),
            td(f"{p['other_only']} gained / {p['base_only']} lost", "num"),
            td(sign(p["median_delta_combined_cost_usd"], money=True), f"num {cls_delta(p['median_delta_combined_cost_usd'], higher=False)}"),
            td(sign(p["median_delta_combined_total_tokens"], integer=True), f"num {cls_delta(p['median_delta_combined_total_tokens'], higher=False)}"),
            td(f"{p['improved_cells']} / {p['worsened_cells']} / {p['tied_cells']}", "num"),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", "num"),
        ]))
    return "\n".join(rows)


def difficulty_rows(pair_key):
    rows = []
    p = P[pair_key]
    for bucket in ["hard", "medium", "easy"]:
        d = p["difficulty"][bucket]
        rows.append(tr([
            td(bucket.title()),
            td(str(d["n"]), "num"),
            td(f"{d['base_solves']} → {d['other_solves']}", "num"),
            td(sign(d["solve_delta"], integer=True), f"num {cls_delta(d['solve_delta'])}"),
            td(sign(d["mean_delta_partial"], 4), f"num {cls_delta(d['mean_delta_partial'])}"),
            td(sign(d["median_delta_cost"], money=True), f"num {cls_delta(d['median_delta_cost'], higher=False)}"),
            td(sign(d["median_delta_tokens"], integer=True), f"num {cls_delta(d['median_delta_tokens'], higher=False)}"),
        ]))
    return "\n".join(rows)


def projection_table():
    rows = []
    for c in ["projected-om-gpt54mini-low", "projected-om-delta-gpt54mini-low", TARGET]:
        m = S[c]
        rows.append(tr([
            td(html.escape(LABELS[c])),
            td(f"{m['projection_cells_with_injection']}/108", "num"),
            td(fmt_int(m["projection_injected_rows"]), "num"),
            td(fmt_int(m.get("projection_delta_messages") or 0), "num"),
            td(fmt_int(m["projection_injected_chars_total"]), "num"),
            td(fmt_int(m["projection_injected_chars_median_cell"]), "num"),
            td(fmt_int(m["projection_observations"]), "num"),
            td(fmt_int(m["projection_reflections"]), "num"),
            td(fmt_int(m["payload_shape_mentions"]), "num"),
        ], "target" if c == TARGET else ""))
    return "\n".join(rows)


def f2p_table():
    rows = []
    for c in ["baseline", "observational-memory-gpt54mini-low", "projected-om-delta-gpt54mini-low", TARGET]:
        m = S[c]
        rows.append(tr([
            td(html.escape(LABELS[c])),
            td(f"{fmt_int(m['f2p_passed'])}/{fmt_int(m['f2p_total'])}", "num"),
            td(fmt_pct(m["f2p_rate"], 2), "num"),
            td(f"{fmt_int(m['p2p_passed'])}/{fmt_int(m['p2p_total'])}", "num"),
            td(fmt_pct(m["p2p_rate"], 3), "num"),
            td(str(m["partial_lt_09"]), "num"),
            td(str(m["partial_ge_099"]), "num"),
        ], "target" if c == TARGET else ""))
    return "\n".join(rows)


def mover_rows(pair_key, which, n=8):
    rows = []
    for x in P[pair_key][which][:n]:
        delta = x["delta_partial"]
        rows.append(tr([
            td(f"<strong>{html.escape(x['title'])}</strong><br><span class='muted t-mono'>{html.escape(x['task'])} · rep{x['rep']} · {x['difficulty']}</span>"),
            td(f"{x['base_partial']:.3f} → {x['other_partial']:.3f}", "num"),
            td(sign(delta, 3), f"num {cls_delta(delta)}"),
            td(("✓" if x["base_solved"] else "—") + " → " + ("✓" if x["other_solved"] else "—"), "num"),
            td(sign(x["delta_cost"], money=True), f"num {cls_delta(x['delta_cost'], higher=False)}"),
        ]))
    return "\n".join(rows)


def frontier_table():
    rows = []
    for r in FRONTIER_ROWS:
        rows.append(tr([
            td(f"<strong>{html.escape(r['label'])}</strong><br><span class='muted t-mono'>{html.escape(r['config'])}</span>"),
            td(f"{r['solves']}/108", "num"),
            td(fmt_float(r["mean_partial"]), "num"),
            td(fmt_money(r["median_cost"], 3), "num"),
            td(fmt_int(r["median_tokens"]), "num"),
            td(tag(r["verdict"], r["kind"])),
        ], "target" if r["config"] == TARGET else ""))
    return "\n".join(rows)


def bar(label, value, maxv, kind="blue", sub=""):
    width = 0 if maxv == 0 else max(1, min(100, value / maxv * 100))
    return f"<div class='bar-row'><div class='bar-label'>{html.escape(label)}</div><div><div class='bar-track'><div class='bar-fill {kind}' style='width:{width:.2f}%'></div></div><div class='vals'><span>{fmt_int(value)}</span><span>{html.escape(sub)}</span></div></div></div>"


def projection_bars():
    v1 = S["projected-om-gpt54mini-low"]
    neutral = S["projected-om-delta-gpt54mini-low"]
    target = S[TARGET]
    max_chars = max(v1["projection_injected_chars_total"], neutral["projection_injected_chars_total"], target["projection_injected_chars_total"])
    return "".join([
        bar("v1 provider rewrite", v1["projection_injected_chars_total"], max_chars, "red", "chars injected"),
        bar("delta + neutral sentence", neutral["projection_injected_chars_total"], max_chars, "green", "chars injected"),
        bar("delta / no orchestration", target["projection_injected_chars_total"], max_chars, "green", "chars injected"),
    ])


base = S["baseline"]
stock = S["observational-memory-gpt54mini-low"]
neutral = S["projected-om-delta-gpt54mini-low"]
target = S[TARGET]
vs_base = P["delta_vs_baseline"]
vs_stock = P["delta_vs_stock_om"]
vs_neutral = P["delta_vs_delta_neutral_sentence"]

html_doc = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8' />
<meta name='viewport' content='width=device-width, initial-scale=1' />
<title>Projected OM delta no-orchestration · GPT-5.5 low · DeepSWE report</title>
<style>
:root {{
  --bg:#f4f7fb; --surface:#ffffff; --surface-2:#f8fafc; --ink:#102033; --muted:#607086;
  --line:#d9e1ec; --blue:#335dff; --blue-2:#1d3fb8; --green:#178a5b; --green-soft:#e7f7ef;
  --red:#d0473f; --red-soft:#fdeceb; --amber:#c58a00; --amber-soft:#fff4d8;
  --shadow:0 24px 60px rgba(14,30,62,.08); --shadow-sm:0 10px 30px rgba(14,30,62,.06);
  --radius-xl:28px; --radius-lg:20px; --radius-md:14px; --max:1280px;
}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}
.hero,section{{background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}
.hero{{padding:clamp(24px,4vw,42px);overflow:hidden;position:relative}} .eyebrow{{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}
h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.05}} h1{{font-size:clamp(2rem,4.6vw,3.9rem);margin-top:14px;max-width:19ch}} h2{{font-size:clamp(1.35rem,2.2vw,2rem)}} h3{{font-size:1.05rem;margin-bottom:8px}}
.subtitle{{max-width:84ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.08rem);margin:14px 0 0}}
.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}} .pill{{display:inline-flex;align-items:center;gap:8px;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line);color:#31415d}} .pill.good{{background:var(--green-soft);color:var(--green);border-color:rgba(23,138,91,.16)}} .pill.bad{{background:var(--red-soft);color:var(--red);border-color:rgba(208,71,63,.16)}} .pill.caution{{background:var(--amber-soft);color:var(--amber);border-color:rgba(197,138,0,.16)}} .pill.neutral{{background:#eef3ff;color:var(--blue-2);border-color:rgba(51,93,255,.16)}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:26px}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:16px;min-height:118px;box-shadow:var(--shadow-sm)}} .stat .label{{display:block;color:var(--muted);font-size:12px;font-weight:850;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}} .stat .value{{display:block;font-size:clamp(1.25rem,2vw,1.9rem);font-weight:900;letter-spacing:-.04em}} .stat .sub{{display:block;margin-top:8px;font-size:.9rem;color:var(--muted);font-weight:650}}
.goodtxt,.good{{color:var(--green)}} .badtxt,.bad{{color:var(--red)}} .warn{{color:var(--amber)}} .neut{{color:var(--blue-2)}}
section{{margin-top:20px;padding:clamp(18px,3vw,28px)}} .section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}} .section-head p{{margin:6px 0 0;color:var(--muted);max-width:78ch}}
table{{width:100%;border-collapse:collapse;font-size:.94rem;min-width:0}} th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}} td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} tbody tr:hover{{background:var(--surface-2)}} tr.target{{background:#f4fbf7}}
.t-mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}} .muted{{color:var(--muted)}} code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.93em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}}
.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;color:#22314d;margin-top:14px}} .callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}} .callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}} .callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}} .callout strong{{color:var(--blue-2)}}
.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}
.mini{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;text-align:center;box-shadow:var(--shadow-sm)}} .mini .big{{display:block;font-size:2rem;font-weight:900;letter-spacing:-.04em}} .mini .cap{{display:block;color:var(--muted);font-size:12px;font-weight:850;text-transform:uppercase;letter-spacing:.06em;margin-top:6px}}
.tag{{display:inline-flex;padding:4px 10px;border-radius:999px;font-size:.78rem;font-weight:850;letter-spacing:.03em;text-transform:uppercase}} .tag.good{{background:var(--green-soft);color:var(--green)}} .tag.bad{{background:var(--red-soft);color:var(--red)}} .tag.neutral{{background:#eef3ff;color:var(--blue-2)}} .tag.caution{{background:var(--amber-soft);color:var(--amber)}}
.bar-list{{display:grid;gap:14px;margin-top:8px}} .bar-row{{display:grid;grid-template-columns:210px 1fr;gap:14px;align-items:center}} .bar-label{{font-weight:850;color:#22314d;font-size:14px}} .bar-track{{position:relative;height:18px;border-radius:999px;background:#edf2f7;overflow:hidden;border:1px solid #dde5ef}} .bar-fill{{position:absolute;inset:0 auto 0 0;border-radius:inherit}} .bar-fill.blue{{background:linear-gradient(90deg,#6f8cff,#244de0)}} .bar-fill.green{{background:linear-gradient(90deg,#45bf81,#178a5b)}} .bar-fill.red{{background:linear-gradient(90deg,#f1786f,#d0473f)}} .vals{{display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);font-weight:700;font-variant-numeric:tabular-nums;margin-top:4px}}
.foot{{margin-top:26px;color:var(--muted);font-size:.86rem;text-align:center}}
@media (max-width:900px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.grid-2,.grid-3{{grid-template-columns:1fr}}table{{font-size:.84rem}}th,td{{padding:8px 7px}}.bar-row{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class='wrap'>
<header class='hero'>
  <span class='eyebrow'>DeepSWE · GPT-5.5 low · 36_v2 × 3 reps</span>
  <h1>No-orchestration projected OM is cleaner, cheaper, and still noisy.</h1>
  <p class='subtitle'>This run removed the inherited neutral OM sentence and kept only extension-owned surfaces: the recall tool, GPT‑5.4‑mini low memory workers, and cache-safe delta projections inserted as executor-visible custom messages. It is the cleanest projected-OM run so far, but it still does not clearly expand the solve/cost frontier.</p>
  <div class='pillrow'>
    {pill('108/108 result cells', 'good')}
    {pill('0 empty patches / 0 reward=-1', 'good')}
    {pill('+7 solves vs clean baseline', 'neutral')}
    {pill('+2 solves vs neutral delta', 'neutral')}
    {pill('p-values not decisive', 'caution')}
    {pill('no provider rewrite', 'good')}
  </div>
  <div class='stats'>
    <div class='stat'><span class='label'>Target solves</span><span class='value'>{target['solves']}/108</span><span class='sub neut'>{sign(vs_base['solve_delta'], integer=True)} vs clean baseline</span></div>
    <div class='stat'><span class='label'>Mean partial</span><span class='value'>{fmt_float(target['mean_partial'])}</span><span class='sub neut'>{sign(vs_base['mean_delta_partial'], 4)} vs baseline</span></div>
    <div class='stat'><span class='label'>Median combined cost</span><span class='value'>{fmt_money(target['median_combined_cost'], 2)}</span><span class='sub badtxt'>{sign(vs_base['median_delta_combined_cost_usd'], money=True)} vs baseline</span></div>
    <div class='stat'><span class='label'>Memory projection</span><span class='value'>{fmt_int(target['projection_delta_messages'])}</span><span class='sub goodtxt'>custom_message deltas, 0 provider rewrites</span></div>
    <div class='stat'><span class='label'>Worker cost</span><span class='value'>{fmt_money(target['om_worker_cost'], 2)}</span><span class='sub'>{fmt_m(target['om_worker_tokens'])} worker tokens</span></div>
  </div>
</header>

<section>
  <div class='section-head'><div><h2>Verdict</h2><p>Mechanically successful; directionally useful; not yet a Pareto win.</p></div></div>
  <div class='grid-3'>
    <div class='callout good'><strong>Cleanliness improved.</strong> The config has no <code>system_preamble.md</code>, no <code>orchestration.md</code>, and result metadata records <code>append_system_prompt_chars=0</code>. A search found no inherited “Observational memory is enabled…” sentence in the target results.</div>
    <div class='callout good'><strong>Projection design improved.</strong> The target used 332 delta custom messages and 453,735 injected chars. The old v1 provider-rewrite path used 2,671 repeated injections and 9,480,710 chars.</div>
    <div class='callout caution'><strong>Outcome is still noisy.</strong> Versus clean baseline it gained 7 solves, but McNemar is {pval(vs_base['mcnemar_p'])} and partial-reward Wilcoxon is {pval(vs_base['wilcoxon_partial_p'])}. Treat this as a promising direction, not proof.</div>
  </div>
  <div class='callout bad'><strong>Frontier note:</strong> on this slice, <code>baseline-wf-only</code> also solved 35/108 with higher mean partial and lower median cost. So this run does not move the broad solve/cost frontier, even though it is a cleaner memory-specific treatment than the earlier OM runs.</div>
</section>

<section>
  <div class='section-head'><div><h2>Run health and treatment validation</h2><p>The run completed cleanly. The one dashboard “skipped” batch cell is the smoke cell reused by the batch scheduler; all 108 target result files exist.</p></div></div>
  <div class='grid-3'>
    <div class='mini'><span class='big'>108</span><span class='cap'>result.json files</span></div>
    <div class='mini'><span class='big'>0</span><span class='cap'>transient errors</span></div>
    <div class='mini'><span class='big'>0</span><span class='cap'>timeouts / empty patches / reward=-1</span></div>
  </div>
  <div class='callout'><strong>Resolved treatment:</strong> main executor <code>openai-codex/gpt-5.5</code> thinking low; OM observer/reflector workers <code>openai-codex/gpt-5.4-mini</code> thinking low; <code>passive=false</code>; <code>observeAfterTokens=10000</code>; <code>reflectAfterTokens=20000</code>; <code>compactAfterTokens=81000</code>; <code>debugLog=true</code>. Dropper did not run.</div>
</section>

<section>
  <div class='section-head'><div><h2>Headline comparison</h2><p>All token and cost columns use combined metrics where available, so OM worker usage is included.</p></div></div>
  <table><thead><tr>{th('Config')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Total cost','num')}{th('Median tokens','num')}{th('Worker calls','num')}{th('Projection msgs','num')}{th('')}</tr></thead><tbody>{config_table()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Paired deltas</h2><p>The important comparison is not just “target vs clean baseline.” The ladder shows what projection adds over recall scaffolding, stock workers, and the previous delta run with the neutral sentence.</p></div></div>
  <table><thead><tr>{th('Comparison')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Solve flips','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('Cells + / − / =','num')}{th('Tests','num')}</tr></thead><tbody>{pair_table()}</tbody></table>
  <div class='callout'><strong>Best causal read:</strong> compared with stock OM workers, no-orchestration delta projection gains 8 solves, mostly in hard and medium buckets, with almost no median token increase. Compared with the previous neutral-sentence delta run, it gains 2 solves and gets cheaper, but the cell-level flips are mixed.</div>
</section>

<section>
  <div class='section-head'><div><h2>Difficulty split</h2><p>Versus clean baseline, the solve gains came mainly from medium and hard tasks, not easy tasks.</p></div></div>
  <div class='grid-3'>
    <div><h3>Target vs clean baseline</h3><table><thead><tr>{th('Bucket')}{th('n','num')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Δ cost','num')}{th('Δ tokens','num')}</tr></thead><tbody>{difficulty_rows('delta_vs_baseline')}</tbody></table></div>
    <div><h3>Target vs stock OM</h3><table><thead><tr>{th('Bucket')}{th('n','num')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Δ cost','num')}{th('Δ tokens','num')}</tr></thead><tbody>{difficulty_rows('delta_vs_stock_om')}</tbody></table></div>
    <div><h3>Target vs neutral delta</h3><table><thead><tr>{th('Bucket')}{th('n','num')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Δ cost','num')}{th('Δ tokens','num')}</tr></thead><tbody>{difficulty_rows('delta_vs_delta_neutral_sentence')}</tbody></table></div>
  </div>
</section>

<section>
  <div class='section-head'><div><h2>Projection mechanics</h2><p>This is the strongest result: delta projection removed most repeated prompt burden while keeping memory executor-visible.</p></div></div>
  <div class='grid-2'>
    <div><table><thead><tr>{th('Projection config')}{th('Cells','num')}{th('Rows','num')}{th('Custom msgs','num')}{th('Total chars','num')}{th('Median chars/cell','num')}{th('Obs','num')}{th('Refl','num')}{th('Payload rewrites','num')}</tr></thead><tbody>{projection_table()}</tbody></table></div>
    <div><div class='bar-list'>{projection_bars()}</div><div class='callout good'><strong>No-orchestration target:</strong> 108 projection logs, 104 cells with injected memory, median first injection request 13.5, 0 stock Pi compactions, 0 <code>om.folded</code> compaction records, and 0 <code>payloadShape</code> rewrite markers.</div></div>
  </div>
</section>

<section>
  <div class='section-head'><div><h2>Verifier health</h2><p>No-orchestration has the best f2p rate in this ladder, but its p2p health falls back near clean baseline. That suggests the gain is not a simple uniform correctness lift.</p></div></div>
  <table><thead><tr>{th('Config')}{th('f2p','num')}{th('f2p rate','num')}{th('p2p','num')}{th('p2p rate','num')}{th('Partial < .9','num')}{th('Partial ≥ .99','num')}</tr></thead><tbody>{f2p_table()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Top movers vs clean baseline</h2><p>Large positive movement is concentrated in a few tasks. Some losses are threshold flips on already strong baseline cells.</p></div></div>
  <div class='grid-2'>
    <div><h3>Largest partial wins</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}{th('Solved','num')}{th('Δ cost','num')}</tr></thead><tbody>{mover_rows('delta_vs_baseline','top_wins')}</tbody></table></div>
    <div><h3>Largest partial losses</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}{th('Solved','num')}{th('Δ cost','num')}</tr></thead><tbody>{mover_rows('delta_vs_baseline','top_losses')}</tbody></table></div>
  </div>
</section>

<section>
  <div class='section-head'><div><h2>What changed when the neutral sentence was removed?</h2><p>Removing the config-authored sentence did not hurt aggregate performance. It made the run cheaper and slightly better on solves, but the individual cell flips remain noisy.</p></div></div>
  <div class='grid-2'>
    <div><h3>Wins vs neutral-sentence delta</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}{th('Solved','num')}{th('Δ cost','num')}</tr></thead><tbody>{mover_rows('delta_vs_delta_neutral_sentence','top_wins')}</tbody></table></div>
    <div><h3>Losses vs neutral-sentence delta</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}{th('Solved','num')}{th('Δ cost','num')}</tr></thead><tbody>{mover_rows('delta_vs_delta_neutral_sentence','top_losses')}</tbody></table></div>
  </div>
  <div class='callout caution'><strong>Key outlier:</strong> fastapi-deprecation-response-headers rep2 collapsed from 0.997 to 0.041 versus the neutral-sentence delta run, while several hard/medium cells improved. This is why the aggregate mean barely moves despite +2 net solves.</div>
</section>

<section>
  <div class='section-head'><div><h2>Pareto context</h2><p>This is a memory-specific improvement, not a broad frontier expansion.</p></div></div>
  <table><thead><tr>{th('Run')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Median tokens','num')}{th('Read')}</tr></thead><tbody>{frontier_table()}</tbody></table>
  <div class='callout bad'><strong>Bottom line:</strong> no-orchestration projected OM is cleaner than the previous OM configs and improves over clean baseline, but <code>baseline-wf-only</code> reaches the same solve count with lower cost and higher mean partial. So this run is not the answer to the project’s Pareto-frontier question yet.</div>
</section>

<section>
  <div class='section-head'><div><h2>Recommended next step</h2><p>Do not rerun blindly. The mechanism is now clean enough to tune.</p></div></div>
  <div class='grid-2'>
    <div class='callout good'><strong>Keep:</strong> delta custom-message projection. It is much cheaper than provider-instruction rewrite and it actually reaches the executor without waiting for stock compaction.</div>
    <div class='callout caution'><strong>Change:</strong> reduce noisy projection volume and target when memory appears. Reflections had the clearest earlier correlation signal, but this no-orch run shows no strong simple correlation between injected rows/chars and reward.</div>
  </div>
  <div class='callout'><strong>Decision:</strong> the next clean experiment should not restore any config-authored orchestration text. If we continue OM, test projection selection policy: reflections-first, smaller cap, fewer observation repeats, and possibly task-state-aware injection timing.</div>
</section>

<div class='foot'>Sources: <code>analysis/gpt55-low-projected-om-delta-no-orch-36v2/summary.json</code>, <code>results/_runs/gpt55-low-projected-om-delta-no-orch-36v2-r3-w24/status.json</code>, and target result/session/projection artifacts under <code>results/gpt-5.5/low/{html.escape(TARGET)}/</code>.</div>
</div>
</body>
</html>
"""

(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html")
