#!/usr/bin/env python3
from __future__ import annotations
import html, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'analysis/gpt55-low-historical-corpus/corpus_overlap_vs_clean_low.json'
OUT=ROOT/'reports/gpt55-low-historical-corpus/index.html'
LOW_MED=ROOT/'analysis/prompt-scaffolds-vs-thinking-budget/prompt_scaffold_metrics.json'

def e(x): return html.escape(str(x), quote=True)
def money(x): return '—' if x is None else f'${x:,.2f}'
def num(x): return '—' if x is None else f'{x:,.0f}'
def cps(x): return '—' if x is None else (f'${x:,.2f}' if x>=0 else f'near-zero / lower total cost ({x:.2f})')

def main():
    data=json.load(open(DATA))
    rows=data['rows']
    lm=json.load(open(LOW_MED))
    ref=lm['baselines']['low_to_medium_reference']
    clean_low=lm['baselines']['clean_low']
    clean_medium=lm['baselines']['clean_medium']
    full=[r for r in rows if r['overlap_cells']==108]
    partial=[r for r in rows if r['overlap_cells']<108]
    best_extensions=[r for r in full if r['category']=='extension_or_skill_config']
    best_prompt=[r for r in full if r['category']=='prompt_or_orchestration_only']
    best_ext=max(best_extensions, key=lambda r:r['solve_delta'])
    best_pr=max(best_prompt, key=lambda r:r['solve_delta'])
    def row(r):
        tag='good' if r['solve_delta']>0 and (r['cost_per_net_solve'] is not None and r['cost_per_net_solve']<=ref['cost_per_net_solve']) else 'caution'
        if r['solve_delta']<=0: tag='bad'
        if r['category']=='clean_stock_pi': tag='neutral'
        if r['invalid_reward_cells']: tag='bad'
        pfiles='<br>'.join(f'<code>{e(p)}</code>' for p in r['prompt_files']) or '<span class="muted">none found</span>'
        sample='<br>'.join(f'<code>{e(p)}</code>' for p in r['sample_result_paths'][:2])
        return f'''<tr>
<td><span class="tag {tag}">{e(r['config'])}</span><div class="muted">{e(r['category'])}</div></td>
<td>{r['overlap_cells']}</td><td>{r['solves_on_overlap']} <span class="muted">baseline {r['clean_solves_on_overlap']}</span></td>
<td><b>{r['solve_delta']:+d}</b><div class="muted">{r['other_only']} gains / {r['clean_only']} losses</div></td>
<td>{money(r['cost_delta'])}</td><td>{cps(r['cost_per_net_solve'])}</td>
<td>{num(r['median_token_delta']/1000)}k</td><td>{r['invalid_reward_cells']}</td><td>{pfiles}</td><td>{sample}</td></tr>'''
    def cat_summary(cat):
        cr=[r for r in full if r['category']==cat and r['config']!='baseline']
        if not cr: return ''
        best=max(cr,key=lambda r:r['solve_delta'])
        return f'<li><b>{e(cat)}</b>: best {e(best["config"])} at {best["solves_on_overlap"]}/108 ({best["solve_delta"]:+d}), cost delta {money(best["cost_delta"])}.</li>'
    html_doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GPT-5.5 low historical corpus map</title><style>
:root {{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,#173d63,#07111f 42%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}} main{{max-width:1320px;margin:0 auto;padding:36px 22px 64px}} .hero,.card,.callout{{background:rgba(15,29,49,.9);border:1px solid var(--line);border-radius:24px;padding:22px}} .hero{{padding:32px;background:linear-gradient(135deg,rgba(96,165,250,.18),rgba(15,29,49,.94) 45%,rgba(52,211,153,.1))}} h1{{font-size:clamp(34px,5vw,64px);line-height:.96;letter-spacing:-.055em;margin:12px 0 16px}} h2{{margin:34px 0 12px}} p{{color:#dbe7fb;max-width:1000px}} .kicker{{color:var(--blue);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}} .stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}} .stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}} .stat b{{display:block;font-size:30px;line-height:1;letter-spacing:-.04em}} .stat span,.muted,.src{{color:var(--muted);font-size:12px}} .pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728;color:var(--muted);white-space:nowrap}} .good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}} .bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}} .caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}} .neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}} .pills{{display:flex;gap:10px;flex-wrap:wrap}} table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68)}} th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}} th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}} tr:last-child td{{border-bottom:0}} code{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px;padding:1px 5px;font-size:12px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} @media(max-width:900px){{.stats,.grid{{grid-template-columns:1fr}} table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">Historical corpus map · GPT-5.5 low · clean 36_v2 overlap</div><h1>The narrow prompt report missed the bigger GPT-5.5:low story.</h1>
<p>This report inventories <b>{len(rows)}</b> historical GPT-5.5:low result configs and compares every available overlapping cell to the clean 36_v2 stock-Pi baseline. The prompt-only conclusion still holds, but the broader corpus shows where actual wrappers/extensions sit relative to the clean low→medium thinking upgrade.</p>
<div class="pills"><span class="pill neutral">clean low: {clean_low['solves']}/108</span><span class="pill neutral">clean medium: {clean_medium['solves']}/108</span><span class="pill neutral">low→medium: +{ref['solves']} solves · {money(ref['total_cost'])}</span><span class="pill caution">partial subsets separated</span><span class="pill bad">invalid reward cells flagged</span></div>
<div class="src">Evidence: <code>{e(str(DATA.relative_to(ROOT)))}</code> generated from <code>{e(data['baseline_manifest'])}</code> and result.json files under <code>results/gpt-5.5/low/</code>.</div></section>
<div class="stats"><div class="stat"><b>{len(full)}</b><span>configs with full 108-cell overlap</span></div><div class="stat"><b>{best_ext['solve_delta']:+d}</b><span>best extension/wrapper delta: {e(best_ext['config'])}</span></div><div class="stat"><b>{best_pr['solve_delta']:+d}</b><span>best prompt/orchestration-only delta: {e(best_pr['config'])}</span></div><div class="stat"><b>{ref['solves']:+d}</b><span>clean low→medium reference delta</span></div></div>
<section class="callout good"><h2>Updated verdict</h2><p>The broader GPT-5.5:low corpus changes the framing. <b>pi-codex-goal</b> and <b>codebase-memory-max-pi-codex-goal</b> nearly close the raw solve gap to clean medium at low thinking ({best_ext['solve_delta']:+d} vs +{ref['solves']} solves), but they are less cost-efficient than simply raising thinking level. Among prompt-only additions, <b>{e(best_pr['config'])}</b> remains the best pure scaffold at {best_pr['solve_delta']:+d} solves and {money(best_pr['cost_delta'])} extra cost. So prompt scaffolds are cheap but limited; wrappers can be powerful but usually expensive; medium thinking remains the hard reference line.</p></section>
<div class="grid"><section class="card"><h2>Category winners</h2><ul>{''.join(cat_summary(c) for c in sorted({r['category'] for r in full}))}</ul></section><section class="card"><h2>Important cautions</h2><ul><li>Comparisons use overlapping cells against clean 36_v2; rows with fewer than 108 overlap cells are context, not full evidence.</li><li>OMP rows are harness/tool-surface context, not clean Pi prompt-only evidence.</li><li><code>pi-dynamic-workflows</code> has 21 invalid reward cells in its 36-cell overlap and should be treated as a failure-mode artifact.</li><li>Prompt files are listed when present; extension behavior is not reducible to prompt text.</li></ul></section></div>
<h2>Full 108-cell overlap table</h2><table><thead><tr><th>Config</th><th>N</th><th>Solves</th><th>Delta</th><th>Cost Δ</th><th>$/net solve</th><th>Median token Δ</th><th>Invalid</th><th>Prompt files</th><th>Sample evidence</th></tr></thead><tbody>{''.join(row(r) for r in full)}</tbody></table>
<h2>Partial-overlap historical rows</h2><p>These runs touch only part of the clean 36_v2 baseline cell set. They can suggest follow-up experiments, but should not be mixed with the full 108-cell comparisons.</p><table><thead><tr><th>Config</th><th>N</th><th>Solves</th><th>Delta</th><th>Cost Δ</th><th>$/net solve</th><th>Median token Δ</th><th>Invalid</th><th>Prompt files</th><th>Sample evidence</th></tr></thead><tbody>{''.join(row(r) for r in partial)}</tbody></table>
<section class="callout caution"><h2>What this adds beyond the prompt-scaffold report</h2><p>The first report answered a narrow prompt-only question. This corpus map shows the full historical landscape: goal scaffolding is the strongest low-thinking wrapper, codebase-memory by itself is modest, recursive/workflow tools are expensive or failure-prone in these runs, and several memory/ponytail configs cost more without beating clean low by much. The next deeper report should drill into <b>why pi-codex-goal gets +20 solves</b> and whether its gains are prompt/process, tool behavior, or trajectory-management effects.</p></section>
</main></body></html>'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_doc)
    print('wrote', OUT.relative_to(ROOT), 'bytes', OUT.stat().st_size)
if __name__=='__main__': main()
