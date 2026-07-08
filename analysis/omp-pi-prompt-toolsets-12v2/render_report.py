#!/usr/bin/env python3
from __future__ import annotations

import html, json
from pathlib import Path

OUT = Path(__file__).resolve().parent
D = json.loads((OUT / 'summary.json').read_text())
S = D['summaries']; P = D['pairs']; L = D['labels']

NEW = ['baseline-omp-pi-prompt-bash-only','baseline-omp-pi-prompt-grepglob','baseline-omp-pi-prompt-ast']
DISPLAY = ['baseline','baseline-omp-pi-prompt-bash-only','baseline-omp-pi-prompt-grepglob','baseline-omp-pi-prompt-ast','baseline-omp','baseline-omp-bash-only','baseline-omp-ast']


def fmt_int(x): return f"{int(round(x)):,}"
def fmt_m(x): return f"{x/1_000_000:.2f}M"
def money(x, d=2): return f"${x:,.{d}f}"
def pct(x): return f"{100*x:.1f}%"
def f(x,d=3): return f"{x:.{d}f}"
def sign(x,d=3,m=False,i=False):
    s = fmt_int(abs(x)) if i else money(abs(x),3) if m else f(abs(x),d)
    return ('+' if x>=0 else '−') + s
def cls(x, higher=True):
    if abs(x) < 1e-12: return 'neutral'
    return 'good' if (x>0)==higher else 'bad'
def td(x, c=''): return f"<td class='{c}'>{x}</td>"
def th(x, c=''): return f"<th class='{c}'>{x}</th>"
def tr(cells, c=''): return f"<tr class='{c}'>" + ''.join(cells) + '</tr>'
def tag(x,k='neutral'): return f"<span class='tag {k}'>{html.escape(x)}</span>"
def pill(x,k='neutral'): return f"<span class='pill {k}'>{html.escape(x)}</span>"
def pval(x): return '—' if x is None else f"p={x:.3f}"

def summary_rows():
    rows=[]
    for c in DISPLAY:
        m=S[c]
        kind='target' if c in NEW else ''
        rows.append(tr([
            td(html.escape(L[c])),
            td(f"{m['solves']}/36", 'num'),
            td(f(m['mean_partial'],4), 'num'),
            td(money(m['median_combined_cost_usd'],3), 'num'),
            td(fmt_m(m['median_combined_total_tokens']), 'num'),
            td(f"{m['median_turns']:.0f}", 'num'),
            td(f"{m['median_tool_calls']:.0f}", 'num'),
            td(fmt_int(m['median_non_message_tokens_t1']) if m['median_non_message_tokens_t1'] is not None else '—', 'num'),
            td(tag('new run','good') if c in NEW else tag('reference','neutral')),
        ], kind))
    return '\n'.join(rows)

def pair_rows():
    keys=['pi_prompt_bash_vs_pi','pi_prompt_grepglob_vs_pi','pi_prompt_ast_vs_pi','pi_prompt_grepglob_vs_bash','pi_prompt_ast_vs_bash','pi_prompt_bash_vs_default_bash','pi_prompt_grepglob_vs_default_omp','pi_prompt_ast_vs_default_ast']
    rows=[]
    for k in keys:
        p=P[k]
        rows.append(tr([
            td(f"{html.escape(p['other_label'])}<br><span class='muted'>vs {html.escape(p['base_label'])}</span>"),
            td(sign(p['solve_delta'], i=True), f"num {cls(p['solve_delta'])}"),
            td(sign(p['mean_delta_partial'],4), f"num {cls(p['mean_delta_partial'])}"),
            td(sign(p['median_delta_cost'], m=True), f"num {cls(p['median_delta_cost'], higher=False)}"),
            td(sign(p['median_delta_tokens'], i=True), f"num {cls(p['median_delta_tokens'], higher=False)}"),
            td(f"{p['other_only']} / {p['base_only']}", 'num'),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", 'num'),
        ]))
    return '\n'.join(rows)

def task_rows():
    rows=[]
    for r in D['task_rows']:
        rows.append(tr([
            td(f"<strong>{html.escape(r['title'])}</strong><br><span class='muted t-mono'>{html.escape(r['task'])} · {r['bucket']}</span>"),
            td(str(r['baseline_solves']), 'num'),
            td(str(r['baseline-omp-pi-prompt-bash-only_solves']), 'num'),
            td(str(r['baseline-omp-pi-prompt-grepglob_solves']), 'num'),
            td(str(r['baseline-omp-pi-prompt-ast_solves']), 'num'),
            td(str(r['baseline-omp_solves']), 'num'),
        ]))
    return '\n'.join(rows)

def tool_rows():
    tools=sorted(set().union(*(S[c]['tool_counts'].keys() for c in DISPLAY)))
    rows=[]
    for t in tools:
        rows.append(tr([td(t, 't-mono')]+[td(fmt_int(S[c]['tool_counts'].get(t,0)), 'num') for c in ['baseline','baseline-omp-pi-prompt-bash-only','baseline-omp-pi-prompt-grepglob','baseline-omp-pi-prompt-ast','baseline-omp']]))
    return '\n'.join(rows)

def prompt_rows():
    rows=[]
    for c in ['baseline','baseline-omp-pi-prompt-bash-only','baseline-omp-pi-prompt-grepglob','baseline-omp-pi-prompt-ast','baseline-omp','baseline-omp-bash-only','baseline-omp-ast']:
        m=S[c]
        rows.append(tr([
            td(html.escape(L[c])),
            td(str(m.get('omp_system_prompt_chars') or ('2,432' if c=='baseline' else 'default OMP')), 'num'),
            td(fmt_int(m['median_non_message_tokens_t1']) if m['median_non_message_tokens_t1'] is not None else '—', 'num'),
            td(html.escape(m.get('omp_tools') or 'read,bash,edit,write')),
        ], 'target' if c in NEW else ''))
    return '\n'.join(rows)

def mover_rows(key, which='top_wins', n=6):
    rows=[]
    for x in P[key][which][:n]:
        rows.append(tr([
            td(f"<strong>{html.escape(x['title'])}</strong><br><span class='muted t-mono'>{x['task']} · rep{x['rep']}</span>"),
            td(f"{x['base_partial']:.3f} → {x['other_partial']:.3f}", 'num'),
            td(sign(x['delta_partial'],3), f"num {cls(x['delta_partial'])}"),
            td(('✓' if x['base_solved'] else '—')+' → '+('✓' if x['other_solved'] else '—'), 'num'),
        ]))
    return '\n'.join(rows)

def bar(label, val, maxv, color, sub=''):
    w = 0 if maxv==0 else max(1, val/maxv*100)
    return f"<div class='bar-row'><div class='bar-label'>{html.escape(label)}</div><div><div class='bar-track'><div class='bar-fill {color}' style='width:{w:.2f}%'></div></div><div class='vals'><span>{fmt_int(val)}</span><span>{html.escape(sub)}</span></div></div></div>"

def token_bars():
    vals=[(L[c], S[c]['median_combined_total_tokens']) for c in ['baseline','baseline-omp-pi-prompt-bash-only','baseline-omp-pi-prompt-grepglob','baseline-omp-pi-prompt-ast','baseline-omp']]
    mx=max(v for _,v in vals)
    colors=['blue','green','red','amber','gray']
    return ''.join(bar(lbl, v, mx, col, 'median tokens/cell') for (lbl,v),col in zip(vals,colors))

base=S['baseline']; bash=S['baseline-omp-pi-prompt-bash-only']; grep=S['baseline-omp-pi-prompt-grepglob']; ast=S['baseline-omp-pi-prompt-ast']; default=S['baseline-omp']

html_doc=f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/><title>OMP Pi-like prompt toolsets · 12_v2 · DeepSWE report</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#c58a00;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);--radius-xl:28px;--radius-lg:20px;--max:1260px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55}}.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}}.hero,section{{background:rgba(255,255,255,.9);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}.hero{{padding:clamp(24px,4vw,42px);position:relative;overflow:hidden}}.hero::after{{content:"";position:absolute;inset:auto -10% -30% auto;width:440px;height:440px;background:radial-gradient(circle,rgba(51,93,255,.14),transparent 70%)}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.05}}h1{{font-size:clamp(2rem,4.4vw,3.8rem);margin-top:14px;max-width:17ch}}h2{{font-size:clamp(1.35rem,2.2vw,2rem)}}.subtitle{{max-width:82ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.08rem);margin:14px 0 0}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}.pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line);color:#31415d}}.pill.good{{background:var(--green-soft);color:var(--green)}}.pill.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral{{background:#eef3ff;color:var(--blue-2)}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:26px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:16px;min-height:118px;box-shadow:var(--shadow-sm)}}.label{{display:block;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}}.value{{display:block;font-size:clamp(1.25rem,2vw,1.9rem);font-weight:900;letter-spacing:-.04em}}.sub{{display:block;margin-top:8px;font-size:.9rem;color:var(--muted);font-weight:600}}section{{margin-top:20px;padding:clamp(18px,3vw,28px)}}.section-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}}.section-head p{{margin:6px 0 0;color:var(--muted);max-width:78ch}}table{{width:100%;border-collapse:collapse;font-size:.94rem}}th,td{{text-align:left;padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:800}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}tbody tr:hover{{background:var(--surface-2)}}tr.target{{background:#f4fbf7}}.muted{{color:var(--muted)}}.t-mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.good,.goodtxt{{color:var(--green)}}.bad,.badtxt{{color:var(--red)}}.neutral,.neut{{color:var(--blue-2)}}.warn{{color:var(--amber)}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;color:#22314d;margin-top:14px}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.mini{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:18px;text-align:center;box-shadow:var(--shadow-sm)}}.mini .big{{display:block;font-size:2rem;font-weight:900;letter-spacing:-.04em}}.mini .cap{{display:block;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;margin-top:6px}}.tag{{display:inline-flex;padding:4px 10px;border-radius:999px;font-size:.78rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase}}.tag.good{{background:var(--green-soft);color:var(--green)}}.tag.bad{{background:var(--red-soft);color:var(--red)}}.tag.neutral{{background:#eef3ff;color:var(--blue-2)}}.bar-list{{display:grid;gap:14px;margin-top:8px}}.bar-row{{display:grid;grid-template-columns:210px 1fr;gap:14px;align-items:center}}.bar-label{{font-weight:800;color:#22314d;font-size:14px}}.bar-track{{position:relative;height:18px;border-radius:999px;background:#edf2f7;overflow:hidden;border:1px solid #dde5ef}}.bar-fill{{position:absolute;inset:0 auto 0 0;border-radius:inherit}}.bar-fill.blue{{background:#8fa3c7}}.bar-fill.green{{background:linear-gradient(90deg,#45bf81,#178a5b)}}.bar-fill.red{{background:linear-gradient(90deg,#f1786f,#d0473f)}}.bar-fill.amber{{background:linear-gradient(90deg,#f1bd49,#c58a00)}}.bar-fill.gray{{background:linear-gradient(90deg,#6f8cff,#244de0)}}.vals{{display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);font-weight:700;font-variant-numeric:tabular-nums;margin-top:4px}}.foot{{margin-top:26px;color:var(--muted);font-size:.86rem;text-align:center}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}}@media(max-width:900px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.grid-2,.grid-3{{grid-template-columns:1fr}}table{{font-size:.84rem}}th,td{{padding:8px 7px}}.bar-row{{grid-template-columns:1fr}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>OMP prompt/toolset ablation · GPT-5.5 low · 12_v2 × 3</span><h1>The Pi-like prompt helped only when OMP stayed bash-only.</h1><p class='subtitle'>This run tested three OMP variants with the default Oh My Pi instruction block replaced by a short Pi-like prompt. The useful signal is not “OMP tools are better.” It is narrower: <strong>the stripped-down bash-only OMP config got the best raw solve count, while grep/glob and AST variants underperformed it.</strong></p><div class='pillrow'>{pill('108/108 cells complete','good')}{pill('bash-only: 13/36 solves','good')}{pill('grep/glob: negative hint','bad')}{pill('AST: no clear benefit','caution')}{pill('still 1.9× Pi cost','caution')}</div><div class='stats'><div class='stat'><span class='label'>Best new variant</span><span class='value'>13/36</span><span class='sub goodtxt'>Pi-like bash-only; clean Pi was 8/36</span></div><div class='stat'><span class='label'>Median cost</span><span class='value'>{money(bash['median_combined_cost_usd'],2)}</span><span class='sub badtxt'>vs clean Pi {money(base['median_combined_cost_usd'],2)}</span></div><div class='stat'><span class='label'>Median tokens</span><span class='value'>{fmt_m(bash['median_combined_total_tokens'])}</span><span class='sub badtxt'>vs clean Pi {fmt_m(base['median_combined_total_tokens'])}</span></div><div class='stat'><span class='label'>Prompt wrapper</span><span class='value'>{fmt_int(bash['median_non_message_tokens_t1'])}</span><span class='sub goodtxt'>down from OMP default 7–8k/turn</span></div><div class='stat'><span class='label'>Strongest hint</span><span class='value'>−6</span><span class='sub badtxt'>grep/glob solves vs bash-only, p≈0.07</span></div></div></header>
<section><div class='section-head'><div><h2>High-level read</h2><p>Use this as a direction-finding run, not a final result. With 36 cells per config, we care about repeated directional hints and cost mechanics.</p></div></div><div class='grid-3'><div class='callout good'><strong>Keep:</strong> the Pi-like OMP bash-only config. It moved 6 cells from Pi-only failures to OMP solves and lost only 1 clean-Pi solve. That is a real enough signal to justify scaling.</div><div class='callout bad'><strong>Drop for now:</strong> the Pi-like grep/glob config. It was cheaper, but lost 6 solves against Pi-like bash-only. The negative solve signal is one of the stronger hints in the run.</div><div class='callout caution'><strong>Pause:</strong> the AST config. It used <code>ast_grep</code> only 15 times and <code>ast_edit</code> 0 times. It did not beat bash-only, so it is not worth scaling before a task-targeted AST subset.</div></div></section>
<section><div class='section-head'><div><h2>Headline table</h2><p>All rows are the same 12_v2 tasks × 3 reps. Reference rows are included so we can separate prompt effect from toolset effect.</p></div></div><table><thead><tr>{th('Config')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Median tokens','num')}{th('Turns','num')}{th('Tool calls','num')}{th('Wrapper tok/turn','num')}{th('kind')}</tr></thead><tbody>{summary_rows()}</tbody></table><div class='callout'><strong>Key point:</strong> prompt slimming reduced OMP's wrapper overhead, but did not make OMP cheap. Even the best variant still used {bash['median_combined_total_tokens']/base['median_combined_total_tokens']:.2f}× clean-Pi median tokens and {bash['median_combined_cost_usd']/base['median_combined_cost_usd']:.2f}× median cost.</div></section>
<section><div class='section-head'><div><h2>Paired comparisons</h2><p>Think of these as hints. The most actionable hint is grep/glob losing against bash-only while saving tokens.</p></div></div><table><thead><tr>{th('Comparison')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('solve flips other/base','num')}{th('tests','num')}</tr></thead><tbody>{pair_rows()}</tbody></table></section>
<div class='grid-2'><section><div class='section-head'><div><h2>Token footprint</h2><p>The Pi-like prompt cuts OMP overhead, especially compared with default OMP, but OMP remains much larger than clean Pi.</p></div></div><div class='bar-list'>{token_bars()}</div></section><section><div class='section-head'><div><h2>Prompt/tool surface</h2><p>Initial OMP provider requests still include larger OMP tool schemas and an always-exposed <code>generate_image</code> tool.</p></div></div><table><thead><tr>{th('Config')}{th('system prompt chars','num')}{th('wrapper tok/turn','num')}{th('tool whitelist')}</tr></thead><tbody>{prompt_rows()}</tbody></table></section></div>
<section><div class='section-head'><div><h2>Tool usage</h2><p>Adding dedicated search/AST tools changed behavior, but not in the helpful direction on this slice.</p></div></div><table><thead><tr>{th('tool')}{th('Pi clean','num')}{th('Pi-like bash','num')}{th('Pi-like grep/glob','num')}{th('Pi-like AST','num')}{th('OMP default','num')}</tr></thead><tbody>{tool_rows()}</tbody></table><div class='callout caution'><strong>AST reality check:</strong> under the Pi-like AST prompt, OMP made 15 <code>ast_grep</code> calls and 0 <code>ast_edit</code> calls across 36 cells. This was mostly an AST-search experiment, not an AST-edit experiment.</div></section>
<section><div class='section-head'><div><h2>Task-level solves</h2><p>Pi-like bash-only's solve lift came from near-miss conversions, not one giant outlier.</p></div></div><table><thead><tr>{th('Task')}{th('Pi clean','num')}{th('Pi-like bash','num')}{th('Pi-like grep/glob','num')}{th('Pi-like AST','num')}{th('OMP default','num')}</tr></thead><tbody>{task_rows()}</tbody></table></section>
<section><div class='section-head'><div><h2>Concrete solve flips: Pi-like bash-only vs clean Pi</h2><p>This is the comparison that makes the bash-only variant worth another look.</p></div></div><div class='grid-2'><div><h3>Largest wins</h3><table><thead><tr>{th('Task')}{th('partial','num')}{th('Δ','num')}{th('solve','num')}</tr></thead><tbody>{mover_rows('pi_prompt_bash_vs_pi','top_wins')}</tbody></table></div><div><h3>Largest losses</h3><table><thead><tr>{th('Task')}{th('partial','num')}{th('Δ','num')}{th('solve','num')}</tr></thead><tbody>{mover_rows('pi_prompt_bash_vs_pi','top_losses')}</tbody></table></div></div><div class='callout good'><strong>Solve flips:</strong> bash-only gained <code>superjson rep0</code>, <code>obsidian rep0/rep2</code>, <code>go-critic rep0/rep2</code>, and <code>mobly rep1</code>. It lost only <code>sql-formatter rep1</code>, and that loss was a 0.9995 near-solve.</div></section>
<section><div class='section-head'><div><h2>Conclusion and next move</h2></div></div><div class='callout good'><strong>Most reasonable next direction:</strong> scale only <code>baseline-omp-pi-prompt-bash-only</code> to 36_v2. It is the only variant here that improved raw solves over clean Pi and default OMP while reducing OMP default overhead.</div><div class='callout bad'><strong>Do not spend more on grep/glob right now:</strong> it saved about 211k median tokens vs bash-only but lost 6 solves, with discordant solve flips 7 against vs 1 for. In our high-cost regime, that is a good enough negative screen.</div><div class='callout caution'><strong>AST needs a different test:</strong> broad 12_v2 did not make the model use <code>ast_edit</code>. If AST is worth testing, create a small syntax-rewrite-heavy subset and a smoke that proves the tool is actually used.</div></section>
<div class='foot'>Generated from <code>analysis/omp-pi-prompt-toolsets-12v2/summary.json</code> · run <code>omp-pi-prompt-toolsets-12v2-r3-w24</code> · exact filter: <code>12_v2 × rep0..2</code></div>
</div></body></html>"""
(OUT/'index.html').write_text(html_doc)
print(OUT/'index.html')
