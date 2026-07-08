#!/usr/bin/env python3
"""CodeGraph retrospective report renderer. Data is hard-coded from the verified
unified-metrics pass (/tmp/cg_full.py output + analysis/codegraph-* summaries +
the churn-deep-dive classification.json)."""
from pathlib import Path
import html, json

OUT = Path(__file__).resolve().parent
esc = html.escape

# ---- verified data ----
# 12_v0 from analysis/codegraph-12v0-results.txt (historical, n=36 per arm)
fam12 = [
    # config, solve, partial, dpartial_vs_base, dsolve_vs_base, sig, med_tok, med_cost
    ("baseline",                 0.250, 0.990, "—", "—",     "",     743, 0.92),
    ("observational-memory",     0.444, 0.976, "−0.014", "+0.194", "",   786, 1.10),
    ("codegraph-skill",          0.333, 0.986, "−0.004", "+0.083", "ns", 953, 1.17),
    ("codegraph-impact (names)", 0.306, 0.952, "−0.038", "+0.056", "*",  827, 1.06),
    ("codegraph-auto (counts)",  0.278, 0.899, "−0.091", "+0.028", "*", 1015, 1.17),
]
fam36 = [
    # config, solve_count, solve_rate, partial, med_tok, med_cost, tot_cost
    ("baseline",                 28, 0.259, 0.957,  598678, 0.83, 102.19),
    ("baseline-preamble-orch",   33, 0.306, 0.967,  608190, 0.86, 102.03),
    ("baseline-wf-only",         35, 0.324, 0.970,  729401, 0.96, 118.17),
    ("codegraph-skill",          28, 0.259, 0.962,  731003, 0.99, 118.74),
    ("codegraph-cli-skill",      30, 0.278, 0.967, 1033286, 1.09, 130.45),
    ("codegraph-cli-skill-seam", 31, 0.287, 0.964, 1068000, 1.02, 120.36),
    ("medium/baseline",          50, 0.463, 0.980, 1552840, 1.62, 195.36),
]
passk = [
    # config, p1, p3, med_cost, always3, seqretry
    ("low/baseline",                 0.259, 0.389, 0.83, 2.48, 1.90),
    ("low/baseline-preamble-orch",   0.306, 0.472, 0.86, 2.59, 1.88),
    ("low/baseline-wf-only",         0.324, 0.444, 0.96, 2.87, 2.04),
    ("low/codegraph-cli-skill",      0.278, 0.417, 1.09, 3.28, 2.46),
    ("low/codegraph-cli-skill-seam", 0.287, 0.389, 1.02, 3.07, 2.27),
    ("low/pi-codex-goal",            0.444, 0.694, 1.97, 5.92, 3.68),
    ("medium/baseline",              0.463, 0.722, 1.62, 4.86, 2.96),
]

def fam12_rows():
    r=[]
    for cfg,sol,part,dp,ds,sig,tok,cost in fam12:
        tone = "bad" if (sig=="*") else ("neutral" if cfg=="baseline" or cfg=="observational-memory" else "caution")
        r.append(f"<tr><td><strong>{esc(cfg)}</strong></td><td class='num'>{sol:.1%}</td><td class='num'>{part:.3f}</td>"
                 f"<td class='num'>{esc(dp)}</td><td class='num'>{esc(ds)} <span class='muted'>{esc(sig)}</span></td>"
                 f"<td class='num'>{tok:,}</td><td class='num'>${cost:.2f}</td></tr>")
    return "\n".join(r)

def fam36_rows():
    r=[]
    dominated = {"codegraph-skill","codegraph-cli-skill","codegraph-cli-skill-seam"}
    for cfg,sc,sr,part,tok,cost,tc in fam36:
        tag = "<span class='tag bad'>dominated</span>" if cfg in dominated else ("<span class='tag good'>frontier</span>" if cfg in ("baseline-wf-only","medium/baseline") else "<span class='tag neutral'>ref</span>")
        r.append(f"<tr><td><strong>{esc(cfg)}</strong> {tag}</td><td class='num'>{sc}/108</td><td class='num'>{sr:.1%}</td>"
                 f"<td class='num'>{part:.3f}</td><td class='num'>{tok:,}</td><td class='num'>${cost:.2f}</td><td class='num'>${tc:.0f}</td></tr>")
    return "\n".join(r)

def passk_rows():
    r=[]
    for cfg,p1,p3,mc,a3,sr in passk:
        dom = cfg in ("low/codegraph-cli-skill","low/codegraph-cli-skill-seam","low/pi-codex-goal","low/baseline","low/baseline-wf-only")
        tag = "<span class='tag bad'>dominated</span>" if cfg.startswith("low/codegraph") else ("<span class='tag good'>frontier</span>" if cfg in ("medium/baseline","low/baseline-preamble-orch") else "")
        r.append(f"<tr><td><strong>{esc(cfg)}</strong> {tag}</td><td class='num'>{p1:.1%}</td><td class='num'>{p3:.1%}</td>"
                 f"<td class='num'>${mc:.2f}</td><td class='num'>${a3:.2f}</td><td class='num'>${sr:.2f}</td></tr>")
    return "\n".join(r)

# Pareto bar chart (solve vs cost) - simple inline SVG
def pareto_svg():
    pts = [("baseline",28,0.83),("baseline-wf",35,0.96),("codegraph-skill",28,0.99),
           ("codegraph-cli-skill",30,1.09),("codegraph-cli-seam",31,1.02),("medium",50,1.62)]
    W,H=560,300; pad=46
    maxs=55; maxc=1.8
    def x(c): return pad + (c/maxc)*(W-pad-20)
    def y(s): return H-30 - (s/maxs)*(H-30-pad)
    s=f"<svg viewBox='0 0 {W} {H}' class='chart' role='img' aria-label='Pareto chart solve vs cost'>"
    # axes
    s+=f"<line x1='{pad}' y1='{H-30}' x2='{W-10}' y2='{H-30}' stroke='#d9e1ec'/><line x1='{pad}' y1='{pad-10}' x2='{pad}' y2='{H-30}' stroke='#d9e1ec'/>"
    for sv in (0,15,30,45):
        yy=y(sv); s+=f"<line x1='{pad}' y1='{yy}' x2='{W-10}' y2='{yy}' stroke='#eef2f7'/><text x='{pad-8}' y='{yy+4}' text-anchor='end' font-size='10' fill='#607086'>{sv}</text>"
    for cv in (0.5,1.0,1.5):
        xx=x(cv); s+=f"<text x='{xx}' y='{H-12}' text-anchor='middle' font-size='10' fill='#607086'>${cv}</text>"
    s+=f"<text x='10' y='{pad-18}' font-size='11' fill='#102033' font-weight='700'>solves / 108</text>"
    s+=f"<text x='{W-10}' y='{H-12}' text-anchor='end' font-size='11' fill='#102033' font-weight='700'>median $/cell →</text>"
    colors={"baseline":"#335dff","baseline-wf":"#178a5b","codegraph-skill":"#d0473f","codegraph-cli-skill":"#d0473f","codegraph-cli-seam":"#d0473f","medium":"#178a5b"}
    frontier={"baseline-wf","medium"}
    for n,sv,cv in pts:
        xx,yy=x(cv),y(sv); c=colors[n]
        s+=f"<circle cx='{xx}' cy='{yy}' r='{8 if n in frontier else 6}' fill='{c}' opacity='0.85'/>"
        lx = xx+10 if n!="medium" else xx-10
        ta = "start" if n!="medium" else "end"
        s+=f"<text x='{lx}' y='{yy+4}' font-size='10' fill='#102033' text-anchor='{ta}'>{esc(n)}</text>"
    return s+"</svg>"

html_doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>CodeGraph retrospective — why we're parking it</title>
<style>
:root{{--bg:#f4f7fb;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--greenSoft:#e7f7ef;--redSoft:#fdeceb;--amberSoft:#fff5dd;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:24px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),linear-gradient(180deg,#fbfdff,var(--bg));font-family:Inter,system-ui,-apple-system,sans-serif;color:var(--ink);line-height:1.55}}.wrap{{max-width:1240px;margin:0 auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.95);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:var(--radius)}}.hero{{padding:42px}}section{{padding:26px;margin-top:20px}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.1}}h1{{font-size:clamp(1.9rem,4vw,3.2rem);max-width:26ch;margin-top:14px}}h2{{font-size:clamp(1.3rem,2vw,1.8rem);margin-bottom:6px}}h3{{font-size:1.02rem;margin:6px 0}}p{{color:var(--muted)}}.subtitle{{font-size:1.05rem;max-width:96ch}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}}.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase}}.pill{{padding:8px 13px;border:1px solid var(--line);background:#f8fafc;color:#31415d}}.pill.good{{background:var(--greenSoft);color:var(--green)}}.pill.bad{{background:var(--redSoft);color:var(--red)}}.pill.caution{{background:var(--amberSoft);color:var(--amber)}}.pill.neutral{{background:#eef3ff;color:#1d3fb8}}.tag{{padding:3px 8px;font-size:10px}}.tag.good{{background:var(--greenSoft);color:var(--green)}}.tag.bad{{background:var(--redSoft);color:var(--red)}}.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:28px}}.stat{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;min-height:108px}}.stat .label{{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:850;margin-bottom:8px}}.stat .value{{display:block;font-size:clamp(1.3rem,1.8vw,1.8rem);font-weight:900;letter-spacing:-.03em}}.stat .sub{{display:block;color:var(--muted);font-size:.84rem;margin-top:6px;font-weight:650}}table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}}td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}tbody tr:hover{{background:#f8fafc}}.muted{{color:var(--muted)}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#eef2ff;border-radius:6px;padding:.12em .35em;font-size:.88em}}.chart{{width:100%;height:auto;max-width:560px;display:block}}.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin:14px 0}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}}.head{{margin-bottom:14px}}.foot{{text-align:center;color:var(--muted);font-size:.86rem;margin-top:24px}}ul.tight li{{margin:4px 0}}@media(max-width:900px){{.stats{{grid-template-columns:1fr 1fr}}.grid2{{grid-template-columns:1fr}}table{{font-size:.8rem}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>CodeGraph retrospective · GPT-5.5-low · 12_v0 + 36_v2</span>
<h1>We tried CodeGraph five different ways. None of them moved the Pareto frontier.</h1>
<p class='subtitle'>From a soft "use the CLI" skill to hard auto-injection of caller maps, from caller counts to caller names, from solo to observational-memory hybrids, and finally to a churn-driven skill rewrite — every CodeGraph variant was Pareto-dominated by plain Pi or plain thinking budget. One config was actively harmful. The skill rewrite produced pure churn. Here's the full arc, the numbers, and the conditions under which we'd come back.</p>
<div class='pillrow'><span class='pill neutral'>8 configs built</span><span class='pill bad'>5 ran clean comparisons</span><span class='pill bad'>1 net-harmful (−0.091 partial)</span><span class='pill caution'>1 perfect null (28/28, churn)</span><span class='pill good'>1 real skill-aligned win (n=1)</span><span class='pill good'>0 expanded the frontier</span></div>
<div class='stats'>
<div class='stat'><span class='label'>Best CodeGraph (36_v2)</span><span class='value'>31/108</span><span class='sub'>seam-checkpoint, 28.7% — dominated by wf-only 35</span></div>
<div class='stat'><span class='label'>Cost per net solve</span><span class='value'>~29M tok</span><span class='sub'>CLI-skill: +58.8M tok for +2 solves (vs ~4.7M for thinking)</span></div>
<div class='stat'><span class='label'>Worst CodeGraph (12_v0)</span><span class='value'>−0.091</span><span class='sub'>codegraph-auto counts, CI excludes 0 — actively harmful</span></div>
<div class='stat'><span class='label'>Frontier at pass@3</span><span class='value'>medium 72%</span><span class='sub'>beats every CodeGraph config + pi-codex-goal on both axes</span></div>
</div></header>

<section><div class='head'><h2>The lineage — what we built and tested</h2><p>Eight configs total. Five produced clean comparable runs; the three observational-memory hybrids only ran partial diagnostic cells (quarantined) and never completed a comparable batch.</p></div>
<table><thead><tr><th>Config</th><th>Mechanism</th><th>Subset</th><th>Cells</th><th>Verdict</th></tr></thead><tbody>
<tr><td><strong>codegraph-skill</strong></td><td>Soft: CLI on PATH + full skill; agent chooses to query blast radius</td><td>12_v0 + 36_v2</td><td class='num'>135</td><td>Null-to-negative; perfect 28/28 null on 36_v2</td></tr>
<tr><td><strong>codegraph-cli-skill</strong></td><td>Softer: just <code>You should use codegraph cli</code> + skill</td><td>36_v2</td><td class='num'>108</td><td>+2 solves (ns), +73% tokens, dominated</td></tr>
<tr><td><strong>codegraph-auto</strong></td><td>Hard: extension auto-injects caller <em>counts</em> (brief) on every read/edit</td><td>12_v0</td><td class='num'>36</td><td><span class='tag bad'>net harmful</span> −0.091 partial</td></tr>
<tr><td><strong>codegraph-impact</strong></td><td>Hard v2: auto-injects caller <em>names</em> (fn-impact), fix for auto</td><td>12_v0</td><td class='num'>36</td><td>Better than auto (+0.053) but still −0.038 vs base</td></tr>
<tr><td><strong>codegraph-cli-skill-seam-checkpoint</strong></td><td>Rewritten skill: seam checkpoint + "choose the behavioral seam" + "smaller edit"</td><td>36_v2</td><td class='num'>108</td><td>+1 solve, pure churn, pass@3 <em>worse</em></td></tr>
<tr><td><strong>codegraph-*-om</strong> (×3)</strong></td><td>CodeGraph + observational-memory hybrids</td><td>12_v0</td><td class='num'>~diag only</td><td>Never completed a clean comparable run (quarantined)</td></tr>
</tbody></table></section>

<section><div class='head'><h2>12_v0 — where the "hard" injection hurt</h2><p>From <code>analysis/codegraph-12v0-results.txt</code> (n=36/arm, bootstrap 95% CI). <strong>codegraph-auto's count-injection was significantly net-harmful</strong>, which triggered the primitive audit.</p></div>
<table><thead><tr><th>Arm</th><th>Solve</th><th>Partial</th><th>Δ partial</th><th>Δ solve</th><th>Med tok(k)</th><th>Med $</th></tr></thead><tbody>{fam12_rows()}</tbody></table>
<p class='muted'><strong>ns</strong> = not significant, <strong>*</strong> = 95% CI excludes 0. Note observational-memory (not CodeGraph) was the only arm that clearly moved solves on 12_v0.</p>
<div class='callout bad'><strong>The primitive audit</strong> (<code>configs/codegraph-auto/CODEGRAPH_PRIMITIVE_AUDIT.md</code>) diagnosed why counts failed: <code>brief</code> returns flat per-file caller <em>counts</em> ("7 callers") with no <em>names</em> or chain — the shallowest relationship primitive. The fix was <code>fn-impact</code> (caller names by level), which codegraph-impact adopted and recovered +0.053 partial — but still net-negative vs baseline. The audit also found <code>diff-impact</code> (the in-flight-change blast signal) is <strong>broken in 3.15.0</strong>, and that codegraph is <strong>repo-scoped</strong>: it cannot see cross-package / shared-type / <code>node_modules</code> seams — which is exactly where many DeepSWE failure modes live.</p></div>
</section>

<section><div class='head'><h2>36_v2 — every CodeGraph config is dominated</h2><p>n=108/arm. The two non-dominated Pi rows (baseline-wf-only, medium) beat every CodeGraph variant on solves <em>and</em> cost.</p></div>
<table><thead><tr><th>Arm</th><th>Solves</th><th>Rate</th><th>Partial</th><th>Med tok</th><th>Med $</th><th>Total $</th></tr></thead><tbody>{fam36_rows()}</tbody></table>
<div class='grid2' style='margin-top:16px'>
<div class='callout bad'><h3>The perfect null: codegraph-skill</h3><p>On 36_v2, <strong>codegraph-scored exactly the same 28/108 as baseline</strong>, with 9 baseline-only solves and 9 codegraph-only solves (90 cells agreed). Identical solve count, pure churn — but +22% tokens (+132k median) and +$16 total. The tool ran; it just redistributed which boundary cells landed which way without adding any.</p></div>
<div>{pareto_svg()}<p class='muted' style='text-align:center;font-size:.84rem'>Green = Pareto frontier · red = CodeGraph (all dominated)</p></div>
</div></section>

<section><div class='head'><h2>The skill rewrite was pure churn</h2><p>After the 36_v2 CLI-skill run, we did a paired-trajectory deep dive on all 19 solve flips between old-skill and seam-skill (<code>analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/</code>), classifying each from session/patch/verifier evidence via parallel reviewers.</p></div>
<div class='grid2'>
<div class='callout'><h3>What the 19 flips actually were</h3><ul class='tight'>
<li><strong>13 threshold noise</strong> — 1–3 f2p/p2p boundary tests, |Δpartial|&lt;0.04</li>
<li><strong>2 capability-edge variance</strong> — go-critic reps misread <code>types.LookupFieldOrMethod</code> return signature (orthogonal bugs on the same task)</li>
<li><strong>1 verifier false positive</strong> — claude-code "gain" was a heap-OOM crash producing a degenerate all-pass JUnit</li>
<li><strong>1 real fix, weak attribution</strong> — happy-dom async lifecycle; but seam patch was <em>larger</em>, violating its own rule</li>
<li><strong>1 real skill-aligned win</strong> — etree reused <code>FindElement</code> instead of hand-rolling a broken selector (n=1, confounded by +136k tokens)</li>
</ul></div>
<div class='callout bad'><h3>The skill's own rule isn't followed</h3><p>In <strong>3 of 6 meaningful flips the seam patch was larger</strong> than the old patch, directly contradicting the seam-skill's "let CodeGraph make the edit smaller" rule. At pass@3 the seam skill (38.9%) is <em>worse</em> than the old skill (41.7%) and equal to plain baseline — the rewrite didn't just fail to help, it slightly lowered the ceiling.</p></div>
</div></section>

<section><div class='head'><h2>pass@3 settles it</h2><p>3 reps = pass@3 by construction. The CodeGraph configs are dominated at the pass@3 ceiling too.</p></div>
<table><thead><tr><th>Arm</th><th>pass@1</th><th>pass@3</th><th>$/rep</th><th>$ always-3</th><th>$ seq-retry*</th></tr></thead><tbody>{passk_rows()}</tbody></table>
<p class='muted'>*seq-retry = expected $/task if you stop at first solve (cap 3). At pass@3 the frontier collapses to <strong>low/baseline-preamble-orch (47.2%)</strong> and <strong>medium/baseline (72.2%)</strong> — the latter beats even pi-codex-goal on both solve and cost.</p></div></section>

<section><div class='head'><h2>Why we're moving on</h2></div>
<div class='callout bad'><strong>1. Pareto-dominated at every config, every subset, every k.</strong> No CodeGraph variant beats the cheapest non-dominated alternative. The best (seam-checkpoint, 31/108) is beaten by baseline-wf-only (35/108) at lower cost; medium thinking (50/108) beats all of them.</p></div>
<div class='callout bad'><strong>2. The cost-per-solve is brutal.</strong> codegraph-cli-skill: +58.8M tokens for +2 net solves = ~29M tokens/solve. Low→medium thinking gets solves at ~4.7M tokens/solve. CodeGraph is ~6× more expensive per marginal solve than just buying thinking budget — no skill tweak recovers from structural per-call tool overhead.</p></div>
<div class='callout bad'><strong>3. Hard injection can hurt.</strong> codegraph-auto's count-injection was significantly net-harmful (−0.091 partial). Even the fixed caller-name version (codegraph-impact) stayed net-negative. Auto-injecting relationship context the agent didn't ask for added noise.</p></div>
<div class='callout bad'><strong>4. The ceiling is structural.</strong> The primitive audit found codegraph is repo-scoped — it cannot see cross-package, shared-type, or <code>node_modules</code> seams, which is exactly where DeepSWE failures cluster ("missed boring integration seam"). And <code>diff-impact</code>, the in-flight-change blast signal, is broken in 3.15.0.</p></div>
<div class='callout bad'><strong>5. The agent doesn't follow the skill.</strong> GPT-5.5-low wrote larger patches in 3/6 meaningful flips despite the "smaller edit" rule. Prose guidance doesn't bind at this capability level; capability-edge bugs (misreading stdlib signatures) are out of scope for skill text.</p></div></section>

<section><div class='head'><h2>What would bring us back</h2><p>Concrete, falsifiable conditions — not "try harder."</p></div>
<div class='grid2'>
<div class='callout'><h3>Tool / upstream</h3><ul class='tight'>
<li><strong><code>diff-impact</code> fixed</strong> so a consolidation-time blast signal works (currently broken in 3.15.0) — then a hook could inject blast radius of the actual in-flight change, not just static callers.</li>
<li><strong>Cross-package indexing</strong> — if codegraph could resolve shared-type / <code>node_modules</code> seams, it would cover the DeepSWE failure mode it's structurally blind to today.</li>
<li><strong>Semantic <code>search</code>/<code>embed</code></strong> actually built and exercised — a different value proposition (find-by-meaning) than caller chains.</li>
</ul></div>
<div class='callout'><h3>Executor / method</h3><ul class='tight'>
<li><strong>A stronger executor</strong> that reliably follows a checkable process — at GPT-5.5-low the skill rules are ignored (larger patches). Worth re-testing at medium/high where the agent might actually execute "reuse existing API before reinventing."</li>
<li><strong>Checkable enforcement, not prose</strong> — a diff-size budget gate or a "name the existing API or justify reinvention" step (via <code>codegraph where/deps</code>) that the harness verifies, rather than a paragraph the model can ignore.</li>
<li><strong>A task distribution where failures are internal-caller-chain breaks</strong> — not cross-package seams. On a repo where the regressions are genuinely "I broke an internal caller," the caller map earns its keep.</li>
</ul></div>
</div>
<div class='callout good'><strong>What we keep.</strong> The solve-churn analysis <em>method</em> (paired trajectory packets → f2p/p2p split → patch-shape diff → verifier-test mapping → failure-mode classification) is durable and reusable — it gave the first clean causal breakdown of why marginal configs churn, and it transfers to whatever we evaluate next.</div></section>

<section><div class='head'><h2>The bottom line</h2></div>
<div class='callout'><p>This is the project's recurring finding in one clean case study: <strong>thinking budget dominates, and no skill or extension tested has expanded the Pareto frontier beyond what thinking alone provides.</strong> CodeGraph is the most thoroughly explored instance of that pattern — five mechanisms, two subsets, a primitive audit, a churn deep dive, and a skill rewrite, all converging on "adds tokens, doesn't add solves." The mechanism is sound in theory (structural understanding should help), but at GPT-5.5-low on DeepSWE the agent doesn't use it well, the cost is structural, and the failures it would need to catch are largely outside its ceiling. We're parking it.</p>
<p class='muted'>Open levers that actually could move the frontier: sequential retry with early termination (validate the modeled ~40% cost cut at the pass@3 ceiling), and/or higher k on the medium frontier — neither of which involves another skill.</p></div></section>

<div class='foot'>Sources: <code>analysis/codegraph-12v0-results.txt</code>, <code>analysis/codegraph-cli-skill-36v2/</code>, <code>analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/classification.json</code>, <code>configs/codegraph-auto/CODEGRAPH_PRIMITIVE_AUDIT.md</code>, unified metrics pass over <code>results/gpt-5.5/low/</code>. Generated by <code>render.py</code>.</div>
</div></body></html>"""
(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html", len(html_doc), "bytes")
