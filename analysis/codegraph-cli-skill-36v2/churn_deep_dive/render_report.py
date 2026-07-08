#!/usr/bin/env python3
from __future__ import annotations
import html, json
from pathlib import Path
OUT=Path(__file__).resolve().parent
CLS=json.loads((OUT/'classification.json').read_text())
IDX=json.loads((OUT/'loss_packets_index.json').read_text())
SUMMARY=json.loads((OUT.parent/'summary.json').read_text())

def esc(x): return html.escape(str(x))
def fmt_int(x): return f"{int(round(x)):,}"
def money(x,d=3): return f"${x:,.{d}f}"
def signed(x,d=3,integer=False):
    pref='+' if x>=0 else '−'; v=abs(x)
    return pref+(fmt_int(v) if integer else f"{v:.{d}f}")
def tone(x,higher=True):
    if abs(x)<1e-12: return 'neutral'
    return 'good' if ((x>0)==higher) else 'bad'
def th(x,cls=''): return f"<th class='{cls}'>{esc(x)}</th>"
def td(x,cls=''): return f"<td class='{cls}'>{x}</td>"
def tr(cells,cls=''): return f"<tr class='{cls}'>"+''.join(cells)+"</tr>"
def pill(text,kind='neutral'): return f"<span class='pill {kind}'>{esc(text)}</span>"

cases=CLS['cases']
by_task={c['task']:c for c in cases}
idx_by_task={o['loss']['task']:o for o in IDX}

def case_rows():
    rows=[]
    for c in cases:
        o=idx_by_task[c['task']]
        rows.append(tr([
            td(f"<strong>{esc(c['task'])}</strong><br><span class='muted'>{esc(c['difficulty'])} · rep{c['rep']}</span>"),
            td(esc(c['partial']),'num'),
            td(signed(c['token_delta'],integer=True),f"num {tone(c['token_delta'],False)}"),
            td(esc(c['f2p']),'num'),td(esc(c['p2p']),'num'),
            td(f"<span class='tag bad'>{esc(c['primary_bucket'])}</span><br><span class='muted'>{esc(c['secondary_bucket'])}</span>"),
            td(esc(c['mechanism'])),
        ]))
    return '\n'.join(rows)

def packet_links():
    rows=[]
    for c in cases:
        stem=f"{c['task']}__rep{c['rep']}"
        rows.append(tr([td(f"<strong>{esc(c['task'])}</strong>"),td(f"<a href='{stem}.md'>packet md</a> · <a href='{stem}.json'>packet json</a> · <a href='review_{short_name(c['task'])}.md'>review</a>")]))
    return '\n'.join(rows)

def short_name(task):
    return {
        'claude-code-by-agents-recursive-delegation':'claude',
        'happy-dom-deterministic-intersectionobserver':'happy_dom',
        'wazero-multi-module-snapshots':'wazero',
        'vulture-persistent-analysis-cache':'vulture',
        'yjs-map-conflict-detection':'yjs',
        'obsidian-linter-link-format-conversion':'obsidian',
        'sql-formatter-bigquery-pipe-formatting':'sql_formatter',
    }[task]

def bucket_rows():
    ag=CLS['aggregate']
    data=[
        ('F2P-only losses', ag['f2p_only_losses'], 'Missed new feature semantics while preserving old tests.'),
        ('P2P regression cases', ag['p2p_regression_cases'], 'Regressed existing behavior or verifier node identity.'),
        ('Wrong-layer / wrong-scope cases', ag['wrong_layer_or_scope_cases'], 'Implementation happened at too global or too low-level a seam.'),
        ('Under-implementation / missing invariant', ag['under_implementation_or_missing_invariant_cases'], 'Patch omitted a lifecycle, invariant, fallback, or guard hidden tests expected.'),
        ('Over-elaboration / over-smart behavior', ag['over_elaboration_or_over_smart_cases'], 'Patch normalized, redesigned, or broadened beyond the task contract.'),
    ]
    return ''.join(tr([td(f"<strong>{esc(k)}</strong>"),td(str(v),'num'),td(esc(desc))]) for k,v,desc in data)

def method_rows():
    return ''.join(tr([td(str(i+1),'num'),td(esc(step))]) for i,step in enumerate(CLS['method']['comparison_steps']))

def guidance_rows():
    return ''.join(tr([td(f"<strong>{esc(c['primary_bucket'])}</strong><br><span class='muted mono'>{esc(c['task'])}</span>"),td(esc(c['guidance_implication']))]) for c in cases)

p=SUMMARY['pairs']['baseline__vs__codegraph-cli-skill']
html_doc=f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>CodeGraph solve churn deep dive</title><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--greenSoft:#e7f7ef;--redSoft:#fdeceb;--amberSoft:#fff5dd;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:24px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.13),transparent 30%),linear-gradient(180deg,#fbfdff,var(--bg));font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);line-height:1.5}}.wrap{{max-width:1460px;margin:0 auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.96);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:var(--radius)}}.hero{{padding:42px}}section{{padding:26px;margin-top:20px}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2.1rem,4.8vw,4.2rem);max-width:18ch;margin-top:14px}}h2{{font-size:clamp(1.35rem,2.2vw,2rem)}}h3{{font-size:1.05rem;margin:12px 0}}p{{color:var(--muted)}}.subtitle{{font-size:1.08rem;max-width:98ch}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}}.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase}}.pill{{padding:8px 13px;border:1px solid var(--line);background:#f8fafc;color:#31415d}}.pill.good,.tag.good{{background:var(--greenSoft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--redSoft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amberSoft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.tag{{padding:4px 9px;white-space:normal;text-align:left}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:28px}}.stat{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;min-height:118px}}.stat .label{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:850;margin-bottom:8px}}.stat .value{{display:block;font-size:clamp(1.35rem,2vw,2rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;color:var(--muted);font-size:.9rem;margin-top:8px;font-weight:650}}table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}tbody tr:hover{{background:#f8fafc}}.muted{{color:var(--muted)}}.mono,code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}code{{background:#eef2ff;border-radius:6px;padding:.12em .35em}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}.neutral{{color:#1d3fb8}}.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin:14px 0}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}}.head{{display:flex;justify-content:space-between;align-items:end;gap:14px;flex-wrap:wrap;margin-bottom:14px}}.head p{{margin:.4rem 0 0;max-width:90ch}}.foot{{text-align:center;color:var(--muted);font-size:.86rem;margin-top:24px}}@media(max-width:900px){{.stats,.grid2,.grid3{{grid-template-columns:1fr}}.hero{{padding:26px}}table{{font-size:.82rem}}th,td{{padding:7px 6px}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>Solve churn deep dive · CodeGraph CLI skill vs clean Pi low</span><h1>The +2 net hides 16 solve flips.</h1><p class='subtitle'>CodeGraph CLI solved 9 cells clean Pi missed, but lost 7 cells clean Pi solved. This report focuses on those 7 losses. The goal is not just blame assignment; it is a repeatable trajectory-analysis method for understanding skill-induced churn and eventually improving the CodeGraph skill guidance.</p><div class='pillrow'>{pill('9 CodeGraph-only solves','good')}{pill('7 clean-Pi-only solves','bad')}{pill('+2 net solves','neutral')}{pill('7/7 losses have concrete patch mechanisms','good')}{pill('not pure verifier noise','good')}</div><div class='stats'><div class='stat'><span class='label'>Net result</span><span class='value'>+2</span><span class='sub'>30 vs 28 solves</span></div><div class='stat'><span class='label'>Solve churn</span><span class='value'>16</span><span class='sub'>9 gains + 7 losses</span></div><div class='stat'><span class='label'>Loss token delta</span><span class='value'>+2.57M</span><span class='sub'>across 7 lost solves</span></div><div class='stat'><span class='label'>P2P regressions</span><span class='value'>2/7</span><span class='sub'>vulture + sql-formatter</span></div><div class='stat'><span class='label'>F2P-only misses</span><span class='value'>5/7</span><span class='sub'>feature edge/invariant misses</span></div></div></header>

<section><div class='head'><div><h2>Method: paired trajectory packet</h2><p>The repeatable technique is to reduce each solve flip to an evidence packet, then classify only after linking verifier failures to patch deltas.</p></div></div><table><thead><tr>{th('Step','num')}{th('Action')}</tr></thead><tbody>{method_rows()}</tbody></table><div class='callout'><strong>Artifacts:</strong> each case has a Markdown packet, JSON packet, and read-only reviewer note. The packet includes result metrics, f2p/p2p counts, session tool timeline, CodeGraph commands, changed files, patch excerpts, and verifier tails.</div></section>

<section><div class='head'><div><h2>Aggregate buckets</h2><p>The losses are not one thing. CodeGraph overhead is common, but the immediate failure mechanisms split across missed invariants, wrong-scope edits, protocol drift, and over-smart normalization.</p></div></div><table><thead><tr>{th('Bucket')}{th('Cases','num')}{th('Meaning')}</tr></thead><tbody>{bucket_rows()}</tbody></table><div class='callout good'><strong>Main finding:</strong> all seven lost solves have concrete patch-level explanations. None look like random verifier wobble. The churn is real behavioral divergence.</div></section>

<section><div class='head'><div><h2>The 7 clean-Pi-only solves</h2><p>Each row states the failing mechanism, not just the metric delta.</p></div></div><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ tokens','num')}{th('F2P','num')}{th('P2P','num')}{th('Bucket')}{th('Mechanism')}</tr></thead><tbody>{case_rows()}</tbody></table></section>

<section><div class='head'><div><h2>What CodeGraph changed in the trajectory</h2><p>Across the losses, CodeGraph often added structural scouting and post-edit checks. That helped confidence, but did not force the right behavioral test.</p></div></div><div class='grid3'><div class='callout'><strong>Structural confidence ≠ behavior confidence.</strong> <code>codegraph diff-impact</code> and <code>check</code> caught graph/signature issues, not hidden behavioral invariants like polling cycles, compression size guards, or cross-dialect lexer collisions.</div><div class='callout caution'><strong>Wrong seam risk.</strong> In yjs and sql-formatter, the trajectory moved to a lower/global seam instead of the existing transaction/dialect choke point.</div><div class='callout bad'><strong>Protocol drift risk.</strong> In claude-code-by-agents, the implementation redesigned event shape and continuation behavior even though hidden tests expected the existing public stream contract.</div></div></section>

<section><div class='head'><div><h2>Skill-guidance implications</h2><p>These are not final CodeGraph skill edits yet. They are the candidate lessons this analysis technique surfaces.</p></div></div><table><thead><tr>{th('Failure mode')}{th('Possible guidance improvement')}</tr></thead><tbody>{guidance_rows()}</tbody></table><div class='callout caution'><strong>Writing-great-skills framing:</strong> the future skill change should be a checkable process, not vague advice. For example: “After CodeGraph scouting, name the existing behavioral seam and the invariant tests you must preserve before editing.”</div></section>

<section><div class='head'><div><h2>Evidence packet links</h2><p>Use these for spot-checking or for a second-pass reviewer. They are intentionally deterministic and regenerate from result/session artifacts.</p></div></div><table><thead><tr>{th('Task')}{th('Artifacts')}</tr></thead><tbody>{packet_links()}</tbody></table></section>

<section><div class='head'><div><h2>Conclusion</h2></div></div><div class='grid2'><div class='callout bad'><strong>The +2 net solve count is misleading by itself.</strong> The treatment caused substantial churn: 9 wins and 7 losses. The losses are mostly threshold-sensitive but real.</div><div class='callout good'><strong>The analysis technique worked.</strong> Pairwise packet → verifier failure mapping → patch-delta classification produced actionable skill-design hypotheses rather than generic “more tokens” explanations.</div></div><div class='callout'><strong>Next analysis iteration:</strong> run the exact same packet method on the 9 CodeGraph-only solves, then compare winning and losing trajectories. The skill guidance should keep the winning patterns while preventing the seven loss modes above.</div></section>

<div class='foot'>Generated from <code>classification.json</code> and <code>loss_packets_index.json</code>. Parent report: <code>analysis/codegraph-cli-skill-36v2/index.html</code>.</div>
</div></body></html>"""
(OUT/'index.html').write_text(html_doc)
print(OUT/'index.html')
