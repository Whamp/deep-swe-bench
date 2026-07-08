#!/usr/bin/env python3
from __future__ import annotations
import html, json
from pathlib import Path

OUT = Path(__file__).resolve().parent
C = json.loads((OUT / "classification.json").read_text())
FLIPS = C["flips"]
ROOT = Path(__file__).resolve().parents[3]

def esc(x): return html.escape(str(x))
def sgn(x): return "+" if x >= 0 else "−"
def dp(x): return f"{sgn(x)}{abs(x):.4f}"


def direction_tag(d):
    return "seam gain" if d == "seam_gain" else "seam loss"


def bucket_tone(b):
    if "variance" in b or "noise" in b or "verifier_artifact" in b: return "bad"
    if "real fix" in b: return "good"
    return "neutral"


def evidence_list(ev):
    return "<ul>" + "".join(f"<li>{esc(e)}</li>" for e in ev) + "</ul>"


def flip_rows():
    out = []
    # sort: meaningful first, then by |delta_partial|
    ordered = sorted(FLIPS, key=lambda f: (0 if f["category"] == "meaningful" else 1, -abs(f["delta_partial"])))
    for f in ordered:
        out.append(f"""<tr>
<td><strong>{esc(f['task'])}</strong> · rep{f['rep']}<br><span class='muted'>{esc(f.get('title',''))}</span></td>
<td><span class='tag {'good' if f['direction']=='seam_gain' else 'bad'}'>{direction_tag(f['direction'])}</span></td>
<td class='num'>{esc(f['old_f2p'])} → {esc(f['seam_f2p'])}<br><span class='muted'>{esc(f['old_p2p'])} → {esc(f['seam_p2p'])} p2p</span></td>
<td class='num'>{dp(f['delta_partial'])}</td>
<td><strong>{esc(f['bucket'])}</strong></td>
<td>{esc(f['seam_text_plausibly_mattered'])}</td>
<td>{esc(f['confidence'])}</td>
</tr>""")
    return "\n".join(out)


def detail_blocks():
    out = []
    meaningful = [f for f in FLIPS if f["category"] == "meaningful"]
    meaningful.sort(key=lambda f: -abs(f["delta_partial"]))
    for f in meaningful:
        tone = bucket_tone(f["bucket"])
        out.append(f"""<div class='callout {tone}'><h3>{esc(f['task'])} · rep{f['rep']} — <span class='tag {'good' if f['direction']=='seam_gain' else 'bad'}'>{direction_tag(f['direction'])}</span> {dp(f['delta_partial'])} partial</h3>
<p><strong>Bucket:</strong> {esc(f['bucket'])}</p>
<p><strong>Mechanism:</strong> {esc(f['mechanism'])}</p>
<p><strong>Did the seam-checkpoint text plausibly matter?</strong> {esc(f['seam_text_plausibly_mattered'])} &nbsp; <strong>Confidence:</strong> {esc(f['confidence'])}</p>
<p><strong>f2p:</strong> {esc(f['old_f2p'])} → {esc(f['seam_f2p'])} &nbsp; <strong>p2p:</strong> {esc(f['old_p2p'])} → {esc(f['seam_p2p'])}</p>
{evidence_list(f.get('evidence', []))}</div>""")
    return "\n".join(out)


# aggregate stats
from collections import Counter
bucket_counts = Counter(f["bucket"] for f in FLIPS)
noise_n = sum(1 for f in FLIPS if f["category"] == "noise")
meaningful_n = sum(1 for f in FLIPS if f["category"] == "meaningful")
real_fix = sum(1 for f in FLIPS if "real fix" in f["bucket"])
variance = sum(1 for f in FLIPS if "variance" in f["bucket"] or "verifier_artifact" in f["bucket"])
seam_helped = sum(1 for f in FLIPS if str(f["seam_text_plausibly_mattered"]).lower().startswith("yes"))

html_doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>CodeGraph seam vs old skill · paired trajectory deep dive</title><style>
:root{{--bg:#f4f7fb;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--greenSoft:#e7f7ef;--redSoft:#fdeceb;--amberSoft:#fff5dd;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:24px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),linear-gradient(180deg,#fbfdff,var(--bg));font-family:Inter,system-ui,-apple-system,sans-serif;color:var(--ink);line-height:1.5}}.wrap{{max-width:1280px;margin:0 auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.95);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:var(--radius)}}.hero{{padding:42px}}section{{padding:26px;margin-top:20px}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.1}}h1{{font-size:clamp(1.9rem,4vw,3.4rem);max-width:24ch;margin-top:14px}}h2{{font-size:clamp(1.3rem,2vw,1.8rem);margin-bottom:8px}}h3{{font-size:1.05rem;margin:6px 0}}p{{color:var(--muted)}}.subtitle{{font-size:1.05rem;max-width:92ch}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}}.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase}}.pill{{padding:8px 13px;border:1px solid var(--line);background:#f8fafc;color:#31415d}}.pill.good,.tag.good{{background:var(--greenSoft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--redSoft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amberSoft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.tag{{padding:4px 9px}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:28px}}.stat{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;min-height:108px}}.stat .label{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:850;margin-bottom:8px}}.stat .value{{display:block;font-size:clamp(1.3rem,1.8vw,1.8rem);font-weight:900;letter-spacing:-.03em}}.stat .sub{{display:block;color:var(--muted);font-size:.88rem;margin-top:6px;font-weight:650}}table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}}td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}tbody tr:hover{{background:#f8fafc}}.muted{{color:var(--muted)}}.mono,code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}code{{background:#eef2ff;border-radius:6px;padding:.12em .35em}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin:14px 0}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}}.head{{margin-bottom:14px}}.foot{{text-align:center;color:var(--muted);font-size:.86rem;margin-top:24px}}@media(max-width:900px){{.stats{{grid-template-columns:1fr 1fr}}table{{font-size:.8rem}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>Paired trajectory deep dive · old skill ↔ seam skill</span><h1>The +1 solve is 13 noise flips, 1 verifier false positive, and one genuine skill-aligned fix.</h1><p class='subtitle'>Controlled comparison: same GPT-5.5-low, same tools, same one-line prompt, same CodeGraph CLI. The only delta is the skill markdown (seam checkpoint + behavioral-seam scout + "make the edit smaller" rule). I built a trajectory packet for all 19 solve flips and classified each from session/patch/verifier evidence. The churn is dominated by single-digit boundary-test noise and capability-edge implementation bugs the skill text cannot touch.</p>
<div class='pillrow'><span class='pill neutral'>19 solve flips</span><span class='pill bad'>13 threshold noise</span><span class='pill bad'>2 capability-edge variance</span><span class='pill bad'>1 verifier false positive</span><span class='pill good'>1 skill-aligned real fix (n=1)</span><span class='pill neutral'>1 real fix, weak attribution</span></div>
<div class='stats'><div class='stat'><span class='label'>Threshold-noise flips</span><span class='value'>{noise_n}/19</span><span class='sub'>1–3 f2p/p2p boundary tests, |Δpartial|&lt;0.04</span></div><div class='stat'><span class='label'>Variance / artifact</span><span class='value'>3/6</span><span class='sub'>of the 6 meaningful flips</span></div><div class='stat'><span class='label'>Real fixes</span><span class='value'>{real_fix}/19</span><span class='sub'>only {seam_helped} plausibly seam-driven (n=1)</span></div><div class='stat'><span class='label'>Skill text violated</span><span class='value'>3/6</span><span class='sub'>seam patches LARGER despite "smaller edit" rule</span></div></div></header>

<section><div class='head'><h2>Method</h2><p>For each of the 19 solve flips I extracted a paired packet (metrics, patch stats, tool timeline, CodeGraph commands, verifier tails, changed files). The 6 flips with |Δpartial|&gt;0.04 were independently classified by read-only reviewers from packet + session evidence. The remaining 13 were bucketed as threshold noise from their single-digit f2p/p2p counts. Every claim below distinguishes direct session/patch evidence from inference.</p></div></section>

<section><div class='head'><h2>All 19 flips — classification table</h2><p>Meaningful flips first (|Δpartial|&gt;0.04), then noise flips sorted by partial delta.</p></div><table><thead><tr><th>Task · rep</th><th>Dir</th><th>f2p / p2p</th><th>Δ partial</th><th>Bucket</th><th>Seam text?</th><th>Conf.</th></tr></thead><tbody>{flip_rows()}</tbody></table></section>

<section><div class='head'><h2>The 6 meaningful flips in detail</h2><p>These are the only flips where partial reward moved enough to be a real quality signal rather than binary-boundary noise.</p></div>{detail_blocks()}</section>

<section><div class='head'><h2>Win vs loss pattern comparison</h2></div><div class='grid2' style='display:grid;grid-template-columns:1fr 1fr;gap:18px'><div class='callout good'><h3>Wins pattern (etree, happy-dom-rep1)</h3><p>The genuine wins came from <strong>choosing the right behavioral seam</strong>: etree reused etree's existing <code>FindElement</code> instead of hand-rolling a broken selector; happy-dom implemented a self-rescheduling poll loop instead of a one-shot callback. These align with the seam-skill's "choose the behavioral seam before editing" guidance.</p><p><strong>But:</strong> in happy-dom-rep1 the seam patch was <em>larger</em> (449 vs 357 lines), directly contradicting the "make the edit smaller" rule. And both wins are single reps confounded by extra token spend (+136k / +135k).</p></div><div class='callout bad'><h3>Losses pattern (go-critic ×2, happy-dom-rep2)</h3><p>The losses were <strong>capability-edge implementation bugs the skill text cannot prevent</strong>: go-critic-rep0 misread the return signature of <code>types.LookupFieldOrMethod</code> (bound <code>indirect</code> instead of the Object); go-critic-rep1 missed a LookupPackage branch for two-part package refs. These are orthogonal defects on the same task — the signature of capability-edge variance. happy-dom-rep2 is a <strong>perfect cross-rep inversion</strong> of rep1 (net skill effect = 0).</p><p><strong>Crucially:</strong> in 3 of 6 meaningful flips the seam patch was LARGER, violating the seam-skill's own "smaller edit" rule.</p></div></div></section>

<section><div class='head'><h2>The one clean attribution: etree</h2></div><div class='callout good'><p>The only flip where the seam-skill's guidance <em>specifically</em> aligns with the fix is <strong>etree-xml-diff-patch rep2</strong>. OLD hand-rolled a 49-line <code>selectElem</code> selector parser that silently no-op'd every <code>ApplyPatch</code> operation; SEAM reused etree's existing <code>(*Document).FindElement</code> API and wrote a smaller correct patch. SEAM ran 3 API-discovery greps (<code>AddChild</code>/<code>RemoveChild</code>/<code>FindElement</code> — exactly the APIs it then reused) and a self-verification <code>go run</code> that OLD never did. This is the seam-skill's "choose the behavioral seam" + "make the edit smaller" rules doing exactly what they say.</p><p><strong>Caveat:</strong> n=1, and SEAM spent +136k tokens, so the larger exploration budget — not the wording — could plausibly explain the flip on its own.</p></div></section>

<section><div class='head'><h2>Skill-design hypotheses</h2><p>Using checkable-process principles (trigger → action → completion criterion), not vague advice.</p></div>
<div class='callout caution'><p><strong>The seam-checkpoint text is the right KIND of guidance but is not being followed.</strong> GPT-5.5-low wrote larger patches in 3 of 6 meaningful flips despite the "make the edit smaller" rule. The prose does not bind.</p></div>
<div class='callout'><p><strong>H1 — diff-size budget gate.</strong> The skill says "smaller" but nothing checks it. A checkable rule would be: <em>after scouting, if the planned change touches shared/parser/protocol code, run <code>diff-impact</code> and confirm the change is scoped to one feature gate before editing</em> — a verifiable step, not a preference.</p></div>
<div class='callout'><p><strong>H2 — "reuse existing API" as a checkable seam test.</strong> etree is the one win, and it came from <em>not reinventing</em>. A checkable process: <em>before hand-rolling a parser/selector/dispatcher, run <code>codegraph where</code>/<code>deps</code> for the closest existing function that already does this; name it or justify the reinvention</em>.</p></div>
<div class='callout'><p><strong>H3 — capability-edge bugs are out of scope for skill prose.</strong> go-critic's <code>LookupFieldOrMethod</code> return-signature misread is not something a skill paragraph prevents; it needs a typecheck/run-test loop (which both arms did). Do not expect skill text to fix wrong-API-signature bugs.</p></div>
<div class='callout'><p><strong>H4 — verify the verifier.</strong> The claude-code rep0 "gain" is a heap-OOM false positive. The grader trusted a degenerate all-pass JUnit. This is a harness issue, not a skill issue, and it inflates apparent solves — flag for the benchmark, not the skill.</p></div></section>

<section><div class='head'><h2>Conclusion</h2></div><div class='callout bad'><strong>No systematic skill-text effect.</strong> Of 19 flips, 13 are boundary-test noise, 2 are capability-edge variance the skill cannot touch, 1 is a verifier false positive, and only 1 (etree) cleanly matches the seam guidance — at n=1 and confounded by token budget. The seam-skill is slightly cheaper in aggregate but does not reliably change which boundary cells land which way.</div><div class='callout'><strong>The honest mechanism:</strong> at GPT-5.5-low on near-ceiling tasks, solve outcomes are decided by a handful of f2p tests crossing an all-or-nothing boundary. The skill text moves the agent's exploration budget and patch shape, but not enough to systematically convert boundary tests — and in several cases the seam-skill's own "smaller edit" rule is violated. To make this skill pay off you need either a stronger executor or a checkable enforcement (diff-size gate, reuse-existing-API test), not more prose.</div></section>

<div class='foot'>Generated from <code>analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/classification.json</code>. Packets: <code>churn_deep_dive/*__rep*__*.md</code>.</div>
</div></body></html>"""
(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html")
