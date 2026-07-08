#!/usr/bin/env python3
from __future__ import annotations
import html, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ANA=ROOT/'analysis/gpt55-low-historical-corpus/prompt_embedding_analysis.json'
CORP=ROOT/'analysis/gpt55-low-historical-corpus/corpus_overlap_vs_clean_low.json'
OUT=ROOT/'reports/gpt55-low-prompt-embedding-analysis/index.html'

def e(x): return html.escape(str(x), quote=True)
def money(x): return f'${x:,.1f}'

def main():
    ana=json.load(open(ANA)); docs={d['id']:d for d in ana['documents']}
    def cluster_rows(section):
        rows=[]
        for idx,g in enumerate(ana[section]['clusters'],1):
            full=[docs[i] for i in g if docs[i]['overlap_cells']==108]
            if not full: continue
            best=max(full,key=lambda d:d['solve_delta'])
            worst=min(full,key=lambda d:d['solve_delta'])
            members='<br>'.join(f'<code>{e(d["config"])}</code> <span class="muted">{d["solve_delta"]:+d}, {money(d["cost_delta"])}</span>' for d in sorted(full,key=lambda d:-d['solve_delta']))
            paths='<br>'.join(e(p) for p in best['paths'][:4])
            tag='good' if best['solve_delta']>=7 else ('caution' if best['solve_delta']>0 else 'bad')
            rows.append(f'<tr><td><span class="tag {tag}">cluster {idx}</span><div class="muted">{len(g)} embedded docs · {len(full)} full-overlap configs</div></td><td><b>{best["config"]}</b><div class="muted">best {best["solve_delta"]:+d} solves · {money(best["cost_delta"])} cost Δ</div></td><td>{worst["solve_delta"]:+d}..{best["solve_delta"]:+d}</td><td>{members}</td><td><span class="muted">best evidence paths</span><br>{paths}</td></tr>')
        return ''.join(rows)
    def pair_rows(section):
        out=[]
        for p in ana[section]['top_pairs'][:18]:
            a,b=docs[p['a']],docs[p['b']]
            out.append(f'<tr><td>{p["similarity"]:.3f}</td><td><code>{e(a["config"])}</code><div class="muted">{a["solve_delta"]:+d}, {money(a["cost_delta"])}</div></td><td><code>{e(b["config"])}</code><div class="muted">{b["solve_delta"]:+d}, {money(b["cost_delta"])}</div></td></tr>')
        return ''.join(out)
    html_doc=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GPT-5.5 low prompt embedding analysis</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,#163a5d,#07111f 44%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}}main{{max-width:1280px;margin:0 auto;padding:36px 22px 70px}}.hero,.callout,.card{{background:rgba(15,29,49,.91);border:1px solid var(--line);border-radius:24px;padding:24px}}.hero{{padding:32px;background:linear-gradient(135deg,rgba(96,165,250,.18),rgba(15,29,49,.94) 48%,rgba(52,211,153,.1))}}h1{{font-size:clamp(34px,5vw,62px);line-height:.96;letter-spacing:-.055em;margin:12px 0 16px}}h2{{margin:34px 0 12px}}p{{color:#dbe7fb;max-width:980px}}.kicker{{color:var(--blue);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:30px;line-height:1}}.muted,.stat span,.src{{color:var(--muted);font-size:12px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728;color:var(--muted)}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.pills{{display:flex;gap:10px;flex-wrap:wrap}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68)}}th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}code{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px;padding:1px 5px;font-size:12px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:900px){{.stats,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">Octen embedding analysis · GPT-5.5 low prompt surfaces</div><h1>Semantic prompt clusters mostly match the hand taxonomy — but they expose non-obvious outcome splits.</h1><p>I embedded historical GPT-5.5:low prompt/config text with Will’s local <b>{e(ana['model'])}</b> endpoint and clustered both explicit prompt files and broader extension prompt surfaces. This is a semantic-neighborhood analysis, not causal proof.</p><div class="pills"><span class="pill neutral">endpoint: {e(ana['embedding_endpoint'])}</span><span class="pill neutral">{ana['dimensions']}-dim vectors</span><span class="pill neutral">{len(ana['documents'])} documents</span><span class="pill caution">threshold cosine ≥ 0.86</span></div><div class="src">Artifacts: <code>analysis/gpt55-low-historical-corpus/prompt_embedding_analysis.json</code>, <code>prompt_embeddings.json</code>.</div></section>
<div class="stats"><div class="stat"><b>{len([d for d in ana['documents'] if d['doc_type']=='explicit_prompt'])}</b><span>explicit prompt documents</span></div><div class="stat"><b>{len([d for d in ana['documents'] if d['doc_type']=='prompt_surface'])}</b><span>broader prompt-surface documents</span></div><div class="stat"><b>+20</b><span>pi-codex-goal remains semantic singleton and strongest outcome</span></div><div class="stat"><b>+7</b><span>best prompt-only cluster outcome</span></div></div>
<section class="callout good"><h2>Embedding takeaways</h2><ul><li>The OMP Pi-like prompts, codebase-memory prompts, observational-memory prompts, ponytail prompts, codegraph prompts, and prompt-ablation preamble/workflow prompts separate cleanly.</li><li>The engineer preamble and workflow checklist land in the same semantic cluster, yet their outcomes range from +3 to +7 solves, so small wording/interactions matter.</li><li><code>pi-codex-goal</code> is a semantic singleton, matching its unusually large +20 solve outcome.</li><li>Codebase-memory prompt surfaces cluster tightly, but performance ranges from +3 to +20 because adding goal creation changes behavior beyond semantic prompt similarity.</li></ul></section>
<h2>Explicit prompt-file clusters</h2><table><thead><tr><th>Cluster</th><th>Best member</th><th>Delta range</th><th>Full-overlap members</th><th>Evidence paths</th></tr></thead><tbody>{cluster_rows('explicit_prompt_analysis')}</tbody></table>
<h2>Broader prompt-surface clusters</h2><p>This second pass includes selected non-vendor extension files whose names suggest instructions, messages, goals, memory, workflows, hooks, or prompts. Treat it as prompt-surface/source similarity, not pure prompt text.</p><table><thead><tr><th>Cluster</th><th>Best member</th><th>Delta range</th><th>Full-overlap members</th><th>Evidence paths</th></tr></thead><tbody>{cluster_rows('prompt_surface_analysis')}</tbody></table>
<div class="grid"><section class="card"><h2>Top explicit-prompt nearest pairs</h2><table><thead><tr><th>cosine</th><th>A</th><th>B</th></tr></thead><tbody>{pair_rows('explicit_prompt_analysis')}</tbody></table></section><section class="card"><h2>Top prompt-surface nearest pairs</h2><table><thead><tr><th>cosine</th><th>A</th><th>B</th></tr></thead><tbody>{pair_rows('prompt_surface_analysis')}</tbody></table></section></div>
<section class="callout caution"><h2>What to do next</h2><p>The embedding analysis is good for clustering and duplicate detection, but outcome prediction needs a second pass: annotate cluster members by concrete instruction deltas, then compare paired win/loss cells inside each cluster. The highest-value target is explaining why <code>pi-codex-goal</code> is semantically isolated and nearly reaches medium-thinking solve count.</p></section>
</main></body></html>'''
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(html_doc)
    print('wrote', OUT.relative_to(ROOT), OUT.stat().st_size)
if __name__=='__main__': main()
