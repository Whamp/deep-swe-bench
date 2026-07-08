#!/usr/bin/env python3
"""Render the OMP-vs-Pi turn/token deep-dive HTML report."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent

# Key measured facts (from tool_result_sizes.py, compounding.py, source extraction)
PI = dict(turns=38, reads=1147, read_med=2398, bash_med=365, edit_med=61, edit_calls=1024,
          result_chars=69452, recache=1665456, wrapper=1891, bash_artifact_pct=0.0, solve=33)
OMP = dict(turns=53, reads=2218, read_med=2333, bash_med=155, edit_med=595, edit_calls=1496,
           result_chars=133061, recache=4798978, wrapper=7968, bash_artifact_pct=59.5, solve=36)

def r(x, base): return f"{x/base:.2f}×"

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Why OMP burns 3× tokens · turn/token deep dive · DeepSWE</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;
--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;
--amber:#c58a00;--amber-soft:#fff4d8;--purple:#7c3aed;--purple-soft:#f3eefe;
--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);
--radius-xl:28px;--radius-lg:20px;--max:1180px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),linear-gradient(180deg,#f8fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.55}}
.wrap{{max-width:var(--max);margin:0 auto;padding:28px 20px 60px}}
.hero,section{{background:rgba(255,255,255,.88);backdrop-filter:blur(8px);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius-xl);box-shadow:var(--shadow)}}
.hero{{padding:clamp(24px,4vw,40px)}}
.eyebrow{{display:inline-flex;gap:8px;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}
h1,h2,h3{{margin:0;letter-spacing:-0.03em;line-height:1.08}}h1{{font-size:clamp(1.9rem,4vw,3.2rem);margin-top:14px}}
.subtitle{{max-width:74ch;color:var(--muted);font-size:clamp(1rem,1.1vw,1.06rem);margin:14px 0 0}}
.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}
.pill{{display:inline-flex;gap:8px;padding:8px 13px;border-radius:999px;font-size:12px;font-weight:800;text-transform:uppercase;background:var(--surface-2);border:1px solid var(--line);color:#31415d}}
.pill.bad{{background:var(--red-soft);color:var(--red);border-color:rgba(208,71,63,.16)}}
.pill.caution{{background:var(--amber-soft);color:var(--amber)}}
.pill.neutral{{background:#eef3ff;color:var(--blue-2)}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:26px}}
.stat{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);padding:16px;box-shadow:var(--shadow-sm)}}
.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}}
.stat .value{{display:block;font-size:clamp(1.3rem,2vw,1.85rem);font-weight:900;letter-spacing:-0.04em}}
.stat .sub{{display:block;margin-top:6px;font-size:.85rem;color:var(--muted)}}
section{{margin-top:20px;padding:clamp(18px,3vw,28px)}}
.section-head h2{{font-size:clamp(1.4rem,2.4vw,1.85rem);margin-bottom:6px}}
.section-head p{{margin:0;color:var(--muted);max-width:72ch}}
.chain{{display:grid;grid-template-columns:1fr;gap:12px;margin-top:8px}}
.step{{display:grid;grid-template-columns:48px 1fr;gap:16px;align-items:start;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:var(--shadow-sm)}}
.step .num{{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,var(--blue),var(--blue-2));color:#fff;font-weight:900;display:flex;align-items:center;justify-content:center;font-size:1.1rem}}
.step h3{{font-size:1.05rem;margin-bottom:4px}}
.step p{{margin:0;color:#3a4a66;font-size:.95rem}}
.step .tag{{display:inline-block;margin-top:8px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:800;text-transform:uppercase}}
.tag.mech{{background:var(--red-soft);color:var(--red)}}.tag.behav{{background:var(--purple-soft);color:var(--purple)}}.tag.struct{{background:var(--amber-soft);color:var(--amber)}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.quote{{background:#0d1b2e;color:#cfe1ff;border-radius:12px;padding:14px 16px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9rem;margin:10px 0;white-space:pre-wrap;overflow-x:auto}}
.cmp{{width:100%;border-collapse:collapse;font-size:.95rem;margin-top:10px}}
.cmp th,.cmp td{{text-align:left;padding:11px 12px;border-bottom:1px solid var(--line);white-space:nowrap}}
.cmp th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:800}}
.cmp td.num,.cmp th.num{{text-align:right;font-variant-numeric:tabular-nums}}
.cmp tbody tr:hover{{background:var(--surface-2)}}
.ratio{{color:var(--red);font-weight:800}}
.bar{{height:14px;border-radius:4px;display:inline-block;vertical-align:middle}}
.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;color:#22314d;margin-top:14px}}
.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}
.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}
.callout strong{{color:var(--blue-2)}}
@media(max-width:820px){{.stats{{grid-template-columns:repeat(2,1fr)}}}}
.foot{{margin-top:18px;color:var(--muted);font-size:.85rem}}
</style></head><body><div class="wrap">

<div class="hero">
 <span class="eyebrow">Why OMP burns 3× tokens · GPT-5.5 low · 36_v2 · 108 cells/arm</span>
 <h1>It's the persona prompt <em>and</em> the tool results — compounding over more turns</h1>
 <p class="subtitle">OMP re-identifies the model as Google DeepMind's <strong>Antigravity</strong> agent, caps bash output to a ~184-char tail (59.5% of calls offloaded to artifacts), and forces the model to compensate with ~2× more reads plus a grep/glob pass. Those extra results compound across more turns on top of a 4× heavier per-turn wrapper. Same model, same solves, 3× tokens.</p>
 <div class="pillrow">
   <span class="pill bad">59.5% bash outputs truncated to artifact refs</span>
   <span class="pill caution">Antigravity persona prompt</span>
   <span class="pill bad">2.88× result re-cache burden</span>
   <span class="pill neutral">7968 vs 1891 tok/turn wrapper</span>
 </div>
 <div class="stats">
   <div class="stat"><span class="label">Bash truncated to artifact</span><span class="value">{OMP['bash_artifact_pct']}%</span><span class="sub">OMP vs Pi 0% — model starved of output</span></div>
   <div class="stat"><span class="label">Result re-cache burden</span><span class="value">{r(OMP['recache'],PI['recache'])}</span><span class="sub">4.8M vs 1.67M char-turns</span></div>
   <div class="stat"><span class="label">Reads per 108 cells</span><span class="value">{r(OMP['reads'],PI['reads'])}</span><span class="sub">2218 vs 1147 — same size each</span></div>
   <div class="stat"><span class="label">Per-turn wrapper</span><span class="value">{r(OMP['wrapper'],PI['wrapper'])}</span><span class="sub">7968 vs 1891 tok, every turn</span></div>
 </div>
</div>

<section>
 <div class="section-head"><h2>The causal chain</h2><p>Five OMP-specific factors, none of which is "the model is dumber." Each tagged by type: <span class="tag behav">behavioral</span> <span class="tag mech">tool mechanic</span> <span class="tag struct">structural</span></p></div>
 <div class="chain">
  <div class="step"><div class="num">1</div><div>
    <h3>Identity: "You are Antigravity" <span class="tag behav">behavioral</span></h3>
    <p>OMP's system prompt re-identifies the model as a different agent rather than a generic assistant:</p>
    <div class="quote">You are Antigravity, a powerful agentic AI coding assistant designed by the
Google Deepmind team working on Advanced Agentic Coding. You are pair
programming with a USER to solve their coding task. **Absolute paths only** **Proactiveness** ...</div>
    <p>This Antigravity-style persona promotes methodical, exploratory work — the root of the "read everything, verify, map the repo" pattern.</p>
  </div></div>
  <div class="step"><div class="num">2</div><div>
    <h3>Bash output starved to artifacts <span class="tag mech">tool mechanic</span></h3>
    <p><strong>{OMP['bash_artifact_pct']}% of OMP bash calls</strong> return only a ~184-char tail plus <code>[raw output: artifact://N]</code> — the full output is offloaded to an artifact store. Pi shows full output inline (0% offload). The model gets a fraction of the test/build/error information per call.</p>
    <div class="quote">Tests:       9 failed, 9 total
Snapshots:   0 total
Time:        17.812 s
[raw output: artifact://5]

Wall time: 18.28 seconds

Command exited with code 1</div>
    <p>To recover the detail it can't see, the model reaches for more reads and greps → more tool calls.</p>
  </div></div>
  <div class="step"><div class="num">3</div><div>
    <h3>Compensating calls become extra turns <span class="tag struct">structural</span></h3>
    <p>OMP makes <strong>{r(OMP['reads'],PI['reads'])} more reads</strong> (2218 vs 1147) — and crucially each read returns the <em>same</em> size (OMP {OMP['read_med']:,} vs Pi {PI['read_med']:,} chars/call; the read tool is <strong>not</strong> truncating). The agent just reads more. Plus a grep/glob repo-mapping pass and {r(OMP['edit_calls'],PI['edit_calls'])} more edits. Tools-per-turn ≈ 1.0 for both, so every extra call is an extra turn: <strong>53 vs 38 turns</strong>.</p>
  </div></div>
  <div class="step"><div class="num">4</div><div>
    <h3>Edit bleeds content <span class="tag mech">tool mechanic</span></h3>
    <p>OMP's hashline edit mode returns <strong>{r(OMP['edit_med'],PI['edit_med'])} more per call</strong> ({OMP['edit_med']} vs {PI['edit_med']} chars), called {r(OMP['edit_calls'],PI['edit_calls'])} more often. Large edit confirmations pile into history. (Edit-result chars: OMP 1.11M vs Pi 70k — 16× more.)</p>
  </div></div>
  <div class="step"><div class="num">5</div><div>
    <h3>Compounding + heavy wrapper = the token explosion <span class="tag struct">structural</span></h3>
    <p>Every tool result stays in history and is re-cached on each later turn. OMP's 1.92× more result content, re-cached across 1.39× more turns = <strong>{r(OMP['recache'],PI['recache'])} re-cache burden</strong>. Layered on top: a <strong>{r(OMP['wrapper'],PI['wrapper'])} heavier per-turn wrapper</strong> ({OMP['wrapper']:,} vs {PI['wrapper']:,} tok — persona + larger tool defs), paid every turn.</p>
  </div></div>
 </div>
</section>

<section>
 <div class="section-head"><h2>Per-tool result sizes — the decisive ablation</h2><p>Median chars returned per tool call, and call counts, summed across 108 cells each.</p></div>
 <table class="cmp">
  <thead><tr><th>Tool</th><th class="num">Pi med chars/call</th><th class="num">OMP med chars/call</th><th class="num">OMP/Pi size</th><th class="num">Pi calls</th><th class="num">OMP calls</th><th class="num">call ratio</th><th>Reading</th></tr></thead>
  <tbody>
   <tr><td class="mono">read</td><td class="num">{PI['read_med']:,}</td><td class="num">{OMP['read_med']:,}</td><td class="num">{r(OMP['read_med'],PI['read_med'])}</td><td class="num">{PI['reads']:,}</td><td class="num">{OMP['reads']:,}</td><td class="num ratio">{r(OMP['reads'],PI['reads'])}</td><td>Same size/call — agent just reads 1.93× more. <strong>Not</strong> truncation.</td></tr>
   <tr><td class="mono">bash</td><td class="num">{PI['bash_med']}</td><td class="num">{OMP['bash_med']}</td><td class="num">{r(OMP['bash_med'],PI['bash_med'])}</td><td class="num">1,923</td><td class="num">1,807</td><td class="num">0.94×</td><td>OMP 59.5% offloaded to artifacts → model sees ~184-char tail.</td></tr>
   <tr><td class="mono">edit</td><td class="num">{PI['edit_med']}</td><td class="num">{OMP['edit_med']}</td><td class="num ratio">{r(OMP['edit_med'],PI['edit_med'])}</td><td class="num">{PI['edit_calls']:,}</td><td class="num">{OMP['edit_calls']:,}</td><td class="num ratio">{r(OMP['edit_calls'],PI['edit_calls'])}</td><td>Hashline mode returns far more; compounds in history.</td></tr>
   <tr><td class="mono">grep</td><td class="num">—</td><td class="num">3,049</td><td class="num">—</td><td class="num">0</td><td class="num">477</td><td class="num">—</td><td>OMP-only repo-mapping pass; Pi uses bash for search.</td></tr>
  </tbody>
 </table>
 <div class="callout">The read tool is <strong>not</strong> the culprit — it returns the same size per call. The culprits are: (a) the <strong>bash artifact cap</strong> starving the model, (b) the agent <strong>voluntarily reading 1.93× more</strong>, (c) <strong>edit bleeding 9.75× more content</strong> per call, and (d) a <strong>grep/glob pass</strong> Pi doesn't do.</div>
</section>

<section>
 <div class="section-head"><h2>Where the 3× tokens go</h2><p>The token gap decomposes into re-cached results (compounding) + the per-turn wrapper, each multiplied by the extra turns.</p></div>
 <table class="cmp">
  <thead><tr><th>Component</th><th class="num">Pi (median/cell)</th><th class="num">OMP (median/cell)</th><th class="num">ratio</th><th>note</th></tr></thead>
  <tbody>
   <tr><td>Turns</td><td class="num">{PI['turns']}</td><td class="num">{OMP['turns']}</td><td class="num">{r(OMP['turns'],PI['turns'])}</td><td>≈ tool calls (tools/turn ≈ 1.0 both)</td></tr>
   <tr><td>Result content produced</td><td class="num">{PI['result_chars']:,} chars</td><td class="num">{OMP['result_chars']:,} chars</td><td class="num">{r(OMP['result_chars'],PI['result_chars'])}</td><td>more reads + edit bleed + grep</td></tr>
   <tr><td><strong>Re-cache burden</strong> (results × later turns)</td><td class="num">{PI['recache']:,}</td><td class="num">{OMP['recache']:,}</td><td class="num ratio">{r(OMP['recache'],PI['recache'])}</td><td><strong>dominant token driver</strong></td></tr>
   <tr><td>Per-turn wrapper (tok)</td><td class="num">{PI['wrapper']:,}</td><td class="num">{OMP['wrapper']:,}</td><td class="num">{r(OMP['wrapper'],PI['wrapper'])}</td><td>persona + tool defs</td></tr>
   <tr><td>Wrapper × turns (tok)</td><td class="num">{PI['wrapper']*PI['turns']:,}</td><td class="num">{OMP['wrapper']*OMP['turns']:,}</td><td class="num ratio">{r(OMP['wrapper']*OMP['turns'],PI['wrapper']*PI['turns'])}</td><td>compounds with extra turns</td></tr>
  </tbody>
 </table>
 <div class="callout bad">The re-cache burden (<strong>{r(OMP['recache'],PI['recache'])}</strong>) and wrapper×turns (<strong>{r(OMP['wrapper']*OMP['turns'],PI['wrapper']*PI['turns'])}</strong>) together account for the 3× token gap. Both multiply with the extra turns — which exist because bash starvation forces compensating reads.</div>
</section>

<section>
 <div class="section-head"><h2>Bottom line</h2></div>
 <div class="callout"><strong>System prompt <em>or</em> tool results? Both — intertwined.</strong> The Antigravity persona drives exploratory behavior; the bash artifact cap starves the model of per-call information, forcing ~2× more reads and a grep/glob pass; the hashline edit bleeds content; and all of it compounds across more turns under a 4× heavier wrapper. None of it makes the model solve more (OMP 36 vs Pi 33 solves).</div>
 <div class="callout good" style="margin-top:14px"><strong>Levers, in priority order.</strong> (1) Show full bash output inline (or raise the artifact cap dramatically) — kills the compensating-reads chain. (2) Shrink the system prompt / persona. (3) Switch edit off hashline mode. (4) Only then worry about grep/glob. Token selection (the toolset ablation) barely moved the needle because these root causes are upstream of which search tool is registered.</div>
</section>

<div class="foot">Deep dive · analysis/omp-toolset-36v2/ (tool_result_sizes.py, compounding.py) · OMP source: ~/.cache/.bun/bin/omp · same model openai-codex/gpt-5.5 low · deterministic, no AI charts.</div>

</div></body></html>"""

out = HERE / "deep_dive.html"
out.write_text(html)
print(f"wrote {out} ({len(html):,} bytes)")
