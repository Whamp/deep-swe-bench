#!/usr/bin/env python3
from __future__ import annotations
import html, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'analysis/gpt55-low-historical-corpus/kaggle_plugin_prompt_lessons.json'
OUT=ROOT/'reports/kaggle-plugin-prompt-lessons/index.html'

def e(x): return html.escape(str(x), quote=True)

def table(items, cols):
    head=''.join(f'<th>{e(c[0])}</th>' for c in cols)
    rows=[]
    for it in items:
        cells=[]
        for _, key in cols:
            v=it.get(key,'')
            if key=='source_url': v=f'<a href="{e(v)}">source</a>'
            elif key=='file': v=f'<code>{e(v)}</code>'
            else: v=e(v)
            cells.append(f'<td>{v}</td>')
        rows.append('<tr>'+''.join(cells)+'</tr>')
    return f'<table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'

def main():
    d=json.load(open(DATA))
    rec=''.join(f'<li>{e(x)}</li>' for x in d['recommended_next_analyses'])
    cmds=''.join(f'<li><code>{e(x)}</code></li>' for x in d['plugin_run']['commands_used'])
    html_doc=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NVIDIA Kaggle plugin lessons for prompt scaffolds</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,#163d22,#07111f 42%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}}main{{max-width:1260px;margin:0 auto;padding:36px 22px 64px}}.hero,.card,.callout{{background:rgba(15,29,49,.91);border:1px solid var(--line);border-radius:24px;padding:24px}}.hero{{padding:32px;background:linear-gradient(135deg,rgba(118,185,0,.22),rgba(15,29,49,.94) 45%,rgba(96,165,250,.1))}}h1{{font-size:clamp(34px,5vw,62px);line-height:.96;letter-spacing:-.055em;margin:12px 0 16px}}h2{{margin:34px 0 12px}}p,li{{color:#dbe7fb}}.kicker{{color:#a3e635;text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:30px;line-height:1}}.muted,.stat span,.src{{color:var(--muted);font-size:12px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728;color:var(--muted)}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.pills{{display:flex;gap:10px;flex-wrap:wrap}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68);margin:10px 0 26px}}th,td{{text-align:left;vertical-align:top;padding:11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}code{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px;padding:1px 5px;font-size:12px}}a{{color:#93c5fd}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:900px){{.stats,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">NVIDIA Kaggle plugin · now credentialed</div><h1>Kaggle prompt-recovery winners suggest our next benchmark analysis should be conditional, not just clustered.</h1><p>Using NVIDIA’s Kaggle plugin with the local KGAT token, I fetched LLM Prompt Recovery competition context, top writeups, high-vote discussions, and public notebooks. The strongest transfer is a concrete analysis plan for GPT-5.5:low prompt scaffolds: find semantically similar configs with divergent outcomes, then explain the non-semantic differences.</p><div class="pills"><span class="pill good">plugin run: {e(d['plugin_run']['status'])}</span><span class="pill neutral">competition: {e(d['plugin_run']['competition'])}</span><span class="pill neutral">top 5 writeups fetched</span><span class="pill neutral">discussions + kernels cached</span></div><div class="src">Evidence dir: <code>{e(d['plugin_run']['local_evidence_dir'])}</code>. Token was loaded from <code>~/.kaggle/access_token</code> and not printed.</div></section>
<div class="stats"><div class="stat"><b>5</b><span>top writeups fetched</span></div><div class="stat"><b>14</b><span>discussion threads cached/read</span></div><div class="stat"><b>6</b><span>notebooks read</span></div><div class="stat"><b>6</b><span>recommended next analyses</span></div></div>
<section class="callout good"><h2>Updated verdict</h2><p>Kaggle’s best prompt-recovery work did not stop at embedding clusters. It combined <b>global mean prompts</b>, <b>dynamic predictions</b>, <b>retrieval/reranking</b>, <b>cluster-specific templates</b>, and <b>gates</b>. For deep-swe-bench, the analogous question is: when does a prompt scaffold help, for which task families, and which semantically similar scaffolds diverge because of tool surface, context placement, or trajectory management?</p></section>
<section class="card"><h2>Competition metric caveat</h2><p>{e(d['competition_metric']['description'])}</p><p><b>Transfer caution:</b> {e(d['competition_metric']['transfer_caution'])}</p></section>
<h2>Top writeup lessons</h2>{table(d['writeup_lessons'], [('Rank','rank'),('Method','method'),('Transfer to us','use_for_us'),('Evidence file','file'),('URL','source_url')])}
<h2>Discussion lessons</h2>{table(d['discussion_lessons'], [('Thread','title'),('Lesson','lesson'),('Transfer to us','use_for_us'),('Evidence file','file')])}
<h2>Kernel/notebook lessons</h2>{table(d['kernel_lessons'], [('Kernel','kernel_ref'),('Lesson','lesson'),('Transfer to us','use_for_us'),('Evidence file','file')])}
<div class="grid"><section class="callout caution"><h2>Recommended next analyses</h2><ol>{rec}</ol></section><section class="callout neutral"><h2>Plugin commands used</h2><ul>{cmds}</ul></section></div>
</main></body></html>'''
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(html_doc)
    print('wrote', OUT.relative_to(ROOT), OUT.stat().st_size)
if __name__=='__main__': main()
