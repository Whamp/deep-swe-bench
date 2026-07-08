#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "summary.json").read_text())
S = DATA["summaries"]
P = DATA["pairs"]

PI = "baseline"
CLEAN_MEDIUM = "baseline__gpt55_medium"
PREAMBLE_MEDIUM = "baseline-preamble-orchestration__gpt55_medium"
BASH = "baseline-omp-pi-prompt-bash-only-no-project"
GREP = "baseline-omp-pi-prompt-grepglob-no-project"
AST = "baseline-omp-pi-prompt-ast-no-project"
DEF_BASH = "baseline-omp-bash-only"
DEF_GREP = "baseline-omp"
DEF_AST = "baseline-omp-ast"
NO_PROJECT = [BASH, GREP, AST]
DEFAULTS = [DEF_BASH, DEF_GREP, DEF_AST]
ALL = [PI, CLEAN_MEDIUM, PREAMBLE_MEDIUM] + NO_PROJECT + DEFAULTS

SHORT = {
    PI: "Clean Pi low",
    CLEAN_MEDIUM: "Clean Pi medium",
    PREAMBLE_MEDIUM: "Pi preamble/orch medium",
    BASH: "OMP bash-only no-PROJECT",
    GREP: "OMP grep/glob no-PROJECT",
    AST: "OMP AST no-PROJECT",
    DEF_BASH: "Default OMP bash-only",
    DEF_GREP: "Default OMP grep/glob",
    DEF_AST: "Default OMP AST",
}


def esc(x): return html.escape(str(x))
def fmt_int(x): return f"{int(round(x)):,}"
def money(x, digits=3): return f"${x:,.{digits}f}"
def f4(x): return f"{x:.4f}"
def pct(x): return f"{100*x:.1f}%"
def signed(x, digits=3, dollar=False, integer=False):
    pref = "+" if x >= 0 else "−"
    v = abs(x)
    if dollar: body = money(v, digits)
    elif integer: body = fmt_int(v)
    else: body = f"{v:.{digits}f}"
    return pref + body

def tone(x, higher=True):
    if abs(x) < 1e-12: return "neutral"
    return "good" if ((x > 0) == higher) else "bad"

def pill(text, kind="neutral"):
    return f"<span class='pill {kind}'>{esc(text)}</span>"

def th(x, cls=""): return f"<th class='{cls}'>{esc(x)}</th>"
def td(x, cls=""): return f"<td class='{cls}'>{x}</td>"
def tr(cells, cls=""): return f"<tr class='{cls}'>" + "".join(cells) + "</tr>"
def pval(x): return "—" if x is None else f"p={x:.3f}"


def main_rows(configs):
    out=[]
    for c in configs:
        s=S[c]
        out.append(tr([
            td(f"<strong>{esc(SHORT[c])}</strong><br><span class='muted mono'>{esc(c)}</span>"),
            td(f"{s['solves']}/108", "num"),
            td(f4(s['mean_partial']), "num"),
            td(money(s['median_cost']), "num"),
            td(fmt_int(s['median_tokens']), "num"),
            td(f"{s['median_wall_s']:.1f}s", "num"),
            td(f"{s['median_turns']:.1f}", "num"),
            td(f"{s['median_tool_calls']:.1f}", "num"),
            td(money(s['total_cost'],2), "num"),
        ]))
    return "\n".join(out)


def vs_pi_rows():
    out=[]
    for c in NO_PROJECT:
        p=P[f"{PI}__vs__{c}"]
        out.append(tr([
            td(f"<strong>{esc(SHORT[c])}</strong>"),
            td(f"{p['a_solves']} → {p['b_solves']}", "num"),
            td(signed(p['solve_delta'], integer=True), f"num {tone(p['solve_delta'])}"),
            td(signed(p['mean_delta_partial'], 4), f"num {tone(p['mean_delta_partial'])}"),
            td(signed(p['median_delta_combined_cost_usd'], dollar=True), f"num {tone(p['median_delta_combined_cost_usd'], False)}"),
            td(signed(p['median_delta_combined_total_tokens'], integer=True), f"num {tone(p['median_delta_combined_total_tokens'], False)}"),
            td(f"{p['b_only']} / {p['a_only']}", "num"),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", "num"),
        ]))
    return "\n".join(out)


def medium_rows():
    pairs = [
        (PI, CLEAN_MEDIUM, "Clean Pi low → clean Pi medium"),
        (AST, CLEAN_MEDIUM, "OMP AST no-PROJECT low → clean Pi medium"),
        (GREP, CLEAN_MEDIUM, "OMP grep/glob no-PROJECT low → clean Pi medium"),
        (BASH, CLEAN_MEDIUM, "OMP bash-only no-PROJECT low → clean Pi medium"),
        (CLEAN_MEDIUM, PREAMBLE_MEDIUM, "Clean Pi medium → preamble/orch medium"),
    ]
    out=[]
    for a,b,label in pairs:
        p=P[f"{a}__vs__{b}"]
        out.append(tr([
            td(f"<strong>{esc(label)}</strong>"),
            td(f"{p['a_solves']} → {p['b_solves']}", "num"),
            td(signed(p['solve_delta'], integer=True), f"num {tone(p['solve_delta'])}"),
            td(signed(p['mean_delta_partial'],4), f"num {tone(p['mean_delta_partial'])}"),
            td(signed(p['median_delta_combined_cost_usd'], dollar=True), f"num {tone(p['median_delta_combined_cost_usd'], False)}"),
            td(signed(p['median_delta_combined_total_tokens'], integer=True), f"num {tone(p['median_delta_combined_total_tokens'], False)}"),
            td(f"{p['b_only']} / {p['a_only']}", "num"),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", "num"),
        ]))
    return "\n".join(out)


def default_rows():
    out=[]
    for a,b in [(DEF_BASH,BASH),(DEF_GREP,GREP),(DEF_AST,AST)]:
        p=P[f"{a}__vs__{b}"]
        out.append(tr([
            td(f"<strong>{esc(SHORT[a])}</strong> → <strong>{esc(SHORT[b])}</strong>"),
            td(f"{p['a_solves']} → {p['b_solves']}", "num"),
            td(signed(p['solve_delta'], integer=True), f"num {tone(p['solve_delta'])}"),
            td(signed(p['mean_delta_partial'],4), f"num {tone(p['mean_delta_partial'])}"),
            td(signed(p['median_delta_combined_cost_usd'], dollar=True), f"num {tone(p['median_delta_combined_cost_usd'], False)}"),
            td(signed(p['median_delta_combined_total_tokens'], integer=True), f"num {tone(p['median_delta_combined_total_tokens'], False)}"),
            td(signed(p['median_delta_turns'], 1), f"num {tone(p['median_delta_turns'], False)}"),
            td(signed(p['median_delta_tool_calls'], 1), f"num {tone(p['median_delta_tool_calls'], False)}"),
        ]))
    return "\n".join(out)


def difficulty_rows():
    out=[]
    for c in NO_PROJECT:
        p=P[f"{PI}__vs__{c}"]
        for bucket in ["hard","medium","easy"]:
            d=p['difficulty'][bucket]
            out.append(tr([
                td(SHORT[c]),
                td(bucket.title()),
                td(f"{d['a_solves']} → {d['b_solves']}", "num"),
                td(signed(d['solve_delta'], integer=True), f"num {tone(d['solve_delta'])}"),
                td(signed(d['mean_delta_partial'],4), f"num {tone(d['mean_delta_partial'])}"),
                td(signed(d['median_delta_cost'], dollar=True), f"num {tone(d['median_delta_cost'], False)}"),
            ]))
    return "\n".join(out)


def tool_rows():
    out=[]
    for c in ALL:
        tc=S[c]['tool_counts']
        out.append(tr([
            td(f"<strong>{esc(SHORT[c])}</strong>"),
            td(fmt_int(sum(tc.values())), "num"),
            td(fmt_int(tc.get('bash',0)), "num"),
            td(fmt_int(tc.get('read',0)), "num"),
            td(fmt_int(tc.get('edit',0)), "num"),
            td(fmt_int(tc.get('grep',0)), "num"),
            td(fmt_int(tc.get('glob',0)), "num"),
            td(fmt_int(tc.get('ast_grep',0)), "num"),
            td(fmt_int(tc.get('ast_edit',0)), "num"),
        ]))
    return "\n".join(out)


def provider_rows():
    out=[]
    for c in [PI, CLEAN_MEDIUM]+NO_PROJECT:
        s=S[c]
        tools=', '.join(s['provider_tool_variants'][0]) if s['provider_tool_variants'] else '—'
        roles=', '.join(s['provider_input_role_variants'][0]) if s['provider_input_role_variants'] else '—'
        out.append(tr([
            td(f"<strong>{esc(SHORT[c])}</strong>"),
            td(fmt_int(s['provider_instructions_chars_median']), "num"),
            td(fmt_int(s['provider_tool_schema_bytes_median']), "num"),
            td(fmt_int(s['provider_payload_bytes_median']), "num"),
            td(esc(roles)),
            td(esc(tools)),
            td(f"{s['provider_project_cells']}/108", "num good"),
            td(f"{s['provider_generate_image_cells']}/108", "num good"),
        ]))
    return "\n".join(out)


def health_rows():
    out=[]
    for c in NO_PROJECT:
        s=S[c]
        out.append(tr([
            td(f"<strong>{esc(SHORT[c])}</strong>"),
            td(f"{s['provider_project_cells']}/108", "num good"),
            td(f"{s['provider_generate_image_cells']}/108", "num good"),
            td(str(s['stale_usage_limit_cells']), "num caution"),
            td(str(s['latest_usage_limit_cells']), "num good"),
            td(str(s['usage_mismatch_cells']), "num good"),
            td(str(s['transient_json_cells']), "num good"),
            td(str(s['stderr_nonempty_cells']), "num good"),
        ]))
    return "\n".join(out)


def flip_rows(c, gains=True, n=10):
    p=P[f"{PI}__vs__{c}"]
    arr=p['solve_gains' if gains else 'solve_losses'][:n]
    return "\n".join(tr([
        td(f"<strong>{esc(m['title'])}</strong><br><span class='muted mono'>{esc(m['task'])} · rep{m['rep']} · {m['difficulty']}</span>"),
        td(f"{m['a_partial']:.3f} → {m['b_partial']:.3f}", "num"),
        td(signed(m['delta_partial'],3), f"num {tone(m['delta_partial'])}"),
    ]) for m in arr) or tr([td("None"), td("—","num"), td("—","num")])


def pareto_rows():
    out=[]
    for r in DATA['pareto_all']:
        status = "frontier" if not r['dominated_by'] else "dominated"
        out.append(tr([
            td(f"<strong>{esc(SHORT[r['config']])}</strong>"),
            td(f"{r['solves']}/108", "num"),
            td(money(r['median_cost']), "num"),
            td(f4(r['mean_partial']), "num"),
            td(f"<span class='tag {'good' if status=='frontier' else 'neutral'}'>{status}</span>"),
            td(', '.join(SHORT[d] for d in r['dominated_by']) or '—'),
        ]))
    return "\n".join(out)


def bars():
    max_cost=max(S[c]['median_cost'] for c in ALL)
    rows=[]
    for c in ALL:
        width=100*S[c]['median_cost']/max_cost
        rows.append(f"<div class='barrow'><div class='barlabel'>{esc(SHORT[c])}</div><div class='track'><div class='bar' style='width:{width:.1f}%'></div></div><div class='barval'>{S[c]['solves']}/108 · {money(S[c]['median_cost'])}</div></div>")
    return "\n".join(rows)

html_doc=f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>OMP no-PROJECT 36_v2 report</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--greenSoft:#e7f7ef;--redSoft:#fdeceb;--amberSoft:#fff5dd;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:24px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.12),transparent 30%),linear-gradient(180deg,#fbfdff,var(--bg));font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);line-height:1.5}}.wrap{{max-width:1360px;margin:0 auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.95);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:var(--radius)}}.hero{{padding:42px}}section{{padding:26px;margin-top:20px}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2.1rem,4.8vw,4.2rem);max-width:18ch;margin-top:14px}}h2{{font-size:clamp(1.35rem,2.2vw,2rem)}}h3{{font-size:1.05rem;margin:12px 0}}p{{color:var(--muted)}}.subtitle{{font-size:1.08rem;max-width:95ch}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}}.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase}}.pill{{padding:8px 13px;border:1px solid var(--line);background:#f8fafc;color:#31415d}}.pill.good,.tag.good{{background:var(--greenSoft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--redSoft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amberSoft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.tag{{padding:4px 9px}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:28px}}.stat{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;min-height:118px}}.stat .label{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:850;margin-bottom:8px}}.stat .value{{display:block;font-size:clamp(1.35rem,2vw,2rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;color:var(--muted);font-size:.9rem;margin-top:8px;font-weight:650}}table{{width:100%;border-collapse:collapse;font-size:.92rem}}th,td{{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}tbody tr:hover{{background:#f8fafc}}.muted{{color:var(--muted)}}.mono,code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}code{{background:#eef2ff;border-radius:6px;padding:.12em .35em}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}.neutral{{color:#1d3fb8}}.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin:14px 0}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}}.head{{display:flex;justify-content:space-between;align-items:end;gap:14px;flex-wrap:wrap;margin-bottom:14px}}.head p{{margin:.4rem 0 0;max-width:85ch}}.barrow{{display:grid;grid-template-columns:220px 1fr 150px;gap:12px;align-items:center;margin:10px 0}}.barlabel{{font-weight:750}}.track{{height:14px;background:#edf2f7;border-radius:999px;overflow:hidden}}.bar{{height:100%;background:linear-gradient(90deg,var(--blue),#7b92ff);border-radius:999px}}.barval{{text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}}.foot{{text-align:center;color:var(--muted);font-size:.86rem;margin-top:24px}}@media(max-width:900px){{.stats,.grid2,.grid3{{grid-template-columns:1fr}}.barrow{{grid-template-columns:1fr}}.barval{{text-align:left}}.hero{{padding:26px}}table{{font-size:.82rem}}th,td{{padding:7px 6px}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>OMP no-PROJECT rerun · GPT-5.5 low · 36_v2 × 3 reps</span>
<h1>OMP got cleaner, cheaper, and still costs a lot.</h1>
<p class='subtitle'>This report compares clean Pi low, clean Pi medium, the historical prompt-bearing Pi medium row, and the no-PROJECT OMP Pi-like toolsets on the arm-independent 36_v2 subset. The hidden OMP <code>PROJECT</code> developer message and unintended <code>generate_image</code> tool are gone from the OMP provider requests. The new clean GPT-5.5 medium baseline is now the decisive reference point.</p>
<div class='pillrow'>{pill('OMP run complete: 324/324 cells', 'good')}{pill('clean medium complete: 108/108 cells', 'good')}{pill('0 PROJECT provider requests', 'good')}{pill('0 generate_image provider tools', 'good')}{pill('clean medium: 50/108 solves', 'good')}{pill('best no-PROJECT: 35/108 solves', 'neutral')}</div>
<div class='stats'>
<div class='stat'><span class='label'>Clean Pi</span><span class='value'>28/108</span><span class='sub'>{money(S[PI]['median_cost'])} median cost</span></div>
<div class='stat'><span class='label'>Clean Pi medium</span><span class='value'>50/108</span><span class='sub good'>{money(S[CLEAN_MEDIUM]['median_cost'])} median cost</span></div>
<div class='stat'><span class='label'>Cheapest no-PROJECT</span><span class='value'>{money(S[AST]['median_cost'])}</span><span class='sub'>AST no-PROJECT, 35 solves</span></div>
<div class='stat'><span class='label'>Best no-PROJECT solves</span><span class='value'>35/108</span><span class='sub'>grep/glob and AST tie</span></div>
<div class='stat'><span class='label'>Run health</span><span class='value'>clean</span><span class='sub good'>3 stale quota sessions ignored safely</span></div>
</div></header>

<section><div class='head'><div><h2>Run-health audit</h2><p>The run is usable. Three cells have stale usage-limit session files from the earlier pause, but each final scored retry has a clean latest session and matching <code>result.json</code> usage.</p></div></div>
<table><thead><tr>{th('Config')}{th('PROJECT cells','num')}{th('generate_image cells','num')}{th('stale quota sessions','num')}{th('latest quota sessions','num')}{th('usage mismatches','num')}{th('transient json','num')}{th('stderr nonempty','num')}</tr></thead><tbody>{health_rows()}</tbody></table>
<div class='callout good'><strong>Score safety:</strong> all three stale quota files are <code>adaptix-name-mapping-aliases</code> rep2 from the paused 12_v2 run. The successful 36_v2 retry sessions contain no usage-limit text, and usage accounting matches the latest root session.</div></section>

<section><div class='head'><div><h2>Headline table</h2><p>OMP no-PROJECT improves solve count over clean Pi, while remaining far more expensive. Compared with default OMP, the Pi-like no-PROJECT prompt usually recovers cost and tokens.</p></div></div>
<table><thead><tr>{th('Config')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Median tokens','num')}{th('Median wall','num')}{th('Turns','num')}{th('Tool calls','num')}{th('Total cost','num')}</tr></thead><tbody>{main_rows([PI, CLEAN_MEDIUM, PREAMBLE_MEDIUM]+NO_PROJECT+DEFAULTS)}</tbody></table>
<div class='callout good'><strong>Clean medium is now the reference:</strong> clean GPT-5.5 medium solves 50/108 at {money(S[CLEAN_MEDIUM]['median_cost'])} median cost. That beats every low-thinking OMP row on solve count, mean partial, and usually cost efficiency.</div></section>

<section><div class='head'><div><h2>No-PROJECT OMP vs clean Pi low</h2><p>All three OMP variants gain solves over clean Pi low. Only bash-only shows a strong paired partial-reward signal; grep/glob and AST gain binary solves without a significant partial-reward shift.</p></div></div>
<table><thead><tr>{th('Config')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('OMP-only / Pi-only','num')}{th('Tests','num')}</tr></thead><tbody>{vs_pi_rows()}</tbody></table>
<div class='callout caution'><strong>Read this as directional:</strong> solve deltas are +5 to +7, but McNemar p-values stay above 0.09. The partial story is clearer for bash-only (Wilcoxon p=0.004), weaker for grep/glob and AST.</div></section>

<section><div class='head'><div><h2>Clean medium changes the answer</h2><p>Raising clean Pi from low to medium adds 22 solves. It also beats every low-thinking OMP row by 15–17 solves in paired comparisons.</p></div></div>
<table><thead><tr>{th('Comparison')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('Right-only / left-only solves','num')}{th('Tests','num')}</tr></thead><tbody>{medium_rows()}</tbody></table>
<div class='callout good'><strong>Efficiency read:</strong> clean medium costs about {money(S[CLEAN_MEDIUM]['median_cost'] - S[PI]['median_cost'])} more than clean low at the median and adds 22 solves. Against no-PROJECT AST, clean medium adds 15 solves for only about {money(P[f'{AST}__vs__{CLEAN_MEDIUM}']['median_delta_combined_cost_usd'])} more median cost.</div></section>

<section><div class='head'><div><h2>Difficulty split vs clean Pi low</h2><p>The OMP gains are not only easy-task conversions. Bash-only lifts hard solves most; grep/glob and AST lift medium solves more.</p></div></div>
<table><thead><tr>{th('Config')}{th('Bucket')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}</tr></thead><tbody>{difficulty_rows()}</tbody></table></section>

<section><div class='head'><div><h2>No-PROJECT OMP vs default OMP</h2><p>The Pi-like no-PROJECT prompt mostly makes OMP cheaper and shorter. It does not uniformly improve solves: default grep/glob still has one extra solve, but at much higher cost.</p></div></div>
<table><thead><tr>{th('Comparison')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('Δ turns','num')}{th('Δ tool calls','num')}</tr></thead><tbody>{default_rows()}</tbody></table>
<div class='callout'><strong>Practical take:</strong> no-PROJECT AST is the best solve-cost OMP variant in this table: 35 solves at {money(S[AST]['median_cost'])}. Default grep/glob gets 36 solves, but costs {money(S[DEF_GREP]['median_cost'])} median and uses about {fmt_int(S[DEF_GREP]['median_tokens'])} median tokens.</div></section>

<section><div class='head'><div><h2>Provider-visible surface</h2><p>The cleanup worked, but OMP still does not match Pi's tool surface. OMP's tool schemas are much larger even after removing <code>PROJECT</code> and <code>generate_image</code>.</p></div></div>
<table><thead><tr>{th('Config')}{th('Instruction chars','num')}{th('Tool schema bytes','num')}{th('Provider request bytes','num')}{th('Input roles')}{th('Tools')}{th('PROJECT','num')}{th('generate_image','num')}</tr></thead><tbody>{provider_rows()}</tbody></table>
<div class='callout'><strong>Remaining confound:</strong> top-level instructions are near parity for bash-only ({fmt_int(S[BASH]['provider_instructions_chars_median'])} vs Pi {fmt_int(S[PI]['provider_instructions_chars_median'])} chars), but bash-only's provider tool schema is about 6× Pi's ({fmt_int(S[BASH]['provider_tool_schema_bytes_median'])} vs {fmt_int(S[PI]['provider_tool_schema_bytes_median'])} bytes).</div></section>

<section><div class='head'><div><h2>Tool behavior</h2><p>The no-PROJECT variants still make more calls than Pi. AST tools are now used more than on 12_v2, but mostly for search: <code>ast_grep</code> 64 calls, <code>ast_edit</code> 2 calls.</p></div></div>
<table><thead><tr>{th('Config')}{th('Total starts','num')}{th('bash','num')}{th('read','num')}{th('edit','num')}{th('grep','num')}{th('glob','num')}{th('ast_grep','num')}{th('ast_edit','num')}</tr></thead><tbody>{tool_rows()}</tbody></table></section>

<section><div class='head'><div><h2>Solve-cost frontier in this slice</h2><p>Clean medium changes the picture. The low-thinking OMP variants are no longer competitive with simply raising Pi from low to medium. The frontier is clean Pi low, no-PROJECT AST low, clean Pi medium, and the prompt-bearing medium row.</p></div></div>
<div>{bars()}</div>
<table><thead><tr>{th('Config')}{th('Solves','num')}{th('Median cost','num')}{th('Mean partial','num')}{th('Status')}{th('Dominated by')}</tr></thead><tbody>{pareto_rows()}</tbody></table></section>

<section><div class='head'><div><h2>Concrete solve flips vs clean Pi</h2><p>These examples show the main pattern: OMP often converts near-misses to solves, but it also loses some clean-Pi solves.</p></div></div>
<div class='grid3'>
<div><h3>Bash-only gains</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{flip_rows(BASH, True)}</tbody></table><h3>Bash-only losses</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{flip_rows(BASH, False)}</tbody></table></div>
<div><h3>Grep/glob gains</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{flip_rows(GREP, True)}</tbody></table><h3>Grep/glob losses</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{flip_rows(GREP, False)}</tbody></table></div>
<div><h3>AST gains</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{flip_rows(AST, True)}</tbody></table><h3>AST losses</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{flip_rows(AST, False)}</tbody></table></div>
</div></section>

<section><div class='head'><div><h2>Conclusion</h2><p>The clean rerun changes the OMP readout from “contaminated spike” to “real but expensive tradeoff.”</p></div></div>
<div class='grid2'>
<div class='callout good'><strong>Use the no-PROJECT rows for future OMP prompt/toolset claims.</strong> The cleanup removed the hidden developer message and image tool across all 324 cells.</div>
<div class='callout caution'><strong>Do not call OMP a Pareto win over Pi broadly.</strong> It buys solves on this low-thinking 36_v2 slice, but at a large token/cost premium. The best no-PROJECT row is a tradeoff, not a free improvement.</div>
</div>
<div class='callout'><strong>Bottom line:</strong> OMP no-PROJECT is a real improvement over clean Pi low, but clean Pi medium is a much stronger intervention. The historical preamble/orchestration medium row adds only +3 solves over clean medium and is not statistically decisive.</div></section>

<div class='foot'>Generated from <code>analysis/omp-pi-prompt-no-project-36v2/summary.json</code>. Run state: <code>results/_runs/omp-pi-prompt-toolsets-no-project-36v2-r3-w24/</code>.</div>
</div></body></html>"""

(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html")
