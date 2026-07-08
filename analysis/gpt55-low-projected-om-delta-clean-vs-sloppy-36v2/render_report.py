#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "summary.json").read_text())
OLD = DATA["old_config"]
NEW = DATA["new_config"]
OLD_LABEL = DATA["old_label"]
NEW_LABEL = DATA["new_label"]
S = DATA["summaries"]
P = DATA["pair"]
old = S[OLD]
new = S[NEW]


def fmt_int(x):
    return f"{int(round(x)):,}"


def fmt_money(x, digits=3):
    return f"${x:,.{digits}f}"


def fmt_pct(x, digits=1):
    return f"{100*x:.{digits}f}%"


def fmt_float(x, digits=4):
    return f"{x:.{digits}f}"


def sign(x, digits=4, money=False, integer=False):
    if integer:
        body = fmt_int(abs(x))
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


def td(x, cls=""):
    return f"<td class='{cls}'>{x}</td>"


def th(x, cls=""):
    return f"<th class='{cls}'>{x}</th>"


def tr(cells, cls=""):
    return f"<tr class='{cls}'>" + "".join(cells) + "</tr>"


def metric_table():
    rows = []
    metrics = [
        ("Solves", f"{old['solves']}/108", f"{new['solves']}/108", P["solve_delta"], True, True),
        ("Mean partial", fmt_float(old["mean_partial"]), fmt_float(new["mean_partial"]), P["mean_delta_partial"], True, False),
        ("Median combined cost", fmt_money(old["median_combined_cost"]), fmt_money(new["median_combined_cost"]), P["median_delta_combined_cost_usd"], False, False),
        ("Total combined cost", fmt_money(old["total_combined_cost"], 2), fmt_money(new["total_combined_cost"], 2), new["total_combined_cost"] - old["total_combined_cost"], False, False),
        ("Median combined tokens", fmt_int(old["median_combined_tokens"]), fmt_int(new["median_combined_tokens"]), P["median_delta_combined_total_tokens"], False, True),
        ("Total combined tokens", fmt_int(old["total_combined_tokens"]), fmt_int(new["total_combined_tokens"]), new["total_combined_tokens"] - old["total_combined_tokens"], False, True),
        ("Median turns", fmt_int(old["median_turns"]), fmt_int(new["median_turns"]), P["median_delta_turns"], False, True),
        ("Median tool calls", fmt_int(old["median_tool_calls"]), fmt_int(new["median_tool_calls"]), P["median_delta_tool_calls"], False, True),
        ("Worker calls", fmt_int(old["om_worker_calls"]), fmt_int(new["om_worker_calls"]), new["om_worker_calls"] - old["om_worker_calls"], False, True),
        ("Worker cost", fmt_money(old["om_worker_cost"]), fmt_money(new["om_worker_cost"]), new["om_worker_cost"] - old["om_worker_cost"], False, False),
        ("Agent timeouts", str(old["agent_timeouts"]), str(new["agent_timeouts"]), new["agent_timeouts"] - old["agent_timeouts"], False, True),
    ]
    for label, o, n, d, higher, integer in metrics:
        dstr = sign(d, money=("cost" in label.lower()), integer=integer)
        rows.append(tr([td(label), td(o, "num"), td(n, "num"), td(dstr, f"num {cls_delta(d, higher=higher)}")]))
    return "\n".join(rows)


def treatment_table():
    rows = [
        ("Config-authored orchestration", "present", "absent", "The only treatment file removed."),
        ("Exact appended sentence", "present in 108/108 provider requests", "present in 0/108 provider requests", "Confirmed through initial_context captures."),
        ("Median system prompt chars", fmt_int(old["prompt_system_chars_median"]), fmt_int(new["prompt_system_chars_median"]), "−146 chars"),
        ("Median append_system_prompt_chars", fmt_int(old["append_system_prompt_chars_median"]), fmt_int(new["append_system_prompt_chars_median"]), "−144 chars"),
        ("Pi flags", "same", "same", "Same OM extension, worker-usage trace, and delta projection extension."),
        ("OM settings", "same", "same", "Same GPT-5.4-mini low workers and thresholds."),
        ("Projection mechanism", "same", "same", "Both use delta custom-message projection, not provider-instruction rewrite."),
    ]
    return "\n".join(tr([td(a), td(b), td(c), td(d)]) for a,b,c,d in rows)


def pair_table():
    rows = [
        ("Solve agreement", f"both {P['both_solved']} · sloppy-only {P['old_only']} · clean-only {P['new_only']} · neither {P['neither']}", "12 clean-only, 10 sloppy-only"),
        ("Binary test", pval(P["mcnemar_p"]), "No reliable binary win at 3 reps."),
        ("Partial reward test", pval(P["wilcoxon_partial_p"]), "No reliable partial-reward shift."),
        ("Cell movement", f"{P['improved_cells']} improved · {P['worsened_cells']} worsened · {P['tied_cells']} tied", "More cells worsened than improved, but solve flips favored clean."),
        ("Rep-level solve deltas", ", ".join(sign(x, integer=True) for x in P["rep_values_solve_delta"]), "Per-rep solve deltas were +1, −1, +2."),
        ("Rep-level partial deltas", ", ".join(sign(x, 4) for x in P["rep_values_partial_delta"]), "Mixed: one positive rep between two negative reps."),
        ("Mean partial without fastapi outlier", "+0.0102", "The largest clean-run loss masks the direction of the rest."),
    ]
    return "\n".join(tr([td(a), td(b, "num" if a.endswith("test") else ""), td(c)]) for a,b,c in rows)


def difficulty_rows():
    rows = []
    for bucket in ["hard", "medium", "easy"]:
        d = P["difficulty"][bucket]
        rows.append(tr([
            td(bucket.title()),
            td(str(d["n"]), "num"),
            td(f"{d['old_solves']} → {d['new_solves']}", "num"),
            td(sign(d["solve_delta"], integer=True), f"num {cls_delta(d['solve_delta'])}"),
            td(sign(d["mean_delta_partial"], 4), f"num {cls_delta(d['mean_delta_partial'])}"),
            td(sign(d["median_delta_cost"], money=True), f"num {cls_delta(d['median_delta_cost'], higher=False)}"),
            td(sign(d["median_delta_tokens"], integer=True), f"num {cls_delta(d['median_delta_tokens'], higher=False)}"),
        ]))
    return "\n".join(rows)


def projection_table():
    rows = []
    metrics = [
        ("Cells with injection", f"{old['projection_cells_with_injection']}/108", f"{new['projection_cells_with_injection']}/108", new['projection_cells_with_injection'] - old['projection_cells_with_injection'], True),
        ("Projection rows", fmt_int(old['projection_rows']), fmt_int(new['projection_rows']), new['projection_rows'] - old['projection_rows'], False),
        ("Injected delta messages", fmt_int(old['projection_delta_messages']), fmt_int(new['projection_delta_messages']), new['projection_delta_messages'] - old['projection_delta_messages'], False),
        ("Injected chars", fmt_int(old['projection_injected_chars_total']), fmt_int(new['projection_injected_chars_total']), new['projection_injected_chars_total'] - old['projection_injected_chars_total'], False),
        ("Median injected chars/cell", fmt_int(old['projection_injected_chars_median_cell']), fmt_int(new['projection_injected_chars_median_cell']), new['projection_injected_chars_median_cell'] - old['projection_injected_chars_median_cell'], False),
        ("Injected observations", fmt_int(old['projection_observations']), fmt_int(new['projection_observations']), new['projection_observations'] - old['projection_observations'], False),
        ("Injected reflections", fmt_int(old['projection_reflections']), fmt_int(new['projection_reflections']), new['projection_reflections'] - old['projection_reflections'], False),
        ("Payload rewrite markers", fmt_int(old['payload_shape_mentions']), fmt_int(new['payload_shape_mentions']), new['payload_shape_mentions'] - old['payload_shape_mentions'], False),
    ]
    for label, o, n, d, higher in metrics:
        rows.append(tr([td(label), td(o, "num"), td(n, "num"), td(sign(d, integer=True), f"num {cls_delta(d, higher=higher)}")]))
    return "\n".join(rows)


def verifier_table():
    rows = []
    metrics = [
        ("f2p", f"{fmt_int(old['f2p_passed'])}/{fmt_int(old['f2p_total'])}", f"{fmt_int(new['f2p_passed'])}/{fmt_int(new['f2p_total'])}", new['f2p_passed'] - old['f2p_passed'], True),
        ("f2p rate", fmt_pct(old['f2p_passed']/old['f2p_total'], 2), fmt_pct(new['f2p_passed']/new['f2p_total'], 2), new['f2p_passed']/new['f2p_total'] - old['f2p_passed']/old['f2p_total'], True),
        ("p2p", f"{fmt_int(old['p2p_passed'])}/{fmt_int(old['p2p_total'])}", f"{fmt_int(new['p2p_passed'])}/{fmt_int(new['p2p_total'])}", new['p2p_passed'] - old['p2p_passed'], True),
        ("p2p rate", fmt_pct(old['p2p_passed']/old['p2p_total'], 3), fmt_pct(new['p2p_passed']/new['p2p_total'], 3), new['p2p_passed']/new['p2p_total'] - old['p2p_passed']/old['p2p_total'], True),
        ("Partial < .9", str(old['partial_lt_09']), str(new['partial_lt_09']), new['partial_lt_09'] - old['partial_lt_09'], False),
        ("Partial ≥ .99", str(old['partial_ge_099']), str(new['partial_ge_099']), new['partial_ge_099'] - old['partial_ge_099'], True),
    ]
    for label, o, n, d, higher in metrics:
        rows.append(tr([td(label), td(o, "num"), td(n, "num"), td(sign(d, 4, integer=isinstance(d, int)), f"num {cls_delta(d, higher=higher)}")]))
    return "\n".join(rows)


def solve_flip_rows(items):
    rows = []
    for x in sorted(items, key=lambda z: (z["difficulty"], z["task"], z["rep"])):
        rows.append(tr([
            td(f"<strong>{html.escape(x['title'])}</strong><br><span class='muted t-mono'>{html.escape(x['task'])} · rep{x['rep']} · {x['difficulty']}</span>"),
            td(f"{x['old_partial']:.3f} → {x['new_partial']:.3f}", "num"),
            td(sign(x["delta_partial"], 3), f"num {cls_delta(x['delta_partial'])}"),
            td(sign(x["delta_cost"], money=True), f"num {cls_delta(x['delta_cost'], higher=False)}"),
        ]))
    return "\n".join(rows)


def task_mean_rows(which, n=8):
    rows = []
    tasks = DATA["task_level"]
    tasks = sorted(tasks, key=lambda x: x["mean_delta_partial"], reverse=(which == "wins"))[:n]
    for x in tasks:
        rows.append(tr([
            td(f"<strong>{html.escape(x['title'])}</strong><br><span class='muted t-mono'>{html.escape(x['task'])} · {x['difficulty']}</span>"),
            td(f"{x['old_mean_partial']:.3f} → {x['new_mean_partial']:.3f}", "num"),
            td(sign(x["mean_delta_partial"], 3), f"num {cls_delta(x['mean_delta_partial'])}"),
            td(f"{x['old_solves']} → {x['new_solves']}", "num"),
            td(sign(x["median_delta_cost"], money=True), f"num {cls_delta(x['median_delta_cost'], higher=False)}"),
        ]))
    return "\n".join(rows)


html_doc = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8' />
<meta name='viewport' content='width=device-width, initial-scale=1' />
<title>Clean vs sloppy projected OM delta · DeepSWE report</title>
<style>
:root {{ --bg:#f4f7fb; --surface:#fff; --surface-2:#f8fafc; --ink:#102033; --muted:#607086; --line:#d9e1ec; --blue:#335dff; --blue-2:#1d3fb8; --green:#178a5b; --green-soft:#e7f7ef; --red:#d0473f; --red-soft:#fdeceb; --amber:#c58a00; --amber-soft:#fff4d8; --shadow:0 24px 60px rgba(14,30,62,.08); --shadow-sm:0 10px 30px rgba(14,30,62,.06); --radius-xl:28px; --radius-lg:20px; --max:1280px; }}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}} .hero,section{{background:rgba(255,255,255,.93);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}} .hero{{padding:clamp(24px,4vw,42px)}}
.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}
h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.05}} h1{{font-size:clamp(2rem,4.5vw,3.8rem);margin-top:14px;max-width:18ch}} h2{{font-size:clamp(1.35rem,2.2vw,2rem)}} h3{{font-size:1.05rem;margin-bottom:8px}}
.subtitle{{max-width:86ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.08rem);margin:14px 0 0}}
.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}} .pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line);color:#31415d}} .pill.good{{background:var(--green-soft);color:var(--green);border-color:rgba(23,138,91,.16)}} .pill.bad{{background:var(--red-soft);color:var(--red);border-color:rgba(208,71,63,.16)}} .pill.caution{{background:var(--amber-soft);color:var(--amber);border-color:rgba(197,138,0,.16)}} .pill.neutral{{background:#eef3ff;color:var(--blue-2);border-color:rgba(51,93,255,.16)}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:26px}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:16px;min-height:118px;box-shadow:var(--shadow-sm)}} .stat .label{{display:block;color:var(--muted);font-size:12px;font-weight:850;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}} .stat .value{{display:block;font-size:clamp(1.25rem,2vw,1.9rem);font-weight:900;letter-spacing:-.04em}} .stat .sub{{display:block;margin-top:8px;font-size:.9rem;color:var(--muted);font-weight:650}}
.goodtxt,.good{{color:var(--green)}} .badtxt,.bad{{color:var(--red)}} .warn{{color:var(--amber)}} .neut{{color:var(--blue-2)}} section{{margin-top:20px;padding:clamp(18px,3vw,28px)}} .section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}} .section-head p{{margin:6px 0 0;color:var(--muted);max-width:80ch}}
table{{width:100%;border-collapse:collapse;font-size:.94rem}} th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}} td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} tbody tr:hover{{background:var(--surface-2)}}
.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}} .callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;color:#22314d;margin-top:14px}} .callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}} .callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}} .callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}} .callout strong{{color:var(--blue-2)}}
.tag{{display:inline-flex;padding:4px 10px;border-radius:999px;font-size:.78rem;font-weight:850;letter-spacing:.03em;text-transform:uppercase}} .tag.good{{background:var(--green-soft);color:var(--green)}} .tag.bad{{background:var(--red-soft);color:var(--red)}} .tag.neutral{{background:#eef3ff;color:var(--blue-2)}} .tag.caution{{background:var(--amber-soft);color:var(--amber)}} .t-mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}} .muted{{color:var(--muted)}} code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}}
.quote{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9rem;background:#111827;color:#e5e7eb;border-radius:16px;padding:16px;white-space:pre-wrap;overflow:auto}} .foot{{margin-top:26px;color:var(--muted);font-size:.86rem;text-align:center}}
@media (max-width:900px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.grid-2,.grid-3{{grid-template-columns:1fr}}table{{font-size:.84rem}}th,td{{padding:8px 7px}}}}
</style>
</head>
<body>
<div class='wrap'>
<header class='hero'>
  <span class='eyebrow'>Direct comparison · same OM delta config except one sentence</span>
  <h1>Removing the sloppy sentence did not hurt. It probably helped a little.</h1>
  <p class='subtitle'>This report compares the immediately prior projected-OM-delta run with the new no-orchestration run. The treatment change is the removal of one config-authored <code>orchestration.md</code> sentence. Same executor, same worker model, same OM settings, same delta projection extension, same subset, same 3 reps.</p>
  <div class='pillrow'>
    {pill('only treatment file removed: orchestration.md', 'good')}
    {pill('33 → 35 solves', 'neutral')}
    {pill('median cost −$0.103', 'good')}
    {pill('median tokens −54.6k', 'good')}
    {pill('p-values not decisive', 'caution')}
  </div>
  <div class='stats'>
    <div class='stat'><span class='label'>Solve count</span><span class='value'>33 → 35</span><span class='sub goodtxt'>+2 net solves</span></div>
    <div class='stat'><span class='label'>Mean partial</span><span class='value'>{fmt_float(old['mean_partial'])} → {fmt_float(new['mean_partial'])}</span><span class='sub neut'>{sign(P['mean_delta_partial'],4)}</span></div>
    <div class='stat'><span class='label'>Median cost</span><span class='value'>{fmt_money(old['median_combined_cost'])} → {fmt_money(new['median_combined_cost'])}</span><span class='sub goodtxt'>{sign(P['median_delta_combined_cost_usd'], money=True)}</span></div>
    <div class='stat'><span class='label'>Prompt surface</span><span class='value'>3466 → 3320</span><span class='sub goodtxt'>provider instruction chars</span></div>
    <div class='stat'><span class='label'>Sloppy sentence</span><span class='value'>108 → 0</span><span class='sub goodtxt'>provider requests containing it</span></div>
  </div>
</header>

<section>
  <div class='section-head'><div><h2>Verdict</h2><p>The sloppy sentence was not carrying the result. Removing it made the treatment cleaner, slightly improved raw solves, and reduced cost/tokens. The quality delta remains noisy.</p></div></div>
  <div class='grid-3'>
    <div class='callout good'><strong>Treatment isolation is clean.</strong> A recursive config diff shows the only treatment file removed was <code>orchestration.md</code>. README and smoke metadata differ, but execution settings match.</div>
    <div class='callout good'><strong>Operationally better.</strong> The clean run used fewer turns, fewer tool calls, fewer OM worker calls, fewer projected chars, lower median combined cost, and lower total combined cost.</div>
    <div class='callout caution'><strong>Not proof of prompt harm.</strong> The direct solve delta is +2, but there are 12 clean-only solves and 10 sloppy-only solves. McNemar is {pval(P['mcnemar_p'])}; partial-reward Wilcoxon is {pval(P['wilcoxon_partial_p'])}.</div>
  </div>
</section>

<section>
  <div class='section-head'><div><h2>What changed exactly?</h2><p>The old config appended this sentence to the executor's system prompt. The new config removed it.</p></div></div>
  <div class='quote'>{html.escape(DATA['sloppy_sentence'])}</div>
  <table><thead><tr>{th('Surface')}{th('Old sloppy config')}{th('New clean config')}{th('Meaning')}</tr></thead><tbody>{treatment_table()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Direct outcome table</h2><p>Combined cost and token metrics include OM worker usage.</p></div></div>
  <table><thead><tr>{th('Metric')}{th('Old sloppy','num')}{th('New clean','num')}{th('Clean − sloppy','num')}</tr></thead><tbody>{metric_table()}</tbody></table>
  <div class='callout'><strong>Cost note:</strong> total combined cost fell from {fmt_money(old['total_combined_cost'],2)} to {fmt_money(new['total_combined_cost'],2)}: {sign(new['total_combined_cost'] - old['total_combined_cost'], money=True)} over the 108 cells.</div>
</section>

<section>
  <div class='section-head'><div><h2>Paired interpretation</h2><p>Clean gained more binary solves, but not by enough to call the sentence causally harmful from this sample alone.</p></div></div>
  <table><thead><tr>{th('Check')}{th('Value')}{th('Interpretation')}</tr></thead><tbody>{pair_table()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Difficulty split</h2><p>The net solve gains were medium +1 and easy +1. Hard had better mean partial and lower cost, but the same solve count.</p></div></div>
  <table><thead><tr>{th('Bucket')}{th('n','num')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}</tr></thead><tbody>{difficulty_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Projection and worker behavior</h2><p>The projection code did not change. These differences are downstream behavior changes after removing the sentence.</p></div></div>
  <table><thead><tr>{th('Metric')}{th('Old sloppy','num')}{th('New clean','num')}{th('Clean − sloppy','num')}</tr></thead><tbody>{projection_table()}</tbody></table>
  <div class='callout good'><strong>Both configs used the cache-safe delta projection path:</strong> 0 provider rewrite markers, 0 stock compactions, 0 <code>om.folded</code> compaction records. The clean run simply generated fewer worker/projection events.</div>
</section>

<section>
  <div class='section-head'><div><h2>Verifier health</h2><p>Clean improves f2p but loses p2p health. Almost the entire p2p drop comes from one fastapi rep.</p></div></div>
  <table><thead><tr>{th('Metric')}{th('Old sloppy','num')}{th('New clean','num')}{th('Clean − sloppy','num')}</tr></thead><tbody>{verifier_table()}</tbody></table>
  <div class='callout caution'><strong>Fastapi outlier:</strong> <code>fastapi-deprecation-response-headers</code> accounts for −3,134 of the −3,147 p2p delta and is the largest mean-partial loss. Excluding that task, mean cell-level partial delta is +0.0102 instead of +0.0011.</div>
</section>

<section>
  <div class='section-head'><div><h2>Solve flips</h2><p>There were 22 discordant solve cells: 12 clean-only and 10 sloppy-only.</p></div></div>
  <div class='grid-2'>
    <div><h3>Clean-only solves</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}{th('Δ cost','num')}</tr></thead><tbody>{solve_flip_rows(P['solve_gains'])}</tbody></table></div>
    <div><h3>Sloppy-only solves</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}{th('Δ cost','num')}</tr></thead><tbody>{solve_flip_rows(P['solve_losses'])}</tbody></table></div>
  </div>
</section>

<section>
  <div class='section-head'><div><h2>Task-level movers</h2><p>These average the three reps per task, which is more stable than single-cell solve flips.</p></div></div>
  <div class='grid-2'>
    <div><h3>Largest task-level clean wins</h3><table><thead><tr>{th('Task')}{th('Mean partial','num')}{th('Δ','num')}{th('Solves','num')}{th('Median Δ cost','num')}</tr></thead><tbody>{task_mean_rows('wins')}</tbody></table></div>
    <div><h3>Largest task-level clean losses</h3><table><thead><tr>{th('Task')}{th('Mean partial','num')}{th('Δ','num')}{th('Solves','num')}{th('Median Δ cost','num')}</tr></thead><tbody>{task_mean_rows('losses')}</tbody></table></div>
  </div>
</section>

<section>
  <div class='section-head'><div><h2>Conclusion</h2><p>This direct comparison answers the narrow question.</p></div></div>
  <div class='callout good'><strong>Answer:</strong> yes, the meaningful config difference was the removal of the sloppy <code>orchestration.md</code> sentence. Removing it produced a cleaner treatment and did not reduce performance. It improved raw solves from 33 to 35 and lowered median cost/tokens.</div>
  <div class='callout caution'><strong>Careful wording:</strong> say “the sentence was unnecessary and possibly harmful/noisy,” not “the sentence caused a measured regression.” The paired data are mixed, and the significance tests do not support a strong causal claim.</div>
</section>

<div class='foot'>Sources: <code>analysis/gpt55-low-projected-om-delta-clean-vs-sloppy-36v2/summary.json</code>, <code>configs/projected-om-delta-gpt54mini-low/orchestration.md</code>, <code>configs/projected-om-delta-no-orchestration-gpt54mini-low/</code>, and result artifacts under <code>results/gpt-5.5/low/</code>.</div>
</div>
</body>
</html>
"""

(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html")
