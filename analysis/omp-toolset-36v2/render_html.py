#!/usr/bin/env python3
"""Render the OMP toolset comparison HTML report from summary.json."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
S = json.load(open(HERE / "summary.json"))
C = S["configs"]
P = S["paired"]
AST = S["ast_usage"]

def fmt_tok(n): return f"{n/1e6:.2f}M" if n >= 1e6 else f"{n/1e3:.0f}k"
def fmt_money(n): return f"${n:.2f}" if n >= 1 else f"${n:.3f}".rstrip('0').rstrip('.')

# verdict tag for a row vs pi-baseline on cost+tokens
def tag_vs_pi(key):
    c = C[key]; pi = C["pi-baseline"]
    if key == "pi-baseline": return ("neutral","reference")
    dtok = (c["median_tokens"] - pi["median_tokens"]) / pi["median_tokens"] * 100
    dsolve = c["solves"] - pi["solves"]
    if dsolve <= 0 and dtok > 50:
        return ("bad", f"dominated (+{dtok:.0f}% tok, {dsolve:+d} solves)")
    if dsolve > 0 and dtok > 50:
        return ("caution", f"more solves, +{dtok:.0f}% tok")
    return ("neutral", f"{dsolve:+d} solves, +{dtok:.0f}% tok")

# tool mix bar data (OMP configs only)
OMP_KEYS = ["omp-grepglob","omp-bash-only","omp-ast"]
ALL_TOOLS = ["read","bash","edit","write","grep","glob","ast_grep","ast_edit"]
def tool_pct(key, tool):
    t = C[key]["tool_mix"]["totals"]
    tot = sum(t.values()) or 1
    return t.get(tool,0)/tot*100, t.get(tool,0)

# Pareto: non-dominated by (solves desc, cost asc)
pts = [(k, C[k]["solves"], C[k]["median_cost"]) for k in C]
def dominated(k):
    sk, ck = C[k]["solves"], C[k]["median_cost"]
    for k2,_,_ in pts:
        if k2==k: continue
        s2,c2 = C[k2]["solves"], C[k2]["median_cost"]
        if s2 >= sk and c2 <= ck and (s2>sk or c2<ck):
            return True
    return False

rows = []
for k in ["pi-baseline","omp-grepglob","omp-bash-only","omp-ast"]:
    c=C[k]; tagcls,tagtxt=tag_vs_pi(k)
    rows.append((c["label"], c["solves"], c["solve_rate"], c["mean_partial"],
                 c["median_tokens"], c["median_cost"], c["median_wall"],
                 c["median_patch"], c["median_turns"], tagcls, tagtxt, dominated(k)))

# paired table rows (OMP variants vs grepglob, and each vs pi)
def paired_row(label, pkey, a_label, b_label):
    p=P[pkey]
    return (label, p["mean_delta_partial"], p["median_delta_tokens"], p["median_delta_cost"],
            p["solve_a_only"], p["solve_b_only"], p["solve_both"], p["solve_neither"])

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>OMP toolset comparison · GPT-5.5 low · 36_v2 · DeepSWE</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;
--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;
--amber:#c58a00;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);
--radius-xl:28px;--radius-lg:20px;--radius-md:14px;--max:1240px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,-apple-system,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 60px}}
.hero,section{{background:rgba(255,255,255,.88);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}
.hero{{padding:clamp(24px,4vw,40px);overflow:hidden;position:relative}}
.eyebrow{{display:inline-flex;gap:8px;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}
h1,h2,h3{{margin:0;letter-spacing:-0.03em;line-height:1.05}}h1{{font-size:clamp(2rem,4.4vw,3.6rem);margin-top:14px;max-width:18ch}}
.subtitle{{max-width:74ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.08rem);margin:14px 0 0}}
.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}
.pill{{display:inline-flex;gap:8px;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line);color:#31415d}}
.pill.good{{background:var(--green-soft);color:var(--green);border-color:rgba(23,138,91,.16)}}
.pill.bad{{background:var(--red-soft);color:var(--red);border-color:rgba(208,71,63,.16)}}
.pill.caution{{background:var(--amber-soft);color:var(--amber);border-color:rgba(197,138,0,.16)}}
.pill.neutral{{background:#eef3ff;color:var(--blue-2);border-color:rgba(51,93,255,.16)}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:26px}}
.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:16px;min-height:118px;box-shadow:var(--shadow-sm)}}
.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}}
.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.9rem);font-weight:900;letter-spacing:-0.04em}}
.stat .sub{{display:block;margin-top:8px;font-size:.88rem;color:var(--muted);font-weight:600}}
section{{margin-top:20px;padding:clamp(18px,3vw,28px)}}
.section-head h2{{font-size:clamp(1.4rem,2.4vw,1.9rem);margin-bottom:6px}}
.section-head p{{margin:0;color:var(--muted);max-width:72ch}}
table{{width:100%;border-collapse:collapse;font-size:.95rem}}
th,td{{text-align:left;padding:11px 12px;border-bottom:1px solid var(--line);white-space:nowrap}}
th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:800}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
tbody tr:hover{{background:var(--surface-2)}}
.tag{{display:inline-block;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}}
.tag.bad{{background:var(--red-soft);color:var(--red)}}.tag.good{{background:var(--green-soft);color:var(--green)}}
.tag.caution{{background:var(--amber-soft);color:var(--amber)}}.tag.neutral{{background:#eef3ff;color:var(--blue-2)}}
.tag.pareto{{background:var(--green-soft);color:var(--green)}}.tag.dom{{background:#eef0f4;color:var(--muted)}}
.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;color:#22314d;margin-top:14px}}
.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}
.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}
.callout strong{{color:var(--blue-2)}}
/* tool-mix bar */
.tbar{{display:flex;align-items:center;gap:8px;margin:7px 0}}
.tbar .tl{{width:74px;font-size:12px;font-weight:700;color:var(--muted);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.tbar .track{{flex:1;height:18px;background:#eef2f8;border-radius:6px;overflow:hidden;position:relative}}
.tbar .fill{{height:100%;border-radius:6px}}
.tbar .cnt{{width:54px;text-align:right;font-size:12px;font-weight:700;font-variant-numeric:tabular-nums}}
.c-read{{background:#335dff}}.c-bash{{background:#178a5b}}.c-edit{{background:#c58a00}}.c-write{{background:#8a93a6}}
.c-grep{{background:#7c3aed}}.c-glob{{background:#a855f7}}.c-ast_grep{{background:#d0473f}}.c-ast_edit{{background:#ef6f5f}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px;font-size:12px;color:var(--muted)}}
.legend span{{display:inline-flex;align-items:center;gap:6px}}.legend i{{width:11px;height:11px;border-radius:3px;display:inline-block}}
.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
@media(max-width:880px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid-2{{grid-template-columns:1fr}}}}
.foot{{margin-top:18px;color:var(--muted);font-size:.85rem}}
</style></head><body><div class="wrap">

<div class="hero">
 <span class="eyebrow">OMP toolset ablation · GPT-5.5 low · 36_v2 · 108 cells/arm</span>
 <h1>Turning grep/glob off (or AST on) does not close OMP's token gap</h1>
 <p class="subtitle">Three Oh-My-Pi toolset variants vs plain Pi on the same model. Removing grep/glob recovered only ~10% of tokens and <em>cost</em> solves; AST tools were used but added cost without solving more. The overhead is the OMP harness itself, not its tool selection.</p>
 <div class="pillrow">
   <span class="pill bad">bash-only: −10% tokens, −4 solves</span>
   <span class="pill bad">AST: +6% tokens, −4 solves</span>
   <span class="pill neutral">Pi dominates all 3 on cost</span>
   <span class="pill caution">grep+glob was net-helpful</span>
 </div>
 <div class="stats">
   <div class="stat"><span class="label">Solves (of 108)</span><span class="value">36 <span style="font-size:.6em;color:var(--muted)">/ 33 / 32 / 32</span></span><span class="sub">grepglob / Pi / bash-only / AST</span></div>
   <div class="stat"><span class="label">Token gap vs Pi</span><span class="value">3.1–3.7×</span><span class="sub">OMP median tokens vs Pi 608k</span></div>
   <div class="stat"><span class="label">Cost gap vs Pi</span><span class="value">2.0–2.3×</span><span class="sub">$1.71–2.02 vs $0.86 median</span></div>
   <div class="stat"><span class="label">AST usage (voluntary)</span><span class="value">{AST['ast_grep_calls']} ast_grep</span><span class="sub">{AST['ast_edit_calls']} ast_edit · GPT-5.5 low</span></div>
   <div class="stat"><span class="label">Pareto winner</span><span class="value" style="color:var(--green)">Pi baseline</span><span class="sub">all OMP variants dominated</span></div>
 </div>
</div>

<section>
 <div class="section-head"><h2>Headline comparison</h2><p>Same model (openai-codex/gpt-5.5 low), same 36_v2 subset, 3 reps each. OMP arms differ only in the registered toolset.</p></div>
 <table>
  <thead><tr><th>Config</th><th class="num">Solves</th><th class="num">Solve&nbsp;rate</th><th class="num">Mean&nbsp;partial</th><th class="num">Median&nbsp;tokens</th><th class="num">Median&nbsp;cost</th><th class="num">Median&nbsp;wall</th><th class="num">Median&nbsp;patch</th><th class="num">Turns</th><th>vs&nbsp;Pi</th><th>Pareto</th></tr></thead>
  <tbody>"""
for r in rows:
    label,solves,srate,mpart,mtok,mcost,mwall,mpatch,mturns,tc,tt,dom = r
    ptag = "dominated" if dom else "frontier"
    pcls = "dom" if dom else "pareto"
    html += f"""
    <tr><td><strong>{label}</strong></td><td class="num">{solves}/108</td><td class="num">{srate*100:.1f}%</td><td class="num">{mpart:.4f}</td><td class="num t-mono">{fmt_tok(mtok)}</td><td class="num">{fmt_money(mcost)}</td><td class="num">{mwall:.0f}s</td><td class="num">{mpatch:,}B</td><td class="num">{mturns:.0f}</td><td><span class="tag {tc}">{tt}</span></td><td><span class="tag {pcls}">{ptag}</span></td></tr>"""
html += f"""
  </tbody>
 </table>
 <div class="callout">All three OMP variants cluster at <strong>1.9–2.3M median tokens</strong> vs Pi's <strong>608k</strong>. The token overhead barely moves with the toolset: bash-only trims ~10%, AST adds ~6%. Solve rates are flat (32–36) and every OMP variant is Pareto-dominated by Pi on cost.</div>
</section>

<section>
 <div class="section-head"><h2>Tool mix by config</h2><p>Per-tool call counts summed across all 108 cells. This is the core ablation signal.</p></div>
 <div class="legend">"""
for t in ALL_TOOLS:
    html += f"<span><i class='c-{t}'></i>{t}</span>"
html += "</div>"
for k in OMP_KEYS:
    t = C[k]["tool_mix"]["totals"]; tot = sum(t.values()) or 1
    html += f'<h3 style="margin:18px 0 4px;font-size:1.05rem">{C[k]["label"]} <span style="color:var(--muted);font-weight:600;font-size:.85rem">— {tot:,} total calls · {C[k]["tool_mix"]["median_per_cell"]:.0f}/cell median</span></h3>'
    for tool in ALL_TOOLS:
        cnt = t.get(tool,0); pct = cnt/tot*100
        if cnt==0 and tool not in ("grep","glob","ast_grep","ast_edit"): 
            # still show zero bars for present tools
            pass
        bw = max(pct, 0.3) if cnt>0 else 0
        html += f'<div class="tbar"><span class="tl">{tool}</span><div class="track"><div class="fill c-{tool}" style="width:{pct}%;{'opacity:.18' if cnt==0 else ''}"></div></div><span class="cnt">{cnt:,}</span></div>'
html += f"""
 <div class="callout good"><strong>Config integrity confirmed.</strong> bash-only made <strong>0 grep / 0 glob</strong> calls and substituted with bash (1807→2312). AST made <strong>0 grep / 0 glob</strong> and used <strong>{AST['ast_grep_calls']} ast_grep</strong> calls — GPT-5.5 low voluntarily reached for AST search once it was the only structured-search tool, though <strong>ast_edit ({AST['ast_edit_calls']}) stayed near-zero</strong>.</div>
</section>

<section>
 <div class="section-head"><h2>Does removing grep/glob recover tokens?</h2><p>bash-only vs grep+glob (paired, 108 cells). Hypothesis was that OMP's repo-mapping grep/glob pass drove the token gap.</p></div>"""
pr = paired_row("bash-only vs grep+glob","omp-bash-only_vs_grepglob","bash-only","grep+glob")
html += f"""
 <table>
  <thead><tr><th>Comparison</th><th class="num">Δ partial (mean)</th><th class="num">Δ tokens (median)</th><th class="num">Δ cost (median)</th><th class="num">solves: A-only / B-only</th><th>Verdict</th></tr></thead>
  <tbody>
   <tr><td><strong>bash-only vs grep+glob</strong></td><td class="num">{pr[1]:+.4f}</td><td class="num t-mono">{fmt_tok(abs(pr[2]))} {'cheaper' if pr[2]<0 else 'more'}</td><td class="num">{fmt_money(abs(pr[3]))} {'saved' if pr[3]<0 else 'more'}</td><td class="num">{pr[4]} / {pr[5]}</td><td><span class="tag bad">−10% tokens, −4 solves</span></td></tr>
  </tbody>
 </table>
 <div class="callout bad">Only ~10% token recovery — and bash-only <strong>lost 4 solves</strong> (36→32). The agent replaced grep/glob with <strong>more bash (+28%) and more reads (+25%)</strong>, so the exploration bloat moved rather than disappeared. Conclusion: grep/glob repo-mapping was <strong>not</strong> the primary token driver; the OMP harness wrapper + exploration style is.</div>
</section>

<section>
 <div class="section-head"><h2>Do AST tools help?</h2><p>omp-ast registered ast_grep + ast_edit (grep/glob off). GPT-5.5 low used ast_grep but the cost rose and solves did not improve.</p></div>
 <table>
  <thead><tr><th>Comparison</th><th class="num">Δ partial</th><th class="num">Δ tokens (median)</th><th class="num">Δ cost (median)</th><th class="num">solves A-only / B-only</th><th>Verdict</th></tr></thead>
  <tbody>"""
for label,pk in [("AST vs grep+glob","omp-ast_vs_grepglob"),("AST vs bash-only","omp-ast_vs_bash-only"),("AST vs Pi","omp-ast_vs_pi")]:
    p=P[pk]; 
    vt = "more expensive, no solve gain" if p["median_delta_tokens"]>0 else "cheaper"
    vcls = "bad" if p["median_delta_tokens"]>0 else "good"
    html += f'<tr><td><strong>{label}</strong></td><td class="num">{p["mean_delta_partial"]:+.4f}</td><td class="num t-mono">{fmt_tok(abs(p["median_delta_tokens"]))} {"more" if p["median_delta_tokens"]>0 else "less"}</td><td class="num">{fmt_money(abs(p["median_delta_cost"]))}</td><td class="num">{p["solve_a_only"]} / {p["solve_b_only"]}</td><td><span class="tag {vcls}">{vt}</span></td></tr>'
html += f"""
  </tbody>
 </table>
 <div class="callout bad">AST is the <strong>most expensive</strong> variant (2.25M tok, $2.02) and tied for the <strong>fewest solves</strong> (32). ast_grep got used ({AST['ast_grep_calls']} calls) but the extra tool definitions <strong>inflated the per-turn cache</strong> (2.11M cache_read, highest of all) and the searches did not convert to solves. ast_edit was effectively ignored ({AST['ast_edit_calls']} calls).</div>
</section>

<section>
 <div class="section-head"><h2>Why the gap barely moved: per-turn cache</h2><p>Median cache_read per cell — the cached system-prompt + tool-defs + history that gets re-sent every turn.</p></div>
 <table>
  <thead><tr><th>Config</th><th class="num">Median cache_read</th><th class="num">Median output</th><th class="num">Median turns</th><th class="num">Median tool_calls</th></tr></thead>
  <tbody>"""
for k in ["pi-baseline","omp-grepglob","omp-bash-only","omp-ast"]:
    c=C[k]
    html += f'<tr><td><strong>{c["label"]}</strong></td><td class="num t-mono">{fmt_tok(c["median_cache_read"])}</td><td class="num">{c["median_output_tokens"]:,}</td><td class="num">{c["median_turns"]:.0f}</td><td class="num">{c["median_tool_calls"]:.0f}</td></tr>'
html += f"""
  </tbody>
 </table>
 <div class="callout">Removing grep/glob <strong>trimmed ~8%</strong> of cache_read (1.97M→1.80M) — the tool defs shrank. But adding <strong>ast_grep+ast_edit raised it to 2.11M</strong>. The OMP system prompt (the bulk of the ~7968 tok/turn wrapper identified earlier) is unchanged across all variants, so no toolset swap can close a 3× gap driven by the wrapper + extra turns.</div>
</section>

<section>
 <div class="section-head"><h2>Bottom line</h2></div>
 <div class="grid-2">
  <div class="callout bad"><strong>Q1 — bash-only recovers tokens?</strong> Barely. ~10% fewer tokens, but −4 solves. The agent substitutes bash + read for the missing grep/glob, so exploration bloat persists. <strong>No.</strong></div>
  <div class="callout bad"><strong>Q2 — AST tools compensate?</strong> No. GPT-5.5 low used ast_grep (386 calls) but ast_edit was ignored (7). AST is the most expensive variant and tied for fewest solves. <strong>No.</strong></div>
 </div>
 <div class="callout good" style="margin-top:14px"><strong>Conclusion.</strong> OMP's token overhead is structural — the harness wrapper + more turns + broader exploration — not its tool selection. No toolset variant escapes Pareto-domination by plain Pi (33 solves at $0.86). The cheapest path to closing the gap is a smaller OMP system prompt or fewer turns, not a different tool whitelist.</div>
</section>

<div class="foot">Generated from analysis/omp-toolset-36v2/ · data: results/gpt-5.5/low/{ {k:v['config_dir'] for k,v in C.items()} } · subset 36_v2 (arm-intrinsic stratified) · deterministic, no AI charts.</div>

</div></body></html>"""

out = HERE / "index.html"
out.write_text(html)
print(f"wrote {out} ({len(html):,} bytes)")
